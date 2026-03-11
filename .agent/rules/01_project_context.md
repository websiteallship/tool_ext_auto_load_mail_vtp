# Project: Email Auto-Download Tool

## Overview
Desktop application (Python + CustomTkinter) to automate downloading invoices and attachments from Gmail emails. Primary use case: Viettel Post e-invoices with "chi tiết bảng kê" links.

## Tech Stack
- **Language:** Python 3.11+
- **GUI:** CustomTkinter
- **Gmail:** google-api-python-client (OAuth2)
- **HTML Parsing:** BeautifulSoup4 + lxml
- **HTTP:** requests
- **Credentials:** keyring (Windows Credential Locker)
- **Retry:** tenacity
- **Packaging:** PyInstaller

## Project Structure
```
ext_auto_load_mail/
├── app.py                 # GUI entry point
├── src/                   # Core business logic
│   ├── gmail_client.py    # Gmail API connection
│   ├── link_extractor.py  # HTML link parsing
│   ├── file_downloader.py # File download operations
│   ├── rule_engine.py     # Multi-rule email processing
│   ├── scheduler.py       # Auto-scheduling
│   └── models.py          # Shared dataclasses
├── config/                # JSON configuration files
├── downloads/             # Downloaded files (per-rule subfolders)
├── logs/                  # Application logs
├── tests/                 # pytest unit tests
└── docs/                  # Foundation documentation
```

## Architecture
- **3-Layer:** GUI → Core → Infrastructure
- **GUI layer** never contains business logic
- **Core layer** is independent of GUI framework
- **Data-driven rules** — new email types require only JSON config, not new code

## Documentation
All technical specs are in `docs/`. Always reference:
- `docs/CORE_*.md` for module API contracts
- `docs/ARCH_*.md` for architecture decisions
- `docs/SPECS_*.md` for technical standards
- `docs/OPS_*.md` for build and operations
