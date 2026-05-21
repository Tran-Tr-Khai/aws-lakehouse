{{ config(
    materialized='table',
    table_type='hive',
    format='parquet'
) }}

with date_source as (
    select distinct
        pickup_date as date
    from {{ source('nyc_taxi_lakehouse', 'silver_yellow_taxi') }}
    where pickup_date is not null
)

select
    cast(date_format(cast(date as timestamp), '%Y%m%d') as integer) as date_key,
    date,
    year(date) as year,
    month(date) as month,
    day(date) as day,
    date_format(cast(date as timestamp), '%W') as day_of_week,
    case
        when day_of_week(date) in (6, 7) then true
        else false
    end as is_weekend
from date_source