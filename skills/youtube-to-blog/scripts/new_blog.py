#!/usr/bin/env python3
"""Create a blog delivery folder for an approved angle (03 Blogs/<date> <slug>/).

Usage:
    new_blog.py [--vault PATH] --run RUN_DIR --slug SLUG --title TITLE [--description TEXT]
                [--template ID] [--rights R] [--mode M] [--word-goal N] [--force]

Creates the folder, images/, and <slug>.md with the full frontmatter: the post
fields the renderer needs (title, description, date, author, slug, tags, lang,
canonical), the pipeline fields (type, yt2b_status, yt2b_score, yt2b_video,
yt2b_rights, yt2b_mode, yt2b_template) and the Writing Studio fields
(binder-order as YYYYMMDD plus a two digit sequence, binder-status,
binder-type and word-count-goal). The body
is a placeholder until the writer runs. canonical is always written: from
Settings site_url when set, else a placeholder plus a warning. Registers the
blog in run.md. Prints {blog_dir, md_path, slug, canonical, warnings}.
Exit 0 ok, 2 invalid input or existing folder without --force.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import yt2b_common as common  # noqa: E402
import make_run_note  # noqa: E402

PLACEHOLDER_SITE = "https://example.com/blog"
DEFAULT_WORD_GOAL = 2000
PLACEHOLDER_BODY = "<!-- draft pending -->\n"


def canonical_url(site_url: str, slug: str) -> tuple[str, str | None]:
    """Canonical URL plus a warning when Settings has no site_url."""
    if site_url and str(site_url).startswith(("http://", "https://")):
        return f"{str(site_url).rstrip('/')}/{slug}", None
    return f"{PLACEHOLDER_SITE}/{slug}", "site_url is empty in 00 Home/Settings.md; canonical uses a placeholder, set site_url before publishing"


def binder_order(blogs_root: Path, date: str, blog_dir: Path) -> int:
    """YYYYMMDD followed by the two digit sequence among today's blog folders."""
    existing = [p for p in blogs_root.glob(f"{date} *") if p.is_dir() and p != blog_dir] if blogs_root.is_dir() else []
    return int(date.replace("-", "") + f"{len(existing) + 1:02d}")


def build_frontmatter(settings: dict, run_dir: Path, vault: Path, slug: str, args, canonical: str, order: int) -> dict:
    run_fm = common.read_note(run_dir / "run.md")[0] if (run_dir / "run.md").is_file() else {}
    run_link = common.wikilink(common.rel(run_dir, vault) + "/run.md", str(run_fm.get("title") or run_dir.name))
    return {
        "title": args.title, "description": args.description or "", "date": common.today(),
        "author": str(settings.get("author") or ""), "slug": slug, "tags": [], "lang": str(settings.get("language") or "en"),
        "canonical": canonical, "type": common.NOTE_TYPES["blog"], "yt2b_status": "drafting", "yt2b_score": 0,
        "yt2b_video": run_link, "yt2b_rights": args.rights or str(run_fm.get("rights") or ""),
        "yt2b_mode": args.mode or str(run_fm.get("mode") or ""), "yt2b_template": args.template or "",
        "binder-order": order, "binder-status": "draft", "binder-type": "article",
        "word-count-goal": int(args.word_goal or DEFAULT_WORD_GOAL),
        "created": common.today(), "updated": common.today(),
    }


def create_blog(vault: Path, run_dir: Path, args) -> dict:
    settings = common.load_settings(vault)
    slug = common.slugify(args.slug, 60)
    blogs_root = vault / common.ROOMS["blogs"]
    blog_dir = blogs_root / common.blog_dir_name(slug)
    md_path = blog_dir / f"{slug}.md"
    if blog_dir.exists() and not args.force:
        raise FileExistsError(f"blog folder exists: {blog_dir} (use --force to reuse it)")
    warnings: list[str] = []
    canonical, warning = canonical_url(str(settings.get("site_url") or ""), slug)
    if warning:
        warnings.append(warning)
    if not settings.get("author"):
        warnings.append("author is empty in 00 Home/Settings.md; the renderer requires a non-empty author")
    order = binder_order(blogs_root, common.today(), blog_dir)
    frontmatter = build_frontmatter(settings, run_dir, vault, slug, args, canonical, order)
    body = PLACEHOLDER_BODY
    if md_path.is_file():
        old_fm, old_body = common.read_note(md_path)
        frontmatter["created"] = old_fm.get("created", frontmatter["created"])
        frontmatter["binder-order"] = old_fm.get("binder-order", order)
        body = old_body if old_body.strip() else body
    common.ensure_dir(blog_dir / "images")
    common.write_note(md_path, frontmatter, body)
    make_run_note.update_run_note(vault, run_dir, add_blog=blog_dir, log=f"blog created: {slug}")
    return {"ok": True, "blog_dir": str(blog_dir), "md_path": str(md_path), "slug": slug, "canonical": canonical,
            "binder_order": frontmatter["binder-order"], "warnings": warnings}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create a blog delivery folder.")
    parser.add_argument("--vault")
    parser.add_argument("--run", required=True)
    parser.add_argument("--slug", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--description", default="")
    parser.add_argument("--template", default="")
    parser.add_argument("--rights", choices=common.RIGHTS + ("ask",))
    parser.add_argument("--mode", choices=common.MODES)
    parser.add_argument("--word-goal", type=int, default=DEFAULT_WORD_GOAL)
    parser.add_argument("--force", action="store_true", help="Reuse an existing folder (the body is kept)")
    args = parser.parse_args(argv)
    try:
        vault = Path(args.vault).expanduser().resolve() if args.vault else common.find_vault_root()
    except FileNotFoundError as exc:
        return common.fail(common.EXIT_INPUT, str(exc))
    run_dir = make_run_note.resolve_run(vault, args.run)
    if not run_dir.is_dir():
        return common.fail(common.EXIT_INPUT, f"run folder not found: {run_dir}")
    if not args.title.strip():
        return common.fail(common.EXIT_INPUT, "--title must not be empty")
    try:
        result = create_blog(vault, run_dir, args)
    except FileExistsError as exc:
        return common.fail(common.EXIT_INPUT, str(exc))
    for message in result["warnings"]:
        common.warn(f"warning: {message}")
    common.emit(result)
    return common.EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
