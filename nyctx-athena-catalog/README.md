# nyctx-athena-catalog

AWS Glue Data Catalog and Athena DDL, partition management, validation, and profiling SQL scripts.

## Structure

```
ddl/          # CREATE DATABASE and CREATE TABLE statements
partitions/   # ALTER TABLE ADD PARTITION for Hive-partitioned tables
validation/   # Row count, schema, join, and outlier validation queries
profiling/    # Data profiling and distribution analysis queries
```

## Script Index

### DDL
| Script | Description |
|--------|-------------|
| `ddl/01_create_database.sql` | Create `nyc_taxi_lakehouse` Glue database |
| `ddl/02_create_bronze_yellow_taxi_table.sql` | Create Bronze Yellow Taxi external table |
| `ddl/05_create_reference_taxi_zone_lookup_table.sql` | Create reference zone lookup table |
| `ddl/09_create_silver_yellow_taxi_table.sql` | Create Silver Yellow Taxi table |

### Partitions
| Script | Description |
|--------|-------------|
| `partitions/03_add_bronze_partitions.sql` | Register year/month partitions on Bronze table |

### Validation
| Script | Description |
|--------|-------------|
| `validation/04_validate_bronze_yellow_taxi.sql` | Validate Bronze row count and schema |
| `validation/06_validate_reference_taxi_zone_lookup.sql` | Validate zone lookup reference table |
| `validation/07_validate_bronze_reference_join.sql` | Validate Bronze ↔ zone lookup join |
| `validation/10_validate_silver_yellow_taxi.sql` | Validate Silver row count and columns |
| `validation/11_validate_silver_outlier_flags.sql` | Validate Silver outlier flags |

### Profiling
| Script | Description |
|--------|-------------|
| `profiling/08_profile_bronze_yellow_taxi.sql` | Profile Bronze data distributions |

## Usage

Run scripts sequentially in Athena using workgroup `wg_nyc_taxi_lakehouse`. See [docs/aws_athena_glue_setup.md](../docs/aws_athena_glue_setup.md) for full setup guide.
