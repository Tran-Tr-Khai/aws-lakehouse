
    
    

select
    date_key as unique_field,
    count(*) as n_records

from "awsdatacatalog"."nyc_taxi_lakehouse"."mart_daily_trip_revenue"
where date_key is not null
group by date_key
having count(*) > 1


