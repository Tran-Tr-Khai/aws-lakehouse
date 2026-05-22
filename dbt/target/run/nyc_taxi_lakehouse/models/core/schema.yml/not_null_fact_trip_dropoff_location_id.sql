
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select dropoff_location_id
from "awsdatacatalog"."nyc_taxi_lakehouse"."fact_trip"
where dropoff_location_id is null



  
  
      
    ) dbt_internal_test