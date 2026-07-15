from __future__ import annotations

from nyctx_glue_processor.silver_job import SilverJobConfig, config_from_glue_args


def test_config_builds_month_window_and_paths() -> None:
    config = SilverJobConfig(bucket="demo-bucket", year=2024, month=1)

    assert config.month_str == "01"
    assert config.start_date_str == "2024-01-01"
    assert config.end_date_str == "2024-02-01"
    assert config.bronze_path == "s3://demo-bucket/bronze/yellow_taxi/year=2024/month=01/"
    assert config.silver_path == "s3://demo-bucket/silver/yellow_taxi/year=2024/month=01/"


def test_config_handles_december_rollover() -> None:
    config = SilverJobConfig(bucket="demo-bucket", year=2024, month=12)

    assert config.end_date_str == "2025-01-01"


def test_config_from_glue_args_casts_types() -> None:
    config = config_from_glue_args({"BUCKET": "demo-bucket", "YEAR": "2024", "MONTH": "7"})

    assert config == SilverJobConfig(bucket="demo-bucket", year=2024, month=7)
