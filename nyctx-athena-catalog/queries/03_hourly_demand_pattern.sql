-- Scan safety: SAFE.
-- Required partition filter: exactly one runtime year/month partition.
-- Usage: pass --year YYYY --month MM.
-- Purpose: inspect hourly demand and revenue pattern for a single month.

SELECT
    pickup_hour,
    COUNT(*) AS trip_count,
    SUM(total_amount) AS total_revenue,
    AVG(trip_distance) AS avg_trip_distance,
    AVG(trip_duration_minutes) AS avg_trip_duration_minutes
FROM __NYCTX_ATHENA_DATABASE__.__NYCTX_ATHENA_SILVER_TABLE__
WHERE year = '__NYCTX_ATHENA_QUERY_YEAR__'
  AND month = '__NYCTX_ATHENA_QUERY_MONTH__'
GROUP BY
    pickup_hour
ORDER BY
    pickup_hour;
