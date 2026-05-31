# S3 Module

This module manages the lakehouse S3 bucket baseline:

- S3 bucket
- public access block
- default server-side encryption with S3-managed keys

Dataset files are not managed by Terraform.

The lakehouse uses these prefix conventions:

- `bronze/`
- `silver/`
- `gold/`
- `reference/`
- `athena-results/`
- `scripts/`

Those prefixes are created by pipeline tools when data is written. Terraform
does not upload parquet files or query result objects.
