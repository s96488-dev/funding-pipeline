from sqlalchemy import (
    Column,
    DateTime,
    Double,
    Engine,
    MetaData,
    Table,
    Text,
    create_engine,
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
    )
    with engine.begin() as conn:
        result = conn.execute(stmt)
    return result.rowcount
