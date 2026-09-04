#!/usr/bin/env python3
"""Finalize the rendered blog HTML and write the publish kit.

Rewrites <blog>/<slug>.html in place:
  * exactly one application/ld+json script holding
    {"@context": "https://schema.org", "@graph": [BlogPosting, Person]}
    where BlogPosting is the renderer's node kept verbatim (wordCount included)
    plus "@id" (<canonical>#article) and, when a Person exists, an "author"
    reference to it; Person comes from the Author Profile note and Settings
  * a <style id="yt2b-styles"> block with the layout grid CSS when the page
    uses .yt2b-layout figures or the video-embed figure

The preview HTML never holds a player (the renderer strips iframes), so the
VideoObject is not placed in the HTML graph. It is written to
publish-kit/video-object.jsonld for the live page that renders the player.

Also writes publish-kit/embed.html, layouts.css, <slug>.publish.md (layout
blocks converted to HTML figures), youtube-chapters.txt (own mode, at least
three valid chapters) and README.txt.

Idempotent. Exit codes: 0 ok, 1 failure, 2 invalid input.
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import yt2b_common as common  # noqa: E402

LD_RE = re.compile(r'<script\b[^>]*\btype=["\']application/ld\+json["\'][^>]*>(.*?)</script>[ \t]*\n?', re.S | re.I)
STYLE_ID = "yt2b-styles"
STYLE_RE = re.compile(r'<style id="' + STYLE_ID + r'">.*?</style>\n?', re.S)
EMBED_RE = re.compile(r"youtube-nocookie\.com/embed/([A-Za-z0-9_-]{11})")
AUTHOR_PROFILE = "Author Profile.md"
MIN_CHAPTERS = 3
MIN_CHAPTER_GAP_S = 10

LAYOUT_CSS = """.yt2b-layout{display:grid;gap:.75rem;margin:2rem 0;padding:0}
.yt2b-layout figure{margin:0;padding:0}
.yt2b-layout img{width:100%;height:auto;display:block;border-radius:8px}
.yt2b-layout figcaption{font-size:.875rem;line-height:1.4;opacity:.8;margin-top:.35rem}
.yt2b-layout>figcaption{grid-column:1/-1;margin-top:0}
.yt2b-layout.image-layout-a{grid-template-columns:repeat(2,minmax(0,1fr))}
.yt2b-layout.image-layout-d{grid-template-columns:2fr 1fr;grid-template-areas:"main top" "main bottom" "caption caption"}
.yt2b-layout.image-layout-d>:nth-child(1){grid-area:main}
.yt2b-layout.image-layout-d>:nth-child(2){grid-area:top}
.yt2b-layout.image-layout-d>:nth-child(3){grid-area:bottom}
.yt2b-layout.image-layout-d>figcaption{grid-area:caption}
.yt2b-layout.image-layout-h{grid-template-columns:repeat(3,minmax(0,1fr))}
.yt2b-layout.image-layout-masonry-3{display:block;columns:3;column-gap:.75rem}
.yt2b-layout.image-layout-masonry-3>*{break-inside:avoid;margin:0 0 .75rem}
.yt2b-layout.image-layout-masonry-3>figcaption{column-span:all}
.yt2b-layout:not(.image-layout-a):not(.image-layout-d):not(.image-layout-h):not(.image-layout-masonry-3){grid-template-columns:repeat(auto-fit,minmax(240px,1fr))}
.yt2b-layout.yt2b-fit-cover img{aspect-ratio:16/9;object-fit:cover}
.yt2b-layout.yt2b-fit-contain img{object-fit:contain}
.yt2b-layout.yt2b-align-center{margin-left:auto;margin-right:auto}
.video-embed{margin:2rem 0;padding:0}
.video-embed iframe{display:block;width:100%;aspect-ratio:16/9;height:auto;border:0;border-radius:12px}
.video-embed img{width:100%;height:auto;display:block;border-radius:12px}
.video-embed figcaption{font-size:.875rem;line-height:1.4;opacity:.8;margin-top:.5rem}
article table{display:block;max-width:100%;overflow-x:auto}
article img{max-width:100%;height:auto}
@media (max-width:640px){.yt2b-layout.image-layout-a,.yt2b-layout.image-layout-h{grid-template-columns:1fr}.yt2b-layout.image-layout-d{grid-template-columns:1fr;grid-template-areas:"main" "top" "bottom" "caption"}.yt2b-layout.image-layout-masonry-3{columns:1}}
"""

EMBED_TEMPLATE = """<figure class="video-embed">
  <iframe src="https://www.youtube-nocookie.com/embed/{video_id}" title="{title}" loading="lazy" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
  <noscript><a href="{watch}"><img src="images/video-thumb.jpg" alt="Watch: {title}" loading="lazy"></a></noscript>
  <figcaption>Video: <a href="{watch}">{title}</a> by {channel_html} (YouTube, published {published}).</figcaption>
