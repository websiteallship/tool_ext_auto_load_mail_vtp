# FEATURE: GUI Application (v2.1)

> Skills áp dụng: `02_python-pro`, `08_clean-code`

## Mục Đích

Giao diện desktop CustomTkinter — toggle rule, chạy từng rule, preview trước khi tải, lịch sử download, system tray, và đếm ngược.

---

## Dashboard Tab (v2.1)

```
┌──────────────────────────────────────────────────────────┐
│  📊 Dashboard                              v2.1          │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  [▶ Run] [⏹ Stop] [↻ Reset] [📂 Open ▼]               │
│  [📋 Lịch sử]                   ● Ready   Last: 14:30  │
│                                                          │
│  Chạy rule: [▶ Tất cả rule đang bật  ▼] [👁️ Preview]   │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │ 📊 Hôm nay: 12   Tuần: 45   Tổng: 230            │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░  70%                         │
│  ⏱ Chạy tiếp sau: 24:35                                 │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │ Log Output                                         │  │
│  │ [14:30:01] Bắt đầu chạy: J&T Express COD          │  │
│  │ [14:30:02] Found 2 emails...                       │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  ✅ 1 rules, 2 emails, 2 files (2.7s)                    │
└──────────────────────────────────────────────────────────┘
```

### Tính năng mới v2.1:
- 👁️ **Preview button** — quét email, hiện danh sách (không tải)
- 📋 **Lịch sử button** — mở dialog lịch sử download
- 📊 **Stats card** — thống kê hôm nay / tuần / tổng
- ⏱️ **Countdown** — đếm ngược tới lần chạy tiếp (auto-schedule)

---

## PreviewDialog (NEW v2.1)

```
┌──────────────────────────────────────────────┐
│  👁️  Preview — Danh sách email & file        │
│  Thời gian quét: 1.2s                        │
│                                              │
│  📦 Viettel Post Invoice (3 emails)          │
│  ├─ Email: "HĐ tháng 3/2026"  (16/03)       │
│  │  └─ 📎 K26TAN2038744.pdf                 │
│  │  └─ 📎 K26TAN2038744.xml                 │
│  ├─ Email: "HĐ tháng 3/2026"  (19/03)       │
│  │  └─ 🔗 Bảng kê chi tiết (link)           │
│  └─ ...                                      │
│                                              │
│  📊 J&T Express COD (2 emails)               │
│  ├─ Email: "Đối soát COD"  (16/03)           │
│  │  └─ 📎 251LC17070_COD.xlsx                │
│  └─ ...                                      │
│                                              │
│  Tổng: 5 emails, 8 files dự kiến             │
│                                              │
│  [▶ Tải ngay]              [Đóng]            │
└──────────────────────────────────────────────┘
```

---

## HistoryDialog (NEW v2.1)

```
┌──────────────────────────────────────────────┐
│  📋  Lịch sử tải file                        │
│                                              │
│  Lọc: [Tất cả rules  ▼]                     │
│                                              │
│  ┌─────────────────────────────────────────┐ │
│  │ Ngày      │ File          │ Rule │ Status│ │
│  ├───────────┼───────────────┼──────┼───────┤ │
│  │ 23/03 18h │ COD_0316.xlsx │ J&T  │  ✅   │ │
│  │ 23/03 18h │ COD_0319.xlsx │ J&T  │  ✅   │ │
│  │ 23/03 17h │ K26TAN...pdf  │ VTP  │  ⏭   │ │
│  └─────────────────────────────────────────┘ │
│                                              │
│  Tổng: 230 files  │  [Xóa lịch sử] [Đóng]   │
└──────────────────────────────────────────────┘
```

---

## System Tray (NEW v2.1)

```
Tray Menu:
┌─────────────────────┐
│ 📧 Email Auto-Download │
│ ─────────────────── │
│ 📂 Mở ứng dụng     │
│ ▶  Chạy ngay        │
│ ⏹  Dừng             │
│ ─────────────────── │
│ ❌ Thoát            │
└─────────────────────┘

Toast: "✅ Email Auto-Download — 5 files đã tải về"
```

---

## Settings Tab (v2.1 additions)

```
│  System                                     │
│  ☑ Minimize to system tray                  │
│  ☑ Khởi động cùng Windows                   │
```

---

## Threading Model (unchanged)

- GUI → main thread
- Processing → daemon thread
- Giao tiếp qua Queue (thread-safe)
- Tray icon → thread riêng (pystray)
- Countdown timer → `after(1000)` loop
