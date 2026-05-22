
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select airport_trip_type
from "awsdatacatalog"."nyc_taxi_lakehouse"."mart_airport_trip_summary"
where airport_trip_type is null



  
  
      
    ) dbt_internal_test