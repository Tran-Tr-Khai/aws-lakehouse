
    
    

select
    vendor_id as unique_field,
    count(*) as n_records

from "awsdatacatalog"."nyc_taxi_lakehouse"."dim_vendor"
where vendor_id is not null
group by vendor_id
having count(*) > 1


