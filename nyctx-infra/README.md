# nyctx-infra

Terraform infrastructure for the NYC Taxi Lakehouse on AWS.

## Structure

```
terraform/
├── modules/              # Reusable Terraform modules (S3, Glue, Athena, IAM)
└── environments/
    └── dev/              # Dev environment config
```

> Work in progress — will provision S3 buckets, Glue jobs, Athena workgroups, IAM roles.
