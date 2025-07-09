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
from core.discord_poster import NewsDiscordFormatter  # Import the formatter
from logger.logger_config import setup_logger
from core.gemini_processor import main as gemini_main
import asyncio
import os
from pathlib import Path

logger = setup_logger()

if __name__ == "__main__":
    CONFIG_PATH = "configs/api_config.json"
    OUTPUT_FILE = "latest_news.json"
    FILTERED_FILE = "filtered_news.json"
    DISCORD_OUTPUT_FILE = "output.txt"

    try:
        logger.info("Starting the AI-driven smart news application.")

        # Load API configuration
        logger.info(f"Loading API configuration from {CONFIG_PATH}.")
        api_config_loader = APIConfigLoader(CONFIG_PATH)
        logger.info("API configuration loaded successfully.")

        # Fetch news
        logger.info("Fetching the latest news articles.")
        news_fetcher = NewsFetcher(api_config_loader)
        all_latest_news = []
        for source in api_config_loader.get_all_sources():
            name = source.get("name")
            logger.info(f"Fetching latest news from source: {name}")
            latest_news = news_fetcher.fetch_latest_news(name)
            all_latest_news.extend(latest_news)

        if not latest_news:
            logger.warning("No latest news found. Skipping GeminiNewsProcessor.")
        else:
            logger.info(f"Fetched {len(latest_news)} articles.")

            # Save news to file
            logger.info(f"Saving fetched news to {OUTPUT_FILE}.")
            NewsSaver.save_news_to_file(latest_news, OUTPUT_FILE)
            logger.info("News saved successfully.")

            # Process saved news using GeminiNewsProcessor
            logger.info("Processing saved news using GeminiNewsProcessor.")
            asyncio.run(gemini_main())
            logger.info("GeminiNewsProcessor completed successfully.")

            # Generate Discord-ready output
            logger.info("Generating Discord-ready output.")
            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                logger.critical("Set GEMINI_API_KEY environment variable.")
                raise EnvironmentError("GEMINI_API_KEY not set.")

            discord_formatter = NewsDiscordFormatter(api_key)
            asyncio.run(
                discord_formatter.process(
                    Path(FILTERED_FILE), Path(DISCORD_OUTPUT_FILE)
                )
            )
            logger.info(f"Discord-ready output written to {DISCORD_OUTPUT_FILE}.")

        logger.info("AI-driven smart news application finished.")
    except FileNotFoundError as e:
        logger.error(f"Configuration file not found: {e}")
    except Exception as e:
        logger.critical(f"An unexpected error occurred: {e}")
