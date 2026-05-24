{{ config(
    materialized='table',
    table_type='hive',
    format='parquet', 
    external_location='s3://nyc-taxi-lakehouse-tntk/gold/core/dim_payment_type/'
) }}

select *
from (
    values
        (1, 'Credit card', true),
        (2, 'Cash', true),
        (3, 'No charge', false),
        (4, 'Dispute', false)
) as t(payment_type_id, payment_type_name, is_standard_payment)