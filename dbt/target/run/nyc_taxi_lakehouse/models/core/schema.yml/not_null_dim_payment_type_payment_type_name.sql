
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select payment_type_name
from "awsdatacatalog"."nyc_taxi_lakehouse"."dim_payment_type"
where payment_type_name is null



  
  
      
    ) dbt_internal_test