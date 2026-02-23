import asyncio
import re
import time

import httpx
from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.base import Item
from app.models.session import _session_context
from app.schemas.search import SearchResultList

# ------------------- CONFIGS -------------------
CATEGORY_MAP = {
    "cpu": 873,
    "cool": 887,
    "mb": 875,
    "mem": 874,
    "gpu": 876,
    "ssd": 32617,
    "hdd": 877,
    "case": 879,
    "psu": 880,
}
MARKET_SEQ = 16
URL_BASE = f"https://shop.danawa.com/virtualestimate/?controller=estimateMain&methods=product&marketPlaceSeq={MARKET_SEQ}"
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": URL_BASE,
}


async def get_search_result(
    session: httpx.AsyncClient, category, keyword
) -> SearchResultList:
    full_url = f"{URL_BASE}&categorySeq={CATEGORY_MAP[category]}&categoryDepth=2&pseq=2&name={keyword}"
    link_url_base = f"{URL_BASE}&productSeq="

    r = await session.get(full_url, headers=HEADERS)
    r.raise_for_status()  # NOTE: Don't cache failures
    soup = BeautifulSoup(r.text, "html.parser")

    pattern = re.compile(r"^productList_(\d+)$")
    rows = soup.find_all("tr", class_=pattern)

    search_results: list[dict[str, str]] = []
    for row in rows:
        product_name = "No product name"
        product_price = "-1"
        product_id = None

        # prod id
        cls_list = row.get("class", [])
        for cls in cls_list:
            match = pattern.match(cls)
            if match:
                product_id = match.group(1)
                break

        # prod name
        p_wrapper = row.find("p", class_="subject")
        if p_wrapper:
            a_wrapper = p_wrapper.find("a")
            if a_wrapper:
                product_name = a_wrapper.get_text(strip=True)

        # prod price
        span_wrapper = row.find("span", class_="prod_price")
        if span_wrapper:
            product_price = span_wrapper.get_text(strip=True).replace(",", "")

        search_results.append(
            {
                "id": product_id,
                "category": category,
                "name": product_name,
                "price": product_price,
                "link": f"{link_url_base}{product_id}",
                "time": time.time(),
            }
        )

    return SearchResultList(results=search_results)


# NOTE: Use its own thread!!! dont pass main thread sessions!!
async def get_refreshed_results(
    db: Session, session: httpx.AsyncClient, user_id: str | None = None, rate_limit=3
) -> SearchResultList:
    """
    user_id: for debugging
    """
    statement = select(Item)
    if user_id:
        statement = statement.where(Item.user_id == user_id)
    items: list[Item] = db.scalars(statement).all()

    SP = asyncio.Semaphore(rate_limit)

    async def refresh_item(item: Item):
        async with SP:
            res = await get_search_result(session, item.category, item.name)
            return [
                r for r in res.results if r.id == item.prod_id and r.name == item.name
            ]

    results = await asyncio.gather(*(refresh_item(item) for item in items))

    flattened = [r for sublist in results for r in sublist]
    return SearchResultList(results=flattened)


async def scheduler():
    while True:
        async with httpx.AsyncClient() as session:
            with _session_context() as db:
                await get_refreshed_results(db, session)

        await asyncio.sleep(1800)
