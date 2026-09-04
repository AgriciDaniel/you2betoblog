"""Tests for release projection checks without exposing matched values."""

from __future__ import annotations

import release_check
import pytest


@pytest.mark.parametrize("prefix,suffix,kind", [
    ("github_pat_", "A" * 50, "github-token"),
    ("ghs_", "A" * 30, "github-token"),
    ("AKIA", "A" * 16, "aws-access-key"),
    ("xoxb-", "1" * 30, "slack-token"),
    ("gsk_", "A" * 40, "groq-key"),
    ("postgres://", "user:password" + "@" + "db.example.invalid", "credential-url"),
])
def test_additional_credentials_are_redacted(tmp_path, prefix, suffix, kind):
    note = tmp_path / "config.txt"
    value = prefix + suffix
    note.write_text(value)
    findings = release_check.scan_sensitive(tmp_path, [note])
    assert any(finding["kind"] == kind for finding in findings)
    assert value not in str(findings)


def test_sensitive_scan_reports_location_and_kind_only(tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    note = vault / "bad.txt"
    secret = "ghp_" + "A" * 30
    note.write_text(f"token={secret}\n", encoding="utf-8")
    findings = release_check.scan_sensitive(vault, [note])
    assert findings == [{"file": "bad.txt", "line": 1, "kind": "github-token"}]
    assert secret not in str(findings)


def test_json_and_symlink_checks(tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    good = vault / "good.json"
    bad = vault / "bad.json"
    good.write_text("{}\n", encoding="utf-8")
    bad.write_text("{\n", encoding="utf-8")
    assert release_check.check_json(vault, [good]) == []
    assert release_check.check_json(vault, [bad]) == ["bad.json: JSONDecodeError"]
    outside = tmp_path / "outside.txt"
    outside.write_text("x", encoding="utf-8")
    link = vault / "outside-link"
    link.symlink_to(outside)
    assert release_check.check_symlinks(vault, [link]) == ["outside-link"]
