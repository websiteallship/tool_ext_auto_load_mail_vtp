"""
Email Auto-Download Tool — GUI Application

Main entry point. CustomTkinter GUI with Light Theme:
- Dashboard: Run Now, log output, status, progress bar
- Rules: Add/edit/delete email rules
- Settings: Gmail auth, output dir, schedule interval

Skills applied: 02_python-pro, 08_clean-code
"""

from __future__ import annotations

import json
import logging
import os
import platform
import subprocess
import threading
import tkinter as tk
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from queue import Empty, Queue
from tkinter import filedialog, messagebox

import customtkinter as ctk

from src.file_downloader import FileDownloader
from src.gmail_client import GmailClient
from src.link_extractor import LinkExtractor
from src.models import EmailRule, RunResult, SchedulerState
from src.rule_engine import RuleEngine
from src.scheduler import Scheduler

# ── Logging Setup ────────────────────────────────────────────────────

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

log_queue: Queue = Queue()
logger = logging.getLogger("email_auto_download")
logger.setLevel(logging.DEBUG)

file_handler = RotatingFileHandler(
    LOG_DIR / "app.log", maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(
    logging.Formatter("%(asctime)s [%(levelname)-8s] %(name)s: %(message)s")
)
logger.addHandler(file_handler)

# ── Settings ─────────────────────────────────────────────────────────

SETTINGS_FILE = Path("config/settings.json")
CONFIG_DIR = Path("config")
CONFIG_DIR.mkdir(exist_ok=True)


def load_settings() -> dict:
    if SETTINGS_FILE.exists():
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "output_dir": "downloads",
        "auto_schedule_enabled": False,
        "schedule_interval_minutes": 30,
        "skip_duplicates": True,
        "mark_processed_label": "AutoDownloaded",
        "log_level": "INFO",
    }


def save_settings(settings: dict) -> None:
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)


def open_folder(path: Path) -> None:
    """Open a folder in the system file explorer (cross-platform)."""
    path.mkdir(parents=True, exist_ok=True)
    system = platform.system()
    if system == "Windows":
        os.startfile(str(path))
    elif system == "Darwin":
        subprocess.Popen(["open", str(path)])
    else:
        subprocess.Popen(["xdg-open", str(path)])


# ── Color Palette (Light theme) ─────────────────────────────────────

class Colors:
    """Application color palette — light theme inspired by modern tools."""
    BG = "#F5F7FA"           # Main background
    CARD = "#FFFFFF"         # Cards / panels
    BORDER = "#E2E8F0"       # Subtle borders
    TEXT = "#1A202C"         # Primary text (very dark)
    TEXT_MUTED = "#4A5568"   # Secondary text (dark gray — readable)
    PRIMARY = "#3182CE"      # Primary blue
    PRIMARY_HOVER = "#2B6CB0"
    SUCCESS = "#38A169"      # Green
    SUCCESS_HOVER = "#2F855A"
    WARNING = "#DD6B20"      # Orange
    WARNING_HOVER = "#C05621"
    DANGER = "#E53E3E"       # Red
    DANGER_HOVER = "#C53030"
    ACCENT = "#4299E1"       # Light blue accent
    PROGRESS_BG = "#E2E8F0"  # Progress bar track
    PROGRESS_FG = "#3182CE"  # Progress bar fill
    LOG_BG = "#F7FAFC"       # Log area bg
    SIDEBAR = "#EDF2F7"      # Sidebar / tab bg
    FOOTER = "#718096"       # Footer text (medium gray)


# ── Application ──────────────────────────────────────────────────────

