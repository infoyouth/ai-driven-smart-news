"""
Gemini News Processor

Orchestrates the processing and filtering of news articles using the Gemini API.
Can be run directly for the full pipeline.

Author: infoyouth
Date: 2025-06-08
"""

import os
import json
import aiohttp
from typing import List, Dict, Any
from logger.logger_config import setup_logger
from core.gemini_filters import ArticleFilter
from core.gemini_api import GeminiApiClient

logger = setup_logger()


class GeminiNewsProcessor:
    """
    Processes news articles and analyzes their relevance for engineering students.

    Attributes:
        input_file: Path to the input JSON file.
        output_file: Path to the output JSON file.
        days: Number of days for recent articles.
        gemini_client: GeminiApiClient instance.
    """

    def __init__(
        self,
        input_file: str,
        output_file: str,
        gemini_api_key: str,
        days: int = 1,
    ):
        self.input_file = input_file
        self.output_file = output_file
        self.days = days
        self.gemini_client = GeminiApiClient(gemini_api_key)

    async def load_data(self) -> List[Dict[str, Any]]:
        """
        Loads articles from the input file.

        Returns:
            List of articles.

        Raises:
            FileNotFoundError: If the file is missing.
            json.JSONDecodeError: If the file is not valid JSON.
        """
        try:
            with open(self.input_file, "r") as file:
                articles = json.load(file)
                logger.info(f"Loaded {len(articles)} articles from {self.input_file}.")
                return articles
        except FileNotFoundError:
            logger.error(f"Input file {self.input_file} not found.")
            raise
        except json.JSONDecodeError:
            logger.error(f"Error decoding JSON from {self.input_file}.")
            raise

    async def process_articles(
        self, articles: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Filters and analyzes articles.

        Args:
            articles: List of loaded articles.

        Returns:
            Filtered and analyzed articles.
        """
        recent_articles = ArticleFilter.filter_recent_articles(articles, self.days)
        if not recent_articles:
            logger.warning(
                "No articles found published within the specified time frame."
            )
            return [
                {
                    "message": (
                        f"No articles found published within the last "
                        f"{self.days} days."
                    )
                }
            ]
        async with aiohttp.ClientSession() as session:
            top_titles = await self.gemini_client.analyze_titles(
                session, recent_articles
            )
            logger.info(f"Filtered {len(top_titles)} articles.")
            return top_titles

    async def save_data(self, articles: List[Dict[str, Any]]) -> None:
        """
        Saves filtered articles to the output file.

        Args:
            articles: List of filtered articles.
        """
        try:
            with open(self.output_file, "w") as file:
                json.dump(articles, file, indent=4)
            logger.info(
                f"Saved {len(articles)} filtered articles to {self.output_file}."
            )
        except Exception as exc:
            logger.error(f"Error saving data to {self.output_file}: {exc}")
            raise


async def main() -> None:
    """
    Main entrypoint for the Gemini News Processor.
    """
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        logger.critical(
            "Gemini API key not found. Please set the GEMINI_API_KEY environment "
            "variable."
        )
        raise ValueError(
            "Gemini API key not found. Please set the GEMINI_API_KEY environment "
            "variable."
        )
    processor = GeminiNewsProcessor(
        "latest_news.json", "filtered_news.json", gemini_api_key, days=2
    )
    try:
        articles = await processor.load_data()
        filtered_articles = await processor.process_articles(articles)
        await processor.save_data(filtered_articles)
        logger.info(
            f"Processing completed successfully. Filtered "
            f"{len(filtered_articles)} articles."
        )
    except Exception as exc:
        logger.critical(f"An unexpected error occurred: {exc}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
