"""
Structured logging configuration using structlog.

Provides consistent, structured logging across the entire application.
"""

from __future__ import annotations

import logging
import sys
from typing import Any

import structlog

from src.utils.config import get_settings


def setup_logging() -> None:
    """
    Configure structured logging for the application.

    Sets up structlog with JSON output in production and colored console output
    in development.
    """
    settings = get_settings()

    # Determine log level
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    # Configure structlog
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    # Add different renderers based on environment
    if settings.environment == "production":
        # JSON output for production
        processors.append(structlog.processors.JSONRenderer())
    else:
        # Pretty colored output for development
        processors.append(structlog.dev.ConsoleRenderer(colors=True))

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str, **initial_context: Any) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (typically __name__ of the module)
        **initial_context: Initial context to bind to logger

    Returns:
        Configured structlog logger

    Example:
        ```python
        logger = get_logger(__name__, agent_id="agent_123")
        logger.info("agent_action", action="read_paper", paper_id="arxiv:1234")
        ```
    """
    logger = structlog.get_logger(name)
    if initial_context:
        logger = logger.bind(**initial_context)
    return logger


class LoggerAdapter:
    """
    Adapter for adding structured logging to classes.

    Usage:
        class MyClass:
            def __init__(self):
                self.logger = LoggerAdapter(self, agent_id=self.agent_id)

            def do_something(self):
                self.logger.info("doing_something", detail="value")
    """

    def __init__(self, obj: object, **context: Any):
        """
        Initialize logger adapter.

        Args:
            obj: Object to create logger for (uses __class__.__name__)
            **context: Initial context to bind
        """
        self._logger = get_logger(obj.__class__.__name__, **context)

    def bind(self, **new_context: Any) -> LoggerAdapter:
        """Bind additional context and return new adapter."""
        self._logger = self._logger.bind(**new_context)
        return self

    def debug(self, event: str, **kwargs: Any) -> None:
        """Log debug message."""
        self._logger.debug(event, **kwargs)

    def info(self, event: str, **kwargs: Any) -> None:
        """Log info message."""
        self._logger.info(event, **kwargs)

    def warning(self, event: str, **kwargs: Any) -> None:
        """Log warning message."""
        self._logger.warning(event, **kwargs)

    def error(self, event: str, **kwargs: Any) -> None:
        """Log error message."""
        self._logger.error(event, **kwargs)

    def exception(self, event: str, **kwargs: Any) -> None:
        """Log exception with traceback."""
        self._logger.exception(event, **kwargs)


# Initialize logging on module import
setup_logging()
