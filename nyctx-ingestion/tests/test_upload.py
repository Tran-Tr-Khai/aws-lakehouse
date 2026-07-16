from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

import pytest
from botocore.exceptions import ClientError

from nyctx_ingestion.upload import (
    RemoteObjectMetadata,
    UploadItem,
    build_upload_items,
    parse_args,
    read_remote_object_metadata,
    run,
    upload_item,
    validate_local_artifact,
)


class FakeS3Client:
    def __init__(self) -> None:
        self.head_responses: dict[tuple[str, str], dict[str, Any]] = {}
        self.upload_calls: list[tuple[str, str, dict[str, Any]]] = []
        self.errors: dict[tuple[str, str], Exception] = {}

    def head_object(self, *, Bucket: str, Key: str) -> dict[str, Any]:
        if (Bucket, Key) in self.errors:
            raise self.errors[(Bucket, Key)]
        return self.head_responses[(Bucket, Key)]

    def upload_fileobj(self, fileobj: Any, bucket: str, key: str, ExtraArgs: dict[str, Any]) -> None:
        self.upload_calls.append((bucket, key, ExtraArgs))


class FakeMissingClient:
    def head_object(self, *, Bucket: str, Key: str) -> dict[str, Any]:
        raise ClientError({'Error': {'Code': '404', 'Message': 'Not Found'}}, 'HeadObject')


def make_args(**overrides: object) -> argparse.Namespace:
    values = {
        'periods': None,
        'months_file': None,
        'with_zone_lookup': False,
        'with_zone_centroids': False,
        'force': False,
        'dry_run': False,
        'bucket': 'sample-bucket',
    }
    values.update(overrides)
    return argparse.Namespace(**values)


def test_build_upload_items_rejects_empty_request() -> None:
    with pytest.raises(ValueError, match='Provide month inputs'):
        build_upload_items(make_args())


def test_build_upload_items_deduplicates_and_sorts_periods() -> None:
    items = build_upload_items(make_args(periods=['2024-02', '2024-01', '2024-02']))
    assert [item.label for item in items] == ['2024-01', '2024-02']


def test_validate_local_artifact_rejects_empty_csv(tmp_path: Path) -> None:
    path = tmp_path / 'taxi_zone_lookup.csv'
    path.write_text('', encoding='utf-8')
    with pytest.raises(ValueError, match='empty'):
        validate_local_artifact(path)


def test_read_remote_object_metadata_returns_missing_for_404() -> None:
    assert read_remote_object_metadata(FakeMissingClient(), 'bucket', 'key') == RemoteObjectMetadata(
        size=None,
        checksum=None,
    )


def test_upload_item_skips_when_remote_matches(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / 'taxi_zone_lookup.csv'
    with path.open('w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['location_id', 'zone'])
        writer.writerow(['1', 'A'])

    checksum = '7d97ac8e1b90d5dff2f4c0bdc9788f3a93c315464675734e53d1a59f0bc72b1d'
    client = FakeS3Client()
    client.head_responses[('bucket', 'reference/taxi_zone_lookup/taxi_zone_lookup.csv')] = {
        'ContentLength': path.stat().st_size,
        'Metadata': {'sha256': checksum},
    }
    monkeypatch.setattr('nyctx_ingestion.upload.compute_sha256', lambda *_args, **_kwargs: checksum)

    result = upload_item(
        UploadItem(path, 'reference/taxi_zone_lookup/taxi_zone_lookup.csv', 'zone lookup'),
        s3_client=client,
        bucket='bucket',
        force=False,
        dry_run=False,
    )
    assert result == 'skipped'
    assert client.upload_calls == []


def test_upload_item_supports_dry_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / 'taxi_zone_lookup.csv'
    path.write_text('location_id,zone\n1,A\n', encoding='utf-8')
    monkeypatch.setattr('nyctx_ingestion.upload.compute_sha256', lambda *_args, **_kwargs: 'abc')

    result = upload_item(
        UploadItem(path, 'reference/taxi_zone_lookup/taxi_zone_lookup.csv', 'zone lookup'),
        s3_client=FakeMissingClient(),
        bucket='bucket',
        force=False,
        dry_run=True,
    )
    assert result == 'dry-run'


def test_parse_args_accepts_bucket_override_and_dry_run() -> None:
    args = parse_args(['--bucket', 'demo-bucket', '--with-zone-lookup', '--dry-run'])
    assert args.bucket == 'demo-bucket'
    assert args.with_zone_lookup is True
    assert args.dry_run is True


def test_run_builds_client_once(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    path = tmp_path / 'taxi_zone_lookup.csv'
    path.write_text('location_id,zone\n1,A\n', encoding='utf-8')
    client = FakeS3Client()
    client.errors[('sample-bucket', 'reference/taxi_zone_lookup/taxi_zone_lookup.csv')] = ClientError(
        {'Error': {'Code': '404', 'Message': 'Not Found'}},
        'HeadObject',
    )

    monkeypatch.setattr('nyctx_ingestion.upload.build_s3_client', lambda: client)
    monkeypatch.setattr(
        'nyctx_ingestion.upload.build_upload_items',
        lambda _args: [UploadItem(path, 'reference/taxi_zone_lookup/taxi_zone_lookup.csv', 'zone lookup')],
    )
    monkeypatch.setattr('nyctx_ingestion.upload.compute_sha256', lambda *_args, **_kwargs: 'abc')

    run(make_args(dry_run=True))
    assert client.upload_calls == []
