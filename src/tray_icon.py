"""
System Tray Icon — Minimize to tray with menu and notifications.

Uses pystray for cross-platform tray icon support.
Runs on a separate thread from the main GUI.
"""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Callable

logger = logging.getLogger("email_auto_download.tray")

try:
    import pystray
    from PIL import Image
    HAS_PYSTRAY = True
except ImportError:
    HAS_PYSTRAY = False
    logger.debug("pystray not installed — tray icon disabled")


def _create_icon_image() -> "Image.Image":
    """Create a simple tray icon (blue envelope)."""
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    # Draw a simple blue square as icon
    for x in range(8, 56):
        for y in range(12, 52):
            img.putpixel((x, y), (49, 130, 206, 255))  # Colors.PRIMARY
    # White "envelope" lines
    for x in range(12, 52):
        img.putpixel((x, 16), (255, 255, 255, 255))
        img.putpixel((x, 48), (255, 255, 255, 255))
    for y in range(16, 48):
        img.putpixel((12, y), (255, 255, 255, 255))
        img.putpixel((51, y), (255, 255, 255, 255))
    return img


class TrayIcon:
    """System tray icon with menu and balloon notifications."""

    def __init__(
        self,
        on_show: Callable[[], None] | None = None,
        on_run: Callable[[], None] | None = None,
        on_stop: Callable[[], None] | None = None,
        on_quit: Callable[[], None] | None = None,
    ):
        self._on_show = on_show
        self._on_run = on_run
        self._on_stop = on_stop
        self._on_quit = on_quit
        self._icon: pystray.Icon | None = None
        self._thread: threading.Thread | None = None

    @property
    def available(self) -> bool:
        """Whether pystray is available."""
        return HAS_PYSTRAY

    def start(self) -> None:
        """Start the tray icon on a background thread."""
        if not HAS_PYSTRAY or self._icon:
            return

        menu = pystray.Menu(
            pystray.MenuItem("📂 Mở ứng dụng", self._show, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("▶  Chạy ngay", self._run),
            pystray.MenuItem("⏹  Dừng", self._stop),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("❌ Thoát", self._quit),
        )

        self._icon = pystray.Icon(
            name="EmailAutoDownload",
            icon=_create_icon_image(),
            title="Email Auto-Download Tool",
            menu=menu,
        )

        self._thread = threading.Thread(target=self._icon.run, daemon=True)
        self._thread.start()
        logger.info("System tray icon started")

    def stop(self) -> None:
        """Remove the tray icon."""
        if self._icon:
            try:
                self._icon.stop()
            except Exception:
                pass
            self._icon = None
            logger.info("System tray icon stopped")

    def notify(self, title: str, message: str) -> None:
        """Show a balloon/toast notification."""
        if self._icon:
            try:
                self._icon.notify(message, title)
            except Exception as e:
                logger.debug(f"Tray notification failed: {e}")

    def update_tooltip(self, text: str) -> None:
        """Update tray icon tooltip text."""
        if self._icon:
            self._icon.title = text

    # ── Menu callbacks ───────────────────────────────────

    def _show(self, *_) -> None:
        if self._on_show:
            self._on_show()

    def _run(self, *_) -> None:
        if self._on_run:
            self._on_run()

    def _stop(self, *_) -> None:
        if self._on_stop:
            self._on_stop()

    def _quit(self, *_) -> None:
        if self._on_quit:
            self._on_quit()
