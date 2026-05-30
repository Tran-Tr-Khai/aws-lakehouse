{{ config(
    materialized='table',
    table_type='hive',
    format='parquet',
    external_location=var('gold_s3_base') ~ '/core/dim_date/'
) }}

with date_source as (
    select distinct
        pickup_date as date
    from {{ source('nyc_taxi_lakehouse', 'silver_yellow_taxi') }}
    where pickup_date is not null
      and coalesce(is_analytical_outlier, false) = false
)

select
    cast(date_format(cast(date as timestamp), '%Y%m%d') as integer) as date_key,
    date,
    year(date) as year,
    quarter(date) as quarter,
    month(date) as month,
    case month(date)
        when 1 then 'Jan'
        when 2 then 'Feb'
        when 3 then 'Mar'
        when 4 then 'Apr'
        when 5 then 'May'
        when 6 then 'Jun'
        when 7 then 'Jul'
        when 8 then 'Aug'
        when 9 then 'Sep'
        when 10 then 'Oct'
        when 11 then 'Nov'
        when 12 then 'Dec'
    end as month_name,
    day(date) as day_of_month,
    day_of_week(date) as day_of_week,
    date_format(cast(date as timestamp), '%W') as day_of_week_name,
    case
        when day_of_week(date) in (6, 7) then true
        else false
    end as is_weekend
from date_source
