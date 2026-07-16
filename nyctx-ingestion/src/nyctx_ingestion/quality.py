"""Local Bronze data profiling and configurable quality gates."""

from __future__ import annotations

import argparse
import logging
import os
from datetime import UTC, datetime
from importlib.resources import files
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

from nyctx_ingestion.paths import COMPONENT_ROOT, LANDING_DIR, QUALITY_DIR, resolve_project_path
from nyctx_ingestion.periods import load_year_months_from_file, normalize_periods

LOGGER = logging.getLogger(__name__)
SQL_DIR = COMPONENT_ROOT / "sql"

QUERIES = {
    "summary": "summary.sql",
    "null_checks": "null_checks.sql",
    "critical_quality": "critical_quality.sql",
    "warning_quality": "warning_quality.sql",
    "payment_type_distribution": "payment_distribution.sql",
    "ratecode_distribution": "ratecode_distribution.sql",
    "vendor_distribution": "vendor_distribution.sql",
    "store_and_fwd_distribution": "store_and_fwd_distribution.sql",
}


class QualityGateError(RuntimeError):
    """Raised when a configured Bronze quality threshold is exceeded."""


def get_trip_file(year: int, month: int) -> Path:
    filename = f"yellow_tripdata_{year}-{month:02d}.parquet"
    return LANDING_DIR / "yellow_taxi" / f"year={year}" / f"month={month:02d}" / filename


def load_query(sql_filename: str, **values: str) -> str:
    """Load a trusted SQL template and escape string substitutions."""
    packaged_sql = files("nyctx_ingestion").joinpath("sql", sql_filename)
    if packaged_sql.is_file():
        template = packaged_sql.read_text(encoding="utf-8")
    else:
        sql_file = SQL_DIR / sql_filename
        if not sql_file.is_file():
            raise FileNotFoundError(f"SQL template not found: {sql_file}")
        template = sql_file.read_text(encoding="utf-8")

    escaped = {key: value.replace("'", "''") for key, value in values.items()}
    return template.format(**escaped)


def run_raw_quality_check(year: int, month: int, trip_file: Path) -> dict[str, pd.DataFrame]:
    """Execute all profiling queries against a monthly Parquet file."""
    if not trip_file.is_file():
        raise FileNotFoundError(f"Trip file not found: {trip_file}")

    start = datetime(year, month, 1)
    end = datetime(year + (month == 12), month % 12 + 1, 1)
    values = {
        "trip_file_sql": str(trip_file),
        "partition_start": start.isoformat(sep=" "),
        "partition_end": end.isoformat(sep=" "),
    }
    with duckdb.connect() as connection:
        return {
            name: connection.execute(load_query(filename, **values)).fetchdf()
            for name, filename in QUERIES.items()
        }


def first_value(frame: pd.DataFrame | None, column: str) -> Any:
    if frame is None or frame.empty or column not in frame.columns:
        return None
    return frame[column].iloc[0]


def sum_violation_counts(frame: pd.DataFrame | None, aggregate_column: str) -> int:
    if frame is None or frame.empty:
        return 0
    excluded = {"total_rows", aggregate_column}
    columns = [
        column for column in frame.columns if column.endswith("_count") and column not in excluded
    ]
    return int(frame[columns].sum(numeric_only=True).sum()) if columns else 0


def build_month_summary(
    year: int,
    month: int,
    trip_file: Path,
    results: dict[str, pd.DataFrame],
    details_dir: Path | None,
) -> dict[str, Any]:
    summary = results.get("summary")
    critical = results.get("critical_quality")
    warning = results.get("warning_quality")
    total_rows = int(first_value(summary, "total_rows") or 0)
    critical_rows = int(first_value(critical, "critical_row_count") or 0)
    warning_rows = int(first_value(warning, "warning_row_count") or 0)
    return {
        "period": f"{year}-{month:02d}",
        "year": year,
        "month": month,
        "total_rows": total_rows,
        "critical_row_count": critical_rows,
        "critical_row_ratio": critical_rows / total_rows if total_rows else 0.0,
        "critical_issue_count": sum_violation_counts(critical, "critical_row_count"),
        "warning_row_count": warning_rows,
        "warning_row_ratio": warning_rows / total_rows if total_rows else 0.0,
        "warning_issue_count": sum_violation_counts(warning, "warning_row_count"),
        "min_pickup_datetime": first_value(summary, "min_pickup_datetime"),
        "max_pickup_datetime": first_value(summary, "max_pickup_datetime"),
        "input_file": str(trip_file),
        "details_output_dir": str(details_dir) if details_dir else "",
    }


