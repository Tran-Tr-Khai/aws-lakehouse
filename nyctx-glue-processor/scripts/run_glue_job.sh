#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

AWS_REGION="${AWS_REGION:-${AWS_DEFAULT_REGION:-us-east-1}}"
BUCKET="${NYCTX_S3_BUCKET:-nyc-taxi-lakehouse-tntk}"
JOB_NAME="${NYCTX_GLUE_JOB_NAME:-glue-silver-yellow-taxi}"
START_RETRIES="${NYCTX_GLUE_START_RETRIES:-10}"
START_RETRY_SECONDS="${NYCTX_GLUE_START_RETRY_SECONDS:-30}"
OUTPUT_FORMAT="${NYCTX_SILVER_OUTPUT_FORMAT:-iceberg}"
ATHENA_DATABASE="${NYCTX_ATHENA_DATABASE:-nyc_taxi_lakehouse}"
ICEBERG_TABLE="${NYCTX_ICEBERG_TABLE:-silver_yellow_taxi_iceberg}"
ICEBERG_SPARK_CONF="spark.sql.extensions=org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions --conf spark.sql.catalog.glue_catalog=org.apache.iceberg.spark.SparkCatalog --conf spark.sql.catalog.glue_catalog.warehouse=s3://${BUCKET}/ --conf spark.sql.catalog.glue_catalog.catalog-impl=org.apache.iceberg.aws.glue.GlueCatalog --conf spark.sql.catalog.glue_catalog.io-impl=org.apache.iceberg.aws.s3.S3FileIO --conf spark.sql.iceberg.handle-timestamp-without-timezone=true"

MONTHS_FILE=""
YEAR_MONTHS=()
ANNUAL_YEAR=""
FORCE=false

usage() {
  echo "Usage:"
  echo "  $0 --year 2024 [--force]"
  echo "  $0 2024 1 [--force]"
  echo "  $0 --year-months 2024-01 2020-04 [--force]"
  echo "  $0 --months-file config/recovery_sample_months.txt [--force]"
}

wait_for_job() {
  local job_run_id="$1"
  local period="$2"

  while true; do
    local state
    state=$(
      aws glue get-job-run \
        --job-name "${JOB_NAME}" \
        --run-id "${job_run_id}" \
        --region "${AWS_REGION}" \
        --query "JobRun.JobRunState" \
        --output text
    )

    echo "[STATUS] ${period} ${job_run_id}: ${state}"

    case "${state}" in
      SUCCEEDED)
        echo "[DONE] ${period}"
        return 0
        ;;
      FAILED|ERROR|TIMEOUT|STOPPED)
        echo "[FAILED] ${period}"

        aws glue get-job-run \
          --job-name "${JOB_NAME}" \
          --run-id "${job_run_id}" \
          --region "${AWS_REGION}" \
          --query "JobRun.ErrorMessage" \
          --output text

        return 1
        ;;
      *)
        sleep 30
        ;;
    esac
  done
}

start_job_with_retry() {
  local year_month="$1"
  local year="$2"
  local month_int="$3"
  local attempt=1
  local output

  while (( attempt <= START_RETRIES )); do
    if output=$(
      aws glue start-job-run \
        --job-name "${JOB_NAME}" \
        --region "${AWS_REGION}" \
        --arguments "{
          \"--BUCKET\": \"${BUCKET}\",
          \"--YEAR\": \"${year}\",
          \"--MONTH\": \"${month_int}\",
          \"--OUTPUT_FORMAT\": \"${OUTPUT_FORMAT}\",
          \"--ATHENA_DATABASE\": \"${ATHENA_DATABASE}\",
          \"--ICEBERG_TABLE\": \"${ICEBERG_TABLE}\",
          \"--datalake-formats\": \"iceberg\",
          \"--enable-glue-datacatalog\": \"true\",
          \"--conf\": \"${ICEBERG_SPARK_CONF}\"
        }" \
        --query "JobRunId" \
        --output text 2>&1
    ); then
      echo "${output}"
      return 0
    fi

    if [[ "${output}" == *"ConcurrentRunsExceededException"* && "${attempt}" -lt "${START_RETRIES}" ]]; then
      echo "[WAIT] ${year_month} Glue concurrency limit reached. Retry ${attempt}/${START_RETRIES} in ${START_RETRY_SECONDS}s." >&2
      sleep "${START_RETRY_SECONDS}"
      attempt=$((attempt + 1))
      continue
    fi

    echo "${output}" >&2
    return 1
  done
}

silver_output_exists() {
  if [[ "${OUTPUT_FORMAT}" == "iceberg" || "${OUTPUT_FORMAT}" == "both" ]]; then
    return 1
  fi

  local year="$1"
  local month="$2"
  local silver_prefix="s3://${BUCKET}/silver-parquet/yellow_taxi/year=${year}/month=${month}/"

  aws s3 ls "${silver_prefix}" --region "${AWS_REGION}" 2>/dev/null \
    | awk '{print $4}' \
    | grep -q '\.parquet$'
}

silver_year_output_exists() {
  if [[ "${OUTPUT_FORMAT}" == "iceberg" || "${OUTPUT_FORMAT}" == "both" ]]; then
    return 1
  fi

  local year="$1"
  local silver_prefix="s3://${BUCKET}/silver-parquet/yellow_taxi/year=${year}/"

  aws s3 ls "${silver_prefix}" --recursive --region "${AWS_REGION}" 2>/dev/null \
    | awk '{print $4}' \
    | grep -q '\.parquet$'
}

