
    
    

select
    pickup_location_id as unique_field,
    count(*) as n_records

from "awsdatacatalog"."nyc_taxi_lakehouse"."mart_pickup_zone_performance"
where pickup_location_id is not null
group by pickup_location_id
having count(*) > 1


