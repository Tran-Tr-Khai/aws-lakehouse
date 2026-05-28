{{ config(
    materialized='table',
    table_type='hive',
    format='parquet',
    external_location=var('gold_s3_base') ~ '/core/dim_vendor/'
) }}

with vendors(vendor_id, vendor_name) as (
    values
        (1, 'Creative Mobile Technologies'),
        (2, 'VeriFone')
)

select
    vendor_id,
    vendor_name
from vendors
