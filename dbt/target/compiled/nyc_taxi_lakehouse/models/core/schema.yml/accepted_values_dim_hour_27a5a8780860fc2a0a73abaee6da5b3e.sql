
    
    

with all_values as (

    select
        time_period as value_field,
        count(*) as n_records

    from "awsdatacatalog"."nyc_taxi_lakehouse"."dim_hour"
    group by time_period

)

select *
from all_values
where value_field not in (
    'late_night','morning','midday','evening','night'
)


