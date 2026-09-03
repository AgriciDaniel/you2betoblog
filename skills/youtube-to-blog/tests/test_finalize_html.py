"""Tests for finalize_html.py against the real renderer output fixture."""
from __future__ import annotations

import datetime as dt
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
sys.path.insert(0, str(SCRIPTS))
import yt2b_common as common  # noqa: E402

VIDEO_ID = "abc123DEF45"
SLUG = "claude-code-hooks-guide"
LD_RE = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)
TIMESTAMP = 1756540800


def run_script(*args):
    proc = subprocess.run([sys.executable, str(SCRIPTS / "finalize_html.py"), *map(str, args)], capture_output=True, text=True)
    lines = [line for line in proc.stdout.strip().splitlines() if line.strip()]
    return proc.returncode, (json.loads(lines[-1]) if lines else {}), proc.stderr


def info_dict() -> dict:
    return {
        "id": VIDEO_ID, "title": "Claude Code Hooks Explained", "channel": "Daniel Agrici",
        "channel_url": "https://www.youtube.com/@danielagrici", "upload_date": "20260830", "timestamp": TIMESTAMP,
        "duration": 754, "view_count": 1234,
        "description": "A walkthrough of Claude Code hooks. " * 12,
        "thumbnail": f"https://i.ytimg.com/vi/{VIDEO_ID}/maxresdefault.jpg",
        "chapters": [{"start_time": 0, "title": "Intro"}, {"start_time": 42, "title": "What is a hook"}],
    }


def make_world(tmp_path: Path, rights: str = "own", profile: bool = True, chapters=None) -> tuple[Path, Path, Path]:
    vault = tmp_path / "vault"
    (vault / ".obsidian").mkdir(parents=True)
    fm = dict(common.DEFAULT_SETTINGS)
    fm.update({"type": "yt2b-settings", "author": "Daniel Agrici", "site_url": "https://example.com"})
    common.write_note(vault / "00 Home" / "Settings.md", fm, "Settings\n")
    if profile:
        common.write_note(vault / "06 AI Team" / "03 Knowledge" / "04 Voice" / "Author Profile.md", {
            "type": "yt2b-knowledge", "kind": "voice", "name": "Daniel Agrici", "url": "https://example.com/about",
            "job_title": "Marketing engineer", "same_as": ["https://www.youtube.com/@danielagrici", "https://github.com/AgriciDaniel"],
        }, "# Author Profile\n")
    run = vault / "02 Videos" / f"2026-09-03-claude-code-hooks-explained-{VIDEO_ID}"
    (run / "source").mkdir(parents=True)
    common.json_dump(run / "source" / "video.info.json", info_dict())
    common.write_note(run / "run.md", {"type": "yt2b-video", "video_id": VIDEO_ID, "rights": rights, "mode": "companion",
                                       "tags": ["yt2b", "video"]}, "## Summary\n")
    if chapters is None:
        chapters = [{"start_s": 0, "title": "Intro"}, {"start_s": 42, "title": "What is a hook"},
                    {"start_s": 90, "title": "Wiring the first hook"}, {"start_s": 235, "title": "Common mistakes"}]
    common.json_dump(run / "brief" / "video-brief.json", {"chapters": chapters})
    blog = vault / "03 Blogs" / f"2026-09-03 {SLUG}"
    (blog / "images").mkdir(parents=True)
    source = (FIXTURES / "rendered-sample.source.md").read_text(encoding="utf-8")
    if rights != "own":
        source = source.replace("yt2b_rights: own", "yt2b_rights: third-party")
    (blog / f"{SLUG}.md").write_text(source, encoding="utf-8")
    shutil.copyfile(FIXTURES / "rendered-sample.html", blog / f"{SLUG}.html")
    for name in ("video-thumb.jpg", "02-settings-before-0130.jpg", "03-settings-after-0212.jpg", "04-exit-126-0355.jpg"):
        (blog / "images" / name).write_bytes(b"jpg")
    return vault, run, blog


def graph_of(html_text: str) -> list[dict]:
    blocks = LD_RE.findall(html_text)
    assert len(blocks) == 1, f"expected one JSON-LD script, found {len(blocks)}"
    data = json.loads(blocks[0])
    assert data["@context"] == "https://schema.org"
    return data["@graph"]


