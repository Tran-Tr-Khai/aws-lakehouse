-- Scan safety: SAFE when used with a bounded runtime month list.
-- Required partition filter: pass --months-file with known processed periods.
-- Purpose: compare Silver row counts and business totals across processed months.

SELECT
    year,
    month,
    COUNT(*) AS trip_count,
    SUM(total_amount) AS total_revenue,
    AVG(total_amount) AS avg_total_amount,
    AVG(trip_distance) AS avg_trip_distance,
    AVG(trip_duration_minutes) AS avg_trip_duration_minutes,
    SUM(CASE WHEN is_analytical_outlier THEN 1 ELSE 0 END) AS analytical_outlier_count
FROM __NYCTX_ATHENA_DATABASE__.__NYCTX_ATHENA_SILVER_TABLE__
WHERE __NYCTX_ATHENA_PERIOD_FILTER__
GROUP BY
    year,
    month
ORDER BY
    year,
    month;
