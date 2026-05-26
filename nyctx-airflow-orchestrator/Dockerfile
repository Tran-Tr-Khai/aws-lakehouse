FROM apache/airflow:2.10.5-python3.11

ARG AIRFLOW_VERSION=2.10.5
ARG PYTHON_VERSION=3.11
ENV AIRFLOW_CONSTRAINTS_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"

USER root

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl unzip \
    && curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "/tmp/awscliv2.zip" \
    && unzip -q /tmp/awscliv2.zip -d /tmp \
    && /tmp/aws/install \
    && rm -rf /var/lib/apt/lists/* /tmp/aws /tmp/awscliv2.zip

COPY --chown=airflow:0 nyctx-ingestion /opt/airflow/project/nyctx-ingestion
COPY --chown=airflow:0 nyctx-airflow-orchestrator/dags /opt/airflow/dags

USER airflow

RUN pip install --no-cache-dir \
    --constraint "${AIRFLOW_CONSTRAINTS_URL}" \
    "apache-airflow-providers-amazon" \
    -e /opt/airflow/project/nyctx-ingestion
