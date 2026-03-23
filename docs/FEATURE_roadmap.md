# FEATURE: Roadmap & Extensions (v2.1)

> Skills áp dụng: `04_architecture`

## Mục Đích

Lộ trình phát triển tính năng, chia thành MVP và các phase mở rộng.

---

## Phase 1: MVP (v1.0) ✅ HOÀN THÀNH

| Tính năng | Module | Trạng thái |
|-----------|--------|-----------|
| Kết nối Gmail (OAuth2) | `gmail_client.py` | ✅ |
| Tìm email theo tiêu đề | `gmail_client.py` | ✅ |
| Tải file đính kèm (PDF, XML) | `file_downloader.py` | ✅ |
| Trích xuất link bảng kê | `link_extractor.py` | ✅ |
| Tải bảng kê từ URL | `file_downloader.py` | ✅ |
| 1 Rule mặc định (Viettel Post) | `rule_engine.py` | ✅ |
| GUI cơ bản (Dashboard + Settings) | `app.py` | ✅ |
| Log real-time | `scheduler.py` | ✅ |
| Build .exe | `build.bat` | ✅ |

---

## Phase 2–3: Multi-Rule & Automation (v1.1–1.2) ✅ HOÀN THÀNH

| Tính năng | Trạng thái |
|-----------|-----------|
| Nhiều rule email + GUI Rules tab | ✅ |
| Completion Dialog (chi tiết file) | ✅ |
| Chạy tự động theo lịch | ✅ |
| Duplicate detection | ✅ |

---

## Phase 4: Plugin Architecture (v2.0) ✅ HOÀN THÀNH — 2026-03-23

| Tính năng | Trạng thái |
|-----------|-----------|
| Handler System (Base + Registry + 4 handlers) | ✅ |
| Rules Tab redesign (switch + folder picker) | ✅ |
| Per-rule run selector + Smart Open Folder | ✅ |
| CompletionDialog per-rule folder buttons | ✅ |
| Auto-subfolder theo tháng ({YYYYMM}/) | ✅ |
| Error isolation + Tab change sync | ✅ |
| 80 unit tests | ✅ |

---

## Phase 5: UX Enhancement (v2.1) ✅ HOÀN THÀNH

### 5.1 Preview & History

| Tính năng | Mô tả | Module |
|-----------|-------|--------|
| ✅ 👁️ Dry-run Preview | Quét email → hiện preview (không tải) → bấm "Tải ngay" | `scheduler.py`, `app.py` |
| ✅ 📋 Download History | Lịch sử file đã tải, lọc rule/ngày | `download_history.py`, `app.py` |
| ✅ 📊 Stats Summary | Card "Hôm nay: 12 | Tuần: 45 | Tổng: 230" trên Dashboard | `app.py` |

### 5.2 System Integration

| Tính năng | Mô tả | Module |
|-----------|-------|--------|
| ✅ 🔽 System Tray | Minimize → icon tray, menu Mở/Chạy/Dừng/Thoát | `tray_icon.py`, `app.py` |
| ✅ 🔔 Toast Notification | Windows notification khi tải xong + app minimize | `tray_icon.py`, `app.py` |
| ✅ 🚀 Windows Startup | Tự khởi động cùng Windows (checkbox) | `app.py` |

### 5.3 Dashboard UX

| Tính năng | Mô tả | Module |
|-----------|-------|--------|
| ✅ ⏱️ Countdown Timer | "Chạy tiếp sau: 24:35" khi auto-schedule bật | `app.py` |

---

## Phase 6: Advanced (v3.0)

| Tính năng | Mô tả |
|-----------|-------|
| PDF data extraction | Trích xuất dữ liệu từ hóa đơn PDF |
| Multi-account Gmail | Nhiều tài khoản Gmail |
| IMAP support | Hỗ trợ email ngoài Gmail |
| Dark mode | Theme tối cho GUI |

---

## Nguyên Tắc Phát Triển

1. **Ship MVP first** — tải được file = thành công ✅
2. **User feedback** — thêm tính năng theo nhu cầu thực
3. **Backwards compatible** — config cũ phải chạy được trên version mới
4. **Plugin per provider** — mỗi nhà cung cấp = 1 handler độc lập
