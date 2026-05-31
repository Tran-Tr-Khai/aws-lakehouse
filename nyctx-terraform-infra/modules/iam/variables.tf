variable "glue_role_name" {
  description = "IAM role name assumed by AWS Glue jobs."
  type        = string
}

variable "lakehouse_bucket_arn" {
  description = "ARN of the lakehouse S3 bucket."
  type        = string
}

variable "glue_database_arn" {
  description = "ARN of the Glue Catalog database managed for this environment."
  type        = string
}

variable "glue_database_name" {
  description = "Name of the Glue Catalog database managed for this environment."
  type        = string
}
