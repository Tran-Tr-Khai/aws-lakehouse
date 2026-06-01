#!/usr/bin/env bash

set -euo pipefail

AWS_REGION="${AWS_REGION:-${AWS_DEFAULT_REGION:-us-east-1}}"
S3_BUCKET="${NYCTX_S3_BUCKET:-nyc-taxi-lakehouse-tntk-dev}"
WORKGROUP="${NYCTX_ATHENA_WORKGROUP:-wg_nyc_taxi_lakehouse_dev}"
OUTPUT_LOCATION="${NYCTX_ATHENA_OUTPUT_LOCATION:-s3://${S3_BUCKET}/athena-results/}"
DATABASE="${NYCTX_ATHENA_DATABASE:-nyc_taxi_lakehouse_dev}"
SILVER_TABLE="${NYCTX_ATHENA_SILVER_TABLE:-silver_yellow_taxi}"
SILVER_LOCATION="${NYCTX_ATHENA_SILVER_LOCATION:-s3://${S3_BUCKET}/silver/yellow_taxi/}"
ZONE_LOOKUP_LOCATION="${NYCTX_ZONE_LOOKUP_LOCATION:-s3://${S3_BUCKET}/reference/taxi_zone_lookup/}"
ZONE_CENTROIDS_LOCATION="${NYCTX_ZONE_CENTROIDS_LOCATION:-s3://${S3_BUCKET}/reference/taxi_zone_centroids/}"
POLL_SECONDS="${NYCTX_ATHENA_POLL_SECONDS:-5}"

SQL_FILE=""
LABEL="athena_query"

if [[ "${SILVER_LOCATION}" != */ ]]; then
  SILVER_LOCATION="${SILVER_LOCATION}/"
fi

if [[ "${ZONE_LOOKUP_LOCATION}" != */ ]]; then
  ZONE_LOOKUP_LOCATION="${ZONE_LOOKUP_LOCATION}/"
fi

if [[ "${ZONE_CENTROIDS_LOCATION}" != */ ]]; then
  ZONE_CENTROIDS_LOCATION="${ZONE_CENTROIDS_LOCATION}/"
fi

render_sql_template() {
  local rendered="$1"

  rendered="${rendered//__NYCTX_ATHENA_DATABASE__/${DATABASE}}"
  rendered="${rendered//__NYCTX_ATHENA_SILVER_TABLE__/${SILVER_TABLE}}"
  rendered="${rendered//__NYCTX_ATHENA_SILVER_LOCATION__/${SILVER_LOCATION}}"
  rendered="${rendered//__NYCTX_ZONE_LOOKUP_LOCATION__/${ZONE_LOOKUP_LOCATION}}"
  rendered="${rendered//__NYCTX_ZONE_CENTROIDS_LOCATION__/${ZONE_CENTROIDS_LOCATION}}"

  printf '%s' "${rendered}"
}

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
echo "[INFO] database=${DATABASE}"
echo "[INFO] silver_table=${SILVER_TABLE}"
echo "[INFO] silver_location=${SILVER_LOCATION}"
echo "[INFO] zone_lookup_location=${ZONE_LOOKUP_LOCATION}"
echo "[INFO] zone_centroids_location=${ZONE_CENTROIDS_LOCATION}"
echo "[INFO] workgroup=${WORKGROUP}"
echo "[INFO] output_location=${OUTPUT_LOCATION}"
echo "[INFO] region=${AWS_REGION}"
echo "========================================"

query_string="$(render_sql_template "$(<"${SQL_FILE}")")"

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
