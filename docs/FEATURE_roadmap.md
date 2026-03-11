# FEATURE: Roadmap & Extensions

> Skills áp dụng: `04_architecture`

## Mục Đích

Lộ trình phát triển tính năng, chia thành MVP và các phase mở rộng.

---

## Phase 1: MVP (v1.0) ← Đang triển khai

| Tính năng | Module | Trạng thái |
|-----------|--------|-----------|
| Kết nối Gmail (OAuth2) | `gmail_client.py` | ⬜ |
| Tìm email theo tiêu đề | `gmail_client.py` | ⬜ |
| Tải file đính kèm (PDF, XML) | `file_downloader.py` | ⬜ |
| Trích xuất link bảng kê | `link_extractor.py` | ⬜ |
| Tải bảng kê từ URL | `file_downloader.py` | ⬜ |
| 1 Rule mặc định (Viettel Post) | `rule_engine.py` | ⬜ |
| GUI cơ bản (Dashboard + Settings) | `app.py` | ⬜ |
| Log real-time | `scheduler.py` | ⬜ |
| Build .exe | `build.bat` | ⬜ |

---

## Phase 2: Multi-Rule (v1.1)

| Tính năng | Mô tả |
|-----------|-------|
| Nhiều rule email | Hỗ trợ VNPT, FPT, EVN... |
| GUI Rules tab | Thêm/sửa/xóa rule |
| Import/Export rules | JSON import/export |
| Tổ chức thư mục theo rule | `downloads/<rule_name>/` |

---

## Phase 3: Automation (v1.2)

| Tính năng | Mô tả |
|-----------|-------|
| Chạy tự động theo lịch | Scheduler mỗi 30 phút |
| Duplicate detection | Skip file đã tải |
| Email labeling | Gán nhãn "Đã xử lý" |
| System tray icon | Chạy nền Windows |
| Windows startup | Auto-start khi boot |

---

## Phase 4: Analytics (v1.3)

| Tính năng | Mô tả |
|-----------|-------|
| History tab | Lịch sử file đã tải |
| Excel summary export | Tổng hợp danh sách file |
| Statistics dashboard | Số email/file theo thời gian |
| Filter by date range | Chỉ xử lý email từ-đến |

---

## Phase 5: Advanced (v2.0)

| Tính năng | Mô tả |
|-----------|-------|
| PDF data extraction | Trích xuất dữ liệu từ hóa đơn PDF |
| OCR cho file ảnh | Nhận dạng bảng kê dạng ảnh |
| Windows notification | Toast notification khi có file mới |
| Multi-account Gmail | Nhiều tài khoản Gmail |
| IMAP support | Hỗ trợ email ngoài Gmail |
| Plugin system | Mở rộng thêm handler cho loại email mới |

---

## Nguyên Tắc Phát Triển

```
"Start simple, add complexity ONLY when proven necessary."
                                    — Architecture Skill
```

1. **Ship MVP first** — tải được file = thành công
2. **User feedback** — thêm tính năng theo nhu cầu thực
3. **Backwards compatible** — config v1.0 phải chạy được trên v2.0
4. **Data-driven rules** — thêm loại email mới không cần code mới
