from __future__ import annotations

import os
import re
from dataclasses import dataclass


ATHENA_IDENTIFIER_PATTERN = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')
S3_BUCKET_PATTERN = re.compile(r'^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$')
YEAR_RANGE_PATTERN = re.compile(r'^(?P<start>\d{4}),(?P<end>\d{4})$')


def _ensure_trailing_slash(value: str) -> str:
    return value if value.endswith('/') else f'{value}/'


def _positive_int_from_env(name: str, default: int) -> int:
    raw_value = os.getenv(name, str(default))
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ValueError(f'{name} must be an integer, got: {raw_value}') from exc
    if value <= 0:
        raise ValueError(f'{name} must be greater than zero, got: {value}')
    return value


def _validate_identifier(name: str, value: str) -> None:
    if not ATHENA_IDENTIFIER_PATTERN.fullmatch(value):
        raise ValueError(f'{name} is not a valid unquoted Athena identifier: {value}')


def _validate_s3_uri(name: str, value: str) -> None:
    if not value.startswith('s3://') or value == 's3://':
        raise ValueError(f'{name} must be a valid s3:// URI, got: {value}')


def _validate_year_range(value: str) -> None:
    match = YEAR_RANGE_PATTERN.fullmatch(value)
    if match is None:
        raise ValueError(f'NYCTX_ATHENA_YEAR_RANGE must use YYYY,YYYY, got: {value}')
    if int(match.group('start')) > int(match.group('end')):
        raise ValueError(f'NYCTX_ATHENA_YEAR_RANGE start must not exceed end: {value}')


@dataclass(frozen=True)
class AthenaConfig:
    aws_region: str
    s3_bucket: str
    workgroup: str
    output_location: str
    database: str
    silver_table: str
    silver_location: str
    iceberg_table: str
    iceberg_location: str
    zone_lookup_location: str
    zone_centroids_location: str
    poll_seconds: int
    query_timeout_seconds: int
    year_range: str

    def __post_init__(self) -> None:
        if not self.aws_region.strip():
            raise ValueError('AWS region must not be empty')
        if not S3_BUCKET_PATTERN.fullmatch(self.s3_bucket):
            raise ValueError(f'NYCTX_S3_BUCKET is invalid: {self.s3_bucket}')
        if not self.workgroup.strip():
            raise ValueError('Athena workgroup must not be empty')
        _validate_identifier('NYCTX_ATHENA_DATABASE', self.database)
        _validate_identifier('NYCTX_ATHENA_SILVER_TABLE', self.silver_table)
        _validate_identifier('NYCTX_ATHENA_ICEBERG_TABLE', self.iceberg_table)
        _validate_s3_uri('NYCTX_ATHENA_OUTPUT_LOCATION', self.output_location)
        _validate_s3_uri('NYCTX_ATHENA_SILVER_LOCATION', self.silver_location)
        _validate_s3_uri('NYCTX_ATHENA_ICEBERG_LOCATION', self.iceberg_location)
        _validate_s3_uri('NYCTX_ZONE_LOOKUP_LOCATION', self.zone_lookup_location)
        _validate_s3_uri('NYCTX_ZONE_CENTROIDS_LOCATION', self.zone_centroids_location)
        if self.poll_seconds <= 0:
            raise ValueError('Athena poll interval must be greater than zero')
        if self.query_timeout_seconds <= 0:
            raise ValueError('Athena query timeout must be greater than zero')
        _validate_year_range(self.year_range)

    @classmethod
    def from_env(cls) -> 'AthenaConfig':
        aws_region = os.getenv('AWS_REGION') or os.getenv('AWS_DEFAULT_REGION') or 'us-east-1'
        s3_bucket = os.getenv('NYCTX_S3_BUCKET', 'nyc-taxi-lakehouse-tntk')
        return cls(
            aws_region=aws_region,
            s3_bucket=s3_bucket,
            workgroup=os.getenv('NYCTX_ATHENA_WORKGROUP', 'wg_nyc_taxi_lakehouse'),
            output_location=_ensure_trailing_slash(
                os.getenv('NYCTX_ATHENA_OUTPUT_LOCATION', f's3://{s3_bucket}/athena-results/')
            ),
            database=os.getenv('NYCTX_ATHENA_DATABASE', 'nyc_taxi_lakehouse'),
            silver_table=os.getenv('NYCTX_ATHENA_SILVER_TABLE', 'silver_yellow_taxi'),
            silver_location=_ensure_trailing_slash(
                os.getenv('NYCTX_ATHENA_SILVER_LOCATION', f's3://{s3_bucket}/silver/yellow_taxi/')
            ),
            iceberg_table=os.getenv('NYCTX_ATHENA_ICEBERG_TABLE', 'silver_yellow_taxi_iceberg'),
            iceberg_location=_ensure_trailing_slash(
                os.getenv(
                    'NYCTX_ATHENA_ICEBERG_LOCATION',
                    f's3://{s3_bucket}/silver_iceberg/yellow_taxi/',
                )
            ),
            zone_lookup_location=_ensure_trailing_slash(
                os.getenv(
                    'NYCTX_ZONE_LOOKUP_LOCATION',
                    f's3://{s3_bucket}/reference/taxi_zone_lookup/',
                )
            ),
            zone_centroids_location=_ensure_trailing_slash(
                os.getenv(
                    'NYCTX_ZONE_CENTROIDS_LOCATION',
                    f's3://{s3_bucket}/reference/taxi_zone_centroids/',
                )
            ),
            poll_seconds=_positive_int_from_env('NYCTX_ATHENA_POLL_SECONDS', 5),
            query_timeout_seconds=_positive_int_from_env(
                'NYCTX_ATHENA_QUERY_TIMEOUT_SECONDS', 1800
            ),
            year_range=os.getenv('NYCTX_ATHENA_YEAR_RANGE', '2019,2030'),
        )
