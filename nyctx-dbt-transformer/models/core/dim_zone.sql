{{ config(
    materialized='table',
    table_type='hive',
    format='parquet',
    external_location='s3://nyc-taxi-lakehouse-tntk/gold/core/dim_zone/'
) }}

select
    locationid as location_id,
    borough,
    zone,
    service_zone
from {{ source('nyc_taxi_lakehouse', 'reference_taxi_zone_lookup') }}
where locationid is not null