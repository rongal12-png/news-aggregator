from sqlalchemy.orm import Session

from app.models import Story, StorySummary
from app.services.ai_service import AIService, create_fallback_summary


async def get_or_create_summary(
    db: Session,
    story: Story,
    language: str = "en",
    mode: str = "standard"
) -> StorySummary:
    """
    Get an existing summary or create one (lazy generation).

    Args:
        db: Database session
        story: Story object to get/create summary for
        language: Language code ('en', 'he')
        mode: Summary mode ('standard', 'tldr', 'delta', 'forward')
    """
    # Check for existing summary with this mode
    summary = (
        db.query(StorySummary)
        .filter(
            StorySummary.story_id == story.id,
            StorySummary.language == language,
            StorySummary.mode == mode,
        )
        .first()
    )

    if summary:
        return summary

    # If requesting non-English, first ensure English exists for this mode
    if language != "en":
        en_summary = await get_or_create_summary(db, story, "en", mode)
        summary = await _create_translated_summary(db, story, en_summary, language, mode)
    else:
        summary = await _create_summary(db, story, language, mode)

    return summary


async def _create_summary(
    db: Session,
    story: Story,
    language: str,
    mode: str = "standard"
) -> StorySummary:
    """
    Create a new summary for a story using AI or fallback.
    """
    ai_service = AIService()

    # Try AI generation with specified mode
    result = await ai_service.generate_summary(story, mode=mode)

    if not result:
        # Use fallback with mode
        result = create_fallback_summary(story, mode=mode)

    summary = StorySummary(
        story_id=story.id,
        language=language,
        mode=mode,
        title=result["title"],
        bullets=result["bullets"],
        tags=result["tags"],
    )

    db.add(summary)
    db.commit()
    db.refresh(summary)

    return summary


async def _create_translated_summary(
    db: Session,
    story: Story,
    en_summary: StorySummary,
    target_lang: str,
    mode: str = "standard"
) -> StorySummary:
    """
    Create a translated summary from the English version.
    """
    ai_service = AIService()

    # Try AI translation
    result = await ai_service.translate_summary(
        title=en_summary.title,
        bullets=en_summary.bullets,
        tags=en_summary.tags,
        target_lang=target_lang,
    )

    if not result:
        # Use English as fallback
        result = {
            "title": en_summary.title,
            "bullets": en_summary.bullets,
            "tags": en_summary.tags,
        }

    summary = StorySummary(
        story_id=story.id,
        language=target_lang,
        mode=mode,
        title=result["title"],
        bullets=result["bullets"],
        tags=result["tags"],
    )

    db.add(summary)
    db.commit()
    db.refresh(summary)

    return summary
