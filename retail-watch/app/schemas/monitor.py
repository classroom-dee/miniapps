from datetime import datetime

from pydantic import BaseModel


class Item(BaseModel):
    name: str
    price: float
    link: str
    time: datetime
