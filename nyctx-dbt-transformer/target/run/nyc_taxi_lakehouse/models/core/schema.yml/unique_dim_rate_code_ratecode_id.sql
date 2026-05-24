
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

select
    ratecode_id as unique_field,
    count(*) as n_records

from "awsdatacatalog"."nyc_taxi_lakehouse"."dim_rate_code"
where ratecode_id is not null
group by ratecode_id
having count(*) > 1



  
  
      
    ) dbt_internal_test