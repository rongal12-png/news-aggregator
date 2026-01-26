from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any, List

from .article import ArticleResponse


class ScoreBreakdown(BaseModel):
    """Score component breakdown for explainability."""
    source_count: int
    weight_sum: float
    freshness: float
    breaking_bonus: float
    diversity_bonus: float
    coverage_bonus: float
    authority_bonus: float
    final_score: float


class StoryExplanation(BaseModel):
    """Explanation of why a story is shown."""
    score_breakdown: Dict[str, Any]
    matching_preferences: List[str]
    tags_involved: List[str]
    sources_involved: List[str]
    why_text: str
    why_text_he: str


class StoryResponse(BaseModel):
    id: int
    title: str
    bullets: list[str]
    tags: list[str]
    source_count: int
    sources: list[str]
    category: str
    published_at: datetime
    # Optional explainability fields
    score_factors: Optional[Dict[str, Any]] = None
    explanation: Optional[StoryExplanation] = None

    class Config:
        from_attributes = True


class StoryDetailResponse(BaseModel):
    id: int
    title: str
    bullets: list[str]
    tags: list[str]
    articles: list[ArticleResponse]
    category: str
    published_at: datetime
    # Optional explainability fields
    score_factors: Optional[Dict[str, Any]] = None
    explanation: Optional[StoryExplanation] = None

    class Config:
        from_attributes = True
