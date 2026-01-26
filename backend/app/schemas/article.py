from pydantic import BaseModel
from datetime import datetime


class ArticleResponse(BaseModel):
    id: int
    title: str
    url: str
    source: str
    published_at: datetime

    class Config:
        from_attributes = True
