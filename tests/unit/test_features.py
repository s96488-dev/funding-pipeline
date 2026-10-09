from datetime import UTC, datetime

import pandas as pd
import pytest

from funding_pipeline.models import AssetSnapshot
from funding_pipeline.processing.features import (
    HOURS_PER_YEAR,
    add_derived_columns,
    build_leaderboard,
    snapshots_to_frame,
)

SNAPSHOT_TIME = datetime(2026, 10, 9, 9, 0, tzinfo=UTC)


def make_snapshot(coin: str, funding: float, usd_volume: float) -> AssetSnapshot:
    return AssetSnapshot(
        coin_name=coin,
        mark_px=2.0,
        funding=funding,
        open_interest=100.0,
        usd_volume=usd_volume,
        premium=0.0,
        oracle_px=2.0,
        timestamp=SNAPSHOT_TIME,
    )


@pytest.fixture
def frame() -> pd.DataFrame:
    snapshots = [
        make_snapshot("LOW", funding=0.00001, usd_volume=1_000_000),
        make_snapshot("HIGH", funding=0.00005, usd_volume=1_000_000),
        make_snapshot("ILLIQUID", funding=0.001, usd_volume=10_000),
    ]
    return add_derived_columns(snapshots_to_frame(snapshots))


def test_snapshots_to_frame_has_one_row_per_snapshot() -> None:
    df = snapshots_to_frame([make_snapshot("BTC", 0.0001, 1.0)])
    assert len(df) == 1
    assert df.loc[0, "coin_name"] == "BTC"


def test_baseline_hourly_funding_is_about_11_percent_apr() -> None:
    # Hyperliquid pays funding hourly: 0.00125% per hour ≈ 10.95% per year.
    df = add_derived_columns(snapshots_to_frame([make_snapshot("BTC", 0.0000125, 1.0)]))
    assert df.loc[0, "funding_apr"] == pytest.approx(0.1095)


def test_funding_apr_uses_hours_per_year(frame: pd.DataFrame) -> None:
    high = frame.loc[frame["coin_name"] == "HIGH", "funding_apr"].item()
    assert high == pytest.approx(0.00005 * HOURS_PER_YEAR)


def test_open_interest_is_converted_to_usd(frame: pd.DataFrame) -> None:
    assert (frame["open_interest_usd"] == 200.0).all()


def test_add_derived_columns_does_not_mutate_input() -> None:
    df = snapshots_to_frame([make_snapshot("BTC", 0.0001, 1.0)])
    add_derived_columns(df)
    assert "funding_apr" not in df.columns


def test_leaderboard_drops_illiquid_coins(frame: pd.DataFrame) -> None:
    board = build_leaderboard(frame, min_volume=500_000)
    assert "ILLIQUID" not in board["coin_name"].tolist()


def test_leaderboard_is_sorted_by_funding_desc(frame: pd.DataFrame) -> None:
    board = build_leaderboard(frame, min_volume=500_000)
    assert board["coin_name"].tolist() == ["HIGH", "LOW"]


def test_leaderboard_keeps_coin_exactly_at_min_volume(frame: pd.DataFrame) -> None:
    board = build_leaderboard(frame, min_volume=1_000_000)
    assert set(board["coin_name"]) == {"HIGH", "LOW"}
