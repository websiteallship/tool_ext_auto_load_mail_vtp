"""
Scheduler — Orchestrate email processing runs.

Connects all core modules: GmailClient → LinkExtractor → FileDownloader.
Manages run-once and auto-scheduled execution with progress callbacks.

Skills applied: 05_async-python-patterns, 09_error-handling-patterns
"""

from __future__ import annotations

import json
import logging
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable

from src.file_downloader import FileDownloader
from src.gmail_client import GmailClient
from src.link_extractor import LinkExtractor
from src.models import (
    AppError,
    AuthError,
    DownloadStatus,
    EmailRule,
    RunResult,
    SchedulerState,
)
from src.rule_engine import RuleEngine

logger = logging.getLogger("email_auto_download.scheduler")

PROCESSED_EMAILS_FILE = "config/processed_emails.json"


class Scheduler:
    """
    Orchestrate email processing.

    Runs on a background thread when in auto mode.
    Reports progress via callbacks (thread-safe).
    """

    def __init__(
        self,
        gmail_client: GmailClient,
        rule_engine: RuleEngine,
        output_dir: Path,
        interval_minutes: int = 30,
        on_log: Callable[[str, str], None] | None = None,
        on_state_change: Callable[[SchedulerState], None] | None = None,
        on_progress: Callable[[str], None] | None = None,
        on_complete: Callable[[RunResult], None] | None = None,
    ):
        self.gmail = gmail_client
        self.rule_engine = rule_engine
        self.output_dir = Path(output_dir)
        self.interval_minutes = interval_minutes

        self._on_log = on_log
        self._on_state_change = on_state_change
        self._on_progress = on_progress
        self._on_complete = on_complete

        self._state = SchedulerState.IDLE
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._last_result: RunResult | None = None
        self._next_run: datetime | None = None

        self._link_extractor = LinkExtractor()
        self._processed_ids: set[str] = set()
        self._load_processed_ids()

    @property
    def state(self) -> SchedulerState:
        return self._state

    @property
    def next_run(self) -> datetime | None:
        return self._next_run

    @property
    def last_result(self) -> RunResult | None:
        return self._last_result

    def run_once(self) -> RunResult:
        """
        Run one complete processing cycle for all enabled rules.

        Returns:
            RunResult with statistics
        """
        self._set_state(SchedulerState.RUNNING)
        started = datetime.now()
        result = RunResult(started_at=started, finished_at=started)

        # Reload from disk so external resets (delete file) take effect
        self._load_processed_ids()

        try:
            rules = self.rule_engine.get_enabled_rules()
            result.rules_processed = len(rules)
            self._log("info", f"Starting run ({len(rules)} rules enabled)")

            for rule in rules:
                if self._stop_event.is_set():
                    self._log("info", "Run stopped by user")
                    break
                self._process_rule(rule, result)

        except AuthError as e:
            self._log("error", f"Authentication error: {e}")
            result.errors.append(str(e))
        except AppError as e:
            self._log("error", f"Application error: {e}")
            result.errors.append(str(e))
        except Exception as e:
            self._log("error", f"Unexpected error: {e}")
            result.errors.append(str(e))
        finally:
            result.finished_at = datetime.now()
            self._last_result = result
            self._save_processed_ids()
            self._log("info", result.summary())
            if self._on_complete:
                try:
                    self._on_complete(result)
                except Exception:
                    pass

        return result

    def start(self) -> None:
        """Start auto-scheduled processing in background thread."""
        if self._thread and self._thread.is_alive():
            logger.warning("Scheduler already running")
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        self._log("info", f"Auto-scheduler started (every {self.interval_minutes} min)")

    def stop(self) -> None:
        """Stop auto-scheduled processing."""
        self._stop_event.set()
        self._set_state(SchedulerState.STOPPED)
        self._next_run = None
        self._log("info", "Scheduler stopped")

    def clear_history(self) -> None:
        """Clear processed email history (public API)."""
        self._processed_ids.clear()
        path = Path(PROCESSED_EMAILS_FILE)
        if path.exists():
            path.unlink()
        self._log("info", "Processed email history cleared")

    # ── Processing Logic ─────────────────────────────────────────────

    def _process_rule(self, rule: EmailRule, result: RunResult) -> None:
        """Process a single email rule."""
        self._log("info", f"Processing rule: {rule.name}")
        self._progress(f"Rule: {rule.name}")

        try:
            query = rule.to_gmail_query()
            emails = self.gmail.search_emails(query, max_results=rule.max_emails)
            result.emails_found += len(emails)
            self._log("info", f"Found {len(emails)} emails for rule '{rule.name}'")

            downloader = FileDownloader(
                output_dir=self.output_dir,
                skip_duplicates=True,
            )

            skipped_count = 0
            for email in emails:
                if self._stop_event.is_set():
                    break

                # Skip already processed
                if email.id in self._processed_ids:
                    skipped_count += 1
                    continue

                self._progress(f"Email: {email.subject[:50]}")
                self._process_email(email, rule, downloader, result)
                self._processed_ids.add(email.id)

            if skipped_count > 0:
                self._log("info", f"  ⏭ {skipped_count} email(s) đã xử lý trước đó — bỏ qua")

            downloader.close()

        except Exception as e:
            self._log("error", f"Rule '{rule.name}' failed: {e}")
            result.errors.append(f"Rule '{rule.name}': {e}")

    def _process_email(
        self,
        email,
        rule: EmailRule,
        downloader: FileDownloader,
        result: RunResult,
    ) -> None:
        """Process a single email: download attachments + bảng kê."""
        self._log("info", f"  → Email: {email.subject[:60]}")

        # 1. Download attachments
        if rule.download_attachments:
            try:
                attachments = self.gmail.get_attachments(email.id)
                self._log("info", f"    Attachments found: {len(attachments)}")
                for att in attachments:
                    ext = Path(att.filename).suffix.lower()
                    if rule.attachment_extensions and ext not in rule.attachment_extensions:
                        self._log("info", f"    Skipped (extension {ext} not in filter): {att.filename}")
                        continue
                    try:
                        data, _ = self.gmail.download_attachment(email.id, att.id)
                        dl_result = downloader.save_attachment(data, att.filename)
                        self._log("info", f"    [{dl_result.status.value}] {att.filename}")
                        if dl_result.status == DownloadStatus.SUCCESS:
                            result.attachments_downloaded += 1
                            result.downloaded_files.append(att.filename)
                        elif dl_result.status == DownloadStatus.SKIPPED_DUPLICATE:
                            result.skipped_duplicates += 1
                            result.skipped_files.append(att.filename)
                    except Exception as e:
                        self._log("warning", f"    Attachment download error ({att.filename}): {e}")
                        result.errors.append(f"Attachment {att.filename}: {e}")
            except Exception as e:
                self._log("warning", f"    get_attachments() error: {e}")
                result.errors.append(f"get_attachments: {e}")

        # 2. Extract and download bảng kê
        if rule.download_bang_ke:
            try:
                body = self.gmail.get_email_body(email.id)
                self._log("info", f"    Body length: {len(body) if body else 0} chars")
                if body:
                    bang_ke_url = self._link_extractor.extract_bang_ke_link(body)
                    self._log("info", f"    Bảng kê URL: {bang_ke_url or 'NOT FOUND'}")
                    if bang_ke_url:
                        self._log("info", "    Downloading bảng kê...")
                        dl_result = downloader.download_from_url(
                            bang_ke_url, subfolder="bang_ke"
                        )
                        self._log("info", f"    [{dl_result.status.value}] bangke — {dl_result.error_message or dl_result.filename}")
                        if dl_result.status == DownloadStatus.SUCCESS:
                            result.bang_ke_downloaded += 1
                            result.downloaded_files.append(f"📊 {dl_result.filename}")
                        elif dl_result.status == DownloadStatus.SKIPPED_DUPLICATE:
                            result.skipped_duplicates += 1
                            result.skipped_files.append(f"📊 {dl_result.filename}")
                        elif dl_result.status in (
                            DownloadStatus.FAILED,
                            DownloadStatus.FAILED_RETRY_EXHAUSTED,
                        ):
                            self._log("warning", f"    Bảng kê download failed: {dl_result.error_message}")
                else:
                    self._log("warning", "    Email body is empty — skip bảng kê extraction")
            except Exception as e:
                self._log("warning", f"    Bảng kê extraction error: {e}")

    # ── Auto-schedule Loop ───────────────────────────────────────────

    def _run_loop(self) -> None:
        """Background thread: run → wait → repeat."""
        while not self._stop_event.is_set():
            result = self.run_once()

            if self._stop_event.is_set():
                break

            # Wait for next run
            self._set_state(SchedulerState.WAITING)
            wait_seconds = self.interval_minutes * 60
            self._next_run = datetime.now().replace(
                second=0, microsecond=0
            )
            self._next_run += timedelta(minutes=self.interval_minutes)

            self._log("info", f"Next run at {self._next_run.strftime('%H:%M:%S')}")

            # Sleep in small increments so we can check stop_event
            for _ in range(wait_seconds):
                if self._stop_event.is_set():
                    break
                time.sleep(1)

        self._set_state(SchedulerState.STOPPED)

    # ── State & Callbacks ────────────────────────────────────────────

    def _set_state(self, state: SchedulerState) -> None:
        """Update state and notify callback."""
        self._state = state
        if self._on_state_change:
            try:
                self._on_state_change(state)
            except Exception:
                pass

    def _log(self, level: str, message: str) -> None:
        """Log message and notify callback."""
        getattr(logger, level, logger.info)(message)
        if self._on_log:
            try:
                self._on_log(level, message)
            except Exception:
                pass

    def _progress(self, message: str) -> None:
        """Notify progress callback."""
        if self._on_progress:
            try:
                self._on_progress(message)
            except Exception:
                pass

    # ── Processed Email Tracking ─────────────────────────────────────

    def _load_processed_ids(self) -> None:
        """Load processed email IDs from file."""
        path = Path(PROCESSED_EMAILS_FILE)
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._processed_ids = set(data.get("processed_ids", []))
                logger.debug(f"Loaded {len(self._processed_ids)} processed email IDs")
            except (json.JSONDecodeError, KeyError):
                self._processed_ids = set()

    def _save_processed_ids(self) -> None:
        """Save processed email IDs to file."""
        path = Path(PROCESSED_EMAILS_FILE)
        path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "last_updated": datetime.now().isoformat(),
            "count": len(self._processed_ids),
            "processed_ids": list(self._processed_ids),
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
