
    
    

select
    payment_type_id as unique_field,
    count(*) as n_records

from "awsdatacatalog"."nyc_taxi_lakehouse"."mart_payment_behavior"
where payment_type_id is not null
group by payment_type_id
having count(*) > 1


