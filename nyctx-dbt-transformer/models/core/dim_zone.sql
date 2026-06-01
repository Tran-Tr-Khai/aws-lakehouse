{{ config(
    materialized='table',
    table_type='hive',
    format='parquet',
    external_location=var('gold_s3_base') ~ '/core/dim_zone/'
) }}

with zone_lookup as (
    select
        try_cast(locationid as integer) as location_id,
        nullif(trim(borough), '') as borough,
        nullif(trim(zone), '') as zone,
        nullif(trim(service_zone), '') as service_zone
    from {{ source('nyc_taxi_lakehouse', 'reference_taxi_zone_lookup') }}
),

zone_centroids as (
    select
        try_cast(location_id as integer) as location_id,
        try_cast(latitude as double) as latitude,
        try_cast(longitude as double) as longitude
    from {{ source('nyc_taxi_lakehouse', 'reference_taxi_zone_centroids') }}
)

select
    l.location_id,
    l.borough,
    l.zone,
    l.service_zone,
    c.latitude,
    c.longitude
from zone_lookup l
left join zone_centroids c
    on l.location_id = c.location_id
where l.location_id is not null
