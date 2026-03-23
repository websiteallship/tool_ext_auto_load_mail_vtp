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

        self.title("Email Auto-Download Tool v2.0.0")
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

        # Refresh Dashboard dropdowns whenever user switches tabs
        self.tabview.configure(command=self._on_tab_changed)

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

        self.folder_menu = ctk.CTkOptionMenu(
            top_frame,
            width=160,
            height=34,
            fg_color=Colors.CARD,
            button_color=Colors.SIDEBAR,
            button_hover_color=Colors.BORDER,
            text_color=Colors.TEXT,
            dropdown_fg_color=Colors.CARD,
            dropdown_text_color=Colors.TEXT,
            dropdown_hover_color=Colors.SIDEBAR,
            font=("", 12),
            corner_radius=6,
            values=["📂 Open Folder"],
            command=self._on_open_folder,
        )
        self.folder_menu.set("📂 Open Folder")
        self.folder_menu.pack(side="left", padx=(0, 8))
        self._update_folder_menu()

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

        # ── Rule selector row ─────────────────────
        selector_frame = ctk.CTkFrame(tab, fg_color="transparent")
        selector_frame.pack(fill="x", padx=12, pady=(0, 6))

        ctk.CTkLabel(
            selector_frame,
            text="Chạy rule:",
            font=("", 12, "bold"),
            text_color=Colors.TEXT,
        ).pack(side="left", padx=(0, 8))

        self.rule_selector = ctk.CTkOptionMenu(
            selector_frame,
            width=350,
            height=32,
            fg_color=Colors.LOG_BG,
            button_color=Colors.SIDEBAR,
            button_hover_color=Colors.BORDER,
            text_color=Colors.TEXT,
            dropdown_fg_color=Colors.CARD,
            dropdown_text_color=Colors.TEXT,
            dropdown_hover_color=Colors.SIDEBAR,
            font=("", 12),
            corner_radius=6,
            values=["▶ Tất cả rule đang bật"],
        )
        self.rule_selector.set("▶ Tất cả rule đang bật")
        self.rule_selector.pack(side="left", padx=(0, 8))

        # Populate rule selector with enabled rules
        self._update_rule_selector()

        # Summary label
        self.lbl_summary = ctk.CTkLabel(
            selector_frame,
            text="",
            font=("", 11),
            text_color=Colors.TEXT_MUTED,
        )
        self.lbl_summary.pack(side="right")
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

        self.lbl_stats_summary = ctk.CTkLabel(
            stats_frame,
            text="Ready — chọn rule rồi bấm Run Now.",
            font=("", 12),
            text_color=Colors.TEXT_MUTED,
        )
        self.lbl_stats_summary.pack(side="left")



    # ── Rules Tab (v2.0 — Dev-configured) ─────────────────────────────

    def _build_rules_tab(self) -> None:
        """Build Rules tab — dev-configured rules with switch + folder picker."""
        tab = self.tab_rules

        # Header explanation
        header = ctk.CTkFrame(
            tab, fg_color="#EBF8FF", corner_radius=10,
            border_color="#BEE3F8", border_width=1,
        )
        header.pack(fill="x", padx=12, pady=(12, 8))

        ctk.CTkLabel(
            header,
            text="📧  Chọn loại email cần tải",
            font=("", 15, "bold"),
            text_color=Colors.PRIMARY,
        ).pack(anchor="w", padx=16, pady=(10, 2))

        ctk.CTkLabel(
            header,
            text="Bật/tắt rule bạn muốn, chọn thư mục lưu. Bấm Run Now ở Dashboard khi sẵn sàng.",
            font=("", 12),
            text_color=Colors.TEXT_MUTED,
        ).pack(anchor="w", padx=16, pady=(0, 10))

        # Rules list
        self.rules_scroll = ctk.CTkScrollableFrame(
            tab,
            fg_color=Colors.LOG_BG,
            border_color=Colors.BORDER,
            border_width=1,
            corner_radius=8,
        )
        self.rules_scroll.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        # Store references to folder entries per rule
        self._rule_folder_entries: dict[str, ctk.CTkEntry] = {}

        self._refresh_rules_list()

    def _refresh_rules_list(self) -> None:
        """Rebuild rules display — dev-configured rule cards."""
        for widget in self.rules_scroll.winfo_children():
            widget.destroy()
        self._rule_folder_entries.clear()

        # Sync Dashboard rule selector dropdown
        if hasattr(self, "rule_selector"):
            self._update_rule_selector()
        if hasattr(self, "folder_menu"):
            self._update_folder_menu()

        if not self.rule_engine.rules:
            ctk.CTkLabel(
                self.rules_scroll,
                text="Chưa có rule nào được cấu hình.\n"
                     "Liên hệ quản trị viên để thêm rule.",
                text_color=Colors.TEXT_MUTED,
                font=("", 13),
                justify="center",
            ).pack(pady=40)
            return

        # Count enabled
        enabled_count = sum(1 for r in self.rule_engine.rules if r.enabled)
        total_count = len(self.rule_engine.rules)

        # Summary bar
        summary_frame = ctk.CTkFrame(self.rules_scroll, fg_color="transparent")
        summary_frame.pack(fill="x", padx=4, pady=(4, 8))
        ctk.CTkLabel(
            summary_frame,
            text=f"Đang bật {enabled_count}/{total_count} rule",
            font=("", 12, "bold"),
            text_color=Colors.SUCCESS if enabled_count > 0 else Colors.TEXT_MUTED,
        ).pack(side="left")

        for rule in self.rule_engine.rules:
            self._create_rule_card(rule)

    def _create_rule_card(self, rule: EmailRule) -> None:
        """Create a modern rule card with switch, description, and folder picker."""
        # Card border color indicates active/inactive
        border_color = Colors.PRIMARY if rule.enabled else Colors.BORDER
        card_bg = Colors.CARD if rule.enabled else "#FAFBFC"

        card = ctk.CTkFrame(
            self.rules_scroll,
            corner_radius=10,
            fg_color=card_bg,
            border_color=border_color,
            border_width=2 if rule.enabled else 1,
        )
        card.pack(fill="x", pady=5, padx=4)

        # ── Row 1: Icon + Name + Switch ────────────────────────────
        row1 = ctk.CTkFrame(card, fg_color="transparent")
        row1.pack(fill="x", padx=14, pady=(12, 0))

        # Icon (from rule metadata or handler)
        icon = rule.icon if rule.icon else "📧"
        ctk.CTkLabel(
            row1, text=icon, font=("", 22), width=32,
        ).pack(side="left", padx=(0, 8))

        # Rule name
        name_color = Colors.TEXT if rule.enabled else Colors.TEXT_MUTED
        ctk.CTkLabel(
            row1,
            text=rule.name,
            font=("", 15, "bold"),
            text_color=name_color,
        ).pack(side="left")

        # ON/OFF switch (large, easy to tap)
        switch_var = ctk.BooleanVar(value=rule.enabled)
        switch = ctk.CTkSwitch(
            row1,
            text="BẬT" if rule.enabled else "TẮT",
            variable=switch_var,
            onvalue=True,
            offvalue=False,
            fg_color=Colors.BORDER,
            progress_color=Colors.SUCCESS,
            button_color=Colors.CARD,
            button_hover_color=Colors.SIDEBAR,
            text_color=Colors.SUCCESS if rule.enabled else Colors.TEXT_MUTED,
            font=("", 12, "bold"),
            width=60,
            command=lambda r=rule, sv=switch_var: self._on_toggle_rule(r, sv),
        )
        switch.pack(side="right", padx=(8, 0))

        # ── Row 2: Description + file types badge ──────────────────
        row2 = ctk.CTkFrame(card, fg_color="transparent")
        row2.pack(fill="x", padx=14, pady=(4, 0))

        desc = rule.description or "Không có mô tả"
        ctk.CTkLabel(
            row2,
            text=desc,
            font=("", 12),
            text_color=Colors.TEXT_MUTED,
        ).pack(side="left")

        # File types badge
        if rule.file_types:
            badge_frame = ctk.CTkFrame(
                row2, fg_color="#EDF2F7", corner_radius=6,
            )
            badge_frame.pack(side="right")
            ctk.CTkLabel(
                badge_frame,
                text=rule.file_types,
                font=("", 10),
                text_color=Colors.TEXT_MUTED,
            ).pack(padx=8, pady=2)

        # ── Row 3: Folder picker ───────────────────────────────────
        row3 = ctk.CTkFrame(card, fg_color="transparent")
        row3.pack(fill="x", padx=14, pady=(8, 0))

        ctk.CTkLabel(
            row3,
            text="📁 Lưu vào:",
            font=("", 12, "bold"),
            text_color=Colors.TEXT,
        ).pack(side="left", padx=(0, 6))

        folder_entry = ctk.CTkEntry(
            row3,
            width=380,
            height=32,
            fg_color=Colors.LOG_BG,
            border_color=Colors.BORDER,
            text_color=Colors.TEXT,
            font=("", 11),
            placeholder_text="Chọn thư mục lưu file...",
        )
        # Pre-fill with rule's output_folder or global setting
        current_folder = rule.output_folder or self.settings.get("output_dir", "downloads")
        folder_entry.insert(0, current_folder)
        folder_entry.pack(side="left", padx=(0, 6))

        self._rule_folder_entries[rule.name] = folder_entry

        ctk.CTkButton(
            row3,
            text="Chọn...",
            width=70,
            height=32,
            fg_color=Colors.SIDEBAR,
            hover_color=Colors.BORDER,
            text_color=Colors.TEXT,
            font=("", 11),
            corner_radius=6,
            command=lambda r=rule, e=folder_entry: self._on_browse_rule_folder(r, e),
        ).pack(side="left")

        # ── Row 4: Auto-subfolder preview ──────────────────────────
        row4 = ctk.CTkFrame(card, fg_color="transparent")
        row4.pack(fill="x", padx=14, pady=(2, 10))

        from datetime import datetime
        month_str = datetime.now().strftime("%Y%m")
        folder_name = Path(current_folder).name if current_folder else "..."
        preview_text = f"📂 Cấu trúc: {folder_name}/{month_str}/file_name.pdf"
        ctk.CTkLabel(
            row4,
            text=preview_text,
            font=("", 10),
            text_color=Colors.FOOTER,
        ).pack(anchor="w", padx=(34, 0))

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
            title_frame, text="📖  Hướng Dẫn Sử Dụng — v2.0",
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
        self._help_section(scroll, "Bước 2 — Bật rule và chọn thư mục lưu", [
            ("📋", "Vào tab Rules",
             "Mỗi Rule đại diện cho 1 loại email cần tải (VTP, J&T...).\n"
             "Rules đã được cấu hình sẵn — bạn chỉ cần bật/tắt."),
            ("🔄", "Bật/Tắt rule",
             "Gạt công tắc BẬT/TẮT bên phải mỗi rule.\n"
             "Rule nào được bật sẽ chạy khi bấm Run Now."),
            ("📁", "Chọn thư mục lưu",
             "Nhấn 'Chọn...' để chọn thư mục lưu file cho từng rule.\n"
             "File tải về sẽ tự động sắp xếp theo tháng (vd: 202603/)."),
        ])

        # Step 3
        self._help_section(scroll, "Bước 3 — Cài đặt thư mục & lịch tự động", [
            ("📁", "Thư mục mặc định",
             "Vào Settings → mục Download Folder.\n"
             "Nhấn Browse... để chọn thư mục mặc định (dùng khi rule chưa chọn folder riêng)."),
            ("⏰", "Lịch tự động (Auto Schedule)",
             "Bật Enable automatic checking để ứng dụng tự chạy định kỳ.\n"
             "Đặt Interval (phút) — ví dụ 30 = kiểm tra email mỗi 30 phút."),
            ("💾", "Lưu cài đặt",
             "Nhấn Save Settings sau khi thay đổi."),
        ])

        # Step 4 — Per-rule run
        self._help_section(scroll, "Bước 4 — Chạy và theo dõi", [
            ("🎯", "Chọn rule cần chạy",
             "Trên Dashboard, dropdown 'Chạy rule' cho phép:\n"
             "• Chọn 'Tất cả rule đang bật' → chạy tuần tự tất cả\n"
             "• Chọn 1 rule cụ thể → chỉ chạy rule đó\n"
             "⚠ Rule tắt hiện '✗ TẮT' — phải bật ở tab Rules trước."),
            ("▶", "Bấm Run Now",
             "Ứng dụng sẽ duyệt Gmail theo rule đã chọn.\n"
             "Thanh progress bar hiển thị tiến độ.\n"
             "Log hiển thị chi tiết từng bước xử lý."),
            ("⏹", "Dừng giữa chừng",
             "Nhấn Stop bất cứ lúc nào để dừng quá trình."),
        ])

        # Step 5 — Folder & results
        self._help_section(scroll, "Bước 5 — Xem kết quả & thư mục", [
            ("📊", "Dialog hoàn tất",
             "Sau khi chạy xong, dialog hiện:\n"
             "• Số email, file đã tải, file bỏ qua (trùng)\n"
             "• Chi tiết từng file (tên, trạng thái)\n"
             "• Nút mở thư mục cho từng rule đã chạy."),
            ("📂", "Mở folder bất kỳ lúc nào",
             "Trên Dashboard, bấm '📂 Open Folder ▼' → chọn:\n"
             "• Folder mặc định\n"
             "• Folder riêng của từng rule (VTP, J&T...)\n"
             "Click → mở folder trong File Explorer."),
            ("↻", "Reset lịch sử",
             "Nhấn Reset để xóa danh sách email đã xử lý.\n"
             "⚠ Lần chạy tiếp theo sẽ tải lại TẤT CẢ email phù hợp."),
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
                "• Ứng dụng chỉ tải file từ các domain đáng tin cậy.\n"
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

    def _on_tab_changed(self, tab_name: str) -> None:
        """Refresh Dashboard data when user switches to it."""
        if tab_name == "Dashboard":
            # Reload rules from disk to pick up external edits
            self.rule_engine.load_rules()
            if hasattr(self, "rule_selector"):
                self._update_rule_selector()
            if hasattr(self, "folder_menu"):
                self._update_folder_menu()
        elif tab_name == "Rules":
            # Reload rules from disk for Rules tab too
            self.rule_engine.load_rules()
            if hasattr(self, "rules_scroll"):
                self._refresh_rules_list()

    def _update_rule_selector(self) -> None:
        """Update rule selector dropdown with current rules.

        Enabled rules show ✓, disabled show ✗ TẮT.
        Selecting a disabled rule triggers a warning.
        """
        options = ["▶ Tất cả rule đang bật"]
        for rule in self.rule_engine.rules:
            prefix = rule.icon or "📧"
            if rule.enabled:
                options.append(f"{prefix} {rule.name}")
            else:
                options.append(f"✗ {rule.name} (TẮT)")
        self.rule_selector.configure(values=options)

    def _get_selected_rules(self) -> list[EmailRule] | None:
        """Get rules to run based on selector dropdown.

        Returns None if a disabled rule was selected (shows warning).
        Returns empty list if no enabled rules exist.
        """
        selected = self.rule_selector.get()

        if selected == "▶ Tất cả rule đang bật":
            return self.rule_engine.get_enabled_rules()

        # Check if user selected a disabled rule
        if selected.startswith("✗") and "(TẮT)" in selected:
            # Extract rule name
            rule_name = selected.replace("✗ ", "").replace(" (TẮT)", "")
            messagebox.showinfo(
                "Rule chưa bật",
                f"Rule '{rule_name}' đang tắt.\n\n"
                f"Vui lòng vào tab Rules để bật rule này trước khi chạy.",
            )
            self.rule_selector.set("▶ Tất cả rule đang bật")
            return None

        # Find matching enabled rule by name
        for rule in self.rule_engine.rules:
            if rule.name in selected:
                if not rule.enabled:
                    messagebox.showinfo(
                        "Rule chưa bật",
                        f"Rule '{rule.name}' đang tắt.\n\n"
                        f"Vui lòng vào tab Rules để bật rule này trước khi chạy.",
                    )
                    self.rule_selector.set("▶ Tất cả rule đang bật")
                    return None
                return [rule]

        return self.rule_engine.get_enabled_rules()

    def _on_run_now(self) -> None:
        """Run selected rules in a background thread."""
        if self._is_running:
            return

        if not self.gmail.is_authenticated:
            messagebox.showwarning(
                "Chưa kết nối",
                "Vui lòng kết nối Gmail trong tab Settings trước.",
            )
            return

        # Get rules to run
        rules_to_run = self._get_selected_rules()
        if rules_to_run is None:
            # User selected a disabled rule — warning already shown
            return
        if not rules_to_run:
            messagebox.showinfo(
                "Không có rule",
                "Không có rule nào để chạy. Hãy bật ít nhất 1 rule trong tab Rules.",
            )
            return

        rule_names = ", ".join(r.name for r in rules_to_run)
        self._queue_log("info", f"Bắt đầu chạy: {rule_names}")

        # Store for CompletionDialog
        self._last_rules_run = rules_to_run

        self._is_running = True
        self.btn_run.configure(state="disabled", fg_color=Colors.SIDEBAR, text_color=Colors.TEXT_MUTED)
        self.btn_stop.configure(
            state="normal",
            border_color=Colors.DANGER,
            text_color=Colors.DANGER,
        )
        self._set_status("● Running...", Colors.PRIMARY)
        self.progress_bar.set(0)
        self.lbl_progress.configure(text=f"Đang chạy {len(rules_to_run)} rule...")

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
                result = self.scheduler.run_rules(rules_to_run)
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
            self.lbl_stats_summary.configure(text=last.summary())
            self.lbl_last_run.configure(
                text=f"Last run: {last.finished_at.strftime('%H:%M:%S')}"
            )
            self.lbl_progress.configure(
                text=f"Done — {last.attachments_downloaded + last.bang_ke_downloaded} files"
            )
            # Show completion dialog with per-rule folders
            output_dir = Path(self.settings.get("output_dir", "downloads"))
            rules_run = getattr(self, "_last_rules_run", [])
            CompletionDialog(self, last, output_dir, rules_run=rules_run)
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

    # ── Rule Actions (v2.0 — toggle + folder only) ────────────────────

    def _on_toggle_rule(self, rule: EmailRule, switch_var=None) -> None:
        """Toggle a rule on/off and save its folder path."""
        if switch_var is not None:
            rule.enabled = switch_var.get()
        else:
            rule.enabled = not rule.enabled

        # Also save folder path if entry exists
        if rule.name in self._rule_folder_entries:
            folder = self._rule_folder_entries[rule.name].get().strip()
            if folder:
                rule.output_folder = folder

        self.rule_engine.save_rules()
        self._refresh_rules_list()

    def _on_browse_rule_folder(self, rule: EmailRule, entry: ctk.CTkEntry) -> None:
        """Browse folder for a specific rule."""
        path = filedialog.askdirectory(title=f"Chọn thư mục cho: {rule.name}")
        if path:
            entry.delete(0, "end")
            entry.insert(0, path)
            rule.output_folder = path
            self.rule_engine.save_rules()

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


    def _update_folder_menu(self) -> None:
        """Rebuild folder dropdown with per-rule folders."""
        global_dir = self.settings.get("output_dir", "downloads")
        options = [f"📂 Mặc định: {Path(global_dir).name}"]
        for rule in self.rule_engine.rules:
            if rule.enabled:
                folder = rule.output_folder or global_dir
                icon = rule.icon or "📧"
                folder_name = Path(folder).name
                options.append(f"{icon} {rule.name}: {folder_name}")
        self.folder_menu.configure(values=options)
        self.folder_menu.set("📂 Open Folder")

    def _on_open_folder(self, selection: str = "") -> None:
        """Open the folder matching the user's dropdown selection."""
        global_dir = Path(self.settings.get("output_dir", "downloads"))

        # Default / header item
        if not selection or "Mặc định" in selection:
            open_folder(global_dir)
            self.folder_menu.set("📂 Open Folder")
            return

        # Find rule by name match
        for rule in self.rule_engine.rules:
            if rule.name in selection:
                folder = Path(rule.output_folder) if rule.output_folder else global_dir
                open_folder(folder)
                self.folder_menu.set("📂 Open Folder")
                return

        # Fallback
        open_folder(global_dir)
        self.folder_menu.set("📂 Open Folder")

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

    def __init__(self, parent, result, output_dir: Path, rules_run: list | None = None):
        super().__init__(parent)
        self.title("Hoàn tất")
        self.resizable(False, False)
        self.configure(fg_color=Colors.BG)
        self.transient(parent)
        self.grab_set()
        self._output_dir = output_dir
        self._rules_run = rules_run or []

        total_files = result.attachments_downloaded + result.bang_ke_downloaded
        has_errors = len(result.errors) > 0
        has_file_log = len(result.downloaded_files) > 0 or len(result.skipped_files) > 0
        has_multi_rules = len(self._rules_run) > 1

        # Dynamic height based on content
        base_h = 350
        if has_file_log:
            base_h += 180
        if has_errors:
            base_h += 24
        base_h += 80  # folder buttons section always visible
        if has_multi_rules:
            base_h += 40 * len(self._rules_run)
        self.geometry(f"480x{min(base_h, 700)}")

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

        # ── Folder buttons (per-rule) — always visible ──
        folder_card = ctk.CTkFrame(
            self, fg_color=Colors.CARD, corner_radius=10,
            border_color=Colors.BORDER, border_width=1,
        )
        folder_card.pack(fill="x", padx=20, pady=6)

        ctk.CTkLabel(
            folder_card, text="📂  Xem thư mục đã lưu",
            font=("", 13, "bold"), text_color=Colors.TEXT,
        ).pack(anchor="w", padx=14, pady=(8, 4))

        if has_multi_rules:
            # Per-rule folder buttons
            for rule in self._rules_run:
                r_icon = rule.icon or "📧"
                r_folder = Path(rule.output_folder) if rule.output_folder else output_dir
                folder_name = r_folder.name

                btn_row = ctk.CTkFrame(folder_card, fg_color="transparent")
                btn_row.pack(fill="x", padx=10, pady=2)

                ctk.CTkButton(
                    btn_row,
                    text=f"{r_icon}  {rule.name}  →  {folder_name}",
                    command=lambda f=r_folder: self._open_rule_folder(f),
                    height=34,
                    fg_color=Colors.PRIMARY,
                    hover_color=Colors.PRIMARY_HOVER,
                    font=("", 12),
                    corner_radius=6,
                    anchor="w",
                ).pack(fill="x")

            ctk.CTkFrame(folder_card, height=6, fg_color="transparent").pack()
        else:
            # Single rule — use THAT rule's folder
            single_rule = self._rules_run[0] if self._rules_run else None
            if single_rule and single_rule.output_folder:
                single_folder = Path(single_rule.output_folder)
                btn_label = f"{single_rule.icon or '📂'}  Mở: {single_folder.name}"
            else:
                single_folder = output_dir
                btn_label = "📂  Mở thư mục tải về"

            ctk.CTkButton(
                folder_card,
                text=btn_label,
                command=lambda f=single_folder: self._open_rule_folder(f),
                height=36,
                fg_color=Colors.PRIMARY,
                hover_color=Colors.PRIMARY_HOVER,
                font=("", 13, "bold"),
                corner_radius=8,
            ).pack(fill="x", padx=10, pady=(0, 8))

        # ── Close button ──────────────────────────
        ctk.CTkButton(
            self,
            text="Đóng",
            command=self.destroy,
            width=100,
            height=40,
            fg_color=Colors.SIDEBAR,
            hover_color=Colors.BORDER,
            text_color=Colors.TEXT,
            font=("", 13),
            corner_radius=8,
        ).pack(pady=(8, 16))

        # Center on screen
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        sx = (self.winfo_screenwidth() - w) // 2
        sy = (self.winfo_screenheight() - h) // 2
        self.geometry(f"+{sx}+{sy}")

    def _open_folder(self) -> None:
        open_folder(self._output_dir)

    def _open_rule_folder(self, folder: Path) -> None:
        open_folder(folder)


# RuleDialog removed in v2.0 — rules are now dev-configured only.
# Users control rules via toggle switch and folder picker on the Rules tab.


# ── Entry Point ──────────────────────────────────────────────────────

def main() -> None:
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
