
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select time_period
from "awsdatacatalog"."nyc_taxi_lakehouse"."dim_hour"
where time_period is null



  
  
      
    ) dbt_internal_test