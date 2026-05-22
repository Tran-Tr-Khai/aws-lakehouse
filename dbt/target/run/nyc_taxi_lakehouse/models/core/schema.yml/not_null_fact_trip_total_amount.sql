
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select total_amount
from "awsdatacatalog"."nyc_taxi_lakehouse"."fact_trip"
where total_amount is null



  
  
      
    ) dbt_internal_test