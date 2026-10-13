from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException, Query

from funding_pipeline.api.deps import EngineDep
from funding_pipeline.api.schemas import FundingPoint
from funding_pipeline.processing.features import HOURS_PER_YEAR
from funding_pipeline.processing.storage import fetch_coin_history

router = APIRouter(tags=["funding"])


@router.get("/funding/{symbol}")
def get_funding_history(
    symbol: str,
    engine: EngineDep,
    hours: int = Query(24, ge=1, le=24 * 30),
) -> list[FundingPoint]:
    since = datetime.now(UTC) - timedelta(hours=hours)
    snapshots = fetch_coin_history(engine, symbol, since)
    if not snapshots:
        raise HTTPException(status_code=404, detail=f"No data for {symbol}")
    return [
        FundingPoint(
            timestamp=s.timestamp,
            funding=s.funding,
            funding_apr=s.funding * HOURS_PER_YEAR,
            mark_px=s.mark_px,
        )
        for s in snapshots
    ]
