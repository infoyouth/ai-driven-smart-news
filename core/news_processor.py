"""
Gemini News Processor

This script processes news articles, filters them based on their publication date,
analyzes their relevance using the Gemini AI API, and saves the filtered results.

Modules:
    - aiohttp: For asynchronous HTTP requests.
    - json: For handling JSON data.
    - re: For regular expressions to clean up text.
    - asyncio: For asynchronous programming.
    - datetime: For handling date and time operations.
    - logger.logger_config: For setting up logging.

Usage:
    Set the GEMINI_API_KEY environment variable with your API key.
    Run the script to process articles from the input file and save filtered results to the output file.
"""
import os
import json
import aiohttp
import re
import asyncio
from datetime import datetime, timedelta, timezone
from logger.logger_config import setup_logger

# Set up logger
logger = setup_logger()


class GeminiNewsProcessor:
    """
    A class to process news articles and analyze their relevance for engineering students and recent graduates.

    This class filters articles based on their publication date, sends them to the Gemini AI API for analysis,
    and saves the filtered results in a JSON file.

    Attributes:
        input_file (str): Path to the input JSON file containing articles.
        output_file (str): Path to the output JSON file for saving filtered articles.
        gemini_api_key (str): API key for accessing the Gemini AI API.
        gemini_endpoint (str): Endpoint URL for the Gemini AI API.
        days (int): Number of days to filter articles based on their publication date.
    """

    def __init__(
        self, input_file: str, output_file: str, gemini_api_key: str, days: int = 1
    ):
        """
        Initialize the GeminiNewsProcessor class.

        Args:
            input_file (str): Path to the input JSON file containing articles.
            output_file (str): Path to the output JSON file for saving filtered articles.
            gemini_api_key (str): API key for accessing the Gemini AI API.
            days (int): Number of days to filter articles based on their publication date. Default is 1.
        """
        self.input_file = input_file
        self.output_file = output_file
        self.gemini_api_key = gemini_api_key
        self.gemini_endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={self.gemini_api_key}"
        self.days = days

    async def load_data(self) -> list:
        """
        Load articles from the input JSON file.

        Returns:
            list: A list of articles loaded from the input file.

        Raises:
            FileNotFoundError: If the input file is not found.
            json.JSONDecodeError: If the input file contains invalid JSON.
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

    def filter_recent_articles(self, articles: list) -> list:
        """
        Filter articles published within the configurable time frame.

        Args:
            articles (list): List of articles to filter.

        Returns:
            list: A list of articles published within the last `self.days` days.
        """
        now = datetime.now(timezone.utc)
        time_threshold = now - timedelta(days=self.days)
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
            f"Found {len(recent_articles)} articles published in the last {self.days} days."
        )
        return recent_articles

    async def analyze_titles(
        self, session: aiohttp.ClientSession, articles: list
    ) -> list:
        """
        Send titles and URLs to Gemini AI for analysis and ranking.

        Args:
            session (aiohttp.ClientSession): The session used to make the request.
            articles (list): List of dictionaries containing titles and URLs.

        Returns:
            list: Top 10 titles in the specified format.

        Raises:
            aiohttp.ClientError: If the request to the Gemini API fails.
            json.JSONDecodeError: If the response from Gemini cannot be parsed.
        """
        # Prepare prompt text
        prompt_text = """
        Analyze the provided list of titles and URLs and identify the top 10 most relevant ones for engineering students and recent graduates, focusing on their career development, educational growth, and future opportunities. Consider factors such as industry trends, employability, skills advancement, and emerging technologies in engineering.

        Present your selection in the following JSON format:
        [{"title": "Short and Attractive Title", "url": "Original URL"}]
        """
        prompt_text += "\n".join(
            [
                f"Title: {article['title']}\nURL: {article['url']}"
                for article in articles
            ]
        )

        # Create request payload
        data = {"contents": [{"parts": [{"text": prompt_text}]}]}
        headers = {"Content-Type": "application/json"}

        try:
            async with session.post(
                self.gemini_endpoint, json=data, headers=headers
            ) as response:
                logger.debug(f"Sending prompt to Gemini with status: {response.status}")
                response.raise_for_status()
                result = await response.json()
                logger.debug(f"Full response from Gemini: {result}")
                logger.info("Received response from Gemini.")

                # Extract and parse the JSON-like content from the response
                raw_text = (
                    result.get("candidates", [{}])[0]
                    .get("content", {})
                    .get("parts", [{}])[0]
                    .get("text", "")
                )
                logger.debug(f"Raw text from Gemini: {raw_text}")

                try:
                    # Clean up the raw text using regex to remove unexpected characters
                    cleaned_text = re.sub(r"```json|```", "", raw_text).strip()
                    parsed_data = json.loads(cleaned_text)
                    logger.info(
                        f"Successfully parsed {len(parsed_data)} articles from Gemini response."
                    )
                    return parsed_data
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON from Gemini response: {e}")
                    return []
        except aiohttp.ClientError as e:
            logger.error(f"Request to Gemini API failed: {e}")
            return []

    async def process_articles(self, articles: list) -> list:
        """
        Process articles and generate filtered JSON.

        Args:
            articles (list): List of articles to process.

        Returns:
            list: A list of filtered articles in the specified format.
        """
        recent_articles = self.filter_recent_articles(articles)
        if not recent_articles:
            logger.warning(
                "No articles found published within the specified time frame."
            )
            return [
                {
                    "message": "No articles found published within the last {self.days} days."
                }
            ]

        async with aiohttp.ClientSession() as session:
            top_titles = await self.analyze_titles(session, recent_articles)
            logger.info(f"Filtered {len(top_titles)} articles.")
            return top_titles

        async with aiohttp.ClientSession() as session:
            top_titles = await self.analyze_titles(session, recent_articles)
            filtered_articles = [
                {"title": title["title"], "url": title["url"]} for title in top_titles
            ]
            logger.info(f"Filtered {len(filtered_articles)} articles.")
            return filtered_articles

    async def save_data(self, articles: list):
        """
        Save filtered articles to the output JSON file.

        Args:
            articles (list): List of filtered articles to save.

        Raises:
            Exception: If an error occurs while saving the data.
        """
        try:
            with open(self.output_file, "w") as file:
                json.dump(articles, file, indent=4)
            logger.info(
                f"Saved {len(articles)} filtered articles to {self.output_file}."
            )
        except Exception as e:
            logger.error(f"Error saving data to {self.output_file}: {e}")
            raise


async def main():
    """
    Main function to execute the processing pipeline.

    Steps:
        1. Load articles from the input file.
        2. Filter articles based on publication date.
        3. Analyze titles using Gemini AI.
        4. Save filtered articles to the output file.

    Raises:
        ValueError: If the Gemini API key is not set.
        Exception: If an unexpected error occurs during processing.
    """
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        logger.critical(
            "Gemini API key not found. Please set the GEMINI_API_KEY environment variable."
        )
        raise ValueError(
            "Gemini API key not found. Please set the GEMINI_API_KEY environment variable."
        )

    processor = GeminiNewsProcessor(
        "latest_news.json", "filtered_news.json", GEMINI_API_KEY, days=2
    )
    try:
        articles = await processor.load_data()
        filtered_articles = await processor.process_articles(articles)
        await processor.save_data(filtered_articles)
        logger.info(
            f"Processing completed successfully. Filtered {len(filtered_articles)} articles."
        )
    except Exception as e:
        logger.critical(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    asyncio.run(main())
