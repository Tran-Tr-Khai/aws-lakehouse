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
    "--job-language" = "python"
    "--BUCKET"       = var.silver_job_bucket_name
    "--YEAR"         = var.silver_job_default_year
    "--MONTH"        = var.silver_job_default_month
  }
}
