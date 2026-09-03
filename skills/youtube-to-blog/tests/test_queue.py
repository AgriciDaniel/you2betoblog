"""Tests for queue.py: add, duplicates, list, next, set, import-inbox."""

from __future__ import annotations

import yt2b_common as common
from conftest import run_main

URL = "https://www.youtube.com/watch?v=abcdefghijk"


def test_add_creates_schema_note(vault, capsys):
    code, out = run_main("queue", ["--vault", str(vault), "add", URL, "--rights", "own", "--note", "hello"], capsys)
    assert code == 0 and out["created"] is True
    path = vault / "01 Queue" / f"{common.today()}-abcdefghijk.md"
    assert path.is_file()
    fm, body = common.read_note(path)
    assert fm["type"] == "yt2b-queue" and fm["video_id"] == "abcdefghijk" and fm["video_url"] == URL
    assert fm["rights"] == "own" and fm["mode"] == "companion" and fm["priority"] == 3
    assert fm["status"] == "queued" and fm["run"] == "" and fm["note"] == "hello"
    assert fm["source_notes"] == [] and fm["discovered_via"] == "cli"
    assert fm["tags"] == ["yt2b", "stage/queue", "format/video", "source/youtube", "rights/own"]
    assert f"[Watch on YouTube]({URL})" in body


def test_add_same_id_is_not_duplicated(vault, capsys):
    run_main("queue", ["--vault", str(vault), "add", URL], capsys)
    code, out = run_main("queue", ["--vault", str(vault), "add", "https://youtu.be/abcdefghijk"], capsys)
    assert code == 0 and out["created"] is False
    assert len(list((vault / "01 Queue").glob("*-abcdefghijk.md"))) == 1


def test_add_invalid_url_exit_2(vault, capsys):
    code, out = run_main("queue", ["--vault", str(vault), "add", "https://example.com/x"], capsys)
    assert code == 2 and out["ok"] is False


def test_list_and_next_priority(vault, capsys):
    run_main("queue", ["--vault", str(vault), "add", URL, "--priority", "3"], capsys)
    run_main("queue", ["--vault", str(vault), "add", "https://www.youtube.com/watch?v=bbbbbbbbbbb", "--priority", "1"], capsys)
    code, out = run_main("queue", ["--vault", str(vault), "list"], capsys)
    assert code == 0 and out["count"] == 2 and {i["video_id"] for i in out["items"]} == {"abcdefghijk", "bbbbbbbbbbb"}
    code, out = run_main("queue", ["--vault", str(vault), "next"], capsys)
    assert code == 0 and out["empty"] is False and out["note"]["video_id"] == "bbbbbbbbbbb"
    run_main("queue", ["--vault", str(vault), "set", out["path"], "--status", "done"], capsys)
    code, out = run_main("queue", ["--vault", str(vault), "next"], capsys)
    assert out["note"]["video_id"] == "abcdefghijk"
    code, out = run_main("queue", ["--vault", str(vault), "list", "--status", "done"], capsys)
    assert out["count"] == 1 and out["items"][0]["video_id"] == "bbbbbbbbbbb"


def test_next_empty(vault, capsys):
    code, out = run_main("queue", ["--vault", str(vault), "next"], capsys)
    assert code == 0 and out["empty"] is True and out["note"] is None


def test_set_status_run_and_error(vault, capsys):
    _, added = run_main("queue", ["--vault", str(vault), "add", URL], capsys)
    run = vault / "02 Videos" / "2026-09-03-test-abcdefghijk"
    run.mkdir(parents=True)
    code, out = run_main("queue", ["--vault", str(vault), "set", added["path"], "--status", "running", "--run", str(run)], capsys)
    assert code == 0 and out["status"] == "running"
    assert out["run"] == "[[02 Videos/2026-09-03-test-abcdefghijk/run|2026-09-03-test-abcdefghijk]]"
    for _ in range(2):
        run_main("queue", ["--vault", str(vault), "set", "01 Queue/" + added["name"] + ".md", "--status", "failed", "--error", "boom"], capsys)
    fm, body = common.read_note(added["path"])
    assert fm["status"] == "failed" and body.count("> [!failure] boom") == 1
    assert fm["tags"] == ["yt2b", "stage/blocked", "format/video", "source/youtube"]


def test_import_inbox_rewrites_lines(vault, capsys):
    code, out = run_main("queue", ["--vault", str(vault), "import-inbox"], capsys)
    assert code == 0 and len(out["created"]) == 2 and out["existing"] == []
    assert any("not a YouTube" in s["reason"] for s in out["skipped"])
    text = (vault / common.HOME_NOTE).read_text(encoding="utf-8")
    today = common.today()
    assert f"- [x] {URL} -> [[01 Queue/{today}-abcdefghijk|queued]]" in text
    assert f"> - [x] https://www.youtube.com/watch?v=bbbbbbbbbbb -> [[01 Queue/{today}-bbbbbbbbbbb|queued]]" in text
    assert "https://www.youtube.com/watch?v=zzzzzzzzzzz" in text and "zzzzzzzzzzz|queued" not in text
    assert "- [x] https://www.youtube.com/watch?v=alreadydone -> [[01 Queue/2026-01-01-alreadydone|queued]]" in text
    assert "- [ ] https://example.com/not-youtube" in text
    fm, _ = common.read_note(vault / "01 Queue" / f"{today}-abcdefghijk.md")
    assert fm["rights"] == "own" and fm["mode"] == "companion" and fm["note"] == "first video"
    fm, _ = common.read_note(vault / "01 Queue" / f"{today}-bbbbbbbbbbb.md")
    assert fm["rights"] == "third-party" and fm["mode"] == "expand" and fm["note"] == "callout item"
    code, out = run_main("queue", ["--vault", str(vault), "import-inbox"], capsys)
    assert out["created"] == [] and out["existing"] == []
    assert (vault / common.HOME_NOTE).read_text(encoding="utf-8") == text
