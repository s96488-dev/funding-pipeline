from pydantic import AwareDatetime, BaseModel


class AssetSnapshot(BaseModel):
    coin_name: str
    mark_px: float
    funding: float
    open_interest: float
    usd_volume: float
    premium: float | None
    oracle_px: float
    timestamp: AwareDatetime
