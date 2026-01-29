import asyncio
import logging

from celery import shared_task

from app.db import SessionLocal
from app.services.cluster_service import ClusterService
from app.services.scoring_service import ScoringService

logger = logging.getLogger(__name__)


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
        cluster_service = ClusterService(db)

        # Step 1: Filter articles for newsworthiness before clustering
        filtered_count = 0
        try:
            from app.services.pipeline_service import PipelineService
            from app.models import Article

            # Get unfiltered, unclustered articles that haven't been evaluated yet
            unfiltered = (
                db.query(Article)
                .filter(
                    Article.story_id == None,
                    Article.is_filtered == False,
                    Article.importance_score == None,
                )
                .all()
            )

            if unfiltered:
                pipeline = PipelineService(db)
                result = asyncio.run(pipeline.filter_articles(unfiltered))
                filtered_count = result.get("filtered_count", 0)
                logger.info(
                    f"Article filter: {result.get('passed_count', 0)} passed, "
                    f"{filtered_count} filtered"
                )

        except Exception as e:
            logger.error(f"Article filtering failed (continuing without filter): {e}")

        # Step 2: Cluster articles (only non-filtered ones)
        clustered_count = cluster_service.cluster_articles()

        # Step 3: Update all story scores
        scoring_service = ScoringService(db)
        stories_updated = scoring_service.update_all_scores()

        return {
            "status": "completed",
            "articles_filtered": filtered_count,
            "articles_clustered": clustered_count,
            "stories_scored": stories_updated,
        }

    finally:
        db.close()
