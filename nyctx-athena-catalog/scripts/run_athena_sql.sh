#!/usr/bin/env bash

set -euo pipefail

AWS_REGION="${AWS_REGION:-${AWS_DEFAULT_REGION:-us-east-1}}"
WORKGROUP="${NYCTX_ATHENA_WORKGROUP:-wg_nyc_taxi_lakehouse}"
OUTPUT_LOCATION="${NYCTX_ATHENA_OUTPUT_LOCATION:-s3://nyc-taxi-lakehouse-tntk/athena-results/}"
POLL_SECONDS="${NYCTX_ATHENA_POLL_SECONDS:-5}"

SQL_FILE=""
LABEL="athena_query"

usage() {
  echo "Usage:"
  echo "  $0 --file nyctx-athena-catalog/ddl/create_database.sql [--label create_database]"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --file)
      SQL_FILE="$2"
      shift 2
      ;;
    --label)
      LABEL="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "[ERROR] Unknown argument: $1"
      usage
      exit 1
      ;;
  esac
done

if [[ -z "${SQL_FILE}" ]]; then
  echo "[ERROR] Missing required --file argument."
  usage
  exit 1
fi

if [[ ! -f "${SQL_FILE}" ]]; then
  echo "[ERROR] SQL file not found: ${SQL_FILE}"
  exit 1
fi

echo "========================================"
echo "[INFO] step=athena_query status=started"
echo "[INFO] label=${LABEL}"
echo "[INFO] sql_file=${SQL_FILE}"
echo "[INFO] workgroup=${WORKGROUP}"
echo "[INFO] output_location=${OUTPUT_LOCATION}"
echo "[INFO] region=${AWS_REGION}"
echo "========================================"

query_string="$(<"${SQL_FILE}")"

query_execution_id=$(
  aws athena start-query-execution \
    --region "${AWS_REGION}" \
    --work-group "${WORKGROUP}" \
    --query-string "${query_string}" \
    --result-configuration "OutputLocation=${OUTPUT_LOCATION}" \
    --query "QueryExecutionId" \
    --output text
)

echo "[INFO] query_execution_id=${query_execution_id}"

while true; do
  state=$(
    aws athena get-query-execution \
      --region "${AWS_REGION}" \
      --query-execution-id "${query_execution_id}" \
      --query "QueryExecution.Status.State" \
      --output text
  )

  echo "[INFO] query_execution_id=${query_execution_id} state=${state}"

  case "${state}" in
    SUCCEEDED)
      data_scanned_bytes=$(
        aws athena get-query-execution \
          --region "${AWS_REGION}" \
          --query-execution-id "${query_execution_id}" \
          --query "QueryExecution.Statistics.DataScannedInBytes" \
          --output text
      )

      echo "[INFO] step=athena_query status=succeeded"
      echo "[INFO] query_execution_id=${query_execution_id}"
      echo "[INFO] data_scanned_bytes=${data_scanned_bytes}"
      exit 0
      ;;
    FAILED|CANCELLED)
      reason=$(
        aws athena get-query-execution \
          --region "${AWS_REGION}" \
          --query-execution-id "${query_execution_id}" \
          --query "QueryExecution.Status.StateChangeReason" \
          --output text
      )

      echo "[ERROR] step=athena_query status=${state}"
      echo "[ERROR] query_execution_id=${query_execution_id}"
      echo "[ERROR] reason=${reason}"
      exit 1
      ;;
    *)
      sleep "${POLL_SECONDS}"
      ;;
  esac
done
