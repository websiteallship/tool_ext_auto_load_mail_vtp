# FEATURE: GUI Application

> Skills áp dụng: `02_python-pro`, `08_clean-code`

## Mục Đích

Giao diện người dùng desktop sử dụng CustomTkinter, cho phép cấu hình rule, chạy thủ công/tự động, và theo dõi tiến trình.

---

## Thiết Kế 4 Tabs

### Tab 1: Dashboard

```
┌──────────────────────────────────────────┐
│  📊 Dashboard                            │
├──────────────────────────────────────────┤
│                                          │
│  [▶ Run Now]  [⏸ Stop]  [🔄 Refresh]    │
│                                          │
│  Status: ● Running / ● Idle / ● Error   │
│  Last run: 2026-03-10 14:30:05           │
│  Next run: 2026-03-10 15:00:00           │
│                                          │
│  ┌────────────────────────────────────┐  │
│  │ Log Output (real-time)            │  │
│  │ [14:30:01] Searching emails...    │  │
│  │ [14:30:03] Found 3 emails         │  │
│  │ [14:30:04] ✅ K26TAN2038744.pdf   │  │
│  │ [14:30:05] ✅ Bảng kê downloaded  │  │
│  │ [14:30:05] Done. 5 files saved.   │  │
│  └────────────────────────────────────┘  │
│                                          │
│  Summary: 3 emails | 5 files | 0 errors  │
└──────────────────────────────────────────┘
```

### Tab 2: Rules

```
┌──────────────────────────────────────────┐
│  📋 Email Rules                          │
├──────────────────────────────────────────┤
│                                          │
│  [+ Add Rule]  [Import]  [Export]        │
│                                          │
│  ┌────────────────────────────────────┐  │
│  │ ☑ Viettel Post Invoice           │  │
│  │   Subject: Tổng công ty Cổ phần..│  │
│  │   From: noreply@viettelpost...    │  │
│  │   Folder: downloads/viettel_post  │  │
│  │   [Edit] [Delete]                 │  │
│  ├────────────────────────────────────┤  │
│  │ ☐ VNPT Invoice (disabled)        │  │
│  │   Subject: VNPT hóa đơn          │  │
│  │   [Edit] [Delete] [Enable]        │  │
│  └────────────────────────────────────┘  │
└──────────────────────────────────────────┘
```

### Tab 3: Settings

```
┌──────────────────────────────────────────┐
│  ⚙️ Settings                             │
├──────────────────────────────────────────┤
│                                          │
│  Gmail Authentication                    │
│  Status: ● Connected (ketoan@gmail.com)  │
│  [Re-authenticate]  [Disconnect]         │
│                                          │
│  ──────────────────────────────────────  │
│                                          │
│  Download Folder: [D:\Downloads\invoices]│
│  [Browse...]                             │
│                                          │
│  ──────────────────────────────────────  │
│                                          │
│  Auto Schedule                           │
│  ☑ Enable automatic checking             │
│  Interval: [30] minutes                  │
│                                          │
│  ──────────────────────────────────────  │
│                                          │
│  Duplicate Check                         │
│  ☑ Skip already downloaded files         │
│  ☑ Mark processed emails with label      │
│  Label name: [AutoDownloaded]            │
│                                          │
└──────────────────────────────────────────┘
```

### Tab 4: History

```
┌──────────────────────────────────────────┐
│  📁 Download History                     │
├──────────────────────────────────────────┤
│                                          │
│  Search: [________________] [🔍]        │
│  Filter: [All Rules ▼] [All Dates ▼]   │
│                                          │
│  ┌────┬──────────┬──────────┬────────┐  │
│  │Date│ Filename │ Rule     │ Status │  │
│  ├────┼──────────┼──────────┼────────┤  │
│  │3/10│K26TAN..  │Viettel   │ ✅     │  │
│  │3/10│0104..xml │Viettel   │ ✅     │  │
│  │3/10│bangke..  │Viettel   │ ✅     │  │
│  │3/09│K26TAN..  │Viettel   │ ⏭ Skip│  │
│  └────┴──────────┴──────────┴────────┘  │
│                                          │
│  Total: 47 files | [Open Folder]        │
│  [Export to Excel]                       │
└──────────────────────────────────────────┘
```

---

## Threading Model

```python
import threading
from queue import Queue

class AppController:
    def __init__(self):
        self.log_queue = Queue()  # Thread-safe log messages
        self.is_running = False
    
    def run_now(self):
        """Chạy processing trên background thread."""
        if self.is_running:
            return
        
        self.is_running = True
        thread = threading.Thread(
            target=self._process_emails,
            daemon=True
        )
        thread.start()
    
    def _process_emails(self):
        """Background thread — KHÔNG gọi GUI trực tiếp."""
        try:
            # ... processing logic ...
            self.log_queue.put(("info", "Found 3 emails"))
        finally:
            self.is_running = False
    
    def poll_logs(self):
        """Gọi từ GUI main loop mỗi 100ms."""
        while not self.log_queue.empty():
            level, message = self.log_queue.get_nowait()
            self.update_log_display(level, message)
```

**Nguyên tắc:**
- GUI chỉ chạy trên **main thread**
- Processing chạy trên **daemon thread**
- Giao tiếp qua **Queue** (thread-safe)
- Dùng `after()` của Tkinter để poll queue

---

## Dependencies

```
customtkinter>=5.2.0
Pillow>=10.0.0  # cho icons
```
