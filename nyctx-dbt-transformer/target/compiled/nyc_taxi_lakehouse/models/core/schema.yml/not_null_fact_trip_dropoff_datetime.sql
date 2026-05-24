
    
    



select dropoff_datetime
from "awsdatacatalog"."nyc_taxi_lakehouse"."fact_trip"
where dropoff_datetime is null


