
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select pickup_datetime
from "awsdatacatalog"."nyc_taxi_lakehouse"."fact_trip"
where pickup_datetime is null



  
  
      
    ) dbt_internal_test