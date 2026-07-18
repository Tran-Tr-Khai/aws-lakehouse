from __future__ import annotations

from nyctx_glue_processor.silver_job import SilverJobConfig, config_from_glue_args


def test_config_builds_month_window_and_paths() -> None:
    config = SilverJobConfig(bucket="demo-bucket", year=2024, month=1)

    assert config.month_str == "01"
    assert config.start_date_str == "2024-01-01"
    assert config.end_date_str == "2024-02-01"
    assert config.bronze_path == "s3://demo-bucket/bronze/yellow_taxi/year=2024/month=01/"
    assert config.silver_path == "s3://demo-bucket/silver-parquet/yellow_taxi/year=2024/month=01/"


def test_config_handles_december_rollover() -> None:
    config = SilverJobConfig(bucket="demo-bucket", year=2024, month=12)

    assert config.end_date_str == "2025-01-01"


def test_config_from_glue_args_casts_types() -> None:
    config = config_from_glue_args({"BUCKET": "demo-bucket", "YEAR": "2024", "MONTH": "7"})

    assert config == SilverJobConfig(bucket="demo-bucket", year=2024, month=7)


def test_config_builds_annual_window_and_paths() -> None:
    config = SilverJobConfig(bucket="demo-bucket", year=2024, month=None)

    assert config.is_annual is True
    assert config.month_str == "ALL"
    assert config.batch_label == "2024"
    assert config.start_date_str == "2024-01-01"
    assert config.end_date_str == "2025-01-01"
    assert config.bronze_path == "s3://demo-bucket/bronze/yellow_taxi/year=2024/"
    assert config.silver_path == "s3://demo-bucket/silver-parquet/yellow_taxi/"


def test_config_from_glue_args_supports_annual_mode() -> None:
    config = config_from_glue_args({"BUCKET": "demo-bucket", "YEAR": "2024", "MONTH": "ALL"})

    assert config == SilverJobConfig(bucket="demo-bucket", year=2024, month=None)


def test_config_from_glue_args_supports_iceberg_output() -> None:
    config = config_from_glue_args(
        {
            "BUCKET": "demo-bucket",
            "YEAR": "2024",
            "MONTH": "1",
            "OUTPUT_FORMAT": "both",
            "ATHENA_DATABASE": "analytics_db",
            "ICEBERG_TABLE": "silver_taxi_iceberg",
        }
    )

    assert config.output_format == "both"
    assert config.writes_parquet is True
    assert config.writes_iceberg is True
    assert config.silver_iceberg_location == "s3://demo-bucket/silver/yellow_taxi/"
    assert config.iceberg_table_identifier == "glue_catalog.analytics_db.silver_taxi_iceberg"