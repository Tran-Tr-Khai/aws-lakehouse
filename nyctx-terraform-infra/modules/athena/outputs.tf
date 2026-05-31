output "pipeline_workgroup_name" {
  description = "Athena workgroup name for pipeline validation and manual SQL checks."
  value       = aws_athena_workgroup.pipeline.name
}

output "dbt_workgroup_name" {
  description = "Athena workgroup name for dbt CTAS/table builds."
  value       = aws_athena_workgroup.dbt.name
}

output "pipeline_output_location" {
  description = "S3 output location for pipeline Athena query results."
  value       = var.pipeline_output_location
}

output "dbt_output_location" {
  description = "S3 output location for dbt Athena query results."
  value       = var.dbt_output_location
}
