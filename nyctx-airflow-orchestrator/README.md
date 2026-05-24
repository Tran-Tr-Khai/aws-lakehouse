# nyctx-airflow-orchestrator

Apache Airflow DAGs for end-to-end pipeline orchestration.

## Structure

```
dags/       # Airflow DAG definitions
plugins/    # Custom Airflow operators/hooks
config/     # Airflow config and connections
```

> Work in progress — DAGs will orchestrate ingestion → Glue → dbt.
