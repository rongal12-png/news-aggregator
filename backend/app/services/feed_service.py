import feedparser
import hashlib
from datetime import datetime, timezone
from typing import List, Optional
from dateutil import parser as date_parser

from app.config import settings
from app.utils import normalize_title, generate_url_hash, sanitize_html


class FeedEntry:
    def __init__(
        self,
        title: str,
        url: str,
        url_hash: str,
        snippet: str,
        published_at: datetime,
        normalized_key: str,
    ):
        self.title = title
        self.url = url
        self.url_hash = url_hash
        self.snippet = snippet
        self.published_at = published_at
        self.normalized_key = normalized_key


class FeedService:
    def __init__(self):
        self.timeout = settings.FEED_FETCH_TIMEOUT
        self.limit = settings.FEED_FETCH_LIMIT

    def parse_feed(self, feed_url: str) -> List[FeedEntry]:
        """
        Parse an RSS feed and return a list of entries.
        """
        try:
            feed = feedparser.parse(feed_url)

            if feed.bozo and not feed.entries:
                # Feed parsing error with no entries
                return []

            entries = []
            for entry in feed.entries[:self.limit]:
                parsed_entry = self._parse_entry(entry)
                if parsed_entry:
                    entries.append(parsed_entry)

            return entries

        except Exception as e:
            # Log error in production
            return []

    def _parse_entry(self, entry) -> Optional[FeedEntry]:
        """
        Parse a single feed entry into our format.
        """
        # Get title
        title = getattr(entry, "title", None)
        if not title:
            return None

        title = sanitize_html(title, max_length=500)

        # Get URL
        url = getattr(entry, "link", None)
        if not url:
            return None

        # Get snippet/summary
        snippet = ""
        if hasattr(entry, "summary"):
            snippet = sanitize_html(entry.summary, max_length=500)
        elif hasattr(entry, "description"):
            snippet = sanitize_html(entry.description, max_length=500)

        # Get published date
        published_at = self._parse_date(entry)

        # Generate normalized key for clustering
        normalized_key = normalize_title(title)

        # Generate URL hash for deduplication
        url_hash = generate_url_hash(url)

        return FeedEntry(
            title=title,
            url=url,
            url_hash=url_hash,
            snippet=snippet,
            published_at=published_at,
            normalized_key=normalized_key,
        )

    def _parse_date(self, entry) -> datetime:
        """
        Parse the published date from a feed entry.
        """
        # Try different date fields
        date_fields = ["published_parsed", "updated_parsed", "created_parsed"]

        for field in date_fields:
            if hasattr(entry, field) and getattr(entry, field):
                try:
                    time_tuple = getattr(entry, field)
                    return datetime(*time_tuple[:6], tzinfo=timezone.utc)
                except (TypeError, ValueError):
                    continue

        # Try parsing string dates
        string_fields = ["published", "updated", "created"]
        for field in string_fields:
            if hasattr(entry, field) and getattr(entry, field):
                try:
                    return date_parser.parse(getattr(entry, field))
                except (ValueError, TypeError):
                    continue

        # Default to now if no date found
        return datetime.now(timezone.utc)
