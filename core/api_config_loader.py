"""
api_config_loader.py
---------------------
This module is responsible for loading and validating API configuration
from a JSON file. It ensures that API keys are securely loaded from
environment variables and validates the presence of required fields.

The `APIConfigLoader` class provides methods to load the configuration
and retrieve specific source configurations by name.

Author: infoyouth
Date: 2025-06-08
"""
import os
import json
from typing import Optional, Dict
from logger.logger_config import setup_logger

logger = setup_logger()


class APIConfigLoader:
    """
    Handles loading and validation of API configuration.

    Attributes:
        config_path (str): Path to the configuration file.
        config (dict): Loaded configuration data.
    """

    def __init__(self, config_path: str):
        """
        Initialize the APIConfigLoader.

        Args:
            config_path (str): Path to the configuration file.
        """
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> dict:
        """
        Load API configuration from a JSON file.

        Returns:
            dict: Parsed configuration data.

        Raises:
            FileNotFoundError: If the configuration file is not found.
            json.JSONDecodeError: If the configuration file is not valid JSON.
            ValueError: If an API key is missing for a source.
        """
        try:
            with open(self.config_path, "r") as file:
                config = json.load(file)
                for source in config["sources"]:
                    if source.get("api_key_env"):
                        source["api_key"] = os.getenv(source["api_key_env"])
                        if not source["api_key"]:
                            logger.error(f"API key not found for source: {source['name']}")
                            raise ValueError(f"API key missing for source: {source['name']}")
                        logger.debug(f"Loaded API key for {source['name']}: {source['api_key']}")
                logger.info("API configuration loaded successfully.")
                return config
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {self.config_path}")
            raise
        except json.JSONDecodeError:
            logger.error(f"Error decoding JSON configuration file: {self.config_path}")
            raise

    def get_source(self, source_name: str) -> Optional[dict]:
        """
        Retrieve a specific source configuration by name.

        Args:
            source_name (str): Name of the source.

        Returns:
            dict: Source configuration if found, otherwise None.
        """
        return next((s for s in self.config["sources"] if s["name"] == source_name), None)
    
if __name__ == "__main__":
    CONFIG_PATH = "configs/api_config.json"
    try:
        loader = APIConfigLoader(CONFIG_PATH)
        source = loader.get_source("NewsAPI")
        logger.info(f"Loaded source configuration: {source}")
    except Exception as e:
        logger.error(f"Error: {e}")