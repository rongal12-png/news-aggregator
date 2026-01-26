from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship

from .base import Base


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("sources.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(500), nullable=False)
    url = Column(String(2000), nullable=False)
    url_hash = Column(String(64), nullable=False)
    snippet = Column(Text, nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=False)
    normalized_key = Column(String(500), nullable=True, index=True)
    story_id = Column(Integer, ForeignKey("stories.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default="now()", nullable=False)

    # Agent pipeline fields - Article filtering
    is_filtered = Column(Boolean, nullable=False, default=False, index=True)
    filter_reason = Column(Text, nullable=True)
    importance_score = Column(Float, nullable=True, index=True)

    # Relationships
    source = relationship("Source", back_populates="articles")
    story = relationship("Story", back_populates="articles")

    __table_args__ = (
        UniqueConstraint("source_id", "url_hash", name="uq_article_source_url"),
        Index("idx_articles_published", "published_at"),
        Index("idx_articles_story", "story_id"),
        Index("idx_articles_is_filtered", "is_filtered"),
        Index("idx_articles_importance_score", "importance_score"),
    )

    def __repr__(self):
        return f"<Article {self.title[:50]}>"
