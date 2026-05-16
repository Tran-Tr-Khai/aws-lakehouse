from pathlib import Path
import sys
import argparse

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from src.paths import get_yellow_taxi_landing_file, get_quality_log_file
from src.quality import run_raw_quality_check
from src.logger import setup_file_logger


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run raw quality checks for NYC Yellow Taxi data."
    )

    parser.add_argument("--year", type=int, required=True)

    parser.add_argument(
        "--months",
        type=int,
        nargs="+",
        required=True,
        help="Months to check, example: --months 1 2 3",
    )

    return parser.parse_args()


def run_one_month(year: int, month: int) -> None:
    log_file = get_quality_log_file("raw", year, month)

    logger = setup_file_logger(
        logger_name=f"raw_quality_check_{year}_{month:02d}",
        log_file=log_file,
    )

    trip_file = get_yellow_taxi_landing_file(year, month)

    logger.info(f"Running raw quality check for year={year}, month={month:02d}")
    logger.info(f"Input file: {trip_file}")

    result = run_raw_quality_check(trip_file)
    metrics = result.iloc[0].to_dict()

    logger.info(f"Total rows: {int(metrics['total_rows']):,}")
    logger.warning(f"Invalid datetime rows: {int(metrics['invalid_datetime_count']):,}")
    logger.warning(f"Invalid distance rows: {int(metrics['invalid_distance_count']):,}")
    logger.warning(f"Invalid fare rows: {int(metrics['invalid_fare_count']):,}")
    logger.warning(f"Invalid total amount rows: {int(metrics['invalid_total_amount_count']):,}")
    logger.warning(f"Null pickup location rows: {int(metrics['null_pickup_location_count']):,}")
    logger.warning(f"Null dropoff location rows: {int(metrics['null_dropoff_location_count']):,}")
    logger.warning(f"Null payment type rows: {int(metrics['null_payment_type_count']):,}")
    logger.warning(f"Invalid passenger count rows: {int(metrics['invalid_passenger_count']):,}")

    logger.info(f"Log saved to: {log_file}")
    logger.info("Raw quality check completed successfully")


def main() -> None:
    args = parse_args()

    for month in args.months:
        if month < 1 or month > 12:
            raise ValueError(f"Invalid month: {month}")

        run_one_month(args.year, month)


if __name__ == "__main__":
    main()