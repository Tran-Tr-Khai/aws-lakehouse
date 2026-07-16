from __future__ import annotations

import argparse
import csv
import hashlib
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import boto3
from botocore.client import BaseClient
from botocore.exceptions import BotoCoreError, ClientError

from nyctx_ingestion.download import validate_download
from nyctx_ingestion.paths import LANDING_DIR, resolve_project_path
from nyctx_ingestion.periods import load_year_months_from_file, normalize_periods

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class UploadItem:
    local_path: Path
    object_key: str
    label: str


@dataclass(frozen=True)
class RemoteObjectMetadata:
    size: int | None
    checksum: str | None


def build_s3_client() -> BaseClient:
    return boto3.client('s3')


def validate_csv(path: Path) -> None:
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError(f'CSV file is empty: {path}')
    with path.open('r', encoding='utf-8', newline='') as file:
        reader = csv.reader(file)
        try:
            header = next(reader)
        except StopIteration as exc:
            raise ValueError(f'CSV file is empty: {path}') from exc
    if not header or any(not column.strip() for column in header):
        raise ValueError(f'CSV header is invalid: {path}')


def validate_local_artifact(path: Path) -> None:
    suffix = path.suffix.lower()
    if suffix in {'.parquet', '.zip'}:
        validate_download(path)
        return
    if suffix == '.csv':
        validate_csv(path)
        return
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError(f'Upload file is empty or missing: {path}')


def compute_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def read_remote_object_metadata(
    s3_client: BaseClient,
    bucket: str,
    object_key: str,
) -> RemoteObjectMetadata:
    try:
        response = s3_client.head_object(Bucket=bucket, Key=object_key)
    except ClientError as error:
        error_code = str(error.response.get('Error', {}).get('Code', ''))
        if error_code in {'404', 'NoSuchKey', 'NotFound'}:
            return RemoteObjectMetadata(size=None, checksum=None)
        raise RuntimeError(f'Failed to inspect s3://{bucket}/{object_key}: {error}') from error
    except BotoCoreError as error:
        raise RuntimeError(f'Failed to inspect s3://{bucket}/{object_key}: {error}') from error

    metadata = response.get('Metadata') or {}
    if not isinstance(metadata, dict):
        metadata = {}
    size = response.get('ContentLength')
    checksum = metadata.get('sha256')
    return RemoteObjectMetadata(
        size=int(size) if size is not None else None,
        checksum=str(checksum) if checksum else None,
    )


def upload_with_boto3(
    s3_client: BaseClient,
    local_path: Path,
    bucket: str,
    object_key: str,
    *,
    checksum: str,
    local_size: int,
) -> None:
    try:
        with local_path.open('rb') as file:
            s3_client.upload_fileobj(
                file,
                bucket,
                object_key,
                ExtraArgs={
                    'Metadata': {
                        'sha256': checksum,
                        'source-size': str(local_size),
                    }
                },
            )
    except (BotoCoreError, ClientError) as error:
        raise RuntimeError(f'Failed to upload s3://{bucket}/{object_key}: {error}') from error


def build_plan(args: argparse.Namespace) -> list[tuple[int, int]]:
    methods = sum((bool(args.periods), bool(args.months_file)))
    if methods > 1:
        raise ValueError('Use either --periods or --months-file, not both.')
    if args.periods:
        return normalize_periods(args.periods)
    if args.months_file:
        values = load_year_months_from_file(resolve_project_path(args.months_file))
        return normalize_periods(values)
    return []


def build_upload_items(args: argparse.Namespace) -> list[UploadItem]:
    plan = build_plan(args)
    items: list[UploadItem] = []

    if args.with_zone_lookup:
        items.append(
            UploadItem(
                local_path=LANDING_DIR / 'lookup' / 'taxi_zone_lookup.csv',
                object_key='reference/taxi_zone_lookup/taxi_zone_lookup.csv',
                label='zone lookup',
            )
        )
    if args.with_zone_centroids:
        items.append(
            UploadItem(
                local_path=LANDING_DIR / 'lookup' / 'taxi_zone_centroids.csv',
                object_key='reference/taxi_zone_centroids/taxi_zone_centroids.csv',
                label='zone centroids',
            )
        )
    for year, month in plan:
        filename = f'yellow_tripdata_{year}-{month:02d}.parquet'
        items.append(
            UploadItem(
                local_path=LANDING_DIR / 'yellow_taxi' / f'year={year}' / f'month={month:02d}' / filename,
                object_key=f'bronze/yellow_taxi/year={year}/month={month:02d}/{filename}',
                label=f'{year}-{month:02d}',
            )
        )

    if not items:
        raise ValueError('Provide month inputs or at least one reference upload flag.')

    return items


def upload_item(
    item: UploadItem,
    *,
    s3_client: BaseClient,
    bucket: str,
    force: bool,
    dry_run: bool,
) -> str:
    if not item.local_path.is_file():
        raise FileNotFoundError(f'Upload file not found: {item.local_path}')

    validate_local_artifact(item.local_path)
    local_size = item.local_path.stat().st_size
    checksum = compute_sha256(item.local_path)
    remote = read_remote_object_metadata(s3_client, bucket, item.object_key)

    if not force and remote.size == local_size and remote.checksum == checksum:
        LOGGER.info('[SKIP] %s: verified size and SHA-256', item.label)
        return 'skipped'

    if dry_run:
        LOGGER.info('[DRY-RUN] %s -> s3://%s/%s', item.label, bucket, item.object_key)
        return 'dry-run'

    LOGGER.info('[UPLOAD] %s -> s3://%s/%s', item.label, bucket, item.object_key)
    upload_with_boto3(
        s3_client,
        item.local_path,
        bucket,
        item.object_key,
        checksum=checksum,
        local_size=local_size,
    )
    return 'uploaded'


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Upload validated landing artifacts to S3.')
    parser.add_argument('--periods', '--year-months', dest='periods', nargs='+', help='Period specs: YYYY-MM, YYYY, or START:END.')
    parser.add_argument('--months-file', type=Path, help='File containing YYYY-MM values.')
    parser.add_argument('--with-zone-lookup', action='store_true')
    parser.add_argument('--with-zone-centroids', action='store_true')
    parser.add_argument('--force', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument(
        '--bucket',
        default=os.getenv('NYCTX_S3_BUCKET', ''),
        help='Destination S3 bucket. Defaults to NYCTX_S3_BUCKET.',
    )
    return parser.parse_args(argv)


def run(args: argparse.Namespace) -> None:
    if not args.bucket:
        raise ValueError('NYCTX_S3_BUCKET must be set explicitly or passed via --bucket.')

    items = build_upload_items(args)
    s3_client = build_s3_client()
    LOGGER.info('Uploading validated landing data to bucket: %s', args.bucket)
    for item in items:
        upload_item(
            item,
            s3_client=s3_client,
            bucket=args.bucket,
            force=args.force,
            dry_run=args.dry_run,
        )
    LOGGER.info('Upload completed successfully')


def main(argv: list[str] | None = None) -> None:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
    try:
        run(parse_args(argv))
    except (FileNotFoundError, RuntimeError, ValueError) as error:
        LOGGER.error('%s', error)
        raise SystemExit(1) from error


if __name__ == '__main__':
    main()
