{{ config(
    materialized='table',
    table_type='hive',
    format='parquet'
) }}

select
    locationid as location_id,
    borough,
    zone,
    service_zone
from {{ source('nyc_taxi_lakehouse', 'reference_taxi_zone_lookup') }}
where locationid is not null