import argparse
from pathlib import Path

from nyctx_ingestion.logger import setup_file_logger
from nyctx_ingestion.quality import run_raw_quality_check


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def get_trip_file(year: int, month: int) -> Path:
    month_str = f"{month:02d}"
    return (
        PROJECT_ROOT
        / "data"
        / "landing"
        / "yellow_taxi"
        / f"year={year}"
        / f"month={month_str}"
        / f"yellow_tripdata_{year}-{month_str}.parquet"
    )


def get_output_dir(year: int, month: int) -> Path:
    month_str = f"{month:02d}"
    return (
        PROJECT_ROOT
        / "data"
        / "quality"
        / "bronze_profile"
        / f"year={year}"
        / f"month={month_str}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Profile local Bronze/Raw NYC Yellow Taxi data using DuckDB."
    )
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--month", type=int, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    trip_file = get_trip_file(args.year, args.month)
    output_dir = get_output_dir(args.year, args.month)
    output_dir.mkdir(parents=True, exist_ok=True)

    log_file = PROJECT_ROOT / "logs" / f"raw_quality_check_{args.year}_{args.month:02d}.log"
    logger = setup_file_logger("raw_quality_check", log_file)

    logger.info("=== BRONZE LOCAL PROFILING ===")
    logger.info(f"Input file: {trip_file}")
    logger.info(f"Output dir: {output_dir}")

    profile_results = run_raw_quality_check(trip_file)

    for name, df in profile_results.items():
        output_file = output_dir / f"{name}.csv"
        df.to_csv(output_file, index=False)
        logger.info(f"[{name.upper()}] saved to {output_file}")

    logger.info("Bronze profiling completed successfully.")


if __name__ == "__main__":
    main()