# 📧 Email Auto-Download Tool

Tự động tải hóa đơn điện tử và bảng kê từ email Gmail.  
Đóng gói thành **1 file .exe** duy nhất — không cần cài Python.

## ✨ Tính Năng

- 🔍 **Tìm email thông minh** — lọc theo tiêu đề, người gửi, nhãn Gmail
- 📎 **Tải file đính kèm** — PDF, XML, XLSX, ZIP
- 📊 **Trích xuất bảng kê** — tự tìm & tải link "chi tiết bảng kê" từ nội dung email
- 📋 **Quản lý nhiều rule** — Viettel Post, VNPT, hay bất kỳ nguồn nào
- ⏰ **Lịch chạy tự động** — kiểm tra email mới theo khoảng thời gian tùy chỉnh
- ⏭ **Bỏ qua file trùng** — không tải lại file đã có
- ✅ **Dialog hoàn tất** — hiển thị chi tiết file đã tải / bỏ qua, nút mở thư mục
- 🖥️ **GUI hiện đại** — Light theme, CustomTkinter
- 🔐 **Bảo mật** — Token lưu trong Windows Credential Locker (keyring)

## 🚀 Sử Dụng Nhanh (File .exe)

1. Chạy `EmailAutoDownload.exe`
2. Vào tab **Settings** → nhấn **Authenticate Gmail** → đăng nhập Google
3. Vào tab **Rules** → tạo rule lọc email
4. Về tab **Dashboard** → nhấn **▶ Run Now**
5. Xem kết quả trong dialog hoàn tất → nhấn **📂 Xem thư mục đã lưu**

> 💡 Chỉ cần **1 file .exe** để chia sẻ cho người dùng khác.  
> Người nhận cần tự đăng nhập Gmail và tạo rules riêng.

## 🛠️ Phát Triển

### Yêu cầu
- Python 3.11+
- Google Cloud Project với Gmail API enabled
- File `credentials.json` (xem [CREDENTIALS_GUIDE.md](CREDENTIALS_GUIDE.md))

### Cài đặt

```bash
# Clone & setup
git clone <repo>
cd ext_auto_load_mail
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Chạy
python app.py
```

### Cấu hình

#### Email Rules (`config/rules.json`)
```json
[
  {
    "name": "Viettel Post Invoice",
    "enabled": true,
    "subject_query": "Tổng công ty Cổ phần Bưu Chính Viettel",
    "sender_filter": "",
    "label_filter": "INBOX",
    "download_attachments": true,
    "download_bang_ke": true,
    "max_emails": 50
  }
]
```

#### Settings (`config/settings.json`)
| Tùy chọn | Mô tả | Mặc định |
|-----------|--------|----------|
| `output_dir` | Thư mục lưu file | `downloads` |
| `auto_schedule_enabled` | Bật lịch tự động | `false` |
| `schedule_interval_minutes` | Khoảng cách (phút) | `30` |
| `skip_duplicates` | Bỏ qua file trùng | `true` |

## 📦 Build .exe

```bash
# Cách 1: Dùng build script
build.bat

# Cách 2: Dùng spec file
pyinstaller EmailAutoDownload.spec --clean --noconfirm
```

Output: `dist/EmailAutoDownload.exe` (~44 MB)

## 🧪 Tests

```bash
pytest tests/ -v
# 44 tests — file_downloader, link_extractor, rule_engine
```

## 📁 Cấu Trúc

```
ext_auto_load_mail/
├── app.py                  # GUI chính (CustomTkinter)
├── src/
│   ├── models.py           # Data models & exceptions
│   ├── gmail_client.py     # Gmail API client (OAuth2)
│   ├── scheduler.py        # Điều phối xử lý email
│   ├── rule_engine.py      # Quản lý rules (CRUD)
│   ├── link_extractor.py   # Trích xuất link bảng kê
│   └── file_downloader.py  # Tải & lưu file
├── config/
│   ├── rules.json          # Cấu hình rules
│   └── settings.json       # Cài đặt ứng dụng
├── tests/                  # Unit tests
├── build.bat               # Script build .exe
├── EmailAutoDownload.spec  # PyInstaller spec
├── requirements.txt        # Dependencies
└── credentials.json        # Google OAuth client ID
```

## 📄 Tài Liệu

- [CREDENTIALS_GUIDE.md](CREDENTIALS_GUIDE.md) — Hướng dẫn tạo Google credentials
- [docs/](docs/) — Tài liệu chi tiết

## 📝 License

MIT
