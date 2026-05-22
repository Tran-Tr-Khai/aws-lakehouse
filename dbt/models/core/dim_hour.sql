{{ config(
    materialized='table',
    table_type='hive',
    format='parquet', 
    external_location='s3://nyc-taxi-lakehouse-tntk/gold/core/dim_hour/'
) }}

select
    hour_key,
    hour_key as hour,
    case
        when hour_key between 0 and 5 then 'late_night'
        when hour_key between 6 and 10 then 'morning'
        when hour_key between 11 and 15 then 'midday'
        when hour_key between 16 and 20 then 'evening'
        else 'night'
    end as time_period
from unnest(sequence(0, 23)) as t(hour_key)