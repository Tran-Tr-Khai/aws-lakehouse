from __future__ import annotations

import shlex
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Callable

from orchestrator.config import PipelineConfig


@dataclass(frozen=True)
class CommandStep:
    name: str
    command: str


@dataclass(frozen=True)
class CommandBuilder:
    config: PipelineConfig

    def run(self, command: str) -> None:
        process = subprocess.Popen(
            ["bash", "-lc", self.project_bash(command)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        assert process.stdout is not None
        for line in process.stdout:
            print(line, end="", flush=True)

        return_code = process.wait()
        if return_code != 0:
            raise subprocess.CalledProcessError(return_code, process.args)

    def run_step(self, step: CommandStep, *, step_group: str) -> None:
        print(f"[INFO] step_group={step_group} step={step.name} status=started")
        try:
            self.run(step.command)
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(
                f"step_group={step_group} step={step.name} failed with exit code {exc.returncode}"
            ) from exc
        print(f"[INFO] step_group={step_group} step={step.name} status=succeeded")

    def run_steps(self, steps: Sequence[CommandStep], *, step_group: str) -> None:
        for step in steps:
            self.run_step(step, step_group=step_group)

    def run_chunk_sequence(
        self,
        chunk_files: Sequence[str],
        steps_builder: Callable[[str], Sequence[CommandStep]],
        *,
        step_name: str,
    ) -> None:
        total_chunks = len(chunk_files)
        for index, months_file in enumerate(chunk_files, start=1):
            chunk_group = f"{step_name}[{index}/{total_chunks}]"
            print(
                f"[INFO] step={step_name} chunk_index={index}/{total_chunks} "
                f"months_file={months_file}"
            )
            self.run_steps(steps_builder(months_file), step_group=chunk_group)

    def project_bash(self, command: str) -> str:
        return f"""
        set -euo pipefail
        cd {self.config.project_root}
        export XDG_CACHE_HOME={self.config.xdg_cache_home}
        export UV_CACHE_DIR={self.config.uv_cache_dir}
        export UV_LINK_MODE={self.config.uv_link_mode}
        mkdir -p {self.config.xdg_cache_home} {self.config.uv_cache_dir}

        {command}
        """

    def with_upload_cache(self, command: str) -> str:
        return f"{self.config.upload_cache_env} {command}"

    def months_file_arg(self, months_file: str) -> str:
        return f"--months-file {shlex.quote(months_file)}"

    def athena_sql(self, sql_file: str, label: str, extra_args: str = "") -> str:
        extra_suffix = f" {extra_args.strip()}" if extra_args.strip() else ""
        return (
            f"bash {self.config.athena_sql_script} "
            f"--file {sql_file} "
            f"--label {label}{extra_suffix}"
        )

    def first_period_exports(self, months_file: str) -> CommandStep:
        quoted_months_file = shlex.quote(months_file)
        return CommandStep(
            name="resolve_first_period",
            command="\n".join(
                [
                    f'FIRST_PERIOD="$(head -n 1 {quoted_months_file})"',
                    'FIRST_YEAR="${FIRST_PERIOD%-*}"',
                    'FIRST_MONTH="${FIRST_PERIOD#*-}"',
                ]
            ),
        )

    def reference_download_steps(self) -> list[CommandStep]:
        return [
            CommandStep(
                name="download_reference_data",
                command="nyctx-download --with-zone-lookup --with-zone-centroids",
            )
        ]

    def reference_upload_steps(self) -> list[CommandStep]:
        return [
            CommandStep(
                name="upload_reference_to_s3",
                command=self.with_upload_cache(
                    "bash nyctx-ingestion/scripts/upload_to_s3.sh --with-zone-lookup --with-zone-centroids"
                ),
            )
        ]

    def ingestion_steps(self, months_file: str) -> list[CommandStep]:
        months_arg = self.months_file_arg(months_file)
        return [
            CommandStep(name="download_bronze", command=f"nyctx-download {months_arg}"),
            CommandStep(name="profile_bronze", command=f"nyctx-quality-check {months_arg}"),
            CommandStep(
                name="upload_bronze_to_s3",
                command=self.with_upload_cache(
                    f"bash nyctx-ingestion/scripts/upload_to_s3.sh {months_arg}"
                ),
            ),
        ]

    def athena_catalog_steps(self) -> list[CommandStep]:
        return [
            CommandStep(
                name=label,
                command=self.athena_sql(sql_file, label),
            )
            for sql_file, label in self.config.athena_catalog_steps
        ]

    def chunk_athena_steps(self, months_file: str) -> list[CommandStep]:
        months_arg = self.months_file_arg(months_file)
        return [
            CommandStep(
                name="athena_validate_silver_partitions",
                command=f"bash {self.config.athena_validate_script} {months_arg}",
            ),
            self.first_period_exports(months_file),
            CommandStep(
                name="athena_smoke_test",
                command=self.athena_sql(
                    "nyctx-athena-catalog/queries/00_smoke_test.sql",
                    "smoke_test",
                    '--year "${FIRST_YEAR}" --month "${FIRST_MONTH}"',
                ),
            ),
            CommandStep(
                name="athena_monthly_trip_summary",
                command=self.athena_sql(
                    "nyctx-athena-catalog/queries/01_monthly_trip_summary.sql",
                    "monthly_trip_summary",
                    months_arg,
                ),
            ),
            CommandStep(
                name="athena_payment_type_summary",
                command=self.athena_sql(
                    "nyctx-athena-catalog/queries/02_payment_type_summary.sql",
                    "payment_type_summary",
                    '--year "${FIRST_YEAR}" --month "${FIRST_MONTH}"',
                ),
            ),
            CommandStep(
                name="athena_iceberg_snapshot_history",
                command=self.athena_sql(
                    "nyctx-athena-catalog/queries/05_iceberg_snapshot_history.sql",
                    "iceberg_snapshot_history",
                ),
            ),
        ]

    def chunk_full_pipeline_steps(self, months_file: str) -> list[CommandStep]:
        return [
            *self.ingestion_steps(months_file),
            CommandStep(
                name="glue_run_silver",
                command=(
                    f"bash nyctx-glue-processor/scripts/run_glue_job.sh "
                    f"{self.months_file_arg(months_file)}"
                ),
            ),
            *self.chunk_athena_steps(months_file),
        ]

    def dbt_gold(self, full_months_file: str, *, force_gold: bool, run_dbt_tests: bool) -> str:
        command = (
            "bash nyctx-dbt-transformer/scripts/run_dbt_gold.sh "
            f"--selector dashboard_all --months-file {shlex.quote(full_months_file)}"
        )
        if force_gold:
            command += " --force"
        if not run_dbt_tests:
            command += " --skip-tests"
        return command