def profile_month(
    year: int,
    month: int,
    *,
    output_dir: Path,
    write_details: bool,
) -> dict[str, Any]:
    period = f"{year}-{month:02d}"
    trip_file = get_trip_file(year, month)
    LOGGER.info("Profiling Bronze data: period=%s input=%s", period, trip_file)
    results = run_raw_quality_check(year, month, trip_file)
    details_dir = output_dir / f"year={year}" / f"month={month:02d}" if write_details else None
    if details_dir:
        details_dir.mkdir(parents=True, exist_ok=True)
        for name, frame in results.items():
            frame.to_csv(details_dir / f"{name}.csv", index=False)
    summary = build_month_summary(year, month, trip_file, results, details_dir)
    LOGGER.info(
        "Profile complete: period=%s rows=%d critical_rows=%d warning_rows=%d",
        period,
        summary["total_rows"],
        summary["critical_row_count"],
        summary["warning_row_count"],
    )
    return summary


def write_summary(summary_rows: list[dict[str, Any]], output_dir: Path) -> None:
    """Atomically write CSV and Markdown summaries for one isolated run."""
    frame = pd.DataFrame(summary_rows).sort_values(["year", "month"])
    csv_path = output_dir / "bronze_quality_summary.csv"
    md_path = output_dir / "bronze_quality_summary.md"
    csv_temp = csv_path.with_suffix(".csv.part")
    md_temp = md_path.with_suffix(".md.part")
    report_columns = [
        "period",
        "total_rows",
        "critical_row_count",
        "critical_row_ratio",
        "warning_row_count",
        "warning_row_ratio",
        "min_pickup_datetime",
        "max_pickup_datetime",
    ]
    frame.to_csv(csv_temp, index=False)
    markdown = frame[report_columns].to_markdown(index=False)
    generated_at = datetime.now(UTC).isoformat()
    md_temp.write_text(
        f"# Bronze Quality Summary\n\nGenerated at: `{generated_at}`\n\n{markdown}\n",
        encoding="utf-8",
    )
    csv_temp.replace(csv_path)
    md_temp.replace(md_path)
    LOGGER.info("Quality summary written: %s", output_dir)


def default_output_dir() -> Path:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S.%fZ")
    return QUALITY_DIR / f"run_id={timestamp}-{os.getpid()}"


def build_plan(args: argparse.Namespace) -> list[tuple[int, int]]:
    methods = sum(
        (
            bool(args.periods),
            bool(args.months_file),
            args.year is not None or args.month is not None,
        )
    )
    if methods != 1:
        raise ValueError(
            "Use exactly one input method: --year/--month, --periods, or --months-file."
        )
    if args.periods:
        return normalize_periods(args.periods)
    if args.months_file:
        return normalize_periods(load_year_months_from_file(resolve_project_path(args.months_file)))
    if args.year is None or args.month is None:
        raise ValueError("--year and --month must be provided together.")
    return normalize_periods([f"{args.year:04d}-{args.month:02d}"])


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Profile local Bronze NYC Taxi data.")
    parser.add_argument("--year", type=int)
    parser.add_argument("--month", type=int)
    parser.add_argument("--periods", "--year-months", dest="periods", nargs="+")
    parser.add_argument("--months-file", type=Path)
    parser.add_argument("--write-details", action="store_true")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument(
        "--max-critical-ratio",
        type=float,
        help="Fail after profiling when the distinct critical-row ratio exceeds this value.",
    )
    parser.add_argument(
        "--fail-on-critical",
        action="store_true",
        help="Equivalent to --max-critical-ratio 0.",
    )
    return parser.parse_args(argv)


def run(args: argparse.Namespace) -> Path:
    plan = build_plan(args)
    if not plan:
        raise ValueError('No valid periods were provided.')
    threshold = 0.0 if args.fail_on_critical else args.max_critical_ratio
    if threshold is not None and not 0.0 <= threshold <= 1.0:
        raise ValueError('--max-critical-ratio must be between 0 and 1.')
    output_dir = resolve_project_path(args.output_dir) if args.output_dir else default_output_dir()
    output_dir.mkdir(parents=True, exist_ok=False)
    rows = [
        profile_month(year, month, output_dir=output_dir, write_details=args.write_details)
        for year, month in plan
    ]
    write_summary(rows, output_dir)
    failures = [
        row for row in rows if threshold is not None and row['critical_row_ratio'] > threshold
    ]
    if failures:
        periods = ', '.join(row['period'] for row in failures)
        raise QualityGateError(
            f'Bronze quality gate failed for {periods}: max critical-row ratio={threshold:.4f}'
        )
    return output_dir


def main(argv: list[str] | None = None) -> None:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
    try:
        run(parse_args(argv))
    except (FileNotFoundError, QualityGateError, ValueError) as error:
        LOGGER.error('%s', error)
        raise SystemExit(1) from error


if __name__ == '__main__':
    main()