def test_graph_person_css_and_publish_kit_own_mode(tmp_path):
    vault, run, blog = make_world(tmp_path, "own")
    original = json.loads(LD_RE.findall((FIXTURES / "rendered-sample.html").read_text(encoding="utf-8"))[0])
    code, data, err = run_script("--vault", vault, "--run", run, "--blog", blog)
    assert code == 0, err
    html_text = (blog / f"{SLUG}.html").read_text(encoding="utf-8")
    graph = graph_of(html_text)
    assert data["schema_nodes"] == 2 and len(graph) == 2
    posting, person = graph
    assert posting["@type"] == "BlogPosting" and "@context" not in posting
    assert posting["wordCount"] == original["wordCount"], "renderer wordCount kept verbatim"
    assert posting["headline"] == original["headline"] and posting["description"] == original["description"]
    assert posting["image"] == original["image"] and posting["datePublished"] == original["datePublished"]
    assert posting["@id"] == f"https://example.com/{SLUG}/#article"
    assert posting["author"] == {"@id": "https://example.com/about#person"}
    assert person == {"@type": "Person", "@id": "https://example.com/about#person", "name": "Daniel Agrici",
                      "url": "https://example.com/about", "jobTitle": "Marketing engineer",
                      "sameAs": ["https://www.youtube.com/@danielagrici", "https://github.com/AgriciDaniel"]}
    assert not any(node.get("@type") == "VideoObject" for node in graph), "no player in the preview, no VideoObject"
    assert html_text.count('<style id="yt2b-styles">') == 1 and ".yt2b-layout.image-layout-a" in html_text
    assert "<iframe" not in html_text
    assert data["embed_present"] is True and data["person"] is True

    kit = blog / "publish-kit"
    names = sorted(p.name for p in kit.iterdir())
    assert names == sorted(["README.txt", "embed.html", "layouts.css", "video-object.jsonld", f"{SLUG}.publish.md", "youtube-chapters.txt"])
    vo = json.loads((kit / "video-object.jsonld").read_text(encoding="utf-8"))
    assert vo["@type"] == "VideoObject" and vo["@id"] == f"https://example.com/{SLUG}/#video"
    assert vo["name"] == "Claude Code Hooks Explained" and len(vo["description"]) <= 200
    assert vo["thumbnailUrl"] == f"https://i.ytimg.com/vi/{VIDEO_ID}/maxresdefault.jpg"
    assert vo["uploadDate"] == dt.datetime.fromtimestamp(TIMESTAMP, tz=dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    assert vo["duration"] == "PT12M34S"
    assert vo["embedUrl"] == f"https://www.youtube-nocookie.com/embed/{VIDEO_ID}"
    assert vo["url"] == f"https://www.youtube.com/watch?v={VIDEO_ID}"
    assert vo["isPartOf"] == {"@id": f"https://example.com/{SLUG}/#article"}
    assert vo["creator"] == {"@id": "https://example.com/about#person"}
    assert "contentUrl" not in vo and "interactionStatistic" not in vo
    embed = (kit / "embed.html").read_text(encoding="utf-8")
    assert f'src="https://www.youtube-nocookie.com/embed/{VIDEO_ID}"' in embed
    assert 'referrerpolicy="strict-origin-when-cross-origin"' in embed and "no-referrer" not in embed
    assert "published 2026-08-30" in embed
    publish = (kit / f"{SLUG}.publish.md").read_text(encoding="utf-8")
    assert '<figure class="yt2b-layout image-layout-a">' in publish and "```image-layout" not in publish
    assert '<figure class="video-embed">' in publish
    publish_fm, _ = common.read_note(kit / f"{SLUG}.publish.md")
    assert publish_fm["binder-compile"] is False
    chapters = (kit / "youtube-chapters.txt").read_text(encoding="utf-8").splitlines()
    assert chapters == ["00:00 Intro", "00:42 What is a hook", "01:30 Wiring the first hook", "03:55 Common mistakes"]
    readme = (kit / "README.txt").read_text(encoding="utf-8")
    assert "only on the page" in readme and "#video" in readme

    code, again, err = run_script("--vault", vault, "--run", run, "--blog", blog)
    assert code == 0, err
    assert (blog / f"{SLUG}.html").read_text(encoding="utf-8") == html_text, "idempotent"
    assert LD_RE.findall(html_text) and len(LD_RE.findall(html_text)) == 1


def test_third_party_without_profile(tmp_path):
    vault, run, blog = make_world(tmp_path, "third-party", profile=False, chapters=[{"start_s": 0, "title": "Intro"}])
    code, data, err = run_script("--vault", vault, "--run", run, "--blog", blog)
    assert code == 0, err
    graph = graph_of((blog / f"{SLUG}.html").read_text(encoding="utf-8"))
    posting, person = graph
    assert person["@id"] == "https://example.com/author/daniel-agrici#person" and person["name"] == "Daniel Agrici"
    assert "url" not in person and "jobTitle" not in person
    assert posting["author"] == {"@id": person["@id"]}
    vo = json.loads((blog / "publish-kit" / "video-object.jsonld").read_text(encoding="utf-8"))
    assert vo["creator"] == {"@type": "Organization", "name": "Daniel Agrici", "url": "https://www.youtube.com/@danielagrici"}
    assert not (blog / "publish-kit" / "youtube-chapters.txt").exists()
    assert not any("youtube-chapters" in w for w in data["warnings"]), "third-party mode never writes chapters"


def test_chapter_validation_skips_short_lists(tmp_path):
    vault, run, blog = make_world(tmp_path, "own", chapters=[{"start_s": 0, "title": "Intro"}, {"start_s": 5, "title": "Too soon"}])
    code, data, err = run_script("--vault", vault, "--run", run, "--blog", blog)
    assert code == 0, err
    assert not (blog / "publish-kit" / "youtube-chapters.txt").exists()
    assert any("youtube-chapters.txt" in w for w in data["warnings"])
    fh = common.load_module(SCRIPTS / "finalize_html.py", "yt2b_finalize_test")
    lines, warning = fh.chapter_lines([{"start_s": 0, "title": "A"}, {"start_s": 20, "title": "B"}, {"start_s": 3700, "title": "C"}])
    assert lines == ["00:00 A", "00:20 B", "1:01:40 C"] and warning == ""
    assert fh.chapter_lines([{"start_s": 1, "title": "A"}, {"start_s": 20, "title": "B"}, {"start_s": 40, "title": "C"}])[1]
    assert fh.chapter_lines([{"start_s": 0, "title": "A"}, {"start_s": 20, "title": "B"}, {"start_s": 25, "title": "C"}])[1]


def test_missing_html_is_invalid_input(tmp_path):
    vault, run, blog = make_world(tmp_path)
    (blog / f"{SLUG}.html").unlink()
    code, data, _ = run_script("--vault", vault, "--run", run, "--blog", blog)
    assert code == 2 and data["ok"] is False


@pytest.mark.skipif(not (common.blog_scripts_dir() / "blog_render.py").is_file(), reason="blog_render.py not installed")
def test_renderer_strips_iframe_and_keeps_thumbnail_link(tmp_path):
    out_dir = tmp_path / "draft"
    out_dir.mkdir()
    src = out_dir / f"{SLUG}.md"
    shutil.copyfile(FIXTURES / "rendered-sample.md", src)
    proc = subprocess.run([sys.executable, str(common.blog_scripts_dir() / "blog_render.py"), "--md", str(src),
                           "--out-dir", str(out_dir), "--hero", "hero.jpg", "--pdf-engine", "none"],
                          capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    html_text = (out_dir / f"{SLUG}.html").read_text(encoding="utf-8")
    assert "<iframe" not in html_text
    figure = html_text[html_text.index('<figure class="video-embed">'):]
    figure = figure[:figure.index("</figure>")]
    assert figure.count("<img") == 1 and 'src="images/video-thumb.jpg"' in figure
    assert f'href="https://www.youtube.com/watch?v={VIDEO_ID}"' in figure
    assert 'href="https://www.youtube.com/@danielagrici"' in figure
    assert "<noscript" not in figure
