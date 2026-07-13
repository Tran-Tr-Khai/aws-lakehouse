"""Shared paths used by ingestion commands."""

import os
from pathlib import Path


def discover_project_root() -> Path:
    """Find the monorepo root in source checkouts and installed runtimes."""
    configured_root = os.getenv("NYCTX_PROJECT_ROOT")
    if configured_root:
        return Path(configured_root).expanduser().resolve()

    source_component = Path(__file__).resolve().parents[2]
    if source_component.name == "nyctx-ingestion":
        return source_component.parent

    return Path.cwd().resolve()


PROJECT_ROOT = discover_project_root()
COMPONENT_ROOT = PROJECT_ROOT / "nyctx-ingestion"
LANDING_DIR = PROJECT_ROOT / "data" / "landing"
QUALITY_DIR = PROJECT_ROOT / "data" / "quality" / "local_profile"


def resolve_project_path(path: Path) -> Path:
    """Resolve a CLI path relative to the monorepo root."""
    return path if path.is_absolute() else PROJECT_ROOT / path