class App(ctk.CTk):
    """Main application window — Light Theme."""

    def __init__(self):
        super().__init__()

        self.title("Email Auto-Download Tool")
        self.geometry("960x680")
        self.minsize(860, 580)

        # Light theme
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.configure(fg_color=Colors.BG)

        # Core components
        self.settings = load_settings()
        self.gmail = GmailClient()
        self.rule_engine = RuleEngine(CONFIG_DIR / "rules.json")
        self.rule_engine.load_rules()
        self.scheduler: Scheduler | None = None
        self._is_running = False

        # Build UI
        self._create_tabs()
        self._build_dashboard_tab()
        self._build_rules_tab()
        self._build_settings_tab()
        self._build_help_tab()

        # Poll log queue
        self.after(200, self._poll_logs)

        # Auto-connect Gmail if token exists
        self.after(500, self._auto_connect_gmail)

        # Footer
        self._build_footer()

    # ── Tab Container ────────────────────────────────────────────────

    def _create_tabs(self) -> None:
        self.tabview = ctk.CTkTabview(
            self,
            anchor="nw",
            fg_color=Colors.CARD,
            segmented_button_fg_color=Colors.SIDEBAR,
            segmented_button_selected_color=Colors.PRIMARY,
            segmented_button_selected_hover_color=Colors.PRIMARY_HOVER,
            segmented_button_unselected_color=Colors.SIDEBAR,
            segmented_button_unselected_hover_color=Colors.BORDER,
            text_color=Colors.TEXT,
            border_color=Colors.BORDER,
            border_width=1,
        )
        self.tabview.pack(fill="both", expand=True, padx=16, pady=(12, 4))

        self.tab_dashboard = self.tabview.add("Dashboard")
        self.tab_rules = self.tabview.add("Rules")
        self.tab_settings = self.tabview.add("Settings")
        self.tab_help = self.tabview.add("Hướng Dẫn")

        # Style tabs
        for tab in (self.tab_dashboard, self.tab_rules, self.tab_settings, self.tab_help):
            tab.configure(fg_color=Colors.CARD)

    # ── Dashboard Tab ────────────────────────────────────────────────

    def _build_dashboard_tab(self) -> None:
        tab = self.tab_dashboard

        # ── Top bar: buttons + status ─────────────
        top_frame = ctk.CTkFrame(tab, fg_color="transparent")
        top_frame.pack(fill="x", padx=12, pady=(12, 8))

        self.btn_run = ctk.CTkButton(
            top_frame,
            text="▶  Run Now",
            command=self._on_run_now,
            width=130,
            height=34,
            fg_color=Colors.PRIMARY,
            hover_color=Colors.PRIMARY_HOVER,
            text_color="#FFFFFF",
            font=("", 13, "bold"),
            corner_radius=6,
        )
        self.btn_run.pack(side="left", padx=(0, 6))

        self.btn_stop = ctk.CTkButton(
            top_frame,
            text="⏹  Stop",
            command=self._on_stop,
            width=90,
            height=34,
            state="disabled",
            fg_color=Colors.CARD,
            hover_color=Colors.LOG_BG,
            border_width=1,
            border_color=Colors.BORDER,
            text_color=Colors.TEXT_MUTED,
            font=("", 13),
            corner_radius=6,
        )
        self.btn_stop.pack(side="left", padx=(0, 6))

        self.btn_reset = ctk.CTkButton(
            top_frame,
            text="↻  Reset",
            command=self._on_reset_history,
            width=90,
            height=34,
            fg_color=Colors.CARD,
            hover_color=Colors.LOG_BG,
            border_width=1,
            border_color=Colors.BORDER,
            text_color=Colors.TEXT,
            font=("", 13),
            corner_radius=6,
        )
        self.btn_reset.pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            top_frame,
            text="📂  Open Folder",
            command=self._on_open_folder,
            width=130,
            height=34,
            fg_color=Colors.CARD,
            hover_color=Colors.LOG_BG,
            border_width=1,
            border_color=Colors.BORDER,
            text_color=Colors.TEXT,
            font=("", 13),
            corner_radius=6,
        ).pack(side="left", padx=(0, 8))

        # Status indicator
        self.lbl_status = ctk.CTkLabel(
            top_frame,
            text="● Ready",
            text_color=Colors.TEXT_MUTED,
            font=("", 13),
        )
        self.lbl_status.pack(side="left", padx=16)

        # Last run
        self.lbl_last_run = ctk.CTkLabel(
            top_frame,
            text="",
            text_color=Colors.TEXT_MUTED,
            font=("", 11),
        )
        self.lbl_last_run.pack(side="right")

        # ── Progress bar ─────────────────────────
        progress_frame = ctk.CTkFrame(tab, fg_color="transparent")
        progress_frame.pack(fill="x", padx=12, pady=(0, 4))

        self.progress_bar = ctk.CTkProgressBar(
            progress_frame,
            height=6,
            corner_radius=3,
            fg_color=Colors.PROGRESS_BG,
            progress_color=Colors.PROGRESS_FG,
        )
        self.progress_bar.pack(fill="x")
        self.progress_bar.set(0)

        self.lbl_progress = ctk.CTkLabel(
            progress_frame,
            text="",
            text_color=Colors.TEXT_MUTED,
            font=("", 11),
        )
        self.lbl_progress.pack(anchor="e")

        # ── Log area (single, no nested tab) ────
        log_frame = ctk.CTkFrame(
            tab,
            fg_color=Colors.LOG_BG,
            corner_radius=8,
            border_color=Colors.BORDER,
            border_width=1,
        )
        log_frame.pack(fill="both", expand=True, padx=12, pady=(0, 6))

        self.log_text = ctk.CTkTextbox(
            log_frame,
            font=("Consolas", 12),
            state="disabled",
            fg_color=Colors.LOG_BG,
            text_color=Colors.TEXT,
            border_width=0,
        )
        self.log_text.pack(fill="both", expand=True, padx=4, pady=4)

        # ── Last-run stats bar ───────────────────
        stats_frame = ctk.CTkFrame(tab, fg_color="transparent")
        stats_frame.pack(fill="x", padx=12, pady=(0, 8))

        self.lbl_summary = ctk.CTkLabel(
            stats_frame,
            text="Ready — click Run Now to start.",
            font=("", 12),
            text_color=Colors.TEXT_MUTED,
        )
        self.lbl_summary.pack(side="left")



    # ── Rules Tab ────────────────────────────────────────────────────

    def _build_rules_tab(self) -> None:
        tab = self.tab_rules

        # Buttons
        btn_frame = ctk.CTkFrame(tab, fg_color="transparent")
        btn_frame.pack(fill="x", padx=12, pady=(12, 8))

        ctk.CTkButton(
            btn_frame,
            text="+ Add Rule",
            command=self._on_add_rule,
            width=120,
            height=36,
            fg_color=Colors.PRIMARY,
            hover_color=Colors.PRIMARY_HOVER,
            font=("", 13, "bold"),
            corner_radius=8,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_frame,
            text="↻ Refresh",
            command=self._refresh_rules_list,
            width=100,
            height=36,
            fg_color=Colors.SIDEBAR,
            hover_color=Colors.BORDER,
            text_color=Colors.TEXT,
            font=("", 13),
            corner_radius=8,
        ).pack(side="left")

        # Rules list
        self.rules_scroll = ctk.CTkScrollableFrame(
            tab,
            fg_color=Colors.LOG_BG,
            border_color=Colors.BORDER,
            border_width=1,
            corner_radius=8,
        )
        self.rules_scroll.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self._refresh_rules_list()

    def _refresh_rules_list(self) -> None:
        """Rebuild rules display."""
        for widget in self.rules_scroll.winfo_children():
            widget.destroy()

        if not self.rule_engine.rules:
            ctk.CTkLabel(
                self.rules_scroll,
                text="No rules configured. Click '+ Add Rule' to get started.",
                text_color=Colors.TEXT_MUTED,
                font=("", 13),
            ).pack(pady=40)
            return

        for rule in self.rule_engine.rules:
            self._create_rule_card(rule)

    def _create_rule_card(self, rule: EmailRule) -> None:
        """Create a card widget for a rule."""
        card = ctk.CTkFrame(
            self.rules_scroll,
            corner_radius=8,
            fg_color=Colors.CARD,
            border_color=Colors.BORDER,
            border_width=1,
        )
        card.pack(fill="x", pady=4, padx=4)

        # Header
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=12, pady=(10, 4))

        status_icon = "●" if rule.enabled else "○"
        status_color = Colors.SUCCESS if rule.enabled else Colors.TEXT_MUTED
        ctk.CTkLabel(
            header,
            text=f"{status_icon}  {rule.name}",
            font=("", 14, "bold"),
            text_color=status_color,
        ).pack(side="left")

        # Buttons (right → left: Delete, Edit, Toggle)
        ctk.CTkButton(
            header,
            text="Delete",
            width=65,
            height=28,
            fg_color=Colors.DANGER,
            hover_color=Colors.DANGER_HOVER,
            font=("", 11),
            corner_radius=6,
            command=lambda n=rule.name: self._on_delete_rule(n),
        ).pack(side="right", padx=2)

        ctk.CTkButton(
            header,
            text="Edit",
            width=60,
            height=28,
            fg_color=Colors.WARNING,
            hover_color=Colors.WARNING_HOVER,
            font=("", 11),
            corner_radius=6,
            command=lambda r=rule: self._on_edit_rule(r),
        ).pack(side="right", padx=2)

        toggle_text = "Disable" if rule.enabled else "Enable"
        toggle_color = Colors.SIDEBAR if rule.enabled else Colors.SUCCESS
        toggle_hover = Colors.BORDER if rule.enabled else Colors.SUCCESS_HOVER
        toggle_text_color = Colors.TEXT if rule.enabled else "#FFFFFF"
        ctk.CTkButton(
            header,
            text=toggle_text,
            width=70,
            height=28,
            fg_color=toggle_color,
            hover_color=toggle_hover,
            text_color=toggle_text_color,
            font=("", 11),
            corner_radius=6,
            command=lambda r=rule: self._on_toggle_rule(r),
        ).pack(side="right", padx=2)

        # Details
        details = ctk.CTkFrame(card, fg_color="transparent")
        details.pack(fill="x", padx=12, pady=(0, 10))

        info = (
            f"Subject: {rule.subject_query or '(any)'}    |    "
            f"From: {rule.sender_filter or '(any)'}"
        )
        ctk.CTkLabel(
            details,
            text=info,
            font=("", 11),
            text_color=Colors.TEXT_MUTED,
            justify="left",
        ).pack(anchor="w")

    # ── Settings Tab ─────────────────────────────────────────────────

    def _build_settings_tab(self) -> None:
        tab = self.tab_settings
        scroll = ctk.CTkScrollableFrame(
            tab,
            fg_color=Colors.CARD,
        )
        scroll.pack(fill="both", expand=True, padx=12, pady=12)

        # ── Gmail Authentication ──────────────────
        self._section_label(scroll, "Gmail Authentication")

        auth_card = ctk.CTkFrame(
            scroll,
            fg_color=Colors.LOG_BG,
            corner_radius=8,
            border_color=Colors.BORDER,
            border_width=1,
        )
        auth_card.pack(fill="x", pady=6)

        auth_inner = ctk.CTkFrame(auth_card, fg_color="transparent")
        auth_inner.pack(fill="x", padx=12, pady=10)

        self.lbl_auth_status = ctk.CTkLabel(
            auth_inner,
            text="● Not connected",
            text_color=Colors.DANGER,
            font=("", 13),
        )
        self.lbl_auth_status.pack(side="left")

        ctk.CTkButton(
            auth_inner,
            text="Disconnect",
            command=self._on_disconnect,
            width=100,
            height=32,
            fg_color=Colors.SIDEBAR,
            hover_color=Colors.BORDER,
            text_color=Colors.TEXT,
            font=("", 12),
            corner_radius=6,
        ).pack(side="right", padx=5)

        ctk.CTkButton(
            auth_inner,
            text="🔑  Authenticate Gmail",
            command=self._on_authenticate,
            width=180,
            height=32,
            fg_color=Colors.PRIMARY,
            hover_color=Colors.PRIMARY_HOVER,
            font=("", 12, "bold"),
            corner_radius=6,
        ).pack(side="right", padx=5)

        # ── Download Folder ──────────────────────
        self._section_label(scroll, "Download Folder")

        dir_card = ctk.CTkFrame(
            scroll,
            fg_color=Colors.LOG_BG,
            corner_radius=8,
            border_color=Colors.BORDER,
            border_width=1,
        )
        dir_card.pack(fill="x", pady=6)

        dir_inner = ctk.CTkFrame(dir_card, fg_color="transparent")
        dir_inner.pack(fill="x", padx=12, pady=10)

        self.entry_output_dir = ctk.CTkEntry(
            dir_inner,
            width=500,
            fg_color=Colors.CARD,
            border_color=Colors.BORDER,
            text_color=Colors.TEXT,
        )
        self.entry_output_dir.insert(0, self.settings.get("output_dir", "downloads"))
        self.entry_output_dir.pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            dir_inner,
            text="Browse...",
            command=self._on_browse_dir,
            width=100,
            height=32,
            fg_color=Colors.SIDEBAR,
            hover_color=Colors.BORDER,
            text_color=Colors.TEXT,
            font=("", 12),
            corner_radius=6,
        ).pack(side="left")

        # ── Auto Schedule ────────────────────────
        self._section_label(scroll, "Auto Schedule")

        sched_card = ctk.CTkFrame(
            scroll,
            fg_color=Colors.LOG_BG,
            corner_radius=8,
            border_color=Colors.BORDER,
            border_width=1,
        )
        sched_card.pack(fill="x", pady=6)

        sched_inner = ctk.CTkFrame(sched_card, fg_color="transparent")
        sched_inner.pack(fill="x", padx=12, pady=10)

        self.chk_auto = ctk.CTkCheckBox(
            sched_inner,
            text="Enable automatic checking",
            text_color=Colors.TEXT,
            fg_color=Colors.PRIMARY,
            hover_color=Colors.PRIMARY_HOVER,
        )
        if self.settings.get("auto_schedule_enabled"):
            self.chk_auto.select()
        self.chk_auto.pack(side="left", padx=(0, 20))

        ctk.CTkLabel(
            sched_inner,
            text="Interval (min):",
            text_color=Colors.TEXT,
        ).pack(side="left")

        self.entry_interval = ctk.CTkEntry(
            sched_inner,
            width=60,
            fg_color=Colors.CARD,
            border_color=Colors.BORDER,
            text_color=Colors.TEXT,
        )
        self.entry_interval.insert(
            0, str(self.settings.get("schedule_interval_minutes", 30))
        )
        self.entry_interval.pack(side="left", padx=5)

        # ── Options ──────────────────────────────
        self._section_label(scroll, "Options")

        opt_card = ctk.CTkFrame(
            scroll,
            fg_color=Colors.LOG_BG,
            corner_radius=8,
            border_color=Colors.BORDER,
            border_width=1,
        )
        opt_card.pack(fill="x", pady=6)

        opt_inner = ctk.CTkFrame(opt_card, fg_color="transparent")
        opt_inner.pack(fill="x", padx=12, pady=10)

        self.chk_skip_dup = ctk.CTkCheckBox(
            opt_inner,
            text="Skip already downloaded files",
            text_color=Colors.TEXT,
            fg_color=Colors.PRIMARY,
            hover_color=Colors.PRIMARY_HOVER,
        )
        if self.settings.get("skip_duplicates", True):
            self.chk_skip_dup.select()
        self.chk_skip_dup.pack(anchor="w")

        # ── Save ─────────────────────────────────
        ctk.CTkButton(
            scroll,
            text="Save Settings",
            command=self._on_save_settings,
            width=160,
            height=38,
            fg_color=Colors.SUCCESS,
            hover_color=Colors.SUCCESS_HOVER,
            font=("", 14, "bold"),
            corner_radius=8,
        ).pack(pady=16)

    def _section_label(self, parent, text: str) -> None:
        """Create a section header with divider."""
        ctk.CTkLabel(
            parent,
            text=text,
            font=("", 14, "bold"),
            text_color=Colors.TEXT,
        ).pack(anchor="w", pady=(18, 3))
        ctk.CTkFrame(
            parent,
            height=1,
            fg_color=Colors.BORDER,
        ).pack(fill="x", pady=(0, 4))

    # ── Help Tab ─────────────────────────────────────────────────────

    def _build_help_tab(self) -> None:
        """Build the Vietnamese user guide tab."""
        tab = self.tab_help
        scroll = ctk.CTkScrollableFrame(tab, fg_color=Colors.CARD)
        scroll.pack(fill="both", expand=True, padx=12, pady=12)

        # Title card
        title_frame = ctk.CTkFrame(
            scroll, fg_color="#EBF8FF", corner_radius=10,
            border_color="#BEE3F8", border_width=1,
        )
        title_frame.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            title_frame, text="📖  Hướng Dẫn Sử Dụng",
            font=("", 20, "bold"), text_color=Colors.PRIMARY,
        ).pack(anchor="w", padx=16, pady=(14, 2))

        ctk.CTkLabel(
            title_frame,
            text="Công cụ tự động tải hóa đơn & bảng kê điện tử từ Gmail",
            font=("", 12), text_color=Colors.TEXT_MUTED,
        ).pack(anchor="w", padx=16, pady=(0, 14))

        # Step 1
        self._help_section(scroll, "Bước 1 — Kết nối Gmail", [
            ("⚙️", "Vào tab Settings",
             "Mở tab Settings ở trên cùng."),
            ("🔗", "Nhấn nút 'Authenticate Gmail'",
             "Ứng dụng sẽ mở trình duyệt để đăng nhập Google.\n"
             "Cho phép (Allow) quyền truy cập Gmail → ứng dụng tự lưu token.\n"
             "Lần sau sẽ tự động kết nối mà không cần đăng nhập lại."),
        ])

        # Step 2
        self._help_section(scroll, "Bước 2 — Thiết lập Rules (Quy tắc)", [
            ("📋", "Vào tab Rules",
             "Mỗi Rule là một bộ điều kiện để lọc email cần tải."),
            ("➕", "Nhấn '+ Add Rule'",
             "Điền thông tin:\n"
             "  • Tên quy tắc: Đặt tên dễ nhận biết (vd: Hóa đơn Viettel Post).\n"
             "  • Subject Query: Từ khóa tìm trong tiêu đề email.\n"
             "  • Sender Filter: Email người gửi (bỏ trống = tất cả).\n"
             "  • Output Folder: Thư mục lưu file tải về.\n"
             "  • Tích chọn tải Attachment hoặc Bảng kê tùy nhu cầu."),
            ("✏️", "Chỉnh sửa / Xóa Rule",
             "Nhấn Edit để thay đổi, Delete để xóa.\n"
             "Bật/tắt Rule bằng nút Enable / Disable."),
        ])

        # Step 3
        self._help_section(scroll, "Bước 3 — Cài đặt thư mục & lịch tự động", [
            ("📁", "Thư mục tải về",
             "Vào Settings → mục Download Folder.\n"
             "Nhấn Browse... để chọn thư mục mặc định lưu file."),
            ("⏰", "Lịch tự động (Auto Schedule)",
             "Bật Enable automatic checking để ứng dụng tự chạy định kỳ.\n"
             "Đặt Interval (phút) — ví dụ 30 = kiểm tra email mỗi 30 phút."),
            ("💾", "Lưu cài đặt",
             "Nhấn Save Settings sau khi thay đổi."),
        ])

        # Step 4
        self._help_section(scroll, "Bước 4 — Chạy và theo dõi", [
            ("▶", "Chạy thủ công (Run Now)",
             "Nhấn nút Run Now ở tab Dashboard.\n"
             "Ứng dụng sẽ duyệt Gmail theo từng Rule và tải file về thư mục đã chọn."),
            ("📊", "Theo dõi tiến trình",
             "Thanh progress bar hiển thị tiến độ.\n"
             "Log hiển thị chi tiết từng bước xử lý."),
            ("📂", "Mở thư mục",
             "Nhấn Open Folder để mở thư mục tải về trong File Explorer."),
            ("⏹", "Dừng",
             "Nhấn Stop bất cứ lúc nào để dừng quá trình."),
        ])

        # Step 5
        self._help_section(scroll, "Bước 5 — Lịch sử & Reset", [
            ("🗂️", "Tab History",
             "Trong Dashboard → tab History:\n"
             "Xem thống kê số file đã tải, bỏ qua, lỗi của từng lần chạy."),
            ("↻", "Reset lịch sử",
             "Nhấn Reset để xóa danh sách email đã xử lý.\n"
             "⚠  Lần chạy tiếp theo sẽ tải lại TẤT CẢ email phù hợp."),
        ])

        # Important notes
        note_frame = ctk.CTkFrame(
            scroll, fg_color="#FFFDE7", corner_radius=8,
            border_color="#FFE082", border_width=1,
        )
        note_frame.pack(fill="x", pady=(12, 6))

        ctk.CTkLabel(
            note_frame, text="⚠  Lưu ý quan trọng",
            font=("", 13, "bold"), text_color="#B7791F",
        ).pack(anchor="w", padx=14, pady=(10, 4))

        ctk.CTkLabel(
            note_frame,
            text=(
                "• Không chia sẻ file credentials.json cho người khác.\n"
                "• Token đăng nhập được lưu an toàn trong hệ thống (keyring).\n"
                "• Ứng dụng chỉ tải file từ các domain đáng tin cậy (vinvoice.viettel.vn, ...).\n"
                "• File trùng tên sẽ bỏ qua nếu tuỳ chọn 'Skip duplicates' được bật.\n"
                "• Nhật ký đầy đủ được lưu tại: logs/app.log"
            ),
            font=("", 12), text_color="#744210", justify="left",
        ).pack(anchor="w", padx=14, pady=(0, 12))

        # Support
        ctk.CTkLabel(
            scroll,
            text="📧  Hỗ trợ kỹ thuật: allship.vn",
            font=("", 11), text_color=Colors.FOOTER,
        ).pack(anchor="center", pady=(12, 4))

    def _help_section(
        self, parent, title: str, items: list[tuple[str, str, str]]
    ) -> None:
        """Render a Help section with icon cards."""
        ctk.CTkLabel(
            parent, text=title,
            font=("", 14, "bold"), text_color=Colors.TEXT,
        ).pack(anchor="w", pady=(14, 3))
        ctk.CTkFrame(parent, height=1, fg_color=Colors.BORDER).pack(
            fill="x", pady=(0, 6)
        )

        for icon, heading, body in items:
            card = ctk.CTkFrame(
                parent, fg_color=Colors.LOG_BG, corner_radius=8,
                border_color=Colors.BORDER, border_width=1,
            )
            card.pack(fill="x", pady=3)

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="x", padx=12, pady=8)

            head_row = ctk.CTkFrame(inner, fg_color="transparent")
            head_row.pack(fill="x")

            ctk.CTkLabel(
                head_row, text=icon, font=("", 16),
                width=28, text_color=Colors.PRIMARY,
            ).pack(side="left", padx=(0, 6))

            ctk.CTkLabel(
                head_row, text=heading,
                font=("", 13, "bold"), text_color=Colors.TEXT,
            ).pack(side="left", anchor="w")

            if body:
                ctk.CTkLabel(
                    inner, text=body, font=("", 12),
                    text_color=Colors.TEXT_MUTED, justify="left",
                    wraplength=750,
                ).pack(anchor="w", padx=(34, 0), pady=(2, 0))

    # ── Footer ───────────────────────────────────────────────────────

    def _build_footer(self) -> None:
        footer = ctk.CTkLabel(
            self,
            text="Copyright by allship.vn",
            font=("", 11),
            text_color=Colors.FOOTER,
        )
        footer.pack(pady=(0, 8))

    # ── Authentication ───────────────────────────────────────────────

    def _on_authenticate(self) -> None:
        """Authenticate Gmail in background thread."""
        self.lbl_auth_status.configure(
            text="● Authenticating...", text_color=Colors.WARNING
        )

        def _auth_worker():
            try:
                self.gmail.authenticate()
                self.after(
                    0,
                    lambda: self.lbl_auth_status.configure(
                        text=f"● Connected ({self.gmail.user_email})",
                        text_color=Colors.SUCCESS,
                    ),
                )
                self._queue_log("info", f"Gmail authenticated: {self.gmail.user_email}")
            except Exception as e:
                self.after(
                    0,
                    lambda: self.lbl_auth_status.configure(
                        text=f"● Failed: {e}",
                        text_color=Colors.DANGER,
                    ),
                )
                self._queue_log("error", f"Authentication failed: {e}")

        threading.Thread(target=_auth_worker, daemon=True).start()

    def _auto_connect_gmail(self) -> None:
        """Auto-connect Gmail on startup if token exists in keyring."""

        def _worker():
            try:
                self.gmail.authenticate()
                self.after(
                    0,
                    lambda: self.lbl_auth_status.configure(
                        text=f"● Connected ({self.gmail.user_email})",
                        text_color=Colors.SUCCESS,
                    ),
                )
                self._queue_log("info", f"Gmail auto-connected: {self.gmail.user_email}")
            except Exception:
                pass  # No valid token — user needs to authenticate manually

        threading.Thread(target=_worker, daemon=True).start()

    def _on_disconnect(self) -> None:
        self.gmail.disconnect()
        self.lbl_auth_status.configure(
            text="● Not connected", text_color=Colors.DANGER
        )
        self._queue_log("info", "Gmail disconnected")

    # ── Run / Stop ───────────────────────────────────────────────────

    def _on_run_now(self) -> None:
        """Run email processing once in a background thread."""
        if self._is_running:
            return

        if not self.gmail.is_authenticated:
            messagebox.showwarning(
                "Not Connected",
                "Please authenticate Gmail first in the Settings tab.",
            )
            return

        self._is_running = True
        self.btn_run.configure(state="disabled", fg_color=Colors.SIDEBAR, text_color=Colors.TEXT_MUTED)
        self.btn_stop.configure(
            state="normal",
            border_color=Colors.DANGER,
            text_color=Colors.DANGER,
        )
        self._set_status("● Running...", Colors.PRIMARY)
        self.progress_bar.set(0)
        self.lbl_progress.configure(text="Starting...")

        # Create scheduler
        output_dir = Path(self.settings.get("output_dir", "downloads"))
        self.scheduler = Scheduler(
            gmail_client=self.gmail,
            rule_engine=self.rule_engine,
            output_dir=output_dir,
            interval_minutes=self.settings.get("schedule_interval_minutes", 30),
            on_log=self._queue_log,
            on_state_change=self._on_scheduler_state,
            on_progress=self._on_scheduler_progress,
        )

        def _run_worker():
            try:
                result = self.scheduler.run_once()
            except Exception as e:
                self._queue_log("error", f"Run failed: {e}")
            finally:
                self.after(0, self._on_run_finished)

        threading.Thread(target=_run_worker, daemon=True).start()

    def _on_stop(self) -> None:
        """Stop the currently running process."""
        if self.scheduler:
            self.scheduler.stop()
        self._is_running = False
        self.btn_run.configure(state="normal", fg_color=Colors.PRIMARY, text_color="#FFFFFF")
        self.btn_stop.configure(
            state="disabled",
            border_color=Colors.BORDER,
            text_color=Colors.TEXT_MUTED,
        )
        self._set_status("● Stopped", Colors.WARNING)
        self.lbl_progress.configure(text="Stopped by user")
        self._queue_log("info", "Processing stopped by user")

    def _on_run_finished(self) -> None:
        """Called on main thread when run completes."""
        self._is_running = False
        self.btn_run.configure(state="normal", fg_color=Colors.PRIMARY, text_color="#FFFFFF")
        self.btn_stop.configure(
            state="disabled",
            border_color=Colors.BORDER,
            text_color=Colors.TEXT_MUTED,
        )
        self.progress_bar.set(1)

        last = self.scheduler.last_result if self.scheduler else None
        if last:
            self._set_status("● Completed", Colors.SUCCESS)
            self.lbl_summary.configure(text=last.summary())
            self.lbl_last_run.configure(
                text=f"Last run: {last.finished_at.strftime('%H:%M:%S')}"
            )
            self.lbl_progress.configure(
                text=f"Done — {last.attachments_downloaded + last.bang_ke_downloaded} files"
            )
            # Show completion dialog
            output_dir = Path(self.settings.get("output_dir", "downloads"))
            CompletionDialog(self, last, output_dir)
        else:
            self._set_status("● Ready", Colors.TEXT_MUTED)

    def _on_scheduler_state(self, state: SchedulerState) -> None:
        """Handle scheduler state changes (from background thread)."""
        state_map = {
            SchedulerState.RUNNING: ("● Running...", Colors.PRIMARY),
            SchedulerState.WAITING: ("● Waiting...", Colors.ACCENT),
            SchedulerState.STOPPED: ("● Stopped", Colors.WARNING),
            SchedulerState.ERROR: ("● Error", Colors.DANGER),
            SchedulerState.IDLE: ("● Ready", Colors.TEXT_MUTED),
        }
        text, color = state_map.get(state, ("● Unknown", Colors.TEXT_MUTED))
        self.after(0, lambda: self._set_status(text, color))

    def _on_scheduler_progress(self, message: str) -> None:
        """Handle scheduler progress updates (from background thread)."""
        self.after(0, lambda: self.lbl_progress.configure(text=message))

    # ── Rule Actions ─────────────────────────────────────────────────

    def _on_add_rule(self) -> None:
        """Open dialog to add a new rule."""
        dialog = RuleDialog(self, "Add Rule")
        self.wait_window(dialog)
        if dialog.result:
            try:
                self.rule_engine.add_rule(dialog.result)
                self._refresh_rules_list()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def _on_delete_rule(self, name: str) -> None:
        if messagebox.askyesno("Confirm", f"Delete rule '{name}'?"):
            self.rule_engine.remove_rule(name)
            self._refresh_rules_list()

    def _on_toggle_rule(self, rule: EmailRule) -> None:
        rule.enabled = not rule.enabled
        self.rule_engine.save_rules()
        self._refresh_rules_list()

    def _on_edit_rule(self, rule: EmailRule) -> None:
        """Open dialog to edit an existing rule."""
        dialog = RuleDialog(self, f"Edit Rule — {rule.name}", rule=rule)
        self.wait_window(dialog)
        if dialog.result:
            old_name = rule.name
            try:
                self.rule_engine.remove_rule(old_name)
                self.rule_engine.add_rule(dialog.result)
                self._refresh_rules_list()
            except Exception as e:
                try:
                    self.rule_engine.add_rule(rule)
                except Exception:
                    pass
                messagebox.showerror("Error", str(e))

    # ── Settings Actions ─────────────────────────────────────────────

    def _on_browse_dir(self) -> None:
        path = filedialog.askdirectory()
        if path:
            self.entry_output_dir.delete(0, "end")
            self.entry_output_dir.insert(0, path)

    def _on_save_settings(self) -> None:
        self.settings["output_dir"] = self.entry_output_dir.get()
        self.settings["auto_schedule_enabled"] = bool(self.chk_auto.get())
        self.settings["skip_duplicates"] = bool(self.chk_skip_dup.get())
        try:
            self.settings["schedule_interval_minutes"] = int(
                self.entry_interval.get()
            )
        except ValueError:
            self.settings["schedule_interval_minutes"] = 30

        save_settings(self.settings)
        messagebox.showinfo("Saved", "Settings saved successfully.")

    def _on_reset_history(self) -> None:
        """Reset processed email history and clear log display."""
        if self.scheduler:
            self.scheduler.clear_history()
        else:
            pef = Path("config/processed_emails.json")
            if pef.exists():
                pef.unlink()

        # Clear log display
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

        self._queue_log("info", "History cleared — next run will process all emails")
        self.progress_bar.set(0)
        self.lbl_progress.configure(text="")
        self.lbl_summary.configure(text="Ready — click Run Now to start.")


    def _on_open_folder(self) -> None:
        output_dir = Path(self.settings.get("output_dir", "downloads"))
        open_folder(output_dir)

    # ── Helpers ──────────────────────────────────────────────────────

    def _set_status(self, text: str, color: str) -> None:
        self.lbl_status.configure(text=text, text_color=color)

    def _queue_log(self, level: str, message: str) -> None:
        """Thread-safe log to GUI."""
        log_queue.put((level, message))

    def _poll_logs(self) -> None:
        """Poll log queue and display messages (called from main thread)."""
        try:
            while True:
                level, message = log_queue.get_nowait()
                timestamp = datetime.now().strftime("%H:%M:%S")

                self.log_text.configure(state="normal")
                self.log_text.insert("end", f"[{timestamp}] {message}\n")
                self.log_text.see("end")
                self.log_text.configure(state="disabled")
        except Empty:
            pass
        finally:
            self.after(200, self._poll_logs)


