{{ config(
    materialized='table',
    table_type='hive',
    format='parquet',
    external_location='s3://nyc-taxi-lakehouse-tntk/gold/core/fact_trip/',
    partitioned_by=['year', 'month']
) }}

with silver_trips as (
    select
        vendor_id,
        pickup_datetime,
        dropoff_datetime,
        passenger_count,
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
        fare_per_mile,
        tip_rate,
        year,
        month
    from {{ source('nyc_taxi_lakehouse', 'silver_yellow_taxi') }}
    where is_analytical_outlier = false
),

final as (
    select
        to_hex(
            md5(
                to_utf8(
                    concat(
                        cast(vendor_id as varchar),
                        '|',
                        cast(pickup_datetime as varchar),
                        '|',
                        cast(dropoff_datetime as varchar),
                        '|',
                        cast(pickup_location_id as varchar),
                        '|',
                        cast(dropoff_location_id as varchar),
                        '|',
                        cast(fare_amount as varchar),
                        '|',
                        cast(total_amount as varchar)
                    )
                )
            )
        ) as trip_id,

        pickup_datetime,
        dropoff_datetime,

        cast(date_format(cast(pickup_date as timestamp), '%Y%m%d') as integer) as pickup_date_key,
        pickup_hour as pickup_hour_key,

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

        year,
        month
    from silver_trips
)

select *
from final