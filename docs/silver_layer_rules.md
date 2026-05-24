# Silver Layer Rules

## 1. Objective

The Silver layer stores cleaned and standardized NYC Yellow Taxi trip data.

This layer is created from the raw Bronze data after applying critical data quality rules.

Flow:

```text
S3 Bronze raw taxi data
→ AWS Glue PySpark transformation
→ S3 Silver cleaned taxi data
```

Silver is not an aggregated reporting layer. It is the cleaned foundation dataset for Gold marts.

---

## 2. Input

Bronze table:

`nyc_taxi_lakehouse.bronze_yellow_taxi`

Bronze S3 location:

`s3://nyc-taxi-lakehouse-tntk/bronze/yellow_taxi/year=2024/month=01/`

Raw input profile:

| Metric                    |     Value |
| ------------------------- | --------: |
| Total rows                | 2,964,624 |
| Invalid datetime rows     |       870 |
| Invalid distance rows     |    60,371 |
| Invalid passenger rows    |   171,627 |
| Invalid fare rows         |    37,448 |
| Invalid total amount rows |    35,504 |
| Payment type = 0 rows     |   140,162 |
| Very long distance rows   |        59 |
| Very long duration rows   |        16 |

---

## 3. Output

Silver S3 location:

`s3://nyc-taxi-lakehouse-tntk/silver/yellow_taxi/year=2024/month=01/`

Future Athena table:

`nyc_taxi_lakehouse.silver_yellow_taxi`

Output format:

`Parquet`

---

## 4. Critical Cleaning Rules

Rows must satisfy all rules below to be included in Silver.

| Rule group       | Condition                                      |
| ---------------- | ---------------------------------------------- |
| Pickup datetime  | `tpep_pickup_datetime IS NOT NULL`             |
| Dropoff datetime | `tpep_dropoff_datetime IS NOT NULL`            |
| Trip duration    | `tpep_dropoff_datetime > tpep_pickup_datetime` |
| Batch month      | `tpep_pickup_datetime >= '2024-01-01'`         |
| Batch month      | `tpep_pickup_datetime < '2024-02-01'`          |
| Distance         | `trip_distance > 0`                            |
| Passenger        | `passenger_count > 0`                          |
| Fare             | `fare_amount >= 0`                             |
| Total amount     | `total_amount >= 0`                            |
| Pickup location  | `PULocationID IS NOT NULL`                     |
| Dropoff location | `DOLocationID IS NOT NULL`                     |
| Payment type     | `payment_type IN (1, 2, 3, 4)`                 |

These rules are considered critical because they directly affect trip validity, time-based analysis, revenue analysis, and location-based joins.

Silver main table keeps payment_type IN (1, 2, 3, 4) for interpretable trip analysis.
Records with payment_type IN (0, 5, 6) are excluded from the main Silver table but can be retained in a separate rejected/exception dataset for data quality and operational analysis.
---

## 5. Why Payment Type 0 Is Excluded

Profiling showed that `payment_type = 0` appears in 140,162 rows.

These rows also align with missing values in fields such as:

- `passenger_count`
- `RatecodeID`
- `store_and_fwd_flag`

For Silver V1, these records are excluded to keep the cleaned dataset reliable.

---

## 6. Warning-Level Checks

These checks are monitored but not immediately used as hard filters in Silver V1.

| Check                                 | Reason                     |
| ------------------------------------- | -------------------------- |
| `VendorID NOT IN (1, 2)`              | unexpected vendor code     |
| `RatecodeID NOT IN (1,2,3,4,5,6,99)`  | unexpected rate code       |
| `tip_amount < 0`                      | possible adjustment/refund |
| `tolls_amount < 0`                    | possible adjustment/refund |
| `Airport_fee < 0`                     | possible adjustment/refund |
| `extra < 0`                           | possible adjustment/refund |
| `mta_tax < 0`                         | possible adjustment/refund |
| `improvement_surcharge < 0`           | possible adjustment/refund |
| `congestion_surcharge < 0`            | possible adjustment/refund |

Warning-level checks are tracked but not dropped immediately to avoid over-filtering rare or source-specific edge cases.

---

## 7. Outlier Analysis

Outliers are not filtered in Silver V1 using fixed thresholds. Instead, they are analyzed using distribution-based profiling such as percentiles.

Recommended metrics:

| Metric | Purpose |
|---|---|
| `approx_quantile(trip_distance, 0.5)` | median distance |
| `approx_quantile(trip_distance, 0.95)` | high-distance threshold |
| `approx_quantile(trip_distance, 0.99)` | extreme-distance threshold |
| `approx_quantile(trip_distance, 0.999)` | very extreme distance |
| `approx_quantile(trip_duration_minutes, 0.95)` | high-duration threshold |
| `approx_quantile(trip_duration_minutes, 0.99)` | extreme-duration threshold |
| `approx_quantile(trip_duration_minutes, 0.999)` | very extreme duration |

Silver V1 does not drop outliers by default. Outlier thresholds should be decided after reviewing the distribution.

## Analytical Outlier Flags

Silver V2 does not immediately drop statistical outliers. Instead, it adds multi-column outlier flags so downstream Gold marts can decide whether to include or exclude these records.

| Flag | Logic | Purpose |
|---|---|---|
| `is_extreme_speed` | `avg_speed_mph > 120` | detects impossible distance-duration combinations |
| `is_fare_distance_mismatch` | `trip_distance < 0.1 AND fare_amount > 100` | detects very high fare on extremely short trips |
| `is_distance_duration_mismatch` | `trip_distance > 100 AND trip_duration_minutes < 90` | detects unrealistic long distance with short duration |
| `is_same_zone_high_fare` | `pickup_location_id = dropoff_location_id AND trip_distance < 0.1 AND fare_amount > 100` | detects suspicious same-zone high-fare records |
| `is_analytical_outlier` | any outlier flag is true | used by Gold marts and ML datasets to exclude analytical noise |

Gold marts should use:

`WHERE is_analytical_outlier = false`

when building normal dashboard/modeling datasets.

---

## 8. Derived Columns

Silver will add the following columns:

| Column                  | Description                                      |
| ----------------------- | ------------------------------------------------ |
| `trip_duration_minutes` | minutes between pickup and dropoff               |
| `pickup_date`           | date extracted from pickup datetime              |
| `pickup_hour`           | hour extracted from pickup datetime              |
| `pickup_day_of_week`    | day of week extracted from pickup datetime       |
| `fare_per_mile`         | `fare_amount / trip_distance`                    |
| `tip_rate`              | `tip_amount / fare_amount` when fare is positive |

---

## 9. Design Decision

Raw/Bronze profiling is used to understand data quality issues without modifying raw data.

Silver transformation applies only critical cleaning rules to create a reliable cleaned dataset.

Principle:

```text
Profile broadly in Bronze.
Clean selectively in Silver.
Validate again after Silver.
```

---

## 10. Next Step

Implement AWS Glue PySpark job:

`nyctx-glue-processor/jobs/glue_silver_yellow_taxi.py`

The job will:

1. Read Bronze Parquet data from S3
2. Apply critical cleaning rules
3. Add derived columns
4. Write cleaned Parquet data to S3 Silver
5. Validate Silver output with Athena