# SPECS: Testing Strategy

> Skills áp dụng: `02_python-pro`, `08_clean-code`

## Mục Đích

Định nghĩa chiến lược testing cho từng module. Đảm bảo quality trước khi build.

---

## Test Pyramid

```
          ┌─────────┐
          │  E2E    │  ← Manual test: chạy app, tải file thật
         ─┼─────────┼─
        ╱ │ Integr. │ ╲ ← Gmail API + file system
       ╱──┼─────────┼──╲
      │   │  Unit   │   │ ← Pure logic tests
      └───┴─────────┴───┘
```

---

## Unit Tests

### `tests/test_link_extractor.py`

```python
import pytest
from src.link_extractor import LinkExtractor

SAMPLE_EMAIL_HTML = """
<html><body>
<p>Click vào link <a href="https://vinvoice.viettel.vn/bang-ke/123">
chi tiết bảng kê</a> để xem chi tiết.</p>
</body></html>
"""

class TestLinkExtractor:
    def setup_method(self):
        self.extractor = LinkExtractor()
    
    def test_extract_bang_ke_link_found(self):
        url = self.extractor.extract_bang_ke_link(SAMPLE_EMAIL_HTML)
        assert url == "https://vinvoice.viettel.vn/bang-ke/123"
    
    def test_extract_bang_ke_link_not_found(self):
        html = "<html><body><p>No link here</p></body></html>"
        url = self.extractor.extract_bang_ke_link(html)
        assert url is None
    
    def test_extract_invoice_number(self):
        html = "<p>hóa đơn K26TAN2038744</p>"
        invoice = self.extractor.extract_invoice_number(html)
        assert invoice == "K26TAN2038744"
    
    def test_extract_secret_code(self):
        html = "<p>mã số bí mật 3T5XD00AWF2BQ09</p>"
        code = self.extractor.extract_secret_code(html)
        assert code == "3T5XD00AWF2BQ09"
```

### `tests/test_rule_engine.py`

```python
import pytest
from src.rule_engine import RuleEngine, EmailRule

class TestRuleEngine:
    def test_load_default_rules(self, tmp_path):
        engine = RuleEngine(tmp_path / "rules.json")
        rules = engine.load_rules()
        assert len(rules) == 1  # Default Viettel rule
    
    def test_add_rule(self, tmp_path):
        engine = RuleEngine(tmp_path / "rules.json")
        engine.load_rules()
        engine.add_rule(EmailRule(name="Test", subject_query="test"))
        assert len(engine.rules) == 2
    
    def test_to_gmail_query(self):
        rule = EmailRule(
            name="Test",
            subject_query="Viettel",
            sender_filter="test@example.com"
        )
        query = rule.to_gmail_query()
        assert 'subject:"Viettel"' in query
        assert "from:test@example.com" in query
    
    def test_validate_rule_empty_name(self):
        rule = EmailRule(name="", subject_query="test")
        engine = RuleEngine(Path("dummy"))
        errors = engine.validate_rule(rule)
        assert "name is required" in errors[0].lower()
```

### `tests/test_file_downloader.py`

```python
import pytest
from src.file_downloader import FileDownloader, DownloadStatus

class TestFileDownloader:
    def test_save_attachment(self, tmp_path):
        dl = FileDownloader(output_dir=tmp_path)
        result = dl.save_attachment(b"test data", "test.pdf")
        assert result.status == DownloadStatus.SUCCESS
        assert (tmp_path / "test.pdf").exists()
    
    def test_skip_duplicate(self, tmp_path):
        dl = FileDownloader(output_dir=tmp_path, skip_duplicates=True)
        # First download
        dl.save_attachment(b"data", "test.pdf")
        # Second download — should skip
        result = dl.save_attachment(b"data", "test.pdf")
        assert result.status == DownloadStatus.SKIPPED_DUPLICATE
    
    def test_is_duplicate(self, tmp_path):
        dl = FileDownloader(output_dir=tmp_path)
        assert dl.is_duplicate("nonexistent.pdf") is False
        (tmp_path / "exists.pdf").write_bytes(b"test")
        assert dl.is_duplicate("exists.pdf") is True
```

---

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/test_link_extractor.py -v

# Run with marker
pytest -m "not integration" tests/
```

---

## Test Coverage Target

| Module | Target | Priority |
|--------|--------|----------|
| `link_extractor.py` | >90% | 🔴 High |
| `rule_engine.py` | >90% | 🔴 High |
| `file_downloader.py` | >80% | 🟡 Medium |
| `gmail_client.py` | >50% | 🟢 Low (API mocking) |
| `scheduler.py` | >60% | 🟡 Medium |
| `app.py` (GUI) | Manual | 🟢 Low |
