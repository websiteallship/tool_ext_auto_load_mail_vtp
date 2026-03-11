"""Unit tests for LinkExtractor."""

import pytest

from src.link_extractor import LinkExtractor


SAMPLE_VIETTEL_HTML = """
<html><body>
<p>Kính gửi Quý khách hàng,</p>
<p>Tổng công ty Cổ phần Bưu Chính Viettel đã xuất hóa đơn điện tử
số K26TAN2038744 cho đơn hàng của bạn.</p>
<p>Mã số thuế bên bán: 0104093672</p>
<p>Quý khách vui lòng dùng mã số bí mật 3T5XD00AWF2BQ09 để tra cứu.</p>
<p>Xem <a href="https://vinvoice.viettel.vn/bang-ke/detail?id=123456">
chi tiết bảng kê</a> tại đây.</p>
<p><a href="https://vinvoice.viettel.vn/utilities/invoice-search?q=abc">
Tra cứu hóa đơn</a></p>
</body></html>
"""

SAMPLE_NO_LINK_HTML = """
<html><body>
<p>This email has no relevant links.</p>
<p>Just plain text content.</p>
</body></html>
"""

SAMPLE_MULTI_LINK_HTML = """
<html><body>
<a href="https://example.com">Example</a>
<a href="mailto:test@test.com">Email</a>
<a href="https://vinvoice.viettel.vn/detail/789">chi tiết bảng kê</a>
<a href="https://other.com/page">Other Link</a>
</body></html>
"""


class TestExtractBangKeLink:
    def setup_method(self):
        self.extractor = LinkExtractor()

    def test_found_in_viettel_email(self):
        url = self.extractor.extract_bang_ke_link(SAMPLE_VIETTEL_HTML)
        assert url == "https://vinvoice.viettel.vn/bang-ke/detail?id=123456"

    def test_not_found(self):
        url = self.extractor.extract_bang_ke_link(SAMPLE_NO_LINK_HTML)
        assert url is None

    def test_empty_html(self):
        assert self.extractor.extract_bang_ke_link("") is None

    def test_none_input(self):
        assert self.extractor.extract_bang_ke_link(None) is None

    def test_multi_link_finds_correct(self):
        url = self.extractor.extract_bang_ke_link(SAMPLE_MULTI_LINK_HTML)
        assert url == "https://vinvoice.viettel.vn/detail/789"


class TestExtractInvoiceNumber:
    def setup_method(self):
        self.extractor = LinkExtractor()

    def test_found(self):
        result = self.extractor.extract_invoice_number(SAMPLE_VIETTEL_HTML)
        assert result == "K26TAN2038744"

    def test_not_found(self):
        result = self.extractor.extract_invoice_number(SAMPLE_NO_LINK_HTML)
        assert result is None

    def test_empty(self):
        assert self.extractor.extract_invoice_number("") is None


class TestExtractSecretCode:
    def setup_method(self):
        self.extractor = LinkExtractor()

    def test_found(self):
        result = self.extractor.extract_secret_code(SAMPLE_VIETTEL_HTML)
        assert result == "3T5XD00AWF2BQ09"

    def test_not_found(self):
        result = self.extractor.extract_secret_code(SAMPLE_NO_LINK_HTML)
        assert result is None


class TestExtractTaxCode:
    def setup_method(self):
        self.extractor = LinkExtractor()

    def test_found(self):
        result = self.extractor.extract_tax_code(SAMPLE_VIETTEL_HTML)
        assert result == "0104093672"

    def test_not_found(self):
        result = self.extractor.extract_tax_code(SAMPLE_NO_LINK_HTML)
        assert result is None


class TestExtractAllLinks:
    def setup_method(self):
        self.extractor = LinkExtractor()

    def test_extracts_all_non_mailto(self):
        links = self.extractor.extract_all_links(SAMPLE_MULTI_LINK_HTML)
        # Should exclude mailto: links
        assert len(links) == 3
        urls = [l.url for l in links]
        assert "https://example.com" in urls
        assert "mailto:test@test.com" not in urls

    def test_classifies_bang_ke(self):
        links = self.extractor.extract_all_links(SAMPLE_MULTI_LINK_HTML)
        bang_ke = [l for l in links if l.link_type == "bang_ke"]
        assert len(bang_ke) == 1
        assert "vinvoice" in bang_ke[0].url

    def test_empty(self):
        assert self.extractor.extract_all_links("") == []
