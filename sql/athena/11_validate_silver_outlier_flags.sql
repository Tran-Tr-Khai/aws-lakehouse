SELECT
    COUNT(*) AS total_rows,
    SUM(CASE WHEN is_extreme_speed THEN 1 ELSE 0 END) AS extreme_speed_count,
    SUM(CASE WHEN is_fare_distance_mismatch THEN 1 ELSE 0 END) AS fare_distance_mismatch_count,
    SUM(CASE WHEN is_distance_duration_mismatch THEN 1 ELSE 0 END) AS distance_duration_mismatch_count,
    SUM(CASE WHEN is_same_zone_high_fare THEN 1 ELSE 0 END) AS same_zone_high_fare_count,
    SUM(CASE WHEN is_analytical_outlier THEN 1 ELSE 0 END) AS analytical_outlier_count
FROM nyc_taxi_lakehouse.silver_yellow_taxi
WHERE year = 2024
  AND month = 1;

SELECT
    vendor_id,
    pickup_datetime,
    dropoff_datetime,
    passenger_count,
    trip_distance,
    fare_amount,
    total_amount,
    fare_per_mile,
    fare_per_minute,
    avg_speed_mph,
    trip_duration_minutes,
    pickup_location_id,
    dropoff_location_id,
    payment_type,
    is_extreme_speed,
    is_fare_distance_mismatch,
    is_distance_duration_mismatch,
    is_same_zone_high_fare
FROM nyc_taxi_lakehouse.silver_yellow_taxi
WHERE year = 2024
  AND month = 1
  AND is_analytical_outlier = true
ORDER BY fare_per_mile DESC
LIMIT 50;

SELECT COUNT(*) AS analytical_clean_rows
FROM nyc_taxi_lakehouse.silver_yellow_taxi
WHERE year = 2024
  AND month = 1
  AND is_analytical_outlier = false;