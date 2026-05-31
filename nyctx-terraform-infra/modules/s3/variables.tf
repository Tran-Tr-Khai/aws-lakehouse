variable "bucket_name" {
  description = "Globally unique S3 bucket name for the lakehouse environment."
  type        = string
}

variable "force_destroy" {
  description = "Whether Terraform can delete the bucket even when it contains objects. Keep false outside disposable environments."
  type        = bool
  default     = false
}
