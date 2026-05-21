from pathlib import Path

import duckdb
import pandas as pd


def run_raw_quality_check(trip_file: Path) -> dict[str, pd.DataFrame]:
    """
    Profile raw/bronze NYC Yellow Taxi data before Silver transformation.

    This function does not clean or modify data.
    It only measures data quality issues and domain distributions.
    """
    if not trip_file.exists():
        raise FileNotFoundError(f"Trip file not found: {trip_file}")

    trip_file_sql = str(trip_file).replace("'", "''")
    con = duckdb.connect()

    try:
        summary_query = f"""
        SELECT
            COUNT(*) AS total_rows,

            COUNT(DISTINCT VendorID) AS distinct_vendor_count,
            COUNT(DISTINCT payment_type) AS distinct_payment_type_count,
            COUNT(DISTINCT RatecodeID) AS distinct_ratecode_count,
            COUNT(DISTINCT PULocationID) AS distinct_pickup_location_count,
            COUNT(DISTINCT DOLocationID) AS distinct_dropoff_location_count,

            MIN(tpep_pickup_datetime) AS min_pickup_datetime,
            MAX(tpep_pickup_datetime) AS max_pickup_datetime,
            MIN(tpep_dropoff_datetime) AS min_dropoff_datetime,
            MAX(tpep_dropoff_datetime) AS max_dropoff_datetime,

            MIN(trip_distance) AS min_trip_distance,
            MAX(trip_distance) AS max_trip_distance,
            AVG(trip_distance) AS avg_trip_distance,

            MIN(fare_amount) AS min_fare_amount,
            MAX(fare_amount) AS max_fare_amount,
            AVG(fare_amount) AS avg_fare_amount,

            MIN(total_amount) AS min_total_amount,
            MAX(total_amount) AS max_total_amount,
            AVG(total_amount) AS avg_total_amount

        FROM read_parquet('{trip_file_sql}');
        """

        null_check_query = f"""
        SELECT
            SUM(CASE WHEN VendorID IS NULL THEN 1 ELSE 0 END) AS null_vendor_id,
            SUM(CASE WHEN tpep_pickup_datetime IS NULL THEN 1 ELSE 0 END) AS null_pickup_datetime,
            SUM(CASE WHEN tpep_dropoff_datetime IS NULL THEN 1 ELSE 0 END) AS null_dropoff_datetime,
            SUM(CASE WHEN passenger_count IS NULL THEN 1 ELSE 0 END) AS null_passenger_count,
            SUM(CASE WHEN trip_distance IS NULL THEN 1 ELSE 0 END) AS null_trip_distance,
            SUM(CASE WHEN RatecodeID IS NULL THEN 1 ELSE 0 END) AS null_ratecode_id,
            SUM(CASE WHEN store_and_fwd_flag IS NULL THEN 1 ELSE 0 END) AS null_store_and_fwd_flag,
            SUM(CASE WHEN PULocationID IS NULL THEN 1 ELSE 0 END) AS null_pickup_location_id,
            SUM(CASE WHEN DOLocationID IS NULL THEN 1 ELSE 0 END) AS null_dropoff_location_id,
            SUM(CASE WHEN payment_type IS NULL THEN 1 ELSE 0 END) AS null_payment_type,
            SUM(CASE WHEN fare_amount IS NULL THEN 1 ELSE 0 END) AS null_fare_amount,
            SUM(CASE WHEN total_amount IS NULL THEN 1 ELSE 0 END) AS null_total_amount
        FROM read_parquet('{trip_file_sql}');
        """

        critical_quality_query = f"""
        SELECT
            COUNT(*) AS total_rows,

            SUM(
                CASE
                    WHEN tpep_pickup_datetime IS NULL
                      OR tpep_dropoff_datetime IS NULL
                      OR tpep_dropoff_datetime <= tpep_pickup_datetime
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
                    WHEN passenger_count IS NULL
                      OR passenger_count <= 0
                    THEN 1 ELSE 0
                END
            ) AS invalid_passenger_count,

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

            SUM(CASE WHEN PULocationID IS NULL THEN 1 ELSE 0 END) AS null_pickup_location_count,
            SUM(CASE WHEN DOLocationID IS NULL THEN 1 ELSE 0 END) AS null_dropoff_location_count,
            SUM(CASE WHEN payment_type IS NULL THEN 1 ELSE 0 END) AS null_payment_type_count

        FROM read_parquet('{trip_file_sql}');
        """

        warning_quality_query = f"""
        SELECT
            SUM(
                CASE
                    WHEN VendorID IS NOT NULL
                     AND VendorID NOT IN (1, 2)
                    THEN 1 ELSE 0
                END
            ) AS invalid_vendor_count,

            SUM(
                CASE
                    WHEN payment_type IS NOT NULL
                     AND payment_type NOT IN (1, 2, 3, 4, 5, 6)
                    THEN 1 ELSE 0
                END
            ) AS invalid_payment_type_domain_count,

            SUM(
                CASE
                    WHEN RatecodeID IS NOT NULL
                     AND RatecodeID NOT IN (1, 2, 3, 4, 5, 6, 99)
                    THEN 1 ELSE 0
                END
            ) AS invalid_ratecode_count,

            SUM(
                CASE
                    WHEN store_and_fwd_flag IS NOT NULL
                     AND store_and_fwd_flag NOT IN ('Y', 'N')
                    THEN 1 ELSE 0
                END
            ) AS invalid_store_and_fwd_flag_count,

            SUM(CASE WHEN extra < 0 THEN 1 ELSE 0 END) AS negative_extra_count,
            SUM(CASE WHEN mta_tax < 0 THEN 1 ELSE 0 END) AS negative_mta_tax_count,
            SUM(CASE WHEN tip_amount < 0 THEN 1 ELSE 0 END) AS negative_tip_count,
            SUM(CASE WHEN tolls_amount < 0 THEN 1 ELSE 0 END) AS negative_tolls_count,
            SUM(CASE WHEN improvement_surcharge < 0 THEN 1 ELSE 0 END) AS negative_improvement_surcharge_count,
            SUM(CASE WHEN congestion_surcharge < 0 THEN 1 ELSE 0 END) AS negative_congestion_surcharge_count,
            SUM(CASE WHEN Airport_fee < 0 THEN 1 ELSE 0 END) AS negative_airport_fee_count,

            SUM(
                CASE
                    WHEN PULocationID IS NOT NULL
                     AND (PULocationID < 1 OR PULocationID > 265)
                    THEN 1 ELSE 0
                END
            ) AS pickup_location_out_of_range_count,

            SUM(
                CASE
                    WHEN DOLocationID IS NOT NULL
                     AND (DOLocationID < 1 OR DOLocationID > 265)
                    THEN 1 ELSE 0
                END
            ) AS dropoff_location_out_of_range_count,

            SUM(CASE WHEN trip_distance > 100 THEN 1 ELSE 0 END) AS very_long_distance_count,

            SUM(
                CASE
                    WHEN date_diff('minute', tpep_pickup_datetime, tpep_dropoff_datetime) > 1440
                    THEN 1 ELSE 0
                END
            ) AS very_long_duration_count

        FROM read_parquet('{trip_file_sql}');
        """

        payment_distribution_query = f"""
        SELECT
            payment_type,
            COUNT(*) AS total_rows
        FROM read_parquet('{trip_file_sql}')
        GROUP BY payment_type
        ORDER BY payment_type;
        """

        ratecode_distribution_query = f"""
        SELECT
            RatecodeID,
            COUNT(*) AS total_rows
        FROM read_parquet('{trip_file_sql}')
        GROUP BY RatecodeID
        ORDER BY RatecodeID;
        """

        vendor_distribution_query = f"""
        SELECT
            VendorID,
            COUNT(*) AS total_rows
        FROM read_parquet('{trip_file_sql}')
        GROUP BY VendorID
        ORDER BY VendorID;
        """

        store_and_fwd_distribution_query = f"""
        SELECT
            store_and_fwd_flag,
            COUNT(*) AS total_rows
        FROM read_parquet('{trip_file_sql}')
        GROUP BY store_and_fwd_flag
        ORDER BY store_and_fwd_flag;
        """

        return {
            "summary": con.execute(summary_query).fetchdf(),
            "null_checks": con.execute(null_check_query).fetchdf(),
            "critical_quality": con.execute(critical_quality_query).fetchdf(),
            "warning_quality": con.execute(warning_quality_query).fetchdf(),
            "payment_type_distribution": con.execute(payment_distribution_query).fetchdf(),
            "ratecode_distribution": con.execute(ratecode_distribution_query).fetchdf(),
            "vendor_distribution": con.execute(vendor_distribution_query).fetchdf(),
            "store_and_fwd_distribution": con.execute(store_and_fwd_distribution_query).fetchdf(),
        }

    finally:
        con.close()