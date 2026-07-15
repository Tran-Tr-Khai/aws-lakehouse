#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

AWS_REGION="${AWS_REGION:-${AWS_DEFAULT_REGION:-us-east-1}}"
BUCKET="${NYCTX_S3_BUCKET:-nyc-taxi-lakehouse-tntk}"
LOCAL_SCRIPT_PATH="${LOCAL_SCRIPT_PATH:-${PROJECT_ROOT}/nyctx-glue-processor/jobs/glue_silver_yellow_taxi.py}"
PACKAGE_BUILD_SCRIPT="${PROJECT_ROOT}/nyctx-glue-processor/scripts/build_glue_package.py"
BUILD_DIR="${PROJECT_ROOT}/nyctx-glue-processor/dist"
LOCAL_PACKAGE_PATH="${BUILD_DIR}/nyctx_glue_processor.zip"
S3_SCRIPT_PATH="${S3_SCRIPT_PATH:-s3://${BUCKET}/scripts/glue_silver_yellow_taxi.py}"
S3_PACKAGE_PATH="${S3_PACKAGE_PATH:-s3://${BUCKET}/artifacts/nyctx_glue_processor.zip}"

usage() {
  echo "Usage:"
  echo "  $0 [--bucket nyc-taxi-lakehouse-tntk]"
  echo "     [--s3-script-path s3://bucket/scripts/glue_silver_yellow_taxi.py]"
  echo "     [--s3-package-path s3://bucket/artifacts/nyctx_glue_processor.zip]"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --bucket)
      BUCKET="$2"
      S3_SCRIPT_PATH="s3://${BUCKET}/scripts/glue_silver_yellow_taxi.py"
      S3_PACKAGE_PATH="s3://${BUCKET}/artifacts/nyctx_glue_processor.zip"
      shift 2
      ;;
    --s3-script-path)
      S3_SCRIPT_PATH="$2"
      shift 2
      ;;
    --s3-package-path)
      S3_PACKAGE_PATH="$2"
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

[[ -f "${LOCAL_SCRIPT_PATH}" ]] || { echo "ERROR: Local Glue script not found: ${LOCAL_SCRIPT_PATH}"; exit 1; }
[[ -f "${PACKAGE_BUILD_SCRIPT}" ]] || { echo "ERROR: Package build script not found: ${PACKAGE_BUILD_SCRIPT}"; exit 1; }

mkdir -p "${BUILD_DIR}"
python3 "${PACKAGE_BUILD_SCRIPT}" "${LOCAL_PACKAGE_PATH}"

echo "========================================"
echo "Uploading Glue artifacts"
echo "Region:  ${AWS_REGION}"
echo "Script:  ${S3_SCRIPT_PATH}"
echo "Package: ${S3_PACKAGE_PATH}"
echo "========================================"

aws s3 cp "${LOCAL_SCRIPT_PATH}" "${S3_SCRIPT_PATH}" --region "${AWS_REGION}"
aws s3 cp "${LOCAL_PACKAGE_PATH}" "${S3_PACKAGE_PATH}" --region "${AWS_REGION}"

echo "========================================"
echo "Upload completed"
echo "========================================"
