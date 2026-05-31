output "database_name" {
  description = "Glue Catalog database name."
  value       = aws_glue_catalog_database.lakehouse.name
}

output "database_arn" {
  description = "Glue Catalog database ARN."
  value       = aws_glue_catalog_database.lakehouse.arn
}

output "silver_job_name" {
  description = "Silver Glue job name."
  value       = aws_glue_job.silver_yellow_taxi.name
}

output "silver_job_arn" {
  description = "Silver Glue job ARN."
  value       = aws_glue_job.silver_yellow_taxi.arn
}
