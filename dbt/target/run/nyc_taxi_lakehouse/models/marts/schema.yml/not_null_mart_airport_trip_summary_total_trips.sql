
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select total_trips
from "awsdatacatalog"."nyc_taxi_lakehouse"."mart_airport_trip_summary"
where total_trips is null



  
  
      
    ) dbt_internal_test