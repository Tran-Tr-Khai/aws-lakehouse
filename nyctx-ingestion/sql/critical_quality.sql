SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (
        WHERE tpep_pickup_datetime IS NULL
           OR tpep_dropoff_datetime IS NULL
           OR tpep_dropoff_datetime <= tpep_pickup_datetime
           OR tpep_pickup_datetime < TIMESTAMP '{partition_start}'
           OR tpep_pickup_datetime >= TIMESTAMP '{partition_end}'
           OR trip_distance IS NULL
           OR trip_distance <= 0
           OR passenger_count IS NULL
           OR passenger_count <= 0
           OR fare_amount IS NULL
           OR fare_amount < 0
           OR total_amount IS NULL
           OR total_amount < 0
           OR PULocationID IS NULL
           OR DOLocationID IS NULL
           OR payment_type IS NULL
    ) AS critical_row_count,
    COUNT(*) FILTER (
        WHERE tpep_pickup_datetime IS NULL
           OR tpep_dropoff_datetime IS NULL
           OR tpep_dropoff_datetime <= tpep_pickup_datetime
    ) AS invalid_datetime_count,
    COUNT(*) FILTER (
        WHERE tpep_pickup_datetime IS NOT NULL
          AND (
              tpep_pickup_datetime < TIMESTAMP '{partition_start}'
              OR tpep_pickup_datetime >= TIMESTAMP '{partition_end}'
          )
    ) AS outside_partition_count,
    COUNT(*) FILTER (WHERE trip_distance IS NULL OR trip_distance <= 0)
        AS invalid_distance_count,
    COUNT(*) FILTER (WHERE passenger_count IS NULL OR passenger_count <= 0)
        AS invalid_passenger_count,
    COUNT(*) FILTER (WHERE fare_amount IS NULL OR fare_amount < 0)
        AS invalid_fare_count,
    COUNT(*) FILTER (WHERE total_amount IS NULL OR total_amount < 0)
        AS invalid_total_amount_count,
    COUNT(*) FILTER (WHERE PULocationID IS NULL) AS null_pickup_location_count,
    COUNT(*) FILTER (WHERE DOLocationID IS NULL) AS null_dropoff_location_count,
    COUNT(*) FILTER (WHERE payment_type IS NULL) AS null_payment_type_count
FROM read_parquet('{trip_file_sql}');
