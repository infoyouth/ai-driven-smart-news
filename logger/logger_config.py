"""
This module sets up logging configuration, including colorized
output for console logging and rotating file handlers for log
persistence.
"""

import logging
from logging.handlers import RotatingFileHandler
import os
import colorlog

LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")
LOG_FILE = os.getenv("LOG_FILE", "app.log")
LOG_FILE_SIZE = max(int(os.getenv("LOG_FILE_SIZE", "10485760")), 1)
LOG_BACKUP_COUNT = max(int(os.getenv("LOG_BACKUP_COUNT", "5")), 1)


def setup_logger(
    log_level: str = LOG_LEVEL,
    log_file: str = LOG_FILE,
    log_file_size: int = LOG_FILE_SIZE,
    log_backup_count: int = LOG_BACKUP_COUNT,
) -> logging.Logger:
    """
    Set up and return a colorized logger with rotating file handler.

    Args:
        log_level (str): Logging level (e.g., DEBUG, INFO).
        log_file (str): Path to the log file.
        log_file_size (int): Maximum size of the log file in bytes.
        log_backup_count (int): Number of backup log files to keep.

    Returns:
        logging.Logger: Configured logger instance.
    """
    log = logging.getLogger(__name__)

    if not log.hasHandlers():
        log.setLevel(log_level)

        formatter = colorlog.ColoredFormatter(
            fmt=(
                "%(asctime)s - "
                "%(log_color)s%(levelname)-8s%(reset)s - "
                "%(filename)s - "
                "%(message)s (Line: %(lineno)d)"
            ),
            datefmt="%Y-%m-%d %H:%M:%S",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold_red",
            },
        )
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)

        file_handler = RotatingFileHandler(
            log_file, maxBytes=log_file_size, backupCount=log_backup_count
        )
        file_handler.setFormatter(formatter)

        log.addHandler(stream_handler)
        log.addHandler(file_handler)

        log.propagate = False

    return log


def get_logger(name: str = __name__) -> logging.Logger:
    """Get the configured logger."""
    return logging.getLogger(name)


# Default logger instance
DEFAULT_LOGGER = setup_logger()

# Example usage
if __name__ == "__main__":
    logger = DEFAULT_LOGGER
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
