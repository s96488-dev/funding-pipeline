from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Double,
    Engine,
    MetaData,
    Table,
    Text,
    create_engine,
    func,
    select,
)
from sqlalchemy.dialects.postgresql import insert

from funding_pipeline.config import Settings
from funding_pipeline.models import AssetSnapshot

metadata = MetaData()

asset_snapshots = Table(
    "asset_snapshots",
    metadata,
    # Primary key order matters: (coin_name, timestamp) makes
    # "history of one coin over a period" an index range scan.
    Column("coin_name", Text, primary_key=True),
    Column("timestamp", DateTime(timezone=True), primary_key=True),
    Column("mark_px", Double, nullable=False),
    Column("funding", Double, nullable=False),
    Column("open_interest", Double, nullable=False),
    Column("usd_volume", Double, nullable=False),
    Column("premium", Double, nullable=True),
    Column("oracle_px", Double, nullable=False),
)


def create_db_engine(settings: Settings) -> Engine:
    return create_engine(settings.database_url, pool_pre_ping=True)


def insert_snapshots(engine: Engine, snapshots: list[AssetSnapshot]) -> int:
    """Insert snapshots, silently skipping ones that are already stored.

    Returns the number of rows actually inserted.
    """
    if not snapshots:
        return 0
    rows = [s.model_dump() for s in snapshots]
    stmt = (
        insert(asset_snapshots)
        .values(rows)
        .on_conflict_do_nothing(index_elements=["coin_name", "timestamp"])
        .returning(asset_snapshots.c.coin_name)
    )
    with engine.begin() as conn:
        result = conn.execute(stmt)
        return len(result.fetchall())


def fetch_latest_snapshots(engine: Engine, since: datetime) -> list[AssetSnapshot]:
    """Latest snapshot per coin, ignoring coins not seen since `since`."""
    latest = (
        select(
            asset_snapshots.c.coin_name,
            func.max(asset_snapshots.c.timestamp).label("latest_ts"),
        )
        .group_by(asset_snapshots.c.coin_name)
        .subquery()
    )
    stmt = (
        select(asset_snapshots)
        .join(
            latest,
            (asset_snapshots.c.coin_name == latest.c.coin_name)
            & (asset_snapshots.c.timestamp == latest.c.latest_ts),
        )
        .where(latest.c.latest_ts >= since)
    )
    with engine.connect() as conn:
        rows = conn.execute(stmt).mappings().all()
    return [AssetSnapshot.model_validate(dict(row)) for row in rows]


def fetch_coin_history(
    engine: Engine, coin_name: str, since: datetime
) -> list[AssetSnapshot]:
    stmt = (
        select(asset_snapshots)
        .where(asset_snapshots.c.coin_name == coin_name)
        .where(asset_snapshots.c.timestamp >= since)
        .order_by(asset_snapshots.c.timestamp)
    )
    with engine.connect() as conn:
        rows = conn.execute(stmt).mappings().all()
    return [AssetSnapshot.model_validate(dict(row)) for row in rows]
