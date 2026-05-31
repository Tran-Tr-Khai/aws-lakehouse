# IAM Module

This module manages the IAM role used by AWS Glue jobs.

Current resources:

- Glue execution role trusted by `glue.amazonaws.com`
- Inline policy scoped to the lakehouse S3 bucket
- Glue Catalog permissions for the environment database
- CloudWatch Logs write permissions

The module intentionally does not create IAM users or access keys. Long-lived
access keys can leak through Terraform state and are not needed for this
lakehouse runtime role.

Policies should stay scoped to the project bucket and required Glue resources.
