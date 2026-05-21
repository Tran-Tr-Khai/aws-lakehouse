
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select hour_key
from "awsdatacatalog"."nyc_taxi_lakehouse"."dim_hour"
where hour_key is null



  
  
      
    ) dbt_internal_test