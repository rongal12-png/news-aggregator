"""Agent-based pipeline infrastructure for news aggregation."""

from .base import BaseAgent, AgentResult, AgentConfig, AgentStatus
from .article_filter import ArticleFilterAgent, ArticleFilterInput, ArticleFilterOutput
from .seo_editor import SEOEditorAgent, SEOEditorInput, SEOEditorOutput
from .country_detector import CountryDetectorAgent, CountryDetectorInput, CountryDetectorOutput
from ..agent_config import AGENT_CONFIGS

__all__ = [
    'BaseAgent',
    'AgentResult',
    'AgentConfig',
    'AgentStatus',
    'AGENT_CONFIGS',
    'ArticleFilterAgent',
    'ArticleFilterInput',
    'ArticleFilterOutput',
    'SEOEditorAgent',
    'SEOEditorInput',
    'SEOEditorOutput',
    'CountryDetectorAgent',
    'CountryDetectorInput',
    'CountryDetectorOutput',
]
