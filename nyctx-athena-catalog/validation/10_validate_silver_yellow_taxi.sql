SELECT COUNT(*) AS silver_total_rows
FROM nyc_taxi_lakehouse.silver_yellow_taxi
WHERE year = 2024
  AND month = 1;
  
SELECT
    SUM(
        CASE
            WHEN pickup_datetime IS NULL
              OR dropoff_datetime IS NULL
              OR dropoff_datetime <= pickup_datetime
            THEN 1 ELSE 0
        END
    ) AS invalid_datetime_count,

    SUM(
        CASE
            WHEN pickup_datetime < TIMESTAMP '2024-01-01 00:00:00'
              OR pickup_datetime >= TIMESTAMP '2024-02-01 00:00:00'
            THEN 1 ELSE 0
        END
    ) AS invalid_batch_month_count,

    SUM(CASE WHEN trip_distance <= 0 THEN 1 ELSE 0 END) AS invalid_distance_count,
    SUM(CASE WHEN passenger_count <= 0 THEN 1 ELSE 0 END) AS invalid_passenger_count,
    SUM(CASE WHEN fare_amount < 0 THEN 1 ELSE 0 END) AS invalid_fare_count,
    SUM(CASE WHEN total_amount < 0 THEN 1 ELSE 0 END) AS invalid_total_amount_count,
    SUM(CASE WHEN pickup_location_id IS NULL THEN 1 ELSE 0 END) AS null_pickup_location_count,
    SUM(CASE WHEN dropoff_location_id IS NULL THEN 1 ELSE 0 END) AS null_dropoff_location_count,
    SUM(CASE WHEN payment_type NOT IN (1, 2, 3, 4) THEN 1 ELSE 0 END) AS invalid_payment_type_count
FROM nyc_taxi_lakehouse.silver_yellow_taxi
WHERE year = 2024
  AND month = 1;
  
  
SELECT
    SUM(CASE WHEN trip_duration_minutes IS NULL THEN 1 ELSE 0 END) AS null_trip_duration_minutes,
    SUM(CASE WHEN trip_duration_minutes <= 0 THEN 1 ELSE 0 END) AS invalid_trip_duration_minutes,

    SUM(CASE WHEN pickup_date IS NULL THEN 1 ELSE 0 END) AS null_pickup_date,
    SUM(CASE WHEN pickup_hour IS NULL THEN 1 ELSE 0 END) AS null_pickup_hour,
    SUM(CASE WHEN pickup_hour < 0 OR pickup_hour > 23 THEN 1 ELSE 0 END) AS invalid_pickup_hour,

    SUM(CASE WHEN pickup_day_of_week IS NULL THEN 1 ELSE 0 END) AS null_pickup_day_of_week,

    SUM(CASE WHEN fare_per_mile IS NULL THEN 1 ELSE 0 END) AS null_fare_per_mile,
    SUM(CASE WHEN fare_per_mile < 0 THEN 1 ELSE 0 END) AS invalid_fare_per_mile,

    SUM(CASE WHEN fare_amount > 0 AND tip_rate IS NULL THEN 1 ELSE 0 END) AS null_tip_rate_when_fare_positive,
    SUM(CASE WHEN tip_rate < 0 THEN 1 ELSE 0 END) AS negative_tip_rate_count
FROM nyc_taxi_lakehouse.silver_yellow_taxi
WHERE year = 2024
  AND month = 1;
  
SELECT
    SUM(CASE WHEN vendor_id NOT IN (1, 2) THEN 1 ELSE 0 END) AS unexpected_vendor_count,
    SUM(CASE WHEN ratecode_id NOT IN (1, 2, 3, 4, 5, 6, 99) THEN 1 ELSE 0 END) AS unexpected_ratecode_count,

    SUM(CASE WHEN tip_amount < 0 THEN 1 ELSE 0 END) AS negative_tip_count,
    SUM(CASE WHEN tolls_amount < 0 THEN 1 ELSE 0 END) AS negative_tolls_count,
    SUM(CASE WHEN airport_fee < 0 THEN 1 ELSE 0 END) AS negative_airport_fee_count,
    SUM(CASE WHEN extra < 0 THEN 1 ELSE 0 END) AS negative_extra_count,
    SUM(CASE WHEN mta_tax < 0 THEN 1 ELSE 0 END) AS negative_mta_tax_count,
    SUM(CASE WHEN improvement_surcharge < 0 THEN 1 ELSE 0 END) AS negative_improvement_surcharge_count,
    SUM(CASE WHEN congestion_surcharge < 0 THEN 1 ELSE 0 END) AS negative_congestion_surcharge_count
FROM nyc_taxi_lakehouse.silver_yellow_taxi
WHERE year = 2024
  AND month = 1;
  
SELECT
    approx_percentile(trip_distance, 0.5) AS trip_distance_p50,
    approx_percentile(trip_distance, 0.95) AS trip_distance_p95,
    approx_percentile(trip_distance, 0.99) AS trip_distance_p99,
    approx_percentile(trip_distance, 0.999) AS trip_distance_p999,
    MAX(trip_distance) AS trip_distance_max,

    approx_percentile(trip_duration_minutes, 0.5) AS trip_duration_p50,
    approx_percentile(trip_duration_minutes, 0.95) AS trip_duration_p95,
    approx_percentile(trip_duration_minutes, 0.99) AS trip_duration_p99,
    approx_percentile(trip_duration_minutes, 0.999) AS trip_duration_p999,
    MAX(trip_duration_minutes) AS trip_duration_max,

    approx_percentile(fare_per_mile, 0.5) AS fare_per_mile_p50,
    approx_percentile(fare_per_mile, 0.99) AS fare_per_mile_p99,
    approx_percentile(fare_per_mile, 0.999) AS fare_per_mile_p999,
    MAX(fare_per_mile) AS fare_per_mile_max
FROM nyc_taxi_lakehouse.silver_yellow_taxi
WHERE year = 2024
  AND month = 1;