from pathlib import Path

from nyctx_athena_catalog.config import AthenaConfig


def test_from_yaml_loads_expected_values(tmp_path: Path) -> None:
    config_file = tmp_path / 'config.yaml'
    config_file.write_text(
        """aws_region: us-east-1
s3_bucket: bucket
workgroup: wg
output_location: s3://bucket/athena-results/
database: db
table_name: silver_yellow_taxi_iceberg
table_location: s3://bucket/silver/
zone_lookup_location: s3://bucket/reference/lookup/
zone_centroids_location: s3://bucket/reference/centroids/
poll_seconds: 5
query_timeout_seconds: 1800
""",
        encoding='utf-8',
    )

    config = AthenaConfig.from_yaml(config_file)

    assert config.s3_bucket == 'bucket'
    assert config.database == 'db'
    assert config.table_name == 'silver_yellow_taxi_iceberg'
    assert config.poll_seconds == 5
    assert config.query_timeout_seconds == 1800
