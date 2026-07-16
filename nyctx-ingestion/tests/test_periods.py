from pathlib import Path

import pytest

from nyctx_ingestion.periods import (
    expand_period_spec,
    load_year_months_from_file,
    normalize_periods,
    parse_year_month,
)


@pytest.mark.parametrize("value", ["2024-00", "2024-13", "1999-01", "24-01", "2024-1"])
def test_parse_year_month_rejects_invalid_values(value: str) -> None:
    with pytest.raises(ValueError):
        parse_year_month(value)


def test_expand_period_spec_supports_single_year() -> None:
    assert expand_period_spec("2024") == [(2024, month) for month in range(1, 13)]


def test_expand_period_spec_supports_month_range() -> None:
    assert expand_period_spec("2024-02:2024-04") == [
        (2024, 2),
        (2024, 3),
        (2024, 4),
    ]


def test_expand_period_spec_supports_mixed_year_and_month_boundaries() -> None:
    assert expand_period_spec("2024:2025-02") == [
        (2024, month) for month in range(1, 13)
    ] + [(2025, 1), (2025, 2)]


@pytest.mark.parametrize("value", ["2024-04:2024-02", "2024-01:bad", "bad", "1999"])
def test_expand_period_spec_rejects_invalid_values(value: str) -> None:
    with pytest.raises(ValueError):
        expand_period_spec(value)


def test_normalize_periods_deduplicates_and_sorts() -> None:
    assert normalize_periods(["2024-02", "2024", "2024-02:2024-03"]) == [
        (2024, month) for month in range(1, 13)
    ]


def test_load_year_months_ignores_comments_and_blank_lines(tmp_path: Path) -> None:
    path = tmp_path / "months.txt"
    path.write_text("# sample\n\n2024-01\n 2024:2024-02 \n", encoding="utf-8")
    assert load_year_months_from_file(path) == ["2024-01", "2024:2024-02"]
