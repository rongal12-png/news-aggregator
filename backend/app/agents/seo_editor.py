"""SEO optimization agent for story metadata."""

import json
import logging
import re
from dataclasses import dataclass
from typing import List

from openai import AsyncOpenAI

from .base import BaseAgent
from ..agent_config.agents import AGENT_CONFIGS, LLM_CONFIG, SEO_CONFIG
from ..models.story import Story
from ..config import settings

logger = logging.getLogger(__name__)


@dataclass
class SEOMetadata:
    """SEO-optimized metadata for a story.

    Attributes:
        meta_description: Meta description tag content (up to 160 chars)
        og_title: Open Graph title (up to 60 chars)
        og_description: Open Graph description (up to 200 chars)
        og_image: Open Graph image URL (optional)
        seo_keywords: List of SEO keywords (3-6 keywords)
    """
    meta_description: str
    og_title: str
    og_description: str
    og_image: str | None
    seo_keywords: List[str]


@dataclass
class SEOEditorInput:
    """Input for SEO editor agent."""
    story: Story
    summary_title: str
    summary_bullets: List[str]
    language: str = "en"


@dataclass
class SEOEditorOutput:
    """Output from SEO editor agent."""
    metadata: SEOMetadata


class SEOEditorAgent(BaseAgent[SEOEditorInput, SEOEditorOutput]):
    """Agent that generates SEO-optimized metadata for stories.

    Generates:
    - Meta description tags
    - Open Graph (OG) tags for social sharing
    - SEO keywords for search optimization
    - Optimized titles for click-through rate

    All content is optimized for length, readability, and engagement.
    """

    def __init__(self):
        """Initialize the SEO editor agent."""
        config = AGENT_CONFIGS.get('seo_editor')
        super().__init__(config=config)

        # Initialize OpenAI client for DeepSeek
        self.client = AsyncOpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,
        )
        self.model = settings.DEEPSEEK_MODEL or LLM_CONFIG['model']
        self.temperature = LLM_CONFIG['temperature']

        # Get optimal lengths from config
        self.meta_desc_length = SEO_CONFIG.get('meta_description_length', 160)
        self.og_title_length = SEO_CONFIG.get('og_title_length', 60)
        self.og_desc_length = SEO_CONFIG.get('og_description_length', 200)

    @property
    def agent_name(self) -> str:
        return "SEOEditorAgent"

    async def _execute(self, input_data: SEOEditorInput) -> SEOEditorOutput:
        """Generate SEO metadata for a story.

        Args:
            input_data: Story and summary information

        Returns:
            SEO-optimized metadata
        """
        # Format story details for prompt
        story_text = self._format_story_for_prompt(input_data)

        # Determine language instruction
        lang_instruction = "in Hebrew" if input_data.language == "he" else "in English"

        prompt = f"""Generate SEO-optimized metadata for this news story {lang_instruction}.

Story Information:
{story_text}

Generate the following SEO metadata:

1. META DESCRIPTION (max {self.meta_desc_length} chars):
   - Concise summary of the story
   - Include key facts and numbers
   - Compelling and click-worthy
   - Natural language, not keyword stuffing

2. OPEN GRAPH TITLE (max {self.og_title_length} chars):
   - Engaging headline for social media
   - Include key information
   - Action-oriented when appropriate
   - Different from meta description

3. OPEN GRAPH DESCRIPTION (max {self.og_desc_length} chars):
   - Expanded description for social sharing
   - Include context and significance
   - Encourage clicks and shares
   - More detailed than meta description

4. SEO KEYWORDS (3-6 keywords):
   - Single words or short phrases
   - Relevant to the story content
   - Include entity names, topics, locations
   - Mix of broad and specific terms

Respond with JSON:
{{
  "meta_description": "...",
  "og_title": "...",
  "og_description": "...",
  "seo_keywords": ["keyword1", "keyword2", ...]
}}

Important:
- Respect the character limits strictly
- Write compelling, natural-sounding copy
- Optimize for both search engines and human readers
- Include numbers, names, and specific details when available
"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                max_tokens=1500,
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

            result = json.loads(content)

            # Truncate if necessary (safety check)
            meta_description = result['meta_description'][:self.meta_desc_length]
            og_title = result['og_title'][:self.og_title_length]
            og_description = result['og_description'][:self.og_desc_length]

            metadata = SEOMetadata(
                meta_description=meta_description,
                og_title=og_title,
                og_description=og_description,
                og_image=None,  # Image selection handled separately
                seo_keywords=result['seo_keywords'][:6]  # Max 6 keywords
            )

            return SEOEditorOutput(metadata=metadata)

        except Exception as e:
            self._logger.error(f"Error generating SEO metadata: {e}")
            # Fallback to basic metadata
            return self._generate_fallback_metadata(input_data)

    def _format_story_for_prompt(self, input_data: SEOEditorInput) -> str:
        """Format story information for the LLM prompt.

        Args:
            input_data: Story input data

        Returns:
            Formatted string with story details
        """
        bullets_text = "\n".join(f"- {bullet}" for bullet in input_data.summary_bullets)

        return f"""Title: {input_data.summary_title}

