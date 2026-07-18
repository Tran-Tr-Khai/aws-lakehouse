from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

DEFAULT_CONFIG_PATH = Path.cwd() / 'nyctx-athena-catalog' / 'config.yaml'


@dataclass(frozen=True)
class AthenaConfig:
    aws_region: str
    s3_bucket: str
    workgroup: str
    output_location: str
    database: str
    table_name: str
    table_location: str
    zone_lookup_location: str
    zone_centroids_location: str
    poll_seconds: int
    query_timeout_seconds: int

    @classmethod
    def from_yaml(cls, path: Path | None = None) -> 'AthenaConfig':
        config_path = path or DEFAULT_CONFIG_PATH
        data = yaml.safe_load(config_path.read_text(encoding='utf-8'))
        return cls(**data)
