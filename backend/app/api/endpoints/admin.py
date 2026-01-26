from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta, timezone, date
from typing import Optional
import hashlib

from app.db import get_db
from app.models import Source, Article, Story, StorySummary, PageView, DailyStats, Category, SystemSettings

router = APIRouter()


# ============ DASHBOARD STATS ============

@router.get("/dashboard")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get overview statistics for the dashboard."""
    now = datetime.now(timezone.utc)
    today = now.date()
    week_ago = today - timedelta(days=7)

    # Basic counts
    total_sources = db.query(Source).count()
    active_sources = db.query(Source).filter(Source.is_active == True).count()
    total_articles = db.query(Article).count()
    total_stories = db.query(Story).filter(Story.is_active == True).count()

    # Articles in last 24h
    yesterday = now - timedelta(hours=24)
    recent_articles = db.query(Article).filter(Article.created_at >= yesterday).count()

    # Page views today
    today_views = db.query(PageView).filter(
        func.date(PageView.created_at) == today
    ).count()

    # Page views this week
    week_views = db.query(PageView).filter(
        func.date(PageView.created_at) >= week_ago
    ).count()

    # Unique visitors today (by ip_hash)
    unique_today = db.query(func.count(func.distinct(PageView.ip_hash))).filter(
        func.date(PageView.created_at) == today
    ).scalar() or 0

    # Views by locale today
    locale_stats = db.query(
        PageView.locale,
        func.count(PageView.id)
    ).filter(
        func.date(PageView.created_at) == today
    ).group_by(PageView.locale).all()

    views_by_locale = {locale: count for locale, count in locale_stats}

    # Top categories today
    category_stats = db.query(
        PageView.category,
        func.count(PageView.id)
    ).filter(
        func.date(PageView.created_at) == today,
        PageView.category != None
    ).group_by(PageView.category).order_by(desc(func.count(PageView.id))).limit(5).all()

    # Sources by category
    sources_by_category = db.query(
        Source.category,
        func.count(Source.id)
    ).filter(Source.is_active == True).group_by(Source.category).all()

    return {
        "overview": {
            "total_sources": total_sources,
            "active_sources": active_sources,
            "total_articles": total_articles,
            "total_stories": total_stories,
            "recent_articles_24h": recent_articles,
        },
        "traffic": {
            "views_today": today_views,
            "views_week": week_views,
            "unique_visitors_today": unique_today,
            "views_by_locale": views_by_locale,
        },
        "top_categories": [
            {"category": cat, "views": count} for cat, count in category_stats
        ],
        "sources_by_category": {cat: count for cat, count in sources_by_category},
    }


@router.get("/analytics/daily")
async def get_daily_analytics(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db)
):
    """Get daily analytics for the last N days."""
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    # Get stored daily stats
    stats = db.query(DailyStats).filter(
        DailyStats.date >= start_date,
        DailyStats.date <= end_date
    ).order_by(DailyStats.date).all()

    # If no stored stats, calculate from page_views
    if not stats:
        daily_data = db.query(
            func.date(PageView.created_at).label('date'),
            func.count(PageView.id).label('views'),
            func.count(func.distinct(PageView.ip_hash)).label('unique')
        ).filter(
            func.date(PageView.created_at) >= start_date
        ).group_by(func.date(PageView.created_at)).all()

        return {
            "days": [
                {
                    "date": str(row.date),
                    "views": row.views,
                    "unique_visitors": row.unique
                }
                for row in daily_data
            ]
        }

    return {
        "days": [
            {
                "date": str(s.date),
                "views": s.total_views,
                "unique_visitors": s.unique_visitors,
                "views_en": s.views_en,
                "views_he": s.views_he,
            }
            for s in stats
        ]
    }


@router.get("/analytics/top-stories")
async def get_top_stories_analytics(
    days: int = Query(7, ge=1, le=30),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get most viewed stories."""
    start_date = datetime.now(timezone.utc) - timedelta(days=days)

    top_stories = db.query(
        PageView.story_id,
        func.count(PageView.id).label('views')
    ).filter(
        PageView.created_at >= start_date,
        PageView.story_id != None
    ).group_by(PageView.story_id).order_by(desc('views')).limit(limit).all()

    result = []
    for story_id, views in top_stories:
        story = db.query(Story).filter(Story.id == story_id).first()
        if story:
            summary = db.query(StorySummary).filter(
                StorySummary.story_id == story_id,
                StorySummary.language == 'en'
            ).first()
            result.append({
                "story_id": story_id,
                "title": summary.title if summary else f"Story #{story_id}",
                "views": views,
                "category": story.category,
                "published_at": story.published_at.isoformat()
            })

    return {"top_stories": result}


