variable "aws_region" {
  description = "AWS region used by the lakehouse infrastructure."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name used for tagging and resource naming context."
  type        = string
  default     = "nyc-taxi-lakehouse"
}

variable "environment" {
  description = "Deployment environment name, for example dev or prod."
  type        = string
  default     = "dev"
}

variable "owner" {
  description = "Owner tag applied to Terraform-managed resources."
  type        = string
  default     = "khai"
}

variable "s3_bucket_name" {
  description = "Target S3 bucket name for the dev lakehouse environment. Used in Phase 2."
  type        = string
  default     = "nyc-taxi-lakehouse-tntk-dev"
}

variable "athena_workgroup_name" {
  description = "Primary Athena workgroup name for the dev environment. Used in Phase 2."
  type        = string
  default     = "wg_nyc_taxi_lakehouse_dev"
}

variable "dbt_athena_workgroup_name" {
  description = "dbt Athena workgroup name for the dev environment. Used in Phase 2."
  type        = string
  default     = "wg_nyc_taxi_dbt_dev"
}

variable "glue_database_name" {
  description = "Glue Catalog database name for the dev lakehouse environment. Used in Phase 4."
  type        = string
  default     = "nyc_taxi_lakehouse_dev"
}
