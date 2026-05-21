CREATE EXTERNAL TABLE IF NOT EXISTS nyc_taxi_lakehouse.silver_yellow_taxi (
    vendor_id INT,
    pickup_datetime TIMESTAMP,
    dropoff_datetime TIMESTAMP,
    passenger_count BIGINT,
    trip_distance DOUBLE,
    ratecode_id BIGINT,
    store_and_fwd_flag STRING,
    pickup_location_id INT,
    dropoff_location_id INT,
    payment_type BIGINT,
    fare_amount DOUBLE,
    extra DOUBLE,
    mta_tax DOUBLE,
    tip_amount DOUBLE,
    tolls_amount DOUBLE,
    improvement_surcharge DOUBLE,
    total_amount DOUBLE,
    congestion_surcharge DOUBLE,
    airport_fee DOUBLE,
    trip_duration_minutes DOUBLE,
    pickup_date DATE,
    pickup_hour INT,
    pickup_day_of_week STRING,
    fare_per_mile DOUBLE,
    tip_rate DOUBLE,
    avg_speed_mph DOUBLE,
    fare_per_minute DOUBLE,
    same_pickup_dropoff_zone BOOLEAN,
    is_extreme_speed BOOLEAN,
    is_fare_distance_mismatch BOOLEAN,
    is_distance_duration_mismatch BOOLEAN,
    is_same_zone_high_fare BOOLEAN,
    is_analytical_outlier BOOLEAN
)
PARTITIONED BY (
    year INT,
    month INT
)
STORED AS PARQUET
LOCATION 's3://nyc-taxi-lakehouse-tntk/silver/yellow_taxi/';


ALTER TABLE nyc_taxi_lakehouse.silver_yellow_taxi
ADD IF NOT EXISTS PARTITION (year = 2024, month = 1)
LOCATION 's3://nyc-taxi-lakehouse-tntk/silver/yellow_taxi/year=2024/month=01/';