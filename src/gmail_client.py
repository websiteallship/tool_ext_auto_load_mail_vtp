"""
Gmail Client — Connect to Gmail API for searching, reading, and downloading.

Supports OAuth2 authentication with token stored in Windows Credential Locker.
Provides a clean facade for Gmail operations.

Skills applied: 01_gmail-automation, 06_secrets-management, 09_error-handling-patterns
"""

from __future__ import annotations

import base64
import json
import logging
import os
from pathlib import Path

import keyring
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from src.models import (
    Attachment,
    AuthError,
    AuthRevokedError,
    EmailMessage,
    NetworkError,
    TokenExpiredError,
)

logger = logging.getLogger("email_auto_download.gmail_client")

load_dotenv()

# Gmail API scopes — minimal permissions
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
]

SERVICE_NAME = "email-auto-download"
KEYRING_TOKEN_KEY = "gmail_oauth_token"


class GmailClient:
    """
    Facade for Gmail API operations.

    Handles authentication, email search, body retrieval, and attachment download.
    """

    def __init__(self):
        self._service = None
        self._credentials: Credentials | None = None
        self._user_email: str | None = None
        self._label_cache: dict[str, str] = {}  # name -> id

    @property
    def is_authenticated(self) -> bool:
        """Check if client has valid credentials."""
        return self._credentials is not None and self._credentials.valid

    @property
    def user_email(self) -> str | None:
        """Get authenticated user's email address."""
        return self._user_email

    def authenticate(self) -> bool:
        """
        Authenticate with Gmail API using OAuth2.

        First attempt: load saved token from keyring.
        If expired: auto-refresh.
        If no token: open browser for consent.

        Returns:
            True if authentication succeeded

        Raises:
            AuthError: If authentication fails
        """
        creds = self._load_token()

        if creds and creds.valid:
            self._credentials = creds
            self._build_service()
            self._fetch_user_email()
            logger.info(f"Authenticated as {self._user_email}")
            return True

        if creds and creds.expired and creds.refresh_token:
            try:
                logger.info("Token expired, refreshing...")
                creds.refresh(Request())
                self._save_token(creds)
                self._credentials = creds
                self._build_service()
                self._fetch_user_email()
                logger.info(f"Token refreshed for {self._user_email}")
                return True
            except Exception as e:
                logger.warning(f"Token refresh failed: {e}")
                # Fall through to re-authenticate

        # No valid token — need browser-based auth
        try:
            creds = self._browser_auth()
            self._save_token(creds)
            self._credentials = creds
            self._build_service()
            self._fetch_user_email()
            logger.info(f"New authentication for {self._user_email}")
            return True
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise AuthError(f"Gmail authentication failed: {e}") from e

    def disconnect(self) -> None:
        """Remove stored credentials and disconnect."""
        try:
            keyring.delete_password(SERVICE_NAME, KEYRING_TOKEN_KEY)
        except keyring.errors.PasswordDeleteError:
            pass
        self._credentials = None
        self._service = None
        self._user_email = None
        logger.info("Disconnected from Gmail")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True,
    )
    def search_emails(
        self, query: str, max_results: int = 50
    ) -> list[EmailMessage]:
        """
        Search Gmail for emails matching query.

        Args:
            query: Gmail search query (e.g. 'subject:"Viettel" has:attachment')
            max_results: Maximum number of results

        Returns:
            List of EmailMessage objects

        Raises:
            AuthError: If not authenticated
            NetworkError: If API call fails
        """
        self._ensure_authenticated()
        logger.info(f"Searching: {query}")

        try:
            results = (
                self._service.users()
                .messages()
                .list(userId="me", q=query, maxResults=max_results)
                .execute()
            )

            messages = results.get("messages", [])
            if not messages:
                logger.info("No emails found")
                return []

            email_list: list[EmailMessage] = []
            for msg_ref in messages:
                msg = self._get_message_metadata(msg_ref["id"])
                if msg:
                    email_list.append(msg)

            logger.info(f"Found {len(email_list)} emails")
            return email_list

        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise NetworkError(f"Gmail search failed: {e}") from e

    def get_email_body(self, message_id: str) -> str:
        """
        Get HTML body of an email.

        Args:
            message_id: Gmail message ID

        Returns:
            HTML body string (empty string if not found)
        """
        self._ensure_authenticated()

        try:
            msg = (
                self._service.users()
                .messages()
                .get(userId="me", id=message_id, format="full")
                .execute()
            )
            return self._extract_body(msg.get("payload", {}))
        except Exception as e:
            logger.error(f"Failed to get body for {message_id}: {e}")
            return ""

    def get_attachments(self, message_id: str) -> list[Attachment]:
        """
        Get list of attachments for an email.

        Args:
            message_id: Gmail message ID

        Returns:
            List of Attachment objects
        """
        self._ensure_authenticated()

        try:
            msg = (
                self._service.users()
                .messages()
                .get(userId="me", id=message_id, format="full")
                .execute()
            )
            return self._extract_attachments_info(msg.get("payload", {}))
        except Exception as e:
            logger.error(f"Failed to get attachments for {message_id}: {e}")
            return []

    def download_attachment(
        self, message_id: str, attachment_id: str
    ) -> tuple[bytes, str]:
        """
        Download a specific attachment.

        Args:
            message_id: Gmail message ID
            attachment_id: Attachment ID

        Returns:
            Tuple of (file_bytes, filename)
        """
        self._ensure_authenticated()

        try:
            att = (
                self._service.users()
                .messages()
                .attachments()
                .get(userId="me", messageId=message_id, id=attachment_id)
                .execute()
            )
            data = base64.urlsafe_b64decode(att["data"])
            return data, ""
        except Exception as e:
            logger.error(f"Failed to download attachment {attachment_id}: {e}")
            raise NetworkError(f"Attachment download failed: {e}") from e

    def add_label(self, message_id: str, label_name: str) -> None:
        """Add a label to a message."""
        self._ensure_authenticated()

        try:
            label_id = self._get_or_create_label(label_name)
            self._service.users().messages().modify(
                userId="me",
                id=message_id,
                body={"addLabelIds": [label_id]},
            ).execute()
            logger.debug(f"Added label '{label_name}' to {message_id}")
        except Exception as e:
            logger.warning(f"Failed to add label: {e}")

    def remove_label(self, message_id: str, label_name: str) -> None:
        """Remove a label from a message."""
        self._ensure_authenticated()

        try:
            label_id = self._get_or_create_label(label_name)
            self._service.users().messages().modify(
                userId="me",
                id=message_id,
                body={"removeLabelIds": [label_id]},
            ).execute()
            logger.debug(f"Removed label '{label_name}' from {message_id}")
        except Exception as e:
            logger.warning(f"Failed to remove label: {e}")

    # ── Private helpers ──────────────────────────────────────────────

    def _ensure_authenticated(self) -> None:
        """Raise if not authenticated."""
        if not self.is_authenticated:
            raise AuthError("Not authenticated. Call authenticate() first.")

    def _build_service(self) -> None:
        """Build Gmail API service."""
        self._service = build("gmail", "v1", credentials=self._credentials)

    def _browser_auth(self) -> Credentials:
        """Run OAuth2 browser-based authentication flow."""
        client_id = os.getenv("GMAIL_CLIENT_ID")
        client_secret = os.getenv("GMAIL_CLIENT_SECRET")

        if not client_id or not client_secret:
            # Find credentials.json — support dev and bundled .exe
            creds_file = self._find_credentials()
            if creds_file:
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(creds_file), SCOPES
                )
            else:
                raise AuthError(
                    "Không tìm thấy credentials.json. "
                    "Liên hệ quản trị viên để được hỗ trợ."
                )
        else:
            client_config = {
                "installed": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": ["http://localhost"],
                }
            }
            flow = InstalledAppFlow.from_client_config(client_config, SCOPES)

        creds = flow.run_local_server(port=0)
        return creds

    @staticmethod
    def _find_credentials() -> Path | None:
        """Find credentials.json — supports both dev and bundled .exe.

        Search order:
        1. Current directory (allows user override)
        2. PyInstaller bundled path (sys._MEIPASS)
        """
        import sys

        # 1. Current directory
        local = Path("credentials.json")
        if local.exists():
            logger.debug("Found credentials.json in current directory")
            return local

        # 2. Bundled inside PyInstaller .exe
        if hasattr(sys, "_MEIPASS"):
            bundled = Path(sys._MEIPASS) / "credentials.json"
            if bundled.exists():
                logger.debug("Found credentials.json in bundled path")
                return bundled

        return None

    def _fetch_user_email(self) -> None:
        """Get authenticated user's email address."""
        try:
            profile = (
                self._service.users()
                .getProfile(userId="me")
                .execute()
            )
            self._user_email = profile.get("emailAddress", "unknown")
        except Exception:
            self._user_email = "unknown"

    def _save_token(self, creds: Credentials) -> None:
        """Save OAuth token to Windows Credential Locker."""
        token_data = {
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": list(creds.scopes) if creds.scopes else SCOPES,
        }
        keyring.set_password(SERVICE_NAME, KEYRING_TOKEN_KEY, json.dumps(token_data))
        logger.debug("Token saved to keyring")

    def _load_token(self) -> Credentials | None:
        """Load OAuth token from Windows Credential Locker."""
        raw = keyring.get_password(SERVICE_NAME, KEYRING_TOKEN_KEY)
        if not raw:
            return None

        try:
            data = json.loads(raw)
            creds = Credentials(
                token=data.get("token"),
                refresh_token=data.get("refresh_token"),
                token_uri=data.get("token_uri", "https://oauth2.googleapis.com/token"),
                client_id=data.get("client_id"),
                client_secret=data.get("client_secret"),
                scopes=data.get("scopes", SCOPES),
            )
            return creds
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Invalid stored token: {e}")
            return None

    def _get_message_metadata(self, message_id: str) -> EmailMessage | None:
        """Fetch message metadata (subject, sender, date)."""
        try:
            msg = (
                self._service.users()
                .messages()
                .get(
                    userId="me",
                    id=message_id,
                    format="metadata",
                    metadataHeaders=["Subject", "From", "Date"],
                )
                .execute()
            )

            headers = {
                h["name"]: h["value"]
                for h in msg.get("payload", {}).get("headers", [])
            }

            from datetime import datetime
            from email.utils import parsedate_to_datetime

            email_date = datetime.now()
            raw_date = headers.get("Date", "")
            if raw_date:
                try:
                    email_date = parsedate_to_datetime(raw_date)
                except (ValueError, TypeError):
                    pass

            return EmailMessage(
                id=message_id,
                subject=headers.get("Subject", "(no subject)"),
                sender=headers.get("From", "unknown"),
                date=email_date,
                snippet=msg.get("snippet", ""),
                has_attachments="ATTACHMENT" in msg.get("payload", {}).get(
                    "mimeType", ""
                )
                or bool(self._find_attachment_parts(msg.get("payload", {}))),
                labels=msg.get("labelIds", []),
            )
        except Exception as e:
            logger.warning(f"Failed to get metadata for {message_id}: {e}")
            return None

    def _extract_body(self, payload: dict) -> str:
        """Extract HTML body from message payload (recursive)."""
        # Direct body
        if payload.get("mimeType") == "text/html":
            data = payload.get("body", {}).get("data", "")
            if data:
                return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

        # Multipart — search parts
        for part in payload.get("parts", []):
            if part.get("mimeType") == "text/html":
                data = part.get("body", {}).get("data", "")
                if data:
                    return base64.urlsafe_b64decode(data).decode(
                        "utf-8", errors="replace"
                    )
            # Nested multipart
            result = self._extract_body(part)
            if result:
                return result

        return ""

    def _extract_attachments_info(self, payload: dict) -> list[Attachment]:
        """Extract attachment info from message payload."""
        parts = self._find_attachment_parts(payload)
        attachments: list[Attachment] = []

        for part in parts:
            att_id = part.get("body", {}).get("attachmentId", "")
            if att_id:
                attachments.append(
                    Attachment(
                        id=att_id,
                        filename=part.get("filename", "unknown"),
                        mime_type=part.get("mimeType", "application/octet-stream"),
                        size=part.get("body", {}).get("size", 0),
                    )
                )

        return attachments

    def _find_attachment_parts(self, payload: dict) -> list[dict]:
        """Recursively find all attachment parts in payload."""
        parts: list[dict] = []

        if payload.get("filename"):
            att_id = payload.get("body", {}).get("attachmentId")
            if att_id:
                parts.append(payload)

        for part in payload.get("parts", []):
            parts.extend(self._find_attachment_parts(part))

        return parts

    def _get_or_create_label(self, label_name: str) -> str:
        """Get label ID by name, create if not exists. Uses cache."""
        if label_name in self._label_cache:
            return self._label_cache[label_name]

        labels = (
            self._service.users().labels().list(userId="me").execute()
        )
        for label in labels.get("labels", []):
            self._label_cache[label["name"]] = label["id"]
            if label["name"] == label_name:
                return label["id"]

        # Create label
        body = {
            "name": label_name,
            "labelListVisibility": "labelShow",
            "messageListVisibility": "show",
        }
        result = (
            self._service.users()
            .labels()
            .create(userId="me", body=body)
            .execute()
        )
        self._label_cache[label_name] = result["id"]
        return result["id"]
