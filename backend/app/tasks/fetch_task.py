from datetime import datetime, timezone
from celery import shared_task

from app.db import SessionLocal
from app.models import Source, Article
from app.services.feed_service import FeedService


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
def fetch_feeds(self, force: bool = False):
    """
    Fetch all active RSS feeds and store new articles.
    Runs via Celery Beat based on configured interval.
    Set force=True to bypass the enabled check (for manual triggers).
    """
    # Check if refresh is enabled (skip check for manual triggers)
    if not force and not is_refresh_enabled():
        return {"status": "skipped", "reason": "refresh_disabled"}

    db = SessionLocal()
    feed_service = FeedService()

    try:
        sources = db.query(Source).filter(Source.is_active == True).all()

        total_new = 0
        errors = 0

        for source in sources:
            try:
                new_count = _fetch_source(db, feed_service, source)
                total_new += new_count

                # Update last fetched timestamp
                source.last_fetched_at = datetime.now(timezone.utc)
                db.commit()

            except Exception as e:
                errors += 1
                db.rollback()
                # In production, log the error
                continue

        return {
            "status": "completed",
            "sources_processed": len(sources),
            "new_articles": total_new,
            "errors": errors,
        }

    finally:
        db.close()


def _fetch_source(db, feed_service: FeedService, source: Source) -> int:
    """
    Fetch a single source and return count of new articles.
    """
    entries = feed_service.parse_feed(source.feed_url)
    new_count = 0

    for entry in entries:
        # Check if article already exists
        existing = (
            db.query(Article)
            .filter(
                Article.source_id == source.id,
                Article.url_hash == entry.url_hash,
            )
            .first()
        )

        if existing:
            continue

        # Create new article
        article = Article(
            source_id=source.id,
            title=entry.title,
            url=entry.url,
            url_hash=entry.url_hash,
            snippet=entry.snippet,
            published_at=entry.published_at,
            normalized_key=entry.normalized_key,
        )

        db.add(article)
        new_count += 1

    db.commit()
    return new_count
