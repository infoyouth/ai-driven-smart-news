"""
Discord News Full Pipeline

Reads raw news JSON, enriches with Gemini (adds topic, emoji, summary), and writes
Discord-ready Markdown (emoji + title link per line) to a text file.

Usage:
    python discord_news_full_pipeline.py input.json output.txt
"""

import os
import sys
import json
import asyncio
import aiohttp
from pathlib import Path
from typing import List, Dict

from core.gemini_api import GeminiApiClient
from logger.logger_config import setup_logger

logger = setup_logger()


class NewsDiscordFormatter:
    """
    Handles enrichment of news articles using Gemini and formatting
    them for Discord in a single line per article.
    """

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self.gemini_client = GeminiApiClient(self.api_key)
        logger.debug("NewsDiscordFormatter initialized with Gemini API key.")

    @staticmethod
    def format_one_liner(news_items: List[Dict[str, str]]) -> str:
        lines = []
        for idx, item in enumerate(news_items):
            title = item.get("title")
            url = item.get("url")
            emoji = item.get("emoji", "📰")
            if not title or not url:
                logger.warning(
                    f"Skipping article at index {idx} due to missing title or url: {item}"
                )
                continue
            lines.append(f"{emoji} [{title}]({url})")
        return "\n".join(lines)

    async def enrich_news(self, raw_news: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Enrich articles using Gemini (topics, emojis, summaries).
        Handles API errors gracefully.
        """
        logger.info("Starting enrichment of news articles with Gemini.")
        async with aiohttp.ClientSession() as session:
            try:
                enriched = await self.gemini_client.enrich_articles(session, raw_news)
            except aiohttp.ClientError as e:
                logger.error("Failed to enrich articles: %s", e)
                raise
        logger.info("Enrichment complete. Total articles enriched: %d", len(enriched))
        return enriched

    async def process(self, input_path: Path, output_path: Path) -> None:
        """
        Complete pipeline:
        - Load raw news
        - Enrich with Gemini
        - Format for Discord
        - Write to output file
        """
        logger.info("Pipeline started: %s -> %s", input_path, output_path)

        # Validate input file
        if not input_path.exists():
            logger.critical("Input file not found: %s", input_path)
            raise FileNotFoundError(f"Input file not found: {input_path}")

        if input_path.suffix != ".json":
            logger.critical(
                "Invalid input file format. Expected a .json file: %s", input_path
            )
            raise ValueError("Input file must be a .json file.")

        # Load raw news
        try:
            with input_path.open("r", encoding="utf-8") as fin:
                raw_news = json.load(fin)
            logger.info("Loaded %d raw news articles.", len(raw_news))
        except json.JSONDecodeError as e:
            logger.critical("Failed to parse input JSON file: %s", e)
            raise

        # Validate raw news structure
        if not isinstance(raw_news, list) or not all(
            isinstance(item, dict) for item in raw_news
        ):
            logger.critical(
                "Invalid input file format. Expected a list of dictionaries."
            )
            raise ValueError("Input file must contain a list of dictionaries.")

        # Enrich news
        enriched_news = await self.enrich_news(raw_news)

        # Format for Discord
        formatted = self.format_one_liner(enriched_news)

        # Validate output file format
        if output_path.suffix != ".txt":
            logger.critical(
                "Invalid output file format. Expected a .txt file: %s", output_path
            )
            raise ValueError("Output file must be a .txt file.")

        # Write to output file
        try:
            with output_path.open("w", encoding="utf-8") as fout:
                fout.write(formatted)
            logger.info("Discord-ready news written to %s", output_path)
        except Exception as e:
            logger.critical("Failed to write to output file: %s", e)
            raise


def main() -> None:
    """
    Entry point for the script. Validates arguments, initializes the formatter,
    and runs the processing pipeline.
    """
    if len(sys.argv) != 3:
        print("Usage: python discord_news_full_pipeline.py input.json output.txt")
        sys.exit(1)

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key or len(api_key) < 20:  # Example validation for API key length
        logger.critical("Invalid or missing GEMINI_API_KEY environment variable.")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    formatter = NewsDiscordFormatter(api_key)
    try:
        asyncio.run(formatter.process(input_path, output_path))
        logger.info("Pipeline completed successfully.")
    except FileNotFoundError as e:
        logger.error("File not found: %s", e)
        sys.exit(1)
    except ValueError as e:
        logger.error("Validation error: %s", e)
        sys.exit(1)
    except Exception as exc:
        logger.critical("Pipeline failed: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
