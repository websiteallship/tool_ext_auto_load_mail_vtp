"""
Handler Registry — Registration mechanism for email handlers.

This is separated from __init__.py to avoid circular imports.
Handler modules import `register` from here, and __init__.py
imports handlers after defining the factory functions.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.handlers.base import BaseEmailHandler

logger = logging.getLogger("email_auto_download.handlers")

# Global registry: handler_type → handler class
HANDLER_REGISTRY: dict[str, type[BaseEmailHandler]] = {}


def register(handler_type: str):
    """Decorator to register a handler class.

    Usage:
        @register("viettel_post")
        class ViettelPostHandler(BaseEmailHandler):
            ...
    """
    def decorator(cls):
        HANDLER_REGISTRY[handler_type] = cls
        cls.handler_type = handler_type
        logger.debug(f"Registered handler: {handler_type} → {cls.__name__}")
        return cls
    return decorator
