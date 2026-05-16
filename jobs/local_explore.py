from pathlib import Path
import duckdb


TRIP_FILE = Path(
    "data/landing/yellow_taxi/year=2024/month=01/yellow_tripdata_2024-01.parquet"
)

ZONE_FILE = Path("data/landing/lookup/taxi_zone_lookup.csv")


def inspect_trip_file() -> None:
    if not TRIP_FILE.exists():
        raise FileNotFoundError(f"Trip file not found: {TRIP_FILE}")

    con = duckdb.connect()

    print("=== TRIP FILE INFO ===")
    print(f"Path: {TRIP_FILE}")
    print(f"Size MB: {TRIP_FILE.stat().st_size / 1024 / 1024:.2f}")

    row_count = con.execute(
        f"""
        SELECT COUNT(*) 
        FROM read_parquet('{TRIP_FILE}')
        """
    ).fetchone()[0]

    print(f"Rows: {row_count:,}")

    print("\n=== TRIP SCHEMA ===")
    schema = con.execute(
        f"""
        DESCRIBE SELECT * 
        FROM read_parquet('{TRIP_FILE}')
        """
    ).fetchdf()
    print(schema)

    print("\n=== TRIP SAMPLE ===")
    sample = con.execute(
        f"""
        SELECT * 
        FROM read_parquet('{TRIP_FILE}')
        LIMIT 5
        """
    ).fetchdf()
    print(sample)


def inspect_zone_file() -> None:
    if not ZONE_FILE.exists():
        raise FileNotFoundError(f"Zone lookup file not found: {ZONE_FILE}")

    con = duckdb.connect()

    print("\n=== ZONE LOOKUP INFO ===")
    print(f"Path: {ZONE_FILE}")

    row_count = con.execute(
        f"""
        SELECT COUNT(*) 
        FROM read_csv_auto('{ZONE_FILE}')
        """
    ).fetchone()[0]

    print(f"Rows: {row_count:,}")

    print("\n=== ZONE SCHEMA ===")
    schema = con.execute(
        f"""
        DESCRIBE SELECT * 
        FROM read_csv_auto('{ZONE_FILE}')
        """
    ).fetchdf()
    print(schema)

    print("\n=== ZONE SAMPLE ===")
    sample = con.execute(
        f"""
        SELECT * 
        FROM read_csv_auto('{ZONE_FILE}')
        LIMIT 5
        """
    ).fetchdf()
    print(sample)


def main() -> None:
    inspect_trip_file()
    inspect_zone_file()


if __name__ == "__main__":
    main()