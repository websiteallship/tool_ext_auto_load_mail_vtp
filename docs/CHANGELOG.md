# CHANGELOG

All notable changes to this project will be documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/).

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

### Changed
- 🗑️ Loại bỏ tab History — gộp vào Dashboard
- 📂 Gộp thư mục tải — dùng chung 1 download folder thay vì per-rule

---

## [0.0.1] — 2026-03-10

### Added
- 📋 Project foundation documentation (17 files in `docs/`)
  - CORE: gmail_client, link_extractor, file_downloader, rule_engine
  - ARCH: system_architecture, data_flow
  - FEATURE: gui_application, scheduler, roadmap
  - SPECS: security_credentials, error_handling, dependencies, testing_strategy, coding_standards
  - OPS: build_packaging, logging_monitoring
- 🛠️ Agent skills installed (11 skills in `.agent/skills/`)
- 📏 Agent rules defined (8 rules in `.agent/rules/`)
- 📐 Implementation plan created
