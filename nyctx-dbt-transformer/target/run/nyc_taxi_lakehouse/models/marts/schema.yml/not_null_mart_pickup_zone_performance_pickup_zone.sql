
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select pickup_zone
from "awsdatacatalog"."nyc_taxi_lakehouse"."mart_pickup_zone_performance"
where pickup_zone is null



  
  
      
    ) dbt_internal_test