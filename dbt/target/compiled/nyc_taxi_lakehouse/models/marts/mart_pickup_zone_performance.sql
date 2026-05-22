

select
    z.location_id as pickup_location_id,
    z.borough as pickup_borough,
    z.zone as pickup_zone,
    z.service_zone as pickup_service_zone,

    count(f.trip_id) as total_trips,
    sum(f.passenger_count) as total_passengers,

    sum(f.total_amount) as total_amount,
    sum(f.fare_amount) as total_fare_amount,
    sum(f.tip_amount) as total_tip_amount,
    sum(f.tolls_amount) as total_tolls_amount,
    sum(f.congestion_surcharge) as total_congestion_surcharge,
    sum(f.airport_fee) as total_airport_fee,

    avg(f.total_amount) as avg_total_amount,
    avg(f.fare_amount) as avg_fare_amount,
    avg(f.tip_amount) as avg_tip_amount,
    avg(f.tip_rate) as avg_tip_rate,

    avg(f.trip_distance) as avg_trip_distance,
    avg(f.trip_duration_minutes) as avg_trip_duration_minutes,
    avg(f.fare_per_mile) as avg_fare_per_mile

from "awsdatacatalog"."nyc_taxi_lakehouse"."fact_trip" f
join "awsdatacatalog"."nyc_taxi_lakehouse"."dim_zone" z
    on f.pickup_location_id = z.location_id

group by
    z.location_id,
    z.borough,
    z.zone,
    z.service_zone