# Gold Layer Model

## Overview

```text
Silver cleaned trips → Gold Core (star schema) → Gold Marts (aggregates)
```

**Tooling:** Athena CTAS SQL (Gold is select/join/aggregate — SQL is more appropriate than Glue PySpark here).

---

## S3 Layout

```text
s3://nyc-taxi-lakehouse-tntk/gold/
├── core/
│   ├── dim_date/
│   ├── dim_hour/
│   ├── dim_zone/
│   ├── dim_payment_type/
│   ├── dim_rate_code/
│   ├── dim_vendor/
│   └── fact_trip/
└── marts/
    ├── mart_daily_revenue/
    ├── mart_hourly_demand/
    ├── mart_pickup_zone_performance/
    └── mart_payment_behavior/
```

---

## Core Dimensions

### `dim_date`
Source: generated from `silver_yellow_taxi.pickup_date`.

| Column        | Type    |
| ------------- | ------- |
| `date_key`    | INT     |
| `date`        | DATE    |
| `year`        | INT     |
| `month`       | INT     |
| `day`         | INT     |
| `day_of_week` | STRING  |
| `is_weekend`  | BOOLEAN |

---

### `dim_hour`
Source: static lookup (0–23).

| Column        | Type   | Note                                          |
| ------------- | ------ | --------------------------------------------- |
| `hour_key`    | INT    | 0–23                                          |
| `time_period` | STRING | late_night / morning / midday / evening / night |

Mapping: `0–5` late_night · `6–10` morning · `11–15` midday · `16–20` evening · `21–23` night

---

### `dim_zone`
Source: `reference_taxi_zone_lookup`.

| Column         | Type   |
| -------------- | ------ |
| `location_id`  | INT    |
| `borough`      | STRING |
| `zone`         | STRING |
| `service_zone` | STRING |

---

### `dim_payment_type`
Source: static mapping.

| `payment_type_id` | `payment_type_name` | `is_standard_payment` |
| ----------------: | ------------------- | --------------------- |
| 1                 | Credit card         | true                  |
| 2                 | Cash                | true                  |
| 3                 | No charge           | false                 |
| 4                 | Dispute             | false                 |

---

### `dim_rate_code`
Source: static mapping.

| `ratecode_id` | `ratecode_name`       |
| ------------: | --------------------- |
| 1             | Standard rate         |
| 2             | JFK                   |
| 3             | Newark                |
| 4             | Nassau or Westchester |
| 5             | Negotiated fare       |
| 6             | Group ride            |
| 99            | Unknown               |

---

### `dim_vendor`

| `vendor_id` | `vendor_name`                |
| ----------: | ---------------------------- |
| 1           | Creative Mobile Technologies |
| 2           | VeriFone                     |

---

## Fact Table: `fact_trip`

**Grain:** one row per valid analytical trip.  
**Source:** `silver_yellow_taxi` (analytical outliers excluded).

**Foreign keys:**

| Column                | References                    |
| --------------------- | ----------------------------- |
| `pickup_date_key`     | `dim_date.date_key`           |
| `pickup_hour_key`     | `dim_hour.hour_key`           |
| `vendor_id`           | `dim_vendor.vendor_id`        |
| `ratecode_id`         | `dim_rate_code.ratecode_id`   |
| `payment_type_id`     | `dim_payment_type.payment_type_id` |
| `pickup_location_id`  | `dim_zone.location_id`        |
| `dropoff_location_id` | `dim_zone.location_id`        |

**Measures:** `passenger_count`, `trip_distance`, `trip_duration_minutes`, `fare_amount`, `extra`, `mta_tax`, `tip_amount`, `tolls_amount`, `improvement_surcharge`, `congestion_surcharge`, `airport_fee`, `total_amount`, `fare_per_mile`, `tip_rate`

**Partitions:** `year`, `month`

---

## Analytics Marts

### `mart_daily_revenue`
Grain: one row per date.  
Key metrics: `total_trips`, `total_fare_amount`, `total_tip_amount`, `total_amount`, `avg_fare_amount`, `avg_tip_rate`, `avg_trip_distance`, `avg_trip_duration_minutes`

### `mart_hourly_demand`
Grain: one row per date + hour.  
Key metrics: `total_trips`, `total_passengers`, `avg_trip_distance`, `avg_fare_per_mile`

### `mart_pickup_zone_performance`
Grain: one row per pickup zone.  
Key metrics: `total_trips`, `total_amount`, `avg_tip_rate`, `avg_trip_distance`

### `mart_payment_behavior`
Grain: one row per payment type.  
Key metrics: `total_trips`, `total_fare_amount`, `total_tip_amount`, `avg_tip_rate`

---

## Build Order

```text
1. dim_zone → dim_payment_type → dim_rate_code → dim_vendor
2. dim_date → dim_hour
3. fact_trip
4. mart_daily_revenue → mart_hourly_demand → mart_pickup_zone_performance → mart_payment_behavior
```

Rule: dims first → fact → marts.
