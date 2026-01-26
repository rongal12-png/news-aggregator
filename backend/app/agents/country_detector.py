"""Country detection agent for geographic context."""

import json
import logging
from dataclasses import dataclass
from typing import List, Optional

from openai import AsyncOpenAI

from .base import BaseAgent
from ..agent_config.agents import AGENT_CONFIGS, COUNTRY_DETECTOR_CONFIG, LLM_CONFIG
from ..models.story import Story
from ..config import settings

logger = logging.getLogger(__name__)


@dataclass
class CountryDetection:
    """Result of country detection.

    Attributes:
        country_code: ISO 3166-1 alpha-2 country code (e.g., 'US', 'GB', 'IL')
        country_name: Full country name
        confidence: Confidence score (0.0-1.0)
        reason: Brief explanation of detection
    """
    country_code: str | None
    country_name: str | None
    confidence: float
    reason: str


@dataclass
class CountryDetectorInput:
    """Input for country detector agent."""
    story: Story
    summary_title: str
    summary_bullets: List[str]


@dataclass
class CountryDetectorOutput:
    """Output from country detector agent."""
    detection: CountryDetection


class CountryDetectorAgent(BaseAgent[CountryDetectorInput, CountryDetectorOutput]):
    """Agent that detects which country a news story is primarily about.

    Uses LLM to analyze story content and identify:
    - Primary country mentioned
    - Geographic context
    - Confidence level of detection

    Returns ISO 3166-1 alpha-2 country codes for flag display.
    """

    # Common country code mappings for validation
    COUNTRY_CODES = {
        'US', 'GB', 'IL', 'FR', 'DE', 'CA', 'AU', 'JP', 'CN', 'RU',
        'IN', 'BR', 'MX', 'IT', 'ES', 'KR', 'NL', 'SE', 'NO', 'DK',
        'FI', 'PL', 'UA', 'TR', 'SA', 'AE', 'EG', 'ZA', 'NG', 'KE',
        'AR', 'CL', 'CO', 'PE', 'VE', 'SG', 'MY', 'TH', 'ID', 'PH',
        'VN', 'NZ', 'IE', 'CH', 'AT', 'BE', 'PT', 'GR', 'CZ', 'HU',
        'RO', 'BG', 'HR', 'RS', 'SK', 'SI', 'LT', 'LV', 'EE', 'IS'
    }

    def __init__(self):
        """Initialize the country detector agent."""
        config = AGENT_CONFIGS.get('country_detector')
        super().__init__(config=config)

        # Initialize OpenAI client for DeepSeek
        self.client = AsyncOpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,
        )
        self.model = settings.DEEPSEEK_MODEL or LLM_CONFIG['model']
        self.temperature = LLM_CONFIG['temperature']
        self.confidence_threshold = COUNTRY_DETECTOR_CONFIG.get('confidence_threshold', 0.5)

    @property
    def agent_name(self) -> str:
        return "CountryDetectorAgent"

    async def _execute(self, input_data: CountryDetectorInput) -> CountryDetectorOutput:
        """Detect the primary country for a story.

        Args:
            input_data: Story and summary information

        Returns:
            Country detection with code and confidence
        """
        # Format story details for prompt
        story_text = self._format_story_for_prompt(input_data)

        prompt = f"""Analyze this news story and determine which country it is primarily about.

Story Information:
{story_text}

Identify:
1. The PRIMARY country this story is about
2. Your confidence level (0.0-1.0)
3. Brief reason for your determination

Guidelines:
- If the story is about a specific country's domestic affairs, that's the primary country
- If the story involves multiple countries, choose the most central one
- If the story is about international/global events with no clear country focus, return null
- Use ISO 3166-1 alpha-2 country codes (2 letters, e.g., 'US', 'GB', 'IL', 'FR')
- Confidence should be:
  - 0.9-1.0: Story clearly about one specific country
  - 0.7-0.9: Story primarily about one country but mentions others
  - 0.5-0.7: Story somewhat focused on a country
  - Below 0.5: International or unclear focus

Respond with JSON:
{{
  "country_code": "US" or null,
  "country_name": "United States" or null,
  "confidence": 0.85,
  "reason": "Story about US presidential election"
}}

Examples:
- "Biden announces new climate policy" → {{"country_code": "US", "country_name": "United States", "confidence": 0.95}}
- "UK and France sign trade deal" → {{"country_code": "GB", "country_name": "United Kingdom", "confidence": 0.7}}
- "Global markets react to tech sell-off" → {{"country_code": null, "country_name": null, "confidence": 0.3}}
- "Netanyahu addresses Israeli parliament" → {{"country_code": "IL", "country_name": "Israel", "confidence": 0.95}}
"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                max_tokens=500,
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

            # Validate country code
            country_code = result.get('country_code')
            if country_code and country_code.upper() not in self.COUNTRY_CODES:
                self._logger.warning(
                    f"Unknown country code: {country_code}. "
                    f"Accepting anyway."
                )

            # Normalize country code to uppercase
            if country_code:
                country_code = country_code.upper()

            # Check confidence threshold
            confidence = float(result['confidence'])
            if confidence < self.confidence_threshold:
                # Low confidence, don't assign country
                country_code = None
                country_name = None

            detection = CountryDetection(
                country_code=country_code,
                country_name=result.get('country_name'),
                confidence=confidence,
                reason=result['reason']
            )

            return CountryDetectorOutput(detection=detection)

        except Exception as e:
            self._logger.error(f"Error detecting country: {e}")
            # Return no country on error
            return CountryDetectorOutput(
                detection=CountryDetection(
                    country_code=None,
                    country_name=None,
                    confidence=0.0,
                    reason=f"Error during detection: {str(e)}"
                )
            )

    def _format_story_for_prompt(self, input_data: CountryDetectorInput) -> str:
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

Category: {input_data.story.category or 'General'}
"""

    async def validate_input(self, input_data: CountryDetectorInput) -> None:
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

    async def validate_output(self, output_data: CountryDetectorOutput) -> None:
        """Validate output detection.

        Args:
            output_data: Output to validate

        Raises:
            ValueError: If output is invalid
        """
        detection = output_data.detection

        # Check confidence range
        if not (0.0 <= detection.confidence <= 1.0):
            raise ValueError(
                f"Invalid confidence: {detection.confidence}. "
                f"Must be between 0.0 and 1.0"
            )

        # If country code is set, validate format
        if detection.country_code:
            if len(detection.country_code) != 2:
                raise ValueError(
                    f"Invalid country code: {detection.country_code}. "
                    f"Must be 2-letter ISO code"
                )

            if not detection.country_code.isupper():
                raise ValueError(
                    f"Country code must be uppercase: {detection.country_code}"
                )

        # If country code is set, country name should be set too
        if detection.country_code and not detection.country_name:
            raise ValueError(
                "Country name is required when country code is set"
            )
