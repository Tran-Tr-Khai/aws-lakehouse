#!/usr/bin/env bash

set -euo pipefail

export PYTHONPATH=/opt/airflow/project/nyctx-ingestion/src
exec python -m nyctx_ingestion.upload $@
