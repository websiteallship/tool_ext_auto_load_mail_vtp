# CHANGELOG

All notable changes to this project will be documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/).

---

## [2.1.0] — 2026-03-23

### Added
- 👁️ **Dry-Run Preview** — quét email và hiện danh sách file dự kiến (không tải)
  - PreviewDialog: bảng email + file, nút "Tải ngay"
  - `preview_rules()` method trên Scheduler
- 📋 **Download History** — lịch sử file đã tải, lọc theo rule
  - HistoryDialog: bảng file, filter rule, xóa lịch sử
  - `DownloadHistory` class: JSON storage, stats API
- 🔽 **System Tray** — minimize xuống tray, menu Mở/Chạy/Dừng/Thoát
  - `pystray` integration, tray icon thread riêng
- 🔔 **Toast Notification** — Windows notification khi tải xong + app minimize
- 🚀 **Windows Startup** — checkbox tự khởi động cùng Windows
- ⏱️ **Countdown Timer** — đếm ngược tới lần chạy tiếp (auto-schedule)
- 📊 **Stats Summary Card** — "Hôm nay: 12 | Tuần: 45 | Tổng: 230"

---

## [2.0.0] — 2026-03-23

### Added
- 🔌 **Plugin Handler Architecture** — mỗi nhà cung cấp = 1 handler độc lập
  - `BaseEmailHandler` + `ExtractionConfig` (2-tier: data + code)
  - `ViettelPostHandler` — refactor logic VTP hiện có
  - `JTInvoiceHandler` — J&T E-Invoice: follow redirect → PDF/XML
  - `JTCODHandler` — J&T COD: tải attachment .xlsx
  - `GenericHandler` — handler mặc định
  - Handler Registry + factory pattern
- 📂 **Auto-subfolder theo tháng** — dựa vào ngày email → `{YYYYMM}/` subfolder
- 📁 **Per-rule output folder** — mỗi rule có folder picker riêng
- 🎯 **Per-rule run** — chọn chạy 1 rule cụ thể hoặc tất cả rule đang bật
  - Dropdown "Chạy rule" trên Dashboard
  - Rule tắt hiện `✗ (TẮT)`, chọn sẽ báo phải enable trước
  - `Scheduler.run_rules(rules)` — API mới hỗ trợ chạy rule chỉ định
- 📂 **Smart Open Folder** — dropdown hiện folder riêng của từng rule
  - Tự sync khi chuyển tab hoặc toggle rule
- 📊 **CompletionDialog nâng cấp** — per-rule folder buttons
  - Chạy 1 rule → 1 nút mở đúng folder rule đó
  - Chạy nhiều rule → nhiều nút, mỗi rule 1 nút với icon+tên+folder
  - Nút folder luôn hiện kể cả khi tất cả file trùng (skip)
  - Dialog hiển thị chính giữa màn hình
- 🔄 **Tab change sync** — tự reload rules.json khi chuyển tab Dashboard/Rules
- 🛡️ **Error isolation** — 1 rule lỗi không ảnh hưởng rule khác
- 🔀 **Follow redirect** — hỗ trợ tracking URL (J&T)
- 🌐 **Dynamic allowed domains** — mỗi handler khai báo domains riêng
- 🧪 **80 unit tests** — 36 handler tests + 44 existing tests

### Changed
- 🎨 **Rules Tab redesign** — rule cards với switch + description + file types badge
- ❌ **Bỏ user rule creation** — rules do dev cấu hình, user chỉ toggle + chọn folder
- 🗑️ **Bỏ RuleDialog** — không cần add/edit/delete UI nữa
- 🔄 **run_once() refactor** — delegate sang run_rules() (backward compatible)
- 🇻🇳 **Vietnamese localization** — dialog, thông báo, label bằng tiếng Việt

---

## [1.1.0] — 2026-03-11

### Added
- ✅ **Completion Dialog** — hiển thị sau mỗi lần quét/tải
  - 3 trạng thái: thành công (xanh), có lỗi (vàng), không có file mới (xám)
  - Thống kê: email tìm thấy, file đã tải, bỏ qua, lỗi, thời gian
  - **📋 Chi tiết file** — log cuộn hiển thị từng file đã tải (✅) và bỏ qua (⏭)
  - Nút **📂 Xem thư mục đã lưu** — mở File Explorer
- 📊 `RunResult` — thêm `downloaded_files` và `skipped_files` để theo dõi từng file

### Fixed
- 🐛 Fix .exe không tìm thấy email — `dist/config/rules.json` bị lệch `sender_filter` so với source
- 🔄 `build.bat` tự động sync config mới nhất vào `dist/` sau mỗi lần build

---

## [1.0.0] — 2026-03-10

### Added
- 📧 Gmail OAuth2 authentication — token lưu an toàn trong Windows Credential Locker
- 🔍 Email search theo rule cấu hình (subject, sender, label)
- 📎 Tải file đính kèm (PDF, XML, XLSX, ZIP) vào thư mục tùy chọn
- 📊 Trích xuất & tải bảng kê từ link trong nội dung email (vinvoice.viettel.vn)
- 📋 Rule engine — thêm/sửa/xóa/bật/tắt rule qua GUI
- ⏰ Auto scheduler — kiểm tra email tự động theo khoảng thời gian
- ⏭ Duplicate detection — bỏ qua file đã tải
- 🖥️ CustomTkinter GUI — 4 tab (Dashboard, Rules, Settings, Hướng Dẫn)
- 📊 Real-time progress bar & log hiển thị chi tiết
- 📂 Nút Open Folder trên Dashboard
- 🔐 Credential storage — keyring cho token, bundled credentials.json
- 📦 Build thành 1 file .exe portable (~44 MB) qua PyInstaller
- 🧪 44 unit tests (file_downloader, link_extractor, rule_engine)

---

## [0.0.1] — 2026-03-10

### Added
- 📋 Project foundation documentation (17 files in `docs/`)
- 🛠️ Agent skills installed (11 skills in `.agent/skills/`)
- 📐 Implementation plan created
