from datetime import UTC, datetime
from typing import Any

import httpx2
import pytest

from funding_pipeline.ingestion.hyperliquid_client import _is_retryable, parse_snapshots

URL = "https://api.hyperliquid.xyz/info"

SNAPSHOT_TIME = datetime(2026, 10, 9, 9, 0, tzinfo=UTC)


def make_ctx(funding: str, premium: str | None = "0.0004") -> dict[str, Any]:
    # Every field has a distinct value so a swapped mapping is caught.
    return {
        "markPx": "101",
        "funding": funding,
        "openInterest": "202",
        "dayNtlVlm": "303",
        "premium": premium,
        "oraclePx": "505",
    }


@pytest.fixture
def payload() -> list[Any]:
    universe = [
        {"name": "BTC", "szDecimals": 5},
        {"name": "MATIC", "szDecimals": 1, "isDelisted": True},
        {"name": "ETH", "szDecimals": 4},
    ]
    contexts = [
        make_ctx("0.0000125"),
        make_ctx("0.0"),
        make_ctx("0.00002", premium=None),
    ]
    return [{"universe": universe}, contexts]


def test_delisted_coins_are_skipped(payload: list[Any]) -> None:
    snapshots = parse_snapshots(payload, SNAPSHOT_TIME)
    assert [s.coin_name for s in snapshots] == ["BTC", "ETH"]


def test_fields_are_mapped_correctly(payload: list[Any]) -> None:
    eth = parse_snapshots(payload, SNAPSHOT_TIME)[1]
    assert eth.coin_name == "ETH"
    assert eth.funding == 0.00002
    assert eth.mark_px == 101
    assert eth.open_interest == 202
    assert eth.usd_volume == 303
    assert eth.oracle_px == 505
    assert eth.premium is None


def test_all_snapshots_share_one_timestamp(payload: list[Any]) -> None:
    snapshots = parse_snapshots(payload, SNAPSHOT_TIME)
    assert all(s.timestamp == SNAPSHOT_TIME for s in snapshots)


def test_mismatched_list_lengths_raise(payload: list[Any]) -> None:
    payload[1].pop()
    with pytest.raises(ValueError):
        parse_snapshots(payload, SNAPSHOT_TIME)


def make_status_error(status_code: int) -> httpx2.HTTPStatusError:
    request = httpx2.Request("POST", URL)
    response = httpx2.Response(status_code, request=request)
    return httpx2.HTTPStatusError("error", request=request, response=response)


@pytest.mark.parametrize("status_code", [429, 500, 502, 503, 504])
def test_retryable_status_codes(status_code: int) -> None:
    assert _is_retryable(make_status_error(status_code))


@pytest.mark.parametrize("status_code", [400, 401, 404, 422])
def test_client_errors_are_not_retried(status_code: int) -> None:
    assert not _is_retryable(make_status_error(status_code))


def test_network_errors_are_retried() -> None:
    assert _is_retryable(httpx2.ConnectError("connection failed"))
    assert _is_retryable(httpx2.ReadTimeout("timed out"))


def test_other_errors_are_not_retried() -> None:
    assert not _is_retryable(KeyError("universe"))
    assert not _is_retryable(ValueError("bad data"))
