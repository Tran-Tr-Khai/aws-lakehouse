import argparse
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from nyctx_ingestion.quality import run_raw_quality_check


PROJECT_ROOT = Path(__file__).resolve().parents[2]
LANDING_DIR = PROJECT_ROOT / "data" / "landing"
QUALITY_DIR = PROJECT_ROOT / "data" / "quality" / "local_profile"


def resolve_project_path(path: Path) -> Path:
    if path.is_absolute():
        return path

    return PROJECT_ROOT / path


def parse_year_month(value: str) -> tuple[int, int]:
    if not re.fullmatch(r"\d{4}-\d{2}", value):
        raise ValueError(f"Invalid year-month format: {value}. Expected YYYY-MM.")

    year_text, month_text = value.split("-")
    year = int(year_text)
    month = int(month_text)

    if month < 1 or month > 12:
        raise ValueError(f"Invalid month: {month}. Month must be between 01 and 12.")

    return year, month


def load_year_months_from_file(path: Path) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(f"Months file not found: {path}")

    year_months: list[str] = []

    for line in path.read_text(encoding="utf-8").splitlines():
        value = line.strip()

        if not value or value.startswith("#"):
            continue

        year_months.append(value)

    return year_months


def get_trip_file(year: int, month: int) -> Path:
    month_str = f"{month:02d}"

    return (
        LANDING_DIR
        / "yellow_taxi"
        / f"year={year}"
        / f"month={month_str}"
        / f"yellow_tripdata_{year}-{month_str}.parquet"
    )


def get_output_dir(year: int, month: int) -> Path:
    return QUALITY_DIR / f"year={year}" / f"month={month:02d}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Profile local Bronze/Raw NYC Yellow Taxi parquet files."
    )

    parser.add_argument("--year", type=int, required=False)
    parser.add_argument("--month", type=int, required=False)

    parser.add_argument(
        "--year-months",
        type=str,
        nargs="+",
        required=False,
        help="Year-month values, example: --year-months 2019-01 2020-04.",
    )

    parser.add_argument(
        "--months-file",
        type=Path,
        required=False,
        help="Text file containing YYYY-MM values, one per line.",
    )

    parser.add_argument(
        "--write-details",
        action="store_true",
        help="Write detailed per-check CSV files under data/quality/local_profile.",
    )

    return parser.parse_args()


def build_profile_plan(args: argparse.Namespace) -> list[tuple[int, int]]:
    year_month_values: list[str] = []

    if args.year_months:
        year_month_values.extend(args.year_months)

    if args.months_file:
        year_month_values.extend(
            load_year_months_from_file(resolve_project_path(args.months_file))
        )

    if year_month_values:
        return [parse_year_month(value) for value in year_month_values]

    if args.year is not None and args.month is not None:
        if args.month < 1 or args.month > 12:
            raise ValueError(
                f"Invalid month: {args.month}. Month must be between 1 and 12."
            )

        return [(args.year, args.month)]

    raise ValueError(
        "Please provide either --year-months, --months-file, or both --year and --month."
    )


def extract_summary_value(
    profile_results: dict[str, pd.DataFrame],
    column: str,
) -> Any:
    summary_df = profile_results.get("summary")

    if summary_df is None or summary_df.empty or column not in summary_df.columns:
        return None

    return summary_df[column].iloc[0]


def get_count_from_check(
    profile_results: dict[str, pd.DataFrame],
    check_name: str,
) -> int | None:
    df = profile_results.get(check_name)

    if df is None or df.empty:
        return None

    excluded_columns = {
        "total_rows",
        "row_count",
        "period",
        "year",
        "month",
    }

    numeric_columns = [
        column
        for column in df.columns
        if column not in excluded_columns
        and pd.api.types.is_numeric_dtype(df[column])
    ]

    if not numeric_columns:
        return len(df)

    total = df[numeric_columns].sum(numeric_only=True).sum()

    return int(total)


def write_csv_outputs(
    profile_results: dict[str, pd.DataFrame],
    output_dir: Path,
) -> list[str]:
    generated_files: list[str] = []

    for name, df in profile_results.items():
        output_file = output_dir / f"{name}.csv"
        df.to_csv(output_file, index=False)
        generated_files.append(output_file.name)

    return generated_files


