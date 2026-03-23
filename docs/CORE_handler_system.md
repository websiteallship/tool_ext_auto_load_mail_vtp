# CORE: Handler System (NEW v2.0)

> Skills áp dụng: `04_architecture`, `08_clean-code`

## Mục Đích

Kiến trúc plugin cho phép mỗi nhà cung cấp (Viettel Post, J&T...) có handler riêng, tách biệt logic xử lý email theo provider.

---

## Thiết Kế 2 Tầng

### Tầng 1: ExtractionConfig (JSON — data-driven)

```python
@dataclass
class ExtractionConfig:
    """Config có thể chỉnh sửa trong rules.json, không cần code."""
    link_text_patterns: list[str]    # ["chi tiết bảng kê", "xem chi tiết"]
    link_url_patterns: list[str]     # ["bang-ke-hoa-don-chi-tiet.do"]
    allowed_domains: list[str]       # ["vinvoice.viettel.vn"]
    attachment_extensions: list[str]  # [".pdf", ".xml", ".xlsx"]
    download_attachments: bool = True
    download_links: bool = True
    follow_redirects: bool = False   # For tracking URLs (J&T)
```

### Tầng 2: Handler Class (Python — logic)

```python
class BaseEmailHandler(ABC):
    DEFAULT_CONFIG: ExtractionConfig
    
    # Display metadata (cho GUI)
    display_name: str
    description: str
    icon: str
    file_types: str
    
    def extract_download_links(self, body, config) -> list[DownloadTarget]
    def process_download(self, url, response, config) -> DownloadResult
    def filter_attachments(self, attachments, config) -> list
    def resolve_config(self, override: dict | None) -> ExtractionConfig
```

---

## Handlers Hiện Có

### GenericHandler (handler_type: `"generic"`)
- Handler mặc định cho rule không chỉ định handler_type
- Tải attachment theo extension filter
- Tìm link theo text/url patterns
- **Không có** logic đặc biệt

### ViettelPostHandler (handler_type: `"viettel_post"`)
- Refactor từ `link_extractor.py`
- Patterns: `"chi tiết bảng kê"`, `vinvoice.viettel.vn`
- **Logic đặc biệt:** HTML bảng kê → .xlsx conversion (openpyxl)

### JTInvoiceHandler (handler_type: `"jt_invoice"`)
- Patterns: `"Nhấn vào đây"`, `einvoice.fast.com.vn`
- **Logic đặc biệt:** Follow tracking redirect (`url3815.hq.jtexpress.vn` → `einvoice.fast.com.vn`)
- Phân biệt link bằng text context: PDF view / XML download / PDF download / Search page
- `follow_redirects = True`

### JTCODHandler (handler_type: `"jt_cod"`)
- Chỉ tải attachment `.xlsx`
- `download_links = False`, `download_attachments = True`
- Không có logic đặc biệt (có thể dùng GenericHandler)

---

## Registry Pattern

```python
# src/handlers/__init__.py
HANDLER_REGISTRY: dict[str, type[BaseEmailHandler]] = {}

def register(handler_type: str):
    def decorator(cls):
        HANDLER_REGISTRY[handler_type] = cls
        return cls
    return decorator

def get_handler(handler_type: str) -> BaseEmailHandler:
    cls = HANDLER_REGISTRY.get(handler_type, HANDLER_REGISTRY["generic"])
    return cls()
```

**Thêm handler mới:**
1. Tạo file trong `src/handlers/`
2. Decorate class với `@register("my_handler")`
3. Import trong `__init__.py`
4. Thêm rule vào `config/rules.json`

---

## Config Override Mechanism

Mỗi handler có `DEFAULT_CONFIG`. User/dev có thể override từng field trong `rules.json`:

```json
{
  "handler_type": "viettel_post",
  "extraction_config": {
    "allowed_domains": ["new-portal.viettel.vn", "vinvoice.viettel.vn"]
  }
}
```

Merge logic: `handler.DEFAULT_CONFIG` ← shallow merge by `rule.extraction_config`

→ Khi VTP đổi domain, chỉ sửa JSON. Không cần rebuild .exe.
