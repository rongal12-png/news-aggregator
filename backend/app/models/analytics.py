from sqlalchemy import Column, Integer, String, DateTime, Date, JSON, Index, Boolean
from datetime import datetime, timezone

from .base import Base


class PageView(Base):
    """Track page views for analytics."""
    __tablename__ = "page_views"

    id = Column(Integer, primary_key=True, index=True)
    path = Column(String(500), nullable=False)
    locale = Column(String(10), default="en")
    story_id = Column(Integer, nullable=True)
    category = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    ip_hash = Column(String(64), nullable=True)  # Hashed for privacy
    referrer = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index('idx_pageviews_created', 'created_at'),
        Index('idx_pageviews_path', 'path'),
        Index('idx_pageviews_story', 'story_id'),
    )


class DailyStats(Base):
    """Aggregated daily statistics."""
    __tablename__ = "daily_stats"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, unique=True, index=True)
    total_views = Column(Integer, default=0)
    unique_visitors = Column(Integer, default=0)
    views_en = Column(Integer, default=0)
    views_he = Column(Integer, default=0)
    top_stories = Column(JSON, default=list)  # [{story_id, views}]
    top_categories = Column(JSON, default=list)  # [{category, views}]
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Category(Base):
    """Dynamic category management."""
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(50), nullable=False, unique=True)
    name_en = Column(String(100), nullable=False)
    name_he = Column(String(100), nullable=False)
    icon = Column(String(10), default="📰")
    color = Column(String(20), default="#6b7280")
    sort_order = Column(Integer, default=100)
    is_active = Column(Boolean, default=True)
    locale_filter = Column(String(10), nullable=True)  # null=all, 'he'=Hebrew only, 'en'=English only
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class SystemSettings(Base):
    """System-wide settings storage."""
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), nullable=False, unique=True)
    value = Column(String(500), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
