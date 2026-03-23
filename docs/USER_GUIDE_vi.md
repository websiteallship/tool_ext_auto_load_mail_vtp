# 📖 Hướng Dẫn Sử Dụng — Email Auto-Download Tool v2.1.0

## Giới Thiệu

Tool tự động tải hóa đơn VAT từ email Gmail. Hỗ trợ nhiều nhà cung cấp (Viettel Post, J&T Express), tải file đính kèm và file từ link trong email.

---

## Bước 1: Kết Nối Gmail

1. Mở app → vào tab **Settings**
2. Bấm **Re-authenticate** (hoặc **Connect Gmail**)
3. Trình duyệt mở → đăng nhập tài khoản Gmail chứa hóa đơn
4. Cấp quyền đọc email → app tự kết nối
5. Trạng thái hiện: `● Connected (email@gmail.com)` = thành công ✅

> 💡 Lần sau mở app sẽ tự kết nối lại, không cần đăng nhập lại.

---

## Bước 2: Cấu Hình Rules

Vào tab **Rules** để bật/tắt loại email cần tải:

| Rule | Mô tả | File tải |
|------|--------|----------|
| 📦 **Viettel Post Invoice** | Hóa đơn + bảng kê chi tiết VTP | .pdf .xml .zip + bảng kê HTML→xlsx |
| 📄 **J&T Express E-Invoice** | Hóa đơn điện tử Thuận Phong | .pdf + .xml (qua link redirect) |
| 📊 **J&T Express COD** | Bảng kê đối soát COD | .xlsx |

### Cách sử dụng:
- **Bật/Tắt rule:** Bấm nút ON/OFF trên mỗi thẻ rule
- **Chọn thư mục lưu:** Bấm **Chọn...** rồi chọn thư mục → mỗi rule lưu vào folder riêng
- **Cấu trúc folder:** File tự động lưu vào subfolder theo tháng, ví dụ: `jt_cod/202603/file.xlsx`

> ⚠️ Rules do lập trình viên cấu hình sẵn. Bạn chỉ cần bật/tắt và chọn thư mục.

---

## Bước 3: Cài Đặt Hệ Thống (MỚI v2.1)

Trong tab **Settings**:

### Hẹn giờ tự động:
1. Tick **☑ Enable automatic checking**
2. Đặt khoảng thời gian (mặc định 30 phút)
3. Dashboard sẽ hiện **⏱ đếm ngược** tới lần chạy tiếp

### System Tray:
- Tick **☑ Minimize to system tray** → đóng cửa sổ sẽ ẩn vào khay hệ thống
- App tiếp tục chạy nền, thông báo Windows khi tải xong

### Khởi động cùng Windows:
- Tick **☑ Khởi động cùng Windows** → app tự chạy khi bật máy

> 💡 Bấm **Save Settings** sau khi thay đổi.

---

## Bước 4: Preview & Chạy Tải (MỚI v2.1)

Vào tab **Dashboard**:

### Preview trước khi tải:
1. Chọn rule trong dropdown **"Chạy rule"**
2. Bấm **👁️ Preview** → app quét email nhưng **KHÔNG tải**
3. Dialog hiện danh sách email + file dự kiến
4. Bấm **▶ Tải ngay** để chạy, hoặc **Đóng** để hủy

### Chạy 1 rule cụ thể:
1. Dropdown **"Chạy rule"** → chọn rule (VD: `📊 J&T Express COD`)
2. Bấm **▶ Run Now** → log hiện quá trình tải

### Chạy tất cả rule đang bật:
1. Dropdown → chọn **"▶ Tất cả rule đang bật"**
2. Bấm **▶ Run Now** → các rule chạy tuần tự

> ⚠️ Rule đang tắt hiện `✗ (TẮT)`. Nếu chọn rule tắt, app sẽ nhắc bật trước.

### Dừng giữa chừng:
- Bấm **⏹ Stop** để dừng ngay

---

## Bước 5: Kết Quả & Lịch Sử

### Dialog "Hoàn tất":
Sau khi chạy xong, dialog hiển thị:
- 📧 Số email tìm thấy  
- 📥 Số file đã tải  
- ⏭ Số file bỏ qua (trùng)  
- Nút mở thư mục cho từng rule đã chạy

### Mở thư mục tải về:
- **Chạy 1 rule:** Bấm nút folder → mở đúng folder rule đó
- **Chạy nhiều rules:** Mỗi rule có 1 nút riêng

### Thống kê trên Dashboard (MỚI v2.1):
- Card **"Hôm nay: N | Tuần: N | Tổng: N"** hiện số file đã tải

### Lịch sử tải file (MỚI v2.1):
- Bấm **📋 Lịch sử** trên Dashboard
- Dialog hiện bảng file đã tải: ngày giờ, tên file, rule, trạng thái
- **Lọc theo rule:** Dropdown filter
- **Xóa lịch sử:** Bấm "Xóa lịch sử"

---

## Bước 6: Mở Folder Bất Kỳ Lúc Nào

Trên Dashboard, bấm **📂 Open Folder ▼** → dropdown hiện:
- `📂 Mặc định: downloads` — folder chung
- `📦 Viettel Post Invoice: viettel_post` — folder VTP
- `📄 J&T Express E-Invoice: jt_e_invoice` — folder J&T hóa đơn
- `📊 J&T Express COD: jt_cod` — folder J&T COD

Chọn mục nào → mở folder đó trong File Explorer.

---

## Reset Lịch Sử Email

Bấm **↻ Reset** trên Dashboard để xóa danh sách email đã xử lý. Lần chạy tiếp sẽ tải lại tất cả email.

---

## FAQ

**Q: Tại sao không thấy email nào?**  
A: Kiểm tra `sender_filter` và `subject_query` trong `config/rules.json` có đúng với email cần tải không.

**Q: File tải về ở đâu?**  
A: Xem folder trong tab Rules (mỗi rule có folder riêng) hoặc bấm **📂 Open Folder** trên Dashboard.

**Q: Tôi muốn thêm loại email mới?**  
A: Liên hệ lập trình viên để tạo handler mới. Sau khi cấu hình xong, rule sẽ xuất hiện trong tab Rules.

**Q: App báo "Rule chưa bật"?**  
A: Vào tab Rules → bấm ON cho rule đó → quay lại Dashboard chạy.

**Q: App ẩn đi đâu?**  
A: Nếu bật "Minimize to tray" → app ẩn xuống khay hệ thống (icon gần đồng hồ). Right-click → Show để mở lại.

---

*Copyright by allship.vn — v2.1.0 (2026-03-23)*
