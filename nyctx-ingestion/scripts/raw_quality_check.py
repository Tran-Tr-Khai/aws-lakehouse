import argparse
import re
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import duckdb
import pandas as pd

# 1. Cấu hình Logging Hệ thống chuẩn Airflow
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

# Định vị các thư mục hệ thống
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[1]
SQL_DIR = PROJECT_ROOT / "nyctx-ingestion" / "sql"
LANDING_DIR = PROJECT_ROOT / "data" / "landing"
QUALITY_DIR = PROJECT_ROOT / "data" / "quality" / "local_profile"


def resolve_project_path(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


def parse_year_month(value: str) -> tuple[int, int]:
    if not re.fullmatch(r"\d{4}-\d{2}", value):
        raise ValueError(f"Invalid year-month format: {value}. Expected YYYY-MM.")
    
    year_text, month_text = value.split("-")
    year, month = int(year_text), int(month_text)
    
    if month < 1 or month > 12:
        raise ValueError(f"Invalid month: {month}. Month must be between 01 and 12.")
    return year, month


def load_year_months_from_file(path: Path) -> list[str]:
    if not path.exists():
        logging.error(f"Target months file does not exist: {path}")
        raise FileNotFoundError(f"Months file not found: {path}")
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def get_trip_file(year: int, month: int) -> Path:
    return (
        LANDING_DIR
        / "yellow_taxi"
        / f"year={year}"
        / f"month={month:02d}"
        / f"yellow_tripdata_{year}-{month:02d}.parquet"
    )


def load_and_format_query(sql_filename: str, trip_file_path: Path) -> str:
    """Đọc file SQL mẫu và format đường dẫn file dữ liệu Parquet đầu vào."""
    sql_file = SQL_DIR / sql_filename
    if not sql_file.exists():
        logging.error(f"Missing required SQL template file: {sql_file}")
        raise FileNotFoundError(f"SQL file template not found: {sql_file}")
    
    sql_template = sql_file.read_text(encoding="utf-8")
    trip_file_sql = str(trip_file_path).replace("'", "''")
    return sql_template.format(trip_file_sql=trip_file_sql)


def run_raw_quality_check(trip_file: Path) -> dict[str, pd.DataFrame]:
    """Sử dụng DuckDB in-memory quét file Parquet thông qua các file SQL mẫu."""
    if not trip_file.exists():
        logging.error(f"Target execution file not found: {trip_file}")
        raise FileNotFoundError(f"Trip file not found: {trip_file}")

    queries = {
        "summary": "summary.sql",
        "null_checks": "null_checks.sql",
        "critical_quality": "critical_quality.sql",
        "warning_quality": "warning_quality.sql",
        "payment_type_distribution": "payment_distribution.sql",
        "ratecode_distribution": "ratecode_distribution.sql",
        "vendor_distribution": "vendor_distribution.sql",
        "store_and_fwd_distribution": "store_and_fwd_distribution.sql",
    }

    con = duckdb.connect()
    try:
        logging.info(f"Executing DuckDB profiling queries on in-memory database...")
        return {
            key: con.execute(load_and_format_query(file, trip_file)).fetchdf()
            for key, file in queries.items()
        }
    except Exception as e:
        logging.error(f"DuckDB execution engine failed: {e}")
        raise e
    finally:
        con.close()


def get_count_from_check(profile_results: dict[str, pd.DataFrame], check_name: str) -> int:
    df = profile_results.get(check_name)
    if df is None or df.empty:
        return 0
    excluded = {"total_rows", "row_count", "period", "year", "month"}
    numeric_cols = [c for c in df.columns if c not in excluded and pd.api.types.is_numeric_dtype(df[c])]
    return int(df[numeric_cols].sum(numeric_only=True).sum()) if numeric_cols else len(df)


def build_month_summary_row(year: int, month: int, trip_file: Path, details_dir: Path | None, 
                            results: dict[str, pd.DataFrame], files: list[str]) -> dict[str, Any]:
    sum_df = results.get("summary")
    get_val = lambda col: sum_df[col].iloc[0] if (sum_df is not None and not sum_df.empty and col in sum_df.columns) else None
    
    return {
        "period": f"{year}-{month:02d}", "year": year, "month": month,
        "total_rows": int(get_val("total_rows")) if get_val("total_rows") is not None else None,
        "critical_issue_count": get_count_from_check(results, "critical_quality"),
        "warning_issue_count": get_count_from_check(results, "warning_quality"),
        "min_pickup_datetime": get_val("min_pickup_datetime"), "max_pickup_datetime": get_val("max_pickup_datetime"),
        "min_dropoff_datetime": get_val("min_dropoff_datetime"), "max_dropoff_datetime": get_val("max_dropoff_datetime"),
        "input_file": str(trip_file), "details_output_dir": str(details_dir) if details_dir else "",
        "generated_files": ", ".join(files),
    }


def write_master_summary(summary_rows: list[dict[str, Any]]) -> None:
    if not summary_rows:
        logging.warning("No summary rows provided. Master summary skipped.")
        return
    QUALITY_DIR.mkdir(parents=True, exist_ok=True)
    summary_df = pd.DataFrame(summary_rows).sort_values(["year", "month"])
    
    csv_path = QUALITY_DIR / "bronze_quality_summary.csv"
    md_path = QUALITY_DIR / "bronze_quality_summary.md"
    
    summary_df.to_csv(csv_path, index=False)
    
    report_cols = ["period", "total_rows", "critical_issue_count", "warning_issue_count", "min_pickup_datetime", "max_pickup_datetime", "details_output_dir"]
    try:
        md_table = summary_df[report_cols].to_markdown(index=False)
    except ImportError:
        md_table = "```text\n" + summary_df[report_cols].to_string(index=False) + "\n```"
        
    lines = [
        "# Bronze Quality Summary", "", f"Generated at: `{datetime.now(timezone.utc).isoformat()}`", "",
        "## Monthly Profiling Summary", "", md_table, "", "## Output Files", "",
        f"- CSV summary: `{csv_path}`",
        "- Detailed CSV outputs are only written when `--write-details` is used.", ""
    ]
    md_path.write_text("\n".join(lines), encoding="utf-8")
    logging.info(f"Master CSV summary generated at: {csv_path}")
    logging.info(f"Master Markdown summary generated at: {md_path}")


def profile_month(year: int, month: int, write_details: bool) -> dict[str, Any]:
    period = f"{year}-{month:02d}"
    trip_file = get_trip_file(year, month)
    
    logging.info(f"Profiling process started for period={period}")
    logging.info(f"Input data path: {trip_file}")
    
    profile_results = run_raw_quality_check(trip_file)
    generated_files, details_dir = [], None

    if write_details:
        details_dir = QUALITY_DIR / f"year={year}" / f"month={month:02d}"
        details_dir.mkdir(parents=True, exist_ok=True)
        for name, df in profile_results.items():
            out_file = details_dir / f"{name}.csv"
            df.to_csv(out_file, index=False)
            generated_files.append(out_file.name)
            logging.info(f"Detailed profile metrics written to: {out_file}")

    summary_row = build_month_summary_row(year, month, trip_file, details_dir, profile_results, generated_files)
    
    logging.info(f"Execution complete: period={period} total_rows={summary_row['total_rows']}")
    
    # Phân tầng cảnh báo rạch ròi dựa trên mức độ nghiêm trọng
    if summary_row["critical_issue_count"] > 0: 
        logging.warning(f"[CRITICAL DETECTED] period={period} found {summary_row['critical_issue_count']} critical data quality issues!")
    if summary_row["warning_issue_count"] > 0: 
        logging.info(f"[DOMAIN WARNING] period={period} found {summary_row['warning_issue_count']} slight business validation warnings.")
        
    logging.info(f"Profiling process completed for period={period}")
    return summary_row


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Profile local Bronze/Raw NYC Yellow Taxi parquet files.")
    parser.add_argument("--year", type=int, required=False)
    parser.add_argument("--month", type=int, required=False)
    parser.add_argument("--year-months", type=str, nargs="+", required=False)
    parser.add_argument("--months-file", type=Path, required=False)
    parser.add_argument("--write-details", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    year_month_values = []
    if args.year_months: year_month_values.extend(args.year_months)
    if args.months_file: year_month_values.extend(load_year_months_from_file(resolve_project_path(args.months_file)))
    
    plan = [parse_year_month(val) for val in year_month_values] if year_month_values else ([(args.year, args.month)] if args.year and args.month else [])
    if not plan:
        logging.error("No execution inputs detected. Parameters missing.")
        raise ValueError("Please provide either --year-months, --months-file, or both --year and --month.")

    logging.info(f"Profiling orchestration engine scheduled for {len(plan)} month(s).")
    summary_rows = [profile_month(y, m, args.write_details) for y, m in plan]
    write_master_summary(summary_rows)
    logging.info("Bronze data profiling pipeline executed successfully.")


if __name__ == "__main__":
    main()