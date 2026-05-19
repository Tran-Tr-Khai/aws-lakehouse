#!/usr/bin/env bash

set -euo pipefail

# ==============================
# Project config
# ==============================

BUCKET_NAME="nyc-taxi-lakehouse-tntk"
YEAR="2024"
MONTH="01"

# ==============================
# Local files
# ==============================

LOCAL_TRIP_FILE="data/landing/yellow_taxi/year=${YEAR}/month=${MONTH}/yellow_tripdata_${YEAR}-${MONTH}.parquet"
LOCAL_LOOKUP_FILE="data/landing/lookup/taxi_zone_lookup.csv"

# ==============================
# S3 target paths
# ==============================

S3_TRIP_PATH="s3://${BUCKET_NAME}/bronze/yellow_taxi/year=${YEAR}/month=${MONTH}/yellow_tripdata_${YEAR}-${MONTH}.parquet"
S3_LOOKUP_PATH="s3://${BUCKET_NAME}/reference/taxi_zone_lookup.csv"

echo "========================================"
echo "Uploading NYC Taxi data to AWS S3"
echo "Bucket: ${BUCKET_NAME}"
echo "Year: ${YEAR}"
echo "Month: ${MONTH}"
echo "========================================"

if [ ! -f "${LOCAL_TRIP_FILE}" ]; then
  echo "ERROR: Trip file not found: ${LOCAL_TRIP_FILE}"
  exit 1
fi

if [ ! -f "${LOCAL_LOOKUP_FILE}" ]; then
  echo "ERROR: Lookup file not found: ${LOCAL_LOOKUP_FILE}"
  exit 1
fi

echo ""
echo "Uploading trip file..."
aws s3 cp "${LOCAL_TRIP_FILE}" "${S3_TRIP_PATH}"

echo ""
echo "Uploading zone lookup file..."
aws s3 cp "${LOCAL_LOOKUP_FILE}" "${S3_LOOKUP_PATH}"

echo ""
echo "========================================"
echo "Upload completed successfully"
echo "Trip file uploaded to:"
echo "${S3_TRIP_PATH}"
echo ""
echo "Lookup file uploaded to:"
echo "${S3_LOOKUP_PATH}"
echo "========================================"