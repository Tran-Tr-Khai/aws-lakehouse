
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select trip_duration_minutes
from "awsdatacatalog"."nyc_taxi_lakehouse"."fact_trip"
where trip_duration_minutes is null



  
  
      
    ) dbt_internal_test