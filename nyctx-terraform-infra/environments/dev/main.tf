locals {
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
    Owner       = var.owner
  }
}

module "s3" {
  source = "../../modules/s3"

  bucket_name   = var.s3_bucket_name
  force_destroy = var.s3_force_destroy
}
