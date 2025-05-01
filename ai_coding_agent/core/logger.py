"""Logging configuration for AI Coding Agent.

This module provides a consistent logging configuration across the application.
"""

import logging
import os
from typing import Any

import json_log_formatter
from langchain.globals import set_debug, set_verbose


class CustomJSONFormatter(json_log_formatter.JSONFormatter):
    """Custom JSON log formatter for logging."""

    def json_record(
        self, message: str, extra: dict[str, Any], record: logging.LogRecord
    ) -> dict[str, Any]:
        """Record a log message in JSON format."""
        extra["timestamp"] = self.formatTime(record, self.datefmt)
        extra["level"] = record.levelname
        extra["name"] = record.name
        extra["lineno"] = record.lineno
        extra["message"] = message
        extra["function_name"] = record.funcName
        extra["module"] = record.module
        extra["args"] = record.args
        return extra

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as a JSON string."""
        message = record.getMessage()
        record_dict = self.json_record(message, record.__dict__, record)
        return self.to_json(record_dict)


def setup_logging(level: int = logging.INFO, log_filename: str = "app.log") -> None:
    """Set up logging configuration for the entire application.

    This should be called once at application startup.

    Args:
        level: The logging level to use. Defaults to INFO.
        log_filename: The filename for the log file.
    """
    set_verbose(True)
    set_debug(True)

    # Configure root logger
    root_logger = logging.getLogger()

    # Remove any existing handlers to ensure consistent configuration
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add our handler
    log_dir = "logs/logs"
    os.makedirs(log_dir, exist_ok=True)
    log_filename = os.path.join(log_dir, log_filename)
    handler = logging.FileHandler(log_filename)
    formatter = CustomJSONFormatter()
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    root_logger.setLevel(level)

    # Set our own loggers to DEBUG by default for more visibility
    logging.getLogger("ai_coding_agent").setLevel(logging.DEBUG)

    # Silence third-party loggers
    silence_third_party_loggers()


def silence_third_party_loggers():
    """Silence third-party loggers to reduce noise."""
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("pytest").setLevel(logging.WARNING)
    logging.getLogger("pytest_asyncio").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("langchain").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpcore.http11").setLevel(logging.WARNING)
    logging.getLogger("httpcore._backends").setLevel(logging.WARNING)
    logging.getLogger("httpcore._exceptions").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("aiofiles").setLevel(logging.WARNING)
    logging.getLogger("_pytest").setLevel(logging.WARNING)


def get_logger(
    name: str, level: int | None = None, log_filename: str = "app.log"
) -> logging.Logger:
    """Get a logger with consistent configuration.

    Args:
        name: The name of the logger, typically __name__
        level: Optional specific level for this logger
        log_filename: The filename for the log file.

    Returns:
        A configured logger instance
    """
    setup_logging(
        level=level if level is not None else logging.DEBUG, log_filename=log_filename
    )
    logger = logging.getLogger(name)

    return logger
