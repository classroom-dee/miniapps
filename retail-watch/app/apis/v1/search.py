import httpx
from fastapi import APIRouter, Depends

from app.apis.helpers import get_session
from app.schemas.search import SearchResultList
from app.scrapers.helpers import cached_search
from app.scrapers.search import get_search_result

router = APIRouter()


# User faced
@router.get("/search", response_model=SearchResultList)
async def get_result(
    category: str, keyword: str, session: httpx.AsyncClient = Depends(get_session)
):
    return await cached_search(
        lambda: get_search_result(session, category, keyword),
        category=category,
        keyword=keyword,
    )


# not for periodic collection!!
@router.get("/search/exact/{id}")
async def get_product(id: int, session: httpx.AsyncClient = Depends(get_session)):
    # fetch from the mall
    return "Result!"