# ============ SOURCE MANAGEMENT ============

@router.get("/sources")
async def list_all_sources(
    include_inactive: bool = Query(False),
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all sources with article counts."""
    query = db.query(Source)

    if not include_inactive:
        query = query.filter(Source.is_active == True)

    if category:
        query = query.filter(Source.category == category)

    sources = query.order_by(Source.category, Source.name).all()

    result = []
    for source in sources:
        article_count = db.query(Article).filter(Article.source_id == source.id).count()
        recent_count = db.query(Article).filter(
            Article.source_id == source.id,
            Article.created_at >= datetime.now(timezone.utc) - timedelta(hours=24)
        ).count()

        result.append({
            "id": source.id,
            "name": source.name,
            "feed_url": source.feed_url,
            "language": source.language,
            "category": source.category,
            "weight": source.weight,
            "is_active": source.is_active,
            "last_fetched_at": source.last_fetched_at.isoformat() if source.last_fetched_at else None,
            "created_at": source.created_at.isoformat() if source.created_at else None,
            "article_count": article_count,
            "recent_articles_24h": recent_count,
        })

    return {"sources": result}


@router.post("/sources")
async def create_source(
    name: str,
    feed_url: str,
    category: str = "general",
    language: str = "en",
    weight: float = 1.0,
    db: Session = Depends(get_db)
):
    """Create a new RSS source."""
    existing = db.query(Source).filter(Source.feed_url == feed_url).first()
    if existing:
        raise HTTPException(status_code=400, detail="Source with this feed URL already exists")

    source = Source(
        name=name,
        feed_url=feed_url,
        category=category,
        language=language,
        weight=weight,
        is_active=True
    )
    db.add(source)
    db.commit()
    db.refresh(source)

    return {"message": "Source created", "source_id": source.id}


@router.put("/sources/{source_id}")
async def update_source(
    source_id: int,
    name: Optional[str] = None,
    feed_url: Optional[str] = None,
    category: Optional[str] = None,
    language: Optional[str] = None,
    weight: Optional[float] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Update a source."""
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    if name is not None:
        source.name = name
    if feed_url is not None:
        source.feed_url = feed_url
    if category is not None:
        source.category = category
    if language is not None:
        source.language = language
    if weight is not None:
        source.weight = weight
    if is_active is not None:
        source.is_active = is_active

    db.commit()
    return {"message": "Source updated"}


@router.delete("/sources/{source_id}")
async def delete_source(source_id: int, db: Session = Depends(get_db)):
    """Delete a source and its articles."""
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    # Delete associated articles
    db.query(Article).filter(Article.source_id == source_id).delete()
    db.delete(source)
    db.commit()

    return {"message": "Source deleted"}


# ============ CATEGORY MANAGEMENT ============

@router.get("/categories")
async def list_categories(db: Session = Depends(get_db)):
    """List all categories."""
    categories = db.query(Category).order_by(Category.sort_order).all()

    # If no categories in DB, return defaults
    if not categories:
        return {
            "categories": [
                {"slug": "all", "name_en": "All", "name_he": "הכל", "icon": "🌐", "color": "#6b7280", "sort_order": 0, "is_active": True, "locale_filter": None},
                {"slug": "israel", "name_en": "Israel", "name_he": "ישראל", "icon": "🇮🇱", "color": "#0066cc", "sort_order": 5, "is_active": True, "locale_filter": "he"},
                {"slug": "world", "name_en": "World", "name_he": "עולם", "icon": "🌍", "color": "#0ea5e9", "sort_order": 10, "is_active": True, "locale_filter": None},
                {"slug": "politics", "name_en": "Politics", "name_he": "פוליטיקה", "icon": "🏛️", "color": "#8b5cf6", "sort_order": 20, "is_active": True, "locale_filter": None},
                {"slug": "tech", "name_en": "Technology", "name_he": "טכנולוגיה", "icon": "💻", "color": "#3b82f6", "sort_order": 30, "is_active": True, "locale_filter": None},
                {"slug": "finance", "name_en": "Finance", "name_he": "כלכלה", "icon": "📈", "color": "#10b981", "sort_order": 40, "is_active": True, "locale_filter": None},
                {"slug": "crypto", "name_en": "Crypto", "name_he": "קריפטו", "icon": "₿", "color": "#f59e0b", "sort_order": 50, "is_active": True, "locale_filter": None},
                {"slug": "sports", "name_en": "Sports", "name_he": "ספורט", "icon": "⚽", "color": "#ef4444", "sort_order": 60, "is_active": True, "locale_filter": None},
                {"slug": "general", "name_en": "General", "name_he": "כללי", "icon": "📰", "color": "#6b7280", "sort_order": 100, "is_active": True, "locale_filter": None},
            ]
        }

    return {
        "categories": [
            {
                "id": c.id,
                "slug": c.slug,
                "name_en": c.name_en,
                "name_he": c.name_he,
                "icon": c.icon,
                "color": c.color,
                "sort_order": c.sort_order,
                "is_active": c.is_active,
                "locale_filter": c.locale_filter,
            }
            for c in categories
        ]
    }


@router.post("/categories")
async def create_category(
    slug: str,
    name_en: str,
    name_he: str,
    icon: str = "📰",
    color: str = "#6b7280",
    sort_order: int = 100,
    locale_filter: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Create a new category."""
    existing = db.query(Category).filter(Category.slug == slug).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category with this slug already exists")

    category = Category(
        slug=slug,
        name_en=name_en,
        name_he=name_he,
        icon=icon,
        color=color,
        sort_order=sort_order,
        locale_filter=locale_filter,
        is_active=True
    )
    db.add(category)
    db.commit()
    db.refresh(category)

    return {"message": "Category created", "category_id": category.id}


@router.put("/categories/{category_id}")
async def update_category(
    category_id: int,
    name_en: Optional[str] = None,
    name_he: Optional[str] = None,
    icon: Optional[str] = None,
    color: Optional[str] = None,
    sort_order: Optional[int] = None,
    is_active: Optional[bool] = None,
    locale_filter: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Update a category."""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    if name_en is not None:
        category.name_en = name_en
    if name_he is not None:
        category.name_he = name_he
    if icon is not None:
        category.icon = icon
    if color is not None:
        category.color = color
    if sort_order is not None:
        category.sort_order = sort_order
    if is_active is not None:
        category.is_active = is_active
    if locale_filter is not None:
        category.locale_filter = locale_filter if locale_filter != "" else None

    db.commit()
    return {"message": "Category updated"}


@router.delete("/categories/{category_id}")
async def delete_category(category_id: int, db: Session = Depends(get_db)):
    """Delete a category."""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    db.delete(category)
    db.commit()
    return {"message": "Category deleted"}


# ============ ANALYTICS TRACKING ============

@router.post("/track")
async def track_pageview(
    request: Request,
    path: str,
    locale: str = "en",
    story_id: Optional[int] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Track a page view."""
    # Hash IP for privacy
    client_ip = request.client.host if request.client else "unknown"
    ip_hash = hashlib.sha256(client_ip.encode()).hexdigest()[:16]

    user_agent = request.headers.get("user-agent", "")[:500]
    referrer = request.headers.get("referer", "")[:500]

    pageview = PageView(
        path=path[:500],
        locale=locale,
        story_id=story_id,
        category=category,
        user_agent=user_agent,
        ip_hash=ip_hash,
        referrer=referrer
    )
    db.add(pageview)
    db.commit()

    return {"status": "tracked"}


# ============ SYSTEM OPERATIONS ============

@router.post("/tasks/fetch")
async def trigger_fetch(db: Session = Depends(get_db)):
    """Manually trigger feed fetching (bypasses enabled check)."""
    from app.tasks.celery_app import celery_app
    result = celery_app.send_task('app.tasks.fetch_task.fetch_feeds', kwargs={'force': True})
    return {"message": "Fetch task triggered", "task_id": str(result.id)}


@router.post("/tasks/cluster")
async def trigger_cluster(db: Session = Depends(get_db)):
    """Manually trigger story clustering (bypasses enabled check)."""
    from app.tasks.celery_app import celery_app
    result = celery_app.send_task('app.tasks.cluster_task.cluster_stories', kwargs={'force': True})
    return {"message": "Cluster task triggered", "task_id": str(result.id)}


@router.post("/tasks/summarize")
async def trigger_summarize(db: Session = Depends(get_db)):
    """Manually trigger summary warming (bypasses enabled check)."""
    from app.tasks.celery_app import celery_app
    result = celery_app.send_task('app.tasks.summarize_task.warm_top_summaries', kwargs={'force': True})
    return {"message": "Summarize task triggered", "task_id": str(result.id)}


@router.delete("/cache/summaries")
async def clear_summaries(db: Session = Depends(get_db)):
    """Clear all cached summaries (forces regeneration)."""
    count = db.query(StorySummary).delete()
    db.commit()
    return {"message": f"Deleted {count} summaries"}


# ============ REFRESH SETTINGS ============

REFRESH_INTERVAL_KEY = "refresh_interval_minutes"
REFRESH_ENABLED_KEY = "refresh_enabled"


def get_setting(db: Session, key: str, default: str = None) -> str:
    """Get a system setting value."""
    setting = db.query(SystemSettings).filter(SystemSettings.key == key).first()
    return setting.value if setting else default


def set_setting(db: Session, key: str, value: str):
    """Set a system setting value."""
    setting = db.query(SystemSettings).filter(SystemSettings.key == key).first()
    if setting:
        setting.value = value
    else:
        setting = SystemSettings(key=key, value=value)
        db.add(setting)
    db.commit()


@router.get("/settings/refresh")
async def get_refresh_settings(db: Session = Depends(get_db)):
    """Get current refresh settings."""
    enabled = get_setting(db, REFRESH_ENABLED_KEY, "true")
    interval = get_setting(db, REFRESH_INTERVAL_KEY, "60")

    return {
        "enabled": enabled.lower() == "true",
        "interval_minutes": int(interval),
        "presets": [
            {"label": "Every minute", "value": 1},
            {"label": "Every 5 minutes", "value": 5},
            {"label": "Every 15 minutes", "value": 15},
            {"label": "Every 30 minutes", "value": 30},
            {"label": "Every hour", "value": 60},
            {"label": "Every 2 hours", "value": 120},
            {"label": "Every 6 hours", "value": 360},
            {"label": "Every 12 hours", "value": 720},
            {"label": "Once daily", "value": 1440},
        ]
    }


@router.put("/settings/refresh")
async def update_refresh_settings(
    enabled: Optional[bool] = None,
    interval_minutes: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Update refresh settings."""
    if enabled is not None:
        set_setting(db, REFRESH_ENABLED_KEY, str(enabled).lower())

    if interval_minutes is not None:
        if interval_minutes < 1:
            raise HTTPException(status_code=400, detail="Interval must be at least 1 minute")
        if interval_minutes > 10080:  # Max 1 week
            raise HTTPException(status_code=400, detail="Interval cannot exceed 10080 minutes (1 week)")
        set_setting(db, REFRESH_INTERVAL_KEY, str(interval_minutes))

    return {"message": "Refresh settings updated"}


@router.post("/tasks/refresh-now")
async def trigger_full_refresh(db: Session = Depends(get_db)):
    """Manually trigger a full refresh (fetch + cluster + summarize)."""
    from app.tasks.celery_app import celery_app

    # Trigger all three tasks in sequence
    fetch_result = celery_app.send_task('app.tasks.fetch_task.fetch_feeds')
    cluster_result = celery_app.send_task('app.tasks.cluster_task.cluster_stories')
    summarize_result = celery_app.send_task('app.tasks.summarize_task.warm_top_summaries')

    return {
        "message": "Full refresh triggered",
        "tasks": {
            "fetch": str(fetch_result.id),
            "cluster": str(cluster_result.id),
            "summarize": str(summarize_result.id)
        }
    }


# ============ STORY MANAGEMENT ============

@router.get("/stories")
async def get_all_stories(
    sort_by: str = Query("time", regex="^(time|topic|score)$"),
    order: str = Query("desc", regex="^(asc|desc)$"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    topic: Optional[str] = None,
    since: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get all stories with filtering and sorting for admin management.

    - **sort_by**: Sort field (time, topic, score)
    - **order**: Sort order (asc, desc)
    - **limit**: Maximum number of results (1-100)
    - **offset**: Pagination offset
    - **topic**: Filter by topic
    - **since**: ISO datetime to mark stories as "new" if created after this time
    """
    # Base query
    query = db.query(Story).filter(Story.is_active == True)

    # Apply topic filter
    if topic:
        query = query.filter(Story.category == topic)

    # Apply sorting
    if sort_by == "time":
        sort_field = Story.created_at
    elif sort_by == "topic":
        sort_field = Story.category
    elif sort_by == "score":
        sort_field = Story.score
    else:
        sort_field = Story.created_at

    if order == "desc":
        query = query.order_by(desc(sort_field))
    else:
        query = query.order_by(sort_field)

    # Get total count before pagination
    total = query.count()

    # Apply pagination
    stories = query.offset(offset).limit(limit).all()

    # Parse since time for marking new stories
    since_dt = None
    if since:
        try:
            since_dt = datetime.fromisoformat(since.replace('Z', '+00:00'))
        except:
            pass

    # Convert to response format
    story_list = []
    for story in stories:
        # Count articles for this story
        article_count = db.query(Article).filter(Article.story_id == story.id).count()

        # Determine if story is "new"
        is_new = False
        if since_dt and story.created_at:
            is_new = story.created_at.replace(tzinfo=timezone.utc) > since_dt.replace(tzinfo=timezone.utc)

        # Get summary for title (try Hebrew first, then English, then any)
        summary = db.query(StorySummary).filter(
            StorySummary.story_id == story.id,
            StorySummary.language == 'he'
        ).first()

        if not summary:
            summary = db.query(StorySummary).filter(
                StorySummary.story_id == story.id,
                StorySummary.language == 'en'
            ).first()

        if not summary:
            summary = db.query(StorySummary).filter(
                StorySummary.story_id == story.id
            ).first()

        # Get tags from summary if available
        story_tags = []
        if summary and summary.tags:
            try:
                import json
                story_tags = json.loads(summary.tags) if isinstance(summary.tags, str) else summary.tags
            except:
                story_tags = []

        story_data = {
            "id": story.id,
            "title": summary.title if summary else f"Story #{story.id}",
            "topic": story.category,
            "tags": story_tags[:5] if story_tags else [],
            "score": float(story.score or 0.0),
            "article_count": article_count,
            "created_at": story.created_at.isoformat() if story.created_at else None,
            "updated_at": story.updated_at.isoformat() if story.updated_at else None,
            "is_new": is_new,
        }
        story_list.append(story_data)

    return {
        "stories": story_list,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.delete("/stories/{story_id}")
async def delete_story(
    story_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a specific story and all related data.

    This will cascade delete:
    - All articles associated with the story
    - All summaries associated with the story
    """
    # Check if story exists
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    # Delete related summaries
    db.query(StorySummary).filter(StorySummary.story_id == story_id).delete()

    # Set articles' story_id to NULL (or delete if preferred)
    db.query(Article).filter(Article.story_id == story_id).update({"story_id": None})

    # Delete the story
    db.delete(story)
    db.commit()

    return {
        "success": True,
        "message": f"Story {story_id} and all related data deleted successfully",
        "story_id": story_id,
    }


@router.get("/stories/stats")
async def get_story_stats(db: Session = Depends(get_db)):
    """
    Get statistics about stories.

    Returns:
    - Total number of stories
    - Stories count by topic
    - Recent activity (stories created in last 24 hours)
    - Average articles per story
    """
    # Total stories
    total_stories = db.query(Story).filter(Story.is_active == True).count()

    # Stories by topic/category
    stories_by_topic_raw = db.query(
        Story.category,
        func.count(Story.id).label("count")
    ).filter(Story.is_active == True).group_by(Story.category).all()

    stories_by_topic = {}
    for category, count in stories_by_topic_raw:
        if category:
            stories_by_topic[category] = count

    # Recent activity (last 24 hours)
    yesterday = datetime.now(timezone.utc) - timedelta(hours=24)

    recent_stories = db.query(Story).filter(
        Story.is_active == True,
        Story.created_at >= yesterday
    ).count()

    recent_articles = db.query(Article).filter(
        Article.created_at >= yesterday
    ).count()

    # Average articles per story
    total_articles = db.query(Article).filter(Article.story_id != None).count()
    avg_articles = total_articles / total_stories if total_stories > 0 else 0.0

    return {
        "total_stories": total_stories,
        "stories_by_topic": stories_by_topic,
        "recent_activity": {
            "stories_last_24h": recent_stories,
            "articles_last_24h": recent_articles,
        },
        "avg_articles_per_story": float(avg_articles),
    }
