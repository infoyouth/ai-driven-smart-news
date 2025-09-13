"""
main.py
-------
This is the entry point for the AI-driven smart news application. It integrates
the `APIConfigLoader`, `NewsFetcher`, and `NewsSaver` modules to load API
configuration, fetch news articles, and save them to a JSON file.

The script is designed to handle errors gracefully and log important events
for debugging and monitoring purposes.

Author: infoyouth
Date: 2025-06-08
"""
from core.api_config_loader import APIConfigLoader
from core.news_fetcher import NewsFetcher
from core.news_saver import NewsSaver
from core.news_filter import filter_top_n
from logger.logger_config import setup_logger

logger = setup_logger()
if __name__ == "__main__":
    CONFIG_PATH = "configs/api_config.json"
    RAW_SUFFIX = "_latest.json"

    try:
        logger.info("Starting the AI-driven smart news application.")

        # Load API configuration
        logger.info(f"Loading API configuration from {CONFIG_PATH}.")
        api_config_loader = APIConfigLoader(CONFIG_PATH)
        logger.info("API configuration loaded successfully.")

        news_fetcher = NewsFetcher(api_config_loader)

        for source in api_config_loader.get_all_sources():
            name = source.get("name")
            if not name:
                logger.warning("Found source without a name, skipping.")
                continue

            logger.info(f"Fetching latest news from source: {name}")
            latest_news = news_fetcher.fetch_latest_news(name)

            if not latest_news:
                logger.warning(
                    f"No latest news found for source '{name}'. Skipping saving."
                )
                continue

            raw_filename = f"{name.lower().replace(' ', '_')}{RAW_SUFFIX}"

            logger.info(f"Saving raw news for source '{name}' to {raw_filename}.")
            NewsSaver.save_news_to_file(latest_news, raw_filename)

            # Apply filtering to produce filtered_<source>.json
            mapping = source.get("response_mapping", {})
            limit = source.get("filter_limit", 10)
            try:
                filtered = filter_top_n(latest_news, mapping, n=limit)
            except Exception as e:
                logger.error(f"Error filtering news for {name}: {e}")
                filtered = latest_news[:limit] if isinstance(latest_news, list) else []

            filtered_filename = f"filtered_{name.lower().replace(' ', '_')}.json"
            logger.info(
                f"Saving filtered news for source '{name}' to {filtered_filename}."
            )
            NewsSaver.save_news_to_file(filtered, filtered_filename)

        logger.info("AI-driven smart news application finished.")

    except FileNotFoundError as e:
        logger.error(f"Configuration file not found: {e}")
    except Exception as e:
        logger.critical(f"An unexpected error occurred: {e}")
