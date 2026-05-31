# nyctx-glue-processor

AWS Glue PySpark jobs for Silver layer transformation.

## Jobs

| Job | Description |
|-----|-------------|
| `jobs/glue_silver_yellow_taxi.py` | Clean Bronze → Silver: filter, enrich, quality flags |

## Scripts

| Script | Description |
|--------|-------------|
| `scripts/deploy_glue_job.sh` | Upload script to S3 and create/update Glue job |
| `scripts/deploy_glue_job_terraform.sh` | Upload Glue script artifact to S3 for Terraform-managed Glue jobs |
| `scripts/run_glue_job.sh` | Trigger a Glue job run for given year/month |

## Usage

```bash
# Deploy job to AWS Glue
bash nyctx-glue-processor/scripts/deploy_glue_job.sh

# Upload script artifact for Terraform-managed dev Glue job
AWS_PROFILE=nyc-taxi bash nyctx-glue-processor/scripts/deploy_glue_job_terraform.sh \
  --bucket nyc-taxi-lakehouse-tntk-dev

# Run job
bash nyctx-glue-processor/scripts/run_glue_job.sh 2024 1
```
