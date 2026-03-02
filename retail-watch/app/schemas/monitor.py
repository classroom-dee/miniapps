from datetime import datetime

from pydantic import BaseModel, field_validator


class Item(BaseModel):
    prod_id: str
    name: str
    category: str
    price: int
    link: str
    time: datetime

    @field_validator("time")
    @classmethod
    def must_have_timezone(cls, v: datetime):
        if v.tzinfo is None or v.utcoffset() is None:
            raise ValueError("time must include timezone")
        return v


class ItemAddResult(BaseModel):
    result: Item
