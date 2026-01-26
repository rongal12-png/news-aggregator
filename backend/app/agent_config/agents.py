"""Configuration for all agent-based pipeline components."""

from ..agents.base import AgentConfig

# Central configuration for all pipeline agents
AGENT_CONFIGS = {
    # Article Filter Agent
    'article_filter': AgentConfig(
        max_retries=2,
        timeout=60.0,
        skip_on_error=False,  # Critical for quality
        retry_delay=2.0,
        log_input=False,
        log_output=True,
    ),

    # Clustering Agent
    'clustering': AgentConfig(
        max_retries=3,
        timeout=180.0,
        skip_on_error=False,  # Critical for story creation
        retry_delay=3.0,
        log_input=False,
        log_output=True,
    ),

    # Summarizer Agent
    'summarizer': AgentConfig(
        max_retries=3,
        timeout=120.0,
        skip_on_error=False,  # Important for UX
        retry_delay=2.0,
        log_input=False,
        log_output=False,
    ),

    # SEO Editor Agent
    'seo_editor': AgentConfig(
        max_retries=2,
        timeout=60.0,
        skip_on_error=True,  # Non-critical enhancement
        retry_delay=1.0,
        log_input=False,
        log_output=False,
    ),

    # Country Detector Agent
    'country_detector': AgentConfig(
        max_retries=2,
        timeout=30.0,
        skip_on_error=True,  # Non-critical, continue without flag
        retry_delay=1.0,
        log_input=False,
        log_output=False,
    ),

    # Publisher Agent
    'publisher': AgentConfig(
        max_retries=2,
        timeout=30.0,
        skip_on_error=False,  # Critical for publication
        retry_delay=1.0,
        log_input=False,
        log_output=True,
    ),
}

# DeepSeek API Configuration
LLM_CONFIG = {
    'model': 'deepseek-chat',  # DeepSeek's main chat model
    'max_tokens': 4096,
    'temperature': 0.3,  # Lower for more consistent/factual outputs
    'top_p': 0.9,
}

# Article Filter Configuration
ARTICLE_FILTER_CONFIG = {
    'batch_size': 10,  # Articles per Claude API call
    'importance_threshold': 0.6,  # Minimum score to keep article
    'prompt_template': '''Analyze the following news articles and determine if they are newsworthy.

Newsworthy articles include:
- Breaking news and major events
- Significant policy changes or announcements
- Important investigations or revelations
- Major international developments
- Substantial economic/market changes

NOT newsworthy (should be filtered):
- Opinion pieces and editorials
- Minor celebrity gossip
- Incremental updates without substance
- Promotional content
- Very local/niche stories without broader impact

For each article, provide:
1. Score (0.0 to 1.0) where 1.0 is highly newsworthy
2. Reason (brief explanation)
3. Decision (keep or filter)''',
}

# SEO Optimization Configuration
SEO_CONFIG = {
    'meta_description_length': 160,  # Optimal for Google
    'og_title_length': 60,  # Optimal for social media
    'max_keywords': 10,
    'keyword_extraction_prompt': '''Extract the most important SEO keywords from this news story.
Focus on:
- Main topics and subjects
- Named entities (people, places, organizations)
- Key events or concepts
- Industry/sector terms

Return 5-10 keywords that would help people find this article through search engines.''',
}

# Country Detection Configuration
COUNTRY_DETECTOR_CONFIG = {
    'confidence_threshold': 0.5,  # Minimum confidence to assign country
    'prompt_template': '''Identify the primary country this news story is about.

Consider:
- Geographic location of events
- Primary actors (government, companies, people)
- Impact zone

Return:
1. ISO 3166-1 alpha-2 country code (e.g., "US", "GB", "IL", "FR")
2. Confidence score (0.0 to 1.0)
3. Brief reason

If the story is truly global or involves multiple countries equally, return "GLOBAL".
If uncertain, return "UNKNOWN".'''
,
}

# Quality Thresholds
QUALITY_THRESHOLDS = {
    'newsworthiness_score': 0.6,  # Minimum score to keep article
    'importance_score': 0.5,  # Minimum score for article ranking
    'seo_confidence': 0.7,  # Minimum confidence for SEO metadata
}

# Feature Flags
FEATURE_FLAGS = {
    'enable_article_filtering': True,
    'enable_seo_optimization': True,
    'enable_country_detection': True,
    'enable_advanced_clustering': True,
}
