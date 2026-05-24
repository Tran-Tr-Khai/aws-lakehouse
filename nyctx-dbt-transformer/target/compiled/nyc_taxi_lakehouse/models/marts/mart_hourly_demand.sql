

select
    d.date_key,
    d.date,
    d.year,
    d.month,
    d.day_of_week,
    d.is_weekend,

    h.hour_key,
    h.hour,
    h.time_period,

    count(f.trip_id) as total_trips,
    sum(f.passenger_count) as total_passengers,

    sum(f.total_amount) as total_amount,
    sum(f.fare_amount) as total_fare_amount,
    sum(f.tip_amount) as total_tip_amount,

    avg(f.total_amount) as avg_total_amount,
    avg(f.fare_amount) as avg_fare_amount,
    avg(f.tip_amount) as avg_tip_amount,
    avg(f.tip_rate) as avg_tip_rate,

    avg(f.trip_distance) as avg_trip_distance,
    avg(f.trip_duration_minutes) as avg_trip_duration_minutes,
    avg(f.fare_per_mile) as avg_fare_per_mile

from "awsdatacatalog"."nyc_taxi_lakehouse"."fact_trip" f
join "awsdatacatalog"."nyc_taxi_lakehouse"."dim_date" d
    on f.pickup_date_key = d.date_key
join "awsdatacatalog"."nyc_taxi_lakehouse"."dim_hour" h
    on f.pickup_hour_key = h.hour_key

group by
    d.date_key,
    d.date,
    d.year,
    d.month,
    d.day_of_week,
    d.is_weekend,
    h.hour_key,
    h.hour,
    h.time_period