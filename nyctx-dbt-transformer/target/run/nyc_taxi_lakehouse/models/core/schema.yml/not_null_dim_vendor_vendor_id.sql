
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select vendor_id
from "awsdatacatalog"."nyc_taxi_lakehouse"."dim_vendor"
where vendor_id is null



  
  
      
    ) dbt_internal_test