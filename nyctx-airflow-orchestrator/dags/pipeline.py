from __future__ import annotations

import re
import shlex
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.decorators import task
from airflow.models.param import Param
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import BranchPythonOperator, get_current_context

from nyctx_ingestion.periods import normalize_periods


PROJECT_ROOT = "/opt/airflow/project"
RUNTIME_PLAN_ROOT = Path("/opt/airflow/logs/partition_plans")
DEFAULT_ALL_PARTITION_SCOPE = "2019:2024"
UPLOAD_CACHE_ENV = "env XDG_CACHE_HOME=/home/airflow/.cache UV_CACHE_DIR=/home/airflow/.cache/uv"


def project_bash(command: str) -> str:
    return f"""
    set -euo pipefail
    cd {PROJECT_ROOT}
    export XDG_CACHE_HOME=/home/airflow/.cache
    export UV_CACHE_DIR=/home/airflow/.cache/uv
    export UV_LINK_MODE=copy
    mkdir -p /home/airflow/.cache /home/airflow/.cache/uv

    {command}
    """


def run_project_command(command: str) -> None:
    subprocess.run(["bash", "-lc", project_bash(command)], check=True)


def resolve_runtime_param(context: dict[str, object], key: str) -> object:
    dag_run = context.get("dag_run")
    params = context["params"]
    default_value = params[key]
    if dag_run is None or dag_run.conf is None:
        return default_value
    return dag_run.conf.get(key, default_value)


def choose_post_reference_path(**context) -> str:
    run_ingestion_only = bool(resolve_runtime_param(context, "run_ingestion_only"))
    return "run_chunk_ingestion_only" if run_ingestion_only else "deploy_glue_script"


def chunk_periods(
    periods: list[tuple[int, int]],
    execution_mode: str,
    chunk_size: int,
) -> list[list[tuple[int, int]]]:
    if not periods:
        raise ValueError("No partitions were resolved from partition_scope.")
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero.")
    if execution_mode == "all_at_once":
        return [periods]
    if execution_mode == "per_month":
        return [[period] for period in periods]
    if execution_mode == "chunked":
        return [periods[index : index + chunk_size] for index in range(0, len(periods), chunk_size)]
    raise ValueError(
        "execution_mode must be one of: all_at_once, per_month, chunked. "
        f"Got: {execution_mode}"
    )


def periods_to_text(periods: list[tuple[int, int]]) -> str:
    return "\n".join(f"{year:04d}-{month:02d}" for year, month in periods) + "\n"


@task
def prepare_execution_plan() -> dict[str, object]:
    context = get_current_context()
    partition_scope = str(resolve_runtime_param(context, "partition_scope")).strip()
    all_partition_scope = str(resolve_runtime_param(context, "all_partition_scope")).strip()
    execution_mode = str(resolve_runtime_param(context, "execution_mode")).strip()
    chunk_size = int(resolve_runtime_param(context, "chunk_size"))

    if not partition_scope:
        raise ValueError("partition_scope must not be empty.")
    if not all_partition_scope:
        raise ValueError("all_partition_scope must not be empty.")

    scope_value = all_partition_scope if partition_scope.lower() == "all" else partition_scope
    periods = normalize_periods([scope_value])
    chunks = chunk_periods(periods, execution_mode, chunk_size)

    run_id = re.sub(r"[^A-Za-z0-9_.-]+", "_", context["run_id"])
    output_dir = RUNTIME_PLAN_ROOT / run_id
    output_dir.mkdir(parents=True, exist_ok=True)

    full_months_file = output_dir / "all_months.txt"
    full_months_file.write_text(periods_to_text(periods), encoding="utf-8")

    chunk_files: list[str] = []
    for index, chunk in enumerate(chunks, start=1):
        chunk_file = output_dir / f"chunk_{index:03d}.txt"
        chunk_file.write_text(periods_to_text(chunk), encoding="utf-8")
        chunk_files.append(str(chunk_file))

    print(
        "[INFO] execution_plan "
        f"partition_scope={partition_scope} resolved_scope={scope_value} "
        f"execution_mode={execution_mode} chunk_size={chunk_size} "
        f"partition_count={len(periods)} chunk_count={len(chunk_files)}"
    )

    return {
        "chunk_files": chunk_files,
        "full_months_file": str(full_months_file),
        "partition_count": len(periods),
        "chunk_count": len(chunk_files),
        "execution_mode": execution_mode,
        "resolved_scope": scope_value,
    }


