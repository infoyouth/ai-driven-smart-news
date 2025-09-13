"""GeminiNewsProcessor

Contains the `GeminiNewsProcessor` class moved out of `gemini_processor.py` to
keep responsibilities separated. This file focuses on the async processor
that loads articles, filters them, calls Gemini, and saves results.
"""
import json
import aiohttp
from typing import List, Dict, Any
from logger.logger_config import setup_logger
from core.gemini_filters import ArticleFilter
from core.gemini_api import GeminiApiClient

logger = setup_logger()


class GeminiNewsProcessor:
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
        try:
            with open(self.input_file, "r", encoding="utf-8") as file:
                articles = json.load(file)
                logger.info(
                    "Loaded %d articles from %s",
                    len(articles),
                    self.input_file,
                )
                return articles
        except FileNotFoundError:
            logger.error("Input file %s not found.", self.input_file)
            raise
        except json.JSONDecodeError:
            logger.error("Error decoding JSON from %s.", self.input_file)
            raise

    async def process_articles(
        self, articles: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        recent_articles = ArticleFilter.filter_recent_articles(articles, self.days)
        if not recent_articles:
            logger.warning("No recent articles in the last %d days.", self.days)
            return []
        async with aiohttp.ClientSession() as session:
            top_titles = await self.gemini_client.analyze_titles(
                session, recent_articles
            )
            logger.info("Filtered %d articles.", len(top_titles))
            return top_titles

    async def save_data(self, articles: List[Dict[str, Any]]) -> None:
        try:
            with open(self.output_file, "w", encoding="utf-8") as file:
                json.dump(articles, file, indent=2)
            logger.info(
                "Saved %d filtered articles to %s",
                len(articles),
                self.output_file,
            )
        except Exception as exc:
            logger.error("Error saving data to %s: %s", self.output_file, exc)
            raise
