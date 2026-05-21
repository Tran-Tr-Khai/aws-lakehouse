
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

select
    payment_type_id as unique_field,
    count(*) as n_records

from "awsdatacatalog"."nyc_taxi_lakehouse"."dim_payment_type"
where payment_type_id is not null
group by payment_type_id
having count(*) > 1



  
  
      
    ) dbt_internal_test