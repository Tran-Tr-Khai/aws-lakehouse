"""Parsing and validation for monthly ingestion periods."""

import re
from pathlib import Path

YEAR_MONTH_PATTERN = re.compile(r"\d{4}-\d{2}")


def parse_year_month(value: str) -> tuple[int, int]:
    """Parse a YYYY-MM value and validate its calendar range."""
    if not YEAR_MONTH_PATTERN.fullmatch(value):
        raise ValueError(f"Invalid year-month format: {value}. Expected YYYY-MM.")

    year_text, month_text = value.split("-", maxsplit=1)
    year, month = int(year_text), int(month_text)
    if not 2000 <= year <= 2100:
        raise ValueError(f"Invalid year: {year}. Expected a value between 2000 and 2100.")
    if not 1 <= month <= 12:
        raise ValueError(f"Invalid month: {month}. Month must be between 01 and 12.")
    return year, month


def load_year_months_from_file(path: Path) -> list[str]:
    """Load non-empty, non-comment YYYY-MM values from a text file."""
    if not path.is_file():
        raise FileNotFoundError(f"Months file not found: {path}")

    return [
        value
        for line in path.read_text(encoding="utf-8").splitlines()
        if (value := line.strip()) and not value.startswith("#")
    ]


def normalize_periods(values: list[str]) -> list[tuple[int, int]]:
    """Validate, deduplicate, and sort period values."""
    return sorted({parse_year_month(value) for value in values})
