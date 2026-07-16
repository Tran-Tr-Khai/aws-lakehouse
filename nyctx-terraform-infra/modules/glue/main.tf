resource "aws_glue_catalog_database" "lakehouse" {
  name        = var.database_name
  description = var.database_description
}

resource "aws_glue_job" "silver_yellow_taxi" {
  name         = var.silver_job_name
  role_arn     = var.silver_job_role_arn
  glue_version = var.silver_job_glue_version
  worker_type  = var.silver_job_worker_type

  number_of_workers = var.silver_job_number_of_workers
  timeout           = var.silver_job_timeout_minutes

  command {
    name            = "glueetl"
    script_location = var.silver_job_script_location
    python_version  = "3"
  }

  execution_property {
    max_concurrent_runs = var.silver_job_max_concurrent_runs
  }

  default_arguments = {
    "--job-language"            = "python"
    "--datalake-formats"        = "iceberg"
    "--enable-glue-datacatalog" = "true"
    "--conf"                    = "spark.sql.extensions=org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions --conf spark.sql.catalog.glue_catalog=org.apache.iceberg.spark.SparkCatalog --conf spark.sql.catalog.glue_catalog.warehouse=s3://${var.silver_job_bucket_name}/ --conf spark.sql.catalog.glue_catalog.catalog-impl=org.apache.iceberg.aws.glue.GlueCatalog --conf spark.sql.catalog.glue_catalog.io-impl=org.apache.iceberg.aws.s3.S3FileIO"
    "--BUCKET"                  = var.silver_job_bucket_name
    "--YEAR"                    = var.silver_job_default_year
    "--MONTH"                   = var.silver_job_default_month
    "--OUTPUT_FORMAT"           = "both"
    "--ATHENA_DATABASE"         = var.database_name
    "--ICEBERG_TABLE"           = "silver_yellow_taxi_iceberg"
  }
}
