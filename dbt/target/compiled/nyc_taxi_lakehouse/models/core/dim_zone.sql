

select
    locationid as location_id,
    borough,
    zone,
    service_zone
from "awsdatacatalog"."nyc_taxi_lakehouse"."reference_taxi_zone_lookup"
where locationid is not null