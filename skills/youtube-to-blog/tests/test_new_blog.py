"""Tests for new_blog.py: naming, frontmatter, binder order, refusal."""

from __future__ import annotations

import yt2b_common as common
from conftest import run_main


def make(vault, run_dir, capsys, slug="My First Post", extra=()):
    return run_main("new_blog", ["--vault", str(vault), "--run", str(run_dir), "--slug", slug, "--title", "Title here",
                                 "--description", "Desc", "--template", "how-to", "--rights", "own", "--mode", "companion", *extra], capsys)


def test_folder_and_frontmatter(vault, run_dir, capsys):
    run_main("make_run_note", ["--vault", str(vault), "--run", str(run_dir), "--status", "strategy"], capsys)
    code, out = make(vault, run_dir, capsys)
    assert code == 0 and out["slug"] == "my-first-post" and out["warnings"] == []
    blog = vault / "03 Blogs" / f"{common.today()} my-first-post"
    assert blog.is_dir() and (blog / "images").is_dir() and blog == blog.resolve() and out["blog_dir"] == str(blog)
    md = blog / "my-first-post.md"
    fm, body = common.read_note(md)
    assert body.strip() == "<!-- draft pending -->"
    assert fm["title"] == "Title here" and fm["description"] == "Desc" and str(fm["date"]) == common.today()
    assert fm["author"] == "Test Author" and fm["slug"] == md.stem and fm["tags"] == [] and fm["lang"] == "en"
    assert fm["canonical"] == "https://brandsite.dev/my-first-post"
    assert fm["type"] == "yt2b-blog" and fm["yt2b_status"] == "drafting" and fm["yt2b_score"] == 0
    assert fm["binder-status"] == "draft" and fm["binder-type"] == "article"
    assert fm["yt2b_video"].startswith("[[02 Videos/") and fm["yt2b_rights"] == "own" and fm["yt2b_mode"] == "companion"
    assert fm["yt2b_template"] == "how-to" and fm["word-count-goal"] == 2000
    assert fm["binder-order"] == int(common.today().replace("-", "") + "01")
    assert [p.name for p in blog.glob("*.md")] == ["my-first-post.md"]
    run_fm, _ = common.read_note(run_dir / "run.md")
    assert run_fm["blogs"] == [f"[[03 Blogs/{common.today()} my-first-post/my-first-post|my-first-post]]"]


def test_binder_order_sequence(vault, run_dir, capsys):
    make(vault, run_dir, capsys, "first")
    code, out = make(vault, run_dir, capsys, "second", ["--word-goal", "1500"])
    fm, _ = common.read_note(out["md_path"])
    assert fm["binder-order"] == int(common.today().replace("-", "") + "02") and fm["word-count-goal"] == 1500


def test_refuse_existing_unless_force(vault, run_dir, capsys):
    _, first = make(vault, run_dir, capsys, "same")
    (vault / "03 Blogs" / f"{common.today()} same" / "same.md").write_text("---\ntitle: old\ncreated: 2020-01-01\n---\nDraft text.\n", encoding="utf-8")
    code, out = make(vault, run_dir, capsys, "same")
    assert code == 2 and out["ok"] is False
    code, out = make(vault, run_dir, capsys, "same", ["--force"])
    fm, body = common.read_note(out["md_path"])
    assert code == 0 and body.strip() == "Draft text." and fm["title"] == "Title here" and str(fm["created"]) == "2020-01-01"


def test_placeholder_canonical_is_refused_before_write(vault, run_dir, capsys):
    common.update_note(vault / common.SETTINGS_NOTE, {"site_url": ""})
    code, out = make(vault, run_dir, capsys)
    assert code == common.EXIT_POLICY and out["ok"] is False
    assert "site_url" in out["error"]
    assert not (vault / "03 Blogs" / f"{common.today()} my-first-post").exists()


def test_missing_run_exit_2(vault, capsys):
    code, out = run_main("new_blog", ["--vault", str(vault), "--run", "02 Videos/none", "--slug", "x", "--title", "T"], capsys)
    assert code == 2
