# Gold Layer — Star Schema Data Model

## Overview

The Gold layer implements a **star schema** optimized for analytical queries and dashboards.
`fact_trip` is the central fact table containing one row per valid analytical trip.
Dimension tables provide descriptive context for each foreign key in `fact_trip`.

> **Note on dbt Lineage Graph:** dbt's lineage graph reflects SQL `source()` / `ref()` dependencies,
> not logical fact-to-dimension relationships. The ERD below is the correct star schema for this project.

---

## Star Schema Diagram

```mermaid
erDiagram
    FACT_TRIP {
        varchar trip_id PK
        timestamp pickup_datetime
        timestamp dropoff_datetime
        int pickup_date_key FK
        int pickup_hour_key FK
        int vendor_id FK
        int ratecode_id FK
        int payment_type_id FK
        int pickup_location_id FK
        int dropoff_location_id FK
        int passenger_count
        double trip_distance
        double trip_duration_minutes
        double fare_amount
        double extra
        double mta_tax
        double tip_amount
        double tolls_amount
        double improvement_surcharge
        double congestion_surcharge
        double airport_fee
        double total_amount
        double fare_per_mile
        double tip_rate
        int year
        int month
    }

    DIM_DATE {
        int date_key PK
        date date
        int year
        int month
        int day
        varchar day_of_week
        boolean is_weekend
    }

    DIM_HOUR {
        int hour_key PK
        int hour
        varchar time_period
    }

    DIM_VENDOR {
        int vendor_id PK
        varchar vendor_name
    }

    DIM_RATE_CODE {
        int ratecode_id PK
        varchar ratecode_name
    }

    DIM_PAYMENT_TYPE {
        int payment_type_id PK
        varchar payment_type_name
        boolean is_standard_payment
    }

    DIM_ZONE {
        int location_id PK
        varchar borough
        varchar zone
        varchar service_zone
    }

    DIM_DATE      ||--o{ FACT_TRIP : "pickup_date_key"
    DIM_HOUR      ||--o{ FACT_TRIP : "pickup_hour_key"
    DIM_VENDOR    ||--o{ FACT_TRIP : "vendor_id"
    DIM_RATE_CODE ||--o{ FACT_TRIP : "ratecode_id"
    DIM_PAYMENT_TYPE ||--o{ FACT_TRIP : "payment_type_id"
    DIM_ZONE      ||--o{ FACT_TRIP : "pickup_location_id"
    DIM_ZONE      ||--o{ FACT_TRIP : "dropoff_location_id"
```

---

## Dimension Tables

| Table | Type | Source | Description |
|---|---|---|---|
| `dim_date` | Date | Silver `pickup_date` | Calendar attributes derived from Silver pickup dates |
| `dim_hour` | Hour | Static values | 24-hour slots with `time_period` classification |
| `dim_vendor` | Vendor | Static values | Taxi vendor lookup (VeriFone, CMT) |
| `dim_rate_code` | Rate code | Static values | Trip rate code lookup |
| `dim_payment_type` | Payment | Static values | Payment method lookup |
| `dim_zone` | Zone | Reference `taxi_zone_lookup.csv` | Taxi zone, borough, and service zone |

---

## Fact Table

| Column | Type | Description |
|---|---|---|
| `trip_id` | `varchar` PK | MD5 surrogate key derived from trip attributes |
| `pickup_date_key` | `int` FK | `yyyyMMdd` integer joining `dim_date.date_key` |
| `pickup_hour_key` | `int` FK | Hour 0–23 joining `dim_hour.hour_key` |
| `vendor_id` | `int` FK | Joins `dim_vendor.vendor_id` |
| `ratecode_id` | `int` FK | Joins `dim_rate_code.ratecode_id` |
| `payment_type_id` | `int` FK | Joins `dim_payment_type.payment_type_id` |
| `pickup_location_id` | `int` FK | Joins `dim_zone.location_id` |
| `dropoff_location_id` | `int` FK | Joins `dim_zone.location_id` |
| `fare_per_mile` | `double` | Derived metric: `fare_amount / trip_distance` |
| `tip_rate` | `double` | Derived metric: `tip_amount / fare_amount` |

**Filter:** `is_analytical_outlier = false` — trips with extreme distance, duration, or fare are excluded from the Gold layer.

---

## Mart Roadmap

Marts join `fact_trip` with dimension tables to produce dashboard-ready aggregations.
Each mart will add visible edges in the dbt Lineage Graph.

| Mart (planned) | Uses | Answers |
|---|---|---|
| `mart_daily_trip_revenue` | `fact_trip` + `dim_date` | Daily trip count, revenue, tip rate |
| `mart_hourly_demand` | `fact_trip` + `dim_hour` + `dim_date` | Peak hours by day type |
| `mart_pickup_zone_performance` | `fact_trip` + `dim_zone` | Revenue and demand by pickup zone |
| `mart_payment_behavior` | `fact_trip` + `dim_payment_type` | Payment mix and tip behavior |
