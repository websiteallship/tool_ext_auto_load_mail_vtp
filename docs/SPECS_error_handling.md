# SPECS: Error Handling & Resilience

> Skills áp dụng: `09_error-handling-patterns`, `07_python-performance-optimization`

## Mục Đích

Định nghĩa cách xử lý lỗi thống nhất trong toàn bộ ứng dụng. Đảm bảo tool chạy ổn định 24/7 khi bật chế độ tự động.

---

## Exception Hierarchy

```python
class AppError(Exception):
    """Base exception cho toàn app."""
    def __init__(self, message: str, recoverable: bool = True):
        self.recoverable = recoverable
        super().__init__(message)

# Authentication
class AuthError(AppError):
    """Lỗi xác thực Gmail."""
class TokenExpiredError(AuthError):
    """Token hết hạn — có thể auto-refresh."""
class AuthRevokedError(AuthError):
    """User thu hồi quyền — cần re-authenticate."""

# Network
class NetworkError(AppError):
    """Lỗi kết nối mạng."""
class ApiQuotaError(NetworkError):
    """Vượt quota Gmail API."""

# File System
class FileError(AppError):
    """Lỗi file system."""
class DiskSpaceError(FileError):
    """Hết dung lượng disk."""

# Configuration
class ConfigError(AppError):
    """Lỗi cấu hình."""
class InvalidRuleError(ConfigError):
    """Rule không hợp lệ."""
```

---

## Retry Strategy

```python
from tenacity import (
    retry, stop_after_attempt, wait_exponential,
    retry_if_exception_type, before_sleep_log
)

# Gmail API calls  
GMAIL_RETRY = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((NetworkError, TimeoutError)),
    before_sleep=before_sleep_log(logger, logging.WARNING),
)

# File downloads
DOWNLOAD_RETRY = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=3, max=30),
    retry=retry_if_exception_type((ConnectionError, TimeoutError)),
)

# Token refresh
TOKEN_RETRY = retry(
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=1, min=1, max=5),
)
```

---

## Error Recovery Matrix

| Lỗi | Auto-Retry? | Recovery Action | User Notification |
|-----|-------------|-----------------|-------------------|
| `TokenExpiredError` | ✅ 1x auto-refresh | Refresh token | Chỉ log nếu fail |
| `AuthRevokedError` | ❌ | Yêu cầu re-auth | ⚠️ Dialog + tray notification |
| `NetworkError` | ✅ 3x backoff | Retry 2s/4s/8s | Log warning |
| `ApiQuotaError` | ❌ | Wait 60s, thử lại | ⚠️ "Quota exceeded, chờ 1 phút" |
| `TimeoutError` | ✅ 3x | Retry, tăng timeout | Log warning |
| `DiskSpaceError` | ❌ | Dừng batch | 🔴 "Hết dung lượng disk!" |
| `InvalidRuleError` | ❌ | Skip rule, tiếp tục | ⚠️ "Rule X không hợp lệ" |
| `404 Not Found` | ❌ | Skip file | Log info |
| `403 Forbidden` | ❌ | Skip file | Log warning |
| `Uncaught Exception` | ❌ | Log traceback | 🔴 Error state |

---

## Graceful Degradation

```
Ưu tiên 1: Tải đính kèm Gmail ← quan trọng nhất
Ưu tiên 2: Tải bảng kê từ URL  ← có thể fail mà không ảnh hưởng đính kèm
Ưu tiên 3: Gán nhãn Gmail       ← nice-to-have

Nếu bảng kê fail → vẫn tiếp tục email tiếp theo
Nếu Gmail fail   → dừng batch, báo user
```

---

## Logging Levels

```python
# DEBUG  — Chi tiết kỹ thuật, chỉ bật khi cần debug
logger.debug(f"HTTP GET {url} → status {response.status_code}")

# INFO   — Hành động chính
logger.info(f"Downloaded: {filename} ({size_kb} KB)")

# WARNING — Lỗi có thể tự xử lý
logger.warning(f"Retry {attempt}/3: {error_message}")

# ERROR  — Lỗi cần user attention
logger.error(f"Failed to download: {filename} — {error}")

# CRITICAL — App không thể tiếp tục
logger.critical(f"Disk space exhausted: {free_mb} MB remaining")
```

---

## Health Check

```python
def health_check(self) -> dict:
    """Kiểm tra sức khỏe hệ thống trước khi chạy."""
    return {
        "gmail_connected": self._check_gmail_auth(),
        "disk_space_mb": self._get_free_disk_space(),
        "internet_available": self._check_internet(),
        "rules_count": len(self.rule_engine.get_enabled_rules()),
        "last_error": self._get_last_error(),
    }
```
