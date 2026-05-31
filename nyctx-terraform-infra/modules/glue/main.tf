resource "aws_glue_catalog_database" "lakehouse" {
  name        = var.database_name
  description = var.database_description
}
