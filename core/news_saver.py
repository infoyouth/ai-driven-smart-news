"""
news_saver.py
-------------
This module is responsible for saving fetched news articles to JSON files.
It ensures that the data is properly serialized and saved to the specified
output file.

The `NewsSaver` class provides a static method to save news articles, making
it reusable across different parts of the application.

Author: infoyouth
Date: 2025-06-08
"""
import json
from typing import List, Dict
from logger.logger_config import setup_logger

logger = setup_logger()


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
    OUTPUT_FILE = "test_news.json"
    test_news = [
        {"title": "Sample News", "description": "This is a test news article."}
    ]
    try:
        NewsSaver.save_news_to_file(test_news, OUTPUT_FILE)
        logger.info("News saved successfully.")
    except Exception as e:
        logger.error(f"Error: {e}")
