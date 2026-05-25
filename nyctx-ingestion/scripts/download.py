from pathlib import Path
import argparse
import re
import requests


BASE_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data"
ZONE_LOOKUP_URL = "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv"

LANDING_DIR = Path("data/landing")


def download_file(url: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.exists():
        print(f"[SKIP] File already exists: {output_path}")
        return

    print(f"[DOWNLOAD] {url}")
    print(f"[SAVE TO]  {output_path}")

    with requests.get(url, stream=True, timeout=120) as response:
        response.raise_for_status()

        with open(output_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    file.write(chunk)

    print(f"[DONE] {output_path}")


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

    parser.add_argument(
        "--year",
        type=int,
        required=False,
        help="Year to download, example: 2024",
    )

    parser.add_argument(
        "--months",
        type=int,
        nargs="+",
        required=False,
        help="Months to download with --year, example: --months 1 2 3",
    )

    parser.add_argument(
        "--year-months",
        type=str,
        nargs="+",
        required=False,
        help="Year-month values to download, example: --year-months 2019-01 2020-04",
    )

    parser.add_argument(
        "--months-file",
        type=Path,
        required=False,
        help="Text file containing YYYY-MM values, one per line.",
    )

    parser.add_argument(
        "--with-zone-lookup",
        action="store_true",
        help="Download taxi zone lookup CSV.",
    )

    return parser.parse_args()


def build_download_plan(args: argparse.Namespace) -> list[tuple[int, int]]:
    year_month_values: list[str] = []

    if args.year_months:
        year_month_values.extend(args.year_months)

    if args.months_file:
        year_month_values.extend(load_year_months_from_file(args.months_file))

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

    download_plan = build_download_plan(args)

    print(f"[PLAN] {len(download_plan)} month(s) to download")

    for year, month in download_plan:
        download_yellow_taxi_month(year=year, month=month)


if __name__ == "__main__":
    main()