from fastapi import APIRouter

from app.schemas.monitor import Item

router = APIRouter()


@router.get("/monitor")
async def get_items():
    # fetch from db
    return ["a", "b"]


@router.get("/monitor/{id}")
def get_item(id: int):
    # fetch from db
    return "return specific item"


@router.post("/monitor")
def add_item(item: Item):  # pydantic
    print(item, flush=True)
    return "return added item"
