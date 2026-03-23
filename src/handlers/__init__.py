"""
Handler package — Auto-register and factory for email handlers.

Usage:
    from src.handlers import get_handler, HANDLER_REGISTRY, get_all_handler_types

    handler = get_handler("viettel_post")  # returns ViettelPostHandler()
    handler = get_handler("unknown")       # falls back to GenericHandler()

Skills applied: 04_architecture, 08_clean-code
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.handlers.registry import HANDLER_REGISTRY, register  # noqa: F401

if TYPE_CHECKING:
    from src.handlers.base import BaseEmailHandler

logger = logging.getLogger("email_auto_download.handlers")


def get_handler(handler_type: str) -> BaseEmailHandler:
    """Get a handler instance by type string.

    Falls back to GenericHandler if handler_type is not found.
    """
    cls = HANDLER_REGISTRY.get(handler_type)
    if cls is None:
        logger.warning(
            f"Handler '{handler_type}' not found, falling back to 'generic'"
        )
        cls = HANDLER_REGISTRY.get("generic")
        if cls is None:
            raise ValueError("GenericHandler not registered. Import handlers first.")
    return cls()


def get_all_handler_types() -> list[dict]:
    """Get list of all registered handler types with metadata.

    Returns list of dicts with: handler_type, display_name, description, icon, file_types
    """
    result = []
    for htype, cls in HANDLER_REGISTRY.items():
        instance = cls()
        result.append({
            "handler_type": htype,
            "display_name": instance.display_name,
            "description": instance.description,
            "icon": instance.icon,
            "file_types": instance.file_types,
        })
    return result


# ── Import all handlers to trigger @register decorators ──────────────
# Order matters: generic first (fallback), then specific handlers

from src.handlers.generic import GenericHandler          # noqa: F401, E402
from src.handlers.viettel_post import ViettelPostHandler  # noqa: F401, E402
from src.handlers.jt_express import (                     # noqa: F401, E402
    JTInvoiceHandler,
    JTCODHandler,
)
