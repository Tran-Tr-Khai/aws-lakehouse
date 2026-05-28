{{ config(
    materialized='table',
    table_type='hive',
    format='parquet',
    external_location=var('gold_s3_base') ~ '/core/dim_rate_code/'
) }}

with rate_codes(ratecode_id, ratecode_name) as (
    values
        (1, 'Standard rate'),
        (2, 'JFK'),
        (3, 'Newark'),
        (4, 'Nassau or Westchester'),
        (5, 'Negotiated fare'),
        (6, 'Group ride'),
        (99, 'Unknown')
)

select
    ratecode_id,
    ratecode_name
from rate_codes
