#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
ATHENA_SRC="${PROJECT_ROOT}/nyctx-athena-catalog/src"
CACHE_ROOT="${XDG_CACHE_HOME:-/home/airflow/.cache}"
UV_CACHE_ROOT="${UV_CACHE_DIR:-${CACHE_ROOT}/uv}"

cd "${PROJECT_ROOT}"
mkdir -p "${CACHE_ROOT}" "${UV_CACHE_ROOT}"

if command -v nyctx-athena-run >/dev/null 2>&1; then
  exec nyctx-athena-run "$@"
fi

if command -v uv >/dev/null 2>&1; then
  exec env XDG_CACHE_HOME="${CACHE_ROOT}" UV_CACHE_DIR="${UV_CACHE_ROOT}" \
    uv run --package nyctx-athena-catalog nyctx-athena-run "$@"
fi

exec env PYTHONPATH="${ATHENA_SRC}${PYTHONPATH:+:${PYTHONPATH}}" \
  python -c 'from nyctx_athena_catalog.cli import run_sql_main; run_sql_main()' "$@"