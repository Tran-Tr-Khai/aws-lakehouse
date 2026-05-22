
    
    

select
    trip_id as unique_field,
    count(*) as n_records

from "awsdatacatalog"."nyc_taxi_lakehouse"."fact_trip"
where trip_id is not null
group by trip_id
having count(*) > 1


