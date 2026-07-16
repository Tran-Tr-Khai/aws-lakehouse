from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import boto3
from botocore.config import Config

from nyctx_athena_catalog.config import AthenaConfig


class AthenaQueryError(RuntimeError):
    """Raised when an Athena query fails or is cancelled."""


@dataclass(frozen=True)
class AthenaQueryResult:
    query_execution_id: str
    state: str
    data_scanned_bytes: int
    state_change_reason: str | None = None


def build_athena_client(config: AthenaConfig) -> Any:
    return boto3.client(
        'athena',
        region_name=config.aws_region,
        config=Config(
            retries={'max_attempts': 5, 'mode': 'standard'},
            connect_timeout=10,
            read_timeout=30,
        ),
    )


def start_query(client: Any, query: str, config: AthenaConfig) -> str:
    response = client.start_query_execution(
        WorkGroup=config.workgroup,
        QueryString=query,
        ResultConfiguration={'OutputLocation': config.output_location},
    )
    return response['QueryExecutionId']


def wait_for_query(client: Any, query_execution_id: str, config: AthenaConfig) -> AthenaQueryResult:
    started_at = time.monotonic()

    while True:
        response = client.get_query_execution(QueryExecutionId=query_execution_id)
        execution = response['QueryExecution']
        state = execution['Status']['State']

        print(f'[INFO] query_execution_id={query_execution_id} state={state}')

        if state == 'SUCCEEDED':
            stats = execution.get('Statistics', {})
            return AthenaQueryResult(
                query_execution_id=query_execution_id,
                state=state,
                data_scanned_bytes=int(stats.get('DataScannedInBytes', 0)),
                state_change_reason=execution['Status'].get('StateChangeReason'),
            )

        if state in {'FAILED', 'CANCELLED'}:
            reason = execution['Status'].get('StateChangeReason')
            raise AthenaQueryError(
                f'query_execution_id={query_execution_id} state={state} reason={reason}'
            )

        if state not in {'QUEUED', 'RUNNING'}:
            raise AthenaQueryError(
                f'query_execution_id={query_execution_id} unexpected_state={state}'
            )

        if time.monotonic() - started_at >= config.query_timeout_seconds:
            client.stop_query_execution(QueryExecutionId=query_execution_id)
            raise AthenaQueryError(
                f'query_execution_id={query_execution_id} state=TIMEOUT '
                f'timeout_seconds={config.query_timeout_seconds}'
            )

        time.sleep(config.poll_seconds)


def fetch_single_value(client: Any, query_execution_id: str) -> str | None:
    response = client.get_query_results(QueryExecutionId=query_execution_id)
    rows = response.get('ResultSet', {}).get('Rows', [])
    if len(rows) < 2:
        return None

    data = rows[1].get('Data', [])
    if not data:
        return None

    return data[0].get('VarCharValue')
