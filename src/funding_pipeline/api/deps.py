from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy import Engine


def get_engine(request: Request) -> Engine:
    engine: Engine = request.app.state.engine
    return engine


EngineDep = Annotated[Engine, Depends(get_engine)]