show_silver_output() {
  local parquet_prefix="$1"

  echo "[SILVER OUTPUT]"
  case "${OUTPUT_FORMAT}" in
    parquet)
      aws s3 ls "${parquet_prefix}" --recursive --region "${AWS_REGION}"
      ;;
    iceberg)
      aws glue get-table \
        --database-name "${ATHENA_DATABASE}" \
        --name "${ICEBERG_TABLE}" \
        --region "${AWS_REGION}" \
        --query "Table.Parameters.metadata_location" \
        --output text
      ;;
    both)
      aws s3 ls "${parquet_prefix}" --recursive --region "${AWS_REGION}"
      aws glue get-table \
        --database-name "${ATHENA_DATABASE}" \
        --name "${ICEBERG_TABLE}" \
        --region "${AWS_REGION}" \
        --query "Table.Parameters.metadata_location" \
        --output text
      ;;
  esac
}

run_one_month() {
  local year_month="$1"

  if [[ ! "${year_month}" =~ ^[0-9]{4}-[0-9]{2}$ ]]; then
    echo "ERROR: Invalid year-month format: ${year_month}. Expected YYYY-MM."
    exit 1
  fi

  local year="${year_month:0:4}"
  local month="${year_month:5:2}"
  local month_int=$((10#${month}))

  if (( month_int < 1 || month_int > 12 )); then
    echo "ERROR: Invalid month: ${month}"
    exit 1
  fi

  if [[ "${FORCE}" == false ]] && silver_output_exists "${year}" "${month}"; then
    echo "[SKIP] Silver output already exists for ${year_month}."
    echo "       Use --force to rerun Glue and overwrite this partition."
    return 0
  fi

  echo "========================================"
  echo "Starting AWS Glue job"
  echo "Job name: ${JOB_NAME}"
  echo "Period: ${year_month}"
  echo "Bucket: ${BUCKET}"
  echo "Output format: ${OUTPUT_FORMAT}"
  echo "Iceberg table: ${ATHENA_DATABASE}.${ICEBERG_TABLE}"
  echo "========================================"

  local job_run_id
  job_run_id="$(start_job_with_retry "${year_month}" "${year}" "${month_int}")"

  echo "[STARTED] ${year_month} -> ${job_run_id}"

  wait_for_job "${job_run_id}" "${year_month}"

  show_silver_output "s3://${BUCKET}/silver-parquet/yellow_taxi/year=${year}/month=${month}/"
}

run_one_year() {
  local year="$1"

  if [[ ! "${year}" =~ ^[0-9]{4}$ ]]; then
    echo "ERROR: Invalid year format: ${year}. Expected YYYY."
    exit 1
  fi

  if [[ "${FORCE}" == false ]] && silver_year_output_exists "${year}"; then
    echo "[SKIP] Silver output already exists for year ${year}."
    echo "       Use --force to rerun Glue and overwrite this year partition set."
    return 0
  fi

  echo "========================================"
  echo "Starting AWS Glue annual job"
  echo "Job name: ${JOB_NAME}"
  echo "Period: ${year}"
  echo "Bucket: ${BUCKET}"
  echo "Output format: ${OUTPUT_FORMAT}"
  echo "Iceberg table: ${ATHENA_DATABASE}.${ICEBERG_TABLE}"
  echo "========================================"

  local job_run_id
  job_run_id="$(start_job_with_retry "${year}" "${year}" "ALL")"

  echo "[STARTED] ${year} -> ${job_run_id}"

  wait_for_job "${job_run_id}" "${year}"

  show_silver_output "s3://${BUCKET}/silver-parquet/yellow_taxi/year=${year}/"
}


if [[ $# -ge 2 && "$1" != --* ]]; then
  year="$1"
  month="$2"
  shift 2

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --force)
        FORCE=true
        shift
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

  month_padded=$(printf "%02d" "${month}")
  run_one_month "${year}-${month_padded}"
  exit 0
fi

while [[ $# -gt 0 ]]; do
  case "$1" in
    --year-months)
      shift
      while [[ $# -gt 0 && "$1" != --* ]]; do
        YEAR_MONTHS+=("$1")
        shift
      done
      ;;
    --months-file)
      MONTHS_FILE="$2"
      shift 2
      ;;
    --year)
      ANNUAL_YEAR="$2"
      shift 2
      ;;
    --force)
      FORCE=true
      shift
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

if [[ -n "${MONTHS_FILE}" ]]; then
  if [[ "${MONTHS_FILE}" != /* ]]; then
    MONTHS_FILE="${PROJECT_ROOT}/${MONTHS_FILE}"
  fi

  if [[ ! -f "${MONTHS_FILE}" ]]; then
    echo "ERROR: Months file not found: ${MONTHS_FILE}"
    exit 1
  fi

  while IFS= read -r line; do
    line="$(echo "$line" | xargs)"
    [[ -z "${line}" || "${line}" == \#* ]] && continue

    YEAR_MONTHS+=("${line}")
  done < "${MONTHS_FILE}"
fi

if [[ -n "${ANNUAL_YEAR}" ]]; then
  if [[ -n "${MONTHS_FILE}" || ${#YEAR_MONTHS[@]} -gt 0 ]]; then
    echo "ERROR: --year cannot be combined with --months-file or --year-months."
    exit 1
  fi

  run_one_year "${ANNUAL_YEAR}"
  exit 0
fi

if [[ ${#YEAR_MONTHS[@]} -eq 0 ]]; then
  echo "ERROR: No months provided."
  usage
  exit 1
fi

echo "========================================"
echo "Running Glue Silver jobs sequentially"

echo "Total months: ${#YEAR_MONTHS[@]}"
echo "Months: ${YEAR_MONTHS[*]}"
echo "========================================"

for year_month in "${YEAR_MONTHS[@]}"; do
  run_one_month "${year_month}"
done

echo "========================================"
echo "All Glue Silver jobs completed successfully"
echo "========================================"
