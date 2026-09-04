"""Integration tests for the local Gate 6 appended by deliver.py."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import yt2b_common as common
from test_contract import SLUG, make_world

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "deliver.py"


def fake_preflight(folder: Path) -> None:
    folder.mkdir()
    script = folder / "blog_preflight.py"
    script.write_text("""import json, pathlib, sys
draft = pathlib.Path(sys.argv[sys.argv.index('--draft') + 1])
report = {'blocked': False, 'gates': [
    {'gate': n, 'name': f'Gate {n}', 'passed': True, 'violations': [], 'warnings': []}
    for n in range(1, 6)
]}
(draft / 'preflight-report.json').write_text(json.dumps(report), encoding='utf-8')
""", encoding="utf-8")


def run_gates(vault: Path, run: Path, blog: Path, scripts: Path) -> tuple[int, dict]:
    env = dict(os.environ)
    env["CLAUDE_BLOG_SCRIPTS_DIR"] = str(scripts)
    proc = subprocess.run([
        sys.executable, str(SCRIPT), "--vault", str(vault), "--run", str(run),
        "--blog", str(blog), "gates",
    ], capture_output=True, text=True, env=env)
    return proc.returncode, json.loads(proc.stdout.strip().splitlines()[-1])


def test_deliver_appends_gate6_and_blocks_policy_drift(tmp_path):
    vault, run, blog = make_world(tmp_path)
    scripts = tmp_path / "fake-blog-scripts"
    fake_preflight(scripts)
    code, data = run_gates(vault, run, blog, scripts)
    assert code == 0 and data["ok"] is True
    report = common.json_load(blog / "preflight-report.json", {})
    gate6 = next(gate for gate in report["gates"] if gate["gate"] == 6)
    assert gate6["passed"] is True and gate6["post_sha256"] and gate6["review_sha256"]

    post = blog / f"{SLUG}.md"
    fm, body = common.read_note(post)
    fm["canonical"] = "https://example.com/not-ready"
    common.write_note(post, fm, body)
    code, data = run_gates(vault, run, blog, scripts)
    assert code == 1 and data["blocked"] is True
    assert any(item["gate"] == 6 for item in data["failed_gates"])
