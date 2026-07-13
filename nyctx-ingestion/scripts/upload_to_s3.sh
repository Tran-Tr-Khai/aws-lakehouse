#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
BUCKET_NAME="${NYCTX_S3_BUCKET:-}"
LANDING_DIR="${PROJECT_ROOT}/data/landing"
MONTHS_FILE=""
YEAR_MONTHS=()
WITH_ZONE_LOOKUP=false
WITH_ZONE_CENTROIDS=false
FORCE=false

usage() {
  cat <<'EOF'
Usage:
  upload_to_s3.sh --year-months 2024-01 2020-04 [reference flags] [--force]
  upload_to_s3.sh --months-file config/recovery_sample_months.txt [reference flags] [--force]
  upload_to_s3.sh --with-zone-lookup --with-zone-centroids [--force]

Required environment:
  NYCTX_S3_BUCKET  Destination bucket name
EOF
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
      [[ $# -ge 2 ]] || { echo "ERROR: --months-file requires a value" >&2; exit 2; }
      MONTHS_FILE="$2"
      shift 2
      ;;
    --with-zone-lookup) WITH_ZONE_LOOKUP=true; shift ;;
    --with-zone-centroids) WITH_ZONE_CENTROIDS=true; shift ;;
    --force) FORCE=true; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "ERROR: Unknown argument: $1" >&2; usage; exit 2 ;;
  esac
done

if [[ -n "${MONTHS_FILE}" ]]; then
  [[ ${#YEAR_MONTHS[@]} -eq 0 ]] || {
    echo "ERROR: Use either --year-months or --months-file, not both." >&2
    exit 2
  }
  [[ "${MONTHS_FILE}" == /* ]] || MONTHS_FILE="${PROJECT_ROOT}/${MONTHS_FILE}"
  [[ -f "${MONTHS_FILE}" ]] || { echo "ERROR: Months file not found: ${MONTHS_FILE}" >&2; exit 2; }
  while IFS= read -r line || [[ -n "${line}" ]]; do
    line="${line#"${line%%[![:space:]]*}"}"
    line="${line%"${line##*[![:space:]]}"}"
    [[ -z "${line}" || "${line}" == \#* ]] || YEAR_MONTHS+=("${line}")
  done < "${MONTHS_FILE}"
fi

if [[ ${#YEAR_MONTHS[@]} -eq 0 && "${WITH_ZONE_LOOKUP}" == false && "${WITH_ZONE_CENTROIDS}" == false ]]; then
  echo "ERROR: No month or reference input was provided." >&2
  usage
  exit 2
fi
[[ -n "${BUCKET_NAME}" ]] || {
  echo "ERROR: NYCTX_S3_BUCKET must be set explicitly." >&2
  exit 2
}

declare -A SEEN_PERIODS=()
TRIP_FILES=()
TRIP_KEYS=()
TRIP_PERIODS=()
for period in "${YEAR_MONTHS[@]}"; do
  [[ "${period}" =~ ^[0-9]{4}-[0-9]{2}$ ]] || {
    echo "ERROR: Invalid year-month format: ${period}. Expected YYYY-MM." >&2
    exit 2
  }
  year="${period:0:4}"
  month="${period:5:2}"
  (( 10#${year} >= 2000 && 10#${year} <= 2100 )) || {
    echo "ERROR: Invalid year: ${year}" >&2
    exit 2
  }
  (( 10#${month} >= 1 && 10#${month} <= 12 )) || {
    echo "ERROR: Invalid month: ${month}" >&2
    exit 2
  }
  [[ -z "${SEEN_PERIODS[${period}]:-}" ]] || continue
  SEEN_PERIODS["${period}"]=1
  filename="yellow_tripdata_${period}.parquet"
  local_file="${LANDING_DIR}/yellow_taxi/year=${year}/month=${month}/${filename}"
  [[ -f "${local_file}" ]] || { echo "ERROR: Trip file not found: ${local_file}" >&2; exit 2; }
  TRIP_FILES+=("${local_file}")
  TRIP_KEYS+=("bronze/yellow_taxi/year=${year}/month=${month}/${filename}")
  TRIP_PERIODS+=("${period}")
done

LOOKUP_FILE="${LANDING_DIR}/lookup/taxi_zone_lookup.csv"
CENTROIDS_FILE="${LANDING_DIR}/lookup/taxi_zone_centroids.csv"
[[ "${WITH_ZONE_LOOKUP}" == false || -f "${LOOKUP_FILE}" ]] || {
  echo "ERROR: Lookup file not found: ${LOOKUP_FILE}" >&2; exit 2;
}
[[ "${WITH_ZONE_CENTROIDS}" == false || -f "${CENTROIDS_FILE}" ]] || {
  echo "ERROR: Centroid file not found: ${CENTROIDS_FILE}" >&2; exit 2;
}

upload_object() {
  local local_file="$1"
  local object_key="$2"
  local label="$3"
  local local_size checksum remote remote_size remote_checksum

  local_size="$(stat -c '%s' "${local_file}")"
  checksum="$(sha256sum "${local_file}" | awk '{print $1}')"
  remote="$(aws s3api head-object \
    --bucket "${BUCKET_NAME}" \
    --key "${object_key}" \
    --query '[ContentLength, Metadata.sha256]' \
    --output text 2>/dev/null || true)"
  read -r remote_size remote_checksum <<< "${remote}"

  if [[ "${FORCE}" == false && "${remote_size:-}" == "${local_size}" && "${remote_checksum:-}" == "${checksum}" ]]; then
    echo "[SKIP] ${label}: verified size and SHA-256"
    return
  fi

  echo "[UPLOAD] ${label} -> s3://${BUCKET_NAME}/${object_key}"
  aws s3 cp "${local_file}" "s3://${BUCKET_NAME}/${object_key}" \
    --only-show-errors \
    --metadata "sha256=${checksum},source-size=${local_size}"
}

echo "Uploading validated landing data to bucket: ${BUCKET_NAME}"
if [[ "${WITH_ZONE_LOOKUP}" == true ]]; then
  upload_object "${LOOKUP_FILE}" "reference/taxi_zone_lookup/taxi_zone_lookup.csv" "zone lookup"
fi
if [[ "${WITH_ZONE_CENTROIDS}" == true ]]; then
  upload_object "${CENTROIDS_FILE}" "reference/taxi_zone_centroids/taxi_zone_centroids.csv" "zone centroids"
fi
for index in "${!TRIP_FILES[@]}"; do
  upload_object "${TRIP_FILES[${index}]}" "${TRIP_KEYS[${index}]}" "${TRIP_PERIODS[${index}]}"
done

echo "Upload completed successfully"
