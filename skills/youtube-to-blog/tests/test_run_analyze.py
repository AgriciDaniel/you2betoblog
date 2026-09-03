"""Tests for run_analyze.py with the analyzer subprocess mocked."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from conftest import load_script, run_main


def fake_analyzer(tmp_path):
    fake = tmp_path / "va"
    (fake / "scripts").mkdir(parents=True)
    (fake / "scripts" / "analyze.py").write_text("", encoding="utf-8")
    return fake


def test_command_and_avt_glob(vault, run_dir, tmp_path, monkeypatch, capsys):
    module = load_script("run_analyze")
    analyzer = fake_analyzer(tmp_path)
    video = tmp_path / "ABC_def-123.mp4"
    video.write_bytes(b"v")
    calls = []

    def fake_run(cmd, stdout=None, stderr=None, text=True):
        calls.append(cmd)
        out = Path(cmd[cmd.index("--out-dir") + 1]) / "avt_outputs" / "abcdef-123"
        (out / "frames").mkdir(parents=True)
        for i in range(2):
            (out / "frames" / f"frame-{i + 1:03d}.jpg").write_bytes(b"")
        (out / "abcdef-123.avt").write_text("AGENTIC-VT 1.0\n", encoding="utf-8")
        return subprocess.CompletedProcess(cmd, 0, str(out / "abcdef-123.avt") + "\n", "")

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    for key in ("GROQ_API_KEY", "OPENAI_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    code, out = run_main("run_analyze", ["--run", str(run_dir), "--video", str(video), "--analyze-dir", str(analyzer)], capsys)
    assert code == 0 and out["ok"] is True and out["frames"] == 2 and out["exit_code"] == 0
    assert out["avt_path"] == str(run_dir / "analysis" / "avt_outputs" / "abcdef-123" / "abcdef-123.avt")
    assert calls == [[sys.executable, str(analyzer / "scripts" / "analyze.py"), str(video), "--out-dir",
                      str(run_dir / "analysis"), "--max-frames", "120", "--no-whisper"]]


def test_analyzer_failure_exit_5(vault, run_dir, tmp_path, monkeypatch, capsys):
    module = load_script("run_analyze")
    analyzer = fake_analyzer(tmp_path)
    video = tmp_path / "v.mp4"
    video.write_bytes(b"v")
    monkeypatch.setattr(module.subprocess, "run", lambda cmd, **k: subprocess.CompletedProcess(cmd, 1, "", ""))
    monkeypatch.setenv("GROQ_API_KEY", "x")
    code, out = run_main("run_analyze", ["--run", str(run_dir), "--video", str(video), "--analyze-dir", str(analyzer), "--force-long"], capsys)
    assert code == 5 and out["ok"] is False and out["avt_path"] is None and out["exit_code"] == 1


def test_missing_analyzer_exit_4(vault, run_dir, tmp_path, monkeypatch, capsys):
    video = tmp_path / "v.mp4"
    video.write_bytes(b"v")
    monkeypatch.setenv("VIDEO_ANALYZER_DIR", str(tmp_path / "nope"))
    code, out = run_main("run_analyze", ["--run", str(run_dir), "--video", str(video)], capsys)
    assert code == 4
