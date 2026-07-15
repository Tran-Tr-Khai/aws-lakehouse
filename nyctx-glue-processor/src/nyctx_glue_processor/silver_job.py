"""Production-oriented core for the Yellow Taxi Silver Glue job."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any, Protocol

try:
    from pyspark.sql import functions as F
except ModuleNotFoundError:  # pragma: no cover - local config tests can run without pyspark
    F = None

if TYPE_CHECKING:
    from pyspark.sql import DataFrame, SparkSession
else:  # pragma: no cover - keeps imports cheap for non-Spark tests
    DataFrame = Any
    SparkSession = Any


class Logger(Protocol):
    """Minimal logger interface used by the job runtime."""

    def info(self, message: str, *args: object) -> None:
        """Emit an informational log message."""


@dataclass(frozen=True)
class SilverJobConfig:
    """Runtime configuration for one Silver batch."""

    bucket: str
    year: int
    month: int
    write_mode: str = "overwrite"

    @property
    def month_str(self) -> str:
        return f"{self.month:02d}"

    @property
    def bronze_path(self) -> str:
        return (
            f"s3://{self.bucket}/bronze/yellow_taxi/"
            f"year={self.year}/month={self.month_str}/"
        )

    @property
    def silver_path(self) -> str:
        return (
            f"s3://{self.bucket}/silver/yellow_taxi/"
            f"year={self.year}/month={self.month_str}/"
        )

    @property
    def start_date(self) -> datetime:
        return datetime(self.year, self.month, 1)

    @property
    def end_date(self) -> datetime:
        if self.month == 12:
            return datetime(self.year + 1, 1, 1)
        return datetime(self.year, self.month + 1, 1)

    @property
    def start_date_str(self) -> str:
        return self.start_date.strftime("%Y-%m-%d")

    @property
    def end_date_str(self) -> str:
        return self.end_date.strftime("%Y-%m-%d")


def config_from_glue_args(raw_args: dict[str, str]) -> SilverJobConfig:
    """Translate Glue string arguments into a typed config."""
    return SilverJobConfig(
        bucket=raw_args["BUCKET"],
        year=int(raw_args["YEAR"]),
        month=int(raw_args["MONTH"]),
    )


def ensure_column(df: DataFrame, column_name: str, default_value: object) -> DataFrame:
    """Backfill missing columns so downstream Silver schema stays stable."""
    if F is None:  # pragma: no cover - protected by runtime environment
        raise RuntimeError("pyspark is required to run Spark transforms")
    if column_name in df.columns:
        return df
    return df.withColumn(column_name, F.lit(default_value))


def normalize_schema(df: DataFrame) -> DataFrame:
    """Normalize schema drift across NYC Yellow Taxi years."""
    if "Airport_fee" in df.columns and "airport_fee" not in df.columns:
        df = df.withColumnRenamed("Airport_fee", "airport_fee")

    df = ensure_column(df, "airport_fee", 0.0)
    df = ensure_column(df, "congestion_surcharge", 0.0)
    df = ensure_column(df, "extra", 0.0)
    df = ensure_column(df, "mta_tax", 0.0)
    df = ensure_column(df, "tip_amount", 0.0)
    df = ensure_column(df, "tolls_amount", 0.0)
    df = ensure_column(df, "improvement_surcharge", 0.0)
    df = ensure_column(df, "store_and_fwd_flag", None)
    return df


def apply_critical_quality_filters(df: DataFrame, config: SilverJobConfig) -> DataFrame:
    """Drop rows that are not suitable for analytical Silver output."""
    if F is None:  # pragma: no cover - protected by runtime environment
        raise RuntimeError("pyspark is required to run Spark transforms")
    return (
        df.filter(F.col("tpep_pickup_datetime").isNotNull())
        .filter(F.col("tpep_dropoff_datetime").isNotNull())
        .filter(F.col("tpep_dropoff_datetime") > F.col("tpep_pickup_datetime"))
        .filter(F.col("tpep_pickup_datetime") >= F.lit(config.start_date_str).cast("timestamp"))
        .filter(F.col("tpep_pickup_datetime") < F.lit(config.end_date_str).cast("timestamp"))
        .filter(F.col("trip_distance").isNotNull())
        .filter(F.col("trip_distance") > 0)
        .filter(F.col("passenger_count").isNotNull())
        .filter(F.col("passenger_count") > 0)
        .filter(F.col("fare_amount").isNotNull())
        .filter(F.col("fare_amount") >= 0)
        .filter(F.col("total_amount").isNotNull())
        .filter(F.col("total_amount") >= 0)
        .filter(F.col("PULocationID").isNotNull())
        .filter(F.col("DOLocationID").isNotNull())
        .filter(F.col("payment_type").isNotNull())
    )


def build_silver_dataframe(df: DataFrame, config: SilverJobConfig) -> DataFrame:
    """Apply Silver enrichments, quality flags, and output schema contract."""
    if F is None:  # pragma: no cover - protected by runtime environment
        raise RuntimeError("pyspark is required to run Spark transforms")
    clean_df = apply_critical_quality_filters(normalize_schema(df), config)

    return (
        clean_df.withColumn("extra", F.coalesce(F.col("extra"), F.lit(0.0)))
        .withColumn("mta_tax", F.coalesce(F.col("mta_tax"), F.lit(0.0)))
        .withColumn("tip_amount", F.coalesce(F.col("tip_amount"), F.lit(0.0)))
        .withColumn("tolls_amount", F.coalesce(F.col("tolls_amount"), F.lit(0.0)))
        .withColumn(
            "improvement_surcharge",
            F.coalesce(F.col("improvement_surcharge"), F.lit(0.0)),
        )
        .withColumn(
            "congestion_surcharge",
            F.coalesce(F.col("congestion_surcharge"), F.lit(0.0)),
        )
        .withColumn("airport_fee", F.coalesce(F.col("airport_fee"), F.lit(0.0)))
        .withColumn(
            "trip_duration_minutes",
            (F.unix_timestamp("tpep_dropoff_datetime") - F.unix_timestamp("tpep_pickup_datetime"))
            / 60.0,
        )
        .withColumn("pickup_date", F.to_date("tpep_pickup_datetime"))
        .withColumn("pickup_hour", F.hour("tpep_pickup_datetime"))
        .withColumn("pickup_day_of_week", F.date_format("tpep_pickup_datetime", "EEEE"))
        .withColumn(
            "fare_per_mile",
            F.when(F.col("trip_distance") > 0, F.col("fare_amount") / F.col("trip_distance"))
            .otherwise(F.lit(None)),
        )
        .withColumn(
            "tip_rate",
            F.when(F.col("fare_amount") > 0, F.col("tip_amount") / F.col("fare_amount"))
            .otherwise(F.lit(None)),
        )
        .withColumn(
            "avg_speed_mph",
            F.when(
                F.col("trip_duration_minutes") > 0,
                F.col("trip_distance") / (F.col("trip_duration_minutes") / 60.0),
            ).otherwise(F.lit(None)),
        )
        .withColumn(
            "fare_per_minute",
            F.when(
                F.col("trip_duration_minutes") > 0,
                F.col("fare_amount") / F.col("trip_duration_minutes"),
            ).otherwise(F.lit(None)),
        )
        .withColumn("is_invalid_vendor", F.col("VendorID").isNotNull() & ~F.col("VendorID").isin(1, 2))
        .withColumn(
            "is_invalid_payment_type_domain",
            F.col("payment_type").isNotNull() & ~F.col("payment_type").isin(1, 2, 3, 4, 5, 6),
        )
        .withColumn(
            "is_invalid_ratecode",
            F.col("RatecodeID").isNotNull() & ~F.col("RatecodeID").isin(1, 2, 3, 4, 5, 6, 99),
        )
        .withColumn(
            "is_invalid_store_and_fwd_flag",
            F.col("store_and_fwd_flag").isNotNull() & ~F.col("store_and_fwd_flag").isin("Y", "N"),
        )
        .withColumn(
            "has_negative_fee_component",
            (F.col("extra") < 0)
            | (F.col("mta_tax") < 0)
            | (F.col("tip_amount") < 0)
            | (F.col("tolls_amount") < 0)
            | (F.col("improvement_surcharge") < 0)
            | (F.col("congestion_surcharge") < 0)
            | (F.col("airport_fee") < 0),
        )
        .withColumn(
            "is_pickup_location_out_of_range",
            (F.col("PULocationID") < 1) | (F.col("PULocationID") > 265),
        )
        .withColumn(
            "is_dropoff_location_out_of_range",
            (F.col("DOLocationID") < 1) | (F.col("DOLocationID") > 265),
        )
        .withColumn("is_very_long_distance", F.col("trip_distance") > 100)
        .withColumn("is_very_long_duration", F.col("trip_duration_minutes") > 1440)
        .withColumn("same_pickup_dropoff_zone", F.col("PULocationID") == F.col("DOLocationID"))
        .withColumn("is_extreme_speed", F.col("avg_speed_mph") > 120)
        .withColumn(
            "is_fare_distance_mismatch",
            (F.col("trip_distance") < 0.1) & (F.col("fare_amount") > 100),
        )
        .withColumn(
            "is_distance_duration_mismatch",
            (F.col("trip_distance") > 100) & (F.col("trip_duration_minutes") < 90),
        )
        .withColumn(
            "is_same_zone_high_fare",
            (F.col("PULocationID") == F.col("DOLocationID"))
            & (F.col("trip_distance") < 0.1)
            & (F.col("fare_amount") > 100),
        )
        .withColumn(
            "has_warning_quality_issue",
            F.col("is_invalid_vendor")
            | F.col("is_invalid_payment_type_domain")
            | F.col("is_invalid_ratecode")
            | F.col("is_invalid_store_and_fwd_flag")
            | F.col("has_negative_fee_component")
            | F.col("is_pickup_location_out_of_range")
            | F.col("is_dropoff_location_out_of_range")
            | F.col("is_very_long_distance")
            | F.col("is_very_long_duration"),
        )
        .withColumn(
            "is_analytical_outlier",
            F.col("is_extreme_speed")
            | F.col("is_fare_distance_mismatch")
            | F.col("is_distance_duration_mismatch")
            | F.col("is_same_zone_high_fare"),
        )
        .withColumn("year", F.lit(config.year))
        .withColumn("month", F.lit(config.month))
        .select(
            F.col("VendorID").cast("int").alias("vendor_id"),
            F.col("tpep_pickup_datetime").alias("pickup_datetime"),
            F.col("tpep_dropoff_datetime").alias("dropoff_datetime"),
            F.col("passenger_count").cast("bigint").alias("passenger_count"),
            F.col("trip_distance").cast("double").alias("trip_distance"),
            F.col("RatecodeID").cast("bigint").alias("ratecode_id"),
            F.col("store_and_fwd_flag").cast("string").alias("store_and_fwd_flag"),
            F.col("PULocationID").cast("int").alias("pickup_location_id"),
            F.col("DOLocationID").cast("int").alias("dropoff_location_id"),
            F.col("payment_type").cast("bigint").alias("payment_type"),
            F.col("fare_amount").cast("double").alias("fare_amount"),
            F.col("extra").cast("double").alias("extra"),
            F.col("mta_tax").cast("double").alias("mta_tax"),
            F.col("tip_amount").cast("double").alias("tip_amount"),
            F.col("tolls_amount").cast("double").alias("tolls_amount"),
            F.col("improvement_surcharge").cast("double").alias("improvement_surcharge"),
            F.col("total_amount").cast("double").alias("total_amount"),
            F.col("congestion_surcharge").cast("double").alias("congestion_surcharge"),
            F.col("airport_fee").cast("double").alias("airport_fee"),
            F.col("trip_duration_minutes").cast("double").alias("trip_duration_minutes"),
            F.col("pickup_date"),
            F.col("pickup_hour").cast("int").alias("pickup_hour"),
            F.col("pickup_day_of_week").cast("string").alias("pickup_day_of_week"),
            F.col("fare_per_mile").cast("double").alias("fare_per_mile"),
            F.col("tip_rate").cast("double").alias("tip_rate"),
            F.col("avg_speed_mph").cast("double").alias("avg_speed_mph"),
            F.col("fare_per_minute").cast("double").alias("fare_per_minute"),
            F.col("same_pickup_dropoff_zone").cast("boolean").alias("same_pickup_dropoff_zone"),
            F.col("is_invalid_vendor").cast("boolean").alias("is_invalid_vendor"),
            F.col("is_invalid_payment_type_domain").cast("boolean").alias("is_invalid_payment_type_domain"),
            F.col("is_invalid_ratecode").cast("boolean").alias("is_invalid_ratecode"),
            F.col("is_invalid_store_and_fwd_flag").cast("boolean").alias("is_invalid_store_and_fwd_flag"),
            F.col("has_negative_fee_component").cast("boolean").alias("has_negative_fee_component"),
            F.col("is_pickup_location_out_of_range").cast("boolean").alias("is_pickup_location_out_of_range"),
            F.col("is_dropoff_location_out_of_range").cast("boolean").alias("is_dropoff_location_out_of_range"),
            F.col("is_very_long_distance").cast("boolean").alias("is_very_long_distance"),
            F.col("is_very_long_duration").cast("boolean").alias("is_very_long_duration"),
            F.col("has_warning_quality_issue").cast("boolean").alias("has_warning_quality_issue"),
            F.col("is_extreme_speed").cast("boolean").alias("is_extreme_speed"),
            F.col("is_fare_distance_mismatch").cast("boolean").alias("is_fare_distance_mismatch"),
            F.col("is_distance_duration_mismatch").cast("boolean").alias("is_distance_duration_mismatch"),
            F.col("is_same_zone_high_fare").cast("boolean").alias("is_same_zone_high_fare"),
            F.col("is_analytical_outlier").cast("boolean").alias("is_analytical_outlier"),
            F.col("year").cast("int").alias("year"),
            F.col("month").cast("int").alias("month"),
        )
    )


def write_silver_dataframe(df: DataFrame, config: SilverJobConfig) -> None:
    """Write one month of Silver data to S3."""
    df.write.mode(config.write_mode).parquet(config.silver_path)


def run_silver_job(spark: SparkSession, config: SilverJobConfig, logger: Logger) -> None:
    """Execute the Silver transformation end-to-end."""
    logger.info("Glue Silver Yellow Taxi Job Started")
    logger.info("Bronze input path: %s", config.bronze_path)
    logger.info("Silver output path: %s", config.silver_path)
    logger.info(
        "Batch pickup range: [%s, %s)",
        config.start_date_str,
        config.end_date_str,
    )

    bronze_df = spark.read.parquet(config.bronze_path)
    silver_df = build_silver_dataframe(bronze_df, config)

    bronze_count = bronze_df.count()
    silver_count = silver_df.count()
    logger.info("Bronze row count: %s", bronze_count)
    logger.info("Silver row count: %s", silver_count)
    logger.info("Dropped row count: %s", bronze_count - silver_count)

    write_silver_dataframe(silver_df, config)
    logger.info("Silver data written successfully.")
    logger.info("Glue Silver Yellow Taxi Job Completed")
