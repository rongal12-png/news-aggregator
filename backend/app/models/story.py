from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class Story(Base, TimestampMixin):
    __tablename__ = "stories"

    id = Column(Integer, primary_key=True, index=True)
    cluster_key = Column(String(500), nullable=False, unique=True)
    published_at = Column(DateTime(timezone=True), nullable=False)
    score = Column(Float, nullable=False, default=0.0)
    article_count = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    category = Column(String(50), nullable=False, default="general")
    # JSONB field storing score breakdown factors for explainability
    score_factors = Column(JSONB, nullable=False, default=dict)

    # Agent pipeline fields - SEO optimization
    meta_description = Column(Text, nullable=True)
    og_title = Column(String(255), nullable=True)
    og_description = Column(Text, nullable=True)
    og_image = Column(String(500), nullable=True)
    seo_keywords = Column(JSONB, nullable=True)

    # Agent pipeline fields - Geographic context
    country_code = Column(String(2), nullable=True, index=True)

    # Agent pipeline fields - Quality control
    is_newsworthy = Column(Boolean, nullable=False, default=True)
    newsworthiness_score = Column(Float, nullable=True)

    # Relationships
    articles = relationship("Article", back_populates="story")
    summaries = relationship("StorySummary", back_populates="story", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_stories_score", "score"),
        Index("idx_stories_published", "published_at"),
        Index("idx_stories_category", "category"),
        Index("idx_stories_country_code", "country_code"),
    )

    def __repr__(self):
        return f"<Story {self.id} score={self.score}>"
