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

variable "s3_force_destroy" {
  description = "Whether Terraform can delete the dev S3 bucket even when it contains objects."
  type        = bool
  default     = false
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

variable "athena_force_destroy" {
  description = "Whether Terraform can delete Athena workgroups that contain saved queries."
  type        = bool
  default     = false
}

variable "glue_database_name" {
  description = "Glue Catalog database name for the dev lakehouse environment. Used in Phase 4."
  type        = string
  default     = "nyc_taxi_lakehouse_dev"
}

variable "glue_role_name" {
  description = "IAM role name assumed by dev AWS Glue jobs."
  type        = string
  default     = "glue-nyc-taxi-lakehouse-dev-role"
}

variable "glue_silver_job_name" {
  description = "AWS Glue job name for the dev Bronze to Silver Yellow Taxi transform."
  type        = string
  default     = "glue-silver-yellow-taxi-dev"
}

variable "glue_silver_job_default_year" {
  description = "Default --YEAR argument for the dev Silver Glue job."
  type        = string
  default     = "2024"
}

variable "glue_silver_job_default_month" {
  description = "Default --MONTH argument for the dev Silver Glue job."
  type        = string
  default     = "1"
}

variable "glue_silver_job_glue_version" {
  description = "Glue runtime version for the dev Silver Glue job."
  type        = string
  default     = "4.0"
}

variable "glue_silver_job_worker_type" {
  description = "Glue worker type for the dev Silver Glue job."
  type        = string
  default     = "G.1X"
}

variable "glue_silver_job_number_of_workers" {
  description = "Number of Glue workers for the dev Silver Glue job."
  type        = number
  default     = 2
}

variable "glue_silver_job_timeout_minutes" {
  description = "Glue job timeout in minutes for the dev Silver Glue job."
  type        = number
  default     = 15
}

variable "glue_silver_job_max_concurrent_runs" {
  description = "Maximum concurrent runs for the dev Silver Glue job."
  type        = number
  default     = 1
}
