import pytest

from nyctx_ingestion.centroids import ring_centroid


def test_ring_centroid_for_square() -> None:
    result = ring_centroid([(0, 0), (2, 0), (2, 2), (0, 2)])
    assert result is not None
    area, x, y = result
    assert abs(area) == pytest.approx(4.0)
    assert x == pytest.approx(1.0)
    assert y == pytest.approx(1.0)
