-- Scan safety: SAFE.
-- Required partition filter: exactly one year/month partition.
-- Purpose: inspect hourly demand and revenue pattern for a single month.

SELECT
    pickup_hour,
    COUNT(*) AS trip_count,
    SUM(total_amount) AS total_revenue,
    AVG(trip_distance) AS avg_trip_distance,
    AVG(trip_duration_minutes) AS avg_trip_duration_minutes
FROM nyc_taxi_lakehouse.silver_yellow_taxi
WHERE year = '2024'
  AND month = '01'
GROUP BY
    pickup_hour
ORDER BY
    pickup_hour;
