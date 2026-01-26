import asyncio
from celery import shared_task

from app.db import SessionLocal
from app.models import Story, StorySummary
from app.services.summary_service import get_or_create_summary
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
def warm_top_summaries(self, force: bool = False):
    """
    Pre-generate summaries for top stories.
    Runs via Celery Beat based on configured interval.
    Set force=True to bypass the enabled check (for manual triggers).
    """
    # Check if refresh is enabled (skip check for manual triggers)
    if not force and not is_refresh_enabled():
        return {"status": "skipped", "reason": "refresh_disabled"}

    db = SessionLocal()

    try:
        # Get top stories that need summaries
        top_stories = (
            db.query(Story)
            .filter(Story.is_active == True)
            .order_by(Story.score.desc())
            .limit(settings.TOP_STORIES_LIMIT)
            .all()
        )

        summaries_created = 0
        errors = 0

        for story in top_stories:
            try:
                # Generate English summary
                en_exists = (
                    db.query(StorySummary)
                    .filter(
                        StorySummary.story_id == story.id,
                        StorySummary.language == "en",
                    )
                    .first()
                )

                if not en_exists:
                    asyncio.run(_generate_summary(db, story, "en"))
                    summaries_created += 1

                # Generate Hebrew summary
                he_exists = (
                    db.query(StorySummary)
                    .filter(
                        StorySummary.story_id == story.id,
                        StorySummary.language == "he",
                    )
                    .first()
                )

                if not he_exists:
                    asyncio.run(_generate_summary(db, story, "he"))
                    summaries_created += 1

            except Exception as e:
                errors += 1
                db.rollback()
                continue

        return {
            "status": "completed",
            "stories_processed": len(top_stories),
            "summaries_created": summaries_created,
            "errors": errors,
        }

    finally:
        db.close()


async def _generate_summary(db, story: Story, language: str):
    """
    Helper to generate a summary asynchronously.
    """
    await get_or_create_summary(db, story, language)
