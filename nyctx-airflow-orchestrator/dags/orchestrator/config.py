from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from airflow.models.param import Param


CONFIG_CANDIDATES = (
    Path("/opt/airflow/project/nyctx-airflow-orchestrator/config/pipeline.yaml"),
    Path.cwd() / "nyctx-airflow-orchestrator" / "config" / "pipeline.yaml",
    Path(__file__).resolve().parents[2] / "config" / "pipeline.yaml",
)


def resolve_config_path() -> Path:
    for candidate in CONFIG_CANDIDATES:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        "Could not find pipeline.yaml. Checked: "
        + ", ".join(str(candidate) for candidate in CONFIG_CANDIDATES)
    )


CONFIG_PATH = resolve_config_path()


@dataclass(frozen=True)
class DagParamDefinition:
    default: object
    type: str
    description: str
    minimum: int | None = None

    def to_airflow_param(self) -> Param:
        kwargs: dict[str, object] = {
            "type": self.type,
            "description": self.description,
        }
        if self.minimum is not None:
            kwargs["minimum"] = self.minimum
        return Param(self.default, **kwargs)


@dataclass(frozen=True)
class PipelineConfig:
    project_root: str
    runtime_plan_root: Path
    xdg_cache_home: str
    uv_cache_dir: str
    uv_link_mode: str
    athena_sql_script: str
    athena_validate_script: str
    glue_deploy_script: str
    athena_catalog_steps: tuple[tuple[str, str], ...]
    dag_id: str
    dag_description: str
    dag_start_date: datetime
    dag_schedule: str | None
    dag_catchup: bool
    dag_tags: tuple[str, ...]
    dag_params: dict[str, Param]

    @property
    def upload_cache_env(self) -> str:
        return (
            f"env XDG_CACHE_HOME={self.xdg_cache_home} "
            f"UV_CACHE_DIR={self.uv_cache_dir}"
        )


def _parse_start_date(value: object) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day)
    return datetime.fromisoformat(str(value))


def _build_param_definitions(raw_params: dict[str, dict[str, Any]]) -> dict[str, Param]:
    return {
        key: DagParamDefinition(
            default=value["default"],
            type=value["type"],
            description=value["description"],
            minimum=value.get("minimum"),
        ).to_airflow_param()
        for key, value in raw_params.items()
    }


@lru_cache(maxsize=1)
def load_pipeline_config(path: Path = CONFIG_PATH) -> PipelineConfig:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))

    dag_config = raw["dag"]
    scripts = raw["scripts"]
    cache = raw["cache"]

    return PipelineConfig(
        project_root=raw["project_root"],
        runtime_plan_root=Path(raw["runtime_plan_root"]),
        xdg_cache_home=cache["xdg_cache_home"],
        uv_cache_dir=cache["uv_cache_dir"],
        uv_link_mode=cache["uv_link_mode"],
        athena_sql_script=scripts["athena_sql"],
        athena_validate_script=scripts["athena_validate"],
        glue_deploy_script=scripts["glue_deploy"],
        athena_catalog_steps=tuple(
            (step["file"], step["label"]) for step in raw["athena_catalog_steps"]
        ),
        dag_id=dag_config["id"],
        dag_description=dag_config["description"],
        dag_start_date=_parse_start_date(dag_config["start_date"]),
        dag_schedule=dag_config["schedule"],
        dag_catchup=bool(dag_config["catchup"]),
        dag_tags=tuple(dag_config["tags"]),
        dag_params=_build_param_definitions(raw["params"]),
    )
