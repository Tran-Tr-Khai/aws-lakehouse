from __future__ import annotations

import argparse
from pathlib import Path

import pytest
import requests

from nyctx_ingestion.download import build_download_plan, download_file, probe_remote_size


class FakeResponse:
    def __init__(self, body: bytes, *, content_length: int | None = None) -> None:
        self.body = body
        self.headers = {
            "Content-Length": str(len(body) if content_length is None else content_length)
        }

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def raise_for_status(self) -> None:
        return None

    def iter_content(self, chunk_size: int):  # noqa: ANN201
        yield self.body


class FakeSession:
    def __init__(self, body: bytes, *, content_length: int | None = None) -> None:
        self.response = FakeResponse(body, content_length=content_length)

    def head(self, *args: object, **kwargs: object) -> FakeResponse:
        return self.response

    def get(self, *args: object, **kwargs: object) -> FakeResponse:
        return self.response

    def close(self) -> None:
        return None


class HeadForbiddenSession(FakeSession):
    def head(self, *args: object, **kwargs: object) -> FakeResponse:
        response = requests.Response()
        response.status_code = 403
        raise requests.HTTPError('403 Client Error', response=response)


def make_args(**overrides: object) -> argparse.Namespace:
    values = {
        "year": None,
        "months": None,
        "year_months": None,
        "months_file": None,
    }
    values.update(overrides)
    return argparse.Namespace(**values)


def test_download_is_published_only_after_validation(tmp_path: Path) -> None:
    output = tmp_path / "lookup.csv"
    download_file("https://example.test/lookup.csv", output, session=FakeSession(b"a,b\n1,2\n"))
    assert output.read_bytes() == b"a,b\n1,2\n"
    assert not output.with_name("lookup.csv.part").exists()


def test_download_removes_partial_file_on_size_mismatch(tmp_path: Path) -> None:
    output = tmp_path / "lookup.csv"
    with pytest.raises(ValueError, match="size mismatch"):
        download_file(
            "https://example.test/lookup.csv",
            output,
            session=FakeSession(b"short", content_length=100),
        )
    assert not output.exists()
    assert not output.with_name("lookup.csv.part").exists()


def test_probe_remote_size_ignores_head_403() -> None:
    assert probe_remote_size(HeadForbiddenSession(b'content'), 'https://example.test/file.csv') is None


def test_download_falls_back_when_head_is_forbidden(tmp_path: Path) -> None:
    output = tmp_path / 'lookup.csv'
    download_file(
        'https://example.test/lookup.csv',
        output,
        session=HeadForbiddenSession(b'a,b\n1,2\n'),
    )
    assert output.read_bytes() == b'a,b\n1,2\n'


def test_download_plan_rejects_mixed_input_methods() -> None:
    with pytest.raises(ValueError, match="exactly one"):
        build_download_plan(make_args(year=2024, months=[1], year_months=["2024-02"]))
