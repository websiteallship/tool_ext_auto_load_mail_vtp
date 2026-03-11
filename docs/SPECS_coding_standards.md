# Coding Standards & Conventions

> Skills áp dụng: `08_clean-code`, `02_python-pro`

## Mục Đích

Quy tắc viết code thống nhất cho toàn dự án, áp dụng Clean Code principles.

---

## Python Style

### Naming

```python
# ✅ Tốt
class GmailClient:                    # PascalCase cho class
    def search_emails(self) -> list:  # snake_case cho method
        max_results = 50              # snake_case cho variable
        GMAIL_SCOPES = [...]          # UPPER_SNAKE cho constants

# ❌ Xấu
class gmailClient:            # camelCase
    def SearchEmails(self):   # PascalCase cho method
        MaxResults = 50       # PascalCase cho variable
```

### Functions

```python
# ✅ Tốt — Mỗi hàm làm 1 việc
def extract_bang_ke_link(html_body: str) -> str | None:
    """Trích xuất link bảng kê từ HTML email body."""
    soup = BeautifulSoup(html_body, "html.parser")
    for anchor in soup.find_all("a", href=True):
        if _is_bang_ke_text(anchor.get_text()):
            return anchor["href"]
    return None

def _is_bang_ke_text(text: str) -> bool:
    """Kiểm tra text có phải link bảng kê không."""
    return "chi tiết bảng kê" in text.lower()

# ❌ Xấu — Hàm làm quá nhiều việc
def process_email(email):
    body = get_body(email)
    links = parse_links(body)
    for link in links:
        download(link)     # Side effect
        save_to_db(link)   # Side effect
        notify_user(link)  # Side effect
```

### Type Hints

```python
# ✅ Luôn dùng type hints
def download_attachment(
    self,
    data: bytes,
    filename: str,
    output_dir: Path
) -> DownloadResult:
    ...

# ❌ Không dùng type hints
def download_attachment(self, data, filename, output_dir):
    ...
```

### Docstrings

```python
def search_emails(
    self,
    query: str,
    max_results: int = 50
) -> list[EmailMessage]:
    """
    Tìm email theo Gmail query syntax.
    
    Args:
        query: Gmail search query (e.g. "subject:Viettel has:attachment")
        max_results: Số email tối đa trả về
    
    Returns:
        Danh sách EmailMessage objects, sắp xếp theo ngày mới nhất
    
    Raises:
        AuthError: Nếu chưa xác thực
        NetworkError: Nếu không kết nối được Gmail
    """
```

---

## Project Conventions

### Imports

```python
# 1. Standard library
import json
import logging
from pathlib import Path
from datetime import datetime

# 2. Third-party
import requests
from bs4 import BeautifulSoup
from tenacity import retry

# 3. Local
from src.models import EmailMessage, Attachment
from src.gmail_client import GmailClient
```

### Error Handling

```python
# ✅ Cụ thể
try:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
except requests.ConnectionError as e:
    logger.warning(f"Connection failed: {e}")
    raise NetworkError(f"Cannot connect to {url}") from e
except requests.Timeout:
    logger.warning(f"Request timed out: {url}")
    raise

# ❌ Nuốt lỗi
try:
    response = requests.get(url)
except Exception:
    pass  # Nuốt lỗi = debug nightmare
```

### Logging

```python
# ✅ Structured, có context
logger.info(f"Downloaded: {filename} ({size_kb} KB) from email '{subject}'")

# ❌ Quá chung chung
logger.info("done")
print("downloaded file")
```

---

## File Organisation

```
src/
├── __init__.py           # Package marker
├── models.py             # Shared dataclasses (KHÔNG logic)
├── gmail_client.py       # Gmail connection (SRP)
├── link_extractor.py     # HTML parsing (SRP)
├── file_downloader.py    # File operations (SRP)
├── rule_engine.py        # Rule management (SRP)
└── scheduler.py          # Orchestration (SRP)
```

Mỗi file = **1 trách nhiệm** (Single Responsibility Principle)

---

## Git Conventions

### Commit Messages

```
feat: add Gmail OAuth2 authentication
fix: handle timeout when downloading bang ke
refactor: extract link patterns to constants
docs: add CORE_gmail_client documentation
test: add unit tests for link_extractor
chore: update dependencies
```

### Branch Naming

```
feature/gmail-auth
feature/gui-dashboard
fix/download-retry
refactor/rule-engine
```
