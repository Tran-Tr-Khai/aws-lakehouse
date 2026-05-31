output "database_name" {
  description = "Glue Catalog database name."
  value       = aws_glue_catalog_database.lakehouse.name
}

output "database_arn" {
  description = "Glue Catalog database ARN."
  value       = aws_glue_catalog_database.lakehouse.arn
}
