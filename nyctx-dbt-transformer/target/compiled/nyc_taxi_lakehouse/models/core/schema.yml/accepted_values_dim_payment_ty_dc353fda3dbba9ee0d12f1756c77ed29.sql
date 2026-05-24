
    
    

with all_values as (

    select
        payment_type_id as value_field,
        count(*) as n_records

    from "awsdatacatalog"."nyc_taxi_lakehouse"."dim_payment_type"
    group by payment_type_id

)

select *
from all_values
where value_field not in (
    1,2,3,4
)