# ── Completion Dialog ────────────────────────────────────────────────

class CompletionDialog(ctk.CTkToplevel):
    """Modern dialog shown after a scan/download run completes."""

    def __init__(self, parent, result, output_dir: Path):
        super().__init__(parent)
        self.title("Hoàn tất")
        self.resizable(False, False)
        self.configure(fg_color=Colors.BG)
        self.transient(parent)
        self.grab_set()
        self._output_dir = output_dir

        total_files = result.attachments_downloaded + result.bang_ke_downloaded
        has_errors = len(result.errors) > 0
        has_file_log = len(result.downloaded_files) > 0 or len(result.skipped_files) > 0

        # Dynamic height based on content
        base_h = 310
        if has_file_log:
            base_h += 160
        if has_errors:
            base_h += 24
        self.geometry(f"440x{base_h}")

        # ── Header card ────────────────────────────
        if total_files > 0 and not has_errors:
            header_bg, header_border = "#EBF8FF", "#BEE3F8"
            icon, title_text = "✅", "Quét & tải hoàn tất!"
            title_color = Colors.SUCCESS
        elif has_errors:
            header_bg, header_border = "#FFFDE7", "#FFE082"
            icon, title_text = "⚠️", "Hoàn tất (có lỗi)"
            title_color = Colors.WARNING
        else:
            header_bg, header_border = "#F7FAFC", Colors.BORDER
            icon, title_text = "📭", "Không có file mới"
            title_color = Colors.TEXT_MUTED

        header = ctk.CTkFrame(
            self, fg_color=header_bg, corner_radius=12,
            border_color=header_border, border_width=1,
        )
        header.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(
            header, text=f"{icon}  {title_text}",
            font=("", 18, "bold"), text_color=title_color,
        ).pack(anchor="w", padx=16, pady=(14, 4))

        ctk.CTkLabel(
            header,
            text=f"Thời gian: {result.duration_seconds:.1f}s",
            font=("", 12), text_color=Colors.TEXT_MUTED,
        ).pack(anchor="w", padx=16, pady=(0, 12))

        # ── Stats card ─────────────────────────────
        stats_card = ctk.CTkFrame(
            self, fg_color=Colors.CARD, corner_radius=10,
            border_color=Colors.BORDER, border_width=1,
        )
        stats_card.pack(fill="x", padx=20, pady=6)

        stats = [
            ("📧", "Email tìm thấy", str(result.emails_found)),
            ("📥", "File đã tải", str(total_files)),
            ("⏭", "Bỏ qua (trùng)", str(result.skipped_duplicates)),
        ]
        if has_errors:
            stats.append(("❌", "Lỗi", str(len(result.errors))))

        for icon_s, label, value in stats:
            row = ctk.CTkFrame(stats_card, fg_color="transparent")
            row.pack(fill="x", padx=14, pady=3)

            ctk.CTkLabel(
                row, text=f"{icon_s}  {label}",
                font=("", 13), text_color=Colors.TEXT,
            ).pack(side="left")

            value_color = Colors.SUCCESS if label == "File đã tải" and int(value) > 0 else Colors.TEXT
            if label == "Lỗi":
                value_color = Colors.DANGER
            ctk.CTkLabel(
                row, text=value,
                font=("", 14, "bold"), text_color=value_color,
            ).pack(side="right")

        ctk.CTkFrame(stats_card, height=4, fg_color="transparent").pack()

        # ── File log ───────────────────────────────
        if has_file_log:
            log_card = ctk.CTkFrame(
                self, fg_color=Colors.CARD, corner_radius=10,
                border_color=Colors.BORDER, border_width=1,
            )
            log_card.pack(fill="x", padx=20, pady=6)

            ctk.CTkLabel(
                log_card, text="📋  Chi tiết file",
                font=("", 13, "bold"), text_color=Colors.TEXT,
            ).pack(anchor="w", padx=14, pady=(8, 4))

            log_scroll = ctk.CTkScrollableFrame(
                log_card, fg_color=Colors.LOG_BG,
                corner_radius=6, height=110,
            )
            log_scroll.pack(fill="x", padx=10, pady=(0, 8))

            # Downloaded files
            for fname in result.downloaded_files:
                ctk.CTkLabel(
                    log_scroll,
                    text=f"  ✅  {fname}",
                    font=("Consolas", 11),
                    text_color=Colors.SUCCESS,
                    justify="left",
                ).pack(anchor="w", pady=1)

            # Skipped files
            for fname in result.skipped_files:
                ctk.CTkLabel(
                    log_scroll,
                    text=f"  ⏭  {fname}",
                    font=("Consolas", 11),
                    text_color=Colors.TEXT_MUTED,
                    justify="left",
                ).pack(anchor="w", pady=1)

        # ── Buttons ────────────────────────────────
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(10, 16))

        if total_files > 0:
            ctk.CTkButton(
                btn_frame,
                text="📂  Xem thư mục đã lưu",
                command=self._open_folder,
                width=200,
                height=40,
                fg_color=Colors.PRIMARY,
                hover_color=Colors.PRIMARY_HOVER,
                font=("", 14, "bold"),
                corner_radius=8,
            ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_frame,
            text="Đóng",
            command=self.destroy,
            width=100,
            height=40,
            fg_color=Colors.SIDEBAR,
            hover_color=Colors.BORDER,
            text_color=Colors.TEXT,
            font=("", 13),
            corner_radius=8,
        ).pack(side="right")

        # Center on parent
        self.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_x()
        py = parent.winfo_y()
        w = self.winfo_width()
        h = self.winfo_height()
        self.geometry(f"+{px + (pw - w) // 2}+{py + (ph - h) // 2}")

    def _open_folder(self) -> None:
        open_folder(self._output_dir)
        self.destroy()


