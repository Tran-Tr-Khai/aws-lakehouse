
    
    

select
    ratecode_id as unique_field,
    count(*) as n_records

from "awsdatacatalog"."nyc_taxi_lakehouse"."dim_rate_code"
where ratecode_id is not null
group by ratecode_id
having count(*) > 1


