# nyctx-glue-processor

AWS Glue PySpark jobs for Silver-layer transformation.

## Architecture

This module now follows a production-oriented split:

```text
jobs/glue_silver_yellow_taxi.py          Thin AWS Glue entrypoint
src/nyctx_glue_processor/silver_job.py   Reusable Spark transformation core
scripts/build_glue_package.py            Build zip artifact for --extra-py-files
scripts/deploy_glue_job.sh               Deploy Glue job definition and artifacts
scripts/deploy_glue_job_terraform.sh     Upload artifacts for Terraform-managed jobs
scripts/run_glue_job.sh                  Start one or many Glue runs
tests/test_silver_job.py                 Fast local tests for config/runtime contract
```

The key idea is:

```text
Glue entrypoint          -> AWS runtime bootstrap only
Silver module            -> business logic and Spark transforms
Deploy scripts           -> package + publish code artifacts
Run script               -> orchestration and operational retries
```

## Why this layout is easier to learn

The old job mixed everything in one file:

```text
Glue args
Spark session setup
quality rules
derived columns
output schema
S3 write
logging
```

The new layout lets you learn one layer at a time:

1. `SilverJobConfig`
   Understand inputs, paths, and month windows.
2. `normalize_schema`
   Understand schema drift handling.
3. `apply_critical_quality_filters`
   Understand which raw rows are rejected.
4. `build_silver_dataframe`
   Understand derived metrics and quality flags.
5. `write_silver_dataframe`
   Understand how Silver is materialized.
6. `jobs/glue_silver_yellow_taxi.py`
   Understand how AWS Glue calls the module.

## Local Study Path

If you want to study this job end to end, read in this order:

1. `src/nyctx_glue_processor/silver_job.py`
2. `jobs/glue_silver_yellow_taxi.py`
3. `scripts/run_glue_job.sh`
4. `scripts/deploy_glue_job.sh`

That order mirrors the real execution model:

```text
business transform -> Glue runtime -> operational trigger -> deployment
```

## Deploy Flow

AWS Glue cannot import the local Python package unless it is uploaded as an
artifact. The deploy flow is now:

1. Build `dist/nyctx_glue_processor.zip`
2. Upload the Glue entry script to S3
3. Upload the package zip to S3
4. Configure Glue with `--extra-py-files`

This is closer to a real production packaging model than uploading a single
monolithic script.

## Usage

```bash
# Deploy the Glue job and package artifacts
bash nyctx-glue-processor/scripts/deploy_glue_job.sh

# Upload artifacts only for Terraform-managed jobs
bash nyctx-glue-processor/scripts/deploy_glue_job_terraform.sh \
  --bucket nyc-taxi-lakehouse-tntk-dev

# Run one month
bash nyctx-glue-processor/scripts/run_glue_job.sh 2024 1

# Run many months from a file
bash nyctx-glue-processor/scripts/run_glue_job.sh \
  --months-file config/recovery_sample_months.txt
```

## Local Validation

```bash
cd nyctx-glue-processor
uv run pytest
python3 scripts/build_glue_package.py dist/nyctx_glue_processor.zip
bash -n scripts/deploy_glue_job.sh
```

## Next Production Upgrades

Good next steps if you want to keep leveling this up:

1. Add local PySpark tests for `build_silver_dataframe`
2. Replace direct overwrite with a safer staging/promote write pattern
3. Emit structured row-count and warning-count metrics
4. Add schema/version metadata to the Silver output contract
