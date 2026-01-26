from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class Source(Base, TimestampMixin):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    feed_url = Column(String(2000), nullable=False, unique=True)
    language = Column(String(10), nullable=False, default="en")
    category = Column(String(50), nullable=False, default="general")
    weight = Column(Float, nullable=False, default=1.0)
    is_active = Column(Boolean, nullable=False, default=True)
    last_fetched_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    articles = relationship("Article", back_populates="source", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Source {self.name}>"
