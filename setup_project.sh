#!/bin/bash

# Define the root project directory
PROJECT_DIR="ai-driven-smart-news"

# Create the project root directory
mkdir -p $PROJECT_DIR

# Navigate into the project directory
cd $PROJECT_DIR

# Create the necessary directories
mkdir -p logger configs core tests utils .github/workflows

# Create the __init__.py files
touch logger/__init__.py
touch configs/__init__.py
touch core/__init__.py
touch tests/__init__.py
touch utils/__init__.py

# Create the Python files inside each folder

# logger/logger_config.py
touch logger/logger_config.py

# configs/api_config.json
touch configs/api_config.json

# configs/discord_config.json
touch configs/discord_config.json

# core/api_handler.py
touch core/api_handler.py

# core/news_processor.py
touch core/news_processor.py

# core/discord_poster.py
touch core/discord_poster.py

# utils/helpers.py
touch utils/helpers.py

# tests/test_api_handler.py
touch tests/test_api_handler.py

# tests/test_news_processor.py
touch tests/test_news_processor.py

# tests/test_discord_poster.py
touch tests/test_discord_poster.py

# .github/workflows/ci.yml
touch .github/workflows/ci.yml

# .gitignore
touch .gitignore

# requirements.txt
touch requirements.txt

# README.md
touch README.md

# setup.py
touch setup.py

# main.py
touch main.py

echo "Project structure created successfully."
