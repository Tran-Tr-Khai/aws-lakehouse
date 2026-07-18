-- Scan safety: SAFE.
-- Required partition filter: exactly one runtime year/month partition.
-- Usage: pass --year YYYY --month MM.
-- Purpose: identify top pickup location IDs by trips and revenue without scanning all history.
-- Note: this intentionally avoids joining a reference table so the Silver layer remains self-contained.

SELECT
    pickup_location_id,
    COUNT(*) AS trip_count,
    SUM(total_amount) AS total_revenue,
    AVG(total_amount) AS avg_total_amount,
    AVG(trip_distance) AS avg_trip_distance
FROM __NYCTX_ATHENA_DATABASE__.__NYCTX_ATHENA_TABLE__
WHERE year = '__NYCTX_ATHENA_QUERY_YEAR__'
  AND month = '__NYCTX_ATHENA_QUERY_MONTH__'
GROUP BY
    pickup_location_id
ORDER BY
    trip_count DESC
LIMIT 25;
