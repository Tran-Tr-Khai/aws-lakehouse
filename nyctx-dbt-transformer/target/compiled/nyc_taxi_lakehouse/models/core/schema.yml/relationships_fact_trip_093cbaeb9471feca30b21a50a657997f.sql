
    
    

with child as (
    select pickup_hour_key as from_field
    from "awsdatacatalog"."nyc_taxi_lakehouse"."fact_trip"
    where pickup_hour_key is not null
),

parent as (
    select hour_key as to_field
    from "awsdatacatalog"."nyc_taxi_lakehouse"."dim_hour"
)

select
    from_field

from child
left join parent
    on child.from_field = parent.to_field

where parent.to_field is null


