# nyctx-dbt-transformer

dbt Gold layer for the NYC Taxi Athena lakehouse.

This module is intentionally scoped to the first dashboard milestone:

```text
Silver Athena table
-> Gold core objects
-> mart_daily_trip_revenue
-> Power BI daily revenue/trip dashboard
```

The other mart SQL files remain in the project, but they are disabled by default
until the dashboard requirements need them. This avoids unnecessary Athena scans.

## Structure

```text
models/
  core/       dim_date, static dimensions, fact_trip
  marts/      mart_daily_trip_revenue and optional future marts
  sources.yml
profiles.yml
selectors.yml
scripts/
  run_dbt_gold.sh
```

## Environment

The checked-in `profiles.yml` uses environment variables and does not contain
secrets.

```bash
export AWS_DEFAULT_REGION=us-east-1
export AWS_PROFILE=default
export NYCTX_ATHENA_WORKGROUP=wg_nyc_taxi_lakehouse
export NYCTX_ATHENA_OUTPUT_LOCATION=s3://nyc-taxi-lakehouse-tntk/athena-results/
export NYCTX_ATHENA_DATABASE=nyc_taxi_lakehouse
export NYCTX_DBT_GOLD_S3_BASE=s3://nyc-taxi-lakehouse-tntk/gold
```

## Run Daily Revenue Gold

From the project root:

```bash
bash nyctx-dbt-transformer/scripts/run_dbt_gold.sh
```

This runs:

```text
dbt debug
uv run dbt run  --selector dashboard_daily_revenue
uv run dbt test --select dim_date dim_hour dim_payment_type dim_rate_code dim_vendor mart_daily_trip_revenue --exclude test_name:relationships
```

The selector builds only the objects needed for the first dashboard:

```text
dim_date
dim_hour
dim_payment_type
dim_rate_code
dim_vendor
fact_trip
mart_daily_trip_revenue
```

The script is selector-driven, so it can be reused when more Gold marts are
enabled later:

```bash
bash nyctx-dbt-transformer/scripts/run_dbt_gold.sh --selector dashboard_daily_revenue
bash nyctx-dbt-transformer/scripts/run_dbt_gold.sh --selector all_gold --test-select marts
bash nyctx-dbt-transformer/scripts/run_dbt_gold.sh --selector dashboard_daily_revenue --skip-tests
```

## Power BI Model

Use `dim_date` as the calendar table and relate it to the mart:

```text
dim_date[date_key] 1 -> * mart_daily_trip_revenue[date_key]
```

`mart_daily_trip_revenue` intentionally keeps only `date_key`, `date`, and
business metrics. Date attributes such as year, month, day name, and weekend
flags should come from `dim_date`.

## Optional Marts

Optional marts are disabled by default through `enable_optional_marts: false`.
To build them later:

```bash
cd nyctx-dbt-transformer
uv run dbt run --profiles-dir . --vars '{"enable_optional_marts": true}' --select marts
```

Only enable them when a dashboard page or analysis actually needs them.
