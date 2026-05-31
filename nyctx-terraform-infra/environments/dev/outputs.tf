output "environment_context" {
  description = "Current Terraform environment context. Phase 1 only; no AWS resources are created yet."
  value = {
    project_name                = var.project_name
    environment                 = var.environment
    aws_region                  = var.aws_region
    s3_bucket_name              = var.s3_bucket_name
    athena_workgroup_name       = var.athena_workgroup_name
    dbt_athena_workgroup_name   = var.dbt_athena_workgroup_name
    glue_database_name          = var.glue_database_name
    creates_aws_resources_today = false
  }
}
