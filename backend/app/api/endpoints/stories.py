from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from typing import Optional

from app.db import get_db
from app.models import Story, StorySummary, Article, Source, Category
from app.schemas import StoryResponse, StoryDetailResponse, ArticleResponse
from app.schemas.story import StoryExplanation
from app.services.summary_service import get_or_create_summary
from app.services.scoring_service import MIN_SOURCES_FOR_DISPLAY, MIN_SCORE_THRESHOLD
from app.services.explainability_service import ExplainabilityService

router = APIRouter()

# Default categories (used if DB is empty)
DEFAULT_CATEGORIES = [
    {"id": "all", "name": "All", "name_he": "הכל", "icon": "🌐", "color": "#6b7280", "locale_filter": None},
    {"id": "israel", "name": "Israel", "name_he": "ישראל", "icon": "🇮🇱", "color": "#0066cc", "locale_filter": "he"},
    {"id": "world", "name": "World", "name_he": "עולם", "icon": "🌍", "color": "#0ea5e9", "locale_filter": None},
    {"id": "politics", "name": "Politics", "name_he": "פוליטיקה", "icon": "🏛️", "color": "#8b5cf6", "locale_filter": None},
    {"id": "tech", "name": "Technology", "name_he": "טכנולוגיה", "icon": "💻", "color": "#3b82f6", "locale_filter": None},
    {"id": "finance", "name": "Finance", "name_he": "כלכלה", "icon": "📈", "color": "#10b981", "locale_filter": None},
    {"id": "crypto", "name": "Crypto", "name_he": "קריפטו", "icon": "₿", "color": "#f59e0b", "locale_filter": None},
    {"id": "sports", "name": "Sports", "name_he": "ספורט", "icon": "⚽", "color": "#ef4444", "locale_filter": None},
    {"id": "general", "name": "General", "name_he": "כללי", "icon": "📰", "color": "#6b7280", "locale_filter": None},
]


@router.get("/categories")
async def get_categories(
    lang: str = Query("en", pattern="^(en|he)$"),
    db: Session = Depends(get_db)
):
    """Return list of available categories, filtered by locale."""
    # Try to get from DB
    db_categories = db.query(Category).filter(Category.is_active == True).order_by(Category.sort_order).all()

    if db_categories:
        categories = []
        for c in db_categories:
            # Filter by locale if specified
            if c.locale_filter and c.locale_filter != lang:
                continue
            categories.append({
                "id": c.slug,
                "name": c.name_en,
                "name_he": c.name_he,
                "icon": c.icon,
                "color": c.color,
                "locale_filter": c.locale_filter,
            })
        return {"categories": categories}

    # Use defaults, filtering by locale
    categories = []
    for c in DEFAULT_CATEGORIES:
        if c["locale_filter"] and c["locale_filter"] != lang:
            continue
        categories.append({
            "id": c["id"],
            "name": c["name"],
            "name_he": c["name_he"],
            "icon": c["icon"],
            "color": c.get("color", "#6b7280"),
            "locale_filter": c["locale_filter"],
        })
    return {"categories": categories}


