#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
DBT_PROJECT_DIR="${PROJECT_ROOT}/nyctx-dbt-transformer"

SELECTOR="dashboard_daily_revenue"
TEST_SELECT="dim_date dim_hour dim_payment_type dim_rate_code dim_vendor mart_daily_trip_revenue"
MONTHS_FILE="${PROJECT_ROOT}/config/recovery_sample_months.txt"
RUN_TESTS="true"
FORCE_RUN="false"

GOLD_TABLES=(
  dim_date
  dim_hour
  dim_payment_type
  dim_rate_code
  dim_vendor
  fact_trip
  mart_daily_trip_revenue
)

run_dbt() {
  if [[ -n "${DBT_BIN:-}" && -x "${DBT_BIN}" ]]; then
    "${DBT_BIN}" "$@"
    return
  fi

  if command -v dbt >/dev/null 2>&1; then
    dbt "$@"
    return
  fi

  if command -v uv >/dev/null 2>&1; then
    uv run dbt "$@"
    return
  fi

  echo "[ERROR] step=dbt_command status=failed reason=dbt_or_uv_not_found"
  exit 1
}

parse_s3_uri() {
  local uri="${1%/}"
  local without_scheme="${uri#s3://}"
  S3_BUCKET="${without_scheme%%/*}"
  S3_PREFIX="${without_scheme#*/}"

  if [[ "${S3_PREFIX}" == "${without_scheme}" ]]; then
    S3_PREFIX=""
  fi

  if [[ -n "${S3_PREFIX}" ]]; then
    S3_PREFIX="${S3_PREFIX%/}/"
  fi
}

s3_prefix_has_objects() {
  local s3_uri="$1"
  local first_object_key

  parse_s3_uri "${s3_uri}"
  first_object_key="$(
    aws s3api list-objects-v2 \
      --bucket "${S3_BUCKET}" \
      --prefix "${S3_PREFIX}" \
      --max-items 1 \
      --query "Contents[0].Key" \
      --output text
  )"

  [[ -n "${first_object_key}" && "${first_object_key}" != "None" ]]
}

glue_table_location() {
  local table_name="$1"

  aws glue get-table \
    --database-name "${NYCTX_ATHENA_DATABASE}" \
    --name "${table_name}" \
    --query "Table.StorageDescriptor.Location" \
    --output text
}

gold_outputs_complete() {
  if ! command -v aws >/dev/null 2>&1; then
    echo "[WARNING] step=gold_skip_check status=skipped reason=aws_cli_not_found"
    return 1
  fi

  if [[ ! -f "${MONTHS_FILE}" ]]; then
    echo "[WARNING] step=gold_skip_check status=missing months_file=${MONTHS_FILE}"
    return 1
  fi

  local table_name
  local table_location
  local fact_location

  for table_name in "${GOLD_TABLES[@]}"; do
    if ! table_location="$(glue_table_location "${table_name}" 2>/dev/null)"; then
      echo "[INFO] step=gold_skip_check status=missing_table table=${table_name}"
      return 1
    fi

    if [[ "${table_location}" != s3://* ]]; then
      echo "[INFO] step=gold_skip_check status=invalid_location table=${table_name} location=${table_location}"
      return 1
    fi

    if ! s3_prefix_has_objects "${table_location}"; then
      echo "[INFO] step=gold_skip_check status=empty_table table=${table_name} location=${table_location}"
      return 1
    fi

    if [[ "${table_name}" == "fact_trip" ]]; then
      fact_location="${table_location%/}"
    fi
  done

  local period
  local clean_period
  local year
  local month

  while IFS= read -r period || [[ -n "${period}" ]]; do
    clean_period="${period%%#*}"
    clean_period="${clean_period//[[:space:]]/}"

    if [[ -z "${clean_period}" ]]; then
      continue
    fi

    year="${clean_period%-*}"
    month="${clean_period#*-}"

    if ! s3_prefix_has_objects "${fact_location}/year=${year}/month=${month}/"; then
      echo "[INFO] step=gold_skip_check status=missing_partition table=fact_trip period=${clean_period}"
      return 1
    fi
  done < "${MONTHS_FILE}"

  echo "[INFO] step=gold_skip_check status=complete"
  return 0
}

check_workgroup_allows_table_location() {
  if ! command -v aws >/dev/null 2>&1; then
    echo "[WARNING] step=workgroup_location_check status=skipped reason=aws_cli_not_found"
    return 0
  fi

  local enforce_config
  if ! enforce_config="$(
    aws athena get-work-group \
      --work-group "${NYCTX_DBT_ATHENA_WORKGROUP}" \
      --query "WorkGroup.Configuration.EnforceWorkGroupConfiguration" \
      --output text
  )"; then
    echo "[ERROR] step=workgroup_location_check status=failed reason=workgroup_lookup_failed workgroup=${NYCTX_DBT_ATHENA_WORKGROUP}"
    exit 1
  fi

  if [[ "${enforce_config}" == "True" ]]; then
    echo "[ERROR] step=workgroup_location_check status=failed reason=output_location_enforced workgroup=${NYCTX_DBT_ATHENA_WORKGROUP}"
    echo "[ERROR] Use a dbt workgroup with Override client-side settings disabled."
    exit 1
  fi

  echo "[INFO] step=workgroup_location_check status=passed workgroup=${NYCTX_DBT_ATHENA_WORKGROUP}"
}

usage() {
  echo "Usage:"
  echo "  $0 [--selector dashboard_daily_revenue] [--months-file config/recovery_sample_months.txt] [--test-select \"dim_date mart_daily_trip_revenue\"] [--skip-tests] [--force]"
  echo
  echo "Examples:"
  echo "  $0"
  echo "  $0 --selector dashboard_daily_revenue"
  echo "  $0 --months-file config/recovery_sample_months.txt"
  echo "  $0 --force"
  echo "  $0 --selector all_gold --test-select marts"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --selector)
      SELECTOR="$2"
      shift 2
      ;;
    --test-select)
      TEST_SELECT="$2"
      shift 2
      ;;
    --months-file)
      MONTHS_FILE="$2"
      shift 2
      ;;
    --skip-tests)
      RUN_TESTS="false"
      shift
      ;;
    --force)
      FORCE_RUN="true"
      shift
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

export AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-us-east-1}"
export AWS_PROFILE="${AWS_PROFILE:-default}"
export NYCTX_ATHENA_DATABASE="${NYCTX_ATHENA_DATABASE:-nyc_taxi_lakehouse}"
export NYCTX_DBT_ATHENA_WORKGROUP="${NYCTX_DBT_ATHENA_WORKGROUP:-wg_nyc_taxi_dbt}"
export NYCTX_DBT_ATHENA_OUTPUT_LOCATION="${NYCTX_DBT_ATHENA_OUTPUT_LOCATION:-s3://nyc-taxi-lakehouse-tntk/athena-results/dbt/}"
export NYCTX_DBT_GOLD_S3_BASE="${NYCTX_DBT_GOLD_S3_BASE:-s3://nyc-taxi-lakehouse-tntk/gold}"

if [[ "${MONTHS_FILE}" != /* ]]; then
  MONTHS_FILE="${PROJECT_ROOT}/${MONTHS_FILE}"
fi

echo "========================================"
echo "[INFO] step=dbt_gold status=started"
echo "[INFO] project_dir=${DBT_PROJECT_DIR}"
echo "[INFO] database=${NYCTX_ATHENA_DATABASE}"
echo "[INFO] workgroup=${NYCTX_DBT_ATHENA_WORKGROUP}"
echo "[INFO] athena_output=${NYCTX_DBT_ATHENA_OUTPUT_LOCATION}"
echo "[INFO] gold_s3_base=${NYCTX_DBT_GOLD_S3_BASE}"
echo "[INFO] selector=${SELECTOR}"
echo "[INFO] months_file=${MONTHS_FILE}"
echo "[INFO] run_tests=${RUN_TESTS}"
echo "[INFO] force=${FORCE_RUN}"
echo "========================================"

cd "${DBT_PROJECT_DIR}"

if [[ "${FORCE_RUN}" != "true" ]] && gold_outputs_complete; then
  echo "[INFO] step=dbt_gold status=skipped reason=gold_outputs_already_complete"
  exit 0
fi

check_workgroup_allows_table_location

run_dbt debug --profiles-dir "${DBT_PROJECT_DIR}"

run_dbt run \
  --profiles-dir "${DBT_PROJECT_DIR}" \
  --selector "${SELECTOR}"

if [[ "${RUN_TESTS}" == "true" ]]; then
  run_dbt test \
    --profiles-dir "${DBT_PROJECT_DIR}" \
    --select ${TEST_SELECT} \
    --exclude test_name:relationships
else
  echo "[INFO] step=dbt_gold_tests status=skipped"
fi

echo "========================================"
echo "[INFO] step=dbt_gold status=succeeded"
echo "========================================"
