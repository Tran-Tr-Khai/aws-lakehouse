
    
    

with all_values as (

    select
        airport_trip_type as value_field,
        count(*) as n_records

    from "awsdatacatalog"."nyc_taxi_lakehouse"."mart_airport_trip_summary"
    group by airport_trip_type

)

select *
from all_values
where value_field not in (
    'airport_to_airport','airport_pickup','airport_dropoff','non_airport'
)


