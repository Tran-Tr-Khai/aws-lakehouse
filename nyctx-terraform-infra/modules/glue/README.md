# Glue Module

This module manages Glue Catalog resources for the lakehouse environment.

Current resources:

- Glue database
- Glue job definition for the Silver PySpark transform

Planned later:

- optional Glue Catalog tables after schema ownership is finalized

Glue job source code remains in `nyctx-glue-processor/jobs/` and is uploaded to
S3 by the deployment flow.
