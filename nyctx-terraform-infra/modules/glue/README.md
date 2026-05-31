# Glue Module

Planned for Phase 3 and Phase 4.

This module will manage:

- Glue database
- Glue job definition for the Silver PySpark transform
- optional Glue Catalog tables after schema ownership is finalized

Glue job source code remains in `nyctx-glue-processor/jobs/` and is uploaded to
S3 by the deployment flow.
