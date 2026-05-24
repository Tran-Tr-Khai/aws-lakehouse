from pathlib import Path
import argparse # thư viện để xử lý đối số dòng lệnh nếu không có sẽ phải nhập trực tiếp vào code
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download NYC Yellow Taxi monthly parquet files."
    )

    parser.add_argument(
        "--year",
        type=int,
        required=True,
        help="Year to download, example: 2024",
    )

    parser.add_argument(
        "--months",
        type=int,
        nargs="+",
        required=True,
        help="Months to download, example: --months 1 2 3",
    )

    parser.add_argument(
        "--with-zone-lookup",
        action="store_true",
        help="Download taxi zone lookup CSV.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.with_zone_lookup:
        download_zone_lookup()

    for month in args.months:
        if month < 1 or month > 12:
            raise ValueError(f"Invalid month: {month}. Month must be between 1 and 12.")

        download_yellow_taxi_month(year=args.year, month=month)


if __name__ == "__main__":
    main()