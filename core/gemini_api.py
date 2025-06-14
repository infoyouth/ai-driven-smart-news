"""
Gemini API Module

Contains the GeminiApiClient class for interacting with the Gemini AI API.
Can be run directly for a minimal connectivity test.

Author: infoyouth
Date: 2025-06-08
"""

import aiohttp
import json
import re
from typing import List, Dict, Any
from logger.logger_config import setup_logger

logger = setup_logger()


class GeminiApiClient:
    """
    Client for sending requests to the Gemini AI API and parsing responses.
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.endpoint = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            "gemini-2.0-flash-exp:generateContent?key=" + self.api_key
        )

    async def analyze_titles(
        self, session: aiohttp.ClientSession, articles: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """
        Analyzes article titles and URLs with the Gemini API.

        Args:
            session: The aiohttp session.
            articles: List of articles with 'title' and 'url'.

        Returns:
            The top 10 articles in the required format.
        """
        prompt_text = (
            "Analyze the provided list of titles and URLs and select the top 10 most "
            "relevant for engineering students and recent graduates, focusing on their "
            "career development, educational growth, and future opportunities. "
            "Only reply with your selection as a JSON array, with no explanation or "
            "additional text. "
            'Format: [{"title": "Short and Attractive Title", "url": "Original URL"}]'
        )
        prompt_text += "\n".join(
            [
                f"Title: {article['title']}\nURL: {article['url']}"
                for article in articles
            ]
        )
        data = {"contents": [{"parts": [{"text": prompt_text}]}]}
        headers = {"Content-Type": "application/json"}

        try:
            async with session.post(
                self.endpoint, json=data, headers=headers
            ) as response:
                logger.debug(
                    f"Sent prompt to Gemini API, response status: {response.status}"
                )
                response.raise_for_status()
                result = await response.json()
                logger.debug(f"Response from Gemini API: {result}")
                return self._parse_gemini_response(result)
        except aiohttp.ClientError as exc:
            logger.error(f"Request to Gemini API failed: {exc}")
            return []

    async def enrich_articles(
        self, session: aiohttp.ClientSession, articles: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """
        Uses Gemini to assign a topic, emoji, and summary to each article.

        Args:
            session: The aiohttp session.
            articles: List of articles with 'title' and 'url'.

        Returns:
            List of dicts with title, url, topic, emoji, and summary.
        """
        prompt = (
            "For each news article below, do the following:\n"
            "- Assign a topic from [Space, AI, Politics, Health, Science, Tech,\n"
            "Other].- Suggest an appropriate emoji for that topic.\n"
            "- Write a concise 1-sentence summary.\n"
            "Reply as a JSON list, where each item is:\n"
            '{"title": "...", "url": "...", "topic": "...",\n'
            ' "emoji": "...", "summary": "..."}\n'
        )
        prompt += "\n".join([f'Title: {a["title"]}\nURL: {a["url"]}' for a in articles])

        data = {"contents": [{"parts": [{"text": prompt}]}]}
        headers = {"Content-Type": "application/json"}

        try:
            async with session.post(
                self.endpoint, json=data, headers=headers
            ) as response:
                logger.debug(
                    "Sent enrich prompt to Gemini API, "
                    f"response status: {response.status}"
                )
                response.raise_for_status()
                result = await response.json()
                logger.debug(f"Response from Gemini API: {result}")
                return self._parse_gemini_response(result)
        except aiohttp.ClientError as exc:
            logger.error(f"Request to Gemini API failed: {exc}")
            return []

    @staticmethod
    def _parse_gemini_response(result: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Parses the Gemini API response, extracting the relevant articles.

        Args:
            result: The JSON response from the Gemini API.

        Returns:
            A list of articles.
        """
        raw_text = (
            result.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
        )
        logger.debug(f"Raw text from Gemini: {raw_text}")
        try:
            cleaned_text = re.sub(r"```json|```", "", raw_text).strip()
            parsed_data = json.loads(cleaned_text)
            logger.info(
                f"Successfully parsed {len(parsed_data)} articles from Gemini response."
            )
            return parsed_data
        except json.JSONDecodeError as exc:
            logger.error(f"Failed to parse JSON from Gemini response: {exc}")
            return []


if __name__ == "__main__":
    import asyncio
    import os

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Please set the GEMINI_API_KEY environment variable.")
    else:

        async def test():
            async with aiohttp.ClientSession() as session:
                client = GeminiApiClient(api_key)
                # Demo with fake article
                articles = [{"title": "Sample", "url": "http://example.com"}]
                result = await client.analyze_titles(session, articles)
                print("Result:", result)

        asyncio.run(test())
