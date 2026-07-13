"""Build taxi-zone centroid reference data from the TLC shapefile."""

from __future__ import annotations

import argparse
import csv
import io
import logging
import os
import zipfile
from pathlib import Path

import requests
import shapefile
from pyproj import Transformer

from nyctx_ingestion.paths import LANDING_DIR

LOGGER = logging.getLogger(__name__)

TAXI_ZONES_ZIP_URL = "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zones.zip"
DEFAULT_ZIP_PATH = LANDING_DIR / "lookup" / "taxi_zones.zip"
DEFAULT_OUTPUT_PATH = LANDING_DIR / "lookup" / "taxi_zone_centroids.csv"
SOURCE_CRS = "EPSG:2263"
TARGET_CRS = "EPSG:4326"


def ring_centroid(points: list[tuple[float, float]]) -> tuple[float, float, float] | None:
    """Return signed area and centroid for a polygon ring."""
    if len(points) < 3:
        return None
    closed_points = points if points[0] == points[-1] else [*points, points[0]]
    area2 = centroid_x_sum = centroid_y_sum = 0.0
    for (x0, y0), (x1, y1) in zip(closed_points, closed_points[1:], strict=False):
        cross = x0 * y1 - x1 * y0
        area2 += cross
        centroid_x_sum += (x0 + x1) * cross
        centroid_y_sum += (y0 + y1) * cross
    if abs(area2) < 1e-9:
        return None
    return area2 / 2.0, centroid_x_sum / (3.0 * area2), centroid_y_sum / (3.0 * area2)


def shape_centroid(shape: shapefile.Shape) -> tuple[float, float]:
    """Calculate an area-weighted centroid for a multipart shape."""
    points = [(float(x), float(y)) for x, y in shape.points]
    part_starts = [*shape.parts, len(points)]
    area_total = weighted_x = weighted_y = 0.0
    for start, end in zip(part_starts, part_starts[1:], strict=False):
        result = ring_centroid(points[start:end])
        if result is None:
            continue
        area, centroid_x, centroid_y = result
        area_total += area
        weighted_x += centroid_x * area
        weighted_y += centroid_y * area
    if abs(area_total) >= 1e-9:
        return weighted_x / area_total, weighted_y / area_total
    xmin, ymin, xmax, ymax = shape.bbox
    return (xmin + xmax) / 2.0, (ymin + ymax) / 2.0


def open_shapefile_from_zip(zip_path: Path) -> shapefile.Reader:
    """Open the required shapefile members directly from a validated ZIP."""
    with zipfile.ZipFile(zip_path) as archive:
        names_by_suffix = {
            Path(name).suffix.lower(): name
            for name in archive.namelist()
            if Path(name).stem == "taxi_zones"
        }
        missing = [suffix for suffix in (".shp", ".shx", ".dbf") if suffix not in names_by_suffix]
        if missing:
            raise FileNotFoundError(f"Taxi zones ZIP is missing members: {missing}")
        return shapefile.Reader(
            shp=io.BytesIO(archive.read(names_by_suffix[".shp"])),
            shx=io.BytesIO(archive.read(names_by_suffix[".shx"])),
            dbf=io.BytesIO(archive.read(names_by_suffix[".dbf"])),
            encoding="latin1",
        )


def build_taxi_zone_centroids(
    zip_path: Path = DEFAULT_ZIP_PATH,
    output_path: Path = DEFAULT_OUTPUT_PATH,
    source_url: str = TAXI_ZONES_ZIP_URL,
    force: bool = False,
    session: requests.Session | None = None,
) -> None:
    """Download source data and atomically publish the centroid CSV."""
    if output_path.exists() and not force:
        LOGGER.info("Taxi zone centroids already exist: %s", output_path)
        return

    # Local import prevents a module cycle at import time.
    from nyctx_ingestion.download import download_file

    download_file(source_url, zip_path, force=force, session=session)
    reader = open_shapefile_from_zip(zip_path)
    try:
        field_names = [field[0].lower() for field in reader.fields[1:]]
        try:
            location_id_index = field_names.index("locationid")
        except ValueError as exc:
            raise ValueError("Taxi zones shapefile does not contain LocationID.") from exc

        transformer = Transformer.from_crs(SOURCE_CRS, TARGET_CRS, always_xy=True)
        rows: list[dict[str, str | int]] = []
        for record, shape in zip(reader.records(), reader.shapes(), strict=True):
            centroid_x, centroid_y = shape_centroid(shape)
            longitude, latitude = transformer.transform(centroid_x, centroid_y)
            rows.append(
                {
                    "location_id": int(record[location_id_index]),
                    "latitude": f"{latitude:.8f}",
                    "longitude": f"{longitude:.8f}",
                }
            )
    finally:
        reader.close()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_name(f"{output_path.name}.part")
    try:
        with temporary_path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=["location_id", "latitude", "longitude"])
            writer.writeheader()
            writer.writerows(sorted(rows, key=lambda row: int(row["location_id"])))
            file.flush()
            os.fsync(file.fileno())
        temporary_path.replace(output_path)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise
    LOGGER.info("Centroids written: path=%s count=%d", output_path, len(rows))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build TLC taxi-zone centroid reference data.")
    parser.add_argument("--zip-path", type=Path, default=DEFAULT_ZIP_PATH)
    parser.add_argument("--output-path", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--source-url", default=TAXI_ZONES_ZIP_URL)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    args = parse_args(argv)
    build_taxi_zone_centroids(args.zip_path, args.output_path, args.source_url, args.force)


if __name__ == "__main__":
    main()
