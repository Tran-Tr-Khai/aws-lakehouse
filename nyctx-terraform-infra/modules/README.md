# Terraform Modules

Reusable modules for the NYC Taxi Lakehouse infrastructure live here.

Planned modules:

```text
s3/       S3 lakehouse bucket, result prefixes, lifecycle rules
athena/   Athena workgroups and output configuration
iam/      Glue IAM role and least-privilege policies
glue/     Glue database, catalog objects, and Glue job definition
```

The module directories are placeholders in Phase 1. Resource implementation
starts in Phase 2 after names and ownership strategy are confirmed.
