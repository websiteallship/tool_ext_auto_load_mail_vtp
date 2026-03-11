# SPECS: Dependencies & Tech Stack

> Skills áp dụng: `02_python-pro`, `11_python-packaging`

## Mục Đích

Danh sách đầy đủ dependencies, lý do chọn, và phiên bản tối thiểu.

---

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Language | Python | 3.11+ |
| GUI | CustomTkinter | 5.2+ |
| Gmail API | google-api-python-client | 2.100+ |
| Auth | google-auth-oauthlib | 1.2+ |
| HTTP | requests | 2.31+ |
| HTML Parsing | BeautifulSoup4 + lxml | 4.12+ |
| Excel | openpyxl | 3.1+ |
| Scheduling | schedule | 1.2+ |
| Credential Store | keyring | 25.0+ |
| Retry Logic | tenacity | 8.2+ |
| Env Config | python-dotenv | 1.0+ |
| Image/Icon | Pillow | 10.0+ |
| Packaging | PyInstaller | 6.0+ |
| Linting | ruff | 0.4+ |
| Type Checking | mypy | 1.8+ |
| Testing | pytest | 8.0+ |

---

## Dependency Justification

### Core

| Package | Tại sao chọn | Thay thế |
|---------|-------------|----------|
| `google-api-python-client` | Official Google SDK | Không có |
| `requests` | HTTP requests đơn giản | httpx (heavier) |
| `beautifulsoup4` | Parse HTML email body | lxml trực tiếp |
| `keyring` | Cross-platform secure credential storage | File encrypt (riskier) |
| `tenacity` | Retry logic linh hoạt | backoff (ít tính năng) |

### GUI

| Package | Tại sao chọn | Thay thế |
|---------|-------------|----------|
| `customtkinter` | Modern Tkinter UI, dark mode | PyQt (GPL), tkinter (ugly) |
| `Pillow` | Xử lý icon cho GUI | N/A |

### Dev Tools

| Package | Tại sao chọn | Thay thế |
|---------|-------------|----------|
| `ruff` | Nhanh, thay black+isort+flake8 | black + isort |
| `mypy` | Static type checking | pyright |
| `pytest` | Testing framework chuẩn | unittest |
| `PyInstaller` | Build .exe portable | cx_Freeze, Nuitka |

---

## `requirements.txt`

```
# Core
google-api-python-client>=2.100.0
google-auth-httplib2>=0.2.0
google-auth-oauthlib>=1.2.0
requests>=2.31.0
beautifulsoup4>=4.12.0
lxml>=5.0.0

# GUI
customtkinter>=5.2.0
Pillow>=10.0.0

# Infrastructure
keyring>=25.0.0
tenacity>=8.2.0
python-dotenv>=1.0.0
openpyxl>=3.1.0
schedule>=1.2.0
```

### `requirements-dev.txt`

```
# Testing
pytest>=8.0.0
pytest-cov>=4.1.0
pytest-asyncio>=0.23.0

# Linting & Formatting
ruff>=0.4.0
mypy>=1.8.0

# Packaging
pyinstaller>=6.0.0
```

---

## Python Version Policy

- **Minimum:** Python 3.11 (for `tomllib`, performance improvements)
- **Recommended:** Python 3.12+  
- **Tested:** 3.11, 3.12, 3.13

---

## Security Notes

- ✅ Tất cả packages từ PyPI official
- ✅ Pin major versions (>=X.Y.0)
- ⚠️ Chạy `pip audit` định kỳ để check vulnerabilities
- ⚠️ Không dùng `pip install --trusted-host` (nguy hiểm)
