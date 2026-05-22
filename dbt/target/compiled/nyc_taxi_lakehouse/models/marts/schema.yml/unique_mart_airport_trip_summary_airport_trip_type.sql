
    
    

select
    airport_trip_type as unique_field,
    count(*) as n_records

from "awsdatacatalog"."nyc_taxi_lakehouse"."mart_airport_trip_summary"
where airport_trip_type is not null
group by airport_trip_type
having count(*) > 1


