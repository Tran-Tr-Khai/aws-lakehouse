output "environment_context" {
  description = "Current Terraform environment context."
  value = {
    project_name                = var.project_name
    environment                 = var.environment
    aws_region                  = var.aws_region
    s3_bucket_name              = var.s3_bucket_name
    athena_workgroup_name       = var.athena_workgroup_name
    dbt_athena_workgroup_name   = var.dbt_athena_workgroup_name
    glue_database_name          = var.glue_database_name
    creates_aws_resources_today = true
  }
}

output "lakehouse_bucket" {
  description = "Terraform-managed lakehouse S3 bucket details."
  value = {
    name   = module.s3.bucket_name
    arn    = module.s3.bucket_arn
    s3_uri = module.s3.s3_uri
  }
}

output "athena_workgroups" {
  description = "Terraform-managed Athena workgroups."
  value = {
    pipeline_name            = module.athena.pipeline_workgroup_name
    pipeline_output_location = module.athena.pipeline_output_location
    dbt_name                 = module.athena.dbt_workgroup_name
    dbt_output_location      = module.athena.dbt_output_location
  }
}
