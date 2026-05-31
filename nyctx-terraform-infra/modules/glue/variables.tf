variable "database_name" {
  description = "Glue Catalog database name for the lakehouse environment."
  type        = string
}

variable "database_description" {
  description = "Glue Catalog database description."
  type        = string
  default     = "NYC Taxi Lakehouse metadata database managed by Terraform."
}
