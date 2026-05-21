{{ config(
    materialized='table',
    table_type='hive',
    format='parquet'
) }}

select *
from (
    values
        (1, 'Standard rate'),
        (2, 'JFK'),
        (3, 'Newark'),
        (4, 'Nassau or Westchester'),
        (5, 'Negotiated fare'),
        (6, 'Group ride'),
        (99, 'Unknown')
) as t(ratecode_id, ratecode_name)