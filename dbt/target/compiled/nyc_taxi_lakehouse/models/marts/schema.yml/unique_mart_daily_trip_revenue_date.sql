
    
    

select
    date as unique_field,
    count(*) as n_records

from "awsdatacatalog"."nyc_taxi_lakehouse"."mart_daily_trip_revenue"
where date is not null
group by date
having count(*) > 1