def build_month_summary_row(
    year: int,
    month: int,
    trip_file: Path,
    details_output_dir: Path | None,
    profile_results: dict[str, pd.DataFrame],
    generated_files: list[str],
) -> dict[str, Any]:
    total_rows = extract_summary_value(profile_results, "total_rows")
    min_pickup = extract_summary_value(profile_results, "min_pickup_datetime")
    max_pickup = extract_summary_value(profile_results, "max_pickup_datetime")
    min_dropoff = extract_summary_value(profile_results, "min_dropoff_datetime")
    max_dropoff = extract_summary_value(profile_results, "max_dropoff_datetime")

    critical_issue_count = get_count_from_check(profile_results, "critical_quality")
    warning_issue_count = get_count_from_check(profile_results, "warning_quality")

    return {
        "period": f"{year}-{month:02d}",
        "year": year,
        "month": month,
        "total_rows": int(total_rows) if total_rows is not None else None,
        "critical_issue_count": critical_issue_count,
        "warning_issue_count": warning_issue_count,
        "min_pickup_datetime": min_pickup,
        "max_pickup_datetime": max_pickup,
        "min_dropoff_datetime": min_dropoff,
        "max_dropoff_datetime": max_dropoff,
        "input_file": str(trip_file),
        "details_output_dir": str(details_output_dir) if details_output_dir else "",
        "generated_files": ", ".join(generated_files),
    }


def dataframe_to_markdown(df: pd.DataFrame) -> str:
    if df.empty:
        return "No records."

    try:
        return df.to_markdown(index=False)
    except ImportError:
        return "```text\n" + df.to_string(index=False) + "\n```"


def write_master_summary(summary_rows: list[dict[str, Any]]) -> None:
    if not summary_rows:
        return

    QUALITY_DIR.mkdir(parents=True, exist_ok=True)

    summary_df = pd.DataFrame(summary_rows).sort_values(["year", "month"])

    csv_path = QUALITY_DIR / "bronze_quality_summary.csv"
    md_path = QUALITY_DIR / "bronze_quality_summary.md"

    summary_df.to_csv(csv_path, index=False)

    report_columns = [
        "period",
        "total_rows",
        "critical_issue_count",
        "warning_issue_count",
        "min_pickup_datetime",
        "max_pickup_datetime",
        "details_output_dir",
    ]

    report_df = summary_df[report_columns].copy()

    lines = [
        "# Bronze Quality Summary",
        "",
        f"Generated at: `{datetime.now(timezone.utc).isoformat()}`",
        "",
        "## Monthly Profiling Summary",
        "",
        dataframe_to_markdown(report_df),
        "",
        "## Output Files",
        "",
        f"- CSV summary: `{csv_path}`",
        "- Detailed CSV outputs are only written when `--write-details` is used.",
        "",
    ]

    md_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"[SUMMARY] {csv_path}")
    print(f"[SUMMARY] {md_path}")


def profile_month(year: int, month: int, write_details: bool) -> dict[str, Any]:
    month_str = f"{month:02d}"
    period = f"{year}-{month_str}"

    trip_file = get_trip_file(year, month)

    if not trip_file.exists():
        raise FileNotFoundError(f"Trip file not found: {trip_file}")

    print("[INFO] step=profile_bronze status=started")
    print(f"[INFO] period={period}")
    print(f"[INFO] input_path={trip_file}")
    print(f"[INFO] write_details={str(write_details).lower()}")

    profile_results = run_raw_quality_check(trip_file)
    generated_files: list[str] = []
    details_output_dir: Path | None = None

    if write_details:
        details_output_dir = get_output_dir(year, month)
        details_output_dir.mkdir(parents=True, exist_ok=True)
        generated_files = write_csv_outputs(profile_results, details_output_dir)

        for file_name in generated_files:
            print(f"[INFO] detail_output={details_output_dir / file_name}")

    summary_row = build_month_summary_row(
        year=year,
        month=month,
        trip_file=trip_file,
        details_output_dir=details_output_dir,
        profile_results=profile_results,
        generated_files=generated_files,
    )

    print(
        "[INFO] "
        f"period={period} "
        f"total_rows={summary_row['total_rows']} "
        f"critical_issue_count={summary_row['critical_issue_count']} "
        f"warning_issue_count={summary_row['warning_issue_count']}"
    )

    if summary_row["critical_issue_count"]:
        print(
            "[WARNING] "
            f"period={period} "
            f"critical_issue_count={summary_row['critical_issue_count']}"
        )

    if summary_row["warning_issue_count"]:
        print(
            "[WARNING] "
            f"period={period} "
            f"warning_issue_count={summary_row['warning_issue_count']}"
        )

    print("[INFO] step=profile_bronze status=completed")

    return summary_row


def main() -> None:
    args = parse_args()
    profile_plan = build_profile_plan(args)

    print(f"[PLAN] {len(profile_plan)} month(s) to profile")
    print(f"[INFO] write_details={str(args.write_details).lower()}")

    summary_rows: list[dict[str, Any]] = []

    for year, month in profile_plan:
        print(f"[PROFILE] {year}-{month:02d}")
        summary_rows.append(profile_month(year, month, args.write_details))

    write_master_summary(summary_rows)

    print("[DONE] Bronze profiling completed successfully.")


if __name__ == "__main__":
    main()
