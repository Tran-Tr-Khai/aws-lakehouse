
    
    

with all_values as (

    select
        day_of_week as value_field,
        count(*) as n_records

    from "awsdatacatalog"."nyc_taxi_lakehouse"."dim_date"
    group by day_of_week

)

select *
from all_values
where value_field not in (
    'Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'
)


