from unittest.mock import Mock, patch

import pytest

from nyctx_athena_catalog.athena import AthenaQueryError, wait_for_query
from nyctx_athena_catalog.config import AthenaConfig


def make_config(*, timeout_seconds: int = 1800) -> AthenaConfig:
    return AthenaConfig(
        aws_region='us-east-1',
        s3_bucket='bucket',
        workgroup='wg',
        output_location='s3://bucket/athena-results/',
        database='db',
        table_name='silver_yellow_taxi_iceberg',
        table_location='s3://bucket/silver/',
        zone_lookup_location='s3://bucket/reference/lookup/',
        zone_centroids_location='s3://bucket/reference/centroids/',
        poll_seconds=1,
        query_timeout_seconds=timeout_seconds,
    )


@patch('nyctx_athena_catalog.athena.time.sleep')
def test_wait_for_query_handles_running_then_success(sleep: Mock) -> None:
    client = Mock()
    client.get_query_execution.side_effect = [
        {'QueryExecution': {'Status': {'State': 'RUNNING'}}},
        {
            'QueryExecution': {
                'Status': {'State': 'SUCCEEDED'},
                'Statistics': {'DataScannedInBytes': 1234},
            }
        },
    ]

    result = wait_for_query(client, 'query-id', make_config())

    assert result.state == 'SUCCEEDED'
    assert result.data_scanned_bytes == 1234
    sleep.assert_called_once_with(1)


def test_wait_for_query_surfaces_failure_reason() -> None:
    client = Mock()
    client.get_query_execution.return_value = {
        'QueryExecution': {
            'Status': {'State': 'FAILED', 'StateChangeReason': 'bad SQL'},
        }
    }

    with pytest.raises(AthenaQueryError, match='bad SQL'):
        wait_for_query(client, 'query-id', make_config())


@patch('nyctx_athena_catalog.athena.time.monotonic', side_effect=[0, 1])
def test_wait_for_query_cancels_timed_out_query(monotonic: Mock) -> None:
    client = Mock()
    client.get_query_execution.return_value = {
        'QueryExecution': {'Status': {'State': 'RUNNING'}}
    }

    with pytest.raises(AthenaQueryError, match='state=TIMEOUT'):
        wait_for_query(client, 'query-id', make_config(timeout_seconds=1))

    client.stop_query_execution.assert_called_once_with(QueryExecutionId='query-id')


def test_wait_for_query_rejects_unknown_state() -> None:
    client = Mock()
    client.get_query_execution.return_value = {
        'QueryExecution': {'Status': {'State': 'UNKNOWN'}}
    }

    with pytest.raises(AthenaQueryError, match='unexpected_state=UNKNOWN'):
        wait_for_query(client, 'query-id', make_config())
