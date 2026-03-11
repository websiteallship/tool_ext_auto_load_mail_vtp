# Hướng dẫn lấy credentials.json (Google OAuth2)

File `credentials.json` là thông tin định danh ứng dụng để kết nối Gmail API.

> **Lưu ý:** File này chỉ chứa Client ID (thông tin public), **KHÔNG** chứa mật khẩu hay token truy cập.

---

## Bước 1: Tạo Google Cloud Project

1. Truy cập [Google Cloud Console](https://console.cloud.google.com/)
2. Nhấn **Select a project** → **New Project**
3. Đặt tên project (VD: `Email Auto Download`) → **Create**

## Bước 2: Bật Gmail API

1. Trong menu bên trái → **APIs & Services** → **Library**
2. Tìm **Gmail API** → Nhấn **Enable**

## Bước 3: Cấu hình OAuth Consent Screen

1. **APIs & Services** → **OAuth consent screen**
2. Chọn **External** → **Create**
3. Điền thông tin:
   - **App name:** `Email Auto Download`
   - **User support email:** email của bạn
   - **Developer contact:** email của bạn
4. Nhấn **Save and Continue**
5. Ở trang **Scopes** → **Add or Remove Scopes** → Thêm:
   - `https://www.googleapis.com/auth/gmail.readonly`
   - `https://www.googleapis.com/auth/gmail.modify`
6. Nhấn **Save and Continue** → hoàn tất

## Bước 4: Tạo OAuth Client ID

1. **APIs & Services** → **Credentials**
2. Nhấn **+ Create Credentials** → **OAuth client ID**
3. **Application type:** chọn **Desktop app**
4. **Name:** `Email Auto Download Desktop`
5. Nhấn **Create**
6. Nhấn **⬇ Download JSON**

## Bước 5: Đặt file vào project

1. Đổi tên file đã tải về thành **`credentials.json`**
2. Copy vào **thư mục gốc** của project (cùng cấp với `app.py`)

```
ext_auto_load_mail/
├── app.py
├── credentials.json   ← đặt ở đây
├── config/
├── src/
└── ...
```

---

## Kiểm tra

Chạy app → tab **Settings** → nhấn **🔑 Authenticate Gmail** → trình duyệt mở ra → đăng nhập Gmail → cấp quyền → xong!

> ⚠️ Google hiển thị "Google hasn't verified this app" → Nhấn **Advanced** → **Go to Email Auto Download (unsafe)** → **Continue**. Đây là bình thường vì app chưa được Google xác minh.

---

## Cấu trúc file credentials.json

```json
{
  "installed": {
    "client_id": "xxxx.apps.googleusercontent.com",
    "project_id": "your-project-id",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "client_secret": "GOCSPX-xxxx",
    "redirect_uris": ["http://localhost"]
  }
}
```

## Bảo mật

| File | Nhạy cảm? | Lưu ý |
|------|-----------|-------|
| `credentials.json` | ❌ Không | Client ID public, an toàn để chia sẻ nội bộ |
| `token.json` | ✅ Có | Access token Gmail — KHÔNG chia sẻ |
