"""Agent pipeline service for story processing."""

import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.agents import (
    ArticleFilterAgent,
    ArticleFilterInput,
    SEOEditorAgent,
    SEOEditorInput,
    CountryDetectorAgent,
    CountryDetectorInput,
)
from app.models import Article, Story, StorySummary
from app.config import settings

logger = logging.getLogger(__name__)


class PipelineService:
    """Service that orchestrates all agent-based processing.

    Pipeline flow:
    1. ArticleFilterAgent: Filter out non-newsworthy articles
    2. ClusteringAgent: Group articles into stories
    3. SummarizerAgent: Generate story summaries
    4. SEOEditorAgent: Generate SEO metadata
    5. CountryDetectorAgent: Detect country context
    """

    def __init__(self, db: Session):
        """Initialize the pipeline service.

        Args:
            db: Database session
        """
        self.db = db

        # Initialize agents (they get API key from settings)
        try:
            self.article_filter = ArticleFilterAgent()
            self.seo_editor = SEOEditorAgent()
            self.country_detector = CountryDetectorAgent()
        except Exception as e:
            logger.error(f"Error initializing agents: {e}")
            raise

    async def filter_articles(self, articles: List[Article]) -> Dict[str, Any]:
        """Filter articles using ArticleFilterAgent.

        Args:
            articles: Articles to filter

        Returns:
            Dictionary with filtering results
        """
        if not articles:
            return {
                "filtered_count": 0,
                "passed_count": 0,
                "filtered_articles": [],
            }

        try:
            # Run article filter agent
            input_data = ArticleFilterInput(articles=articles)
            result = await self.article_filter.process(input_data)

            if not result.is_success:
                logger.error(f"Article filtering failed: {result.error}")
                # Return all articles as passed on error
                return {
                    "filtered_count": 0,
                    "passed_count": len(articles),
                    "error": result.error,
                }

            # Update articles in database with filter results
            for filtered_article in result.data.filtered_articles:
                article = filtered_article.article
                article.is_filtered = not filtered_article.is_newsworthy
                article.filter_reason = filtered_article.filter_reason
                article.importance_score = filtered_article.importance_score

            self.db.commit()

            return {
                "filtered_count": result.data.filtered_count,
                "passed_count": result.data.passed_count,
                "execution_time": result.execution_time,
            }

        except Exception as e:
            logger.error(f"Error in article filtering: {e}")
            self.db.rollback()
            return {
                "filtered_count": 0,
                "passed_count": len(articles),
                "error": str(e),
            }

    async def enhance_story_seo(
        self,
        story: Story,
        summary: StorySummary,
        language: str = "en"
    ) -> Dict[str, Any]:
        """Enhance story with SEO metadata using SEOEditorAgent.

        Args:
            story: Story to enhance
            summary: Story summary with title and bullets
            language: Language code

        Returns:
            Dictionary with SEO enhancement results
        """
        try:
            # Run SEO editor agent
            input_data = SEOEditorInput(
                story=story,
                summary_title=summary.title,
                summary_bullets=summary.bullets,
                language=language
            )
            result = await self.seo_editor.process(input_data)

            if not result.is_success:
                logger.error(f"SEO generation failed for story {story.id}: {result.error}")
                return {
                    "success": False,
                    "error": result.error,
                }

            # Update story with SEO metadata
            metadata = result.data.metadata
            story.meta_description = metadata.meta_description
            story.og_title = metadata.og_title
            story.og_description = metadata.og_description
            story.og_image = metadata.og_image
            story.seo_keywords = metadata.seo_keywords

            self.db.commit()

            return {
                "success": True,
                "execution_time": result.execution_time,
                "metadata": {
                    "meta_description": metadata.meta_description,
                    "og_title": metadata.og_title,
                    "seo_keywords": metadata.seo_keywords,
                }
            }

        except Exception as e:
            logger.error(f"Error enhancing story SEO: {e}")
            self.db.rollback()
            return {
                "success": False,
                "error": str(e),
            }

    async def detect_story_country(
        self,
        story: Story,
        summary: StorySummary
    ) -> Dict[str, Any]:
        """Detect country context using CountryDetectorAgent.

        Args:
            story: Story to analyze
            summary: Story summary with title and bullets

        Returns:
            Dictionary with country detection results
        """
        try:
            # Run country detector agent
            input_data = CountryDetectorInput(
                story=story,
                summary_title=summary.title,
                summary_bullets=summary.bullets
            )
            result = await self.country_detector.process(input_data)

            if not result.is_success:
                logger.error(f"Country detection failed for story {story.id}: {result.error}")
                return {
                    "success": False,
                    "error": result.error,
                }

            # Update story with country info
            detection = result.data.detection
            story.country_code = detection.country_code

            self.db.commit()

            return {
                "success": True,
                "execution_time": result.execution_time,
                "country_code": detection.country_code,
                "country_name": detection.country_name,
                "confidence": detection.confidence,
            }

        except Exception as e:
            logger.error(f"Error detecting story country: {e}")
            self.db.rollback()
            return {
                "success": False,
                "error": str(e),
            }

    async def enhance_story(
        self,
        story: Story,
        language: str = "en"
    ) -> Dict[str, Any]:
        """Run full enhancement pipeline on a story.

        Args:
            story: Story to enhance
            language: Language for SEO content

        Returns:
            Dictionary with enhancement results
        """
        results = {
            "story_id": story.id,
            "seo": None,
            "country": None,
        }

        try:
            # Get story summary
            summary = (
                self.db.query(StorySummary)
                .filter(
                    StorySummary.story_id == story.id,
                    StorySummary.language == language
                )
                .first()
            )

            if not summary:
                logger.warning(f"No summary found for story {story.id} in {language}")
                return results

            # Run SEO enhancement
            seo_result = await self.enhance_story_seo(story, summary, language)
            results["seo"] = seo_result

            # Run country detection
            country_result = await self.detect_story_country(story, summary)
            results["country"] = country_result

            return results

        except Exception as e:
            logger.error(f"Error in story enhancement pipeline: {e}")
            results["error"] = str(e)
            return results

    async def enhance_multiple_stories(
        self,
        stories: List[Story],
        language: str = "en"
    ) -> Dict[str, Any]:
        """Enhance multiple stories with SEO and country detection.

        Args:
            stories: Stories to enhance
            language: Language for SEO content

        Returns:
            Summary of enhancement results
        """
        enhanced_count = 0
        errors = 0
        seo_success = 0
        country_detected = 0

        for story in stories:
            try:
                result = await self.enhance_story(story, language)

                if result.get("seo", {}).get("success"):
                    seo_success += 1

                if result.get("country", {}).get("country_code"):
                    country_detected += 1

                enhanced_count += 1

            except Exception as e:
                logger.error(f"Error enhancing story {story.id}: {e}")
                errors += 1
                continue

        return {
            "total_stories": len(stories),
            "enhanced_count": enhanced_count,
            "seo_success": seo_success,
            "countries_detected": country_detected,
            "errors": errors,
        }
