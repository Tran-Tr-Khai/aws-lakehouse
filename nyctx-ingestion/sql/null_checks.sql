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