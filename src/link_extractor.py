"""
Link Extractor — Parse HTML email body to extract links.

Extracts:
- "Chi tiết bảng kê" links (Viettel Post invoice details)
- Invoice numbers (K26TAN...)
- Secret codes (mã số bí mật)
- All anchor links from email HTML

Skills applied: 03_web-scraper, 08_clean-code
"""

from __future__ import annotations

import logging
import re

from bs4 import BeautifulSoup

from src.models import ExtractedLink

logger = logging.getLogger("email_auto_download.link_extractor")

# Regex patterns
INVOICE_PATTERN = re.compile(r"K\d{2}TAN\d+")
SECRET_CODE_PATTERN = re.compile(
    r"mã\s+số\s+bí\s+mật\s+([A-Z0-9]+)", re.IGNORECASE
)
TAX_CODE_PATTERN = re.compile(r"\b(\d{10}(?:\d{3})?)\b")


class LinkExtractor:
    """
    Extract links and data from email HTML body.

    Single Responsibility: ONLY parses HTML and extracts data.
    Does NOT download anything.
    """

    BANG_KE_PATTERNS: list[str] = [
        "chi tiết bảng kê",
        "chi tiet bang ke",
        "bảng kê chi tiết",
        "bang ke chi tiet",
        "chi tiết",  # shorter form sometimes used
        "xem chi tiết",
    ]

    # URL patterns that indicate a direct bang_ke download link
    BANG_KE_URL_PATTERNS: list[str] = [
        "bang-ke-hoa-don-chi-tiet.do",
        "bangkechitiet",
        "bang-ke-chi-tiet",
    ]

    INVOICE_SEARCH_DOMAINS: list[str] = [
        "vinvoice.viettel.vn",
        "s1.viettelpost.vn",
        "viettelpost.vn",
    ]

    def extract_all_links(self, html_body: str) -> list[ExtractedLink]:
        """
        Extract all anchor links from HTML body.

        Args:
            html_body: Raw HTML string from email

        Returns:
            List of ExtractedLink objects with classified link_type
        """
        if not html_body:
            return []

        soup = BeautifulSoup(html_body, "lxml")
        links: list[ExtractedLink] = []

        for anchor in soup.find_all("a", href=True):
            url = anchor["href"].strip()
            text = anchor.get_text(strip=True)

            if not url or url.startswith("mailto:"):
                continue

            link_type = self._classify_link(url, text)
            links.append(ExtractedLink(url=url, text=text, link_type=link_type))

        logger.debug(f"Extracted {len(links)} links from HTML body")
        return links

    def extract_bang_ke_link(self, html_body: str) -> str | None:
        """
        Find the "chi tiết bảng kê" link from email body.

        Matches by:
        1. Anchor text matching BANG_KE_PATTERNS
        2. Href URL matching BANG_KE_URL_PATTERNS (for any link text)
        """
        if not html_body:
            return None

        soup = BeautifulSoup(html_body, "lxml")

        for anchor in soup.find_all("a", href=True):
            url = anchor["href"].strip()
            link_text = anchor.get_text(strip=True).lower()

            # Match by link text
            if self._is_bang_ke_text(link_text):
                logger.info(f"Found bảng kê link (by text): {url}")
                return url

            # Match by URL pattern (direct .do download links)
            if self._is_bang_ke_url(url):
                logger.info(f"Found bảng kê link (by URL pattern): {url}")
                return url

        logger.debug("No bảng kê link found in email body")
        return None

    def extract_invoice_number(self, html_body: str) -> str | None:
        """
        Extract invoice number (e.g. K26TAN2038744) from HTML body.

        Args:
            html_body: Raw HTML string or plain text

        Returns:
            Invoice number string or None
        """
        if not html_body:
            return None

        text = self._html_to_text(html_body)
        match = INVOICE_PATTERN.search(text)
        if match:
            invoice = match.group(0)
            logger.debug(f"Found invoice number: {invoice}")
            return invoice
        return None

    def extract_secret_code(self, html_body: str) -> str | None:
        """
        Extract secret code (mã số bí mật) from email body.
        Example: "mã số bí mật 3T5XD00AWF2BQ09"

        Args:
            html_body: Raw HTML string or plain text

        Returns:
            Secret code string or None
        """
        if not html_body:
            return None

        text = self._html_to_text(html_body)
        match = SECRET_CODE_PATTERN.search(text)
        if match:
            code = match.group(1)
            logger.debug(f"Found secret code: {code[:4]}***")
            return code
        return None

    def extract_tax_code(self, html_body: str) -> str | None:
        """
        Extract tax code (MST) from email body.
        Example: "mã số thuế bên bán 0104093672"

        Args:
            html_body: Raw HTML string or plain text

        Returns:
            Tax code string or None
        """
        if not html_body:
            return None

        text = self._html_to_text(html_body)

        # Look for tax code near keyword "mã số thuế"
        tax_context = re.search(
            r"mã\s+số\s+thuế[^\d]*(\d{10}(?:\d{3})?)",
            text,
            re.IGNORECASE,
        )
        if tax_context:
            return tax_context.group(1)

        return None

    # ── Private helpers ──────────────────────────────────────────────

    def _is_bang_ke_text(self, text: str) -> bool:
        """Check if link text matches bảng kê patterns."""
        text_lower = text.lower()
        return any(pattern in text_lower for pattern in self.BANG_KE_PATTERNS)

    def _is_bang_ke_url(self, url: str) -> bool:
        """Check if URL matches a known direct bảng kê download pattern."""
        url_lower = url.lower()
        return any(pattern in url_lower for pattern in self.BANG_KE_URL_PATTERNS)

    def _classify_link(self, url: str, text: str) -> str:
        """Classify a link as bang_ke, invoice_search, or other."""
        if self._is_bang_ke_text(text):
            return "bang_ke"
        if any(domain in url for domain in self.INVOICE_SEARCH_DOMAINS):
            return "invoice_search"
        return "other"

    def _html_to_text(self, html: str) -> str:
        """Convert HTML to plain text."""
        soup = BeautifulSoup(html, "lxml")
        return soup.get_text(separator=" ", strip=True)
