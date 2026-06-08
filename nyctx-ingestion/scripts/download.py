from pathlib import Path
import argparse
import re
import requests
import logging

BASE_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data"
ZONE_LOOKUP_URL = "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv"

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LANDING_DIR = PROJECT_ROOT / "data" / "landing"


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()         
    ]
)

def resolve_project_path(path: Path) -> Path:
    if path.is_absolute():
        return path

    return PROJECT_ROOT / path


def download_file(url: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # get metadata 
    try: 
        header_response = requests.head(url, timeout=10)
        server_file_size = int(header_response.headers.get("Content-Length", 0)) 
    except requests.RequestException as e: 
        logging.error(f"Failed to fetch metadata from server: {e}")
        raise e
    
    # Check file có tồn tại vs kích thước có phù hợp hay không.
    if output_path.exists():
        local_file_size = output_path.stat().st_size
        if local_file_size == server_file_size and server_file_size > 0: 
            logging.info("File already exists and fit sizes")
            return
        else: 
            logging.warning(
                f"File mismatch or corrupted! (Local: {local_file_size} bytes, Server: {server_file_size} bytes). Deleting and redownloading..."
            )
            output_path.unlink() #Xóa file lỗi


    logging.info(f"Starting download from URL: {url}")
    logging.info(f"Saving data to path: {output_path}")

    try: 
        with requests.get(url, stream=True, timeout=120) as response:
            response.raise_for_status()

            with open(output_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        file.write(chunk)
        logging.info(f"Successfully downloaded file: {output_path}")
    except requests.RequestException as e: 
        logging.error(f"Critical error occurred during download: {e}")
        raise e

def download_yellow_taxi_month(year: int, month: int) -> None:
    filename = f"yellow_tripdata_{year}-{month:02d}.parquet"
    url = f"{BASE_URL}/{filename}"

    output_path = (
        LANDING_DIR
        / "yellow_taxi"
        / f"year={year}"
        / f"month={month:02d}"
        / filename
    )

    download_file(url, output_path)


def download_zone_lookup() -> None:
    output_path = LANDING_DIR / "lookup" / "taxi_zone_lookup.csv"
    download_file(ZONE_LOOKUP_URL, output_path)


def download_zone_centroids(force: bool = False) -> None:
    from build_taxi_zone_centroids import build_taxi_zone_centroids

    build_taxi_zone_centroids(
        zip_path=LANDING_DIR / "lookup" / "taxi_zones.zip",
        output_path=LANDING_DIR / "lookup" / "taxi_zone_centroids.csv",
        force=force,
    )


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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download NYC Yellow Taxi monthly parquet files."
    )

    parser.add_argument("--year", type=int, required=False, help="Year to download, example: 2024")
    parser.add_argument("--months", type=int, nargs="+", required=False, help="Months to download with --year")
    parser.add_argument("--year-months", type=str, nargs="+", required=False, help="Year-month values to download")
    parser.add_argument("--months-file", type=Path, required=False, help="Text file containing YYYY-MM values")
    parser.add_argument("--with-zone-lookup", action="store_true", help="Download taxi zone lookup CSV.")
    parser.add_argument("--with-zone-centroids", action="store_true", help="Build taxi zone centroid CSV.")
    parser.add_argument("--force-reference", action="store_true", help="Regenerate local reference outputs.")

    return parser.parse_args()


def build_download_plan(args: argparse.Namespace) -> list[tuple[int, int]]:
    if args.year_months and (args.year or args.months):
        raise ValueError("Only 1 method, not add > 1 method.")

    year_month_values: list[str] = []

    if args.year_months:
        year_month_values.extend(args.year_months)

    if args.months_file:
        year_month_values.extend(
            load_year_months_from_file(resolve_project_path(args.months_file))
        )

    if year_month_values:
        return [parse_year_month(value) for value in year_month_values]

    if args.year is not None and args.months:
        plan = []

        for month in args.months:
            if month < 1 or month > 12:
                raise ValueError(
                    f"Invalid month: {month}. Month must be between 1 and 12."
                )

            plan.append((args.year, month))

        return plan

    raise ValueError(
        "Please provide either --year-months, --months-file, or both --year and --months."
    )


def main() -> None:
    args = parse_args()

    if args.with_zone_lookup:
        download_zone_lookup()

    if args.with_zone_centroids:
        download_zone_centroids(force=args.force_reference)

    has_month_inputs = bool(args.year_months or args.months_file or (args.year and args.months))

    if not has_month_inputs:
        if args.with_zone_lookup or args.with_zone_centroids:
            logging.info("Execution plan complete: 0 month(s) to download (Reference flags processed).")
            return
        raise ValueError(
            "Please provide month inputs or at least one reference download flag."
        )

    download_plan = build_download_plan(args)
    logging.info(f"Execution plan created successfully: {len(download_plan)} month(s) scheduled for download.")

    for year, month in download_plan:
        download_yellow_taxi_month(year=year, month=month)


if __name__ == "__main__":
    main()
