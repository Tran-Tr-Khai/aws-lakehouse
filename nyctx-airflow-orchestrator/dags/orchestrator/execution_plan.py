from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from nyctx_ingestion.periods import normalize_periods

from orchestrator.runtime_params import (
    resolve_int_runtime_param,
    resolve_str_runtime_param,
)


@dataclass(frozen=True)
class ExecutionPlan:
    chunk_files: tuple[str, ...]
    full_months_file: str
    partition_count: int
    chunk_count: int
    execution_mode: str
    resolved_scope: str

    def to_payload(self) -> dict[str, object]:
        return {
            "chunk_files": list(self.chunk_files),
            "full_months_file": self.full_months_file,
            "partition_count": self.partition_count,
            "chunk_count": self.chunk_count,
            "execution_mode": self.execution_mode,
            "resolved_scope": self.resolved_scope,
        }


def resolve_partition_scope(partition_scope: str, all_partition_scope: str) -> str:
    return all_partition_scope if partition_scope.lower() == "all" else partition_scope


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


def build_execution_plan(context: dict[str, Any], runtime_plan_root: Path) -> ExecutionPlan:
    partition_scope = resolve_str_runtime_param(context, "partition_scope")
    all_partition_scope = resolve_str_runtime_param(context, "all_partition_scope")
    execution_mode = resolve_str_runtime_param(context, "execution_mode")
    chunk_size = resolve_int_runtime_param(context, "chunk_size")

    if not partition_scope:
        raise ValueError("partition_scope must not be empty.")
    if not all_partition_scope:
        raise ValueError("all_partition_scope must not be empty.")

    scope_value = resolve_partition_scope(partition_scope, all_partition_scope)
    periods = normalize_periods([scope_value])
    chunks = chunk_periods(periods, execution_mode, chunk_size)

    run_id = re.sub(r"[^A-Za-z0-9_.-]+", "_", context["run_id"])
    output_dir = runtime_plan_root / run_id
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

    return ExecutionPlan(
        chunk_files=tuple(chunk_files),
        full_months_file=str(full_months_file),
        partition_count=len(periods),
        chunk_count=len(chunk_files),
        execution_mode=execution_mode,
        resolved_scope=scope_value,
    )