@router.get("/top", response_model=list[StoryResponse])
async def get_top_stories(
    lang: str = Query("en", pattern="^(en|he)$"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0, description="Number of stories to skip for pagination"),
    category: Optional[str] = Query(None, description="Filter by category: tech, crypto, general"),
    # New filtering parameters
    tags: Optional[str] = Query(None, description="Comma-separated tags to include"),
    exclude_tags: Optional[str] = Query(None, description="Comma-separated tags to exclude"),
    sources: Optional[str] = Query(None, description="Comma-separated source names to filter by"),
    # Summary mode
    summary_mode: str = Query("standard", pattern="^(standard|tldr|delta|forward)$"),
    # Explainability
    include_explanation: bool = Query(False, description="Include explanation of why stories are shown"),
    db: Session = Depends(get_db)
):
    """
    Get top stories with optional filtering.

    Filters:
    - category: Filter by story category
    - tags: Include only stories with any of these tags (comma-separated)
    - exclude_tags: Exclude stories with any of these tags (comma-separated)
    - sources: Include only stories from these sources (comma-separated)

    Options:
    - summary_mode: 'standard', 'tldr', 'delta', 'forward'
    - include_explanation: Add explainability data to response
    """
    query = (
        db.query(Story)
        .filter(Story.is_active == True)
        # Only show stories with minimum quality thresholds
        .filter(Story.article_count >= MIN_SOURCES_FOR_DISPLAY)
        .filter(Story.score >= MIN_SCORE_THRESHOLD)
    )

    # Filter by category if specified
    if category and category != "all":
        if category == "israel":
            # Israel category: match by country_code OR source category
            query = query.filter(
                or_(
                    Story.country_code == 'IL',
                    Story.category == 'israel'
                )
            )
        else:
            query = query.filter(Story.category == category)

    # Fetch extra stories if we need to filter by tags/sources (post-filtering)
    fetch_limit = limit * 2 if (tags or exclude_tags or sources) else limit

    stories = (
        query
        .order_by(Story.score.desc())
        .offset(offset)
        .limit(fetch_limit)
        .options(joinedload(Story.articles).joinedload(Article.source))
        .all()
    )

    # Initialize explainability service if needed
    explainability_service = ExplainabilityService() if include_explanation else None

    # Parse filter lists
    tag_list = [t.strip().lower() for t in tags.split(',')] if tags else None
    exclude_tag_list = [t.strip().lower() for t in exclude_tags.split(',')] if exclude_tags else None
    source_list = [s.strip().lower() for s in sources.split(',')] if sources else None

    result = []
    for story in stories:
        if len(result) >= limit:
            break

        summary = await get_or_create_summary(db, story, lang, mode=summary_mode)
        story_tags = [t.lower() for t in summary.tags]
        story_sources = list(set(a.source.name.lower() for a in story.articles[:10] if a.source))

        # Apply tag filters
        if tag_list:
            if not any(t in story_tags for t in tag_list):
                continue

        if exclude_tag_list:
            if any(t in story_tags for t in exclude_tag_list):
                continue

        # Apply source filter
        if source_list:
            if not any(s in story_sources for s in source_list):
                continue

        # Build response
        sources_display = list(set(a.source.name for a in story.articles[:5]))

        response_data = {
            "id": story.id,
            "title": summary.title,
            "bullets": summary.bullets,
            "tags": summary.tags,
            "source_count": story.article_count,
            "sources": sources_display,
            "category": story.category,
            "published_at": story.published_at,
        }

        # Add explainability if requested
        if include_explanation and explainability_service:
            explanation = explainability_service.explain_story(
                story,
                summary_tags=summary.tags,
                language=lang
            )
            response_data["score_factors"] = story.score_factors
            response_data["explanation"] = StoryExplanation(
                score_breakdown=explanation.score_breakdown,
                matching_preferences=explanation.matching_preferences,
                tags_involved=explanation.tags_involved,
                sources_involved=explanation.sources_involved,
                why_text=explanation.why_text,
                why_text_he=explanation.why_text_he
            )

        result.append(StoryResponse(**response_data))

    return result


@router.get("/{story_id}", response_model=StoryDetailResponse)
async def get_story(
    story_id: int,
    lang: str = Query("en", pattern="^(en|he)$"),
    summary_mode: str = Query("standard", pattern="^(standard|tldr|delta|forward)$"),
    include_explanation: bool = Query(False),
    db: Session = Depends(get_db)
):
    story = (
        db.query(Story)
        .filter(Story.id == story_id)
        .options(joinedload(Story.articles).joinedload(Article.source))
        .first()
    )

    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    summary = await get_or_create_summary(db, story, lang, mode=summary_mode)

    articles = [
        ArticleResponse(
            id=a.id,
            title=a.title,
            url=a.url,
            source=a.source.name,
            published_at=a.published_at
        )
        for a in sorted(story.articles, key=lambda x: x.published_at, reverse=True)
    ]

    response_data = {
        "id": story.id,
        "title": summary.title,
        "bullets": summary.bullets,
        "tags": summary.tags,
        "articles": articles,
        "category": story.category,
        "published_at": story.published_at,
    }

    # Add explainability if requested
    if include_explanation:
        explainability_service = ExplainabilityService()
        explanation = explainability_service.explain_story(
            story,
            summary_tags=summary.tags,
            language=lang
        )
        response_data["score_factors"] = story.score_factors
        response_data["explanation"] = StoryExplanation(
            score_breakdown=explanation.score_breakdown,
            matching_preferences=explanation.matching_preferences,
            tags_involved=explanation.tags_involved,
            sources_involved=explanation.sources_involved,
            why_text=explanation.why_text,
            why_text_he=explanation.why_text_he
        )

    return StoryDetailResponse(**response_data)
