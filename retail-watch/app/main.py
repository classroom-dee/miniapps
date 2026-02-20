from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from app.apis.v1.monitor import router as v1_monitor
from app.apis.v1.search import router as v1_search


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.client = httpx.AsyncClient()
    yield
    await app.state.client.aclose()


app = FastAPI(lifespan=lifespan)

app.include_router(v1_monitor, prefix="/v1")
app.include_router(v1_search, prefix="/v1")
