{{ config(
    materialized='table',
    table_type='hive',
    format='parquet',
    external_location=var('gold_s3_base') ~ '/core/dim_payment_type/'
) }}

with payment_types(payment_type_id, payment_type_name, is_standard_payment) as (
    values
        (1, 'Credit card', true),
        (2, 'Cash', true),
        (3, 'No charge', false),
        (4, 'Dispute', false)
)

select
    payment_type_id,
    payment_type_name,
    is_standard_payment
from payment_types
