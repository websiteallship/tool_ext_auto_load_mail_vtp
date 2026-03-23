# 📧 Email Auto-Download Tool v2.1.0

Tự động tải hóa đơn điện tử và bảng kê từ email Gmail.  
Hỗ trợ nhiều nhà cung cấp: **Viettel Post**, **J&T Express**.  
Đóng gói thành **1 file .exe** duy nhất — không cần cài Python.

## ✨ Tính Năng (v2.1)

- 🔌 **Multi-provider** — plugin handler cho từng nhà cung cấp (VTP, J&T Invoice, J&T COD)
- 🎯 **Chạy từng rule** — chọn 1 rule cụ thể hoặc chạy tất cả từ Dashboard
- 📁 **Per-rule folder** — mỗi rule lưu file vào thư mục riêng
- 📂 **Smart Open Folder** — dropdown hiện folder từng rule, click mở nhanh
- 📅 **Auto-subfolder** — tự tạo subfolder theo tháng (`202603/`)
- 📊 **CompletionDialog** — per-rule folder buttons, chi tiết file đã tải/skip
- 👁️ **Preview** — quét email xem trước danh sách file dự kiến (không tải)
- 📋 **Lịch sử tải** — bảng file đã tải, lọc theo rule, xóa lịch sử
- 📊 **Stats card** — "Hôm nay | Tuần | Tổng" trên Dashboard
- 🔽 **System Tray** — minimize xuống khay hệ thống, menu nhanh
- 🔔 **Toast notification** — thông báo Windows khi tải xong
- 🚀 **Windows Startup** — tự chạy khi bật máy
- ⏱️ **Countdown timer** — đếm ngược tới lần chạy tiếp
- ⏰ **Lịch chạy tự động** — kiểm tra email mới theo khoảng thời gian tùy chỉnh
- ⏭ **Bỏ qua file trùng** — không tải lại file đã có
- 🖥️ **GUI hiện đại** — Light theme, CustomTkinter, Vietnamese labels
- 🔐 **Bảo mật** — Token lưu trong Windows Credential Locker (keyring)

## 🚀 Sử Dụng Nhanh

1. Chạy `EmailAutoDownload.exe` (hoặc `python app.py`)
2. Tab **Settings** → **Authenticate Gmail** → đăng nhập Google
3. Tab **Rules** → bật rule cần dùng → chọn thư mục lưu
4. Tab **Dashboard** → chọn rule → **👁️ Preview** xem trước → **▶ Run Now**
5. Dialog hoàn tất → bấm nút folder tương ứng để xem file

> 📖 Xem hướng dẫn chi tiết: [docs/USER_GUIDE_vi.md](docs/USER_GUIDE_vi.md)

## 📦 Rules Có Sẵn

| Rule | Mô tả | File tải |
|------|--------|----------|
| 📦 Viettel Post Invoice | Hóa đơn + bảng kê VTP | .pdf .xml .zip + bảng kê HTML→xlsx |
| 📄 J&T Express E-Invoice | Hóa đơn điện tử Thuận Phong | .pdf + .xml (follow redirect) |
| 📊 J&T Express COD | Bảng kê đối soát COD | .xlsx |

## 🛠️ Phát Triển

### Yêu cầu
- Python 3.11+
- Google Cloud Project với Gmail API enabled
- File `credentials.json` (xem [CREDENTIALS_GUIDE.md](CREDENTIALS_GUIDE.md))

### Cài đặt

```bash
git clone <repo>
cd ext_auto_load_mail
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

### Cấu hình Rules (`config/rules.json`)

```json
[
  {
    "name": "Viettel Post Invoice",
    "enabled": true,
    "handler_type": "viettel_post",
    "subject_query": "Tổng công ty Cổ phần Bưu Chính Viettel",
    "sender_filter": "ketoan.allship@gmail.com",
    "label_filter": "INBOX",
    "output_folder": "D:/TOOL AI/TOOL_AUTO_DOWNLOAD_VAT/viettel_post",
    "max_emails": 50,
    "description": "Hóa đơn + bảng kê chi tiết Viettel Post",
    "icon": "📦",
    "file_types": "📎 .pdf .xml .zip + 🔗 bảng kê HTML→xlsx"
  }
]
```

### Settings (`config/settings.json`)

| Tùy chọn | Mô tả | Mặc định |
|-----------|--------|----------|
| `output_dir` | Thư mục lưu file mặc định | `downloads` |
| `auto_schedule_enabled` | Bật lịch tự động | `false` |
| `schedule_interval_minutes` | Khoảng cách (phút) | `30` |
| `skip_duplicates` | Bỏ qua file trùng | `true` |

## 📦 Build .exe

```bash
build.bat
# hoặc: pyinstaller EmailAutoDownload.spec --clean --noconfirm
```

Output: `dist/EmailAutoDownload.exe` (~44 MB)

## 🧪 Tests

```bash
pytest tests/ -v
# 80 tests — handlers, file_downloader, link_extractor, rule_engine
```

## 📁 Cấu Trúc

```
ext_auto_load_mail/
├── app.py                  # GUI chính (CustomTkinter)
├── src/
│   ├── models.py           # Data models & exceptions
│   ├── gmail_client.py     # Gmail API client (OAuth2)
│   ├── scheduler.py        # Điều phối xử lý email + run_rules()
│   ├── rule_engine.py      # Quản lý rules (JSON config)
│   ├── link_extractor.py   # Trích xuất link bảng kê
│   ├── file_downloader.py  # Tải & lưu file
│   └── handlers/           # Plugin handlers (NEW v2.0)
│       ├── base.py         # BaseEmailHandler + ExtractionConfig
│       ├── generic.py      # GenericHandler (mặc định)
│       ├── viettel_post.py # ViettelPostHandler
│       └── jt_express.py   # JTInvoiceHandler + JTCODHandler
├── config/
│   ├── rules.json          # Cấu hình rules (dev-config)
│   └── settings.json       # Cài đặt ứng dụng
├── docs/                   # Tài liệu chi tiết (20 files)
├── tests/                  # 80 unit tests
├── build.bat               # Script build .exe
└── requirements.txt        # Dependencies
```

## 📄 Tài Liệu

- [docs/USER_GUIDE_vi.md](docs/USER_GUIDE_vi.md) — Hướng dẫn sử dụng (tiếng Việt)
- [docs/CHANGELOG.md](docs/CHANGELOG.md) — Lịch sử thay đổi
- [docs/INDEX.md](docs/INDEX.md) — Danh mục tài liệu
- [CREDENTIALS_GUIDE.md](CREDENTIALS_GUIDE.md) — Hướng dẫn tạo Google credentials

## 📝 License

MIT — *Copyright by allship.vn*