# ── Rule Dialog ──────────────────────────────────────────────────────

class RuleDialog(ctk.CTkToplevel):
    """Dialog for adding/editing a rule — Light Theme."""

    def __init__(self, parent, title: str, rule: EmailRule | None = None):
        super().__init__(parent)
        self.title(title)
        self.geometry("520x520")
        self.configure(fg_color=Colors.CARD)
        self.result: EmailRule | None = None
        self.transient(parent)
        self.grab_set()

        pad = {"padx": 16, "pady": 5}

        ctk.CTkLabel(
            self, text="Rule Name:", text_color=Colors.TEXT, font=("", 12, "bold")
        ).pack(anchor="w", **pad)
        self.entry_name = ctk.CTkEntry(
            self,
            width=460,
            fg_color=Colors.LOG_BG,
            border_color=Colors.BORDER,
            text_color=Colors.TEXT,
        )
        self.entry_name.pack(**pad)

        ctk.CTkLabel(
            self, text="Subject Query:", text_color=Colors.TEXT, font=("", 12, "bold")
        ).pack(anchor="w", **pad)
        self.entry_subject = ctk.CTkEntry(
            self,
            width=460,
            fg_color=Colors.LOG_BG,
            border_color=Colors.BORDER,
            text_color=Colors.TEXT,
        )
        self.entry_subject.pack(**pad)

        ctk.CTkLabel(
            self, text="Sender Filter:", text_color=Colors.TEXT, font=("", 12, "bold")
        ).pack(anchor="w", **pad)
        self.entry_sender = ctk.CTkEntry(
            self,
            width=460,
            fg_color=Colors.LOG_BG,
            border_color=Colors.BORDER,
            text_color=Colors.TEXT,
        )
        self.entry_sender.pack(**pad)

        self.chk_attachments = ctk.CTkCheckBox(
            self,
            text="Download attachments",
            text_color=Colors.TEXT,
            fg_color=Colors.PRIMARY,
            hover_color=Colors.PRIMARY_HOVER,
        )
        self.chk_attachments.select()
        self.chk_attachments.pack(anchor="w", **pad)

        self.chk_bang_ke = ctk.CTkCheckBox(
            self,
            text="Download invoice details link",
            text_color=Colors.TEXT,
            fg_color=Colors.PRIMARY,
            hover_color=Colors.PRIMARY_HOVER,
        )
        self.chk_bang_ke.select()
        self.chk_bang_ke.pack(anchor="w", **pad)

        # Pre-fill if editing
        if rule:
            self.entry_name.insert(0, rule.name)
            self.entry_subject.insert(0, rule.subject_query)
            self.entry_sender.insert(0, rule.sender_filter)

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=16, pady=16)

        ctk.CTkButton(
            btn_frame,
            text="Save",
            command=self._on_save,
            width=110,
            height=36,
            fg_color=Colors.SUCCESS,
            hover_color=Colors.SUCCESS_HOVER,
            font=("", 13, "bold"),
            corner_radius=8,
        ).pack(side="right", padx=5)

        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=self.destroy,
            width=90,
            height=36,
            fg_color=Colors.SIDEBAR,
            hover_color=Colors.BORDER,
            text_color=Colors.TEXT,
            font=("", 13),
            corner_radius=8,
        ).pack(side="right")

    def _on_save(self) -> None:
        name = self.entry_name.get().strip()
        if not name:
            messagebox.showwarning("Required", "Rule name is required.")
            return

        self.result = EmailRule(
            name=name,
            enabled=True,
            subject_query=self.entry_subject.get().strip(),
            sender_filter=self.entry_sender.get().strip(),
            output_folder="",
            download_attachments=bool(self.chk_attachments.get()),
            download_bang_ke=bool(self.chk_bang_ke.get()),
        )
        self.destroy()


# ── Entry Point ──────────────────────────────────────────────────────

def main() -> None:
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
