"""Offline checks for the pinned Obsidian plugin installer."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import install_plugins

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "skills" / "youtube-to-blog" / "scripts" / "install_plugins.py"


def test_plan_is_complete_and_read_only():
    proc = subprocess.run([sys.executable, str(SCRIPT), "--vault", str(ROOT), "plan"], capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert data["ok"] is True and data["mode"] == "plan"
    assert [item["id"] for item in data["plugins"]] == list(install_plugins.ALL)
    assert {item["id"] for item in data["plugins"] if item["patched"]} == set(install_plugins.PATCHED)


def test_local_home_install_and_existing_verification(tmp_path):
    vault = tmp_path / "vault"
    (vault / ".obsidian").mkdir(parents=True)
    source = ROOT / "plugins" / install_plugins.LOCAL
    entry = install_plugins.load_lock(ROOT)[install_plugins.LOCAL]
    result = install_plugins.install_one(vault, source, entry, replace=False)
    assert result["status"] == "installed"
    again = install_plugins.install_one(vault, source, entry, replace=False)
    assert again["status"] == "already-current"
    install_plugins.verify_files(vault / ".obsidian" / "plugins" / install_plugins.LOCAL, entry)


def test_rss_default_data_is_pinned_and_safe():
    entry = install_plugins.load_lock(ROOT)["rss-dashboard"]
    path = install_plugins.verified_rss_default(ROOT, entry)
    assert path.name == "rss-dashboard-data.json"
    assert install_plugins.rss_data_is_safe(path)
