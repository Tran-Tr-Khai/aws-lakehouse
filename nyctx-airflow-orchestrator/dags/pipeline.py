from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG
from airflow.models.param import Param
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator


PROJECT_ROOT = "/opt/airflow/project"
MONTHS_FILE = "config/recovery_sample_months.txt"


def project_bash(command: str) -> str:
    return f"""
    set -euo pipefail
    cd {PROJECT_ROOT}

    {command}
    """


with DAG(
    dag_id="pipeline",
    description="NYC Taxi Bronze ingestion, Silver Glue transform, Athena checks, and optional dbt Gold build",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["nyc-taxi", "bronze", "silver", "gold", "aws"],
    params={
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

    download_raw_sample = BashOperator(
        task_id="download_raw_sample",
        bash_command=project_bash(
            f"""
            python nyctx-ingestion/scripts/download.py \
              --months-file {MONTHS_FILE} \
              --with-zone-lookup
            """
        ),
    )

    profile_bronze_local = BashOperator(
        task_id="profile_bronze_local",
        bash_command=project_bash(
            f"""
            python nyctx-ingestion/scripts/raw_quality_check.py \
              --months-file {MONTHS_FILE}
            """
        ),
    )

    upload_bronze_to_s3 = BashOperator(
        task_id="upload_bronze_to_s3",
        bash_command=project_bash(
            f"""
            bash nyctx-ingestion/scripts/upload_to_s3.sh \
              --months-file {MONTHS_FILE} \
              --with-zone-lookup
            """
        ),
    )

    transform_silver = BashOperator(
        task_id="transform_silver",
        retries=2,
        retry_delay=timedelta(minutes=2),
        bash_command=project_bash(
            f"""
            bash nyctx-glue-processor/scripts/run_glue_job.sh \
              --months-file {MONTHS_FILE}
            """
        ),
    )

    setup_athena_catalog = BashOperator(
        task_id="setup_athena_catalog",
        retries=1,
        retry_delay=timedelta(minutes=1),
        bash_command=project_bash(
            """
            bash nyctx-athena-catalog/scripts/run_athena_sql.sh \
              --file nyctx-athena-catalog/ddl/create_database.sql \
              --label create_database

            bash nyctx-athena-catalog/scripts/run_athena_sql.sh \
              --file nyctx-athena-catalog/ddl/create_silver_yellow_taxi.sql \
              --label create_silver_yellow_taxi
            """
        ),
    )

    validate_silver_athena = BashOperator(
        task_id="validate_silver_athena",
        retries=1,
        retry_delay=timedelta(minutes=1),
        bash_command=project_bash(
            f"""
            bash nyctx-athena-catalog/scripts/validate_silver_partitions.sh \
              --months-file {MONTHS_FILE}
            """
        ),
    )

    build_gold_marts = BashOperator(
        task_id="build_gold_marts",
        retries=1,
        retry_delay=timedelta(minutes=1),
        bash_command=project_bash(
            f"""
            if [[ "{{{{ params.run_gold | lower }}}}" != "true" ]]; then
              echo "[INFO] step=dbt_gold status=skipped reason=run_gold_param_false"
              exit 0
            fi

            DBT_ARGS="--months-file {MONTHS_FILE}"

            if [[ "{{{{ params.force_gold | lower }}}}" == "true" ]]; then
              DBT_ARGS="${{DBT_ARGS}} --force"
            fi

            if [[ "{{{{ params.run_dbt_tests | lower }}}}" != "true" ]]; then
              DBT_ARGS="${{DBT_ARGS}} --skip-tests"
            fi

            bash nyctx-dbt-transformer/scripts/run_dbt_gold.sh ${{DBT_ARGS}}
            """
        ),
    )

    end = EmptyOperator(task_id="end")

    (
        start
        >> download_raw_sample
        >> profile_bronze_local
        >> upload_bronze_to_s3
        >> transform_silver
        >> setup_athena_catalog
        >> validate_silver_athena
        >> build_gold_marts
        >> end
    )
