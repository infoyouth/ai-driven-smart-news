"""
news_fetcher.py
---------------
This module is responsible for fetching news articles from various sources
using the API configuration provided by the `APIConfigLoader`. It constructs
dynamic endpoints and handles HTTP requests to retrieve news data.

The `NewsFetcher` class provides methods to fetch news for specific countries
and categories, as well as fetch the latest news across all configurations.

Author: infoyouth
Date: 2025-06-08
"""
import requests
from typing import Optional, List, Dict
from logger.logger_config import setup_logger
from core.api_config_loader import APIConfigLoader
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

logger = setup_logger()


def get_by_path(obj, path):
    """Helper to get nested data by dot-separated path."""
    for part in path.split("."):
        obj = obj.get(part, {})
    return obj if isinstance(obj, list) else []


def get_value_by_path(obj, path: Optional[str]):
    """Get a nested value from a dict by dot-separated path. Return None if missing."""
    if not path:
        return None
    cur = obj
    for part in path.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
        if cur is None:
            return None
    return cur


class NewsFetcher:
    def __init__(self, api_config_loader: APIConfigLoader):
        self.api_config_loader = api_config_loader

    def _construct_endpoint(self, source: dict, endpoint_name: str, **kwargs) -> str:
        base_url = source["base_url"]
        endpoint_path = source["endpoints"][endpoint_name]
        return urljoin(base_url, endpoint_path)

    def fetch_news(
        self,
        source_name: str,
        country: Optional[str] = None,
        category: Optional[str] = None,
    ) -> Dict:
        source = self.api_config_loader.get_source(source_name)
        if not source:
            logger.error(f"Source not found: {source_name}")
            return {}

        endpoint = self._construct_endpoint(
            source, "top_headlines", country=country or "", category=category or ""
        )

        params = dict(source.get("default_params", {}))

        # Only add if the values are passed and allowed
        if country:
            params["country"] = country
        if category:
            params["category"] = category

        # Add time filter if supported
        now = datetime.utcnow()
        if "from" in params:
            params["from"] = (now - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        if "sortBy" in params:
            params["sortBy"] = "publishedAt"

        headers = source.get("headers", {})

        if source.get("requires_auth") and source.get("api_key"):
            # Respect key passing format (commonly via query param)
            params["apiKey"] = source["api_key"]

        try:
            response = requests.get(endpoint, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()

            mapping = source.get("response_mapping", {})
            items = get_by_path(data, mapping.get("articles_path", "articles"))

            articles = []
            for item in items:
                article = {
                    "title": item.get(mapping.get("title", "title"), ""),
                    "url": item.get(mapping.get("url", "url"), ""),
                    "description": item.get(
                        mapping.get("description", "description"), ""
                    ),
                    "published_at": get_value_by_path(item, mapping.get("published_at_path")),
                }
                if article["title"] and article["url"]:
                    articles.append(article)

            logger.info(f"Fetched {len(articles)} articles from {source_name}")
            return {"articles": articles}

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error fetching news from {source_name}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching news from {source_name}: {e}")
        return {}

    def fetch_latest_news(self, source_name: str) -> List[Dict]:
        source = self.api_config_loader.get_source(source_name)
        if not source:
            logger.error(f"Source not found: {source_name}")
            return []

        countries = source.get("available_countries")
        categories = source.get("available_categories")

        combinations = []

        # Build combinations only if both exist
        if countries and categories:
            combinations = [(c, cat) for c in countries for cat in categories]
        elif countries:
            combinations = [(c, None) for c in countries]
        elif categories:
            combinations = [(None, cat) for cat in categories]
        else:
            # No combinations → fetch once
            combinations = [(None, None)]

        results = []

        def fetch_task(country, category):
            return self.fetch_news(source_name, country=country, category=category)

        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(fetch_task, c, cat) for c, cat in combinations]
            for future in futures:
                result = future.result()
                if result:
                    results.extend(result.get("articles", []))

        logger.info(f"Fetched {len(results)} articles from {source_name}.")
        return results


if __name__ == "__main__":
    CONFIG_PATH = "configs/api_config.json"
    try:
        loader = APIConfigLoader(CONFIG_PATH)
        fetcher = NewsFetcher(loader)
        all_sources = loader.get_all_sources()
        for source in all_sources:
            name = source.get("name")
            logger.info(f"Fetching news from source: {name}")
            news = fetcher.fetch_news(name)
            logger.info(f"Fetched news from {name}: {news}")
    except Exception as e:
        logger.error(f"Error: {e}")
