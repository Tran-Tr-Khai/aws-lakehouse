#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

AWS_REGION="${AWS_REGION:-${AWS_DEFAULT_REGION:-us-east-1}}"
AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID:-767398123193}"
BUCKET="${NYCTX_S3_BUCKET:-nyc-taxi-lakehouse-tntk}"
JOB_NAME="${NYCTX_GLUE_JOB_NAME:-glue-silver-yellow-taxi}"
ROLE_ARN="${NYCTX_GLUE_ROLE_ARN:-arn:aws:iam::${AWS_ACCOUNT_ID}:role/glue-nyc-taxi-lakehouse-role}"

LOCAL_SCRIPT_PATH="${PROJECT_ROOT}/nyctx-glue-processor/jobs/glue_silver_yellow_taxi.py"
PACKAGE_BUILD_SCRIPT="${PROJECT_ROOT}/nyctx-glue-processor/scripts/build_glue_package.py"
BUILD_DIR="${PROJECT_ROOT}/nyctx-glue-processor/dist"
LOCAL_PACKAGE_PATH="${BUILD_DIR}/nyctx_glue_processor.zip"
S3_SCRIPT_PATH="${S3_SCRIPT_PATH:-s3://${BUCKET}/scripts/glue_silver_yellow_taxi.py}"
S3_PACKAGE_PATH="${S3_PACKAGE_PATH:-s3://${BUCKET}/artifacts/nyctx_glue_processor.zip}"

GLUE_VERSION="${GLUE_VERSION:-4.0}"
WORKER_TYPE="${WORKER_TYPE:-G.1X}"
NUMBER_OF_WORKERS="${NUMBER_OF_WORKERS:-2}"
TIMEOUT_MINUTES="${TIMEOUT_MINUTES:-15}"
MAX_CONCURRENT_RUNS="${MAX_CONCURRENT_RUNS:-1}"
SPARK_UI_ENABLED="${SPARK_UI_ENABLED:-true}"
SPARK_EVENT_LOGS_PATH="${SPARK_EVENT_LOGS_PATH:-s3://${BUCKET}/spark-ui/}"
DEFAULT_YEAR="${DEFAULT_YEAR:-2024}"
DEFAULT_MONTH="${DEFAULT_MONTH:-1}"

echo "========================================"
echo "Deploying AWS Glue job"
echo "Job name: ${JOB_NAME}"
echo "Bucket: ${BUCKET}"
echo "Script: ${S3_SCRIPT_PATH}"
echo "Package: ${S3_PACKAGE_PATH}"
echo "========================================"

[[ -f "${LOCAL_SCRIPT_PATH}" ]] || { echo "ERROR: Local script not found: ${LOCAL_SCRIPT_PATH}"; exit 1; }
[[ -f "${PACKAGE_BUILD_SCRIPT}" ]] || { echo "ERROR: Package build script not found: ${PACKAGE_BUILD_SCRIPT}"; exit 1; }

mkdir -p "${BUILD_DIR}"
python3 "${PACKAGE_BUILD_SCRIPT}" "${LOCAL_PACKAGE_PATH}"

echo "Uploading Glue script to S3..."
aws s3 cp "${LOCAL_SCRIPT_PATH}" "${S3_SCRIPT_PATH}" --region "${AWS_REGION}"

echo "Uploading Glue package to S3..."
aws s3 cp "${LOCAL_PACKAGE_PATH}" "${S3_PACKAGE_PATH}" --region "${AWS_REGION}"

JOB_CONFIG=$(
  cat <<EOF
{
  "Role": "${ROLE_ARN}",
  "Command": {
    "Name": "glueetl",
    "ScriptLocation": "${S3_SCRIPT_PATH}",
    "PythonVersion": "3"
  },
  "GlueVersion": "${GLUE_VERSION}",
  "WorkerType": "${WORKER_TYPE}",
  "NumberOfWorkers": ${NUMBER_OF_WORKERS},
  "Timeout": ${TIMEOUT_MINUTES},
  "ExecutionProperty": {
    "MaxConcurrentRuns": ${MAX_CONCURRENT_RUNS}
  },
  "DefaultArguments": {
    "--job-language": "python",
    "--enable-spark-ui": "${SPARK_UI_ENABLED}",
    "--spark-event-logs-path": "${SPARK_EVENT_LOGS_PATH}",
    "--extra-py-files": "${S3_PACKAGE_PATH}",
    "--BUCKET": "${BUCKET}",
    "--YEAR": "${DEFAULT_YEAR}",
    "--MONTH": "${DEFAULT_MONTH}"
  }
}
EOF
)

if aws glue get-job --job-name "${JOB_NAME}" --region "${AWS_REGION}" >/dev/null 2>&1; then
  echo "Glue job exists. Updating job..."
  aws glue update-job \
    --job-name "${JOB_NAME}" \
    --region "${AWS_REGION}" \
    --job-update "${JOB_CONFIG}"
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
    --execution-property "{
      \"MaxConcurrentRuns\": ${MAX_CONCURRENT_RUNS}
    }" \
    --default-arguments "{
      \"--job-language\": \"python\",
      \"--extra-py-files\": \"${S3_PACKAGE_PATH}\",
      \"--BUCKET\": \"${BUCKET}\",
      \"--YEAR\": \"${DEFAULT_YEAR}\",
      \"--MONTH\": \"${DEFAULT_MONTH}\"
    }"
  echo "Glue job created successfully."
fi

echo "========================================"
echo "Deployment completed"
echo "========================================"
