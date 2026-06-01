#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

BUCKET_NAME="${NYCTX_S3_BUCKET:-nyc-taxi-lakehouse-tntk-dev}"
LANDING_DIR="${PROJECT_ROOT}/data/landing"

MONTHS_FILE=""
YEAR_MONTHS=()
WITH_ZONE_LOOKUP=false
WITH_ZONE_CENTROIDS=false
FORCE=false

usage() {
  echo "Usage:"
  echo "  $0 --year-months 2024-01 2020-04 [--with-zone-lookup] [--with-zone-centroids] [--force]"
  echo "  $0 --months-file config/recovery_sample_months.txt [--with-zone-lookup] [--with-zone-centroids] [--force]"
  echo "  $0 --with-zone-lookup --with-zone-centroids [--force]"
}

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
    --with-zone-lookup)
      WITH_ZONE_LOOKUP=true
      shift
      ;;
    --with-zone-centroids)
      WITH_ZONE_CENTROIDS=true
      shift
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
    [[ -z "$line" || "$line" == \#* ]] && continue
    YEAR_MONTHS+=("$line")
  done < "${MONTHS_FILE}"
fi

HAS_REFERENCE_UPLOAD=false
if [[ "${WITH_ZONE_LOOKUP}" == true || "${WITH_ZONE_CENTROIDS}" == true ]]; then
  HAS_REFERENCE_UPLOAD=true
fi

if [[ ${#YEAR_MONTHS[@]} -eq 0 && "${HAS_REFERENCE_UPLOAD}" == false ]]; then
  echo "ERROR: No months provided."
  usage
  exit 1
fi

echo "========================================"
echo "Uploading NYC Taxi landing data to S3"
echo "Bucket: ${BUCKET_NAME}"
if [[ ${#YEAR_MONTHS[@]} -eq 0 ]]; then
  echo "Months: reference-only upload"
else
  echo "Months: ${YEAR_MONTHS[*]}"
fi
echo "========================================"

if [[ "${WITH_ZONE_LOOKUP}" == true ]]; then
  LOCAL_LOOKUP_FILE="${LANDING_DIR}/lookup/taxi_zone_lookup.csv"
  S3_LOOKUP_PATH="s3://${BUCKET_NAME}/reference/taxi_zone_lookup/taxi_zone_lookup.csv"

  if [[ ! -f "${LOCAL_LOOKUP_FILE}" ]]; then
    echo "ERROR: Lookup file not found: ${LOCAL_LOOKUP_FILE}"
    exit 1
  fi

  echo ""
  echo "[UPLOAD] Zone lookup"
  if [[ "${FORCE}" == false ]] && aws s3 ls "${S3_LOOKUP_PATH}" >/dev/null 2>&1; then
    echo "[SKIP] S3 object already exists: ${S3_LOOKUP_PATH}"
  else
    aws s3 cp "${LOCAL_LOOKUP_FILE}" "${S3_LOOKUP_PATH}"
  fi
fi

if [[ "${WITH_ZONE_CENTROIDS}" == true ]]; then
  LOCAL_CENTROIDS_FILE="${LANDING_DIR}/lookup/taxi_zone_centroids.csv"
  S3_CENTROIDS_PATH="s3://${BUCKET_NAME}/reference/taxi_zone_centroids/taxi_zone_centroids.csv"

  if [[ ! -f "${LOCAL_CENTROIDS_FILE}" ]]; then
    echo "ERROR: Taxi zone centroid file not found: ${LOCAL_CENTROIDS_FILE}"
    echo "ERROR: Run download.py with --with-zone-centroids before uploading."
    exit 1
  fi

  echo ""
  echo "[UPLOAD] Zone centroids"
  if [[ "${FORCE}" == false ]] && aws s3 ls "${S3_CENTROIDS_PATH}" >/dev/null 2>&1; then
    echo "[SKIP] S3 object already exists: ${S3_CENTROIDS_PATH}"
  else
    aws s3 cp "${LOCAL_CENTROIDS_FILE}" "${S3_CENTROIDS_PATH}"
  fi
fi

for YEAR_MONTH in "${YEAR_MONTHS[@]}"; do
  if [[ ! "${YEAR_MONTH}" =~ ^[0-9]{4}-[0-9]{2}$ ]]; then
    echo "ERROR: Invalid year-month format: ${YEAR_MONTH}. Expected YYYY-MM."
    exit 1
  fi

  YEAR="${YEAR_MONTH:0:4}"
  MONTH="${YEAR_MONTH:5:2}"

  if (( 10#${MONTH} < 1 || 10#${MONTH} > 12 )); then
    echo "ERROR: Invalid month: ${MONTH}"
    exit 1
  fi

  FILE_NAME="yellow_tripdata_${YEAR}-${MONTH}.parquet"
  LOCAL_TRIP_FILE="${LANDING_DIR}/yellow_taxi/year=${YEAR}/month=${MONTH}/${FILE_NAME}"
  S3_TRIP_PATH="s3://${BUCKET_NAME}/bronze/yellow_taxi/year=${YEAR}/month=${MONTH}/${FILE_NAME}"

  if [[ ! -f "${LOCAL_TRIP_FILE}" ]]; then
    echo "ERROR: Trip file not found: ${LOCAL_TRIP_FILE}"
    exit 1
  fi

  echo ""
  echo "[UPLOAD] ${YEAR_MONTH}"
  echo "Local: ${LOCAL_TRIP_FILE}"
  echo "S3:    ${S3_TRIP_PATH}"

  if [[ "${FORCE}" == false ]] && aws s3 ls "${S3_TRIP_PATH}" >/dev/null 2>&1; then
    echo "[SKIP] S3 object already exists: ${S3_TRIP_PATH}"
    continue
  fi

  aws s3 cp "${LOCAL_TRIP_FILE}" "${S3_TRIP_PATH}"
done

echo ""
echo "========================================"
echo "Upload completed successfully"
echo "========================================"
