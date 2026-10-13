from pydantic import AwareDatetime, BaseModel


class LeaderboardEntry(BaseModel):
    coin_name: str
    funding: float
    funding_apr: float
    usd_volume: float
    open_interest_usd: float
    mark_px: float
    timestamp: AwareDatetime


class FundingPoint(BaseModel):
    timestamp: AwareDatetime
    funding: float
    funding_apr: float
    mark_px: float
