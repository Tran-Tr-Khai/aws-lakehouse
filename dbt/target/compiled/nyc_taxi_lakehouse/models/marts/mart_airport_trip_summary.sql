

with trip_with_zones as (
    select
        f.trip_id,
        f.passenger_count,
        f.trip_distance,
        f.trip_duration_minutes,
        f.fare_amount,
        f.tip_amount,
        f.tolls_amount,
        f.congestion_surcharge,
        f.airport_fee,
        f.total_amount,
        f.tip_rate,
        f.fare_per_mile,

        pickup_z.zone as pickup_zone,
        dropoff_z.zone as dropoff_zone
    from "awsdatacatalog"."nyc_taxi_lakehouse"."fact_trip" f
    join "awsdatacatalog"."nyc_taxi_lakehouse"."dim_zone" pickup_z
        on f.pickup_location_id = pickup_z.location_id
    join "awsdatacatalog"."nyc_taxi_lakehouse"."dim_zone" dropoff_z
        on f.dropoff_location_id = dropoff_z.location_id
),

classified as (
    select
        *,
        case
            when pickup_zone in ('JFK Airport', 'LaGuardia Airport', 'Newark Airport')
              and dropoff_zone in ('JFK Airport', 'LaGuardia Airport', 'Newark Airport')
                then 'airport_to_airport'

            when pickup_zone in ('JFK Airport', 'LaGuardia Airport', 'Newark Airport')
                then 'airport_pickup'

            when dropoff_zone in ('JFK Airport', 'LaGuardia Airport', 'Newark Airport')
                then 'airport_dropoff'

            else 'non_airport'
        end as airport_trip_type
    from trip_with_zones
)

select
    airport_trip_type,

    count(trip_id) as total_trips,
    sum(passenger_count) as total_passengers,

    sum(total_amount) as total_amount,
    sum(fare_amount) as total_fare_amount,
    sum(tip_amount) as total_tip_amount,
    sum(tolls_amount) as total_tolls_amount,
    sum(congestion_surcharge) as total_congestion_surcharge,
    sum(airport_fee) as total_airport_fee,

    avg(total_amount) as avg_total_amount,
    avg(fare_amount) as avg_fare_amount,
    avg(tip_amount) as avg_tip_amount,
    avg(tip_rate) as avg_tip_rate,
    avg(trip_distance) as avg_trip_distance,
    avg(trip_duration_minutes) as avg_trip_duration_minutes,
    avg(fare_per_mile) as avg_fare_per_mile

from classified
group by airport_trip_type