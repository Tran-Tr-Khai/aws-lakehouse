# nyctx-airflow-orchestrator

Airflow orchestration for the NYC Taxi pipeline.

## Structure
```text
dags/
config/
logs/
```

## Setup
```bash
cd nyctx-airflow-orchestrator
cp .env.example .env
sed -i "s/^AIRFLOW_UID=.*/AIRFLOW_UID=$(id -u)/" .env
```

Pipeline defaults:
```text
config/pipeline.yaml
```

## Start
```bash
cd nyctx-airflow-orchestrator
docker compose build
docker compose up airflow-init
docker compose up -d
```

UI:
```text
http://localhost:8080
username: airflow
password: airflow
```

## DAG
```text
pipeline
```

Flow:
```text
prepare execution plan
download + upload reference data
branch: ingestion only | full pipeline
Glue Silver
Athena catalog + validation
optional dbt Gold
```

Trigger example:
```json
{
  "partition_scope": "all",
  "all_partition_scope": "2019:2024",
  "execution_mode": "per_month",
  "chunk_size": 3,
  "run_ingestion_only": false,
  "run_gold": false,
  "force_gold": false,
  "run_dbt_tests": true
}
```

## Reload
```bash
cd nyctx-airflow-orchestrator
docker compose restart airflow-scheduler airflow-webserver
```

## Logs
```bash
docker compose logs -f airflow-scheduler
docker compose logs -f airflow-webserver
find logs -type f | sort
```
