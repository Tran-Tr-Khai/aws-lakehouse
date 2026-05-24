SELECT
    t.PULocationID,
    z.Borough AS pickup_borough,
    z.Zone AS pickup_zone,
    COUNT(*) AS trip_count
FROM nyc_taxi_lakehouse.bronze_yellow_taxi t
LEFT JOIN nyc_taxi_lakehouse.reference_taxi_zone_lookup z
    ON t.PULocationID = z.LocationID
WHERE t.year = 2024
  AND t.month = 1
GROUP BY
    t.PULocationID,
    z.Borough,
    z.Zone
ORDER BY trip_count DESC
LIMIT 10;