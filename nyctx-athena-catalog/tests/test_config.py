import pytest

from nyctx_athena_catalog.config import AthenaConfig


def test_from_env_uses_production_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        'AWS_REGION',
        'AWS_DEFAULT_REGION',
        'NYCTX_S3_BUCKET',
        'NYCTX_ATHENA_DATABASE',
        'NYCTX_ATHENA_POLL_SECONDS',
        'NYCTX_ATHENA_QUERY_TIMEOUT_SECONDS',
    ):
        monkeypatch.delenv(name, raising=False)

    config = AthenaConfig.from_env()

    assert config.s3_bucket == 'nyc-taxi-lakehouse-tntk'
    assert config.database == 'nyc_taxi_lakehouse'
    assert config.poll_seconds == 5
    assert config.query_timeout_seconds == 1800


@pytest.mark.parametrize(
    ('name', 'value', 'message'),
    [
        ('NYCTX_ATHENA_DATABASE', 'bad-name', 'valid unquoted Athena identifier'),
        ('NYCTX_ATHENA_POLL_SECONDS', '0', 'greater than zero'),
        ('NYCTX_ATHENA_QUERY_TIMEOUT_SECONDS', 'invalid', 'must be an integer'),
        ('NYCTX_ATHENA_YEAR_RANGE', '2030,2019', 'start must not exceed end'),
    ],
)
def test_from_env_rejects_invalid_configuration(
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    value: str,
    message: str,
) -> None:
    monkeypatch.setenv(name, value)

    with pytest.raises(ValueError, match=message):
        AthenaConfig.from_env()
