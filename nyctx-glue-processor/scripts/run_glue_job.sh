#!/usr/bin/env bash
set -euo pipefail

AWS_REGION="us-east-1"
BUCKET="nyc-taxi-lakehouse-tntk"
JOB_NAME="glue-silver-yellow-taxi"

MONTHS_FILE=""
YEAR_MONTHS=()

usage() {
  echo "Usage:"
  echo "  $0 2024 1"
  echo "  $0 --year-months 2024-01 2020-04"
  echo "  $0 --months-file config/recovery_sample_months.txt"
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

  echo "========================================"
  echo "Starting AWS Glue job"
  echo "Job name: ${JOB_NAME}"
  echo "Period: ${year_month}"
  echo "Bucket: ${BUCKET}"
  echo "========================================"

  local job_run_id
  job_run_id=$(
    aws glue start-job-run \
      --job-name "${JOB_NAME}" \
      --region "${AWS_REGION}" \
      --arguments "{
        \"--BUCKET\": \"${BUCKET}\",
        \"--YEAR\": \"${year}\",
        \"--MONTH\": \"${month_int}\"
      }" \
      --query "JobRunId" \
      --output text
  )

  echo "[STARTED] ${year_month} -> ${job_run_id}"

  wait_for_job "${job_run_id}" "${year_month}"

  echo "[SILVER OUTPUT]"
  aws s3 ls "s3://${BUCKET}/silver/yellow_taxi/year=${year}/month=${month}/" \
    --region "${AWS_REGION}"
}

if [[ $# -eq 2 && "$1" != --* ]]; then
  year="$1"
  month="$2"
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