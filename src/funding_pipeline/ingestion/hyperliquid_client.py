from datetime import UTC, datetime
from typing import Any

import httpx2

from funding_pipeline.models import AssetSnapshot


def fetch_snapshots() -> list[AssetSnapshot]:
    request_body = {"type": "metaAndAssetCtxs"}
    r = httpx2.post("https://api.hyperliquid.xyz/info", json=request_body, timeout=10)
    r.raise_for_status()
    payload = r.json()
    snapshot_time = datetime.now(UTC)
    return parse_snapshots(payload, snapshot_time)


def parse_snapshots(payload: Any, snapshot_time: datetime) -> list[AssetSnapshot]:
    models_list = []
    universe = payload[0]["universe"]
    asset_contexts = payload[1]
    for coin, ctx in zip(universe, asset_contexts, strict=True):
        if coin.get("isDelisted", False):
            continue
        snapshot = AssetSnapshot(
            coin_name=coin["name"],
            mark_px=ctx["markPx"],
            funding=ctx["funding"],
            open_interest=ctx["openInterest"],
            usd_volume=ctx["dayNtlVlm"],
            premium=ctx["premium"],
            oracle_px=ctx["oraclePx"],
            timestamp=snapshot_time,
        )
        models_list.append(snapshot)
    return models_list


if __name__ == "__main__":
    sorted_snapshots = sorted(fetch_snapshots(), key=lambda s: s.funding, reverse=True)
    print(len(sorted_snapshots))
    for snapshot in sorted_snapshots[:10]:
        print(f"{snapshot.coin_name}: {snapshot.funding:.4%}")
