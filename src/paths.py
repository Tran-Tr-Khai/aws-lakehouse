from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_ROOT / "data"
LANDING_DIR = DATA_DIR / "landing"
BRONZE_DIR = DATA_DIR / "bronze"
SILVER_DIR = DATA_DIR / "silver"
GOLD_DIR = DATA_DIR / "gold"

LOG_DIR = PROJECT_ROOT / "logs"


def get_yellow_taxi_landing_file(year: int, month: int) -> Path:
    return (
        LANDING_DIR
        / "yellow_taxi"
        / f"year={year}"
        / f"month={month:02d}"
        / f"yellow_tripdata_{year}-{month:02d}.parquet"
    )


def get_zone_lookup_file() -> Path:
    return LANDING_DIR / "lookup" / "taxi_zone_lookup.csv"

def get_quality_log_file(layer: str, year: int, month: int) -> Path:
    return LOG_DIR / f"{layer}_quality_check_{year}_{month:02d}.log"