
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select ratecode_name
from "awsdatacatalog"."nyc_taxi_lakehouse"."dim_rate_code"
where ratecode_name is null



  
  
      
    ) dbt_internal_test