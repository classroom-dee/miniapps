import asyncio
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from app.apis.v1.monitor import router as v1_monitor
from app.apis.v1.search import router as v1_search
from app.config import templates
from app.models.session import init_db
from app.scrapers.search import scheduler

init_db()


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.client = httpx.AsyncClient()
    # NOTE: don't do this with multiple uvicorn worker!
    task = asyncio.create_task(scheduler())
    yield
    task.cancel()
    await app.state.client.aclose()


app = FastAPI(lifespan=lifespan)


origins = ["http://localhost", "http://localhost:8000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_monitor, prefix="/v1")
app.include_router(v1_search, prefix="/v1")


# That reminds me of Servlet 🤔
# move on to SPA if time allows
@app.get("/", response_class=HTMLResponse)
def signin(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


FAKE_DB = [
    {"id": 1, "name": "Item One"},
    {"id": 2, "name": "Item Two"},
    {"id": 3, "name": "Item Three"},
]


@app.get("/my-list", response_class=HTMLResponse)
def my_list(request: Request):
    return templates.TemplateResponse(
        "mylist.html", {"request": request, "items": FAKE_DB}
    )
