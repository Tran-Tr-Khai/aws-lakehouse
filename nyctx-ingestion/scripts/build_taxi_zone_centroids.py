from __future__ import annotations

import argparse
import csv
import io
import zipfile
from pathlib import Path

import requests
import shapefile
from pyproj import Transformer


TAXI_ZONES_ZIP_URL = "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zones.zip"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
LANDING_LOOKUP_DIR = PROJECT_ROOT / "data" / "landing" / "lookup"
DEFAULT_ZIP_PATH = LANDING_LOOKUP_DIR / "taxi_zones.zip"
DEFAULT_OUTPUT_PATH = LANDING_LOOKUP_DIR / "taxi_zone_centroids.csv"

SOURCE_CRS = "EPSG:2263"
TARGET_CRS = "EPSG:4326"


def download_zip(source_url: str, zip_path: Path) -> None:
    if zip_path.exists():
        print(f"[SKIP] Taxi zone shapefile already exists: {zip_path}")
        return

    zip_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"[DOWNLOAD] {source_url}")
    print(f"[SAVE TO]  {zip_path}")

    with requests.get(source_url, stream=True, timeout=120) as response:
        response.raise_for_status()

        with open(zip_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    file.write(chunk)

    print(f"[DONE] {zip_path}")


def ring_centroid(points: list[tuple[float, float]]) -> tuple[float, float, float] | None:
    if len(points) < 3:
        return None

    if points[0] != points[-1]:
        points = [*points, points[0]]

    area2 = 0.0
    centroid_x_sum = 0.0
    centroid_y_sum = 0.0

    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        cross = x0 * y1 - x1 * y0
        area2 += cross
        centroid_x_sum += (x0 + x1) * cross
        centroid_y_sum += (y0 + y1) * cross

    if abs(area2) < 1e-9:
        return None

    centroid_x = centroid_x_sum / (3.0 * area2)
    centroid_y = centroid_y_sum / (3.0 * area2)
    signed_area = area2 / 2.0

    return signed_area, centroid_x, centroid_y


def shape_centroid(shape: shapefile.Shape) -> tuple[float, float]:
    points = [(float(x), float(y)) for x, y in shape.points]
    part_starts = [*shape.parts, len(points)]

    area_total = 0.0
    weighted_x = 0.0
    weighted_y = 0.0

    for start, end in zip(part_starts, part_starts[1:]):
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
    with zipfile.ZipFile(zip_path) as archive:
        names_by_suffix = {
            Path(name).suffix.lower(): name
            for name in archive.namelist()
            if Path(name).stem == "taxi_zones"
        }

        required_suffixes = [".shp", ".shx", ".dbf"]
        missing = [suffix for suffix in required_suffixes if suffix not in names_by_suffix]
        if missing:
            raise FileNotFoundError(
                f"Taxi zones zip is missing required shapefile members: {missing}"
            )

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
) -> None:
    if output_path.exists() and not force:
        print(f"[SKIP] Taxi zone centroids already exist: {output_path}")
        return

    download_zip(source_url=source_url, zip_path=zip_path)

    reader = open_shapefile_from_zip(zip_path)
    field_names = [field[0].lower() for field in reader.fields[1:]]

    try:
        location_id_index = field_names.index("locationid")
    except ValueError as exc:
        raise ValueError("Taxi zones shapefile does not contain LocationID.") from exc

    transformer = Transformer.from_crs(SOURCE_CRS, TARGET_CRS, always_xy=True)
    rows: list[dict[str, str | int]] = []

    for record, shape in zip(reader.records(), reader.shapes()):
        location_id = int(record[location_id_index])
        centroid_x, centroid_y = shape_centroid(shape)
        longitude, latitude = transformer.transform(centroid_x, centroid_y)

        rows.append(
            {
                "location_id": location_id,
                "latitude": f"{latitude:.8f}",
                "longitude": f"{longitude:.8f}",
            }
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["location_id", "latitude", "longitude"],
        )
        writer.writeheader()
        writer.writerows(sorted(rows, key=lambda row: int(row["location_id"])))

    print(f"[DONE] Taxi zone centroids written: {output_path}")
    print(f"[INFO] centroid_count={len(rows)} source_crs={SOURCE_CRS} target_crs={TARGET_CRS}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build pickup-zone centroid CSV from the official TLC taxi zones shapefile."
    )
    parser.add_argument("--zip-path", type=Path, default=DEFAULT_ZIP_PATH)
    parser.add_argument("--output-path", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--source-url", default=TAXI_ZONES_ZIP_URL)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    build_taxi_zone_centroids(
        zip_path=args.zip_path,
        output_path=args.output_path,
        source_url=args.source_url,
        force=args.force,
    )


if __name__ == "__main__":
    main()
