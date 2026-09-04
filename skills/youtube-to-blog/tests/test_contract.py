"""Tests for the local Gate 6 article contract."""

from __future__ import annotations

from pathlib import Path

import contract
import yt2b_common as common

VIDEO_ID = "abc123DEF45"
SLUG = "safe-video-guide"


def make_world(tmp_path: Path) -> tuple[Path, Path, Path]:
    vault = tmp_path / "vault"
    (vault / ".obsidian").mkdir(parents=True)
    settings = dict(common.DEFAULT_SETTINGS)
    settings.update({"type": "yt2b-settings", "author": "Test Author", "site_url": "https://brandsite.dev"})
    common.write_note(vault / common.SETTINGS_NOTE, settings, "# Settings\n")
    (vault / "BRAND.md").write_text("# Brand\n", encoding="utf-8")
    (vault / "VOICE.md").write_text("# Voice\n", encoding="utf-8")

    run = vault / "02 Videos" / f"2026-09-04-safe-video-{VIDEO_ID}"
    (run / "brief").mkdir(parents=True)
    common.json_dump(run / "brief" / "video-brief.json", {"sections": []})
    common.write_note(run / "run.md", {
        "type": "yt2b-video", "video_id": VIDEO_ID, "status": "writing", "rights": "own",
        "mode": "companion", "blogs": [], "queue": "", "tags": ["yt2b", "stage/writing"],
    }, "## Log\n\n- 2026-09-04T10:00:00 provider authorization: current full request\n")
    common.write_note(run / "strategy.md", {"type": "yt2b-knowledge", "kind": "strategy"},
                      f"# Strategy\n\n## Angles\n\n### blog-1\n- **Slug**: {SLUG}\n")

    blog = vault / "03 Blogs" / f"2026-09-04 {SLUG}"
    blog.mkdir(parents=True)
    body = f"""# Safe video guide

An original companion article with enough useful words to exercise the deterministic policy checks before delivery.

<figure class="video-embed">
  <iframe src="https://www.youtube-nocookie.com/embed/{VIDEO_ID}" title="Safe video"></iframe>
  <figcaption><a href="https://www.youtube.com/watch?v={VIDEO_ID}">Watch the video</a></figcaption>
</figure>

## What we verified

The important claims were checked against primary documentation and the source video.
"""
    post_fm = {
        "type": "yt2b-blog", "title": "Safe video guide", "slug": SLUG,
        "canonical": f"https://brandsite.dev/blog/{SLUG}",
        "yt2b_video": common.wikilink(common.rel(run / "run.md", vault), "run"),
        "yt2b_status": "drafting", "word-count-goal": contract.body_word_count(body),
    }
    common.write_note(blog / f"{SLUG}.md", post_fm, body)
    (blog / "review.md").write_text("""### Overall Score: 95/100

#### Critical
- (none)

#### High
- (none)

Nonce: 0123456789abcdef0123456789abcdef
BLOCKING: false (ready)
""", encoding="utf-8")

    approvals = vault / common.ROOMS["approvals_queue"]
    strategy_link = common.wikilink(common.rel(run / "run.md", vault), "run")
    common.write_note(approvals / f"2026-09-04-{VIDEO_ID}-strategy.md", {
        "type": "yt2b-approval", "kind": "strategy", "status": "approved", "run": strategy_link,
        "blog": "", "selected": ["blog-1"], "tags": contract.approval_tags("strategy", "approved"),
    }, "# Strategy decision\n")
    common.write_note(approvals / f"2026-09-04-{VIDEO_ID}-outline-{SLUG}.md", {
        "type": "yt2b-approval", "kind": "outline", "status": "approved", "run": strategy_link,
        "blog": common.wikilink(common.rel(blog / f"{SLUG}.md", vault), SLUG), "selected": ["proceed"],
        "tags": contract.approval_tags("outline", "approved"),
    }, "# Outline decision\n")
    return vault, run, blog


def test_contract_passes_for_consistent_article(tmp_path):
    vault, run, blog = make_world(tmp_path)
    gate = contract.contract_gate(vault, run, blog)
    assert gate["passed"] is True, gate
    assert gate["violations"] == [] and gate["actual_word_count"] == gate["word_count_goal"]


def test_contract_rejects_placeholder_slug_embed_and_dash(tmp_path):
    vault, run, blog = make_world(tmp_path)
    post = blog / f"{SLUG}.md"
    fm, body = common.read_note(post)
    fm["canonical"] = "https://example.com/blog/wrong"
    body = body.replace(f"youtube-nocookie.com/embed/{VIDEO_ID}", "evil.test/embed/wrong") + "\nBad \u2014 dash.\n"
    common.write_note(post, fm, body)
    gate = contract.contract_gate(vault, run, blog)
    assert gate["passed"] is False
    joined = "\n".join(gate["violations"])
    assert "canonical" in joined and "iframe source" in joined and "dash" in joined


def test_high_finding_needs_specific_editorial_waiver(tmp_path):
    vault, run, blog = make_world(tmp_path)
    (blog / "review.md").write_text("""### Overall Score: 94/100

#### High
- A cited price does not support the sentence.

No P0 issues.
BLOCKING: false (editor should decide)
""", encoding="utf-8")
    gate = contract.contract_gate(vault, run, blog)
    assert gate["passed"] is False and "unresolved Critical or High" in "\n".join(gate["violations"])
    common.write_note(vault / common.ROOMS["approvals_queue"] / f"2026-09-04-{VIDEO_ID}-editorial-{SLUG}.md", {
        "type": "yt2b-approval", "kind": "editorial", "status": "approved",
        "run": common.wikilink(common.rel(run / "run.md", vault), "run"),
        "blog": common.wikilink(common.rel(blog / f"{SLUG}.md", vault), SLUG),
        "selected": ["accept-high"], "tags": contract.approval_tags("editorial", "approved"),
    }, "# Editorial decision\n")
    assert contract.contract_gate(vault, run, blog)["passed"] is True


def test_word_count_drift_blocks(tmp_path):
    vault, run, blog = make_world(tmp_path)
    post = blog / f"{SLUG}.md"
    fm, body = common.read_note(post)
    fm["word-count-goal"] = max(1, contract.body_word_count(body) // 3)
    common.write_note(post, fm, body)
    gate = contract.contract_gate(vault, run, blog)
    assert gate["passed"] is False and any("word count" in item for item in gate["violations"])


def test_unselected_strategy_angle_is_rejected(tmp_path):
    vault, run, blog = make_world(tmp_path)
    strategy = next((vault / common.ROOMS["approvals_queue"]).glob("*-strategy.md"))
    common.update_note(strategy, {"selected": ["blog-2"]})
    gate = contract.contract_gate(vault, run, blog)
    assert gate["passed"] is False
    assert any("does not map" in item for item in gate["violations"])
