{{ config(
    materialized='table',
    table_type='hive',
    format='parquet',
    external_location='s3://nyc-taxi-lakehouse-tntk/gold/marts/mart_daily_trip_revenue/'
) }}

select
    d.date_key,
    d.date,
    d.year,
    d.month,
    d.day_of_week,
    d.is_weekend,

    count(f.trip_id) as total_trips,
    sum(f.passenger_count) as total_passengers,

    sum(f.fare_amount) as total_fare_amount,
    sum(f.extra) as total_extra,
    sum(f.mta_tax) as total_mta_tax,
    sum(f.tip_amount) as total_tip_amount,
    sum(f.tolls_amount) as total_tolls_amount,
    sum(f.improvement_surcharge) as total_improvement_surcharge,
    sum(f.congestion_surcharge) as total_congestion_surcharge,
    sum(f.airport_fee) as total_airport_fee,
    sum(f.total_amount) as total_amount,

    avg(f.fare_amount) as avg_fare_amount,
    avg(f.total_amount) as avg_total_amount,
    avg(f.tip_amount) as avg_tip_amount,
    avg(f.tip_rate) as avg_tip_rate,
    avg(f.trip_distance) as avg_trip_distance,
    avg(f.trip_duration_minutes) as avg_trip_duration_minutes,
    avg(f.fare_per_mile) as avg_fare_per_mile

from {{ ref('fact_trip') }} f
join {{ ref('dim_date') }} d
    on f.pickup_date_key = d.date_key

group by
    d.date_key,
    d.date,
    d.year,
    d.month,
    d.day_of_week,
    d.is_weekend