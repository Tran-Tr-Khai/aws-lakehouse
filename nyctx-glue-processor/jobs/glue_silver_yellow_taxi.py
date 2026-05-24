import sys
from datetime import datetime

from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from pyspark.sql import functions as F


args = getResolvedOptions(
    sys.argv,
    ["JOB_NAME", "BUCKET", "YEAR", "MONTH"],
)

bucket = args["BUCKET"]
year = int(args["YEAR"])
month = int(args["MONTH"])
month_str = f"{month:02d}"

start_date = datetime(year, month, 1)

if month == 12:
    end_date = datetime(year + 1, 1, 1)
else:
    end_date = datetime(year, month + 1, 1)

start_date_str = start_date.strftime("%Y-%m-%d")
end_date_str = end_date.strftime("%Y-%m-%d")

bronze_path = (
    f"s3://{bucket}/bronze/yellow_taxi/"
    f"year={year}/month={month_str}/"
)

silver_path = (
    f"s3://{bucket}/silver/yellow_taxi/"
    f"year={year}/month={month_str}/"
)


sc = SparkContext()
glue_context = GlueContext(sc)
spark = glue_context.spark_session

job = Job(glue_context)
job.init(args["JOB_NAME"], args)


print("=== Glue Silver Yellow Taxi Job Started ===")
print(f"Bronze input path: {bronze_path}")
print(f"Silver output path: {silver_path}")
print(f"Batch year: {year}")
print(f"Batch month: {month_str}")
print(f"Batch pickup range: [{start_date_str}, {end_date_str})")


bronze_df = spark.read.parquet(bronze_path)
bronze_df.cache()

bronze_count = bronze_df.count()
print(f"Bronze row count: {bronze_count}")


clean_df = (
    bronze_df
    .filter(F.col("tpep_pickup_datetime").isNotNull())
    .filter(F.col("tpep_dropoff_datetime").isNotNull())
    .filter(F.col("tpep_dropoff_datetime") > F.col("tpep_pickup_datetime"))
    .filter(F.col("tpep_pickup_datetime") >= F.lit(start_date_str).cast("timestamp"))
    .filter(F.col("tpep_pickup_datetime") < F.lit(end_date_str).cast("timestamp"))
    .filter(F.col("trip_distance") > 0)
    .filter(F.col("passenger_count") > 0)
    .filter(F.col("fare_amount") >= 0)
    .filter(F.col("total_amount") >= 0)
    .filter(F.col("PULocationID").isNotNull())
    .filter(F.col("DOLocationID").isNotNull())
    .filter(F.col("payment_type").isin(1, 2, 3, 4))
)

silver_df = (
    clean_df
    .withColumn(
        "trip_duration_minutes",
        (
            F.unix_timestamp("tpep_dropoff_datetime")
            - F.unix_timestamp("tpep_pickup_datetime")
        ) / 60.0,
    )
    .withColumn("pickup_date", F.to_date("tpep_pickup_datetime"))
    .withColumn("pickup_hour", F.hour("tpep_pickup_datetime"))
    .withColumn("pickup_day_of_week", F.date_format("tpep_pickup_datetime", "EEEE"))
    .withColumn(
        "fare_per_mile",
        F.when(
            F.col("trip_distance") > 0,
            F.col("fare_amount") / F.col("trip_distance"),
        ).otherwise(F.lit(None)),
    )
    .withColumn(
        "tip_rate",
        F.when(
            F.col("fare_amount") > 0,
            F.col("tip_amount") / F.col("fare_amount"),
        ).otherwise(F.lit(None)),
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
    .withColumn(
        "same_pickup_dropoff_zone",
        F.col("PULocationID") == F.col("DOLocationID"),
    )
    .withColumn(
        "is_extreme_speed",
        F.col("avg_speed_mph") > 120,
    )
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
        "is_analytical_outlier",
        F.col("is_extreme_speed")
        | F.col("is_fare_distance_mismatch")
        | F.col("is_distance_duration_mismatch")
        | F.col("is_same_zone_high_fare"),
    )
    .withColumn("year", F.lit(year))
    .withColumn("month", F.lit(month))
    .select(
        F.col("VendorID").alias("vendor_id"),
        F.col("tpep_pickup_datetime").alias("pickup_datetime"),
        F.col("tpep_dropoff_datetime").alias("dropoff_datetime"),
        F.col("passenger_count"),
        F.col("trip_distance"),
        F.col("RatecodeID").alias("ratecode_id"),
        F.col("store_and_fwd_flag"),
        F.col("PULocationID").alias("pickup_location_id"),
        F.col("DOLocationID").alias("dropoff_location_id"),
        F.col("payment_type"),
        F.col("fare_amount"),
        F.col("extra"),
        F.col("mta_tax"),
        F.col("tip_amount"),
        F.col("tolls_amount"),
        F.col("improvement_surcharge"),
        F.col("total_amount"),
        F.col("congestion_surcharge"),
        F.col("Airport_fee").alias("airport_fee"),
        F.col("trip_duration_minutes"),
        F.col("pickup_date"),
        F.col("pickup_hour"),
        F.col("pickup_day_of_week"),
        F.col("fare_per_mile"),
        F.col("tip_rate"),
        F.col("avg_speed_mph"),
        F.col("fare_per_minute"),
        F.col("same_pickup_dropoff_zone"),
        F.col("is_extreme_speed"),
        F.col("is_fare_distance_mismatch"),
        F.col("is_distance_duration_mismatch"),
        F.col("is_same_zone_high_fare"),
        F.col("is_analytical_outlier"),
        F.col("year"),
        F.col("month"),
    )
)

silver_count = silver_df.count()
print(f"Silver row count: {silver_count}")
print(f"Dropped row count: {bronze_count - silver_count}")


(
    silver_df
    .coalesce(1)
    .write
    .mode("overwrite")
    .parquet(silver_path)
)

print("Silver data written successfully.")
print(f"Output path: {silver_path}")

bronze_df.unpersist()
job.commit()
print("=== Glue Silver Yellow Taxi Job Completed ===")