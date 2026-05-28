#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
DBT_PROJECT_DIR="${PROJECT_ROOT}/nyctx-dbt-transformer"

SELECTOR="dashboard_daily_revenue"
TEST_SELECT="dim_date dim_hour dim_payment_type dim_rate_code dim_vendor mart_daily_trip_revenue"
RUN_TESTS="true"

usage() {
  echo "Usage:"
  echo "  $0 [--selector dashboard_daily_revenue] [--test-select \"dim_date mart_daily_trip_revenue\"] [--skip-tests]"
  echo
  echo "Examples:"
  echo "  $0"
  echo "  $0 --selector dashboard_daily_revenue"
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
    --skip-tests)
      RUN_TESTS="false"
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
export NYCTX_ATHENA_WORKGROUP="${NYCTX_ATHENA_WORKGROUP:-wg_nyc_taxi_lakehouse}"
export NYCTX_ATHENA_OUTPUT_LOCATION="${NYCTX_ATHENA_OUTPUT_LOCATION:-s3://nyc-taxi-lakehouse-tntk/athena-results/}"
export NYCTX_ATHENA_DATABASE="${NYCTX_ATHENA_DATABASE:-nyc_taxi_lakehouse}"
export NYCTX_DBT_GOLD_S3_BASE="${NYCTX_DBT_GOLD_S3_BASE:-s3://nyc-taxi-lakehouse-tntk/gold}"

echo "========================================"
echo "[INFO] step=dbt_gold status=started"
echo "[INFO] project_dir=${DBT_PROJECT_DIR}"
echo "[INFO] database=${NYCTX_ATHENA_DATABASE}"
echo "[INFO] workgroup=${NYCTX_ATHENA_WORKGROUP}"
echo "[INFO] gold_s3_base=${NYCTX_DBT_GOLD_S3_BASE}"
echo "[INFO] selector=${SELECTOR}"
echo "[INFO] run_tests=${RUN_TESTS}"
echo "========================================"

cd "${DBT_PROJECT_DIR}"

uv run dbt debug --profiles-dir "${DBT_PROJECT_DIR}"

uv run dbt run \
  --profiles-dir "${DBT_PROJECT_DIR}" \
  --selector "${SELECTOR}"

if [[ "${RUN_TESTS}" == "true" ]]; then
  uv run dbt test \
    --profiles-dir "${DBT_PROJECT_DIR}" \
    --select ${TEST_SELECT} \
    --exclude test_name:relationships
else
  echo "[INFO] step=dbt_gold_tests status=skipped"
fi

echo "========================================"
echo "[INFO] step=dbt_gold status=succeeded"
echo "========================================"
