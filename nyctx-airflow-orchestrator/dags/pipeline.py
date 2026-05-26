from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG
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
    description="NYC Taxi Bronze ingestion, quality check, and Silver Glue transform",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["nyc-taxi", "bronze", "silver", "aws"],
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

    end = EmptyOperator(task_id="end")

    (
        start
        >> download_raw_sample
        >> profile_bronze_local
        >> upload_bronze_to_s3
        >> transform_silver
        >> end
    )
