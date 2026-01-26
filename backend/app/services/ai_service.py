import json
import re
from typing import Optional
import httpx

from app.config import settings
from app.models import Story, StorySummary


# Different summary modes with tailored prompts
SUMMARY_PROMPTS = {
    'standard': """You are a professional news editor. Summarize this news story based on the following articles.

Articles:
{articles_text}

Create a JSON summary with:
1. "title": A clear, factual headline (50-80 characters)
2. "bullets": Array of 2-4 key points. Each bullet should:
   - Be a complete, informative sentence
   - Cover a different aspect of the story
   - Be 60-120 characters long
   - Focus on facts, not opinions
3. "tags": Array of 3-5 relevant single-word tags (lowercase)

Rules:
- Extract multiple distinct facts from the articles
- Each bullet must provide NEW information
- NO speculation or invented details
- Neutral journalistic tone

Return ONLY valid JSON:
{{
  "title": "Headline here",
  "bullets": ["First key point.", "Second key point.", "Third key point."],
  "tags": ["tag1", "tag2", "tag3"]
}}""",

    'tldr': """You are a news summarizer creating ultra-brief summaries for busy readers.

Articles:
{articles_text}

Create a JSON summary with:
1. "title": One-sentence headline (max 15 words, captures the essence)
2. "bullets": Array with just ONE bullet - the single most important takeaway
3. "tags": Array of 2-3 tags (lowercase)

Rules:
- Be extremely concise
- Focus only on the absolute core message
- No fluff or secondary details
- Perfect for quick scanning

Return ONLY valid JSON:
{{
  "title": "Brief headline",
  "bullets": ["The key takeaway."],
  "tags": ["tag1", "tag2"]
}}""",

    'delta': """You are a news editor tracking developing stories and highlighting what's NEW.

Articles:
{articles_text}

Create a JSON summary focused on WHAT'S NEW:
1. "title": Headline emphasizing the latest development or update
2. "bullets": Array of 2-3 points about:
   - What changed recently
   - New information revealed
   - Latest reactions or developments
3. "tags": Array of 3-4 tags including "update" or "developing"

Rules:
- Focus on what's new, not background
- Use language like "now", "latest", "newly"
- Highlight changes from previous coverage
- Perfect for following a developing story

Return ONLY valid JSON:
{{
  "title": "Latest update headline",
  "bullets": ["What's new now.", "Another recent development."],
  "tags": ["update", "tag1", "tag2"]
}}""",

    'forward': """You are a forward-looking analyst summarizing news with an eye on implications.

Articles:
{articles_text}

Create a JSON summary focused on WHAT'S NEXT:
1. "title": Headline about implications or what to watch
2. "bullets": Array of 2-3 points about:
   - What this means going forward
   - What to watch for next
   - Potential implications or outcomes
3. "tags": Array of 3-4 tags including trend indicators

Rules:
- Focus on implications, not just facts
- Use forward-looking language
- Highlight trends and patterns
- Perfect for strategic planning

Return ONLY valid JSON:
{{
  "title": "Forward-looking headline",
  "bullets": ["What this means...", "What to watch for..."],
  "tags": ["trend", "outlook", "tag1"]
}}"""
}


TRANSLATE_PROMPT = """You are a professional Hebrew translator for a news website.
Translate this news summary to fluent, natural Hebrew.

English Title: {title}

English Bullets:
{bullets}

Tags: {tags}

IMPORTANT REQUIREMENTS:
1. Translate the title to natural Hebrew - it must sound like a real Hebrew news headline
2. Translate ALL bullets to fluent Hebrew - each bullet must be a complete Hebrew sentence
3. Keep tags in English (unchanged)
4. Use proper Hebrew grammar, punctuation, and news style
5. The translation should read naturally to a native Hebrew speaker

Return ONLY valid JSON with Hebrew text:
{{
  "title": "כותרת חדשותית בעברית",
  "bullets": ["נקודה ראשונה בעברית מלאה.", "נקודה שנייה בעברית מלאה.", "נקודה שלישית בעברית מלאה."],
  "tags": ["tag1", "tag2", "tag3"]
}}"""


