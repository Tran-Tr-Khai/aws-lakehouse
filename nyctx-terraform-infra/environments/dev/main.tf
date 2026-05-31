locals {
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
    Owner       = var.owner
  }
}

module "s3" {
  source = "../../modules/s3"

  bucket_name   = var.s3_bucket_name
  force_destroy = var.s3_force_destroy
}

module "athena" {
  source = "../../modules/athena"

  pipeline_workgroup_name  = var.athena_workgroup_name
  dbt_workgroup_name       = var.dbt_athena_workgroup_name
  pipeline_output_location = "${module.s3.s3_uri}/athena-results/"
  dbt_output_location      = "${module.s3.s3_uri}/athena-results/dbt/"
  force_destroy            = var.athena_force_destroy
}

module "glue" {
  source = "../../modules/glue"

  database_name = var.glue_database_name

  silver_job_name                = var.glue_silver_job_name
  silver_job_role_arn            = module.iam.glue_role_arn
  silver_job_script_location     = "${module.s3.s3_uri}/scripts/glue_silver_yellow_taxi.py"
  silver_job_bucket_name         = module.s3.bucket_name
  silver_job_default_year        = var.glue_silver_job_default_year
  silver_job_default_month       = var.glue_silver_job_default_month
  silver_job_glue_version        = var.glue_silver_job_glue_version
  silver_job_worker_type         = var.glue_silver_job_worker_type
  silver_job_number_of_workers   = var.glue_silver_job_number_of_workers
  silver_job_timeout_minutes     = var.glue_silver_job_timeout_minutes
  silver_job_max_concurrent_runs = var.glue_silver_job_max_concurrent_runs
}

module "iam" {
  source = "../../modules/iam"

  glue_role_name       = var.glue_role_name
  lakehouse_bucket_arn = module.s3.bucket_arn
  glue_database_arn    = "arn:aws:glue:${var.aws_region}:${data.aws_caller_identity.current.account_id}:database/${var.glue_database_name}"
  glue_database_name   = var.glue_database_name
}
