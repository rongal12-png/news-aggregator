from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy.orm import Session

from app.models import Article, Story
from app.config import settings


class ClusterService:
    def __init__(self, db: Session):
        self.db = db
        self.max_age_hours = settings.STORY_MAX_AGE_HOURS

    def get_unclustered_articles(self) -> list[Article]:
        """
        Get articles that haven't been assigned to a story yet.
        Only considers articles from the last 48 hours.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=self.max_age_hours)

        return (
            self.db.query(Article)
            .filter(
                Article.story_id == None,
                Article.published_at >= cutoff,
                Article.normalized_key != None,
                Article.normalized_key != "",
                Article.is_filtered != True,  # Skip filtered articles
            )
            .order_by(Article.published_at.desc())
            .all()
        )

    def find_story_by_key(self, normalized_key: str) -> Optional[Story]:
        """
        Find an existing story with the same cluster key.
        """
        if not normalized_key:
            return None

        return (
            self.db.query(Story)
            .filter(
                Story.cluster_key == normalized_key,
                Story.is_active == True,
            )
            .first()
        )

    def create_story(self, cluster_key: str, published_at: datetime, category: str = "general") -> Story:
        """
        Create a new story cluster.
        """
        story = Story(
            cluster_key=cluster_key,
            published_at=published_at,
            score=0.0,
            article_count=0,
            is_active=True,
            category=category,
        )
        self.db.add(story)
        self.db.flush()
        return story

    def link_article_to_story(self, article: Article, story: Story) -> None:
        """
        Link an article to a story and update story metadata.
        """
        article.story_id = story.id

        # Update story's earliest published date
        if article.published_at < story.published_at:
            story.published_at = article.published_at

        # Update article count
        story.article_count = (
            self.db.query(Article)
            .filter(Article.story_id == story.id)
            .count()
        ) + 1  # +1 for the current article being added

    def cluster_articles(self) -> int:
        """
        Main clustering logic. Returns number of articles clustered.
        """
        articles = self.get_unclustered_articles()
        clustered_count = 0

        for article in articles:
            if not article.normalized_key:
                continue

            # Find existing story or create new one
            story = self.find_story_by_key(article.normalized_key)

            if story:
                self.link_article_to_story(article, story)
            else:
                # Get category from the article's source
                category = article.source.category if article.source else "general"
                story = self.create_story(
                    cluster_key=article.normalized_key,
                    published_at=article.published_at,
                    category=category,
                )
                self.link_article_to_story(article, story)

            clustered_count += 1

        self.db.commit()
        return clustered_count
