# CORE: Link Extractor Module

> Skills áp dụng: `03_web-scraper`, `02_python-pro`, `08_clean-code`

## Mục Đích

Parse HTML body email để trích xuất link "chi tiết bảng kê" dẫn đến `vinvoice.viettel.vn`.

---

## API Contract

```python
from dataclasses import dataclass

@dataclass
class ExtractedLink:
    url: str
    text: str
    link_type: str  # "bang_ke" | "invoice_search" | "other"

class LinkExtractor:
    """
    Trích xuất link từ HTML body email.
    Single Responsibility: CHỈ tìm link, KHÔNG tải file.
    """
    
    BANG_KE_PATTERNS = [
        "chi tiết bảng kê",
        "chi tiet bang ke",
        "bảng kê chi tiết",
    ]
    
    INVOICE_SEARCH_PATTERNS = [
        "vinvoice.viettel.vn/utilities/invoice-search",
    ]
    
    def extract_all_links(self, html_body: str) -> list[ExtractedLink]:
        """Trích xuất tất cả link từ HTML body."""
    
    def extract_bang_ke_link(self, html_body: str) -> str | None:
        """
        Tìm link "chi tiết bảng kê" từ body email.
        
        Returns:
            URL string hoặc None nếu không tìm thấy
        """
    
    def extract_secret_code(self, html_body: str) -> str | None:
        """
        Trích xuất mã số bí mật từ body email.
        Ví dụ: "mã số bí mật 3T5XD00AWF2BQ09"
        """
    
    def extract_invoice_number(self, html_body: str) -> str | None:
        """
        Trích xuất số hóa đơn điện tử.
        Ví dụ: "K26TAN2038744"
        """
```

---

## Extraction Strategy (từ `03_web-scraper`)

```
Phase 1: Parse HTML với BeautifulSoup
Phase 2: Tìm <a> tags chứa text khớp patterns
Phase 3: Resolve relative URLs thành absolute URLs
Phase 4: Validate URL format
Phase 5: Trả về ExtractedLink objects
```

### HTML Parsing Logic

```python
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin

def extract_bang_ke_link(self, html_body: str) -> str | None:
    soup = BeautifulSoup(html_body, "html.parser")
    
    for anchor in soup.find_all("a", href=True):
        link_text = anchor.get_text(strip=True).lower()
        
        if any(pattern in link_text for pattern in self.BANG_KE_PATTERNS):
            return anchor["href"]
    
    return None
```

---

## Regex Patterns

```python
# Số hóa đơn: K26TAN + số
INVOICE_PATTERN = re.compile(r"K\d{2}TAN\d+")

# Mã bí mật: chuỗi alphanumeric sau "mã số bí mật"
SECRET_CODE_PATTERN = re.compile(
    r"mã\s+số\s+bí\s+mật\s+([A-Z0-9]+)",
    re.IGNORECASE
)

# MST: 10 or 13 digits
TAX_CODE_PATTERN = re.compile(r"\d{10}(?:\d{3})?")
```

---

## Clean Code Principles (từ `08_clean-code`)

| Nguyên tắc | Áp dụng |
|------------|---------|
| **Single Responsibility** | Module CHỈ extract links, không download |
| **Meaningful Names** | `extract_bang_ke_link()` không phải `get_link()` |
| **No Side Effects** | Chỉ đọc và trả về, không modify input |
| **Small Functions** | Mỗi function < 20 dòng |
| **Testable** | Input = HTML string, Output = URL string |

---

## Dependencies

```
beautifulsoup4>=4.12.0
lxml>=5.0.0  # HTML parser nhanh hơn html.parser
```
