
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select day_of_week
from "awsdatacatalog"."nyc_taxi_lakehouse"."dim_date"
where day_of_week is null



  
  
      
    ) dbt_internal_test