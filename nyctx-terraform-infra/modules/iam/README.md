# IAM Module

Planned for Phase 3.

This module will manage the Glue service role and policies required to:

- read Bronze data from S3
- write Silver data to S3
- read/write Glue Catalog metadata
- write logs to CloudWatch

Policies should stay scoped to the project bucket and required Glue resources.
