SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT VendorID) AS distinct_vendor_count,
    COUNT(DISTINCT payment_type) AS distinct_payment_type_count,
    COUNT(DISTINCT RatecodeID) AS distinct_ratecode_count
FROM nyc_taxi_lakehouse.bronze_yellow_taxi
WHERE year = 2024
  AND month = 1;


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
FROM nyc_taxi_lakehouse.bronze_yellow_taxi
WHERE year = 2024
  AND month = 1;


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

SUM(CASE WHEN trip_distance IS NULL OR trip_distance <= 0 THEN 1 ELSE 0 END) AS invalid_distance_count,

SUM(CASE WHEN passenger_count IS NULL OR passenger_count <= 0 THEN 1 ELSE 0 END) AS invalid_passenger_count,

SUM(CASE WHEN fare_amount IS NULL OR fare_amount < 0 THEN 1 ELSE 0 END) AS invalid_fare_count,

SUM(CASE WHEN total_amount IS NULL OR total_amount < 0 THEN 1 ELSE 0 END) AS invalid_total_amount_count,

SUM(CASE WHEN PULocationID IS NULL THEN 1 ELSE 0 END) AS null_pickup_location_count,

SUM(CASE WHEN DOLocationID IS NULL THEN 1 ELSE 0 END) AS null_dropoff_location_count,

SUM(CASE WHEN payment_type IS NULL THEN 1 ELSE 0 END) AS null_payment_type_count
FROM nyc_taxi_lakehouse.bronze_yellow_taxi
WHERE year = 2024
    AND month = 1;


SELECT
    SUM(CASE WHEN VendorID NOT IN (1, 2) THEN 1 ELSE 0 END) AS invalid_vendor_count,

    SUM(CASE WHEN payment_type NOT IN (1, 2, 3, 4, 5, 6) THEN 1 ELSE 0 END) AS invalid_payment_type_domain_count,

    SUM(CASE WHEN RatecodeID NOT IN (1, 2, 3, 4, 5, 6, 99) THEN 1 ELSE 0 END) AS invalid_ratecode_count,

    SUM(CASE WHEN store_and_fwd_flag IS NOT NULL AND store_and_fwd_flag NOT IN ('Y', 'N') THEN 1 ELSE 0 END) AS invalid_store_and_fwd_flag_count,

    SUM(CASE WHEN tip_amount < 0 THEN 1 ELSE 0 END) AS negative_tip_count,

    SUM(CASE WHEN tolls_amount < 0 THEN 1 ELSE 0 END) AS negative_tolls_count,

    SUM(CASE WHEN Airport_fee < 0 THEN 1 ELSE 0 END) AS negative_airport_fee_count,

    SUM(CASE WHEN trip_distance > 100 THEN 1 ELSE 0 END) AS very_long_distance_count,

    SUM(
        CASE
            WHEN date_diff('minute', tpep_pickup_datetime, tpep_dropoff_datetime) > 1440
            THEN 1 ELSE 0
        END
    ) AS very_long_duration_count
FROM nyc_taxi_lakehouse.bronze_yellow_taxi
WHERE year = 2024
    AND month = 1;



SELECT payment_type, COUNT(*) AS total_rows
FROM nyc_taxi_lakehouse.bronze_yellow_taxi
WHERE year = 2024
  AND month = 1
GROUP BY payment_type
ORDER BY payment_type;


SELECT RatecodeID, COUNT(*) AS total_rows
FROM nyc_taxi_lakehouse.bronze_yellow_taxi
WHERE year = 2024
  AND month = 1
GROUP BY RatecodeID
ORDER BY RatecodeID;


SELECT VendorID, COUNT(*) AS total_rows
FROM nyc_taxi_lakehouse.bronze_yellow_taxi
WHERE year = 2024
  AND month = 1
GROUP BY VendorID
ORDER BY VendorID;