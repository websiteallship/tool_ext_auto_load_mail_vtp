# OPS: Logging & Monitoring

> Skills áp dụng: `07_python-performance-optimization`, `09_error-handling-patterns`

## Mục Đích

Thiết kế hệ thống logging cho cả file log (persistent) và GUI display (real-time).

---

## Logging Architecture

```mermaid
flowchart LR
    SRC[Source Code] -->|logger.info()| ROOT[Root Logger]
    ROOT --> FH[FileHandler<br/>logs/app.log]
    ROOT --> QH[QueueHandler<br/>→ GUI display]
    ROOT --> SH[StreamHandler<br/>→ Console/stderr]
    
    FH -->|RotatingFileHandler| DISK[Disk]
    QH -->|Queue| GUI[GUI Log Panel]
```

---

## Log Configuration

```python
import logging
from logging.handlers import RotatingFileHandler
from queue import Queue

def setup_logging(log_queue: Queue, log_dir: Path) -> logging.Logger:
    logger = logging.getLogger("email_auto_download")
    logger.setLevel(logging.DEBUG)
    
    # File handler — rotating, max 5MB × 3 files
    file_handler = RotatingFileHandler(
        log_dir / "app.log",
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))
    
    # Queue handler — stream to GUI
    queue_handler = logging.handlers.QueueHandler(log_queue)
    queue_handler.setLevel(logging.INFO)
    
    logger.addHandler(file_handler)
    logger.addHandler(queue_handler)
    
    return logger
```

---

## Log Format Examples

```
2026-03-10 14:30:01 [INFO    ] scheduler: Starting run (3 rules enabled)
2026-03-10 14:30:02 [INFO    ] gmail_client: Searching: subject:"Viettel" has:attachment
2026-03-10 14:30:03 [INFO    ] gmail_client: Found 3 emails matching rule "Viettel Post"
2026-03-10 14:30:04 [INFO    ] file_downloader: ✅ Downloaded: K26TAN2038744.pdf (135 KB)
2026-03-10 14:30:04 [INFO    ] file_downloader: ⏭ Skipped duplicate: 0104093672-K26.xml
2026-03-10 14:30:05 [WARNING ] file_downloader: Retry 1/3: Connection timeout for bang_ke URL
2026-03-10 14:30:08 [INFO    ] file_downloader: ✅ Downloaded: XHDTD-TTHMNQ2-2602-226.pdf
2026-03-10 14:30:08 [INFO    ] scheduler: Run complete: 5 files, 1 skip, 0 errors (7.2s)
```

---

## Performance Metrics

```python
@dataclass
class PerformanceMetrics:
    """Thu thập qua mỗi lần chạy."""
    run_duration_seconds: float
    emails_scanned: int
    files_downloaded: int
    total_download_size_bytes: int
    api_calls_count: int
    retry_count: int
    
    def to_log_line(self) -> str:
        size_mb = self.total_download_size_bytes / (1024 * 1024)
        return (
            f"Perf: {self.run_duration_seconds:.1f}s, "
            f"{self.emails_scanned} emails, "
            f"{self.files_downloaded} files ({size_mb:.1f} MB), "
            f"{self.api_calls_count} API calls, "
            f"{self.retry_count} retries"
        )
```

---

## Log Rotation Policy

| Setting | Value |
|---------|-------|
| Max file size | 5 MB |
| Backup count | 3 files |
| Total max | 20 MB |
| Encoding | UTF-8 |
| Naming | `app.log`, `app.log.1`, `app.log.2`, `app.log.3` |

---

## Troubleshooting Logs

Khi cần debug, user có thể:
1. Mở `logs/app.log` bằng text editor
2. Tìm dòng `[ERROR]` hoặc `[WARNING]`
3. Xem traceback đầy đủ (ghi ở mức DEBUG)
