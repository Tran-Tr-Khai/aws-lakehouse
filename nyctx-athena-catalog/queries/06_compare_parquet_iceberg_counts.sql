WITH parquet_counts AS (
    SELECT
        year,
        month,
        COUNT(*) AS parquet_trip_count
    FROM __NYCTX_ATHENA_DATABASE__.__NYCTX_ATHENA_SILVER_TABLE__
    WHERE __NYCTX_ATHENA_PERIOD_FILTER__
    GROUP BY year, month
),
iceberg_counts AS (
    SELECT
        year,
        month,
        COUNT(*) AS iceberg_trip_count
    FROM __NYCTX_ATHENA_DATABASE__.__NYCTX_ATHENA_ICEBERG_TABLE__
    WHERE __NYCTX_ATHENA_PERIOD_FILTER__
    GROUP BY year, month
)
SELECT
    COALESCE(p.year, i.year) AS year,
    COALESCE(p.month, i.month) AS month,
    p.parquet_trip_count,
    i.iceberg_trip_count,
    i.iceberg_trip_count - p.parquet_trip_count AS count_delta
FROM parquet_counts p
FULL OUTER JOIN iceberg_counts i
    ON p.year = i.year
   AND p.month = i.month
ORDER BY year, month;