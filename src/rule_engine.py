"""
Rule Engine — Load, save, validate, and manage email processing rules.

Rules are stored in JSON and define how to search and handle emails.
Data-driven: adding new email types requires only new JSON config, not code.

Skills applied: 02_python-pro, 08_clean-code
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from src.models import EmailRule, ConfigError, InvalidRuleError

logger = logging.getLogger("email_auto_download.rule_engine")

DEFAULT_RULE = EmailRule(
    name="Viettel Post Invoice",
    enabled=True,
    subject_query="Tổng công ty Cổ phần Bưu Chính Viettel",
    sender_filter="noreply@viettelpost.com.vn",
    label_filter="INBOX",
    output_folder="downloads/viettel_post",
    download_attachments=True,
    download_bang_ke=True,
    max_emails=50,
    attachment_extensions=[".pdf", ".xml"],
)


class RuleEngine:
    """
    Manage email processing rules from JSON config.

    Handles CRUD operations and validation.
    Thread-safe for read operations.
    """

    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.rules: list[EmailRule] = []

    def load_rules(self) -> list[EmailRule]:
        """
        Load rules from JSON file. Creates default rule if file doesn't exist.

        Returns:
            List of loaded EmailRule objects
        """
        if not self.config_path.exists():
            logger.info("No rules file found, creating default rule")
            self.rules = [DEFAULT_RULE]
            self.save_rules()
            return self.rules

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, list):
                raise ConfigError(f"rules.json must be a JSON array, got {type(data).__name__}")

            self.rules = [EmailRule.from_dict(item) for item in data]
            logger.info(f"Loaded {len(self.rules)} rules from {self.config_path.name}")
            return self.rules

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {self.config_path}: {e}")
            raise ConfigError(f"Cannot parse rules file: {e}") from e

    def save_rules(self) -> None:
        """Save current rules to JSON file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        data = [rule.to_dict() for rule in self.rules]
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved {len(self.rules)} rules to {self.config_path.name}")

    def add_rule(self, rule: EmailRule) -> None:
        """
        Add a new rule. Validates before adding.

        Args:
            rule: EmailRule to add

        Raises:
            InvalidRuleError: If rule is invalid
        """
        errors = self.validate_rule(rule)
        if errors:
            raise InvalidRuleError(f"Invalid rule: {'; '.join(errors)}")

        self.rules.append(rule)
        self.save_rules()
        logger.info(f"Added rule: {rule.name}")

    def remove_rule(self, name: str) -> bool:
        """
        Remove a rule by name.

        Args:
            name: Name of the rule to remove

        Returns:
            True if rule was found and removed
        """
        original_count = len(self.rules)
        self.rules = [r for r in self.rules if r.name != name]

        if len(self.rules) < original_count:
            self.save_rules()
            logger.info(f"Removed rule: {name}")
            return True

        logger.warning(f"Rule not found: {name}")
        return False

    def update_rule(self, name: str, updated_rule: EmailRule) -> bool:
        """
        Update an existing rule by name.

        Args:
            name: Name of the rule to update
            updated_rule: New rule data

        Returns:
            True if rule was found and updated
        """
        for i, rule in enumerate(self.rules):
            if rule.name == name:
                errors = self.validate_rule(updated_rule, exclude_name=name)
                if errors:
                    raise InvalidRuleError(f"Invalid rule: {'; '.join(errors)}")
                self.rules[i] = updated_rule
                self.save_rules()
                logger.info(f"Updated rule: {name}")
                return True

        logger.warning(f"Rule not found for update: {name}")
        return False

    def get_enabled_rules(self) -> list[EmailRule]:
        """Get all currently enabled rules."""
        enabled = [r for r in self.rules if r.enabled]
        logger.debug(f"{len(enabled)}/{len(self.rules)} rules enabled")
        return enabled

    def get_rule_by_name(self, name: str) -> EmailRule | None:
        """Find a rule by name."""
        for rule in self.rules:
            if rule.name == name:
                return rule
        return None

    def validate_rule(
        self, rule: EmailRule, exclude_name: str | None = None
    ) -> list[str]:
        """
        Validate a rule. Returns list of error messages (empty = valid).

        Args:
            rule: Rule to validate
            exclude_name: Name to exclude from duplicate check (for updates)

        Returns:
            List of validation error strings
        """
        errors: list[str] = []

        if not rule.name or not rule.name.strip():
            errors.append("Rule name is required")

        if not rule.subject_query and not rule.sender_filter:
            errors.append("At least one of subject_query or sender_filter is required")

        if rule.max_emails < 1:
            errors.append("max_emails must be at least 1")

        if rule.max_emails > 500:
            errors.append("max_emails must not exceed 500")

        # Check duplicate name
        existing_names = [
            r.name for r in self.rules
            if r.name != exclude_name
        ]
        if rule.name in existing_names:
            errors.append(f"Rule name '{rule.name}' already exists")

        return errors
