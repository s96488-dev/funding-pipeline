from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Query

from funding_pipeline.api.deps import EngineDep
from funding_pipeline.api.schemas import LeaderboardEntry
from funding_pipeline.processing.features import (
    add_derived_columns,
    build_leaderboard,
    snapshots_to_frame,
)
from funding_pipeline.processing.storage import fetch_latest_snapshots

router = APIRouter(tags=["funding"])

# Coins without a fresh snapshot are considered gone (e.g. delisted).
STALE_AFTER = timedelta(minutes=10)


@router.get("/leaderboard")
def get_leaderboard(
    engine: EngineDep,
    min_volume: float = Query(500_000, ge=0),
    limit: int = Query(20, ge=1, le=200),
) -> list[LeaderboardEntry]:
    since = datetime.now(UTC) - STALE_AFTER
    snapshots = fetch_latest_snapshots(engine, since)
    if not snapshots:
        return []
    frame = add_derived_columns(snapshots_to_frame(snapshots))
    board = build_leaderboard(frame, min_volume).head(limit)
    return [LeaderboardEntry.model_validate(r) for r in board.to_dict("records")]
