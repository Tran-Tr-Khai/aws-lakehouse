# Athena Query Cost Guardrails

Athena charges by the amount of data scanned by each query. A query can be
logically correct and still be expensive if it scans too many S3 objects.

## Why Parquet Matters

Silver data is stored as Parquet. Parquet is columnar, so Athena can read only
the columns referenced by a query instead of scanning full rows. This is one
reason all portfolio queries use explicit column lists and avoid `SELECT *`.

## Why Partition Pruning Matters

Silver data is stored under Hive-style S3 prefixes:

```text
s3://nyc-taxi-lakehouse-tntk/silver/yellow_taxi/year=YYYY/month=MM/
```

The Athena table exposes `year` and `month` as partition columns. Queries must
filter those columns so Athena can prune unrelated S3 prefixes.

Good:

```sql
WHERE year = '2024'
  AND month = '01'
```

Acceptable for a small trend:

```sql
WHERE (year = '2020' AND month IN ('01', '03', '04', '05'))
   OR (year = '2024' AND month = '01')
```

Avoid:

```sql
WHERE pickup_date >= DATE '2024-01-01'
```

The date predicate is useful for business logic, but it does not replace
partition filters.

## Why `SELECT *` Is Avoided

`SELECT *` forces Athena to read every referenced Parquet column. Production
queries should select only the columns needed for validation or analysis.

## Required Query Pattern

Every analytical query should include:

```sql
WHERE year = '<YYYY>'
  AND month = '<MM>'
```

or a deliberately bounded list of month partitions.

## Checking Athena Data Scanned

After every query, inspect the Athena query details:

```text
Query editor -> Query history -> Data scanned
```

Do not trust a query just because it returns quickly. Confirm that the data
scanned is consistent with the intended partition range and selected columns.

## Practical Rules

- Use Silver Parquet for analytics, not raw Bronze files.
- Select only required columns.
- Always filter partition columns.
- Keep trend queries bounded to known month lists.
- Use `ORDER BY` only with aggregated results or with `LIMIT`.
- Avoid broad validation queries that group all years/months unless explicitly
  intended and reviewed for scan cost.
