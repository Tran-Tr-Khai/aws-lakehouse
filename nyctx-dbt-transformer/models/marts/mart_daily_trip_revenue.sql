{{ config(
    materialized='table',
    table_type='hive',
    format='parquet',
    external_location=var('gold_s3_base') ~ '/marts/mart_daily_trip_revenue/',
    tags=['dashboard_v1']
) }}

select
    d.date_key,
    d.date,

    count(f.trip_id) as total_trips,
    sum(coalesce(f.passenger_count, 0)) as total_passengers,

    sum(coalesce(f.total_amount, 0)) as total_revenue,
    sum(coalesce(f.fare_amount, 0)) as total_fare_amount,
    sum(coalesce(f.tip_amount, 0)) as total_tip_amount,
    sum(coalesce(f.tolls_amount, 0)) as total_tolls_amount,
    sum(coalesce(f.airport_fee, 0)) as total_airport_fee,
    sum(coalesce(f.congestion_surcharge, 0)) as total_congestion_surcharge,

    avg(f.total_amount) as avg_total_amount,
    avg(f.fare_amount) as avg_fare_amount,
    avg(f.tip_amount) as avg_tip_amount,
    avg(f.tip_rate) as avg_tip_rate,
    avg(f.trip_distance) as avg_trip_distance,
    avg(f.trip_duration_minutes) as avg_trip_duration_minutes,
    avg(f.fare_per_mile) as avg_fare_per_mile,

    sum(case when f.payment_type_id = 1 then 1 else 0 end) as credit_card_trips,
    sum(case when f.payment_type_id = 2 then 1 else 0 end) as cash_trips,
    sum(case when coalesce(f.airport_fee, 0) > 0 then 1 else 0 end) as airport_fee_trips,
    sum(case when coalesce(f.has_warning_quality_issue, false) then 1 else 0 end) as warning_trip_count

from {{ ref('fact_trip') }} f
join {{ ref('dim_date') }} d
    on f.pickup_date_key = d.date_key

group by
    d.date_key,
    d.date
