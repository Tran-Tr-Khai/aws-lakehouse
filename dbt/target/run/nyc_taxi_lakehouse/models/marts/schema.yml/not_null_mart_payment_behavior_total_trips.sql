
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select total_trips
from "awsdatacatalog"."nyc_taxi_lakehouse"."mart_payment_behavior"
where total_trips is null



  
  
      
    ) dbt_internal_test