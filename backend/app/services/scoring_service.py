from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session

from app.models import Story, Article


# Minimum thresholds for story quality
MIN_SOURCES_FOR_DISPLAY = 2  # Story must have at least 2 sources to be shown
MIN_SCORE_THRESHOLD = 1.5    # Minimum score to be considered relevant


@dataclass
class ScoreBreakdown:
    """Breakdown of score components for explainability."""
    source_count: int
    weight_sum: float
    freshness: float
    breaking_bonus: float
    diversity_bonus: float
    coverage_bonus: float
    authority_bonus: float
    final_score: float

    def to_dict(self) -> dict:
        """Convert to dictionary for JSONB storage."""
        return asdict(self)


class ScoringService:
    def __init__(self, db: Session):
        self.db = db

    def calculate_score(self, story: Story, return_breakdown: bool = False) -> float | ScoreBreakdown:
        """
        Calculate a story's importance score based on:
        - Number of unique sources covering the story (heavily weighted)
        - Sum of source weights (authority)
        - Freshness (time decay)
        - Breaking news detection (many sources in short time)
        - Diversity bonus (sources from different categories)
        - Quality bonuses for multi-source coverage
        """
        articles = (
            self.db.query(Article)
            .filter(Article.story_id == story.id)
            .all()
        )

        if not articles:
            if return_breakdown:
                return ScoreBreakdown(
                    source_count=0, weight_sum=0.0, freshness=0.0,
                    breaking_bonus=0.0, diversity_bonus=0.0,
                    coverage_bonus=0.0, authority_bonus=0.0, final_score=0.0
                )
            return 0.0

        # Count unique sources and calculate weight
        source_ids = set()
        weight_sum = 0.0
        categories = set()
        article_times = []

        for article in articles:
            if article.source_id not in source_ids:
                source_ids.add(article.source_id)
                if article.source:
                    weight_sum += article.source.weight
                    categories.add(article.source.category)
            if article.created_at:
                article_times.append(article.created_at)

        source_count = len(source_ids)

        # Stories with only 1 source get penalized heavily
        if source_count < MIN_SOURCES_FOR_DISPLAY:
            if return_breakdown:
                return ScoreBreakdown(
                    source_count=source_count, weight_sum=weight_sum, freshness=0.1,
                    breaking_bonus=0.0, diversity_bonus=0.0,
                    coverage_bonus=0.0, authority_bonus=0.0, final_score=0.1
                )
            return 0.1  # Very low score, won't show up in top stories

        # Calculate freshness decay - faster decay for older stories
        now = datetime.now(timezone.utc)
        if story.published_at.tzinfo is None:
            age = now - story.published_at.replace(tzinfo=timezone.utc)
        else:
            age = now - story.published_at

        age_hours = age.total_seconds() / 3600

        # Faster decay: stories lose relevance quicker
        freshness = 1.0 / (1.0 + (age_hours / 12.0) ** 1.2)

        # Breaking news detection: many sources in short time
        breaking_bonus = 0.0
        if len(article_times) >= 3:
            # Make times timezone-aware if needed
            aware_times = []
            for t in article_times:
                if t.tzinfo is None:
                    aware_times.append(t.replace(tzinfo=timezone.utc))
                else:
                    aware_times.append(t)

            time_span = (max(aware_times) - min(aware_times)).total_seconds() / 3600
            if time_span < 2 and source_count >= 3:
                breaking_bonus = 1.5
            elif time_span < 4 and source_count >= 4:
                breaking_bonus = 1.0

        # Diversity bonus: sources from different categories
        diversity_bonus = 0.3 * (len(categories) - 1) if len(categories) > 1 else 0.0

        # Multi-source bonus: exponentially rewards stories covered by many sources
        coverage_bonus = 1.0 + (source_count - 1) * 0.5  # +50% per additional source

        # Authority bonus for high-weight sources
        authority_bonus = weight_sum / max(source_count, 1)

        # Calculate final score
        # Base: source_count * 3 (heavily weight source coverage)
        # Plus: weight_sum (source authority)
        # Multiplied by: freshness and coverage bonus
        base_score = (source_count * 3.0 + weight_sum + authority_bonus + breaking_bonus + diversity_bonus)
        final_score = round(base_score * freshness * coverage_bonus, 4)

        if return_breakdown:
            return ScoreBreakdown(
                source_count=source_count,
                weight_sum=round(weight_sum, 2),
                freshness=round(freshness, 4),
                breaking_bonus=breaking_bonus,
                diversity_bonus=round(diversity_bonus, 2),
                coverage_bonus=round(coverage_bonus, 2),
                authority_bonus=round(authority_bonus, 2),
                final_score=final_score
            )

        return final_score

    def update_story_score(self, story: Story) -> None:
        """
        Update a story's score, score_factors, and article count.
        """
        breakdown = self.calculate_score(story, return_breakdown=True)
        story.score = breakdown.final_score
        story.score_factors = breakdown.to_dict()
        story.article_count = (
            self.db.query(Article)
            .filter(Article.story_id == story.id)
            .count()
        )

    def update_all_scores(self) -> int:
        """
        Update scores for all active stories.
        Returns number of stories updated.
        """
        stories = (
            self.db.query(Story)
            .filter(Story.is_active == True)
            .all()
        )

        for story in stories:
            self.update_story_score(story)

        self.db.commit()
        return len(stories)
