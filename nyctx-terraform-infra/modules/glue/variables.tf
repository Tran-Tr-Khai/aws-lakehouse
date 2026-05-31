variable "database_name" {
  description = "Glue Catalog database name for the lakehouse environment."
  type        = string
}

variable "database_description" {
  description = "Glue Catalog database description."
  type        = string
  default     = "NYC Taxi Lakehouse metadata database managed by Terraform."
}

variable "silver_job_name" {
  description = "AWS Glue job name for the Bronze to Silver Yellow Taxi transform."
  type        = string
}

variable "silver_job_role_arn" {
  description = "IAM role ARN used by the Silver Glue job."
  type        = string
}

variable "silver_job_script_location" {
  description = "S3 script location for the Silver Glue job."
  type        = string
}

variable "silver_job_bucket_name" {
  description = "Lakehouse bucket name passed to the Silver Glue job as --BUCKET."
  type        = string
}

variable "silver_job_default_year" {
  description = "Default --YEAR argument for the Silver Glue job."
  type        = string
  default     = "2024"
}

variable "silver_job_default_month" {
  description = "Default --MONTH argument for the Silver Glue job."
  type        = string
  default     = "1"
}

variable "silver_job_glue_version" {
  description = "Glue runtime version for the Silver Glue job."
  type        = string
  default     = "4.0"
}

variable "silver_job_worker_type" {
  description = "Glue worker type for the Silver Glue job."
  type        = string
  default     = "G.1X"
}

variable "silver_job_number_of_workers" {
  description = "Number of Glue workers for the Silver Glue job."
  type        = number
  default     = 2
}

variable "silver_job_timeout_minutes" {
  description = "Glue job timeout in minutes."
  type        = number
  default     = 15
}

variable "silver_job_max_concurrent_runs" {
  description = "Maximum concurrent runs for the Silver Glue job."
  type        = number
  default     = 1
}
