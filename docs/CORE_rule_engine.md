# CORE: Rule Engine Module

> Skills áp dụng: `02_python-pro`, `08_clean-code`

## Mục Đích

Quản lý nhiều "rule" email — mỗi rule định nghĩa cách tìm, lọc và xử lý 1 loại email. Cho phép mở rộng dễ dàng sang các loại email khác ngoài Viettel Post.

---

## API Contract

```python
from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class EmailRule:
    """Một rule xử lý email."""
    name: str
    enabled: bool = True
    subject_query: str = ""
    sender_filter: str = ""
    label_filter: str = "INBOX"
    output_folder: str = "downloads"
    download_attachments: bool = True
    download_bang_ke: bool = True
    max_emails: int = 50
    attachment_extensions: list[str] = field(
        default_factory=lambda: [".pdf", ".xml", ".xlsx"]
    )
    
    def to_gmail_query(self) -> str:
        """Chuyển rule thành Gmail search query string."""
        parts = []
        if self.subject_query:
            parts.append(f'subject:"{self.subject_query}"')
        if self.sender_filter:
            parts.append(f"from:{self.sender_filter}")
        if self.label_filter:
            parts.append(f"in:{self.label_filter.lower()}")
        parts.append("has:attachment")
        return " ".join(parts)

class RuleEngine:
    """
    Load/save/validate email rules từ JSON config.
    """
    
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.rules: list[EmailRule] = []
    
    def load_rules(self) -> list[EmailRule]:
        """Load rules từ JSON file."""
    
    def save_rules(self) -> None:
        """Lưu rules hiện tại ra JSON file."""
    
    def add_rule(self, rule: EmailRule) -> None:
        """Thêm rule mới."""
    
    def remove_rule(self, name: str) -> None:
        """Xóa rule theo tên."""
    
    def get_enabled_rules(self) -> list[EmailRule]:
        """Lấy danh sách rule đang enabled."""
    
    def validate_rule(self, rule: EmailRule) -> list[str]:
        """
        Validate rule, trả về list lỗi (rỗng = hợp lệ).
        Checks: tên trùng, query rỗng, folder hợp lệ.
        """
```

---

## Config Format (JSON)

```json
[
  {
    "name": "Viettel Post Invoice",
    "enabled": true,
    "subject_query": "Tổng công ty Cổ phần Bưu Chính Viettel",
    "sender_filter": "noreply@viettelpost.com.vn",
    "label_filter": "INBOX",
    "output_folder": "downloads/viettel_post",
    "download_attachments": true,
    "download_bang_ke": true,
    "max_emails": 50,
    "attachment_extensions": [".pdf", ".xml"]
  },
  {
    "name": "VNPT Invoice",
    "enabled": false,
    "subject_query": "VNPT hóa đơn",
    "sender_filter": "",
    "output_folder": "downloads/vnpt",
    "download_attachments": true,
    "download_bang_ke": false,
    "max_emails": 20
  }
]
```

---

## Default Rule (Built-in)

Khi chưa có `rules.json`, tự tạo rule mặc định:

```python
DEFAULT_RULE = EmailRule(
    name="Viettel Post Invoice",
    enabled=True,
    subject_query="Tổng công ty Cổ phần Bưu Chính Viettel",
    sender_filter="noreply@viettelpost.com.vn",
    output_folder="downloads/viettel_post",
    download_attachments=True,
    download_bang_ke=True,
)
```

---

## Extensibility

Thiết kế rule engine để dễ mở rộng:

```
Rule hiện tại:        Rule tương lai:
├─ Viettel Post       ├─ VNPT
├─ (có bảng kê)       ├─ FPT Telecom  
                      ├─ EVN (điện)
                      ├─ Sacombank
                      └─ Custom rule bất kỳ
```

Mỗi rule là **data-driven** — không cần code mới, chỉ cần thêm JSON config.
