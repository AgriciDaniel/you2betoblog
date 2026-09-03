"""Tests for evaluate.py: overlap metric, attribution and link checks, review parsing, note."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
sys.path.insert(0, str(SCRIPTS))
import yt2b_common as common  # noqa: E402

ev = common.load_module(SCRIPTS / "evaluate.py", "yt2b_evaluate_test")

VIDEO_ID = "abc123DEF45"
SLUG = "claude-code-hooks-guide"
NONCE = "0123456789abcdef0123456789abcdef"

REVIEW_OK = f"""## Quality Review: Claude Code hooks

### Overall Score: 92/100 - Exceptional
| Category | Score | Max | Notes |
|----------|-------|-----|-------|
| Content Quality | 27 | 30 | tight |
| SEO Optimization | 23 | 25 | fine |
| E-E-A-T Signals | 14 | 15 | bio present |
| Technical Elements | 14 | 15 | schema ok |
| AI Citation Readiness | 14 | 15 | good |

### Issues Found

#### Critical (must fix before publishing)
- (none)

#### High (should fix)
- Add one more internal link in the conclusion

No P0 issues found.

Nonce: {NONCE}
BLOCKING: false (cleared all gates; 92/100, zero P0)
"""

REVIEW_BAD = f"""## Quality Review: Claude Code hooks

### Overall Score: 85/100 - Strong

#### Critical (must fix before publishing)
- Unsourced statistic in section 2 (P0)
- Broken heading hierarchy H2 to H4 (P0)

#### Medium (recommended)
- Shorter intro

