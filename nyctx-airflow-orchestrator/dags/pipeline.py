from __future__ import annotations

from datetime import timedelta

from airflow import DAG
from airflow.decorators import task
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import BranchPythonOperator, get_current_context

from orchestrator.commands import CommandBuilder
from orchestrator.config import load_pipeline_config
from orchestrator.execution_plan import build_execution_plan
from orchestrator.runtime_params import resolve_bool_runtime_param


PIPELINE_CONFIG = load_pipeline_config()
COMMANDS = CommandBuilder(PIPELINE_CONFIG)


@task
def prepare_execution_plan() -> dict[str, object]:
    return build_execution_plan(
        get_current_context(),
        PIPELINE_CONFIG.runtime_plan_root,
    ).to_payload()


@task
def extract_chunk_files(plan: dict[str, object]) -> list[str]:
    return list(plan["chunk_files"])


@task
def extract_full_months_file(plan: dict[str, object]) -> str:
    return str(plan["full_months_file"])


@task
def download_reference_data() -> None:
    COMMANDS.run_steps(COMMANDS.reference_download_steps(), step_group="download_reference_data")


@task
def upload_reference_to_s3() -> None:
    COMMANDS.run_steps(COMMANDS.reference_upload_steps(), step_group="upload_reference_to_s3")


@task(max_active_tis_per_dag=1)
def run_chunk_ingestion_only(chunk_files: list[str]) -> None:
    COMMANDS.run_chunk_sequence(
        chunk_files,
        COMMANDS.ingestion_steps,
        step_name="run_chunk_ingestion_only",
    )


@task(max_active_tis_per_dag=1)
def deploy_glue_script() -> None:
    COMMANDS.run(PIPELINE_CONFIG.glue_deploy_script)


@task(max_active_tis_per_dag=1)
def setup_athena_catalog() -> None:
    COMMANDS.run_steps(COMMANDS.athena_catalog_steps(), step_group="setup_athena_catalog")


@task(max_active_tis_per_dag=1)
def run_chunk_full_pipeline(chunk_files: list[str]) -> None:
    COMMANDS.run_chunk_sequence(
        chunk_files,
        COMMANDS.chunk_full_pipeline_steps,
        step_name="run_chunk_full_pipeline",
    )


@task(retries=1, retry_delay=timedelta(minutes=1))
def build_gold_marts(full_months_file: str) -> None:
    context = get_current_context()
    run_gold = resolve_bool_runtime_param(context, "run_gold")
    force_gold = resolve_bool_runtime_param(context, "force_gold")
    run_dbt_tests = resolve_bool_runtime_param(context, "run_dbt_tests")

    if not run_gold:
        print("[INFO] step=dbt_gold status=skipped reason=run_gold_param_false")
        return

    COMMANDS.run(
        COMMANDS.dbt_gold(
            full_months_file,
            force_gold=force_gold,
            run_dbt_tests=run_dbt_tests,
        )
    )


def choose_post_reference_path(**context) -> str:
    run_ingestion_only = resolve_bool_runtime_param(context, "run_ingestion_only")
    return "run_chunk_ingestion_only" if run_ingestion_only else "deploy_glue_script"


with DAG(
    dag_id=PIPELINE_CONFIG.dag_id,
    description=PIPELINE_CONFIG.dag_description,
    start_date=PIPELINE_CONFIG.dag_start_date,
    schedule=PIPELINE_CONFIG.dag_schedule,
    catchup=PIPELINE_CONFIG.dag_catchup,
    tags=list(PIPELINE_CONFIG.dag_tags),
    params=PIPELINE_CONFIG.dag_params,
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

    run_chunk_ingestion_only_task = run_chunk_ingestion_only(chunk_files)
    deploy_glue_script_task = deploy_glue_script()
    setup_athena_catalog_task = setup_athena_catalog()
    run_chunk_full_pipeline_task = run_chunk_full_pipeline(chunk_files)
    build_gold_marts_task = build_gold_marts(full_months_file)

    end = EmptyOperator(task_id="end", trigger_rule="none_failed_min_one_success")

    start >> execution_plan >> download_reference_data_task >> upload_reference_to_s3_task
    upload_reference_to_s3_task >> choose_post_reference_path_task

    choose_post_reference_path_task >> run_chunk_ingestion_only_task >> end
    choose_post_reference_path_task >> deploy_glue_script_task
    deploy_glue_script_task >> setup_athena_catalog_task >> run_chunk_full_pipeline_task
    run_chunk_full_pipeline_task >> build_gold_marts_task >> end
