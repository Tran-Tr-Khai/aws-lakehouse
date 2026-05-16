import duckdb
import pandas as pd
from pathlib import Path


def run_raw_quality_check(trip_file: Path) -> pd.DataFrame:
    if not trip_file.exists():
        raise FileNotFoundError(f"Trip file not found: {trip_file}")

    con = duckdb.connect()

    query = f"""
    SELECT
        COUNT(*) AS total_rows,

        SUM(
            CASE 
                WHEN tpep_pickup_datetime IS NULL 
                  OR tpep_dropoff_datetime IS NULL
                  OR tpep_pickup_datetime >= tpep_dropoff_datetime
                THEN 1 ELSE 0 
            END
        ) AS invalid_datetime_count,

        SUM(
            CASE 
                WHEN trip_distance IS NULL 
                  OR trip_distance <= 0
                THEN 1 ELSE 0 
            END
        ) AS invalid_distance_count,

        SUM(
            CASE 
                WHEN fare_amount IS NULL 
                  OR fare_amount < 0
                THEN 1 ELSE 0 
            END
        ) AS invalid_fare_count,

        SUM(
            CASE 
                WHEN total_amount IS NULL 
                  OR total_amount < 0
                THEN 1 ELSE 0 
            END
        ) AS invalid_total_amount_count,

        SUM(
            CASE 
                WHEN PULocationID IS NULL
                THEN 1 ELSE 0 
            END
        ) AS null_pickup_location_count,

        SUM(
            CASE 
                WHEN DOLocationID IS NULL
                THEN 1 ELSE 0 
            END
        ) AS null_dropoff_location_count,

        SUM(
            CASE 
                WHEN payment_type IS NULL
                THEN 1 ELSE 0 
            END
        ) AS null_payment_type_count,

        SUM(
            CASE 
                WHEN passenger_count IS NULL
                  OR passenger_count <= 0
                THEN 1 ELSE 0 
            END
        ) AS invalid_passenger_count

    FROM read_parquet('{trip_file}');
    """

    return con.execute(query).fetchdf()