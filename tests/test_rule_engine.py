"""Unit tests for RuleEngine."""

import json
import pytest

from src.models import EmailRule, InvalidRuleError
from src.rule_engine import RuleEngine


class TestLoadRules:
    def test_creates_default_when_no_file(self, tmp_path):
        engine = RuleEngine(tmp_path / "rules.json")
        rules = engine.load_rules()
        assert len(rules) == 1
        assert rules[0].name == "Viettel Post Invoice"
        assert (tmp_path / "rules.json").exists()

    def test_loads_from_existing_file(self, tmp_path):
        data = [
            {"name": "Rule A", "subject_query": "test A"},
            {"name": "Rule B", "subject_query": "test B", "enabled": False},
        ]
        (tmp_path / "rules.json").write_text(json.dumps(data), encoding="utf-8")

        engine = RuleEngine(tmp_path / "rules.json")
        rules = engine.load_rules()
        assert len(rules) == 2
        assert rules[0].name == "Rule A"
        assert rules[1].enabled is False

    def test_invalid_json_raises(self, tmp_path):
        (tmp_path / "rules.json").write_text("not json", encoding="utf-8")
        engine = RuleEngine(tmp_path / "rules.json")
        with pytest.raises(Exception):
            engine.load_rules()


class TestSaveRules:
    def test_saves_to_file(self, tmp_path):
        engine = RuleEngine(tmp_path / "rules.json")
        engine.rules = [EmailRule(name="Test", subject_query="hello")]
        engine.save_rules()

        with open(tmp_path / "rules.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        assert len(data) == 1
        assert data[0]["name"] == "Test"


class TestAddRule:
    def test_add_valid_rule(self, tmp_path):
        engine = RuleEngine(tmp_path / "rules.json")
        engine.load_rules()
        new_rule = EmailRule(name="New Rule", subject_query="new query")
        engine.add_rule(new_rule)
        assert len(engine.rules) == 2

    def test_add_duplicate_name_raises(self, tmp_path):
        engine = RuleEngine(tmp_path / "rules.json")
        engine.load_rules()
        dup = EmailRule(name="Viettel Post Invoice", subject_query="dup")
        with pytest.raises(InvalidRuleError):
            engine.add_rule(dup)

    def test_add_empty_name_raises(self, tmp_path):
        engine = RuleEngine(tmp_path / "rules.json")
        engine.load_rules()
        bad = EmailRule(name="", subject_query="test")
        with pytest.raises(InvalidRuleError):
            engine.add_rule(bad)


class TestRemoveRule:
    def test_remove_existing(self, tmp_path):
        engine = RuleEngine(tmp_path / "rules.json")
        engine.load_rules()
        result = engine.remove_rule("Viettel Post Invoice")
        assert result is True
        assert len(engine.rules) == 0

    def test_remove_nonexistent(self, tmp_path):
        engine = RuleEngine(tmp_path / "rules.json")
        engine.load_rules()
        result = engine.remove_rule("Nonexistent")
        assert result is False


class TestGetEnabledRules:
    def test_filters_disabled(self, tmp_path):
        engine = RuleEngine(tmp_path / "rules.json")
        engine.rules = [
            EmailRule(name="A", enabled=True, subject_query="a"),
            EmailRule(name="B", enabled=False, subject_query="b"),
            EmailRule(name="C", enabled=True, subject_query="c"),
        ]
        enabled = engine.get_enabled_rules()
        assert len(enabled) == 2
        names = [r.name for r in enabled]
        assert "A" in names
        assert "C" in names
        assert "B" not in names


class TestToGmailQuery:
    def test_full_query(self):
        rule = EmailRule(
            name="Test",
            subject_query="Viettel",
            sender_filter="test@example.com",
            label_filter="INBOX",
        )
        query = rule.to_gmail_query()
        assert 'subject:"Viettel"' in query
        assert "from:test@example.com" in query
        assert "in:inbox" in query

    def test_query_without_has_attachment(self):
        """to_gmail_query no longer adds has:attachment (handlers decide)."""
        rule = EmailRule(
            name="Test",
            subject_query="Hello",
            download_attachments=True,
            download_bang_ke=False,
        )
        query = rule.to_gmail_query()
        assert "has:attachment" not in query
        assert 'subject:"Hello"' in query

    def test_no_has_attachment_when_both(self):
        """When both attachments and bang_ke are enabled, omit has:attachment."""
        rule = EmailRule(name="Test", subject_query="Hello")
        query = rule.to_gmail_query()
        assert 'subject:"Hello"' in query
        assert "has:attachment" not in query


class TestValidateRule:
    def test_valid_rule(self, tmp_path):
        engine = RuleEngine(tmp_path / "rules.json")
        engine.rules = []
        rule = EmailRule(name="Good", subject_query="test")
        errors = engine.validate_rule(rule)
        assert errors == []

    def test_no_query_and_no_sender(self, tmp_path):
        engine = RuleEngine(tmp_path / "rules.json")
        rule = EmailRule(name="Bad")
        errors = engine.validate_rule(rule)
        assert len(errors) > 0

    def test_max_emails_too_high(self, tmp_path):
        engine = RuleEngine(tmp_path / "rules.json")
        rule = EmailRule(name="Big", subject_query="x", max_emails=999)
        errors = engine.validate_rule(rule)
        assert any("500" in e for e in errors)
