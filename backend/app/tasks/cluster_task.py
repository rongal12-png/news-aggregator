from celery import shared_task

from app.db import SessionLocal
from app.services.cluster_service import ClusterService
from app.services.scoring_service import ScoringService


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
def cluster_stories(self, force: bool = False):
    """
    Cluster unclustered articles into stories and update scores.
    Runs via Celery Beat based on configured interval.
    Set force=True to bypass the enabled check (for manual triggers).
    """
    # Check if refresh is enabled (skip check for manual triggers)
    if not force and not is_refresh_enabled():
        return {"status": "skipped", "reason": "refresh_disabled"}

    db = SessionLocal()

    try:
        # Cluster articles
        cluster_service = ClusterService(db)
        clustered_count = cluster_service.cluster_articles()

        # Update all story scores
        scoring_service = ScoringService(db)
        stories_updated = scoring_service.update_all_scores()

        return {
            "status": "completed",
            "articles_clustered": clustered_count,
            "stories_scored": stories_updated,
        }

    finally:
        db.close()
