
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select total_amount
from "awsdatacatalog"."nyc_taxi_lakehouse"."mart_pickup_zone_performance"
where total_amount is null



  
  
      
    ) dbt_internal_test