"""
Generic Handler — Default handler for simple email rules.

Handles:
- Download attachments filtered by extension
- Extract links by text/URL patterns
- No special logic (no redirects, no HTML→xlsx)

Used when a rule does not specify a handler_type, or the handler_type is "generic".
"""

from __future__ import annotations

from src.handlers.registry import register
from src.handlers.base import BaseEmailHandler, ExtractionConfig


@register("generic")
class GenericHandler(BaseEmailHandler):
    """Default handler — uses config patterns directly, no special logic."""

    display_name = "Generic"
    description = "Handler cơ bản — tải attachment + link theo pattern"
    icon = "📧"
    file_types = "📎 theo filter extension"

    DEFAULT_CONFIG = ExtractionConfig(
        link_text_patterns=[],
        link_url_patterns=[],
        allowed_domains=[],
        attachment_extensions=[".pdf", ".xml", ".xlsx", ".zip"],
        download_attachments=True,
        download_links=False,
    )
