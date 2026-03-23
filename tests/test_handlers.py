"""
Unit tests for the handler system (plugin architecture).

Tests cover:
- Handler registry: registration, factory, fallback
- ExtractionConfig: merge, defaults
- GenericHandler: attachment filtering
- ViettelPostHandler: bảng kê link extraction
- JTInvoiceHandler: link context parsing, invoice number extraction
- JTCODHandler: config, attachment-only behavior

Skills applied: 08_clean-code
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from src.handlers.registry import HANDLER_REGISTRY, register
from src.handlers.base import BaseEmailHandler, DownloadTarget, ExtractionConfig
from src.handlers import get_handler, get_all_handler_types


# ============================================================================
# Fixtures
# ============================================================================


@dataclass
class FakeAttachment:
    """Minimal attachment stub for testing filter_attachments."""
    filename: str
    id: str = "fake_id"
    size: int = 1024


VTP_EMAIL_HTML = """
<html><body>
<p>Kính gửi Quý khách hàng,</p>
<p>Tổng công ty Cổ phần Bưu Chính Viettel thông báo hóa đơn.</p>
<table>
  <tr>
    <td>Để xem chi tiết bảng kê, vui lòng</td>
    <td><a href="https://s1.viettelpost.vn/bang-ke-hoa-don-chi-tiet.do?id=12345">
      Chi tiết bảng kê
    </a></td>
  </tr>
</table>
<p>Trân trọng.</p>
</body></html>
"""

JT_INVOICE_HTML = """
<html><body>
<p>J&T Express thông báo phát hành hóa đơn</p>
<p>Số hóa đơn (Invoice Number): <b>31784</b></p>
<p>Ký hiệu hóa đơn (Serial Number): <b>C26TBH</b></p>

<div>
  <p>Tải tệp thông tin hóa đơn (To download the xml file)
    <a href="https://url3815.hq.jtexpress.vn/track/xml123">Nhấn vào đây</a>
  </p>

  <p>Tải tệp bản thể hiện (To download the pdf file)
    <a href="https://url3815.hq.jtexpress.vn/track/pdf456">Nhấn vào đây</a>
  </p>

  <p>Tra cứu hóa đơn (For more details please access)
    <a href="https://url3815.hq.jtexpress.vn/track/search">Nhấn vào đây</a>
  </p>

  <p>Tải tệp bảng kê vận đơn
    <a href="">Nhấn vào đây</a>
  </p>
