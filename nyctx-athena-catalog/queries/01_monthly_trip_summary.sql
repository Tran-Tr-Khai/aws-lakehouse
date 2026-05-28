-- Scan safety: SAFE for the current recovery sample.
-- Required partition filter: bounded list of known recovery months only.
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
FROM nyc_taxi_lakehouse.silver_yellow_taxi
WHERE (year = '2019' AND month = '01')
   OR (year = '2020' AND month IN ('01', '03', '04', '05'))
   OR (year = '2021' AND month = '01')
   OR (year = '2022' AND month = '01')
   OR (year = '2023' AND month = '01')
   OR (year = '2024' AND month = '01')
GROUP BY
    year,
    month
ORDER BY
    year,
    month;
