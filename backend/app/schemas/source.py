from pydantic import BaseModel, HttpUrl
from datetime import datetime


class SourceBase(BaseModel):
    name: str
    feed_url: str
    language: str = "en"
    category: str = "general"
    weight: float = 1.0


class SourceCreate(SourceBase):
    pass


class SourceResponse(SourceBase):
    id: int
    is_active: bool
    last_fetched_at: datetime | None = None
    created_at: datetime

    class Config:
        from_attributes = True
