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
}

module "iam" {
  source = "../../modules/iam"

  glue_role_name       = var.glue_role_name
  lakehouse_bucket_arn = module.s3.bucket_arn
  glue_database_arn    = module.glue.database_arn
  glue_database_name   = module.glue.database_name
}
