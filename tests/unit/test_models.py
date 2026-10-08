from datetime import UTC, datetime
from typing import Any

import pytest
from pydantic import ValidationError

from funding_pipeline.models import AssetSnapshot


@pytest.fixture
def snapshot_data() -> dict[str, Any]:
    return {
        "coin_name": "BTC",
        "mark_px": "81200",
        "funding": "0.0001",
        "open_interest": "0.3",
        "usd_volume": "100000",
        "premium": "0.001",
        "oracle_px": "81300",
        "timestamp": datetime(2026, 10, 8, 9, 0, tzinfo=UTC),
    }


def test_numeric_strings_become_floats(snapshot_data: dict[str, Any]) -> None:
    snapshot = AssetSnapshot(**snapshot_data)
    assert snapshot.funding == 0.0001
    assert isinstance(snapshot.mark_px, float)


def test_premium_can_be_none(snapshot_data: dict[str, Any]) -> None:
    snapshot_data["premium"] = None
    snapshot = AssetSnapshot(**snapshot_data)
    assert snapshot.premium is None


def test_naive_timestamp_is_rejected(snapshot_data: dict[str, Any]) -> None:
    snapshot_data["timestamp"] = datetime(2026, 10, 8, 9, 0)
    with pytest.raises(ValidationError):
        AssetSnapshot(**snapshot_data)


def test_garbage_funding_is_rejected(snapshot_data: dict[str, Any]) -> None:
    snapshot_data["funding"] = "abc"
    with pytest.raises(ValidationError):
        AssetSnapshot(**snapshot_data)
