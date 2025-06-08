import os
import json
import requests
from typing import Optional, List, Dict
from logger.logger_config import setup_logger

# Set up logger
logger = setup_logger()


class APIConfigLoader:
    """
    Handles loading and validation of API configuration.

    Attributes:
        config_path (str): Path to the configuration file.
        config (dict): Loaded configuration data.
    """

    def __init__(self, config_path: str):
        """
        Initialize the APIConfigLoader.

        Args:
            config_path (str): Path to the configuration file.
        """
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> dict:
        """
        Load API configuration from a JSON file.

        Returns:
            dict: Parsed configuration data.

        Raises:
            FileNotFoundError: If the configuration file is not found.
            json.JSONDecodeError: If the configuration file is not valid JSON.
            ValueError: If an API key is missing for a source.
        """
        try:
            with open(self.config_path, "r") as file:
                config = json.load(file)
                for source in config["sources"]:
                    if source.get("api_key_env"):
                        source["api_key"] = os.getenv(source["api_key_env"])
                        if not source["api_key"]:
                            logger.error(f"API key not found for source: {source['name']}")
                            raise ValueError(f"API key missing for source: {source['name']}")
                        logger.debug(f"Loaded API key for {source['name']}: {source['api_key']}")
                logger.info("API configuration loaded successfully.")
                return config
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {self.config_path}")
            raise
        except json.JSONDecodeError:
            logger.error(f"Error decoding JSON configuration file: {self.config_path}")
            raise

    def get_source(self, source_name: str) -> Optional[dict]:
        """
        Retrieve a specific source configuration by name.

        Args:
            source_name (str): Name of the source.

        Returns:
            dict: Source configuration if found, otherwise None.
        """
        return next((s for s in self.config["sources"] if s["name"] == source_name), None)


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
        endpoint = source["endpoints"][endpoint_name]
        if "<BASE_URL>" in endpoint:
            endpoint = endpoint.replace("<BASE_URL>", source["base_url"])
        for key, value in kwargs.items():
            endpoint = endpoint.replace(f"<{key}>", value)
        return endpoint

    def fetch_news(
        self, source_name: str, country: Optional[str] = None, category: Optional[str] = None
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

        endpoint = self._construct_endpoint(source, "top_headlines", country=country, category=category)
        params = {
            "apiKey": source.get("api_key"),
            "country": country,
            "category": category,
            "pageSize": source["default_params"]["pageSize"],
            "language": source["default_params"]["language"],
        }
        logger.debug(f"Requesting URL: {endpoint} with params: {params}")

        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            logger.info(f"Fetched news for country: {country}, category: {category}")
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"Error fetching news: {e} (Line: {e.response.status_code})")
            return {}

    def fetch_latest_news(self, source_name: str) -> List[Dict]:
        """
        Fetch the latest news for all countries and categories.

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
        for country in source["available_countries"]:
            for category in source["available_categories"]:
                logger.debug(f"Fetching news for country: {country}, category: {category}")
                news = self.fetch_news(source_name, country=country, category=category)
                if news:
                    results.extend(news.get("articles", []))
        logger.info(f"Fetched {len(results)} articles.")
        return results


class NewsSaver:
    """
    Handles saving fetched news to a file.
    """

    @staticmethod
    def save_news_to_file(news: List[Dict], output_file: str) -> None:
        """
        Save news articles to a JSON file.

        Args:
            news (list): List of news articles.
            output_file (str): Path to the output file.
        """
        try:
            with open(output_file, "w") as file:
                json.dump(news, file, indent=4)
            logger.info(f"Saved {len(news)} articles to {output_file}.")
        except Exception as e:
            logger.error(f"Error saving news to file: {e}")
            raise


if __name__ == "__main__":
    CONFIG_PATH = "configs/api_config.json"
    OUTPUT_FILE = "latest_news.json"

    try:
        # Load API configuration
        api_config_loader = APIConfigLoader(CONFIG_PATH)

        # Fetch news
        news_fetcher = NewsFetcher(api_config_loader)
        latest_news = news_fetcher.fetch_latest_news("NewsAPI")

        # Save news to file
        NewsSaver.save_news_to_file(latest_news, OUTPUT_FILE)
    except Exception as e:
        logger.critical(f"An unexpected error occurred: {e}")