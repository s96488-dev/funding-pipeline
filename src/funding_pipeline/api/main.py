from fastapi import FastAPI

from .routers import health

app = FastAPI()

app.include_router(health.router)
