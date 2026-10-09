import pandas as pd

from funding_pipeline.ingestion.hyperliquid_client import fetch_snapshots
from funding_pipeline.models import AssetSnapshot

HOURS_PER_YEAR = 24 * 365  # Funding in Hyperliquid paid every hour


def snapshots_to_frame(snapshots: list[AssetSnapshot]) -> pd.DataFrame:
    rows = [s.model_dump() for s in snapshots]
    return pd.DataFrame(rows)


def add_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.assign(funding_apr=lambda x: x["funding"] * HOURS_PER_YEAR)
    df = df.assign(open_interest_usd=lambda x: x["open_interest"] * x["mark_px"])
    return df


def build_leaderboard(df: pd.DataFrame, min_volume: float) -> pd.DataFrame:
    mask = df["usd_volume"] >= min_volume
    df = df[mask]
    df = df.sort_values(by=["funding_apr"], ascending=False)
    return df


if __name__ == "__main__":
    data = snapshots_to_frame(fetch_snapshots())
    data = add_derived_columns(data)
    print(build_leaderboard(data, 500000))
