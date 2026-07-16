-- Scan safety: SAFE.
-- Required partition filter: exactly one runtime year/month partition.
-- Usage: pass --year YYYY --month MM.
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
FROM __NYCTX_ATHENA_DATABASE__.__NYCTX_ATHENA_SILVER_TABLE__
WHERE year = '__NYCTX_ATHENA_QUERY_YEAR__'
  AND month = '__NYCTX_ATHENA_QUERY_MONTH__'
LIMIT 25;
