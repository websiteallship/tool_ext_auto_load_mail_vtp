"""
J&T Express Handlers — Handle J&T (Thuận Phong) invoice and COD emails.

Two handlers:
- JTInvoiceHandler: E-Invoice emails with tracking redirect links → PDF/XML
- JTCODHandler: COD reconciliation emails with .xlsx attachment

Based on email template analysis (March 2026):
- E-Invoice links are wrapped in tracking URLs (url3815.hq.jtexpress.vn)
- Follow 302 redirect → einvoice.fast.com.vn → PDF or XML file
- COD emails have direct .xlsx attachment, no links

Skills applied: 03_web-scraper, 08_clean-code
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from bs4 import BeautifulSoup

from src.handlers.registry import register
from src.handlers.base import BaseEmailHandler, DownloadTarget, ExtractionConfig

if TYPE_CHECKING:
    from src.models import Attachment

logger = logging.getLogger("email_auto_download.handlers.jt_express")


# ============================================================================
# J&T E-Invoice Handler
# ============================================================================

@register("jt_invoice")
class JTInvoiceHandler(BaseEmailHandler):
    """J&T Express E-Invoice — follow tracking redirects to download PDF/XML.

    Email structure:
    - Forwarded from einvoice-084@hq.jtexpress.vn
    - 5 links wrapped in tracking URLs (url3815.hq.jtexpress.vn)
    - Links distinguished by text BEFORE the <a> tag:
        - "Xem bản thể hiện" → PDF (view)
        - "Tải tệp thông tin hóa đơn" → XML (download)
        - "Tải bản thể hiện" → PDF (download)
        - "Tra cứu hóa đơn" → Search page (skip)
        - "Tải bảng kê vận đơn" → Empty href (skip)
    """

    display_name = "J&T Express E-Invoice"
    description = "Hóa đơn điện tử J&T Express (Thuận Phong)"
    icon = "📄"
    file_types = "🔗 .pdf + .xml (qua link redirect)"

    DEFAULT_CONFIG = ExtractionConfig(
        link_text_patterns=["Nhấn vào đây", "click here"],
        link_url_patterns=["einvoice.fast.com.vn"],
        allowed_domains=[
            "einvoice.fast.com.vn",
            "hq.jtexpress.vn",
            "url3815.hq.jtexpress.vn",
        ],
        attachment_extensions=[],
        download_attachments=False,
        download_links=True,
        follow_redirects=True,
    )

    # Text patterns to identify link purpose
    _LINK_CONTEXTS = {
        "tải tệp thông tin hóa đơn": ("xml", "Tải XML hóa đơn"),
        "to download the xml file": ("xml", "Download XML"),
        "tải tệp bản thể hiện": ("pdf", "Tải PDF hóa đơn"),
        "to download the pdf file": ("pdf", "Download PDF"),
    }

    # Patterns to SKIP (not downloadable)
    _SKIP_CONTEXTS = [
        "tra cứu hóa đơn",
        "for more details please access",
        "tải tệp bảng kê vận đơn",  # often has empty href
    ]

    def extract_download_links(
        self,
        html_body: str,
        config: ExtractionConfig,
    ) -> list[DownloadTarget]:
        """Extract download links from J&T E-Invoice email.

        Uses text context BEFORE each <a> tag to distinguish
        XML download vs PDF download vs search page.
        """
        if not html_body or not config.download_links:
            return []

        soup = BeautifulSoup(html_body, "lxml")
        targets: list[DownloadTarget] = []
        seen_types: set[str] = set()  # avoid duplicate PDF downloads

        for anchor in soup.find_all("a", href=True):
            href = anchor.get("href", "").strip()
            if not href or href.startswith("mailto:"):
                continue

            # Get context: text before this anchor in parent
            context_text = self._get_preceding_text(anchor).lower()
            link_text = anchor.get_text(strip=True).lower()

            # Skip non-download links
            if any(skip in context_text for skip in self._SKIP_CONTEXTS):
                continue

            # Identify link purpose from context
            for pattern, (file_type, label) in self._LINK_CONTEXTS.items():
                if pattern in context_text:
                    if file_type not in seen_types:
                        seen_types.add(file_type)
                        targets.append(DownloadTarget(
                            url=href,
                            filename_hint=f"invoice.{file_type}",
                            target_type="link",
                            context=label,
                        ))
                    break

        # Extract invoice number for better filename
        invoice_num = self._extract_jt_invoice_number(html_body)
        serial = self._extract_jt_serial(html_body)
        if invoice_num:
            for target in targets:
                ext = target.filename_hint.split(".")[-1] if "." in target.filename_hint else "pdf"
                prefix = f"{invoice_num}_{serial}" if serial else invoice_num
                target.filename_hint = f"{prefix}.{ext}"

        logger.debug(f"[jt_invoice] Found {len(targets)} download targets")
        return targets

    def _get_preceding_text(self, anchor) -> str:
        """Get text content before this anchor tag in its parent."""
        parts = []
        for sibling in anchor.previous_siblings:
            text = sibling.get_text(strip=True) if hasattr(sibling, "get_text") else str(sibling).strip()
            if text:
                parts.append(text)
            if len(parts) >= 3:  # enough context
                break
        return " ".join(reversed(parts))

    @staticmethod
    def _extract_jt_invoice_number(html_body: str) -> str | None:
        """Extract J&T invoice number from body text.

        Pattern: Số hóa đơn (Invoice Number): <b>31784</b>
        """
        match = re.search(
            r"Số hóa đơn.*?<b>\s*(\d+)\s*</b>",
            html_body,
            re.IGNORECASE | re.DOTALL,
        )
        return match.group(1) if match else None

    @staticmethod
    def _extract_jt_serial(html_body: str) -> str | None:
        """Extract J&T serial number.

        Pattern: Ký hiệu hóa đơn (Serial Number): <b>C26TBH</b>
        """
        match = re.search(
            r"Ký hiệu hóa đơn.*?<b>(\w+)</b>",
            html_body,
            re.IGNORECASE | re.DOTALL,
        )
        return match.group(1) if match else None


# ============================================================================
# J&T COD Handler
# ============================================================================

@register("jt_cod")
class JTCODHandler(BaseEmailHandler):
    """J&T Express COD — download .xlsx attachment only.

    Email structure:
    - Forwarded from coddoisoat251-mn1@hq.jtexpress.vn
    - 1 .xlsx attachment (bảng kê cấn trừ COD ~75KB)
    - No links to process
    """

    display_name = "J&T Express COD"
    description = "Bảng kê đối soát COD J&T Express"
    icon = "📊"
    file_types = "📎 .xlsx"

    DEFAULT_CONFIG = ExtractionConfig(
        link_text_patterns=[],
        link_url_patterns=[],
        allowed_domains=[],
        attachment_extensions=[".xlsx"],
        download_attachments=True,
        download_links=False,
        follow_redirects=False,
    )
