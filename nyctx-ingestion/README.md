# nyctx-ingestion

Downloads NYC Yellow Taxi source data, validates local Bronze inputs, builds taxi-zone
reference data, and uploads verified objects to S3.

## Structure

```text
nyctx-ingestion/
├── src/nyctx_ingestion/   # Reusable, tested application code
├── scripts/               # AWS CLI helpers such as upload_to_s3.sh
├── sql/                   # DuckDB profiling queries
└── tests/                 # Unit and behavioral tests
```

Installing the package provides the console entrypoints used by Airflow:

- `nyctx-download`
- `nyctx-quality-check`
- `nyctx-build-zone-centroids`

## Download

Use exactly one month input method:

```bash
uv run --project nyctx-ingestion nyctx-download --year 2024 --months 1 2 3
uv run --project nyctx-ingestion nyctx-download --year-months 2024-01 2024-02
uv run --project nyctx-ingestion nyctx-download \
  --months-file config/recovery_sample_months.txt \
  --with-zone-lookup \
  --with-zone-centroids
```

Downloads use bounded HTTP retries and a `.part` file. The final landing file is published
only after its size and file format are validated.

## Local Bronze quality

Profiling mode records quality metrics without rejecting expected dirty Bronze rows:

```bash
uv run --project nyctx-ingestion nyctx-quality-check --year 2024 --month 1
```

Enable a pipeline gate with an explicit distinct critical-row threshold:

```bash
uv run --project nyctx-ingestion nyctx-quality-check \
  --months-file config/recovery_sample_months.txt \
  --max-critical-ratio 0.40
```

Use `--fail-on-critical` when no critical rows are acceptable. Add `--write-details` to
persist every query result. Each invocation writes to an isolated directory:

```text
data/quality/local_profile/run_id=<timestamp>-<pid>/
├── bronze_quality_summary.csv
├── bronze_quality_summary.md
└── year=YYYY/month=MM/       # only with --write-details
```

## Upload to S3

The destination bucket must be explicit:

```bash
export NYCTX_S3_BUCKET=nyc-taxi-lakehouse-example-dev
bash nyctx-ingestion/scripts/upload_to_s3.sh \
  --months-file config/recovery_sample_months.txt \
  --with-zone-lookup \
  --with-zone-centroids
```

The uploader validates all local inputs before writing. It stores SHA-256 metadata and skips
an existing object only when both its size and checksum match. Use `--force` to overwrite.

## Development

```bash
uv sync --package nyctx-ingestion --group dev
uv run --project nyctx-ingestion pytest nyctx-ingestion/tests
uv run --project nyctx-ingestion ruff check nyctx-ingestion
uv build --package nyctx-ingestion
```
