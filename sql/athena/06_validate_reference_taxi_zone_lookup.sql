SELECT COUNT(*) AS total_zones
FROM nyc_taxi_lakehouse.reference_taxi_zone_lookup;

SELECT *
FROM nyc_taxi_lakehouse.reference_taxi_zone_lookup
ORDER BY LocationID
LIMIT 10;