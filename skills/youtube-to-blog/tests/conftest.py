"""Shared fixtures: a minimal vault in tmp_path, a run folder, loaded script modules."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
sys.path.insert(0, str(SCRIPTS))
import yt2b_common as common  # noqa: E402

# Resolve the analyzer before any HOME monkeypatching (tests skip without it).
REAL_ANALYZE_DIR = common.find_analyze_dir() or next(
    (p for p in (Path.home() / "Desktop/Skills/Public/video-analyzer",) if (p / "scripts" / "avt.py").is_file()), None)

_MODULES: dict[str, object] = {}


def load_script(name: str):
    """Import a script by file path (queue.py shadows the stdlib queue module)."""
    if name not in _MODULES:
        _MODULES[name] = common.load_module(SCRIPTS / f"{name}.py", f"yt2b_test_{name}")
    return _MODULES[name]


SETTINGS = {
    "type": "yt2b-settings", "author": "Test Author", "site_url": "https://brandsite.dev", "language": "en",
    "default_rights": "ask", "default_mode": "companion", "max_blogs_per_video": 3, "frame_width": 1600,
    "max_frames_own": 8, "max_frames_third_party": 4, "keep_video": False, "pause_for_outline": True,
    "max_video_minutes": 90, "visuals": "frames+charts",
}

HOME_MD = """# Home

## Pipeline

- [ ] not an inbox line https://www.youtube.com/watch?v=zzzzzzzzzzz

## Inbox

- [ ] https://www.youtube.com/watch?v=abcdefghijk own companion first video
- [x] https://www.youtube.com/watch?v=alreadydone -> [[01 Queue/2026-01-01-alreadydone|queued]]
- [ ] https://example.com/not-youtube
> [!agent-command] Inbox
> - [ ] https://youtu.be/bbbbbbbbbbb third-party expand callout item

## After
"""


@pytest.fixture
def vault(tmp_path, monkeypatch):
    root = tmp_path / "vault"
    (root / ".obsidian").mkdir(parents=True)
    common.write_note(root / common.SETTINGS_NOTE, SETTINGS, "Settings for tests.\n")
    (root / common.HOME_NOTE).write_text(HOME_MD, encoding="utf-8")
    (root / "01 Queue").mkdir()
    (root / "01 Queue" / "README.md").write_text("# Queue\n", encoding="utf-8")
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.chdir(root)
    return root


@pytest.fixture
def info():
    return json.loads((FIXTURES / "sample.info.json").read_text(encoding="utf-8"))


@pytest.fixture
def run_dir(vault, info):
    run = vault / "02 Videos" / common.run_dir_name(info["title"], info["id"])
    (run / "source").mkdir(parents=True)
    common.json_dump(run / "source" / "video.info.json", info)
    return run


@pytest.fixture
def analyze_dir():
    if REAL_ANALYZE_DIR is None:
        pytest.skip("video-analyzer checkout not available")
    return REAL_ANALYZE_DIR


def place_avt(run: Path, content: str, slug: str = "abcdefghijk", frames: int = 3) -> Path:
    """Write an .avt plus empty frame files the way analyze.py lays them out."""
    out = run / "analysis" / "avt_outputs" / slug
    (out / "frames").mkdir(parents=True, exist_ok=True)
    for i in range(frames):
        (out / "frames" / f"frame-{i + 1:03d}.jpg").write_bytes(b"")
    path = out / f"{slug}.avt"
    path.write_text(content, encoding="utf-8")
    return path


def run_main(name: str, argv: list[str], capsys) -> tuple[int, dict]:
    """Run a script's main() in-process and parse its single JSON line."""
    code = load_script(name).main(argv)
    out = capsys.readouterr().out.strip().splitlines()
    assert len(out) == 1, f"expected exactly one JSON line, got {out!r}"
    return code, json.loads(out[0])


def copy_fixture(name: str, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(FIXTURES / name, dest)
    return dest
