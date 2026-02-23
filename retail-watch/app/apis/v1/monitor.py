from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.models.session import get_db
from app.schemas.monitor import Item, ItemAddResult
from app.scrapers.monitor import add_search_result

router = APIRouter()


# my list
@router.get("/monitor")
async def get_items():
    # fetch from db
    return ["a", "b"]


# analysis
@router.get("/monitor/{id}")
def get_item(id: int):
    # fetch from db
    return "return specific item"


# User faced
# Get user id
@router.post("/monitor", response_model=ItemAddResult)
async def add_item(item: Item, db: Session = Depends(get_db)):
    res_item = await add_search_result(
        db, item.prod_id, item.name, item.category, item.price, item.link, item.time
    )
    return {"result": res_item}
