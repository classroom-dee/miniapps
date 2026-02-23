from datetime import datetime

from sqlalchemy.orm import Session

from app.models.base import Item


async def add_search_result(
    db: Session,
    prod_id: str,
    name: str,
    category: str,
    price: int,
    link: str,
    time: datetime,
    user_id: str = None,
):
    item = Item(
        prod_id=prod_id,
        name=name,
        category=category,
        link=link,
        price=price,
        time=time,
        user_id=user_id,
    )
    db.add(item)
    db.flush()
    return item
