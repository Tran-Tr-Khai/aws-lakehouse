"""Reliable downloads for NYC Taxi source data."""

from __future__ import annotations

import argparse
import logging
import os
import zipfile
from pathlib import Path

import pyarrow.parquet as parquet
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from nyctx_ingestion.centroids import build_taxi_zone_centroids
from nyctx_ingestion.paths import LANDING_DIR, resolve_project_path
from nyctx_ingestion.periods import load_year_months_from_file, normalize_periods

LOGGER = logging.getLogger(__name__)

BASE_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data"
ZONE_LOOKUP_URL = "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv"


def build_http_session() -> requests.Session:
    """Create an HTTP session with bounded retries for transient failures."""
    retry = Retry(
        total=4,
        connect=4,
        read=4,
        backoff_factor=1.0,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET", "HEAD"}),
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session = requests.Session()
    session.headers["User-Agent"] = "nyctx-ingestion/0.1"
    session.mount("https://", adapter)
    return session


def validate_download(path: Path) -> None:
    """Validate downloaded files before publishing them to the landing zone."""
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError(f"Downloaded file is empty: {path}")
    source_name = path.name.removesuffix(".part")
    if source_name.endswith(".parquet"):
        parquet.ParquetFile(path)
    elif source_name.endswith(".zip"):
        with zipfile.ZipFile(path) as archive:
            if archive.testzip() is not None:
                raise ValueError(f"Downloaded ZIP failed CRC validation: {path}")


def probe_remote_size(http: requests.Session, url: str) -> int | None:
    """Try to fetch remote size metadata without failing on HEAD-restricted origins."""
    try:
        with http.head(url, timeout=(10, 30), allow_redirects=True) as response:
            response.raise_for_status()
            content_length = response.headers.get("Content-Length")
            return int(content_length) if content_length else None
    except requests.HTTPError as error:
        status_code = error.response.status_code if error.response is not None else None
        if status_code in {403, 405}:
            LOGGER.warning(
                "HEAD probe rejected for %s with status %s; continuing without remote size",
                url,
                status_code,
            )
            return None
        raise


def download_file(
    url: str,
    output_path: Path,
    *,
    force: bool = False,
    session: requests.Session | None = None,
) -> None:
    """Download to a temporary path, validate it, and atomically publish it."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    own_session = session is None
    http = session or build_http_session()
    temporary_path = output_path.with_name(f"{output_path.name}.part")

    try:
        remote_size = probe_remote_size(http, url)

        if output_path.exists() and not force:
            size_matches = remote_size is None or output_path.stat().st_size == remote_size
            if size_matches:
                validate_download(output_path)
                LOGGER.info("File already exists with expected size: %s", output_path)
                return

        temporary_path.unlink(missing_ok=True)
        LOGGER.info("Downloading %s to %s", url, temporary_path)
        with http.get(url, stream=True, timeout=(10, 120)) as response:
            response.raise_for_status()
            with temporary_path.open("wb") as file:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        file.write(chunk)
                file.flush()
                os.fsync(file.fileno())

        if remote_size is not None and temporary_path.stat().st_size != remote_size:
            raise ValueError(
                f"Downloaded size mismatch for {url}: "
                f"expected={remote_size}, actual={temporary_path.stat().st_size}"
            )
        validate_download(temporary_path)
        temporary_path.replace(output_path)
        LOGGER.info("Download completed: %s", output_path)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise
    finally:
        if own_session:
            http.close()


def build_download_plan(args: argparse.Namespace) -> list[tuple[int, int]]:
    """Build a validated plan from exactly one month input method."""
    methods = sum(
        (
            bool(args.year_months),
            bool(args.months_file),
            args.year is not None or bool(args.months),
        )
    )
    if methods > 1:
        raise ValueError(
            "Use exactly one month input method: --year/--months, --year-months, or --months-file."
        )
    if args.year_months:
        return normalize_periods(args.year_months)
    if args.months_file:
        values = load_year_months_from_file(resolve_project_path(args.months_file))
        return normalize_periods(values)
    if args.year is not None or args.months:
        if args.year is None or not args.months:
            raise ValueError("--year and --months must be provided together.")
        return normalize_periods([f"{args.year:04d}-{month:02d}" for month in args.months])
    return []


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download NYC Yellow Taxi source data.")
    parser.add_argument("--year", type=int, help="Year to download, for example 2024.")
    parser.add_argument("--months", type=int, nargs="+", help="Months used with --year.")
    parser.add_argument("--year-months", nargs="+", help="Periods in YYYY-MM format.")
    parser.add_argument("--months-file", type=Path, help="File containing YYYY-MM values.")
    parser.add_argument("--with-zone-lookup", action="store_true")
    parser.add_argument("--with-zone-centroids", action="store_true")
    parser.add_argument("--force-reference", action="store_true")
    return parser.parse_args(argv)


def run(args: argparse.Namespace) -> None:
    plan = build_download_plan(args)
    if not plan and not (args.with_zone_lookup or args.with_zone_centroids):
        raise ValueError("Provide month inputs or at least one reference download flag.")

    with build_http_session() as session:
        if args.with_zone_lookup:
            download_file(
                ZONE_LOOKUP_URL,
                LANDING_DIR / "lookup" / "taxi_zone_lookup.csv",
                force=args.force_reference,
                session=session,
            )
        if args.with_zone_centroids:
            build_taxi_zone_centroids(
                zip_path=LANDING_DIR / "lookup" / "taxi_zones.zip",
                output_path=LANDING_DIR / "lookup" / "taxi_zone_centroids.csv",
                force=args.force_reference,
                session=session,
            )
        for year, month in plan:
            filename = f"yellow_tripdata_{year}-{month:02d}.parquet"
            output_path = (
                LANDING_DIR / "yellow_taxi" / f"year={year}" / f"month={month:02d}" / filename
            )
            download_file(f"{BASE_URL}/{filename}", output_path, session=session)

    LOGGER.info("Download plan completed: month_count=%d", len(plan))


def main(argv: list[str] | None = None) -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    run(parse_args(argv))


if __name__ == "__main__":
    main()
