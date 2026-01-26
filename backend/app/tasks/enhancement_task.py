"""Story enhancement task using agent pipeline."""

import asyncio
from celery import shared_task

from app.db import SessionLocal
from app.models import Story, StorySummary
from app.services.pipeline_service import PipelineService
from app.config import settings


def is_refresh_enabled() -> bool:
    """Check if auto-refresh is enabled in system settings."""
    from app.models import SystemSettings
    db = SessionLocal()
    try:
        setting = db.query(SystemSettings).filter(SystemSettings.key == "refresh_enabled").first()
        return setting.value.lower() != "false" if setting else True
    finally:
        db.close()


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    max_retries=3,
)
def enhance_top_stories(self, force: bool = False, language: str = "en"):
    """
    Enhance top stories with SEO metadata and country detection.
    Runs via Celery Beat after summarization.
    Set force=True to bypass the enabled check (for manual triggers).

    Args:
        force: Force execution even if refresh is disabled
        language: Language for SEO content (en or he)
    """
    # Check if refresh is enabled (skip check for manual triggers)
    if not force and not is_refresh_enabled():
        return {"status": "skipped", "reason": "refresh_disabled"}

    db = SessionLocal()

    try:
        # Get top stories that have summaries but no SEO metadata
        top_stories = (
            db.query(Story)
            .join(StorySummary, Story.id == StorySummary.story_id)
            .filter(
                Story.is_active == True,
                StorySummary.language == language,
                Story.meta_description == None,  # No SEO metadata yet
            )
            .order_by(Story.score.desc())
            .limit(settings.TOP_STORIES_LIMIT)
            .all()
        )

        if not top_stories:
            return {
                "status": "completed",
                "stories_enhanced": 0,
                "message": "No stories need enhancement"
            }

        # Run enhancement pipeline
        pipeline = PipelineService(db)
        result = asyncio.run(
            pipeline.enhance_multiple_stories(top_stories, language)
        )

        return {
            "status": "completed",
            **result
        }

    finally:
        db.close()


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    max_retries=3,
)
def enhance_story(self, story_id: int, language: str = "en"):
    """
    Enhance a single story with SEO and country detection.
    Can be triggered manually for specific stories.

    Args:
        story_id: ID of story to enhance
        language: Language for SEO content (en or he)
    """
    db = SessionLocal()

    try:
        # Get story
        story = db.query(Story).filter(Story.id == story_id).first()

        if not story:
            return {
                "status": "error",
                "error": f"Story {story_id} not found"
            }

        # Check if summary exists
        summary = (
            db.query(StorySummary)
            .filter(
                StorySummary.story_id == story_id,
                StorySummary.language == language
            )
            .first()
        )

        if not summary:
            return {
                "status": "error",
                "error": f"No {language} summary found for story {story_id}"
            }

        # Run enhancement pipeline
        pipeline = PipelineService(db)
        result = asyncio.run(
            pipeline.enhance_story(story, language)
        )

        return {
            "status": "completed",
            **result
        }

    finally:
        db.close()
