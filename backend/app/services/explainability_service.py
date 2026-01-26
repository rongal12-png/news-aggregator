from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any

from app.models import Story


@dataclass
class StoryExplanation:
    """Explanation of why a story is shown and how it was ranked."""
    score_breakdown: Dict[str, Any]
    matching_preferences: List[str]
    tags_involved: List[str]
    sources_involved: List[str]
    why_text: str
    why_text_he: str

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class ExplainabilityService:
    """Service for generating human-readable explanations of story rankings."""

    def explain_story(
        self,
        story: Story,
        summary_tags: Optional[List[str]] = None,
        user_preferences: Optional[Dict[str, Any]] = None,
        language: str = 'en'
    ) -> StoryExplanation:
        """
        Generate an explanation for why a story appears and how it's ranked.

        Args:
            story: The Story object to explain
            summary_tags: Tags from the story's summary
            user_preferences: Optional user preferences dict with keys like
                             'preferred_tags', 'blocked_sources', etc.
            language: Language for the explanation text

        Returns:
            StoryExplanation object with breakdown and text
        """
        factors = story.score_factors or {}
        reasons_en = []
        reasons_he = []

        # Breaking news detection
        if factors.get('breaking_bonus', 0) > 0:
            reasons_en.append("Breaking: Multiple sources reported rapidly")
            reasons_he.append("חדשות עכשיו: מקורות רבים דיווחו במהירות")

        # High source count
        source_count = factors.get('source_count', 0)
        if source_count >= 5:
            reasons_en.append(f"Trending: Covered by {source_count} sources")
            reasons_he.append(f"טרנדי: מכוסה על ידי {source_count} מקורות")
        elif source_count >= 3:
            reasons_en.append(f"Multi-source: {source_count} sources reporting")
            reasons_he.append(f"רב-מקורי: {source_count} מקורות מדווחים")

        # Diversity bonus
        if factors.get('diversity_bonus', 0) > 0:
            reasons_en.append("Cross-topic: Sources from multiple categories")
            reasons_he.append("חוצה קטגוריות: מקורות ממספר תחומים")

        # High freshness
        freshness = factors.get('freshness', 0)
        if freshness > 0.8:
            reasons_en.append("Very recent: Published in the last few hours")
            reasons_he.append("עדכני מאוד: פורסם בשעות האחרונות")
        elif freshness > 0.5:
            reasons_en.append("Recent: Fresh story from today")
            reasons_he.append("עדכני: סיפור חדש מהיום")

        # User preferences matching
        if user_preferences:
            preferred_tags = user_preferences.get('preferred_tags', [])
            if summary_tags and preferred_tags:
                matching_tags = set(summary_tags) & set(preferred_tags)
                if matching_tags:
                    tags_str = ', '.join(matching_tags)
                    reasons_en.append(f"Matches your interests: {tags_str}")
                    reasons_he.append(f"מתאים לתחומי העניין שלך: {tags_str}")

        # Default reason if none apply
        if not reasons_en:
            reasons_en.append("Highly covered story")
            reasons_he.append("סיפור עם כיסוי נרחב")

        # Get source names
        sources = []
        if story.articles:
            for article in story.articles[:5]:
                if article.source and article.source.name not in sources:
                    sources.append(article.source.name)

        # Build why text
        why_text_en = " | ".join(reasons_en)
        why_text_he = " | ".join(reasons_he)

        return StoryExplanation(
            score_breakdown=factors,
            matching_preferences=reasons_en if language == 'en' else reasons_he,
            tags_involved=summary_tags or [],
            sources_involved=sources,
            why_text=why_text_en if language == 'en' else why_text_he,
            why_text_he=why_text_he
        )

    def explain_score_component(
        self,
        component: str,
        value: float,
        language: str = 'en'
    ) -> str:
        """
        Get a human-readable explanation for a specific score component.

        Args:
            component: Name of the score component
            value: The component's value
            language: Language for the explanation

        Returns:
            Human-readable explanation string
        """
        explanations = {
            'source_count': {
                'en': f"{int(value)} different sources are covering this story",
                'he': f"{int(value)} מקורות שונים מכסים את הסיפור הזה"
            },
            'weight_sum': {
                'en': f"Combined authority score of {value:.1f} from source weights",
                'he': f"ציון סמכות משולב של {value:.1f} ממשקלי המקורות"
            },
            'freshness': {
                'en': f"Freshness factor: {value:.0%} (higher = more recent)",
                'he': f"מקדם עדכניות: {value:.0%} (גבוה יותר = יותר עדכני)"
            },
            'breaking_bonus': {
                'en': "Breaking news bonus applied" if value > 0 else "No breaking news bonus",
                'he': "בונוס חדשות עכשיו הוחל" if value > 0 else "ללא בונוס חדשות עכשיו"
            },
            'diversity_bonus': {
                'en': f"Cross-category diversity bonus: +{value:.1f}" if value > 0 else "Single category coverage",
                'he': f"בונוס גיוון חוצה קטגוריות: +{value:.1f}" if value > 0 else "כיסוי קטגוריה בודדת"
            },
            'coverage_bonus': {
                'en': f"Multi-source coverage multiplier: {value:.1f}x",
                'he': f"מכפיל כיסוי רב-מקורי: {value:.1f}x"
            },
            'authority_bonus': {
                'en': f"Average source authority: {value:.2f}",
                'he': f"סמכות מקור ממוצעת: {value:.2f}"
            },
            'final_score': {
                'en': f"Final ranking score: {value:.2f}",
                'he': f"ציון דירוג סופי: {value:.2f}"
            }
        }

        component_exp = explanations.get(component, {})
        return component_exp.get(language, f"{component}: {value}")

    def get_score_breakdown_text(
        self,
        factors: Dict[str, Any],
        language: str = 'en'
    ) -> List[str]:
        """
        Get a list of human-readable explanations for all score components.

        Args:
            factors: Dictionary of score factors
            language: Language for explanations

        Returns:
            List of explanation strings
        """
        breakdown = []
        for component, value in factors.items():
            if isinstance(value, (int, float)):
                breakdown.append(self.explain_score_component(component, value, language))
        return breakdown
