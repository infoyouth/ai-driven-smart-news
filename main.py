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
from logger.logger_config import setup_logger

logger = setup_logger()

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