</figure>
"""


# ---------------------------------------------------------------------------
# Local helpers
# ---------------------------------------------------------------------------

def blog_markdown(blog_dir: Path) -> Path | None:
    mds = sorted(p for p in blog_dir.glob("*.md") if p.name != "review.md")
    return mds[0] if len(mds) == 1 else None


def note_frontmatter(path: Path | None) -> dict:
    if path is None or not path.is_file():
        return {}
    fm, _ = common.read_note(path)
    return fm


def flatten_nodes(value) -> list[dict]:
    nodes: list[dict] = []
    if isinstance(value, list):
        for item in value:
            nodes.extend(flatten_nodes(item))
    elif isinstance(value, dict):
        graph = value.get("@graph")
        if isinstance(graph, list):
            nodes.extend(flatten_nodes(graph))
        nodes.append(value)
    return nodes


def is_type(node: dict, type_name: str) -> bool:
    t = node.get("@type")
    return t == type_name or (isinstance(t, list) and type_name in t)


def find_blogposting(html_text: str) -> tuple[dict | None, int]:
    blocks = LD_RE.findall(html_text)
    for raw in blocks:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        for node in flatten_nodes(data):
            if is_type(node, "BlogPosting"):
                return node, len(blocks)
    return None, len(blocks)


def serialize_ld(data) -> str:
    return json.dumps(data, ensure_ascii=False).replace("</", "<\\/")


def replace_json_ld(html_text: str, graph_json: str) -> str:
    matches = list(LD_RE.finditer(html_text))
    if not matches:
        raise ValueError("no application/ld+json script found in the rendered html")
    script = f'<script type="application/ld+json">{graph_json}</script>\n'
    out = html_text[:matches[0].start()] + script
    prev = matches[0].end()
    for m in matches[1:]:
        out += html_text[prev:m.start()]
        prev = m.end()
    return out + html_text[prev:]


def set_style(html_text: str, css: str | None) -> str:
    html_text = STYLE_RE.sub("", html_text)
    if not css:
        return html_text
    idx = html_text.lower().find("</head>")
    block = f'<style id="{STYLE_ID}">{css}</style>\n'
    if idx < 0:
        return html_text + block
    return html_text[:idx] + block + html_text[idx:]


IMG_RE = re.compile(r"<img\b([^>]*)>", re.I)
ATTR_RE = re.compile(r'\b([a-zA-Z-]+)\s*=\s*"([^"]*)"')


def image_size(path: Path) -> tuple[int, int] | None:
    try:
        from PIL import Image  # type: ignore
    except Exception:
        return None
    try:
        with Image.open(path) as im:
            return int(im.width), int(im.height)
    except Exception:
        return None


def enhance_images(html_text: str, blog_dir: Path) -> tuple[str, int]:
    """Add loading="lazy" and intrinsic width and height to local content images.

    The hero (hero.*) keeps eager loading. Remote images are left untouched
    (the gates reject them anyway). Idempotent.
    """
    changed = 0

    def fix(match: re.Match) -> str:
        nonlocal changed
        attrs = match.group(1)
        found = dict(ATTR_RE.findall(attrs))
        src = found.get("src", "")
        if not src or src.startswith(("http://", "https://", "data:", "/")):
            return match.group(0)
        if Path(src).name.startswith("hero."):
            return match.group(0)
        extra = ""
        if "loading" not in found:
            extra += ' loading="lazy"'
        if "width" not in found or "height" not in found:
            size = image_size((blog_dir / src).resolve())
            if size:
                if "width" not in found:
                    extra += f' width="{size[0]}"'
                if "height" not in found:
                    extra += f' height="{size[1]}"'
        if not extra:
            return match.group(0)
        changed += 1
        return f"<img{attrs.rstrip()}{extra}>"

    return IMG_RE.sub(fix, html_text), changed


def author_profile(vault: Path) -> dict:
    fm = note_frontmatter(vault / common.ROOMS["voice"] / AUTHOR_PROFILE)
    same_as = fm.get("same_as") or []
    if isinstance(same_as, str):
        same_as = [same_as]
    return {
        "name": str(fm.get("name") or "").strip(),
        "url": str(fm.get("url") or "").strip(),
        "job_title": str(fm.get("job_title") or "").strip(),
        "same_as": [str(s).strip() for s in same_as if str(s).strip()],
    }


def build_person(settings: dict, profile: dict, page_url: str = "") -> dict | None:
    name = profile.get("name") or str(settings.get("author") or "").strip()
    if not name:
        return None
    url = profile.get("url") or ""
    site = str(settings.get("site_url") or "").strip()
    person: dict = {"@type": "Person"}
    if url:
        person["@id"] = f"{url.rstrip('/')}#person"
    elif site:
        person["@id"] = f"{site.rstrip('/')}/author/{common.slugify(name, 60)}#person"
    person["name"] = name
    if "@id" not in person and page_url:
        person["@id"] = f"{page_url}#person"
    if url:
        person["url"] = url
    if profile.get("job_title"):
        person["jobTitle"] = profile["job_title"]
    if profile.get("same_as"):
        person["sameAs"] = list(profile["same_as"])
    return person


def upload_date(info: dict) -> str:
    ts = info.get("timestamp") or info.get("release_timestamp")
    if ts:
        try:
            return dt.datetime.fromtimestamp(int(ts), tz=dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        except (TypeError, ValueError, OverflowError, OSError):
            pass
    return common.upload_date_to_iso(info.get("upload_date"))


def build_video_object(info: dict, video_id: str, page_url: str, rights: str, person: dict | None) -> tuple[dict, list[str]]:
    warnings: list[str] = []
    node: dict = {"@type": "VideoObject"}
    if page_url:
        node["@id"] = f"{page_url}#video"
    node["name"] = str(info.get("title") or video_id)
    description = re.sub(r"\s+", " ", str(info.get("description") or "")).strip()[:200]
    if description:
        node["description"] = description
    if info.get("thumbnail"):
        node["thumbnailUrl"] = str(info["thumbnail"])
    else:
        warnings.append("video.info.json has no thumbnail field; thumbnailUrl omitted (never guessed)")
    when = upload_date(info)
    if when:
        node["uploadDate"] = when
    else:
        warnings.append("no timestamp or upload_date in video.info.json; uploadDate omitted")
    if info.get("duration"):
        node["duration"] = common.iso_duration(float(info["duration"]))
    node["embedUrl"] = f"https://www.youtube-nocookie.com/embed/{video_id}"
    node["url"] = common.watch_url(video_id)
    if page_url:
        node["isPartOf"] = {"@id": f"{page_url}#article"}
    channel = str(info.get("channel") or info.get("uploader") or "").strip()
    channel_url = str(info.get("channel_url") or "").strip()
    if rights == "own" and person is not None:
        node["creator"] = {"@id": person["@id"]} if person.get("@id") else {"@type": "Person", "name": person["name"]}
    elif channel:
        org: dict = {"@type": "Organization", "name": channel}
        if channel_url:
            org["url"] = channel_url
        node["creator"] = org
    else:
        warnings.append("no channel in video.info.json; creator omitted")
    return node, warnings


def format_chapter_time(seconds: float) -> str:
    s = int(round(float(seconds)))
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    return f"{h}:{m:02d}:{sec:02d}" if h else f"{m:02d}:{sec:02d}"


def chapter_lines(chapters: list) -> tuple[list[str], str]:
    """Validate YouTube chapter rules; return (lines, warning)."""
    items: list[tuple[float, str]] = []
    for ch in chapters or []:
        if not isinstance(ch, dict):
            continue
        start = ch.get("start_s", ch.get("start_time"))
        title = re.sub(r"\s+", " ", str(ch.get("title") or "")).strip()
        if start is None or not title:
            continue
        try:
            items.append((float(start), title))
        except (TypeError, ValueError):
            continue
    if len(items) < MIN_CHAPTERS:
        return [], f"only {len(items)} usable chapter(s); YouTube needs at least {MIN_CHAPTERS}, file skipped"
    if items[0][0] != 0:
        return [], "first chapter does not start at 00:00; file skipped"
    for (a, _), (b, _) in zip(items, items[1:]):
        if b <= a:
            return [], "chapters are not ascending; file skipped"
        if b - a < MIN_CHAPTER_GAP_S:
            return [], f"a chapter is shorter than {MIN_CHAPTER_GAP_S} seconds; file skipped"
    return [f"{format_chapter_time(t)} {title}" for t, title in items], ""


def embed_html(video_id: str, info: dict) -> str:
    title = html.escape(str(info.get("title") or video_id), quote=True)
    channel = html.escape(str(info.get("channel") or info.get("uploader") or "the creator"), quote=True)
    channel_url = str(info.get("channel_url") or "").strip()
    channel_html = f'<a href="{html.escape(channel_url, quote=True)}">{channel}</a>' if channel_url else channel
    published = common.upload_date_to_iso(info.get("upload_date")) or upload_date(info)[:10] or "date unknown"
    return EMBED_TEMPLATE.format(video_id=video_id, title=title, watch=common.watch_url(video_id),
                                 channel_html=channel_html, published=published)


def readme_text(slug: str, files: list[str], rights: str, page_url: str, chapters_written: bool) -> str:
    lines = [
        f"Publish kit for {slug}",
        "",
        "Files:",
    ]
    for f in files:
        lines.append(f"  {f}")
    lines += [
        "",
        "How to use:",
        "  1. Upload hero.jpg and the images/ folder next to the post, keeping the relative paths.",
        f"  2. Paste {slug}.publish.md (or its rendered HTML) into the CMS. It already contains the",
        "     embed figure and the converted image layouts.",
        "  3. Add layouts.css to the site stylesheet once (it styles .yt2b-layout and .video-embed).",
        "  4. Add the VideoObject from video-object.jsonld to the live page's JSON-LD graph and add",
        f'     "video": {{"@id": "{page_url or "<canonical>"}#video"}} to the BlogPosting node, only on the page',
        "     that renders the player. The preview HTML in this folder has no player, so its graph",
        "     holds BlogPosting and Person only.",
        "  5. embed.html is the same figure on its own, for a manual paste.",
    ]
    if rights == "own":
        lines.append("  6. youtube-chapters.txt: paste into the YouTube description so the video gets key moments."
                     if chapters_written else
                     "  6. youtube-chapters.txt was not written (fewer than three valid chapters in the brief).")
    lines += [
        "",
        "Rules kept by this kit: no youtu.be links, deep links use www.youtube.com/watch?v=ID&t=NNs,",
        "the embed uses www.youtube-nocookie.com with referrerpolicy strict-origin-when-cross-origin,",
        "thumbnailUrl comes from the video metadata and is never assembled by hand.",
    ]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--vault", help="Vault root (default: auto-detect)")
    parser.add_argument("--run", required=True, help="Run folder (02 Videos/<run>)")
    parser.add_argument("--blog", required=True, help="Blog folder (03 Blogs/<blog>)")
    args = parser.parse_args(argv)

    try:
        vault = Path(args.vault).expanduser().resolve() if args.vault else common.find_vault_root()
    except FileNotFoundError as exc:
        return common.fail(common.EXIT_INPUT, str(exc))
    run_dir = Path(args.run).expanduser().resolve()
    blog_dir = Path(args.blog).expanduser().resolve()
    if not run_dir.is_dir():
        return common.fail(common.EXIT_INPUT, f"run dir not found: {run_dir}")
    if not blog_dir.is_dir():
        return common.fail(common.EXIT_INPUT, f"blog dir not found: {blog_dir}")
    md_path = blog_markdown(blog_dir)
    if md_path is None:
        return common.fail(common.EXIT_INPUT, f"expected exactly one post markdown (besides review.md) in {blog_dir}")
    fm, md_body = common.read_note(md_path)
    slug = str(fm.get("slug") or md_path.stem)
    html_path = blog_dir / f"{slug}.html"
    if not html_path.is_file():
        return common.fail(common.EXIT_INPUT, f"rendered html not found: {html_path} (run blog_render.py first)")
    info_path = run_dir / "source" / "video.info.json"
    info = common.json_load(info_path, None)
    if not isinstance(info, dict):
        return common.fail(common.EXIT_INPUT, f"video metadata not found: {info_path}")

    warnings: list[str] = []
    run_fm = note_frontmatter(run_dir / "run.md")
    video_id = str(run_fm.get("video_id") or info.get("id") or run_dir.name.rsplit("-", 1)[-1])
    rights = fm.get("yt2b_rights") if fm.get("yt2b_rights") in common.RIGHTS else run_fm.get("rights")
    rights = rights if rights in common.RIGHTS else "third-party"
    settings = common.load_settings(vault)
    site = str(settings.get("site_url") or "").strip().rstrip("/")
    canonical = str(fm.get("canonical") or "").strip()
    page_url = canonical or (f"{site}/{slug}/" if site else "")
    if not page_url:
        warnings.append("no canonical in the post and no site_url in Settings; @id values omitted")

    html_text = html_path.read_text(encoding="utf-8")
    posting, block_count = find_blogposting(html_text)
    if posting is None:
        return common.fail(common.EXIT_INPUT, "no BlogPosting JSON-LD node in the rendered html")
    posting = {k: v for k, v in posting.items() if k != "@context"}
    if page_url:
        posting["@id"] = f"{page_url}#article"
    person = build_person(settings, author_profile(vault), page_url)
    if person is not None and rights == "own" and info.get("channel_url"):
        # In own mode the creator is the author, so the channel is a verified profile of the Person.
        same_as = [s for s in person.get("sameAs", []) if s]
        if info["channel_url"] not in same_as:
            same_as.append(info["channel_url"])
        person["sameAs"] = same_as
    graph = [posting]
    if person is not None:
        if person.get("@id"):
            posting["author"] = {"@id": person["@id"]}
        graph.append(person)
    graph_json = serialize_ld({"@context": "https://schema.org", "@graph": graph})
    html_text = replace_json_ld(html_text, graph_json)

    uses_layouts = "yt2b-layout" in html_text or "video-embed" in html_text
    html_text = set_style(html_text, LAYOUT_CSS if uses_layouts else None)
    html_text, images_enhanced = enhance_images(html_text, blog_dir)
    html_path.write_text(html_text, encoding="utf-8")

    video_object, vo_warnings = build_video_object(info, video_id, page_url, rights, person)
    warnings.extend(vo_warnings)
    embed_present = bool(EMBED_RE.search(md_body))
    if not embed_present:
        warnings.append("the post has no video-embed figure (youtube-nocookie.com/embed); see companion-rules.md")

    kit = common.ensure_dir(blog_dir / "publish-kit")
    written: list[Path] = []
    p = kit / "video-object.jsonld"
    p.write_text(json.dumps({"@context": "https://schema.org", **video_object}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    written.append(p)
    p = kit / "embed.html"
    p.write_text(embed_html(video_id, info), encoding="utf-8")
    written.append(p)
    p = kit / "layouts.css"
    p.write_text(LAYOUT_CSS, encoding="utf-8")
    written.append(p)
    layout_convert = common.load_module(Path(__file__).resolve().parent / "layout_convert.py", "yt2b_layout_convert")
    converted, _n, lc_warnings = layout_convert.convert_to_html(md_path.read_text(encoding="utf-8"), blog_dir)
    warnings.extend(lc_warnings)
    p = kit / f"{slug}.publish.md"
    p.write_text(converted, encoding="utf-8")
    common.update_note(p, {"binder-compile": False})
    written.append(p)
    chapters_written = False
    if rights == "own":
        brief = common.json_load(run_dir / "brief" / "video-brief.json", {}) or {}
        chapters = brief.get("chapters") if isinstance(brief, dict) and brief.get("chapters") else info.get("chapters")
        lines, warning = chapter_lines(chapters or [])
        if warning:
            warnings.append(f"youtube-chapters.txt: {warning}")
            stale = kit / "youtube-chapters.txt"
            if stale.exists():
                warnings.append("existing youtube-chapters.txt preserved because it may contain human edits")
        else:
            p = kit / "youtube-chapters.txt"
            p.write_text("\n".join(lines) + "\n", encoding="utf-8")
            written.append(p)
            chapters_written = True
    names = [w.name for w in written] + ["README.txt"]
    p = kit / "README.txt"
    p.write_text(readme_text(slug, names, rights, page_url, chapters_written), encoding="utf-8")
    written.append(p)

    for w in warnings:
        common.warn(w)
    common.emit({
        "html": str(html_path),
        "schema_nodes": len(graph),
        "person": person is not None,
        "embed_present": embed_present,
        "layout_css_injected": uses_layouts,
        "images_enhanced": images_enhanced,
        "ld_blocks_replaced": block_count,
        "publish_kit": [str(w) for w in written],
        "warnings": warnings,
    })
    return common.EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
