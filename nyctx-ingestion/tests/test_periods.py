from pathlib import Path

import pytest

from nyctx_ingestion.periods import (
    load_year_months_from_file,
    normalize_periods,
    parse_year_month,
)


@pytest.mark.parametrize("value", ["2024-00", "2024-13", "1999-01", "24-01", "2024-1"])
def test_parse_year_month_rejects_invalid_values(value: str) -> None:
    with pytest.raises(ValueError):
        parse_year_month(value)


def test_normalize_periods_deduplicates_and_sorts() -> None:
    assert normalize_periods(["2024-02", "2024-01", "2024-02"]) == [
        (2024, 1),
        (2024, 2),
    ]


def test_load_year_months_ignores_comments_and_blank_lines(tmp_path: Path) -> None:
    path = tmp_path / "months.txt"
    path.write_text("# sample\n\n2024-01\n 2024-02 \n", encoding="utf-8")
    assert load_year_months_from_file(path) == ["2024-01", "2024-02"]
