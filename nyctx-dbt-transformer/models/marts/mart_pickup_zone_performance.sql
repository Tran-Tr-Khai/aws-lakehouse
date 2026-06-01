{{ config(
    enabled=var('enable_optional_marts'),
    materialized='table',
    table_type='hive',
    format='parquet',
    external_location=var('gold_s3_base') ~ '/marts/mart_pickup_zone_performance/'
) }}

select
    concat(cast(f.pickup_date_key as varchar), '-', cast(z.location_id as varchar)) as pickup_zone_date_key,
    f.pickup_date_key as date_key,
    d.date,
    d.year,
    d.month,

    z.location_id as pickup_location_id,
    z.borough as pickup_borough,
    z.zone as pickup_zone,
    z.service_zone as pickup_service_zone,
    z.latitude as pickup_latitude,
    z.longitude as pickup_longitude,

    count(f.trip_id) as total_trips,
    sum(f.passenger_count) as total_passengers,

    sum(f.total_amount) as total_amount,
    sum(f.fare_amount) as total_fare_amount,
    sum(f.tip_amount) as total_tip_amount,
    sum(f.tolls_amount) as total_tolls_amount,
    sum(f.congestion_surcharge) as total_congestion_surcharge,
    sum(f.airport_fee) as total_airport_fee,

    avg(f.total_amount) as avg_total_amount,
    avg(f.fare_amount) as avg_fare_amount,
    avg(f.tip_amount) as avg_tip_amount,
    case
        when sum(f.fare_amount) > 0 then sum(f.tip_amount) / sum(f.fare_amount)
        else null
    end as avg_tip_rate,

    avg(f.trip_distance) as avg_trip_distance,
    avg(f.trip_duration_minutes) as avg_trip_duration_minutes,
    case
        when sum(f.trip_distance) > 0 then sum(f.fare_amount) / sum(f.trip_distance)
        else null
    end as avg_fare_per_mile

from {{ ref('fact_trip') }} f
join {{ ref('dim_zone') }} z
    on f.pickup_location_id = z.location_id
join {{ ref('dim_date') }} d
    on f.pickup_date_key = d.date_key

group by
    f.pickup_date_key,
    d.date,
    d.year,
    d.month,
    z.location_id,
    z.borough,
    z.zone,
    z.service_zone,
    z.latitude,
    z.longitude
