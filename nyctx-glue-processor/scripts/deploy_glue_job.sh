#!/usr/bin/env bash
set -euo pipefail

AWS_REGION="us-east-1"
AWS_ACCOUNT_ID="767398123193"

BUCKET="nyc-taxi-lakehouse-tntk"
JOB_NAME="glue-silver-yellow-taxi"
ROLE_ARN="arn:aws:iam::${AWS_ACCOUNT_ID}:role/glue-nyc-taxi-lakehouse-role"

LOCAL_SCRIPT_PATH="nyctx-glue-processor/jobs/glue_silver_yellow_taxi.py"
S3_SCRIPT_PATH="s3://${BUCKET}/scripts/glue_silver_yellow_taxi.py"

GLUE_VERSION="4.0"
WORKER_TYPE="G.1X"
NUMBER_OF_WORKERS=2
TIMEOUT_MINUTES=15

DEFAULT_YEAR="2024"
DEFAULT_MONTH="1"

echo "========================================"
echo "Deploying AWS Glue job"
echo "Job name: ${JOB_NAME}"
echo "Bucket: ${BUCKET}"
echo "Script: ${S3_SCRIPT_PATH}"
echo "========================================"

if [[ ! -f "${LOCAL_SCRIPT_PATH}" ]]; then
  echo "ERROR: Local script not found: ${LOCAL_SCRIPT_PATH}"
  exit 1
fi

echo "Uploading Glue script to S3..."
aws s3 cp "${LOCAL_SCRIPT_PATH}" "${S3_SCRIPT_PATH}" --region "${AWS_REGION}"

echo "Checking if Glue job already exists..."
if aws glue get-job --job-name "${JOB_NAME}" --region "${AWS_REGION}" >/dev/null 2>&1; then
  echo "Glue job exists. Updating job..."

  aws glue update-job \
    --job-name "${JOB_NAME}" \
    --region "${AWS_REGION}" \
    --job-update "{
      \"Role\": \"${ROLE_ARN}\",
      \"Command\": {
        \"Name\": \"glueetl\",
        \"ScriptLocation\": \"${S3_SCRIPT_PATH}\",
        \"PythonVersion\": \"3\"
      },
      \"GlueVersion\": \"${GLUE_VERSION}\",
      \"WorkerType\": \"${WORKER_TYPE}\",
      \"NumberOfWorkers\": ${NUMBER_OF_WORKERS},
      \"Timeout\": ${TIMEOUT_MINUTES},
      \"DefaultArguments\": {
        \"--job-language\": \"python\",
        \"--BUCKET\": \"${BUCKET}\",
        \"--YEAR\": \"${DEFAULT_YEAR}\",
        \"--MONTH\": \"${DEFAULT_MONTH}\"
      }
    }"

  echo "Glue job updated successfully."
else
  echo "Glue job does not exist. Creating job..."

  aws glue create-job \
    --name "${JOB_NAME}" \
    --role "${ROLE_ARN}" \
    --region "${AWS_REGION}" \
    --command "{
      \"Name\": \"glueetl\",
      \"ScriptLocation\": \"${S3_SCRIPT_PATH}\",
      \"PythonVersion\": \"3\"
    }" \
    --glue-version "${GLUE_VERSION}" \
    --worker-type "${WORKER_TYPE}" \
    --number-of-workers "${NUMBER_OF_WORKERS}" \
    --timeout "${TIMEOUT_MINUTES}" \
    --default-arguments "{
      \"--job-language\": \"python\",
      \"--BUCKET\": \"${BUCKET}\",
      \"--YEAR\": \"${DEFAULT_YEAR}\",
      \"--MONTH\": \"${DEFAULT_MONTH}\"
    }"

  echo "Glue job created successfully."
fi

echo "========================================"
echo "Deployment completed"
echo "========================================"