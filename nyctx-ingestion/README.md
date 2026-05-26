# nyctx-ingestion

Downloads NYC Yellow Taxi raw data, uploads to S3 Bronze layer, and provides local data quality profiling.

## Structure

```
scripts/           # Ingestion and quality scripts
src/
└── nyctx_ingestion/   # Shared Python helpers (logger, paths, quality)
```

## Scripts

| Script | Description |
|--------|-------------|
| `scripts/download.py` | Download monthly Yellow Taxi parquet files from TLC |
| `scripts/upload_to_s3.sh` | Upload local parquet + zone lookup to S3 Bronze |
| `scripts/raw_quality_check.py` | Profile local Bronze data using DuckDB |

## Usage

```bash
# Download data
uv run python nyctx-ingestion/scripts/download.py --year 2024 --months 1 2 3 --with-zone-lookup

# Upload to S3
bash nyctx-ingestion/scripts/upload_to_s3.sh --year-months 2024-01 --with-zone-lookup

# Profile quality
uv run python nyctx-ingestion/scripts/raw_quality_check.py --year 2024 --month 1
```

> For local exploration and ad-hoc queries, see `sandbox/local_explore.py`.
