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


class NewsFetcher:
    """
    Handles fetching news from various sources.

    Attributes:
        api_config_loader (APIConfigLoader): Instance of APIConfigLoader.
    """

    def __init__(self, api_config_loader: APIConfigLoader):
        """
        Initialize the NewsFetcher.

        Args:
            api_config_loader (APIConfigLoader): Instance of APIConfigLoader.
        """
        self.api_config_loader = api_config_loader

    def _construct_endpoint(self, source: dict, endpoint_name: str, **kwargs) -> str:
        """
        Construct the endpoint URL dynamically.

        Args:
            source (dict): Source configuration.
            endpoint_name (str): Name of the endpoint.
            kwargs: Dynamic parameters for the endpoint.

        Returns:
            str: Constructed endpoint URL.
        """
        logger.debug(f"Source configuration: {source}")
        base_url = source["base_url"]
        endpoint = source["endpoints"][endpoint_name]
        endpoint = urljoin(base_url, endpoint)
        for key, value in kwargs.items():
            endpoint = endpoint.replace(f"<{key}>", value)
        return endpoint

    def fetch_news(
        self,
        source_name: str,
        country: Optional[str] = None,
        category: Optional[str] = None,
    ) -> Dict:
        """
        Fetch news from the specified source.

        Args:
            source_name (str): Name of the source.
            country (str, optional): Country code.
            category (str, optional): News category.

        Returns:
            dict: Fetched news data.
        """
        source = self.api_config_loader.get_source(source_name)
        if not source:
            logger.error(f"Source not found: {source_name}")
            return {}

        endpoint = self._construct_endpoint(
            source, "top_headlines", country=country, category=category
        )
        now = datetime.utcnow()
        from_date = (now - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        params = {
            "apiKey": source.get("api_key"),
            "country": country,
            "category": category,
            "pageSize": source["default_params"]["pageSize"],
            "language": source["default_params"]["language"],
            "from": from_date,  # Only last 24 hours
            "sortBy": "publishedAt",  # Latest first
        }

        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()
            if "articles" not in data:
                logger.error(f"Invalid response structure: {data}")
                return {}
            logger.info(f"Fetched news for country: {country}, category: {category}")
            return data
        except requests.exceptions.HTTPError as e:
            logger.error(f"Error fetching news: {e} (Line: {e.response.status_code})")
            return {}

    def fetch_latest_news(self, source_name: str) -> List[Dict]:
        """
        Fetch the latest news for all countries and categories concurrently.

        Args:
            source_name (str): Name of the source.

        Returns:
            list: List of news articles.
        """
        source = self.api_config_loader.get_source(source_name)
        if not source:
            logger.error(f"Source not found: {source_name}")
            return []

        results = []

        def fetch_for_country_and_category(country, category):
            logger.debug(f"Fetching news for country: {country}, category: {category}")
            return self.fetch_news(source_name, country=country, category=category)

        with ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(fetch_for_country_and_category, country, category)
                for country in source["available_countries"]
                for category in source["available_categories"]
            ]
            for future in futures:
                news = future.result()
                if news:
                    results.extend(news.get("articles", []))

        logger.info(f"Fetched {len(results)} articles.")
        return results


if __name__ == "__main__":
    CONFIG_PATH = "configs/api_config.json"
    try:
        loader = APIConfigLoader(CONFIG_PATH)
        fetcher = NewsFetcher(loader)
        news = fetcher.fetch_news("NewsAPI", country="us", category="technology")
        logger.info(f"Fetched news: {news}")
    except Exception as e:
        logger.error(f"Error: {e}")
