{{ config(
    materialized='table',
    table_type='hive',
    format='parquet',
    external_location=var('gold_s3_base') ~ '/core/fact_trip/',
    partitioned_by=['year', 'month']
) }}

with silver_trips as (
    select
        vendor_id,
        pickup_datetime,
        dropoff_datetime,
        cast(passenger_count as bigint) as passenger_count,
        trip_distance,
        ratecode_id,
        pickup_location_id,
        dropoff_location_id,
        payment_type,
        fare_amount,
        extra,
        mta_tax,
        tip_amount,
        tolls_amount,
        improvement_surcharge,
        total_amount,
        congestion_surcharge,
        airport_fee,
        trip_duration_minutes,
        pickup_date,
        pickup_hour,
        pickup_day_of_week,
        fare_per_mile,
        tip_rate,
        avg_speed_mph,
        fare_per_minute,
        same_pickup_dropoff_zone,
        has_warning_quality_issue,
        is_extreme_speed,
        is_fare_distance_mismatch,
        is_distance_duration_mismatch,
        is_same_zone_high_fare,
        year,
        month
    from {{ source('nyc_taxi_lakehouse', 'silver_yellow_taxi') }}
    where coalesce(is_analytical_outlier, false) = false
),

final as (
    select
        to_hex(
            md5(
                to_utf8(
                    concat(
                        coalesce(cast(vendor_id as varchar), ''),
                        '|',
                        coalesce(cast(pickup_datetime as varchar), ''),
                        '|',
                        coalesce(cast(dropoff_datetime as varchar), ''),
                        '|',
                        coalesce(cast(pickup_location_id as varchar), ''),
                        '|',
                        coalesce(cast(dropoff_location_id as varchar), ''),
                        '|',
                        coalesce(cast(fare_amount as varchar), ''),
                        '|',
                        coalesce(cast(total_amount as varchar), ''),
                        '|',
                        coalesce(year, ''),
                        '|',
                        coalesce(month, '')
                    )
                )
            )
        ) as trip_id,

        pickup_datetime,
        dropoff_datetime,

        cast(date_format(cast(pickup_date as timestamp), '%Y%m%d') as integer) as pickup_date_key,
        pickup_hour as pickup_hour_key,
        pickup_day_of_week,

        vendor_id,
        ratecode_id,
        payment_type as payment_type_id,
        pickup_location_id,
        dropoff_location_id,

        passenger_count,
        trip_distance,
        trip_duration_minutes,

        fare_amount,
        extra,
        mta_tax,
        tip_amount,
        tolls_amount,
        improvement_surcharge,
        congestion_surcharge,
        airport_fee,
        total_amount,

        fare_per_mile,
        tip_rate,
        avg_speed_mph,
        fare_per_minute,

        same_pickup_dropoff_zone,
        has_warning_quality_issue,
        is_extreme_speed,
        is_fare_distance_mismatch,
        is_distance_duration_mismatch,
        is_same_zone_high_fare,

        year,
        month
    from silver_trips
)

select
    trip_id,
    pickup_datetime,
    dropoff_datetime,
    pickup_date_key,
    pickup_hour_key,
    pickup_day_of_week,
    vendor_id,
    ratecode_id,
    payment_type_id,
    pickup_location_id,
    dropoff_location_id,
    passenger_count,
    trip_distance,
    trip_duration_minutes,
    fare_amount,
    extra,
    mta_tax,
    tip_amount,
    tolls_amount,
    improvement_surcharge,
    congestion_surcharge,
    airport_fee,
    total_amount,
    fare_per_mile,
    tip_rate,
    avg_speed_mph,
    fare_per_minute,
    same_pickup_dropoff_zone,
    has_warning_quality_issue,
    is_extreme_speed,
    is_fare_distance_mismatch,
    is_distance_duration_mismatch,
    is_same_zone_high_fare,
    year,
    month
from final
