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
LOG_FILE_SIZE = int(os.getenv("LOG_FILE_SIZE", "10485760"))  # Default is 10 MB (as string)
LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "5"))  # Default is 5 (as string)

def setup_logger(log_level=LOG_LEVEL):
    """Set up and return a colorized logger with rotating file handler."""
    log = logging.getLogger(__name__)  # Renamed variable from `logger` to `log`

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
            }
        )
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)

        file_handler = RotatingFileHandler(
            LOG_FILE, maxBytes=LOG_FILE_SIZE, backupCount=LOG_BACKUP_COUNT
        )
        file_handler.setFormatter(formatter)

        log.addHandler(stream_handler)
        log.addHandler(file_handler)

        log.propagate = False

    return log

def get_logger(name=__name__):
    """Get the configured logger."""
    return logging.getLogger(name)


# Example usage
if __name__ == "__main__":
    logger = setup_logger()
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
