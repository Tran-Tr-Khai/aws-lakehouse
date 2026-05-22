{{ config(
    materialized='table',
    table_type='hive',
    format='parquet', 
    external_location='s3://nyc-taxi-lakehouse-tntk/gold/core/dim_vendor/'
) }}

select *
from (
    values
        (1, 'Creative Mobile Technologies'),
        (2, 'VeriFone')
) as t(vendor_id, vendor_name)