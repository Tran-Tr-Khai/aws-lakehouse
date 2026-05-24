
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select dropoff_datetime
from "awsdatacatalog"."nyc_taxi_lakehouse"."fact_trip"
where dropoff_datetime is null



  
  
      
    ) dbt_internal_test