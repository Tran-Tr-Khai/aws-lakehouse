{{ config(
    materialized='table',
    table_type='hive',
    format='parquet'
) }}

select *
from (
    values
        (1, 'Creative Mobile Technologies'),
        (2, 'VeriFone')
) as t(vendor_id, vendor_name)