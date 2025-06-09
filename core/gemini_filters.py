"""
Gemini Filters Module

Implements filtering utilities for news articles.
Can be run directly to test filtering.

Author: infoyouth
Date: 2025-06-08
"""

from datetime import datetime, timedelta, timezone
from typing import List, Dict
from logger.logger_config import setup_logger

logger = setup_logger()


class ArticleFilter:
    """
    Utility class for filtering news articles.
    """

    @staticmethod
    def filter_recent_articles(
        articles: List[Dict[str, str]], days: int
    ) -> List[Dict[str, str]]:
        """
        Filters articles published within the specified number of days.

        Args:
            articles: List of articles to filter.
            days: Number of days for filtering.

        Returns:
            List of recent articles.
        """
        now = datetime.now(timezone.utc)
        time_threshold = now - timedelta(days=days)
        recent_articles = [
            {"title": article["title"], "url": article["url"]}
            for article in articles
            if "publishedAt" in article
            and datetime.strptime(article["publishedAt"], "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=timezone.utc
            )
            > time_threshold
        ]
        logger.info(
            f"Found {len(recent_articles)} articles published "
            f"in the last {days} days."
        )
        return recent_articles


if __name__ == "__main__":
    import json

    # Demo articles (adjust date for testing)
    articles = [
        {
            "title": "Test 1",
            "url": "http://a.com",
            "publishedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
        {
            "title": "Test 2",
            "url": "http://b.com",
            "publishedAt": (datetime.now(timezone.utc) - timedelta(days=5)).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            ),
        },
    ]
    filtered = ArticleFilter.filter_recent_articles(articles, days=2)
    print(json.dumps(filtered, indent=2))
