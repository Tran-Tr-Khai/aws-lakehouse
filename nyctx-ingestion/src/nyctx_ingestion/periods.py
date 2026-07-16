"""Parsing and expansion for ingestion partition period specs."""

from __future__ import annotations

import re
from pathlib import Path

YEAR_PATTERN = re.compile(r"\d{4}")
YEAR_MONTH_PATTERN = re.compile(r"\d{4}-\d{2}")


def parse_year_month(value: str) -> tuple[int, int]:
    """Parse a YYYY-MM value and validate its calendar range."""
    if not YEAR_MONTH_PATTERN.fullmatch(value):
        raise ValueError(f"Invalid year-month format: {value}. Expected YYYY-MM.")

    year_text, month_text = value.split("-", maxsplit=1)
    year, month = int(year_text), int(month_text)
    validate_year(year)
    validate_month(month)
    return year, month


def validate_year(year: int) -> None:
    if not 2000 <= year <= 2100:
        raise ValueError(f"Invalid year: {year}. Expected a value between 2000 and 2100.")


def validate_month(month: int) -> None:
    if not 1 <= month <= 12:
        raise ValueError(f"Invalid month: {month}. Month must be between 01 and 12.")


def parse_period_boundary(value: str, *, is_end: bool) -> tuple[int, int]:
    """Parse a range boundary from YYYY or YYYY-MM into a concrete month."""
    if YEAR_MONTH_PATTERN.fullmatch(value):
        return parse_year_month(value)
    if YEAR_PATTERN.fullmatch(value):
        year = int(value)
        validate_year(year)
        return (year, 12) if is_end else (year, 1)
    raise ValueError(
        f"Invalid period boundary: {value}. Expected YYYY or YYYY-MM."
    )


def iter_month_range(start: tuple[int, int], end: tuple[int, int]) -> list[tuple[int, int]]:
    if start > end:
        raise ValueError(
            f"Invalid period range: {start[0]:04d}-{start[1]:02d} is after "
            f"{end[0]:04d}-{end[1]:02d}."
        )

    periods: list[tuple[int, int]] = []
    year, month = start
    end_year, end_month = end
    while (year, month) <= (end_year, end_month):
        periods.append((year, month))
        if month == 12:
            year += 1
            month = 1
        else:
            month += 1
    return periods


def expand_period_spec(value: str) -> list[tuple[int, int]]:
    """Expand one period spec into concrete year-month partitions."""
    value = value.strip()
    if not value:
        return []
    if ":" in value:
        start_text, end_text = value.split(":", maxsplit=1)
        start = parse_period_boundary(start_text.strip(), is_end=False)
        end = parse_period_boundary(end_text.strip(), is_end=True)
        return iter_month_range(start, end)
    if YEAR_MONTH_PATTERN.fullmatch(value):
        return [parse_year_month(value)]
    if YEAR_PATTERN.fullmatch(value):
        year = int(value)
        validate_year(year)
        return [(year, month) for month in range(1, 13)]
    raise ValueError(
        f"Invalid period spec: {value}. Expected YYYY-MM, YYYY, or START:END."
    )


def load_year_months_from_file(path: Path) -> list[str]:
    """Load non-empty, non-comment period specs from a text file."""
    if not path.is_file():
        raise FileNotFoundError(f"Months file not found: {path}")

    values: list[str] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", maxsplit=1)[0].strip()
        if line:
            values.append(line)
    return values


def normalize_periods(values: list[str]) -> list[tuple[int, int]]:
    """Expand, deduplicate, and sort partition period specs."""
    periods = {
        period
        for value in values
        for period in expand_period_spec(value)
    }
    return sorted(periods)
