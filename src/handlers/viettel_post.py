"""
Viettel Post Handler — Handle VTP invoice and bảng kê emails.

Refactored from link_extractor.py. Handles:
- Attachments: .pdf, .xml, .zip (direct download from Gmail)
- Bảng kê link: chi tiết bảng kê → download from s1.viettelpost.vn
- HTML→xlsx conversion for bảng kê pages

Skills applied: 03_web-scraper, 08_clean-code
"""

from __future__ import annotations

import logging

from src.handlers.registry import register
from src.handlers.base import BaseEmailHandler, DownloadTarget, ExtractionConfig

logger = logging.getLogger("email_auto_download.handlers.viettel_post")


@register("viettel_post")
class ViettelPostHandler(BaseEmailHandler):
    """Viettel Post — invoice attachments + bảng kê HTML→xlsx."""

    display_name = "Viettel Post Invoice"
    description = "Hóa đơn + bảng kê chi tiết Viettel Post"
    icon = "📦"
    file_types = "📎 .pdf .xml .zip + 🔗 bảng kê HTML→xlsx"

    DEFAULT_CONFIG = ExtractionConfig(
        link_text_patterns=[
            "chi tiết bảng kê",
            "chi tiet bang ke",
            "bảng kê chi tiết",
            "bang ke chi tiet",
            "xem chi tiết",
        ],
        link_url_patterns=[
            "bang-ke-hoa-don-chi-tiet.do",
            "bangkechitiet",
            "bang-ke-chi-tiet",
        ],
        allowed_domains=[
            "vinvoice.viettel.vn",
            "s1.viettelpost.vn",
            "viettelpost.vn",
        ],
        attachment_extensions=[".pdf", ".xml", ".xlsx", ".zip"],
        download_attachments=True,
        download_links=True,
        follow_redirects=False,
    )

    def extract_download_links(
        self,
        html_body: str,
        config: ExtractionConfig,
    ) -> list[DownloadTarget]:
        """Extract bảng kê link from VTP email body.

        VTP emails contain a "chi tiết bảng kê" link pointing to
        s1.viettelpost.vn which returns an HTML page that needs
        to be converted to xlsx by the FileDownloader.
        """
        targets = super().extract_download_links(html_body, config)

        # VTP has at most one bảng kê link per email
        if targets:
            targets[0].filename_hint = "bangke_chi_tiet"
            targets[0].context = "Bảng kê chi tiết VTP"

        return targets[:1]  # Only first match
