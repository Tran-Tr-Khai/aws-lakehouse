
    
    

with child as (
    select pickup_date_key as from_field
    from "awsdatacatalog"."nyc_taxi_lakehouse"."fact_trip"
    where pickup_date_key is not null
),

parent as (
    select date_key as to_field
    from "awsdatacatalog"."nyc_taxi_lakehouse"."dim_date"
)

select
    from_field

from child
left join parent
    on child.from_field = parent.to_field

where parent.to_field is null


