import logging
import sys

from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext

from nyctx_glue_processor.silver_job import config_from_glue_args, run_silver_job

OPTIONAL_GLUE_ARGS = (
    "OUTPUT_FORMAT",
    "ATHENA_DATABASE",
    "ICEBERG_TABLE",
)


def resolve_glue_args() -> dict[str, str]:
    args = getResolvedOptions(sys.argv, ["JOB_NAME", "BUCKET", "YEAR", "MONTH"])
    for name in OPTIONAL_GLUE_ARGS:
        if f"--{name}" in sys.argv:
            args.update(getResolvedOptions(sys.argv, [name]))
    return args


def main() -> None:
    args = resolve_glue_args()

    sc = SparkContext.getOrCreate()
    glue_context = GlueContext(sc)
    spark = glue_context.spark_session

    job = Job(glue_context)
    job.init(args["JOB_NAME"], args)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    logger = logging.getLogger("nyctx_glue_processor.glue_silver_yellow_taxi")

    run_silver_job(spark, config_from_glue_args(args), logger)
    job.commit()


if __name__ == "__main__":
    main()
