
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select total_fare_amount
from "awsdatacatalog"."nyc_taxi_lakehouse"."mart_daily_trip_revenue"
where total_fare_amount is null



  
  
      
    ) dbt_internal_test