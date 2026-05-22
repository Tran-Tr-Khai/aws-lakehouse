
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

select
    trip_id as unique_field,
    count(*) as n_records

from "awsdatacatalog"."nyc_taxi_lakehouse"."fact_trip"
where trip_id is not null
group by trip_id
having count(*) > 1



  
  
      
    ) dbt_internal_test