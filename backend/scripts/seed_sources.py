"""
Seed script to add initial RSS sources.
Run with: python -m scripts.seed_sources
"""
import sys
sys.path.insert(0, '.')

from app.db import SessionLocal
from app.models import Source

SAMPLE_SOURCES = [
    # Technology
    {
        "name": "TechCrunch",
        "feed_url": "https://techcrunch.com/feed/",
        "language": "en",
        "category": "tech",
        "weight": 1.5,
    },
    {
        "name": "Hacker News",
        "feed_url": "https://hnrss.org/frontpage",
        "language": "en",
        "category": "tech",
        "weight": 2.0,
    },
    {
        "name": "Ars Technica",
        "feed_url": "https://feeds.arstechnica.com/arstechnica/index",
        "language": "en",
        "category": "tech",
        "weight": 1.5,
    },
    {
        "name": "The Verge",
        "feed_url": "https://www.theverge.com/rss/index.xml",
        "language": "en",
        "category": "tech",
        "weight": 1.5,
    },
    {
        "name": "BBC Technology",
        "feed_url": "http://feeds.bbci.co.uk/news/technology/rss.xml",
        "language": "en",
        "category": "tech",
        "weight": 1.5,
    },
    {
        "name": "Wired",
        "feed_url": "https://www.wired.com/feed/rss",
        "language": "en",
        "category": "tech",
        "weight": 1.5,
    },

    # General News
    {
        "name": "BBC News",
        "feed_url": "http://feeds.bbci.co.uk/news/rss.xml",
        "language": "en",
        "category": "general",
        "weight": 2.0,
    },
    {
        "name": "Reuters World",
        "feed_url": "https://www.reutersagency.com/feed/?best-regions=world",
        "language": "en",
        "category": "general",
        "weight": 2.0,
    },
    {
        "name": "NPR News",
        "feed_url": "https://feeds.npr.org/1001/rss.xml",
        "language": "en",
        "category": "general",
        "weight": 1.5,
    },

    # Crypto
    {
        "name": "CoinDesk",
        "feed_url": "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "language": "en",
        "category": "crypto",
        "weight": 1.5,
    },
    {
        "name": "Cointelegraph",
        "feed_url": "https://cointelegraph.com/rss",
        "language": "en",
        "category": "crypto",
        "weight": 1.5,
    },
    {
        "name": "Bitcoin Magazine",
        "feed_url": "https://bitcoinmagazine.com/feed",
        "language": "en",
        "category": "crypto",
        "weight": 1.5,
    },

    # Finance
    {
        "name": "BBC Business",
        "feed_url": "http://feeds.bbci.co.uk/news/business/rss.xml",
        "language": "en",
        "category": "finance",
        "weight": 1.5,
    },
    {
        "name": "CNBC Top News",
        "feed_url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114",
        "language": "en",
        "category": "finance",
        "weight": 2.0,
    },
    {
        "name": "MarketWatch",
        "feed_url": "https://feeds.marketwatch.com/marketwatch/topstories/",
        "language": "en",
        "category": "finance",
        "weight": 1.5,
    },
    {
        "name": "Financial Times",
        "feed_url": "https://www.ft.com/rss/home",
        "language": "en",
        "category": "finance",
        "weight": 2.0,
    },
    {
        "name": "Bloomberg Markets",
        "feed_url": "https://feeds.bloomberg.com/markets/news.rss",
        "language": "en",
        "category": "finance",
        "weight": 2.0,
    },

    # Sports
    {
        "name": "BBC Sport",
        "feed_url": "http://feeds.bbci.co.uk/sport/rss.xml",
        "language": "en",
        "category": "sports",
        "weight": 2.0,
    },
    {
        "name": "ESPN Top Headlines",
        "feed_url": "https://www.espn.com/espn/rss/news",
        "language": "en",
        "category": "sports",
        "weight": 2.0,
    },
    {
        "name": "Sky Sports News",
        "feed_url": "https://www.skysports.com/rss/12040",
        "language": "en",
        "category": "sports",
        "weight": 1.5,
    },
    {
        "name": "BBC Football",
        "feed_url": "http://feeds.bbci.co.uk/sport/football/rss.xml",
        "language": "en",
        "category": "sports",
        "weight": 1.5,
    },
]


def seed_sources():
    db = SessionLocal()

    try:
        added = 0
        skipped = 0

        for source_data in SAMPLE_SOURCES:
            # Check if source already exists
            existing = db.query(Source).filter(
                Source.feed_url == source_data["feed_url"]
            ).first()

            if existing:
                print(f"Skipped (exists): {source_data['name']}")
                skipped += 1
                continue

            source = Source(**source_data)
            db.add(source)
            print(f"Added: {source_data['name']}")
            added += 1

        db.commit()
        print(f"\nDone! Added: {added}, Skipped: {skipped}")

    finally:
        db.close()


if __name__ == "__main__":
    seed_sources()
