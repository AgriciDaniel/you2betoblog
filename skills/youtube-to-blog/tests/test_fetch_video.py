"""Tests for fetch_video.py with subprocess and network fully mocked."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

import yt2b_common as common
from conftest import load_script, run_main

URL = "https://www.youtube.com/watch?v=abcdefghijk"


class FakeYtDlp:
    """Records yt-dlp calls and fakes their side effects."""

    def __init__(self, info: dict, manual_subs: bool = True, auto_subs: bool = True, meta_rc: int = 0, sub_names=None):
        self.info = info
        self.manual_subs, self.auto_subs, self.meta_rc = manual_subs, auto_subs, meta_rc
        self.sub_names = sub_names or ["captions.en.vtt"]
        self.calls: list[list[str]] = []

    def __call__(self, args, capture_output=True, text=True, timeout=None):
        assert isinstance(args, list) and args[0] == "yt-dlp" and timeout
        self.calls.append(args)
        if "--dump-json" in args:
            if self.meta_rc:
                return subprocess.CompletedProcess(args, self.meta_rc, "", "ERROR: Private video. Sign in if you've been granted access")
            return subprocess.CompletedProcess(args, 0, json.dumps(self.info) + "\n", "")
        out_dir = Path(args[args.index("-o") + 1]).parent
        if "--write-subs" in args:
            if self.manual_subs:
                (out_dir / "captions.en.vtt").write_text("WEBVTT\n\n00:00:00.000 --> 00:00:01.000\nhi\n", encoding="utf-8")
        elif "--write-auto-subs" in args:
            if self.auto_subs:
                for name in self.sub_names:
                    (out_dir / name).write_text("WEBVTT\n\n00:00:00.000 --> 00:00:01.000\nauto\n", encoding="utf-8")
        elif "-f" in args:
            (out_dir / "abcdefghijk.mp4").write_bytes(b"video")
        return subprocess.CompletedProcess(args, 0, "", "")


def raw_info(info: dict) -> dict:
    """Shape yt-dlp --dump-json returns (bigger than the trimmed file)."""
    meta = dict(info)
    meta["formats"] = [{"format_id": "137"}] * 5
    meta["requested_formats"] = [{"filesize": 100_000_000}, {"filesize_approx": 5_000_000}]
    meta["subtitles"] = {"en": [{"ext": "vtt"}], "de": [{"ext": "vtt"}]}
    meta["automatic_captions"] = {"en": [{"ext": "vtt"}], "en-orig": [{"ext": "vtt"}], "fr": []}
    meta["thumbnails"] = [{"url": f"https://i.ytimg.com/vi/x/{i}.jpg", "width": w, "height": w * 9 // 16, "id": str(i)}
                          for i, w in enumerate((120, 320, 480, 640, 1280, 1920))]
    meta["timestamp"] = 1756713600
    meta["uploader_url"] = "https://www.youtube.com/@testchannel"
    return meta


@pytest.fixture
def fetch(monkeypatch):
    module = load_script("fetch_video")
    downloads: list[str] = []

    def fake_get(url, dest, cap=0, timeout=0):
        assert url.startswith("https://")
        downloads.append(url)
        Path(dest).write_bytes(b"jpg")

    monkeypatch.setattr(module, "http_get", fake_get)
    module._downloads = downloads
    return module


def test_invalid_url_exit_2(vault, fetch, monkeypatch, capsys):
    fake = FakeYtDlp({})
    monkeypatch.setattr(fetch.subprocess, "run", fake)
    code, out = run_main("fetch_video", ["--vault", str(vault), "https://example.com/watch?v=abcdefghijk"], capsys)
    assert code == 2 and out["ok"] is False and fake.calls == []


def test_missing_ytdlp_exit_4(vault, fetch, monkeypatch, capsys):
    def missing(*a, **k):
        raise FileNotFoundError("yt-dlp")
    monkeypatch.setattr(fetch.subprocess, "run", missing)
    code, out = run_main("fetch_video", ["--vault", str(vault), URL], capsys)
    assert code == 4


def test_metadata_failure_exit_5(vault, fetch, info, monkeypatch, capsys):
    monkeypatch.setattr(fetch.subprocess, "run", FakeYtDlp(raw_info(info), meta_rc=1))
    code, out = run_main("fetch_video", ["--vault", str(vault), URL], capsys)
    assert code == 5 and "sign-in" in out["error"]


def test_duration_guard_exit_3_and_force_long(vault, fetch, info, monkeypatch, capsys):
    meta = raw_info(info)
    meta["duration"] = 91 * 60
    monkeypatch.setattr(fetch.subprocess, "run", FakeYtDlp(meta))
    code, out = run_main("fetch_video", ["--vault", str(vault), URL], capsys)
    assert code == 3 and "--force-long" in out["error"]
    code, out = run_main("fetch_video", ["--vault", str(vault), URL, "--force-long"], capsys)
    assert code == 0


def test_size_guard_exit_3(vault, fetch, info, monkeypatch, capsys):
    meta = raw_info(info)
    meta["requested_formats"] = [{"filesize": 3 * 1024 ** 3}]
    monkeypatch.setattr(fetch.subprocess, "run", FakeYtDlp(meta))
    code, out = run_main("fetch_video", ["--vault", str(vault), URL], capsys)
    assert code == 3 and "2 GB" in out["error"]


def test_happy_path_auto_captions_and_idempotent(vault, fetch, info, monkeypatch, capsys):
    fake = FakeYtDlp(raw_info(info), manual_subs=False, sub_names=["captions.en.vtt", "captions.en-orig.vtt"])
    monkeypatch.setattr(fetch.subprocess, "run", fake)
    _, queued = run_main("queue", ["--vault", str(vault), "add", "https://youtu.be/abcdefghijk"], capsys)
    code, out = run_main("fetch_video", ["--vault", str(vault), URL, "--rights", "own", "--queue", queued["path"]], capsys)
    assert code == 0 and out["ok"] is True
    run = Path(out["run_dir"])
    assert run.name == f"{common.today()}-test-video-claude-code-setup-abcdefghijk" and run.parent == vault / "02 Videos"
    trimmed = json.loads((run / "source" / "video.info.json").read_text(encoding="utf-8"))
    assert "formats" not in trimmed and "requested_formats" not in trimmed
    assert trimmed["subtitles"] == ["de", "en"] and trimmed["automatic_captions"] == ["en", "en-orig", "fr"]
    assert [t["width"] for t in trimmed["thumbnails"]] == [1920, 1280, 640]
    assert set(trimmed["thumbnails"][0]) == {"url", "width", "height"}
    assert trimmed["timestamp"] == 1756713600 and trimmed["uploader_url"] == "https://www.youtube.com/@testchannel"
    assert out["captions_source"] == "auto" and Path(out["captions_path"]).name == "captions.en.vtt"
    assert not (run / "source" / "captions.en-orig.vtt").exists()
    assert Path(out["thumbnail_path"]).is_file() and fetch._downloads == ["https://i.ytimg.com/vi/x/5.jpg"]
    assert Path(out["video_path"]) == vault / ".cache" / "video" / "abcdefghijk.mp4"
    fm, body = common.read_note(run / "run.md")
    assert fm["type"] == "yt2b-video" and fm["status"] == "fetched" and fm["captions"] == "auto" and fm["rights"] == "own"
    assert fm["title"] == info["title"] and fm["duration_s"] == 32 and fm["published"] == "2026-09-01"
    assert fm["queue"].startswith("[[01 Queue/") and "fetched: captions=auto" in body
    qfm, _ = common.read_note(queued["path"])
    assert qfm["status"] == "running" and qfm["run"] == f"[[02 Videos/{run.name}/run|{run.name}]]"
    flags = [c[1] for c in fake.calls]
    assert flags == ["--dump-json", "--write-subs", "--write-auto-subs", "-f"]
    assert "--sub-langs" in fake.calls[1] and fake.calls[1][fake.calls[1].index("--sub-langs") + 1] == "en.*,en"
    # second run: same folder, no new caption or video download
    code, again = run_main("fetch_video", ["--vault", str(vault), URL], capsys)
    assert code == 0 and again["run_dir"] == out["run_dir"] and again["captions_source"] == "auto"
    assert [c[1] for c in fake.calls[4:]] == ["--dump-json"]
    assert len(list((vault / "02 Videos").iterdir())) == 1
    assert body.count("fetched:") == 1


def test_manual_caption_variant_is_normalised(vault, fetch, info, monkeypatch, capsys):
    fake = FakeYtDlp(raw_info(info), manual_subs=False, sub_names=["captions.en-US.vtt"])
    monkeypatch.setattr(fetch.subprocess, "run", fake)
    code, out = run_main("fetch_video", ["--vault", str(vault), URL], capsys)
    assert code == 0 and Path(out["captions_path"]).name == "captions.en.vtt"
    assert out["captions_source"] == "auto"
    fake_manual = FakeYtDlp(raw_info(info), manual_subs=True)
    monkeypatch.setattr(fetch.subprocess, "run", fake_manual)
    (vault / "02 Videos").rename(vault / "gone")
    code, out = run_main("fetch_video", ["--vault", str(vault), URL], capsys)
    assert out["captions_source"] == "manual" and [c[1] for c in fake_manual.calls] == ["--dump-json", "--write-subs"]


def test_no_captions_warns(vault, fetch, info, monkeypatch, capsys):
    monkeypatch.setattr(fetch.subprocess, "run", FakeYtDlp(raw_info(info), manual_subs=False, auto_subs=False))
    code, out = run_main("fetch_video", ["--vault", str(vault), URL], capsys)
    assert code == 0 and out["captions_source"] == "none" and out["captions_path"] is None
    assert any("Whisper" in w for w in out["warnings"])
