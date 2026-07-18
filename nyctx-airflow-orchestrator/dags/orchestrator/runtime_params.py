from __future__ import annotations

from typing import Any


def resolve_runtime_param(context: dict[str, Any], key: str) -> Any:
    dag_run = context.get("dag_run")
    params = context["params"]
    default_value = params[key]
    if dag_run is None or dag_run.conf is None:
        return default_value
    return dag_run.conf.get(key, default_value)


def resolve_bool_runtime_param(context: dict[str, Any], key: str) -> bool:
    return bool(resolve_runtime_param(context, key))


def resolve_int_runtime_param(context: dict[str, Any], key: str) -> int:
    return int(resolve_runtime_param(context, key))


def resolve_str_runtime_param(context: dict[str, Any], key: str) -> str:
    return str(resolve_runtime_param(context, key)).strip()
