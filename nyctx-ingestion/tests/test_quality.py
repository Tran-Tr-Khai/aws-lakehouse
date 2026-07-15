from pathlib import Path

import pandas as pd
import pytest

from nyctx_ingestion.quality import build_month_summary, parse_args, run, sum_violation_counts


def test_violation_count_excludes_distinct_row_aggregate() -> None:
    frame = pd.DataFrame(
        [{'critical_row_count': 2, 'invalid_datetime_count': 2, 'invalid_fare_count': 1}]
    )
    assert sum_violation_counts(frame, 'critical_row_count') == 3


def test_month_summary_calculates_distinct_row_ratios() -> None:
    results = {
        'summary': pd.DataFrame([{'total_rows': 10}]),
        'critical_quality': pd.DataFrame([{'critical_row_count': 2, 'invalid_datetime_count': 2}]),
        'warning_quality': pd.DataFrame([{'warning_row_count': 1, 'invalid_vendor_count': 1}]),
    }
    summary = build_month_summary(2024, 1, Path('sample.parquet'), results, None)
    assert summary['critical_row_ratio'] == 0.2
    assert summary['warning_row_ratio'] == 0.1


def test_quality_run_rejects_empty_months_file(tmp_path: Path) -> None:
    path = tmp_path / 'months.txt'
    path.write_text('# comments only\n\n', encoding='utf-8')
    with pytest.raises(ValueError, match='No valid periods'):
        run(parse_args(['--months-file', str(path)]))
