from pydantic import BaseModel


class SearchResult(BaseModel):
    id: str
    name: str
    category: str
    price: str
    link: str
    time: float


class SearchResultList(BaseModel):
    results: list[SearchResult]