class AIService:
    def __init__(self):
        # Use DeepSeek API
        self.api_key = settings.DEEPSEEK_API_KEY
        self.base_url = settings.DEEPSEEK_BASE_URL or "https://api.deepseek.com"
        self.model = settings.DEEPSEEK_MODEL or "deepseek-chat"

    async def _call_llm(self, messages: list, max_tokens: int = 500, temperature: float = 0.3) -> Optional[str]:
        """Make a direct HTTP call to DeepSeek API (OpenAI-compatible)."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=data
                )

                if response.status_code == 200:
                    result = response.json()
                    content = result["choices"][0]["message"]["content"]
                    # Extract JSON from potential markdown code blocks
                    if "```json" in content:
                        json_start = content.index("```json") + 7
                        json_end = content.rindex("```")
                        content = content[json_start:json_end].strip()
                    elif "```" in content:
                        json_start = content.index("```") + 3
                        json_end = content.rindex("```")
                        content = content[json_start:json_end].strip()
                    return content
                else:
                    print(f"DeepSeek API error {response.status_code}: {response.text[:200]}")
                    return None

        except Exception as e:
            print(f"DeepSeek API call failed: {type(e).__name__}: {e}")
            return None

    async def generate_summary(
        self,
        story: Story,
        mode: str = 'standard'
    ) -> Optional[dict]:
        """
        Generate a summary for a story using the LLM.

        Args:
            story: The Story object to summarize
            mode: Summary mode - 'standard', 'tldr', 'delta', 'forward'

        Returns dict with title, bullets, tags or None on failure.
        """
        articles = story.articles[:10]  # Limit to 10 articles

        if not articles:
            return None

        # Build articles text
        articles_text = "\n".join([
            f"- {a.title}\n  {a.snippet or ''}"
            for a in articles
        ])

        # Get appropriate prompt for mode
        prompt_template = SUMMARY_PROMPTS.get(mode, SUMMARY_PROMPTS['standard'])
        prompt = prompt_template.format(articles_text=articles_text)

        content = await self._call_llm(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.3
        )

        if not content:
            return None

        try:
            data = json.loads(content)

            # Validate and clean response - ensure appropriate bullet count for mode
            bullets = [str(b).strip()[:200] for b in data.get("bullets", []) if str(b).strip()]

            # Mode-specific bullet validation
            if mode == 'tldr':
                bullets = bullets[:1] if bullets else ["Key point pending."]
            else:
                # Ensure we have at least 2 bullets, max 4 for other modes
                if len(bullets) < 2:
                    if bullets and len(bullets[0]) > 100:
                        parts = bullets[0].split('. ')
                        bullets = [p.strip() + '.' for p in parts if p.strip()][:4]

                bullets = bullets[:4] if bullets else ["Story details pending."]

            return {
                "title": str(data.get("title", "")).strip()[:100],
                "bullets": bullets,
                "tags": [str(t).lower().strip()[:30] for t in data.get("tags", []) if str(t).strip()][:5],
            }

        except json.JSONDecodeError as e:
            print(f"Failed to parse AI response: {e}")
            return None

    async def translate_summary(
        self,
        title: str,
        bullets: list[str],
        tags: list[str],
        target_lang: str = "he"
    ) -> Optional[dict]:
        """
        Translate an existing summary to another language.
        """
        if target_lang != "he":
            # Only Hebrew translation supported for now
            return None

        bullets_text = "\n".join([f"- {b}" for b in bullets])

        prompt = TRANSLATE_PROMPT.format(
            title=title,
            bullets=bullets_text,
            tags=", ".join(tags)
        )

        content = await self._call_llm(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
            temperature=0.4
        )

        if not content:
            return None

        try:
            data = json.loads(content)

            translated_title = str(data.get("title", "")).strip()
            translated_bullets = [str(b).strip()[:300] for b in data.get("bullets", []) if str(b).strip()]

            # Verify we got actual Hebrew (contains Hebrew characters)
            has_hebrew = any('\u0590' <= c <= '\u05FF' for c in translated_title)

            if not has_hebrew:
                print(f"Translation failed - no Hebrew in title: {translated_title}")
                return None

            return {
                "title": translated_title[:500],
                "bullets": translated_bullets[:5] if translated_bullets else [translated_title],
                "tags": [str(t).strip()[:50] for t in data.get("tags", tags)][:6],
            }

        except json.JSONDecodeError as e:
            print(f"Failed to parse translation response: {e}")
            return None


def create_fallback_summary(story: Story, mode: str = 'standard') -> dict:
    """
    Create a deterministic fallback summary when AI fails.
    """
    articles = story.articles

    if not articles:
        return {
            "title": "News Story",
            "bullets": ["No details available."],
            "tags": ["news"],
        }

    top_article = articles[0]

    # Extract keywords from title for tags
    words = re.findall(r"\b[A-Za-z]{4,}\b", top_article.title)
    tags = list(set(w.lower() for w in words[:6]))

    # Mode-specific adjustments
    if mode == 'tldr':
        return {
            "title": top_article.title[:80],
            "bullets": [top_article.snippet[:100] if top_article.snippet else top_article.title[:100]],
            "tags": tags[:3] or ["news"],
        }
    elif mode == 'delta':
        tags = ["update"] + tags[:4]
        return {
            "title": f"Update: {top_article.title[:75]}",
            "bullets": [top_article.snippet[:200]] if top_article.snippet else [top_article.title],
            "tags": tags,
        }
    elif mode == 'forward':
        tags = ["outlook"] + tags[:4]
        return {
            "title": f"Analysis: {top_article.title[:75]}",
            "bullets": [top_article.snippet[:200]] if top_article.snippet else [top_article.title],
            "tags": tags,
        }

    return {
        "title": top_article.title[:100],
        "bullets": [top_article.snippet[:200]] if top_article.snippet else [top_article.title],
        "tags": tags or ["news"],
    }
