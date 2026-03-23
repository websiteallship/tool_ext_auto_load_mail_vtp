"""
Handler Base — Abstract base class and data models for email handlers.

Each handler encapsulates the extraction logic for a specific email provider
(e.g., Viettel Post, J&T Express). Handlers define:
- DEFAULT_CONFIG: data-driven extraction patterns (editable via JSON)
- Override methods for special logic (HTML→xlsx, follow redirects)

Skills applied: 04_architecture, 08_clean-code
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from bs4 import BeautifulSoup

if TYPE_CHECKING:
    from src.models import Attachment

logger = logging.getLogger("email_auto_download.handlers")


# ============================================================================
# ExtractionConfig — Tầng 1: Data-driven config, editable in JSON
# ============================================================================

@dataclass
class ExtractionConfig:
    """Data-driven config — editable in rules.json, no code change needed.

    When a provider updates their email template (new domain, new link text),
    only this config needs to change. No code modification required.
    """

    # Link extraction patterns
    link_text_patterns: list[str] = field(default_factory=list)
    link_url_patterns: list[str] = field(default_factory=list)
    allowed_domains: list[str] = field(default_factory=list)

    # Attachment filter
    attachment_extensions: list[str] = field(
        default_factory=lambda: [".pdf", ".xml", ".xlsx", ".zip"]
    )

    # Behavior flags
    download_attachments: bool = True
    download_links: bool = True
    follow_redirects: bool = False

    def merge(self, overrides: dict | None) -> ExtractionConfig:
        """Create a new config with overrides applied (shallow merge).

        This allows rules.json to override specific fields while keeping
        handler defaults for unspecified fields.
        """
        if not overrides:
            return self

        import dataclasses
        current = dataclasses.asdict(self)
        current.update(overrides)
        return ExtractionConfig(**current)


# ============================================================================
# DownloadTarget — What the handler wants to download
# ============================================================================

@dataclass
class DownloadTarget:
    """A file that the handler identified for download."""

    url: str
    filename_hint: str = ""
    target_type: str = "link"       # "link" | "attachment"
    context: str = ""               # descriptive label for logging


# ============================================================================
# BaseEmailHandler — Tầng 2: Override for special logic
# ============================================================================

class BaseEmailHandler(ABC):
    """Abstract base class for email handlers.

    Each provider (Viettel Post, J&T, GHN...) has a handler that:
    1. Declares DEFAULT_CONFIG with extraction patterns
    2. Overrides methods only for special logic (e.g., HTML→xlsx, redirect)

    The generic handler provides sensible defaults for simple cases.
    """

    # ── Display metadata (for GUI) ────────────────────────────────────
    handler_type: str = "base"
    display_name: str = "Base Handler"
    description: str = ""
    icon: str = "📧"
    file_types: str = ""

    # ── Default extraction config ─────────────────────────────────────
    DEFAULT_CONFIG: ExtractionConfig = ExtractionConfig()

    def resolve_config(self, overrides: dict | None = None) -> ExtractionConfig:
        """Merge handler defaults with rule-level overrides."""
        return self.DEFAULT_CONFIG.merge(overrides)

    # ── Methods handlers can override ─────────────────────────────────

    def extract_download_links(
        self,
        html_body: str,
        config: ExtractionConfig,
    ) -> list[DownloadTarget]:
        """Find downloadable links in email body using config patterns.

        Default implementation: match by link_text_patterns + link_url_patterns.
        Override for special logic (e.g., parsing link context to distinguish
        PDF vs XML downloads, following redirects).

        Args:
            html_body: Raw HTML body of the email
            config: Resolved extraction config (defaults + overrides)

        Returns:
            List of DownloadTarget objects
        """
        if not html_body or not config.download_links:
            return []

        if not config.link_text_patterns and not config.link_url_patterns:
            return []

        soup = BeautifulSoup(html_body, "lxml")
        targets: list[DownloadTarget] = []

        for anchor in soup.find_all("a", href=True):
            url = anchor.get("href", "").strip()
            text = anchor.get_text(strip=True).lower()

            if not url or url.startswith("mailto:"):
                continue

            # Match by link text patterns
            text_match = any(
                p.lower() in text for p in config.link_text_patterns
            )

            # Match by URL patterns
            url_match = any(
                p.lower() in url.lower() for p in config.link_url_patterns
            )

            if text_match or url_match:
                targets.append(DownloadTarget(
                    url=url,
                    filename_hint="",
                    context=anchor.get_text(strip=True)[:60],
                ))

        logger.debug(f"[{self.handler_type}] Found {len(targets)} download targets")
        return targets

    def filter_attachments(
        self,
        attachments: list[Attachment],
        config: ExtractionConfig,
    ) -> list[Attachment]:
        """Filter attachments by config (extension whitelist).

        Default: filter by attachment_extensions in config.
        Override for special filter logic (e.g., filename pattern matching).
        """
        if not config.download_attachments:
            return []

        if not config.attachment_extensions:
            return list(attachments)  # no filter = all attachments

        from pathlib import Path
        return [
            att for att in attachments
            if Path(att.filename).suffix.lower() in config.attachment_extensions
        ]

    def get_download_filename(
        self,
        email_subject: str,
        original_filename: str,
        html_body: str | None = None,
    ) -> str:
        """Generate a meaningful filename for downloads.

        Default: use original filename. Override to generate names
        from invoice numbers etc.
        """
        return original_filename
