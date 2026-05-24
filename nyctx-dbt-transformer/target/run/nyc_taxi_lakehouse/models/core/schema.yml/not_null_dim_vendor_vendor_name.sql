
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select vendor_name
from "awsdatacatalog"."nyc_taxi_lakehouse"."dim_vendor"
where vendor_name is null



  
  
      
    ) dbt_internal_test