"""Article filtering agent to identify newsworthy content."""

import json
import logging
from dataclasses import dataclass
from typing import List

from openai import AsyncOpenAI

from .base import BaseAgent, AgentResult
from ..agent_config.agents import AGENT_CONFIGS, LLM_CONFIG
from ..models.article import Article
from ..config import settings

logger = logging.getLogger(__name__)


@dataclass
class FilteredArticle:
    """Result of article filtering.

    Attributes:
        article: The original article
        is_newsworthy: Whether the article is newsworthy
        importance_score: Importance score (0.0-1.0)
        filter_reason: Reason for filtering (if filtered)
    """
    article: Article
    is_newsworthy: bool
    importance_score: float
    filter_reason: str | None = None


@dataclass
class ArticleFilterInput:
    """Input data for article filtering."""
    articles: List[Article]


@dataclass
class ArticleFilterOutput:
    """Output data from article filtering."""
    filtered_articles: List[FilteredArticle]
    filtered_count: int
    passed_count: int


class ArticleFilterAgent(BaseAgent[ArticleFilterInput, ArticleFilterOutput]):
    """Agent that filters articles based on newsworthiness.

    Uses LLM to classify articles as:
    - Newsworthy: Breaking news, major events, significant updates
    - Not newsworthy: Opinion pieces, minor updates, non-significant content

    Each article receives an importance score (0.0-1.0) and filter reason if rejected.
    """

    def __init__(self):
        """Initialize the article filter agent."""
        config = AGENT_CONFIGS.get('article_filter')
        super().__init__(config=config)

        # Initialize OpenAI client for DeepSeek
        self.client = AsyncOpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,
        )
        self.model = settings.DEEPSEEK_MODEL or LLM_CONFIG['model']
        self.temperature = LLM_CONFIG['temperature']
        self.importance_threshold = 0.6

    @property
    def agent_name(self) -> str:
        return "ArticleFilterAgent"

    async def _execute(self, input_data: ArticleFilterInput) -> ArticleFilterOutput:
        """Filter articles based on newsworthiness.

        Args:
            input_data: Articles to filter

        Returns:
            FilteredArticles with importance scores and reasons
        """
        filtered_articles = []

        # Process articles in batches for efficiency
        batch_size = 10
        for i in range(0, len(input_data.articles), batch_size):
            batch = input_data.articles[i:i + batch_size]
            batch_results = await self._filter_batch(batch)
            filtered_articles.extend(batch_results)

        # Count filtered vs passed
        passed_count = sum(1 for fa in filtered_articles if fa.is_newsworthy)
        filtered_count = len(filtered_articles) - passed_count

        return ArticleFilterOutput(
            filtered_articles=filtered_articles,
            filtered_count=filtered_count,
            passed_count=passed_count
        )

    async def _filter_batch(self, articles: List[Article]) -> List[FilteredArticle]:
        """Filter a batch of articles using Claude.

        Args:
            articles: Batch of articles to filter

        Returns:
            List of filtered article results
        """
        # Build prompt with article details
        articles_text = self._format_articles_for_prompt(articles)

        prompt = f"""Analyze these news articles and classify each one as newsworthy or not newsworthy.

NEWSWORTHY articles include:
- Breaking news or developing stories
- Major events with significant impact
- Important political, economic, or social developments
- Scientific breakthroughs or technological innovations
- Natural disasters or emergencies
- Major business deals or market movements

NOT NEWSWORTHY articles include:
- Opinion pieces or editorials
- Minor updates or routine events
- Celebrity gossip or entertainment news (unless major)
- Promotional content or advertisements
- Duplicate coverage of minor stories
- Trivial or unimportant updates

Articles to analyze:
{articles_text}

For each article, respond with a JSON object containing:
{{
  "results": [
    {{
      "index": 0,
      "is_newsworthy": true/false,
      "importance_score": 0.0-1.0,
      "reason": "Brief explanation (if filtered)"
    }},
    ...
  ]
}}

Importance score scale:
- 0.9-1.0: Breaking news, major events
- 0.7-0.9: Significant news
- 0.5-0.7: Moderate importance
- 0.3-0.5: Minor news
- 0.0-0.3: Not newsworthy
"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                max_tokens=2000,
                temperature=self.temperature,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Parse response
            content = response.choices[0].message.content

            # Extract JSON from response (handle markdown code blocks)
            if "```json" in content:
                json_start = content.index("```json") + 7
                json_end = content.rindex("```")
                content = content[json_start:json_end].strip()
            elif "```" in content:
                json_start = content.index("```") + 3
                json_end = content.rindex("```")
                content = content[json_start:json_end].strip()

            results = json.loads(content)

            # Map results back to articles
            filtered_articles = []
            for idx, article in enumerate(articles):
                result = results['results'][idx]

                is_newsworthy = (
                    result['is_newsworthy'] and
                    result['importance_score'] >= self.importance_threshold
                )

                filtered_articles.append(FilteredArticle(
                    article=article,
                    is_newsworthy=is_newsworthy,
                    importance_score=result['importance_score'],
                    filter_reason=result.get('reason') if not is_newsworthy else None
                ))

            return filtered_articles

        except Exception as e:
            self._logger.error(f"Error filtering batch: {e}")
            # On error, mark all as newsworthy to avoid losing content
            return [
                FilteredArticle(
                    article=article,
                    is_newsworthy=True,
                    importance_score=0.5,
                    filter_reason=None
                )
                for article in articles
            ]

    def _format_articles_for_prompt(self, articles: List[Article]) -> str:
        """Format articles for the LLM prompt.

        Args:
            articles: Articles to format

        Returns:
            Formatted string with article details
        """
        formatted = []
        for idx, article in enumerate(articles):
            formatted.append(
                f"[{idx}] Title: {article.title}\n"
                f"    Snippet: {article.snippet or 'N/A'}\n"
                f"    Source: {article.source.name if article.source else 'Unknown'}"
            )
        return "\n\n".join(formatted)

    async def validate_input(self, input_data: ArticleFilterInput) -> None:
        """Validate input articles.

        Args:
            input_data: Input to validate

        Raises:
            ValueError: If input is invalid
        """
        if not input_data.articles:
            raise ValueError("No articles provided for filtering")

        if len(input_data.articles) > 100:
            raise ValueError(
                f"Too many articles ({len(input_data.articles)}). "
                f"Maximum is 100 per batch."
            )

    async def validate_output(self, output_data: ArticleFilterOutput) -> None:
        """Validate output results.

        Args:
            output_data: Output to validate

        Raises:
            ValueError: If output is invalid
        """
        if not output_data.filtered_articles:
            raise ValueError("No filtered articles in output")

        # Verify all scores are in valid range
        for fa in output_data.filtered_articles:
            if not (0.0 <= fa.importance_score <= 1.0):
                raise ValueError(
                    f"Invalid importance score: {fa.importance_score}. "
                    f"Must be between 0.0 and 1.0"
                )
