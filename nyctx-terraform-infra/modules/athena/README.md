# Athena Module

Planned for Phase 2.

This module will manage Athena workgroups for:

- pipeline validation queries
- dbt CTAS/table builds

The dbt workgroup must not enforce a fixed output location because dbt Athena
needs to write table data to configured Gold S3 locations.
