#!/usr/bin/env python3
"""Run the claude-blog delivery steps for one blog folder through one command.

Subcommands:
  render   layout_convert -> blog_render -> finalize_html (idempotent)
  nonce    blog_preflight --init-review-nonce (prints the nonce in the JSON)
  gates    blog_preflight --strict [--repair-attempt] and a compact diagnostic

The claude-blog scripts are resolved from CLAUDE_BLOG_SCRIPTS_DIR or
$HOME/.claude/scripts. Nothing here talks to the network or prints secrets.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import yt2b_common as common  # noqa: E402

HERO_SUFFIXES = (".png", ".jpg", ".jpeg", ".webp")


def blog_scripts_dir() -> Path:
    env = os.environ.get("CLAUDE_BLOG_SCRIPTS_DIR")
    base = Path(env).expanduser() if env else Path.home() / ".claude" / "scripts"
    if not base.is_absolute():
        raise SystemExit("CLAUDE_BLOG_SCRIPTS_DIR must be absolute")
    return base


def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    print("+ " + " ".join(f'"{c}"' if " " in c else c for c in cmd), file=sys.stderr)
    return subprocess.run(cmd, cwd=str(cwd) if cwd else None, capture_output=True, text=True)


def last_json(text: str):
    for line in reversed(text.strip().splitlines()):
        line = line.strip()
        if line.startswith("{") and line.endswith("}"):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue
    return None


def find_slug(blog: Path) -> str:
    mds = [p for p in blog.glob("*.md") if p.name != "review.md"]
    if len(mds) != 1:
        raise SystemExit(f"expected exactly one post markdown in {blog}, found {len(mds)}")
    return mds[0].stem


def find_hero(blog: Path, wanted: str | None) -> str:
    if wanted:
        return wanted
    for p in sorted(blog.glob("hero.*")):
        if p.suffix.lower() in HERO_SUFFIXES and not p.is_symlink():
            return p.name
    raise SystemExit("no hero.<png|jpg|jpeg|webp> in the blog folder; run hires_frames.py or generate_hero.py first")


def cmd_render(args) -> int:
    vault = Path(args.vault).resolve()
    blog = Path(args.blog).resolve()
    run_dir = Path(args.run).resolve()
    scripts = Path(__file__).resolve().parent
    blog_scripts = blog_scripts_dir()
    slug = find_slug(blog)
    hero = find_hero(blog, args.hero)
    render_dir = blog / ".render"
    common.ensure_dir(render_dir)
    result = {"slug": slug, "hero": hero, "steps": {}}

    p = run([sys.executable, str(scripts / "layout_convert.py"), "--md", str(blog / f"{slug}.md"),
             "--out", str(render_dir / f"{slug}.md")])
    sys.stderr.write(p.stderr)
    result["steps"]["layout_convert"] = {"exit_code": p.returncode, "json": last_json(p.stdout)}
    if p.returncode != 0:
        common.emit({**result, "ok": False, "failed_step": "layout_convert"})
        return 1

    p = run([sys.executable, str(blog_scripts / "blog_render.py"), "--md", str(render_dir / f"{slug}.md"),
             "--out-dir", str(blog), "--hero", hero, "--json"])
    sys.stderr.write(p.stderr)
    result["steps"]["blog_render"] = {"exit_code": p.returncode, "json": last_json(p.stdout)}
    if p.returncode != 0:
        common.emit({**result, "ok": False, "failed_step": "blog_render"})
        return 1

    p = run([sys.executable, str(scripts / "finalize_html.py"), "--vault", str(vault), "--run", str(run_dir),
             "--blog", str(blog)])
    sys.stderr.write(p.stderr)
    result["steps"]["finalize_html"] = {"exit_code": p.returncode, "json": last_json(p.stdout)}
    if p.returncode != 0:
        common.emit({**result, "ok": False, "failed_step": "finalize_html"})
        return 1

    html = blog / f"{slug}.html"
    pdf = blog / f"{slug}.pdf"
    result.update({"ok": True, "html": str(html), "pdf": str(pdf) if pdf.exists() else None})
    common.emit(result)
    return 0


def cmd_nonce(args) -> int:
    blog = Path(args.blog).resolve()
    p = run([sys.executable, str(blog_scripts_dir() / "blog_preflight.py"), "--draft", str(blog),
             "--init-review-nonce"])
    sys.stderr.write(p.stderr)
    nonce = ""
    for line in p.stdout.strip().splitlines():
        token = line.strip().split()[-1] if line.strip() else ""
        if len(token) == 32 and all(c in "0123456789abcdef" for c in token.lower()):
            nonce = token.lower()
    common.emit({"ok": p.returncode == 0 and bool(nonce), "nonce": nonce, "exit_code": p.returncode})
    return 0 if nonce else 1


def cmd_gates(args) -> int:
    blog = Path(args.blog).resolve()
    review = blog / "review.md"
    if review.is_file():
        common.update_note(review, {"binder-compile": False})
    cmd = [sys.executable, str(blog_scripts_dir() / "blog_preflight.py"), "--draft", str(blog), "--strict"]
    if args.repair_attempt:
        cmd.append("--repair-attempt")
    p = run(cmd)
    sys.stderr.write(p.stderr)
    sys.stderr.write(p.stdout)
    report = common.json_load(blog / "preflight-report.json", default={}) or {}
    failed = []
    for gate in report.get("gates", []) if isinstance(report.get("gates"), list) else []:
        if isinstance(gate, dict) and not gate.get("passed", True):
            failed.append({"gate": gate.get("gate") or gate.get("name"),
                           "violations": (gate.get("violations") or [])[:8]})
    common.emit({"ok": p.returncode == 0, "exit_code": p.returncode, "blocked": bool(report.get("blocked", p.returncode != 0)),
                 "failed_gates": failed, "report": str(blog / "preflight-report.json")})
    return p.returncode


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vault", default=None)
    ap.add_argument("--run", default=None, help="run folder (needed by render)")
    ap.add_argument("--blog", required=True, help="blog folder")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("render")
    r.add_argument("--hero", default=None, help="hero file name inside the blog folder (auto-detected)")
    sub.add_parser("nonce")
    g = sub.add_parser("gates")
    g.add_argument("--repair-attempt", action="store_true")
    args = ap.parse_args(argv)
    if args.vault is None:
        args.vault = str(common.find_vault_root())
    if args.cmd == "render":
        if not args.run:
            ap.error("render needs --run")
        return cmd_render(args)
    if args.cmd == "nonce":
        return cmd_nonce(args)
    return cmd_gates(args)


if __name__ == "__main__":
    sys.exit(main())
