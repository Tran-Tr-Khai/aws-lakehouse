#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

AWS_REGION="${AWS_REGION:-${AWS_DEFAULT_REGION:-us-east-1}}"
BUCKET="${NYCTX_S3_BUCKET:-nyc-taxi-lakehouse-tntk-dev}"
LOCAL_SCRIPT_PATH="${LOCAL_SCRIPT_PATH:-${PROJECT_ROOT}/nyctx-glue-processor/jobs/glue_silver_yellow_taxi.py}"
S3_SCRIPT_PATH="${S3_SCRIPT_PATH:-s3://${BUCKET}/scripts/glue_silver_yellow_taxi.py}"

usage() {
  echo "Usage:"
  echo "  $0 [--bucket nyc-taxi-lakehouse-tntk-dev] [--s3-script-path s3://bucket/scripts/glue_silver_yellow_taxi.py]"
  echo
  echo "Environment overrides:"
  echo "  AWS_REGION or AWS_DEFAULT_REGION"
  echo "  AWS_PROFILE"
  echo "  NYCTX_S3_BUCKET"
  echo "  LOCAL_SCRIPT_PATH"
  echo "  S3_SCRIPT_PATH"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --bucket)
      BUCKET="$2"
      S3_SCRIPT_PATH="s3://${BUCKET}/scripts/glue_silver_yellow_taxi.py"
      shift 2
      ;;
    --s3-script-path)
      S3_SCRIPT_PATH="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "ERROR: Unknown argument: $1"
      usage
      exit 1
      ;;
  esac
done

if [[ ! -f "${LOCAL_SCRIPT_PATH}" ]]; then
  echo "ERROR: Local Glue script not found: ${LOCAL_SCRIPT_PATH}"
  exit 1
fi

echo "========================================"
echo "Uploading Glue script artifact"
echo "Region: ${AWS_REGION}"
echo "Local:  ${LOCAL_SCRIPT_PATH}"
echo "S3:     ${S3_SCRIPT_PATH}"
echo "========================================"

aws s3 cp "${LOCAL_SCRIPT_PATH}" "${S3_SCRIPT_PATH}" --region "${AWS_REGION}"

echo "========================================"
echo "Upload completed"
echo "========================================"
