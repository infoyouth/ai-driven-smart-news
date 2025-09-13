"""Small wrapper around the Gemini API client to provide a synchronous
enrichment entrypoint used by `main.py`.

This module intentionally keeps imports minimal so it can be imported in
environments that do not have the full async stack available at import time.
"""
from typing import Any, Dict, List
import asyncio
import os
from logger.logger_config import setup_logger

logger = setup_logger()


async def _enrich_async(api_key: str, articles: List[Dict[str, Any]]):
    # local import to avoid importing aiohttp at module import time
    import aiohttp
    from core.gemini_api import GeminiApiClient

    async with aiohttp.ClientSession() as session:
        client = GeminiApiClient(api_key)
        enriched = await client.enrich_articles(session, articles)
        return enriched


def enrich_articles_sync(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Synchronously enrich articles via Ruby-style asyncio runner.

    Returns the enriched articles if available; otherwise returns the input
    articles unchanged.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.warning("GEMINI_API_KEY not set; skipping enrichment.")
        return articles

    try:
        enriched = asyncio.run(_enrich_async(api_key, articles))
        return enriched or articles
    except Exception as exc:
        logger.error("Gemini enrichment failed: %s", exc)
        return articles