@task
def extract_chunk_files(plan: dict[str, object]) -> list[str]:
    return list(plan["chunk_files"])


@task
def extract_full_months_file(plan: dict[str, object]) -> str:
    return str(plan["full_months_file"])


@task
def download_reference_data() -> None:
    run_project_command(
        """
        nyctx-download \
          --with-zone-lookup \
          --with-zone-centroids
        """
    )


@task
def upload_reference_to_s3() -> None:
    run_project_command(
        f"""
        {UPLOAD_CACHE_ENV} \
          bash nyctx-ingestion/scripts/upload_to_s3.sh \
          --with-zone-lookup \
          --with-zone-centroids
        """
    )


@task(max_active_tis_per_dag=1)
def run_chunk_ingestion_only(months_file: str) -> None:
    quoted_months_file = shlex.quote(months_file)
    run_project_command(
        f"""
        nyctx-download \
          --months-file {quoted_months_file}

        nyctx-quality-check \
          --months-file {quoted_months_file}

        {UPLOAD_CACHE_ENV} \
          bash nyctx-ingestion/scripts/upload_to_s3.sh \
          --months-file {quoted_months_file}
        """
    )


@task(max_active_tis_per_dag=1)
def deploy_glue_script() -> None:
    run_project_command("bash nyctx-glue-processor/scripts/deploy_glue_job_terraform.sh")


@task(max_active_tis_per_dag=1)
def setup_athena_catalog() -> None:
    run_project_command(
        """
        bash nyctx-athena-catalog/scripts/run_athena_sql.sh \
          --file nyctx-athena-catalog/ddl/create_database.sql \
          --label create_database

        bash nyctx-athena-catalog/scripts/run_athena_sql.sh \
          --file nyctx-athena-catalog/ddl/create_reference_taxi_zone_lookup.sql \
          --label create_reference_taxi_zone_lookup

        bash nyctx-athena-catalog/scripts/run_athena_sql.sh \
          --file nyctx-athena-catalog/ddl/create_reference_taxi_zone_centroids.sql \
          --label create_reference_taxi_zone_centroids

        bash nyctx-athena-catalog/scripts/run_athena_sql.sh \
          --file nyctx-athena-catalog/ddl/create_silver_yellow_taxi.sql \
          --label create_silver_yellow_taxi

        bash nyctx-athena-catalog/scripts/run_athena_sql.sh \
          --file nyctx-athena-catalog/ddl/create_silver_yellow_taxi_iceberg.sql \
          --label create_silver_yellow_taxi_iceberg
        """
    )


@task(max_active_tis_per_dag=1, retries=2, retry_delay=timedelta(minutes=2))
def run_chunk_full_pipeline(months_file: str) -> None:
    quoted_months_file = shlex.quote(months_file)
    run_project_command(
        f"""
        nyctx-download --months-file {quoted_months_file}

        nyctx-quality-check --months-file {quoted_months_file}

        {UPLOAD_CACHE_ENV} bash nyctx-ingestion/scripts/upload_to_s3.sh --months-file {quoted_months_file}

        bash nyctx-glue-processor/scripts/run_glue_job.sh --months-file {quoted_months_file}

        bash nyctx-athena-catalog/scripts/validate_silver_partitions.sh --months-file {quoted_months_file}

        FIRST_PERIOD="$(head -n 1 {quoted_months_file})"
        FIRST_YEAR="${{FIRST_PERIOD%-*}}"
        FIRST_MONTH="${{FIRST_PERIOD#*-}}"

        bash nyctx-athena-catalog/scripts/run_athena_sql.sh --file nyctx-athena-catalog/queries/00_smoke_test.sql --label smoke_test --year "${{FIRST_YEAR}}" --month "${{FIRST_MONTH}}"

        bash nyctx-athena-catalog/scripts/run_athena_sql.sh --file nyctx-athena-catalog/queries/01_monthly_trip_summary.sql --label monthly_trip_summary --months-file {quoted_months_file}

        bash nyctx-athena-catalog/scripts/run_athena_sql.sh --file nyctx-athena-catalog/queries/02_payment_type_summary.sql --label payment_type_summary --year "${{FIRST_YEAR}}" --month "${{FIRST_MONTH}}"

        bash nyctx-athena-catalog/scripts/run_athena_sql.sh --file nyctx-athena-catalog/queries/06_compare_parquet_iceberg_counts.sql --label compare_parquet_iceberg_counts --months-file {quoted_months_file}

        bash nyctx-athena-catalog/scripts/run_athena_sql.sh --file nyctx-athena-catalog/queries/05_iceberg_snapshot_history.sql --label iceberg_snapshot_history
        """
    )


