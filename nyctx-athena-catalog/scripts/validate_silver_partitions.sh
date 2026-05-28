#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

AWS_REGION="${AWS_REGION:-${AWS_DEFAULT_REGION:-us-east-1}}"
WORKGROUP="${NYCTX_ATHENA_WORKGROUP:-wg_nyc_taxi_lakehouse}"
OUTPUT_LOCATION="${NYCTX_ATHENA_OUTPUT_LOCATION:-s3://nyc-taxi-lakehouse-tntk/athena-results/}"
DATABASE="${NYCTX_ATHENA_DATABASE:-nyc_taxi_lakehouse}"
TABLE="${NYCTX_ATHENA_SILVER_TABLE:-silver_yellow_taxi}"
POLL_SECONDS="${NYCTX_ATHENA_POLL_SECONDS:-5}"

MONTHS_FILE=""

usage() {
  echo "Usage:"
  echo "  $0 --months-file config/recovery_sample_months.txt"
}

run_count_query() {
  local year="$1"
  local month="$2"
  local sql_file
  local query_execution_id
  local state
  local reason
  local row_count
  local data_scanned_bytes
  local query_string

  sql_file="$(mktemp)"

  cat > "${sql_file}" <<SQL
SELECT
    COUNT(*) AS trip_count
FROM ${DATABASE}.${TABLE}
WHERE year = '${year}'
  AND month = '${month}';
SQL

  query_string="$(<"${sql_file}")"

  query_execution_id=$(
    aws athena start-query-execution \
      --region "${AWS_REGION}" \
      --work-group "${WORKGROUP}" \
      --query-string "${query_string}" \
      --result-configuration "OutputLocation=${OUTPUT_LOCATION}" \
      --query "QueryExecutionId" \
      --output text
  )

  rm -f "${sql_file}"

  echo "[INFO] period=${year}-${month} query_execution_id=${query_execution_id}"

  while true; do
    state=$(
      aws athena get-query-execution \
        --region "${AWS_REGION}" \
        --query-execution-id "${query_execution_id}" \
        --query "QueryExecution.Status.State" \
        --output text
    )

    echo "[INFO] period=${year}-${month} state=${state}"

    case "${state}" in
      SUCCEEDED)
        row_count=$(
          aws athena get-query-results \
            --region "${AWS_REGION}" \
            --query-execution-id "${query_execution_id}" \
            --query "ResultSet.Rows[1].Data[0].VarCharValue" \
            --output text
        )

        data_scanned_bytes=$(
          aws athena get-query-execution \
            --region "${AWS_REGION}" \
            --query-execution-id "${query_execution_id}" \
            --query "QueryExecution.Statistics.DataScannedInBytes" \
            --output text
        )

        echo "[INFO] period=${year}-${month} row_count=${row_count} data_scanned_bytes=${data_scanned_bytes}"

        if [[ "${row_count}" == "None" || "${row_count}" -le 0 ]]; then
          echo "[ERROR] period=${year}-${month} validation=failed reason=no_silver_rows"
          return 1
        fi

        echo "[INFO] period=${year}-${month} validation=passed"
        return 0
        ;;
      FAILED|CANCELLED)
        reason=$(
          aws athena get-query-execution \
            --region "${AWS_REGION}" \
            --query-execution-id "${query_execution_id}" \
            --query "QueryExecution.Status.StateChangeReason" \
            --output text
        )

        echo "[ERROR] period=${year}-${month} validation=failed"
        echo "[ERROR] query_execution_id=${query_execution_id}"
        echo "[ERROR] reason=${reason}"
        return 1
        ;;
      *)
        sleep "${POLL_SECONDS}"
        ;;
    esac
  done
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --months-file)
      MONTHS_FILE="$2"
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

if [[ -z "${MONTHS_FILE}" ]]; then
  echo "[ERROR] Missing required --months-file argument."
  usage
  exit 1
fi

if [[ "${MONTHS_FILE}" != /* ]]; then
  MONTHS_FILE="${PROJECT_ROOT}/${MONTHS_FILE}"
fi

if [[ ! -f "${MONTHS_FILE}" ]]; then
  echo "[ERROR] Months file not found: ${MONTHS_FILE}"
  exit 1
fi

echo "========================================"
echo "[INFO] step=validate_silver_partitions status=started"
echo "[INFO] database=${DATABASE}"
echo "[INFO] table=${TABLE}"
echo "[INFO] months_file=${MONTHS_FILE}"
echo "[INFO] workgroup=${WORKGROUP}"
echo "[INFO] output_location=${OUTPUT_LOCATION}"
echo "[INFO] region=${AWS_REGION}"
echo "========================================"

validated_count=0

while IFS= read -r line; do
  year_month="$(echo "${line}" | xargs)"
  [[ -z "${year_month}" || "${year_month}" == \#* ]] && continue

  if [[ ! "${year_month}" =~ ^[0-9]{4}-[0-9]{2}$ ]]; then
    echo "[ERROR] Invalid year-month format: ${year_month}. Expected YYYY-MM."
    exit 1
  fi

  year="${year_month:0:4}"
  month="${year_month:5:2}"

  run_count_query "${year}" "${month}"
  validated_count=$((validated_count + 1))
done < "${MONTHS_FILE}"

echo "========================================"
echo "[INFO] step=validate_silver_partitions status=succeeded"
echo "[INFO] validated_months=${validated_count}"
echo "========================================"
