from pathlib import Path

import pytest

from nyctx_athena_catalog.cli import (
    load_year_months,
    render_sql_template,
    resolve_query_periods,
)
from nyctx_athena_catalog.config import AthenaConfig


def build_config() -> AthenaConfig:
    return AthenaConfig(
        aws_region='us-east-1',
        s3_bucket='bucket',
        workgroup='wg',
        output_location='s3://bucket/athena-results/',
        database='db',
        silver_table='silver_table',
        silver_location='s3://bucket/silver/',
        iceberg_table='silver_iceberg_table',
        iceberg_location='s3://bucket/silver_iceberg/',
        zone_lookup_location='s3://bucket/reference/lookup/',
        zone_centroids_location='s3://bucket/reference/centroids/',
        poll_seconds=5,
        query_timeout_seconds=1800,
        year_range='2019,2030',
    )


def test_render_sql_template_replaces_known_placeholders() -> None:
    rendered = render_sql_template(
        '__NYCTX_ATHENA_DATABASE__|'
        '__NYCTX_ATHENA_SILVER_TABLE__|'
        '__NYCTX_ATHENA_SILVER_LOCATION__|'
        '__NYCTX_ATHENA_ICEBERG_TABLE__|'
        '__NYCTX_ATHENA_ICEBERG_LOCATION__|'
        '__NYCTX_ZONE_LOOKUP_LOCATION__|'
        '__NYCTX_ZONE_CENTROIDS_LOCATION__|'
        '__NYCTX_ATHENA_YEAR_RANGE__',
        build_config(),
    )

    assert rendered == (
        'db|silver_table|s3://bucket/silver/|silver_iceberg_table|'
        's3://bucket/silver_iceberg/|s3://bucket/reference/lookup/|'
        's3://bucket/reference/centroids/|2019,2030'
    )


def test_render_sql_template_replaces_runtime_partition_placeholders() -> None:
    rendered = render_sql_template(
        "WHERE year = '__NYCTX_ATHENA_QUERY_YEAR__' AND month = '__NYCTX_ATHENA_QUERY_MONTH__'",
        build_config(),
        year='2025',
        month='06',
    )

    assert rendered == "WHERE year = '2025' AND month = '06'"


def test_render_sql_template_replaces_runtime_period_filter() -> None:
    rendered = render_sql_template(
        'WHERE __NYCTX_ATHENA_PERIOD_FILTER__',
        build_config(),
        periods=[('2024', '01'), ('2024', '02')],
    )

    assert rendered == (
        "WHERE (year = '2024' AND month = '01') OR (year = '2024' AND month = '02')"
    )


def test_load_year_months_ignores_comments_and_blanks(tmp_path: Path) -> None:
    months_file = tmp_path / 'months.txt'
    months_file.write_text('\n# comment\n2024-01\n 2024-02  # keep\n\n', encoding='utf-8')

    assert load_year_months(months_file) == [('2024', '01'), ('2024', '02')]


@pytest.mark.parametrize('period', ['2024-00', '2024-13', '2024-1', 'year-01'])
def test_load_year_months_rejects_invalid_periods(tmp_path: Path, period: str) -> None:
    months_file = tmp_path / 'months.txt'
    months_file.write_text(f'{period}\n', encoding='utf-8')

    with pytest.raises(ValueError):
        load_year_months(months_file)


def test_load_year_months_rejects_duplicate_period(tmp_path: Path) -> None:
    months_file = tmp_path / 'months.txt'
    months_file.write_text('2024-01\n2024-01\n', encoding='utf-8')

    with pytest.raises(ValueError, match='Duplicate period'):
        load_year_months(months_file)


def test_load_year_months_rejects_empty_file(tmp_path: Path) -> None:
    months_file = tmp_path / 'months.txt'
    months_file.write_text('# no periods\n', encoding='utf-8')

    with pytest.raises(ValueError, match='No year-month periods'):
        load_year_months(months_file)


def test_resolve_query_periods_accepts_single_runtime_period() -> None:
    assert resolve_query_periods(year='2024', month='07', months_file=None) == [('2024', '07')]


def test_resolve_query_periods_rejects_mixed_period_inputs(tmp_path: Path) -> None:
    months_file = tmp_path / 'months.txt'
    months_file.write_text('2024-01\n', encoding='utf-8')

    with pytest.raises(ValueError, match='either --months-file or --year/--month'):
        resolve_query_periods(year='2024', month='01', months_file=months_file)


def test_resolve_query_periods_rejects_partial_runtime_period() -> None:
    with pytest.raises(ValueError, match='Both --year and --month'):
        resolve_query_periods(year='2024', month=None, months_file=None)


def test_render_sql_template_rejects_unknown_placeholder() -> None:
    with pytest.raises(ValueError, match='__NYCTX_UNKNOWN__'):
        render_sql_template('SELECT __NYCTX_UNKNOWN__', build_config())
