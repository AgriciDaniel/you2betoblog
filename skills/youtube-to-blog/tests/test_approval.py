"""Tests for approval.py: create, check, set, expiry, idempotency."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import yt2b_common as common  # noqa: E402

VIDEO_ID = "abc123DEF45"


def run_script(*args):
    proc = subprocess.run([sys.executable, str(SCRIPTS / "approval.py"), *map(str, args)], capture_output=True, text=True)
    lines = [line for line in proc.stdout.strip().splitlines() if line.strip()]
    data = json.loads(lines[-1]) if lines else {}
    return proc.returncode, data, proc.stderr


def make_vault(tmp_path: Path) -> Path:
    vault = tmp_path / "vault"
    (vault / ".obsidian").mkdir(parents=True)
    fm = dict(common.DEFAULT_SETTINGS)
    fm["type"] = "yt2b-settings"
    common.write_note(vault / "00 Home" / "Settings.md", fm, "Settings\n")
    return vault


def make_run(vault: Path) -> Path:
    run = vault / "02 Videos" / f"2026-09-03-sample-{VIDEO_ID}"
    run.mkdir(parents=True)
    common.write_note(run / "run.md", {
        "type": "yt2b-video", "video_id": VIDEO_ID, "title": "Sample", "rights": "own",
        "mode": "companion", "status": "briefed", "tags": ["yt2b", "video"],
    }, "## Summary\n")
    return run


def create(vault: Path, run: Path, tmp_path: Path, **extra):
    req = tmp_path / "request.md"
    req.write_text("Pick the blogs to write.\n", encoding="utf-8")
    args = ["--vault", vault, "create", "--kind", "strategy", "--run", run, "--title", "Strategy for Sample",
            "--request-file", req, "--options", "blog-1=How to X;blog-2=Y vs Z",
            "--questions", "audience=Who is this for?;cta=What should readers do next?"]
    for key, value in extra.items():
        args += [f"--{key.replace('_', '-')}", value]
    return run_script(*args)


def test_create_check_set(tmp_path):
    vault = make_vault(tmp_path)
    run = make_run(vault)
    code, data, err = create(vault, run, tmp_path)
    assert code == 0, err
    assert data["created"] is True and data["options"] == ["blog-1", "blog-2"]
    note = Path(data["note"])
    assert note.name == f"{common.today()}-{VIDEO_ID}-strategy.md"
    assert note.parent == vault / "04 Approvals" / "queue"
    text = note.read_text(encoding="utf-8")
    assert "- [ ] blog-1: How to X" in text and "- [ ] blog-2: Y vs Z" in text
    assert "- **audience**: Who is this for?" in text and "answer:" in text
    assert "## Request" in text and "## Decision" in text
    fm, _ = common.read_note(note)
    assert fm["type"] == "yt2b-approval" and fm["status"] == "requested" and fm["kind"] == "strategy"
    assert fm["tags"] == ["yt2b", "format/approval", "approval/strategy", "decision/requested"] and fm["selected"] == []
    assert fm["run"].startswith("[[02 Videos/")

    code, data, _ = run_script("check", note)
    assert code == 0
    assert data["status"] == "requested" and data["selected"] == [] and data["approved"] is False
    assert data["expired"] is False and data["answers"] == {"audience": "", "cta": ""}

    code, again, _ = create(vault, run, tmp_path)
    assert code == 0 and again["created"] is False and Path(again["note"]) == note

    text = note.read_text(encoding="utf-8")
    text = text.replace("- [ ] blog-1: How to X", "- [x] blog-1: How to X")
    text = text.replace("- **audience**: Who is this for?\n  answer:", "- **audience**: Who is this for?\n  answer: Solo developers")
    note.write_text(text, encoding="utf-8")
    code, data, _ = run_script("check", note)
    assert data["selected"] == ["blog-1"] and data["answers"]["audience"] == "Solo developers"
    assert data["approved"] is False, "a ticked box alone is not approval"
    fm, _ = common.read_note(note)
    assert fm["selected"] == ["blog-1"], "check syncs the selected list into the properties"
    run_fm, run_body = common.read_note(run / "run.md")
    assert run_fm["approvals"] and "## Approvals" in run_body

    code, data, err = run_script("set", note, "--status", "approved", "--decision", "Go with blog-1.")
    assert code == 0, err
    assert data["status"] == "approved" and data["selected"] == ["blog-1"] and data["decided"]
    code, data, _ = run_script("check", note)
    assert data["approved"] is True and data["status"] == "approved" and data["selected"] == ["blog-1"]
    fm, body = common.read_note(note)
    assert fm["decided"] and "Go with blog-1." in body
    assert fm["tags"][-1] == "decision/approved"
    code, data, _ = run_script("set", note, "--status", "approved", "--decision", "Go with blog-1.")
    assert body.count("Go with blog-1.") == 1 and common.read_note(note)[1].count("Go with blog-1.") == 1


def test_expiry_and_select(tmp_path):
    vault = make_vault(tmp_path)
    run = make_run(vault)
    code, data, err = create(vault, run, tmp_path, expires_hours="-1")
    assert code == 0, err
    note = Path(data["note"])
    code, data, _ = run_script("check", note)
    assert data["expired"] is True and data["status"] == "expired" and data["approved"] is False
    fm, _ = common.read_note(note)
    assert fm["status"] == "expired"
    code, data, err = run_script("set", note, "--status", "approved", "--selected", "blog-2")
    assert code == 0, err
    assert data["selected"] == ["blog-2"]
    assert "- [x] blog-2: Y vs Z" in note.read_text(encoding="utf-8")
    code, data, _ = run_script("check", note)
    assert data["approved"] is True and data["selected"] == ["blog-2"]


def test_invalid_inputs(tmp_path):
    vault = make_vault(tmp_path)
    run = make_run(vault)
    req = tmp_path / "request.md"
    req.write_text("x\n", encoding="utf-8")
    code, data, _ = run_script("--vault", vault, "create", "--kind", "strategy", "--run", run, "--title", "T",
                               "--request-file", req, "--options", "not-a-pair")
    assert code == 2 and data["ok"] is False
    code, data, _ = run_script("check", tmp_path / "missing.md")
    assert code == 2
    code, data, _ = create(vault, run, tmp_path)
    note = Path(data["note"])
    code, data, _ = run_script("set", note, "--status", "approved", "--select", "blog-9")
    assert code == 2 and "unknown option" in data["error"]


def test_image_and_outline_names_carry_the_blog_slug(tmp_path):
    vault = make_vault(tmp_path)
    run = make_run(vault)
    blog = vault / "03 Blogs" / "2026-09-03 my-post"
    blog.mkdir(parents=True)
    common.write_note(blog / "my-post.md", {"title": "My post", "slug": "my-post", "type": "yt2b-blog"}, "<!-- draft pending -->\n")
    req = tmp_path / "request.md"
    req.write_text("Generate a hero image.\n", encoding="utf-8")
    code, data, err = run_script("--vault", vault, "create", "--kind", "image", "--run", run, "--blog", blog,
                                 "--title", "Hero image", "--request-file", req, "--options", "hero=Generate the hero",
                                 "--cost-estimate", "about 0.04 USD")
    assert code == 0, err
    note = Path(data["note"])
    assert note.name == f"{common.today()}-{VIDEO_ID}-image-my-post.md"
    fm, _ = common.read_note(note)
    assert fm["cost_estimate"] == "about 0.04 USD" and fm["blog"].startswith("[[03 Blogs/")
    code, data, _ = run_script("--vault", vault, "create", "--kind", "outline", "--run", run, "--blog", blog,
                               "--title", "Outline", "--request-file", req, "--options", "outline=Approve the outline")
    assert Path(data["note"]).name == f"{common.today()}-{VIDEO_ID}-outline-my-post.md"
    code, data, _ = run_script("--vault", vault, "create", "--kind", "image", "--run", run, "--title", "x", "--request-file", req)
    assert code == 2, "image approvals need --blog"
    code, data, _ = run_script("set", note, "--status", "approved", "--selected", "hero", "--selected", "hero")
    assert code == 0 and data["selected"] == ["hero"]
