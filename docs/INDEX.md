# Project Documentation Index

## Email Auto-Download Tool — Viettel Post

> Tài liệu nền tảng cho dự án tự động tải hóa đơn từ Gmail

---

## 📋 Danh Mục Tài Liệu

### 🔵 CORE — Module Core (API contracts, data models)

| File | Mô tả |
|------|--------|
| [CORE_gmail_client.md](CORE_gmail_client.md) | Gmail connection, OAuth2, search, attachments |
| [CORE_link_extractor.md](CORE_link_extractor.md) | HTML parsing, trích link bảng kê |
| [CORE_file_downloader.md](CORE_file_downloader.md) | Download files, async batch, retry |
| [CORE_rule_engine.md](CORE_rule_engine.md) | Multi-rule management, JSON config |

### 🏗️ ARCH — Kiến Trúc

| File | Mô tả |
|------|--------|
| [ARCH_system_architecture.md](ARCH_system_architecture.md) | Layer architecture, ADRs, folder structure |
| [ARCH_data_flow.md](ARCH_data_flow.md) | Data flow diagrams, state management |

### ✨ FEATURE — Tính Năng

| File | Mô tả |
|------|--------|
| [FEATURE_gui_application.md](FEATURE_gui_application.md) | GUI wireframes, 4 tabs, threading model |
| [FEATURE_scheduler.md](FEATURE_scheduler.md) | Auto-scheduling, state machine |
| [FEATURE_roadmap.md](FEATURE_roadmap.md) | Roadmap v1.0 → v2.0 |

### 📐 SPECS — Tiêu Chuẩn Kỹ Thuật

| File | Mô tả |
|------|--------|
| [SPECS_security_credentials.md](SPECS_security_credentials.md) | Token storage, credential management |
| [SPECS_error_handling.md](SPECS_error_handling.md) | Exception hierarchy, retry, resilience |
| [SPECS_dependencies.md](SPECS_dependencies.md) | Tech stack, packages, versions |
| [SPECS_testing_strategy.md](SPECS_testing_strategy.md) | Test pyramid, unit tests, coverage |
| [SPECS_coding_standards.md](SPECS_coding_standards.md) | Naming, functions, Git conventions |

### 🔧 OPS — Vận Hành

| File | Mô tả |
|------|--------|
| [OPS_build_packaging.md](OPS_build_packaging.md) | PyInstaller, build.bat, distribution |
| [OPS_logging_monitoring.md](OPS_logging_monitoring.md) | Logging architecture, rotation policy |

---

## 🎯 Skills Áp Dụng

| # | Skill | Sử dụng trong |
|---|-------|---------------|
| 01 | `gmail-automation` | CORE_gmail_client |
| 02 | `python-pro` | Tất cả modules |
| 03 | `web-scraper` | CORE_link_extractor, CORE_file_downloader |
| 04 | `architecture` | ARCH_* |
| 05 | `async-python-patterns` | CORE_file_downloader, FEATURE_scheduler |
| 06 | `secrets-management` | SPECS_security_credentials |
| 07 | `python-performance-optimization` | OPS_logging_monitoring |
| 08 | `clean-code` | SPECS_coding_standards, tất cả CORE_* |
| 09 | `error-handling-patterns` | SPECS_error_handling, tất cả CORE_* |
| 10 | `documentation` | INDEX này + tất cả docs |
| 11 | `python-packaging` | OPS_build_packaging, SPECS_dependencies |
