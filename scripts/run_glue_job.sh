#!/usr/bin/env bash
set -euo pipefail

AWS_REGION="us-east-1"
BUCKET="nyc-taxi-lakehouse-tntk"
JOB_NAME="glue-silver-yellow-taxi"

YEAR="${1:-2024}"
MONTH="${2:-1}"

echo "========================================"
echo "Starting AWS Glue job"
echo "Job name: ${JOB_NAME}"
echo "Year: ${YEAR}"
echo "Month: ${MONTH}"
echo "Bucket: ${BUCKET}"
echo "========================================"

JOB_RUN_ID=$(
  aws glue start-job-run \
    --job-name "${JOB_NAME}" \
    --region "${AWS_REGION}" \
    --arguments "{
      \"--BUCKET\": \"${BUCKET}\",
      \"--YEAR\": \"${YEAR}\",
      \"--MONTH\": \"${MONTH}\"
    }" \
    --query "JobRunId" \
    --output text
)

echo "Glue job started."
echo "JobRunId: ${JOB_RUN_ID}"

echo ""
echo "Check status with:"
echo "aws glue get-job-run --job-name ${JOB_NAME} --run-id ${JOB_RUN_ID} --region ${AWS_REGION}"

echo ""
echo "Or open AWS Console:"
echo "AWS Glue → ETL jobs → ${JOB_NAME} → Runs"

echo ""
echo "After it succeeds, check Silver output:"
printf "aws s3 ls s3://%s/silver/yellow_taxi/year=%s/month=%02d/ --region %s\n" \
  "${BUCKET}" "${YEAR}" "${MONTH}" "${AWS_REGION}"