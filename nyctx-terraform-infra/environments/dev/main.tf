locals {
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
    Owner       = var.owner
  }
}

# Phase 1 intentionally defines no AWS resources.
# Phase 2 will add S3 and Athena modules after the target resource names are confirmed.
