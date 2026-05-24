# nyctx-dbt-transformer

dbt Gold layer: Core dimensions/facts and analytical marts via AWS Athena.

## Structure

```
models/
├── core/       # dim_date, dim_zone, dim_vendor, dim_payment_type, fact_trip
├── marts/      # mart_daily_trip_revenue, mart_hourly_demand, ...
└── sources.yml
```

## Usage

```bash
# Run from project root
uv run dbt run --project-dir nyctx-dbt-transformer

# Or from inside the folder
cd nyctx-dbt-transformer && uv run dbt run

# Run tests
uv run dbt test --project-dir nyctx-dbt-transformer
```
