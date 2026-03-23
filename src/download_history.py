"""
Download History — Track downloaded files across runs.

Stores history in JSON file, provides stats (today/week/total)
and filtering by rule name.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

from src.models import HistoryEntry

logger = logging.getLogger("email_auto_download")

HISTORY_FILE = "config/download_history.json"
MAX_ENTRIES = 5000  # Keep last N entries to avoid huge files


class DownloadHistory:
    """Persistent download history with stats."""

    def __init__(self, filepath: str = HISTORY_FILE):
        self._filepath = Path(filepath)
        self._entries: list[dict] = []
        self._load()

    def _load(self) -> None:
        """Load history from JSON file."""
        if self._filepath.exists():
            try:
                data = json.loads(self._filepath.read_text(encoding="utf-8"))
                self._entries = data if isinstance(data, list) else []
            except (json.JSONDecodeError, OSError):
                self._entries = []
        else:
            self._entries = []

    def _save(self) -> None:
        """Save history to JSON file."""
        self._filepath.parent.mkdir(parents=True, exist_ok=True)
        # Trim to max entries
        if len(self._entries) > MAX_ENTRIES:
            self._entries = self._entries[-MAX_ENTRIES:]
        self._filepath.write_text(
            json.dumps(self._entries, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def add_entry(
        self,
        rule_name: str,
        filename: str,
        status: str,
        timestamp: datetime | None = None,
    ) -> None:
        """Add a download record."""
        ts = (timestamp or datetime.now()).isoformat(timespec="seconds")
        self._entries.append({
            "timestamp": ts,
            "rule_name": rule_name,
            "filename": filename,
            "status": status,
        })
        self._save()

    def get_entries(
        self,
        rule_filter: str | None = None,
        limit: int = 200,
    ) -> list[HistoryEntry]:
        """Get history entries, newest first."""
        entries = list(reversed(self._entries))
        if rule_filter:
            entries = [e for e in entries if e.get("rule_name") == rule_filter]
        return [
            HistoryEntry(
                timestamp=e.get("timestamp", ""),
                rule_name=e.get("rule_name", ""),
                filename=e.get("filename", ""),
                status=e.get("status", ""),
            )
            for e in entries[:limit]
        ]

    def get_stats(self) -> dict:
        """Return download counts: today, this week, total."""
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=today_start.weekday())

        today = 0
        week = 0
        total = 0

        for e in self._entries:
            if e.get("status") != "downloaded":
                continue
            total += 1
            try:
                ts = datetime.fromisoformat(e["timestamp"])
                if ts >= today_start:
                    today += 1
                if ts >= week_start:
                    week += 1
            except (ValueError, KeyError):
                pass

        return {"today": today, "week": week, "total": total}

    def clear(self) -> None:
        """Clear all history."""
        self._entries.clear()
        if self._filepath.exists():
            self._filepath.unlink()
        logger.info("Download history cleared")

    def reload(self) -> None:
        """Reload from disk."""
        self._load()
