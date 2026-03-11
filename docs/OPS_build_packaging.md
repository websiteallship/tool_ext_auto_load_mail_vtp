# OPS: Build & Packaging

> Skills áp dụng: `11_python-packaging`, `02_python-pro`

## Mục Đích

Hướng dẫn build và đóng gói ứng dụng thành file `.exe` dành cho Windows, không cần cài Python.

---

## Chiến Lược Phân Phối Credentials

### Cách 1: Bundle `credentials.json` vào .exe (★ Khuyên dùng cho nội bộ)

**Nguyên lý:**
- `credentials.json` chứa **Client ID/Secret** của Google Cloud project → thông tin **public**, không nhạy cảm
- `token.json` chứa **access token** sau khi đăng nhập → **nhạy cảm**, tự động tạo riêng cho mỗi người dùng
- Khi bundle `credentials.json` → người dùng chỉ cần **mở app → đăng nhập Gmail** → sử dụng ngay

**Luồng hoạt động:**

```
Người dùng mở app.exe
        ↓
credentials.json đã có sẵn (bundled)
        ↓
App hiển thị "Kết nối Gmail" → mở trình duyệt
        ↓
Người dùng đăng nhập Gmail → cho phép quyền
        ↓
token.json tự động tạo trong thư mục app
        ↓
✅ Sử dụng bình thường
```

**Cách chuẩn bị:**

1. Đặt `credentials.json` trong thư mục gốc project
2. Build bằng PyInstaller với `--add-data "credentials.json;."`
3. Code tự tìm `credentials.json` theo thứ tự:
   - Thư mục hiện tại (cạnh .exe)
   - Bundled trong .exe (via `sys._MEIPASS`)

**Cập nhật `gmail_client.py` — hỗ trợ bundled path:**

```python
import sys
from pathlib import Path

def _find_credentials() -> Path:
    """Tìm credentials.json — hỗ trợ cả dev và bundled .exe"""
    # 1. Thư mục hiện tại (cho phép user override)
    local = Path("credentials.json")
    if local.exists():
        return local

    # 2. Bundled trong PyInstaller .exe
    if hasattr(sys, '_MEIPASS'):
        bundled = Path(sys._MEIPASS) / "credentials.json"
        if bundled.exists():
            return bundled

    raise FileNotFoundError(
        "Không tìm thấy credentials.json. "
        "Vào Settings → 📂 Nhập credentials.json"
    )
```

**Giới hạn:**
- Google cho phép **100 user chưa xác minh** trên cùng 1 project
- Nếu cần nhiều hơn → đăng ký xác minh app với Google hoặc dùng Cách 2

### Cách 2: Người dùng tự import (cho phân phối rộng)

- Không bundle `credentials.json` vào .exe
- App có sẵn nút **📂 Nhập credentials.json** trong Settings tab
- Gửi kèm file hoặc hướng dẫn tạo trên Google Cloud Console

---

## Project Configuration

### `pyproject.toml`

```toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "email-auto-download"
version = "1.0.0"
description = "Tự động tải hóa đơn Viettel Post từ Gmail"
requires-python = ">=3.11"
dependencies = [
    "google-api-python-client>=2.100.0",
    "google-auth-httplib2>=0.2.0",
    "google-auth-oauthlib>=1.2.0",
    "customtkinter>=5.2.0",
    "requests>=2.31.0",
    "beautifulsoup4>=4.12.0",
    "lxml>=5.0.0",
    "openpyxl>=3.1.0",
    "schedule>=1.2.0",
    "keyring>=25.0.0",
    "tenacity>=8.2.0",
    "python-dotenv>=1.0.0",
    "Pillow>=10.0.0",
]

[project.scripts]
email-auto-download = "app:main"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP"]

[tool.mypy]
python_version = "3.11"
strict = true
```

---

## Build Script (`build.bat`)

```batch
@echo off
echo ========================================
echo    Email Auto-Download Tool - Build
echo ========================================

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install Python 3.11+
    exit /b 1
)

REM Create virtual environment
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate venv
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
pip install pyinstaller

REM Build executable (★ credentials.json bundled)
echo Building executable...
pyinstaller ^
    --onefile ^
    --windowed ^
    --name "EmailAutoDownload" ^
    --icon "assets/icon.ico" ^
    --add-data "credentials.json;." ^
    --add-data "config;config" ^
    --hidden-import "charset_normalizer" ^
    --hidden-import "keyring.backends.Windows" ^
    --hidden-import "customtkinter" ^
    --hidden-import "PIL._tkinter_finder" ^
    --hidden-import "openpyxl" ^
    app.py

echo ========================================
echo Build complete: dist/EmailAutoDownload.exe
echo ========================================
pause
```

---

## PyInstaller Spec File (`build.spec`)

```python
# Cho trường hợp build phức tạp
a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('credentials.json', '.'),   # ★ Bundle credentials
        ('config', 'config'),
        ('assets', 'assets'),
    ],
    hiddenimports=[
        'charset_normalizer',
        'keyring.backends.Windows',
        'customtkinter',
        'PIL._tkinter_finder',
        'openpyxl',
    ],
    noarchive=False,
)
```

---

## Known Build Issues

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: charset_normalizer` | `--hidden-import charset_normalizer` |
| CustomTkinter themes missing | `--add-data "venv/Lib/site-packages/customtkinter;customtkinter"` |
| Keyring backend not found | `--hidden-import keyring.backends.Windows` |
| Large exe size (>100MB) | Dùng UPX compression: `--upx-dir upx/` |
| Anti-virus false positive | Sign exe with code signing certificate |
| `credentials.json` not found in .exe | Kiểm tra `--add-data "credentials.json;."` và code `sys._MEIPASS` |

---

## Distribution

### Cách 1 — Bundle credentials (nội bộ)

```
EmailAutoDownload.exe     # Chỉ cần file này, gửi cho người dùng
```

Người nhận: mở .exe → đăng nhập Gmail → sử dụng.

### Cách 2 — Không bundle (phân phối rộng)

```
dist/
├── EmailAutoDownload.exe
├── README.md
├── credentials.json       # Gửi kèm hoặc hướng dẫn tạo
├── config/
│   └── rules.json.example
└── .env.example
```

---

## Bảo Mật Khi Phân Phối

| File | Nhạy cảm? | Bundle vào .exe? |
|------|-----------|-------------------|
| `credentials.json` | ❌ Không (Client ID public) | ✅ Có |
| `token.json` | ✅ Có (access token) | ❌ KHÔNG — tự tạo mỗi user |
| `config/rules.json` | ❌ Không | ✅ Có (config mẫu) |
| `config/settings.json` | ❌ Không | Tuỳ chọn |
| `config/processed_emails.json` | ❌ Không | ❌ KHÔNG — tự tạo |

---

## Development Setup

```bash
# Clone & setup
git clone <repo>
cd ext_auto_load_mail

# Create venv
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run in development
python app.py

# Run tests
pytest tests/ -v

# Lint
ruff check src/ app.py
mypy src/ app.py
```
