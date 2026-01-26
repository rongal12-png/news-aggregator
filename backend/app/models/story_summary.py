from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from .base import Base


class StorySummary(Base):
    __tablename__ = "story_summaries"

    id = Column(Integer, primary_key=True, index=True)
    story_id = Column(Integer, ForeignKey("stories.id", ondelete="CASCADE"), nullable=False)
    language = Column(String(10), nullable=False, default="en")
    title = Column(String(500), nullable=False)
    bullets = Column(JSONB, nullable=False, default=list)
    tags = Column(JSONB, nullable=False, default=list)
    # Summary mode: 'standard', 'tldr', 'delta', 'forward'
    mode = Column(String(20), nullable=False, default="standard")
    created_at = Column(DateTime(timezone=True), server_default="now()", nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default="now()", nullable=False)

    # Relationships
    story = relationship("Story", back_populates="summaries")

    __table_args__ = (
        UniqueConstraint("story_id", "language", "mode", name="uq_summary_story_language_mode"),
    )

    def __repr__(self):
        return f"<StorySummary story={self.story_id} lang={self.language}>"
