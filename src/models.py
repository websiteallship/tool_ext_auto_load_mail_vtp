"""
Shared data models and exceptions for Email Auto-Download Tool.

All dataclasses and enums used across modules are defined here.
No business logic — only data structures.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path


# ============================================================================
# Exceptions
# ============================================================================

class AppError(Exception):
    """Base exception for the entire application."""

    def __init__(self, message: str, recoverable: bool = True):
        self.recoverable = recoverable
        super().__init__(message)


# Authentication
class AuthError(AppError):
    """Gmail authentication error."""


class TokenExpiredError(AuthError):
    """Token expired — can be auto-refreshed."""


class AuthRevokedError(AuthError):
    """User revoked access — needs re-authentication."""

    def __init__(self, message: str = "Gmail access revoked. Please re-authenticate."):
        super().__init__(message, recoverable=False)


# Network
class NetworkError(AppError):
    """Network connection error."""


class ApiQuotaError(NetworkError):
    """Gmail API quota exceeded."""

    def __init__(self, message: str = "Gmail API quota exceeded. Please wait."):
        super().__init__(message, recoverable=True)


# File System
class FileError(AppError):
    """File system error."""


class DiskSpaceError(FileError):
    """Disk space exhausted."""

    def __init__(self, message: str = "Not enough disk space."):
        super().__init__(message, recoverable=False)


# Configuration
class ConfigError(AppError):
    """Configuration error."""


class InvalidRuleError(ConfigError):
    """Invalid email rule configuration."""


# ============================================================================
# Enums
# ============================================================================

class DownloadStatus(Enum):
    """Status of a file download operation."""
    SUCCESS = "success"
    SKIPPED_DUPLICATE = "skipped_duplicate"
    FAILED = "failed"
    FAILED_RETRY_EXHAUSTED = "failed_retry_exhausted"


class SchedulerState(Enum):
    """State of the scheduler."""
    IDLE = "idle"
    RUNNING = "running"
    WAITING = "waiting"
    ERROR = "error"
    STOPPED = "stopped"


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class EmailMessage:
    """Represents a Gmail email message."""
    id: str
    subject: str
    sender: str
    date: datetime
    snippet: str = ""
    has_attachments: bool = False
    labels: list[str] = field(default_factory=list)


@dataclass
class Attachment:
    """Represents an email attachment."""
    id: str
    filename: str
    mime_type: str
    size: int  # bytes


@dataclass
class ExtractedLink:
    """A link extracted from email HTML body."""
    url: str
    text: str
    link_type: str  # "bang_ke" | "invoice_search" | "other"


@dataclass
class DownloadResult:
    """Result of a single file download operation."""
    status: DownloadStatus
    filepath: Path | None
    filename: str
    size_bytes: int = 0
    error_message: str | None = None

    @property
    def is_success(self) -> bool:
        return self.status == DownloadStatus.SUCCESS


@dataclass
class EmailRule:
    """An email processing rule — defines how to search and process emails."""
    name: str
    enabled: bool = True
    subject_query: str = ""
    sender_filter: str = ""
    label_filter: str = "INBOX"
    output_folder: str = "downloads"
    download_attachments: bool = True
    download_bang_ke: bool = True
    max_emails: int = 50
    attachment_extensions: list[str] = field(
        default_factory=lambda: [".pdf", ".xml", ".xlsx"]
    )

    def to_gmail_query(self) -> str:
        """Convert rule to Gmail search query string."""
        parts: list[str] = []
        if self.subject_query:
            parts.append(f'subject:"{self.subject_query}"')
        if self.sender_filter:
            parts.append(f"from:{self.sender_filter}")
        if self.label_filter and self.label_filter.upper() != "ALL":
            parts.append(f"in:{self.label_filter.lower()}")
        # Only filter by attachment if rule REQUIRES attachments
        # (don't add if only downloading bảng kê links from body)
        if self.download_attachments and not self.download_bang_ke:
            parts.append("has:attachment")
        return " ".join(parts)

    def to_dict(self) -> dict:
        """Serialize to dictionary for JSON storage."""
        return {
            "name": self.name,
            "enabled": self.enabled,
            "subject_query": self.subject_query,
            "sender_filter": self.sender_filter,
            "label_filter": self.label_filter,
            "output_folder": self.output_folder,
            "download_attachments": self.download_attachments,
            "download_bang_ke": self.download_bang_ke,
            "max_emails": self.max_emails,
            "attachment_extensions": self.attachment_extensions,
        }

    @classmethod
    def from_dict(cls, data: dict) -> EmailRule:
        """Deserialize from dictionary."""
        return cls(
            name=data.get("name", "Unnamed"),
            enabled=data.get("enabled", True),
            subject_query=data.get("subject_query", ""),
            sender_filter=data.get("sender_filter", ""),
            label_filter=data.get("label_filter", "INBOX"),
            output_folder=data.get("output_folder", "downloads"),
            download_attachments=data.get("download_attachments", True),
            download_bang_ke=data.get("download_bang_ke", True),
            max_emails=data.get("max_emails", 50),
            attachment_extensions=data.get(
                "attachment_extensions", [".pdf", ".xml", ".xlsx"]
            ),
        )


@dataclass
class RunResult:
    """Result of a scheduler run (one complete processing cycle)."""
    started_at: datetime
    finished_at: datetime
    rules_processed: int = 0
    emails_found: int = 0
    attachments_downloaded: int = 0
    bang_ke_downloaded: int = 0
    errors: list[str] = field(default_factory=list)
    skipped_duplicates: int = 0
    downloaded_files: list[str] = field(default_factory=list)
    skipped_files: list[str] = field(default_factory=list)

    @property
    def duration_seconds(self) -> float:
        return (self.finished_at - self.started_at).total_seconds()

    @property
    def is_success(self) -> bool:
        return len(self.errors) == 0

    def summary(self) -> str:
        """Human-readable summary of the run."""
        status = "✅" if self.is_success else "⚠️"
        return (
            f"{status} {self.rules_processed} rules, "
            f"{self.emails_found} emails, "
            f"{self.attachments_downloaded + self.bang_ke_downloaded} files downloaded, "
            f"{self.skipped_duplicates} skipped, "
            f"{len(self.errors)} errors "
            f"({self.duration_seconds:.1f}s)"
        )
