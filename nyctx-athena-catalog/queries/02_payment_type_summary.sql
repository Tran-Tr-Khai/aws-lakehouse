-- Scan safety: SAFE.
-- Required partition filter: exactly one year/month partition.
-- Purpose: summarize payment mix and tipping behavior for one processed month.

SELECT
    payment_type,
    COUNT(*) AS trip_count,
    SUM(total_amount) AS total_revenue,
    AVG(fare_amount) AS avg_fare_amount,
    AVG(tip_amount) AS avg_tip_amount,
    AVG(tip_rate) AS avg_tip_rate
FROM nyc_taxi_lakehouse.silver_yellow_taxi
WHERE year = '2024'
  AND month = '01'
GROUP BY
    payment_type
ORDER BY
    trip_count DESC;
