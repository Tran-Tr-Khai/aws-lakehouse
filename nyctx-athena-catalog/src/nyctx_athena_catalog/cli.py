from __future__ import annotations

import argparse
import re
from pathlib import Path

from nyctx_athena_catalog.athena import (
    AthenaQueryError,
    build_athena_client,
    fetch_single_value,
    start_query,
    wait_for_query,
)
from nyctx_athena_catalog.config import AthenaConfig

PERIOD_PATTERN = re.compile(r'^(?P<year>\d{4})-(?P<month>\d{2})$')
UNRESOLVED_PLACEHOLDER_PATTERN = re.compile(r'__NYCTX_[A-Z0-9_]+__')
YEAR_PATTERN = re.compile(r'^\d{4}$')


def build_partition_predicate(periods: list[tuple[str, str]]) -> str:
    return ' OR '.join(
        f"(year = '{year}' AND month = '{month}')"
        for year, month in periods
    )


def render_sql_template(
    template: str,
    config: AthenaConfig,
    *,
    year: str | None = None,
    month: str | None = None,
    periods: list[tuple[str, str]] | None = None,
) -> str:
    replacements = {
        '__NYCTX_ATHENA_DATABASE__': config.database,
        '__NYCTX_ATHENA_SILVER_TABLE__': config.silver_table,
        '__NYCTX_ATHENA_SILVER_LOCATION__': config.silver_location,
        '__NYCTX_ATHENA_ICEBERG_TABLE__': config.iceberg_table,
        '__NYCTX_ATHENA_ICEBERG_LOCATION__': config.iceberg_location,
        '__NYCTX_ZONE_LOOKUP_LOCATION__': config.zone_lookup_location,
        '__NYCTX_ZONE_CENTROIDS_LOCATION__': config.zone_centroids_location,
        '__NYCTX_ATHENA_YEAR_RANGE__': config.year_range,
    }

    if year is not None and month is not None:
        replacements['__NYCTX_ATHENA_QUERY_YEAR__'] = year
        replacements['__NYCTX_ATHENA_QUERY_MONTH__'] = month

    if periods:
        replacements['__NYCTX_ATHENA_PERIOD_FILTER__'] = build_partition_predicate(periods)

    rendered = template
    for placeholder, value in replacements.items():
        rendered = rendered.replace(placeholder, value)
    unresolved = sorted(set(UNRESOLVED_PLACEHOLDER_PATTERN.findall(rendered)))
    if unresolved:
        raise ValueError(f'Unresolved SQL placeholders: {", ".join(unresolved)}')

    return rendered


def load_year_months(path: Path) -> list[tuple[str, str]]:
    periods: list[tuple[str, str]] = []

    for raw_line in path.read_text(encoding='utf-8').splitlines():
        line = raw_line.split('#', 1)[0].strip()
        if not line:
            continue

        match = PERIOD_PATTERN.fullmatch(line)
        if match is None:
            raise ValueError(f'Invalid period format in {path}: {line}')

        year = match.group('year')
        month = match.group('month')
        if not 1 <= int(month) <= 12:
            raise ValueError(f'Invalid month in {path}: {line}')

        period = (year, month)
        if period in periods:
            raise ValueError(f'Duplicate period in {path}: {line}')
        periods.append(period)

    if not periods:
        raise ValueError(f'No year-month periods found in {path}')

    return periods


def resolve_query_periods(
    *,
    year: str | None,
    month: str | None,
    months_file: Path | None,
) -> list[tuple[str, str]]:
    if months_file is not None and (year is not None or month is not None):
        raise ValueError('Use either --months-file or --year/--month, not both')

    if months_file is not None:
        return load_year_months(months_file)

    if year is None and month is None:
        return []

    if year is None or month is None:
        raise ValueError('Both --year and --month are required together')

    if YEAR_PATTERN.fullmatch(year) is None:
        raise ValueError(f'Invalid year value: {year}')

    if PERIOD_PATTERN.fullmatch(f'{year}-{month}') is None:
        raise ValueError(f'Invalid year/month values: {year}-{month}')

    return [(year, month)]