Nonce: {NONCE}
BLOCKING: true (overall 85/100 below threshold; P0 on heuristic 5)
"""


def run_script(*args):
    proc = subprocess.run([sys.executable, str(SCRIPTS / "evaluate.py"), *map(str, args)], capture_output=True, text=True)
    lines = [line for line in proc.stdout.strip().splitlines() if line.strip()]
    return proc.returncode, (json.loads(lines[-1]) if lines else {}), proc.stderr


def preflight_report(passed: bool) -> dict:
    gates = [{"gate": n, "name": f"Gate {n}", "passed": True, "violations": [], "warnings": []} for n in range(1, 6)]
    if not passed:
        gates[3]["passed"] = False
        gates[3]["violations"] = ["reviewer blocked"]
    return {"draft": "x", "strict": True, "blocked": not passed, "gates": gates}


def make_world(tmp_path: Path, rights: str = "own", body_extra: str = "", review: str = REVIEW_OK,
               passed: bool = True, voice: bool = True) -> tuple[Path, Path, Path]:
    vault = tmp_path / "vault"
    (vault / ".obsidian").mkdir(parents=True)
    fm = dict(common.DEFAULT_SETTINGS)
    fm.update({"type": "yt2b-settings", "author": "Daniel Agrici", "site_url": "https://example.com"})
    common.write_note(vault / "00 Home" / "Settings.md", fm, "Settings\n")
    if voice:
        (vault / "VOICE.md").write_text("# Voice\n\n## Taboo phrases\n\n- game-changer\n- delve\n- `leverage` (as a verb)\n\n## Tone\n\n- calm\n", encoding="utf-8")
    run = vault / "02 Videos" / f"2026-09-03-claude-code-hooks-explained-{VIDEO_ID}"
    (run / "source").mkdir(parents=True)
    common.json_dump(run / "source" / "video.info.json", {
        "id": VIDEO_ID, "title": "Claude Code Hooks Explained", "channel": "Daniel Agrici",
        "channel_url": "https://www.youtube.com/@danielagrici", "thumbnail": f"https://i.ytimg.com/vi/{VIDEO_ID}/maxresdefault.jpg",
    })
    common.write_note(run / "run.md", {"type": "yt2b-video", "video_id": VIDEO_ID, "rights": rights, "mode": "companion",
                                       "channel": "Daniel Agrici", "tags": ["yt2b", "video"]}, "## Summary\n")
    common.json_dump(run / "analysis" / "segments.json", {"schema": "yt2b/v1", "segments": [
        {"start_s": 0, "end_s": 89, "audio": "a hook is a shell command that claude code runs when a named event fires such as a tool call about to start"},
        {"start_s": 90, "end_s": 230, "audio": "the hook lives under dot claude hooks and the settings file names it under a pre tool use matcher"},
    ]})
    common.json_dump(run / "brief" / "video-brief.json", {"sections": [
        {"id": "s1", "title": "What is a Claude Code hook", "start_s": 0, "end_s": 89},
        {"id": "s2", "title": "Wiring the first hook", "start_s": 90, "end_s": 230},
        {"id": "s3", "title": "Common mistakes", "start_s": 231, "end_s": 400},
    ]})
    blog = vault / "03 Blogs" / f"2026-09-03 {SLUG}"
    (blog / "images").mkdir(parents=True)
    source = (FIXTURES / "rendered-sample.source.md").read_text(encoding="utf-8")
    if rights != "own":
        source = source.replace("yt2b_rights: own", "yt2b_rights: third-party")
    source += "\n## What we verified\n\n| Claim | Verdict | Source |\n|---|---|---|\n| Hooks run before tool calls | CONFIRMED | Claude Code docs |\n"
    source += body_extra
    (blog / f"{SLUG}.md").write_text(source, encoding="utf-8")
    common.json_dump(blog / "images" / "manifest.json", {"images": [
        {"rel": "images/02-settings-before-0130.jpg", "t_s": 90, "label": "Before"},
        {"rel": "images/03-settings-after-0212.jpg", "t_s": 132, "label": "After"},
        {"rel": "images/04-exit-126-0355.jpg", "t_s": 235, "label": "Exit 126"},
    ]})
    (blog / "review.md").write_text(review, encoding="utf-8")
    common.json_dump(blog / "preflight-report.json", preflight_report(passed))
    return vault, run, blog


def test_overlap_ratio_on_known_pairs():
    article = "one two three four five six seven eight nine ten eleven twelve".split()
    same = list(article)
    ratio, hits, total = ev.overlap_ratio(article, same)
    assert (ratio, hits, total) == (1.0, 5, 5)
    partial = "one two three four five six seven eight other words here".split()
    ratio, hits, total = ev.overlap_ratio(article, partial)
    assert (ratio, hits, total) == (0.2, 1, 5)
    assert ev.overlap_ratio(article, ["nothing", "shared"])[0] == 0.0
    assert ev.overlap_ratio(["short"], same)[0] == 0.0
    assert ev.words("Hello, World! It's 2026.") == ["hello", "world", "it", "s", "2026"]


def test_review_parsing():
    ok = ev.parse_review(REVIEW_OK)
    assert ok["score"] == 92 and ok["blocking"] is False and ok["p0"] == 0 and ok["nonce"] is True
    assert [c["name"] for c in ok["categories"]] == ["Content Quality", "SEO Optimization", "E-E-A-T Signals", "Technical Elements", "AI Citation Readiness"]
    assert ok["issues"] == [{"severity": "High", "text": "Add one more internal link in the conclusion"}]
    bad = ev.parse_review(REVIEW_BAD)
    assert bad["score"] == 85 and bad["blocking"] is True and bad["p0"] == 2
    assert "below threshold" in bad["reason"]
    missing = ev.parse_review(None)
    assert missing["score"] == 0 and missing["blocking"] is True


def test_full_run_passes(tmp_path):
    vault, run, blog = make_world(tmp_path)
    code, data, err = run_script("--vault", vault, "--run", run, "--blog", blog, "--no-network")
    assert code == 0, err
    assert data["score"] == 92 and data["blocking"] is False and data["p0"] == 0
    assert data["gates_passed"] is True and data["frames_in_place"] is True, data["findings"]
    assert data["attribution_ok"] is True and data["links_ok"] is True and data["verification_section"] is True
    assert data["voice_flags"] == 0 and data["thumbnail_ok"] is None
    assert 0.0 <= data["overlap_ratio"] <= 0.12
    assert data["status"] == "reviewed" and data["rubric_pass"] is True
    note = Path(data["evaluation_note"])
    assert note.parent == vault / "05 Evaluations" and note.name == f"{common.today()}-{SLUG}.md"
    fm, body = common.read_note(note)
    assert fm["type"] == "yt2b-evaluation" and fm["score"] == 92 and fm["blocking"] is False
    assert fm["overlap_ratio"] == data["overlap_ratio"] and fm["links_ok"] is True and fm["verification_section"] is True
    assert fm["blog"].startswith("[[03 Blogs/") and fm["run"].startswith("[[02 Videos/")
    assert "| Reviewer score | 92 | at least 90 | yes |" in body and "| Content Quality | 27 | 30 |" in body
    post_fm, _ = common.read_note(blog / f"{SLUG}.md")
    assert post_fm["yt2b_score"] == 92 and post_fm["yt2b_status"] == "reviewed"
    assert post_fm["binder-status"] == "complete" and post_fm["binder-type"] == "article"
    code, again, _ = run_script("--vault", vault, "--run", run, "--blog", blog, "--no-network")
    assert code == 0 and Path(again["evaluation_note"]) == note


def test_failures_are_reported(tmp_path):
    extra = "\n\nThis game-changer is explained at [the short link](https://youtu.be/abc123DEF45).\n"
    vault, run, blog = make_world(tmp_path, rights="third-party", body_extra=extra, review=REVIEW_BAD, passed=False)
    code, data, err = run_script("--vault", vault, "--run", run, "--blog", blog, "--no-network")
    assert code == 0, err
    assert data["score"] == 85 and data["blocking"] is True and data["p0"] == 2
    assert data["links_ok"] is False and any("youtu.be" in f for f in data["findings"])
    assert data["voice_flags"] == 1 and any("game-changer" in f for f in data["findings"])
    assert data["attribution_ok"] is False and any("disclosure" in f for f in data["findings"])
    assert data["gates_passed"] is False and data["status"] == "blocked" and data["rubric_pass"] is False
    post_fm, _ = common.read_note(blog / f"{SLUG}.md")
    assert post_fm["yt2b_status"] == "blocked" and post_fm["yt2b_score"] == 85
    assert post_fm["binder-status"] == "in-progress" and post_fm["binder-type"] == "article"


def test_frames_out_of_place_and_disclosure(tmp_path):
    disclosure = ("\n\n*Disclosure: This article is an independent companion to Daniel Agrici's video "
                  "'Claude Code Hooks Explained' (YouTube, published 2026-08-30).*\n")
    vault, run, blog = make_world(tmp_path, rights="third-party", body_extra=disclosure)
    md = blog / f"{SLUG}.md"
    text = md.read_text(encoding="utf-8")
    text = text.replace("![The terminal shows the hook exiting with status 126](images/04-exit-126-0355.jpg)\n", "")
    text = text.replace("## What is a Claude Code hook? {#what-is-a-hook}\n\n",
                        "## What is a Claude Code hook? {#what-is-a-hook}\n\n![Exit](images/04-exit-126-0355.jpg)\n*Exit status ([03:55](https://www.youtube.com/watch?v=abc123DEF45&t=235s))*\n\n")
    md.write_text(text, encoding="utf-8")
    code, data, err = run_script("--vault", vault, "--run", run, "--blog", blog, "--no-network")
    assert code == 0, err
    assert data["attribution_ok"] is True, data["findings"]
    assert data["frames_in_place"] is False and any("04-exit-126-0355.jpg" in f for f in data["findings"])
