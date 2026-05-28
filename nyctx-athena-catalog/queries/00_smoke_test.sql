-- Scan safety: SAFE.
-- Required partition filter: exactly one year/month partition.
-- Purpose: verify that the Silver table can read one partition without scanning broad history.

SELECT
    vendor_id,
    pickup_datetime,
    dropoff_datetime,
    passenger_count,
    trip_distance,
    fare_amount,
    total_amount,
    pickup_location_id,
    dropoff_location_id,
    payment_type,
    year,
    month
FROM nyc_taxi_lakehouse.silver_yellow_taxi
WHERE year = '2024'
  AND month = '01'
LIMIT 25;