</div>
</body></html>
"""


# ============================================================================
# Registry Tests
# ============================================================================


class TestHandlerRegistry:
    """Test handler registration and factory."""

    def test_all_handlers_registered(self):
        """All 4 handler types should be in registry."""
        assert "generic" in HANDLER_REGISTRY
        assert "viettel_post" in HANDLER_REGISTRY
        assert "jt_invoice" in HANDLER_REGISTRY
        assert "jt_cod" in HANDLER_REGISTRY

    def test_get_handler_by_type(self):
        handler = get_handler("viettel_post")
        assert handler.handler_type == "viettel_post"
        assert handler.display_name == "Viettel Post Invoice"

    def test_get_handler_fallback(self):
        """Unknown handler type should fallback to GenericHandler."""
        handler = get_handler("nonexistent_handler")
        assert handler.handler_type == "generic"

    def test_get_all_handler_types(self):
        types = get_all_handler_types()
        assert len(types) >= 4
        type_names = [t["handler_type"] for t in types]
        assert "generic" in type_names
        assert "viettel_post" in type_names

    def test_handler_metadata(self):
        """Each handler should have display_name, icon, description."""
        for htype, cls in HANDLER_REGISTRY.items():
            h = cls()
            assert h.display_name, f"{htype} missing display_name"
            assert h.icon, f"{htype} missing icon"
            assert h.description, f"{htype} missing description"


# ============================================================================
# ExtractionConfig Tests
# ============================================================================


class TestExtractionConfig:
    """Test config creation and merge."""

    def test_default_config(self):
        config = ExtractionConfig()
        assert config.download_attachments is True
        assert config.download_links is True
        assert config.follow_redirects is False
        assert ".pdf" in config.attachment_extensions

    def test_merge_with_none(self):
        config = ExtractionConfig(download_links=True)
        merged = config.merge(None)
        assert merged is config  # same object, no copy needed

    def test_merge_overrides(self):
        config = ExtractionConfig(
            allowed_domains=["old.com"],
            download_links=True,
        )
        merged = config.merge({
            "allowed_domains": ["new.com"],
            "follow_redirects": True,
        })
        assert merged.allowed_domains == ["new.com"]
        assert merged.follow_redirects is True
        assert merged.download_links is True  # unchanged

    def test_merge_does_not_mutate_original(self):
        config = ExtractionConfig(allowed_domains=["original.com"])
        merged = config.merge({"allowed_domains": ["changed.com"]})
        assert config.allowed_domains == ["original.com"]
        assert merged.allowed_domains == ["changed.com"]


# ============================================================================
# GenericHandler Tests
# ============================================================================


class TestGenericHandler:
    """Test default handler behavior."""

    def test_default_config_no_links(self):
        handler = get_handler("generic")
        config = handler.resolve_config()
        assert config.download_links is False
        assert config.download_attachments is True

    def test_filter_attachments_by_extension(self):
        handler = get_handler("generic")
        config = handler.resolve_config()
        attachments = [
            FakeAttachment("invoice.pdf"),
            FakeAttachment("data.xlsx"),
            FakeAttachment("readme.txt"),
            FakeAttachment("photo.jpg"),
            FakeAttachment("archive.zip"),
        ]
        filtered = handler.filter_attachments(attachments, config)
        names = [a.filename for a in filtered]
        assert "invoice.pdf" in names
        assert "data.xlsx" in names
        assert "archive.zip" in names
        assert "readme.txt" not in names
        assert "photo.jpg" not in names

    def test_filter_attachments_empty_extensions(self):
        """Empty extension list = no filter = return all."""
        handler = get_handler("generic")
        config = ExtractionConfig(attachment_extensions=[])
        attachments = [FakeAttachment("any.doc"), FakeAttachment("test.bin")]
        filtered = handler.filter_attachments(attachments, config)
        assert len(filtered) == 2

    def test_filter_attachments_disabled(self):
        handler = get_handler("generic")
        config = ExtractionConfig(download_attachments=False)
        attachments = [FakeAttachment("file.pdf")]
        filtered = handler.filter_attachments(attachments, config)
        assert len(filtered) == 0

    def test_extract_links_returns_empty(self):
        """Generic handler with default config should not extract links."""
        handler = get_handler("generic")
        config = handler.resolve_config()
        targets = handler.extract_download_links("<html><a href='x'>test</a></html>", config)
        assert targets == []


# ============================================================================
# ViettelPostHandler Tests
# ============================================================================


class TestViettelPostHandler:
    """Test VTP-specific logic."""

    def test_config_defaults(self):
        handler = get_handler("viettel_post")
        config = handler.resolve_config()
        assert config.download_links is True
        assert config.download_attachments is True
        assert config.follow_redirects is False
        assert "chi tiết bảng kê" in config.link_text_patterns
        assert "vinvoice.viettel.vn" in config.allowed_domains

    def test_extract_bang_ke_link(self):
        handler = get_handler("viettel_post")
        config = handler.resolve_config()
        targets = handler.extract_download_links(VTP_EMAIL_HTML, config)
        assert len(targets) == 1
        assert "s1.viettelpost.vn" in targets[0].url
        assert "bang-ke-hoa-don-chi-tiet.do" in targets[0].url
        assert targets[0].filename_hint == "bangke_chi_tiet"
        assert "VTP" in targets[0].context

    def test_only_one_target(self):
        """VTP should only return max 1 bảng kê link."""
        html = """
        <html><body>
        <a href="https://s1.viettelpost.vn/bang-ke-hoa-don-chi-tiet.do?id=1">Chi tiết bảng kê</a>
        <a href="https://s1.viettelpost.vn/bang-ke-hoa-don-chi-tiet.do?id=2">Chi tiết bảng kê</a>
        </body></html>
        """
        handler = get_handler("viettel_post")
        config = handler.resolve_config()
        targets = handler.extract_download_links(html, config)
        assert len(targets) == 1

    def test_no_link_in_body(self):
        html = "<html><body><p>No links here</p></body></html>"
        handler = get_handler("viettel_post")
        config = handler.resolve_config()
        targets = handler.extract_download_links(html, config)
        assert targets == []

    def test_empty_body(self):
        handler = get_handler("viettel_post")
        config = handler.resolve_config()
        assert handler.extract_download_links("", config) == []
        assert handler.extract_download_links(None, config) == []

    def test_attachment_filter(self):
        handler = get_handler("viettel_post")
        config = handler.resolve_config()
        attachments = [
            FakeAttachment("hoadon.pdf"),
            FakeAttachment("hoadon.xml"),
            FakeAttachment("logo.png"),
        ]
        filtered = handler.filter_attachments(attachments, config)
        names = [a.filename for a in filtered]
        assert "hoadon.pdf" in names
        assert "hoadon.xml" in names
        assert "logo.png" not in names


# ============================================================================
# JTInvoiceHandler Tests
# ============================================================================


class TestJTInvoiceHandler:
    """Test J&T invoice link context parsing and invoice extraction."""

    def test_config_defaults(self):
        handler = get_handler("jt_invoice")
        config = handler.resolve_config()
        assert config.download_links is True
        assert config.download_attachments is False
        assert config.follow_redirects is True

    def test_extract_pdf_and_xml_links(self):
        handler = get_handler("jt_invoice")
        config = handler.resolve_config()
        targets = handler.extract_download_links(JT_INVOICE_HTML, config)

        # Should find XML and PDF, skip search page and empty href
        assert len(targets) == 2

        types = {t.filename_hint.split(".")[-1] for t in targets}
        assert "xml" in types
        assert "pdf" in types

    def test_invoice_number_in_filename(self):
        handler = get_handler("jt_invoice")
        config = handler.resolve_config()
        targets = handler.extract_download_links(JT_INVOICE_HTML, config)

        for t in targets:
            assert "31784" in t.filename_hint
            assert "C26TBH" in t.filename_hint

    def test_skips_search_link(self):
        """'Tra cứu hóa đơn' links should be skipped."""
        handler = get_handler("jt_invoice")
        config = handler.resolve_config()
        targets = handler.extract_download_links(JT_INVOICE_HTML, config)
        urls = [t.url for t in targets]
        assert not any("search" in u for u in urls)

    def test_skips_empty_href(self):
        """Empty href links should be ignored."""
        handler = get_handler("jt_invoice")
        config = handler.resolve_config()
        targets = handler.extract_download_links(JT_INVOICE_HTML, config)
        assert all(t.url for t in targets)

    def test_extract_invoice_number(self):
        from src.handlers.jt_express import JTInvoiceHandler
        num = JTInvoiceHandler._extract_jt_invoice_number(JT_INVOICE_HTML)
        assert num == "31784"

    def test_extract_serial(self):
        from src.handlers.jt_express import JTInvoiceHandler
        serial = JTInvoiceHandler._extract_jt_serial(JT_INVOICE_HTML)
        assert serial == "C26TBH"

    def test_no_invoice_number(self):
        from src.handlers.jt_express import JTInvoiceHandler
        num = JTInvoiceHandler._extract_jt_invoice_number("<p>No number</p>")
        assert num is None

    def test_empty_body(self):
        handler = get_handler("jt_invoice")
        config = handler.resolve_config()
        assert handler.extract_download_links("", config) == []

    def test_no_duplicate_file_types(self):
        """Should not download 2 PDFs or 2 XMLs even if multiple links match."""
        html = """
        <html><body>
        <p>Tải tệp thông tin hóa đơn <a href="https://url1.com/a">Nhấn vào đây</a></p>
        <p>Tải tệp thông tin hóa đơn <a href="https://url2.com/b">Nhấn vào đây</a></p>
        </body></html>
        """
        handler = get_handler("jt_invoice")
        config = handler.resolve_config()
        targets = handler.extract_download_links(html, config)
        xml_targets = [t for t in targets if "xml" in t.filename_hint]
        assert len(xml_targets) == 1


# ============================================================================
# JTCODHandler Tests
# ============================================================================


class TestJTCODHandler:
    """Test J&T COD handler behavior."""

    def test_config_defaults(self):
        handler = get_handler("jt_cod")
        config = handler.resolve_config()
        assert config.download_attachments is True
        assert config.download_links is False
        assert config.follow_redirects is False
        assert config.attachment_extensions == [".xlsx"]

    def test_only_xlsx_attachments(self):
        handler = get_handler("jt_cod")
        config = handler.resolve_config()
        attachments = [
            FakeAttachment("bangke_cod.xlsx"),
            FakeAttachment("summary.pdf"),
            FakeAttachment("logo.png"),
        ]
        filtered = handler.filter_attachments(attachments, config)
        assert len(filtered) == 1
        assert filtered[0].filename == "bangke_cod.xlsx"

    def test_no_link_extraction(self):
        handler = get_handler("jt_cod")
        config = handler.resolve_config()
        targets = handler.extract_download_links("<html><a href='x'>test</a></html>", config)
        assert targets == []

    def test_metadata(self):
        handler = get_handler("jt_cod")
        assert handler.display_name == "J&T Express COD"
        assert handler.icon == "📊"


# ============================================================================
# DownloadTarget Tests
# ============================================================================


class TestDownloadTarget:
    def test_creation(self):
        target = DownloadTarget(
            url="https://example.com/file.pdf",
            filename_hint="invoice.pdf",
            context="Test download",
        )
        assert target.url == "https://example.com/file.pdf"
        assert target.target_type == "link"

    def test_defaults(self):
        target = DownloadTarget(url="https://x.com")
        assert target.filename_hint == ""
        assert target.context == ""
        assert target.target_type == "link"