def run_sql_file(
    sql_file: Path,
    label: str,
    config: AthenaConfig,
    *,
    year: str | None = None,
    month: str | None = None,
    months_file: Path | None = None,
) -> None:
    if not sql_file.is_file():
        raise FileNotFoundError(f'SQL file not found: {sql_file}')

    periods = resolve_query_periods(year=year, month=month, months_file=months_file)

    print('========================================')
    print('[INFO] step=athena_query status=started')
    print(f'[INFO] label={label}')
    print(f'[INFO] sql_file={sql_file}')
    print(f'[INFO] database={config.database}')
    print(f'[INFO] silver_table={config.silver_table}')
    print(f'[INFO] silver_location={config.silver_location}')
    print(f'[INFO] iceberg_table={config.iceberg_table}')
    print(f'[INFO] iceberg_location={config.iceberg_location}')
    print(f'[INFO] zone_lookup_location={config.zone_lookup_location}')
    print(f'[INFO] zone_centroids_location={config.zone_centroids_location}')
    print(f'[INFO] workgroup={config.workgroup}')
    print(f'[INFO] output_location={config.output_location}')
    print(f'[INFO] region={config.aws_region}')
    if months_file is not None:
        print(f'[INFO] months_file={months_file}')
        print(f'[INFO] query_periods={len(periods)}')
    elif periods:
        period_year, period_month = periods[0]
        print(f'[INFO] query_period={period_year}-{period_month}')
    print('========================================')

    render_year = None
    render_month = None
    if len(periods) == 1:
        render_year, render_month = periods[0]

    query = render_sql_template(
        sql_file.read_text(encoding='utf-8'),
        config,
        year=render_year,
        month=render_month,
        periods=periods,
    )
    client = build_athena_client(config)
    query_execution_id = start_query(client, query, config)

    print(f'[INFO] query_execution_id={query_execution_id}')

    result = wait_for_query(client, query_execution_id, config)

    print('[INFO] step=athena_query status=succeeded')
    print(f'[INFO] query_execution_id={result.query_execution_id}')
    print(f'[INFO] data_scanned_bytes={result.data_scanned_bytes}')


def validate_month_partitions(months_file: Path, config: AthenaConfig) -> None:
    if not months_file.is_file():
        raise FileNotFoundError(f'Months file not found: {months_file}')

    print('========================================')
    print('[INFO] step=validate_silver_athena status=started')
    print(f'[INFO] months_file={months_file}')
    print(f'[INFO] database={config.database}')
    print(f'[INFO] table={config.silver_table}')
    print(f'[INFO] workgroup={config.workgroup}')
    print(f'[INFO] output_location={config.output_location}')
    print(f'[INFO] region={config.aws_region}')
    print('========================================')

    periods = load_year_months(months_file)
    client = build_athena_client(config)

    for year, month in periods:
        query = f"""
SELECT
    COUNT(*) AS trip_count
FROM {config.database}.{config.silver_table}
WHERE year = '{year}'
  AND month = '{month}';
""".strip()
        query_execution_id = start_query(client, query, config)
        print(f'[INFO] period={year}-{month} query_execution_id={query_execution_id}')

        try:
            result = wait_for_query(client, query_execution_id, config)
        except AthenaQueryError as exc:
            print(f'[ERROR] period={year}-{month} validation=failed')
            raise RuntimeError(str(exc)) from exc

        row_count = fetch_single_value(client, query_execution_id)
        print(
            f'[INFO] period={year}-{month} row_count={row_count} '
            f'data_scanned_bytes={result.data_scanned_bytes}'
        )

        if row_count is None or int(row_count) <= 0:
            raise RuntimeError(
                f'period={year}-{month} validation=failed reason=no_silver_rows'
            )

        print(f'[INFO] period={year}-{month} validation=passed')

    print(f'[INFO] validated_months={len(periods)}')
    print('[INFO] step=validate_silver_athena status=succeeded')


def build_run_sql_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', required=True, type=Path)
    parser.add_argument('--label', default='athena_query')
    parser.add_argument('--year')
    parser.add_argument('--month')
    parser.add_argument('--months-file', type=Path)
    return parser


def build_validate_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument('--months-file', required=True, type=Path)
    return parser


def run_sql_main() -> None:
    args = build_run_sql_parser().parse_args()
    run_sql_file(
        args.file,
        args.label,
        AthenaConfig.from_env(),
        year=args.year,
        month=args.month,
        months_file=args.months_file,
    )


def validate_partitions_main() -> None:
    args = build_validate_parser().parse_args()
    validate_month_partitions(args.months_file, AthenaConfig.from_env())
