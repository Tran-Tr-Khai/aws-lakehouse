variable "pipeline_workgroup_name" {
  description = "Athena workgroup name for pipeline validation and manual SQL checks."
  type        = string
}

variable "dbt_workgroup_name" {
  description = "Athena workgroup name for dbt CTAS/table builds."
  type        = string
}

variable "pipeline_output_location" {
  description = "S3 output location for pipeline Athena query results."
  type        = string
}

variable "dbt_output_location" {
  description = "S3 output location for dbt Athena query results."
  type        = string
}

variable "force_destroy" {
  description = "Whether Terraform can delete workgroups that contain saved queries."
  type        = bool
  default     = false
}
