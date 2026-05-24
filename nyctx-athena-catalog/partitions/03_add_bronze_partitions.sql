ALTER TABLE nyc_taxi_lakehouse.bronze_yellow_taxi
ADD IF NOT EXISTS PARTITION (year = 2024, month = 1)
LOCATION 's3://nyc-taxi-lakehouse-tntk/bronze/yellow_taxi/year=2024/month=01/';