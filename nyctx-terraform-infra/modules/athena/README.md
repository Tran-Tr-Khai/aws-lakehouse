# Athena Module

This module manages Athena workgroups for:

- pipeline validation and manual SQL checks
- dbt CTAS/table builds

The pipeline workgroup enforces its configured output location so validation
queries consistently write under the lakehouse result prefix.

The dbt workgroup must not enforce a fixed output location because dbt Athena
needs to write table data to configured Gold S3 locations.
