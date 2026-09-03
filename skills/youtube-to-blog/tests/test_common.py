"""Tests for yt2b_common helpers used across the scripts."""

from __future__ import annotations

from pathlib import Path

import pytest

import yt2b_common as common


@pytest.mark.parametrize("url,expected", [
    ("https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=42s", "dQw4w9WgXcQ"),
    ("https://youtu.be/dQw4w9WgXcQ?si=abc", "dQw4w9WgXcQ"),
    ("https://m.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
    ("https://www.youtube.com/shorts/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
    ("https://www.youtube.com/live/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
    ("https://example.com/watch?v=dQw4w9WgXcQ", None),
    ("javascript:alert(1)", None),
    ("https://www.youtube.com/playlist?list=PL123", None),
])
def test_youtube_video_id(url, expected):
    assert common.youtube_video_id(url) == expected


def test_watch_url_never_youtu_be():
    assert common.watch_url("dQw4w9WgXcQ", 95.4) == "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=95s"
    assert "youtu.be" not in common.watch_url("dQw4w9WgXcQ")


def test_slug_and_names():
    assert common.slugify("Claude Code: The BEST tutorial (2026)!") == "claude-code-the-best-tutorial-2026"
    assert common.run_dir_name("A" * 60, "abcdefghijk", "2026-09-03") == "2026-09-03-" + "a" * 40 + "-abcdefghijk"
    assert common.blog_dir_name("My Post", "2026-09-03") == "2026-09-03 my-post"


def test_frontmatter_round_trip(tmp_path):
    fm = {"type": "yt2b-queue", "video_id": "12345678901", "title": "A: B", "tags": ["yt2b", "queue"],
          "priority": 3, "keep": False, "run": "[[02 Videos/x/run|x]]", "empty": ""}
    path = common.write_note(tmp_path / "n.md", fm, "body")
    back, body = common.read_note(path)
    assert back["video_id"] == "12345678901" and isinstance(back["video_id"], str)
    assert back["tags"] == ["yt2b", "queue"] and back["priority"] == 3 and back["keep"] is False
    assert back["run"] == "[[02 Videos/x/run|x]]" and body.strip() == "body"


def test_load_settings_and_vault_root(vault):
    settings = common.load_settings(vault)
    assert settings["author"] == "Test Author" and settings["site_url"] == "https://example.org"
    assert settings["max_video_minutes"] == 90 and settings["keep_video"] is False
    deep = vault / "02 Videos" / "x"
    deep.mkdir(parents=True)
    assert common.find_vault_root(deep) == vault


def test_sections_round_trip():
    body = "intro\n\n## Summary\n\ntext\n\n## Log\n\n- a\n- b\n"
    pre, sections = common.split_sections(body)
    assert pre.strip() == "intro" and [h for h, _ in sections] == ["Summary", "Log"]
    assert common.split_sections(common.join_sections(pre, sections))[1] == sections


def test_key_present_reads_names_only(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("# comment\nGOOGLE_API_KEY=dummy-value\nGROQ_API_KEY=\n", encoding="utf-8")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    assert common.key_present("GOOGLE_API_KEY", env_file) is True
    assert common.key_present("GROQ_API_KEY", env_file) is False
    monkeypatch.setenv("GROQ_API_KEY", "x")
    assert common.key_present("GROQ_API_KEY", env_file) is True


def test_find_analyze_dir_env(tmp_path, monkeypatch):
    fake = tmp_path / "va"
    (fake / "scripts").mkdir(parents=True)
    (fake / "scripts" / "analyze.py").write_text("", encoding="utf-8")
    monkeypatch.setenv("VIDEO_ANALYZER_DIR", str(fake))
    assert common.find_analyze_dir() == fake.resolve()
    monkeypatch.setenv("VIDEO_ANALYZER_DIR", str(tmp_path / "missing"))
    monkeypatch.setenv("HOME", str(tmp_path))
    assert common.find_analyze_dir() is None


def test_time_helpers():
    assert common.seconds_to_mmss(95) == "01:35" and common.mmss_to_seconds("1:02:05") == 3725.0
    assert common.iso_duration(3725) == "PT1H2M5S" and common.upload_date_to_iso("20260903") == "2026-09-03"
    assert "Untrusted" in common.untrusted_notice("transcript")
