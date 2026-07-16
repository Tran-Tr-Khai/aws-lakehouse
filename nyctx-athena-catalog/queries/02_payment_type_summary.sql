-- Scan safety: SAFE.
-- Required partition filter: exactly one runtime year/month partition.
-- Usage: pass --year YYYY --month MM.
-- Purpose: summarize payment mix and tipping behavior for one processed month.

SELECT
    payment_type,
    COUNT(*) AS trip_count,
    SUM(total_amount) AS total_revenue,
    AVG(fare_amount) AS avg_fare_amount,
    AVG(tip_amount) AS avg_tip_amount,
    AVG(tip_rate) AS avg_tip_rate
FROM __NYCTX_ATHENA_DATABASE__.__NYCTX_ATHENA_SILVER_TABLE__
WHERE year = '__NYCTX_ATHENA_QUERY_YEAR__'
  AND month = '__NYCTX_ATHENA_QUERY_MONTH__'
GROUP BY
    payment_type
ORDER BY
    trip_count DESC;
