# AWS Athena + Glue Catalog Setup

## 1. Objective

This step turns raw files stored in S3 into queryable datasets using AWS Glue Catalog and Amazon Athena.

Flow:

S3 Bronze / Reference  
→ Glue Catalog metadata  
→ Athena SQL query

## 2. Why Glue Catalog + Athena?

S3 only stores objects. It does not understand table schema, column types, partitions, or SQL table names.

Glue Catalog stores metadata such as:

- database name
- table name
- schema
- S3 location
- partition columns
- file format

Athena uses Glue Catalog as the metastore and queries the actual data files directly from S3.

## 3. Current S3 Layout

Bucket:

`s3://nyc-taxi-lakehouse-tntk/`

Current layout:

```text
bronze/
  yellow_taxi/year=2024/month=01/yellow_tripdata_2024-01.parquet

reference/
  taxi_zone_lookup.csv

athena-results/
```

## 4. Athena Workgroup

Workgroup:

`wg_nyc_taxi_lakehouse`

Main settings:

| Setting                       | Value                                          |
| ----------------------------- | ---------------------------------------------- |
| Engine                        | Athena SQL                                     |
| Authentication                | IAM                                            |
| Query result location         | `s3://nyc-taxi-lakehouse-tntk/athena-results/` |
| Override client-side settings | Enabled                                        |
| CloudWatch metrics            | Enabled                                        |

## 5. Glue Database

Database:

`nyc_taxi_lakehouse`

SQL script:

[01_create_database.sql](../sql/athena/01_create_database.sql)

## 6. Bronze Yellow Taxi Table

Table:

`nyc_taxi_lakehouse.bronze_yellow_taxi`

Purpose:

- expose raw Parquet files in S3 Bronze as an Athena table
- keep raw files unchanged
- validate row count, schema, and partition

SQL scripts:

- [02_create_bronze_yellow_taxi_table.sql](../sql/athena/02_create_bronze_yellow_taxi_table.sql)
- [03_add_bronze_partitions.sql](../sql/athena/03_add_bronze_partitions.sql)
- [04_validate_bronze_yellow_taxi.sql](../sql/athena/04_validate_bronze_yellow_taxi.sql)

Validation result:

| Check                        |    Result |
| ---------------------------- | --------: |
| Bronze row count for 2024-01 | 2,964,624 |

## 7. Reference Taxi Zone Lookup Table

Table:

`nyc_taxi_lakehouse.reference_taxi_zone_lookup`

Purpose:

- expose `taxi_zone_lookup.csv` as a reference table
- prepare for pickup/dropoff zone enrichment

SQL scripts:

- [05_create_reference_taxi_zone_lookup_table.sql](../sql/athena/05_create_reference_taxi_zone_lookup_table.sql)
- [06_validate_reference_taxi_zone_lookup.sql](../sql/athena/06_validate_reference_taxi_zone_lookup.sql)

Validation result:

| Check                | Result |
| -------------------- | -----: |
| Reference zone count |    265 |

## 8. Bronze + Reference Join Validation

Purpose:

- validate that `PULocationID` can be mapped to `LocationID`
- confirm that raw trip data can be enriched with zone information

SQL script:

[07_validate_bronze_reference_join.sql](../sql/athena/07_validate_bronze_reference_join.sql)

Top pickup zones from January 2024:

| Rank | PULocationID | Borough   | Zone                         | Trip count |
| ---: | -----------: | --------- | ---------------------------- | ---------: |
|    1 |          132 | Queens    | JFK Airport                  |    145,240 |
|    2 |          161 | Manhattan | Midtown Center               |    143,471 |
|    3 |          237 | Manhattan | Upper East Side South        |    142,708 |
|    4 |          236 | Manhattan | Upper East Side North        |    136,465 |
|    5 |          162 | Manhattan | Midtown East                 |    106,717 |
|    6 |          230 | Manhattan | Times Sq/Theatre District    |    106,324 |
|    7 |          186 | Manhattan | Penn Station/Madison Sq West |    104,523 |
|    8 |          142 | Manhattan | Lincoln Square East          |    104,080 |
|    9 |          138 | Queens    | LaGuardia Airport            |     89,533 |
|   10 |          239 | Manhattan | Upper West Side South        |     88,474 |

## 9. Repository Files

Athena SQL scripts:

[sql/athena/](../sql/athena/)

Upload script:

[scripts/upload_to_s3.sh](../scripts/upload_to_s3.sh)

## 10. Conclusion

This step completed the AWS query foundation:

| Layer    | Service      | Role                                            |
| -------- | ------------ | ----------------------------------------------- |
| Storage  | S3           | Stores Bronze and Reference files               |
| Metadata | Glue Catalog | Stores database/table/schema/partition metadata |
| Query    | Athena       | Queries S3 data using SQL                       |

Next step:

Design the Silver layer rules and transform Bronze data into cleaned Silver data.
