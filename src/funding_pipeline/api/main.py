from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from funding_pipeline.api.routers import funding, health, leaderboard
from funding_pipeline.config import Settings
from funding_pipeline.processing.storage import create_db_engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    engine = create_db_engine(Settings())
    app.state.engine = engine
    yield
    engine.dispose()


app = FastAPI(title="Funding Pipeline API", lifespan=lifespan)
app.include_router(health.router)
app.include_router(leaderboard.router)
app.include_router(funding.router)
