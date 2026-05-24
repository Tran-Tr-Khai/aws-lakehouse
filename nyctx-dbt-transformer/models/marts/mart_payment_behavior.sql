{{ config(
    materialized='table',
    table_type='hive',
    format='parquet',
    external_location='s3://nyc-taxi-lakehouse-tntk/gold/marts/mart_payment_behavior/'
) }}

select
    p.payment_type_id,
    p.payment_type_name,
    p.is_standard_payment,

    count(f.trip_id) as total_trips,
    sum(f.passenger_count) as total_passengers,

    sum(f.total_amount) as total_amount,
    sum(f.fare_amount) as total_fare_amount,
    sum(f.tip_amount) as total_tip_amount,
    sum(f.tolls_amount) as total_tolls_amount,

    avg(f.total_amount) as avg_total_amount,
    avg(f.fare_amount) as avg_fare_amount,
    avg(f.tip_amount) as avg_tip_amount,
    avg(f.tip_rate) as avg_tip_rate,
    avg(f.fare_per_mile) as avg_fare_per_mile,

    avg(f.trip_distance) as avg_trip_distance,
    avg(f.trip_duration_minutes) as avg_trip_duration_minutes

from {{ ref('fact_trip') }} f
join {{ ref('dim_payment_type') }} p
    on f.payment_type_id = p.payment_type_id

group by
    p.payment_type_id,
    p.payment_type_name,
    p.is_standard_payment