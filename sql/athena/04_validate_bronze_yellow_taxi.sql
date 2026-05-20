SELECT COUNT(*) AS total_rows
FROM nyc_taxi_lakehouse.bronze_yellow_taxi
WHERE year = 2024 AND month = 1;

SELECT year, month, COUNT(*) AS total_rows
FROM nyc_taxi_lakehouse.bronze_yellow_taxi
GROUP BY year, month;

SELECT
    VendorID,
    tpep_pickup_datetime,
    tpep_dropoff_datetime,
    passenger_count,
    trip_distance,
    fare_amount,
    total_amount,
    PULocationID,
    DOLocationID,
    year,
    month
FROM nyc_taxi_lakehouse.bronze_yellow_taxi
WHERE year = 2024 AND month = 1
LIMIT 10;