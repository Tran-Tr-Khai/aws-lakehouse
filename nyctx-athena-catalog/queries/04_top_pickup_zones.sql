-- Scan safety: SAFE.
-- Required partition filter: exactly one year/month partition.
-- Purpose: identify top pickup location IDs by trips and revenue without scanning all history.
-- Note: this intentionally avoids joining a reference table so the Silver layer remains self-contained.

SELECT
    pickup_location_id,
    COUNT(*) AS trip_count,
    SUM(total_amount) AS total_revenue,
    AVG(total_amount) AS avg_total_amount,
    AVG(trip_distance) AS avg_trip_distance
FROM nyc_taxi_lakehouse.silver_yellow_taxi
WHERE year = '2024'
  AND month = '01'
GROUP BY
    pickup_location_id
ORDER BY
    trip_count DESC
LIMIT 25;