@task(retries=1, retry_delay=timedelta(minutes=1))
def build_gold_marts(full_months_file: str) -> None:
    context = get_current_context()
    run_gold = bool(resolve_runtime_param(context, "run_gold"))
    force_gold = bool(resolve_runtime_param(context, "force_gold"))
    run_dbt_tests = bool(resolve_runtime_param(context, "run_dbt_tests"))

    if not run_gold:
        print("[INFO] step=dbt_gold status=skipped reason=run_gold_param_false")
        return

    command = (
        "bash nyctx-dbt-transformer/scripts/run_dbt_gold.sh "
        f"--selector dashboard_all --months-file {shlex.quote(full_months_file)}"
    )
    if force_gold:
        command += " --force"
    if not run_dbt_tests:
        command += " --skip-tests"

    run_project_command(command)


with DAG(
    dag_id="pipeline",
    description="NYC Taxi Bronze ingestion, Silver Glue transform, Athena checks, and optional dbt Gold build",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["nyc-taxi", "bronze", "silver", "gold", "aws"],
    params={
        "partition_scope": Param(
            "all",
            type="string",
            description="Partitions to run. Use all, YYYY, YYYY-MM, or START:END.",
        ),
        "all_partition_scope": Param(
            DEFAULT_ALL_PARTITION_SCOPE,
            type="string",
            description="Concrete range used when partition_scope=all.",
        ),
        "execution_mode": Param(
            "per_month",
            type="string",
            description="Execution strategy: all_at_once, per_month, or chunked.",
        ),
        "chunk_size": Param(
            3,
            type="integer",
            minimum=1,
            description="Months per chunk when execution_mode=chunked.",
        ),
        "run_ingestion_only": Param(
            False,
            type="boolean",
            description="Stop after Bronze ingestion and skip Silver/Gold downstream tasks.",
        ),
        "run_gold": Param(
            True,
            type="boolean",
            description="Check/build dbt Gold models. Existing complete Gold outputs are skipped without Athena scans.",
        ),
        "force_gold": Param(
            False,
            type="boolean",
            description="Force rebuild dbt Gold models even when existing Gold outputs look complete.",
        ),
        "run_dbt_tests": Param(
            True,
            type="boolean",
            description="Run dbt tests after dbt Gold models are built.",
        ),
    },
) as dag:
    start = EmptyOperator(task_id="start")

    execution_plan = prepare_execution_plan()
    chunk_files = extract_chunk_files(execution_plan)
    full_months_file = extract_full_months_file(execution_plan)

    download_reference_data_task = download_reference_data()
    upload_reference_to_s3_task = upload_reference_to_s3()

    choose_post_reference_path_task = BranchPythonOperator(
        task_id="choose_post_reference_path",
        python_callable=choose_post_reference_path,
    )

    run_chunk_ingestion_only_task = run_chunk_ingestion_only.expand(months_file=chunk_files)
    deploy_glue_script_task = deploy_glue_script()
    setup_athena_catalog_task = setup_athena_catalog()
    run_chunk_full_pipeline_task = run_chunk_full_pipeline.expand(months_file=chunk_files)
    build_gold_marts_task = build_gold_marts(full_months_file)

    end = EmptyOperator(task_id="end", trigger_rule="none_failed_min_one_success")

    start >> execution_plan >> download_reference_data_task >> upload_reference_to_s3_task
    upload_reference_to_s3_task >> choose_post_reference_path_task

    choose_post_reference_path_task >> run_chunk_ingestion_only_task >> end
    choose_post_reference_path_task >> deploy_glue_script_task
    deploy_glue_script_task >> setup_athena_catalog_task >> run_chunk_full_pipeline_task
    run_chunk_full_pipeline_task >> build_gold_marts_task >> end