Summary:
{bullets_text}

Source Count: {input_data.story.article_count}
Published: {input_data.story.published_at.strftime('%Y-%m-%d %H:%M')}
Category: {input_data.story.category or 'General'}
"""

    def _generate_fallback_metadata(self, input_data: SEOEditorInput) -> SEOEditorOutput:
        """Generate basic fallback metadata if LLM fails.

        Args:
            input_data: Story input data

        Returns:
            Basic SEO metadata
        """
        # Use summary title and first bullet as fallback
        title = input_data.summary_title
        first_bullet = input_data.summary_bullets[0] if input_data.summary_bullets else ""

        # Truncate to limits
        meta_description = f"{title}. {first_bullet}"[:self.meta_desc_length]
        og_title = title[:self.og_title_length]
        og_description = f"{title}. {first_bullet}"[:self.og_desc_length]

        # Extract basic keywords from title
        words = re.findall(r'\b\w+\b', title.lower())
        keywords = [w for w in words if len(w) > 4][:5]

        metadata = SEOMetadata(
            meta_description=meta_description,
            og_title=og_title,
            og_description=og_description,
            og_image=None,
            seo_keywords=keywords
        )

        return SEOEditorOutput(metadata=metadata)

    async def validate_input(self, input_data: SEOEditorInput) -> None:
        """Validate input data.

        Args:
            input_data: Input to validate

        Raises:
            ValueError: If input is invalid
        """
        if not input_data.story:
            raise ValueError("Story is required")

        if not input_data.summary_title:
            raise ValueError("Summary title is required")

        if not input_data.summary_bullets:
            raise ValueError("Summary bullets are required")

        if input_data.language not in ['en', 'he']:
            raise ValueError(f"Invalid language: {input_data.language}")

    async def validate_output(self, output_data: SEOEditorOutput) -> None:
        """Validate output metadata.

        Args:
            output_data: Output to validate

        Raises:
            ValueError: If output is invalid
        """
        metadata = output_data.metadata

        # Check required fields
        if not metadata.meta_description:
            raise ValueError("Meta description is required")

        if not metadata.og_title:
            raise ValueError("OG title is required")

        if not metadata.og_description:
            raise ValueError("OG description is required")

        # Check lengths
        if len(metadata.meta_description) > self.meta_desc_length:
            raise ValueError(
                f"Meta description too long: {len(metadata.meta_description)} > {self.meta_desc_length}"
            )

        if len(metadata.og_title) > self.og_title_length:
            raise ValueError(
                f"OG title too long: {len(metadata.og_title)} > {self.og_title_length}"
            )

        if len(metadata.og_description) > self.og_desc_length:
            raise ValueError(
                f"OG description too long: {len(metadata.og_description)} > {self.og_desc_length}"
            )

        # Check keywords
        if not metadata.seo_keywords:
            raise ValueError("SEO keywords are required")

        if len(metadata.seo_keywords) > 6:
            raise ValueError(
                f"Too many SEO keywords: {len(metadata.seo_keywords)} > 6"
            )
