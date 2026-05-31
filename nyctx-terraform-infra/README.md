# nyctx-terraform-infra

Terraform infrastructure for the NYC Taxi Lakehouse on AWS.

## Current Status

Terraform is starting in a conservative learning-first mode:

```text
Phase 0  Learn Terraform basics and state ownership
Phase 1  Create a safe dev scaffold with no AWS resources yet
Phase 2  Add S3 and Athena resources
Phase 3  Add IAM and Glue job resources
Phase 4  Add Glue Catalog resources where Terraform ownership makes sense
```

Phase 1 is implemented as a scaffold.
Phase 2 starts with a Terraform-managed dev S3 bucket baseline.

## Structure

```text
environments/
└── dev/              # Terraform entry point for the dev environment
modules/
├── athena/           # Planned reusable Athena module
├── glue/             # Planned reusable Glue module
├── iam/              # Planned reusable IAM module
└── s3/               # Planned reusable S3 module
```

## Dev Environment

Start here:

```bash
cd nyctx-terraform-infra/environments/dev
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform fmt
terraform validate
terraform plan
```

Expected Phase 1 result:

- Phase 1 plans should create no AWS resources;
- Phase 2 plans should show the dev S3 bucket resources before any apply;
- do not run `terraform apply` until the plan has been reviewed.

## Ownership Rule

Terraform manages infrastructure, not data.

Terraform should manage resources such as S3 buckets, Athena workgroups, Glue
jobs, IAM roles, and selected Glue Catalog metadata. It should not manage
monthly Parquet files, dbt output data, Power BI files, or Athena query result
objects.
