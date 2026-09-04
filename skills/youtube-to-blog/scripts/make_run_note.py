#!/usr/bin/env python3
"""Create or update a video run note (02 Videos/<run>/run.md).

Usage:
    make_run_note.py [--vault PATH] --run RUN_DIR [--status S] [--set key=value ...]
                     [--add-blog BLOG_DIR] [--summary FILE] [--takeaways FILE]
                     [--tags "a,b"] [--log TEXT] [--from-brief [JSON]]

Video fields come from <run>/source/video.info.json. The body keeps the sections
Video (embedded player, thumbnail, facts line, chapters), Summary, Key takeaways,
Tags, Frames (an Image Layouts gallery of every extracted frame), Blogs (hero and
image gallery per registered blog), Artifacts (links to the files that exist) and
Log (one bullet per stage, never duplicated). Video, Frames, Blogs and Artifacts
are regenerated on every run; Summary, Key takeaways and Tags only when given;
sections the script does not own are kept after Log. --from-brief reads summary,
key_takeaways (or takeaways) and tags from <run>/brief/video-brief.json (or the
given file) so the brief stage needs no extra shell commands. Prints {ok, run_note, status}.
Exit 0 ok, 1 failure, 2 invalid input.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import yt2b_common as common  # noqa: E402
import contract  # noqa: E402

SECTIONS = ("Video", "Summary", "Key takeaways", "Tags", "Frames", "Blogs", "Approvals", "Artifacts", "Log")
FIELD_ORDER = ("type", "video_id", "video_url", "title", "channel", "channel_url", "published", "duration_s",
               "rights", "mode", "status", "captions", "thumbnail", "frames", "hero", "blogs", "queue",
               "approvals", "created", "updated", "tags")
IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".webp", ".gif")


def run_tags(status: str, rights: str) -> list[str]:
    """Structural tags for a pipeline run."""
    stage = status if status in common.VIDEO_STATUSES else "fetched"
    tags = ["yt2b", f"stage/{stage}", "format/video", "source/youtube"]
    if rights in common.RIGHTS:
        tags.append(f"rights/{rights}")
    return tags


def resolve_run(vault: Path, run_dir: str) -> Path:
    path = Path(run_dir).expanduser()
    return (path if path.is_absolute() else vault / path).resolve()


def info_fields(run_dir: Path) -> dict:
    """Video fields for the frontmatter, read from source/video.info.json."""
    info = common.json_load(run_dir / "source" / "video.info.json", {}) or {}
    video_id = info.get("id") or run_dir.name.rsplit("-", 1)[-1]
    return {
        "video_id": video_id,
        "video_url": common.watch_url(video_id),
        "title": info.get("title", ""),
        "channel": info.get("channel") or info.get("uploader") or "",
        "channel_url": info.get("channel_url", ""),
        "published": common.upload_date_to_iso(info.get("upload_date")),
        "duration_s": int(info.get("duration") or 0),
    }


def default_frontmatter(run_dir: Path) -> dict:
    fm = {"type": common.NOTE_TYPES["video"]}
    fm.update(info_fields(run_dir))
    fm.update({"rights": "", "mode": "", "status": "fetched", "captions": "none", "blogs": [], "queue": "",
               "created": common.today(), "updated": common.today(), "tags": run_tags("fetched", "")})
    return fm


def ordered(fm: dict) -> dict:
    out = {key: fm[key] for key in FIELD_ORDER if key in fm}
    out.update({k: v for k, v in fm.items() if k not in out})
    return out


def blog_link(vault: Path, blog_dir: Path) -> str:
    """Wikilink to the post inside a blog folder (the single .md besides review.md)."""
    posts = [p for p in blog_dir.glob("*.md") if p.name != "review.md"]
    stem = posts[0].stem if posts else blog_dir.name.split(" ", 1)[-1]
    return common.wikilink(f"{common.rel(blog_dir, vault)}/{stem}.md", stem)


def artifacts(vault: Path, run_dir: Path, fm: dict) -> str:
    """Links to the artifacts that exist right now."""
    lines = []
    run_rel = common.rel(run_dir, vault)
    if (run_dir / "analysis" / "transcript.md").is_file():
        lines.append(f"- Transcript: {common.wikilink(run_rel + '/analysis/transcript.md', 'transcript')}")
    for brief in sorted((run_dir / "brief").glob("*-brief.md")) if (run_dir / "brief").is_dir() else []:
        lines.append(f"- Brief: {common.wikilink(run_rel + '/brief/' + brief.name, brief.stem)}")
    if (run_dir / "strategy.md").is_file():
        lines.append(f"- Strategy: {common.wikilink(run_rel + '/strategy.md', 'strategy')}")
    for link in fm.get("blogs") or []:
        lines.append(f"- Blog: {link}")
        slug = str(link).split("|")[-1].rstrip("]")
        evals = vault / common.ROOMS["evaluations"]
        for note in sorted(evals.glob(f"*-{slug}.md")) if evals.is_dir() else []:
            lines.append(f"- Evaluation: {common.wikilink(common.rel(note, vault), note.stem)}")
    return "\n".join(lines) if lines else "- (none yet)"


def approvals_section(vault: Path, run_dir: Path) -> tuple[list[str], str]:
    """Return approval wikilinks and a readable status list for this run."""
    links: list[str] = []
    lines: list[str] = []
    for note, approval_fm, _body in contract.approval_notes(vault, run_dir):
        link = common.wikilink(common.rel(note, vault), note.stem)
        links.append(link)
        kind = str(approval_fm.get("kind") or "approval")
        status = str(approval_fm.get("status") or "requested")
        lines.append(f"- {link}: {kind}, {status}")
    return links, "\n".join(lines) if lines else "- (none yet)"


def md_path(path: str) -> str:
    """A path usable inside a markdown link destination (spaces encoded, nothing else touched)."""
    return path.replace(" ", "%20")


def alt_text(text: str) -> str:
    """Alt text safe inside ![...](...)."""
    return " ".join(str(text).replace("[", "(").replace("]", ")").split())


def frames_dir(run_dir: Path) -> Path | None:
    """The video-analyzer frames folder (analysis/avt_outputs/<id>/frames) when it holds images."""
    root = run_dir / "analysis" / "avt_outputs"
    if not root.is_dir():
        return None
    for folder in sorted(p for p in root.iterdir() if p.is_dir()):
        frames = folder / "frames"
        if frames.is_dir() and list_images(frames):
            return frames
    return None


def list_images(folder: Path) -> list[Path]:
    return sorted(p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTS)


def layout_block(layout: str, options: dict) -> str:
    """An Image Layouts fenced block that fills itself from a folder (fromFolder option)."""
    lines = [f"```{layout}", "---"]
    lines.extend(f"{key}: {value}" for key, value in options.items())
    lines.extend(["---", "```"])
    return "\n".join(lines)


def chapters_callout(run_dir: Path, video_id: str) -> str:
    """A tip callout with deep links to every chapter in analysis/segments.json (empty when none)."""
    data = common.json_load(run_dir / "analysis" / "segments.json", {}) or {}
    chapters = [c for c in (data.get("chapters") or []) if isinstance(c, dict) and c.get("title")]
    if not chapters:
        return ""
    lines = ["> [!tip] Chapters"]
    for chapter in chapters:
        start = float(chapter.get("start_s") or 0)
        lines.append(f"> - [{common.seconds_to_mmss(start)}]({common.watch_url(video_id, start)}) {str(chapter['title']).strip()}")
    return "\n".join(lines)


def video_section(run_dir: Path, fm: dict) -> str:
    """Native player, thumbnail, one facts line and the chapters callout."""
    video_id = fm.get("video_id") or run_dir.name.rsplit("-", 1)[-1]
    title = str(fm.get("title") or video_id)
    watch = common.watch_url(video_id)
    parts = [f"![]({watch})"]
    if (run_dir / "source" / "thumbnail.jpg").is_file():
        parts.append(f"![Thumbnail of {alt_text(title)}](source/thumbnail.jpg)")
    channel = str(fm.get("channel") or "").strip()
    channel_url = str(fm.get("channel_url") or "").strip()
    facts = [f"[{channel}]({channel_url})" if channel and channel_url else (channel or "Unknown channel")]
    if fm.get("published"):
        facts.append(f"published {fm['published']}")
    if fm.get("duration_s"):
        facts.append(f"duration {common.seconds_to_mmss(fm['duration_s'])}")
    facts.append(f"captions {fm.get('captions') or 'none'}")
    parts.append(", ".join(facts) + f". [Watch on YouTube]({watch})")
    callout = chapters_callout(run_dir, video_id)
    if callout:
        parts.append(callout)
    return "\n\n".join(parts)


def frames_section(vault: Path, run_dir: Path, count: int) -> str:
    """Masonry gallery of every extracted frame plus the transcript link (or a note that none exist yet)."""
    folder = frames_dir(run_dir)
    if folder is None or not count:
        return "- (no frames extracted yet)"
    block = layout_block("image-layout-masonry-4", {
        "fromFolder": common.rel(folder, vault),
        "sortBy": "name",
        "caption": f"{count} frames extracted by video-analyzer (512 px, one per visual segment)",
    })
    transcript = run_dir / "analysis" / "transcript.md"
    if transcript.is_file():
        link = common.wikilink(common.rel(transcript, vault), "transcript")
        note = f"Every frame sits next to its segment in the {link} note."
    else:
        note = f"The frames live in `{common.rel(folder, vault)}`; the transcript note is written by build_segments.py."
    return block + "\n\n" + note


def blog_dir_from_link(vault: Path, link: str) -> Path | None:
    """Resolve a blogs wikilink ([[03 Blogs/<dir>/<slug>|<slug>]]) to the blog folder."""
    inner = str(link).strip().lstrip("[").rstrip("]").split("|")[0]
    if not inner:
        return None
    folder = (vault / inner).parent
    return folder if folder.is_dir() else None


def blog_title(blog_dir: Path, fallback: str) -> str:
    posts = [p for p in blog_dir.glob("*.md") if p.name != "review.md"]
    for post in posts:
        try:
            fm, _ = common.read_note(post)
        except Exception:
            continue
        if fm.get("title"):
            return str(fm["title"])
    return fallback


def hero_path(blog_dir: Path) -> Path | None:
    for name in ("hero.jpg", "hero.png"):
        if (blog_dir / name).is_file():
            return blog_dir / name
    return None


def blogs_section(vault: Path, fm: dict) -> str:
    """Per registered blog: title wikilink, hero image and a masonry gallery of its images folder."""
    parts = []
    for link in fm.get("blogs") or []:
        slug = str(link).split("|")[-1].rstrip("]")
        inner = str(link).strip().lstrip("[").rstrip("]").split("|")[0]
        blog_dir = blog_dir_from_link(vault, link)
        if blog_dir is None:
            parts.append(f"**{common.wikilink(inner, slug)}**")
            continue
        blog_rel = common.rel(blog_dir, vault)
        lines = [f"**{common.wikilink(inner, blog_title(blog_dir, slug))}**"]
        hero = hero_path(blog_dir)
        if hero is not None:
            lines.append(f"![hero]({md_path(blog_rel + '/' + hero.name)})")
        images = blog_dir / "images"
        if images.is_dir() and list_images(images):
            lines.append(layout_block("image-layout-masonry-3", {
                "fromFolder": blog_rel + "/images",
                "limit": 12,
                "caption": f"Frames used in {slug}",
            }))
        parts.append("\n\n".join(lines))
    return "\n\n".join(parts)


def media_fields(vault: Path, run_dir: Path, fm: dict) -> dict:
    """thumbnail, frames and hero properties (hero only when the first blog has one)."""
    thumb = run_dir / "source" / "thumbnail.jpg"
    folder = frames_dir(run_dir)
    out = {
        "thumbnail": common.rel(thumb, vault) if thumb.is_file() else "",
        "frames": len(list_images(folder)) if folder else 0,
    }
    for link in fm.get("blogs") or []:
        blog_dir = blog_dir_from_link(vault, link)
        hero = hero_path(blog_dir) if blog_dir else None
        if hero is not None:
            out["hero"] = common.rel(hero, vault)
        break
    return out


def merge_sections(existing: list[tuple[str, str]], updates: dict) -> list[tuple[str, str]]:
    """Keep the canonical order, apply updates, preserve unknown sections at the end."""
    current = dict(existing)
    current.update(updates)
    merged = [(name, current.get(name, "")) for name in SECTIONS if not (name == "Blogs" and not current.get("Blogs"))]
    merged.extend((name, text) for name, text in existing if name not in SECTIONS)
    return merged


def append_log(existing: str, text: str) -> str:
    lines = [ln for ln in existing.splitlines() if ln.strip()]
    if any(ln.split(" ", 2)[-1] == text for ln in lines):
        return "\n".join(lines)
    lines.append(f"- {common.now_iso()} {text}")
    return "\n".join(lines)


def tags_line(tags: str) -> str:
    items = [common.slugify(t, 40) for t in tags.split(",") if t.strip()]
    return " ".join(f"#{t}" for t in items)


def read_file(path: str | None) -> str | None:
    return Path(path).read_text(encoding="utf-8").strip() if path else None


def update_run_note(vault: Path, run_dir: Path, status: str | None = None, sets: dict | None = None,
                    add_blog: Path | None = None, summary: str | None = None, takeaways: str | None = None,
                    tags: str | None = None, log: str | None = None) -> Path:
    """Apply every requested change to run.md and return its path."""
    note = run_dir / "run.md"
    if note.is_file():
        fm, body = common.read_note(note)
        for key, value in info_fields(run_dir).items():
            fm.setdefault(key, value)
    else:
        fm, body = default_frontmatter(run_dir), ""
    if status:
        if status not in common.VIDEO_STATUSES:
            raise ValueError(f"status must be one of {', '.join(common.VIDEO_STATUSES)}")
        fm["status"] = status
    for key, value in (sets or {}).items():
        fm[key] = value
    fm["tags"] = run_tags(str(fm.get("status") or "fetched"), str(fm.get("rights") or ""))
    if add_blog is not None:
        link = blog_link(vault, add_blog)
        blogs = list(fm.get("blogs") or [])
        if link not in blogs:
            blogs.append(link)
        fm["blogs"] = blogs
    approval_links, approval_text = approvals_section(vault, run_dir)
    fm["approvals"] = approval_links
    fm.update(media_fields(vault, run_dir, fm))
    fm["updated"] = common.today()
    preamble, sections = common.split_sections(body)
    updates: dict = {"Video": video_section(run_dir, fm), "Frames": frames_section(vault, run_dir, fm["frames"]),
                     "Blogs": blogs_section(vault, fm), "Approvals": approval_text}
    if summary is not None:
        updates["Summary"] = summary
    if takeaways is not None:
        updates["Key takeaways"] = takeaways
    if tags is not None:
        updates["Tags"] = tags_line(tags)
    updates["Artifacts"] = artifacts(vault, run_dir, fm)
    if log:
        updates["Log"] = append_log(dict(sections).get("Log", ""), log)
    merged = merge_sections(sections, updates)
    common.write_note(note, ordered(fm), common.join_sections(preamble, merged))
    return note


def brief_fields(run_dir: Path, brief_path: str | None) -> dict:
    """summary, takeaways and tags from the analyst's video-brief.json (missing keys are skipped)."""
    path = Path(brief_path).expanduser() if brief_path else run_dir / "brief" / "video-brief.json"
    data = common.json_load(path, None)
    if not isinstance(data, dict):
        raise FileNotFoundError(f"brief JSON not found or not an object: {path}")
    out: dict = {}
    if data.get("summary"):
        out["summary"] = str(data["summary"]).strip()
    takeaways = data.get("key_takeaways") or data.get("takeaways")
    if takeaways:
        items = takeaways if isinstance(takeaways, list) else [takeaways]
        out["takeaways"] = "\n".join(f"- {str(t).strip()}" for t in items)
    if data.get("tags"):
        tags = data["tags"] if isinstance(data["tags"], list) else [data["tags"]]
        out["tags"] = ",".join(str(t) for t in tags)
    return out


def parse_sets(pairs: list[str]) -> dict:
    out = {}
    for pair in pairs:
        if "=" not in pair:
            raise ValueError(f"--set expects key=value, got {pair!r}")
        key, value = pair.split("=", 1)
        out[key.strip()] = common.coerce_scalar(value)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create or update a video run note.")
    parser.add_argument("--vault")
    parser.add_argument("--run", required=True, help="Run folder (absolute or vault-relative)")
    parser.add_argument("--status", choices=common.VIDEO_STATUSES)
    parser.add_argument("--set", nargs="*", default=[], metavar="KEY=VALUE")
    parser.add_argument("--add-blog", help="Blog folder to register in the blogs list")
    parser.add_argument("--summary", help="File whose text becomes the Summary section")
    parser.add_argument("--takeaways", help="File whose text becomes the Key takeaways section")
    parser.add_argument("--tags", help="Comma separated tags for the Tags section")
    parser.add_argument("--log", help="Log line to append (stage: detail)")
    parser.add_argument("--from-brief", nargs="?", const="", metavar="JSON", help="Fill Summary, Key takeaways and Tags from video-brief.json")
    args = parser.parse_args(argv)
    try:
        vault = Path(args.vault).expanduser().resolve() if args.vault else common.find_vault_root()
        run_dir = resolve_run(vault, args.run)
        if not run_dir.is_dir():
            return common.fail(common.EXIT_INPUT, f"run folder not found: {run_dir}")
        add_blog = resolve_run(vault, args.add_blog) if args.add_blog else None
        summary, takeaways, tags = read_file(args.summary), read_file(args.takeaways), args.tags
        if args.from_brief is not None:
            fields = brief_fields(run_dir, args.from_brief or None)
            summary, takeaways, tags = fields.get("summary", summary), fields.get("takeaways", takeaways), fields.get("tags", tags)
        note = update_run_note(vault, run_dir, args.status, parse_sets(args.set), add_blog, summary, takeaways, tags, args.log)
    except (FileNotFoundError, ValueError) as exc:
        return common.fail(common.EXIT_INPUT, str(exc))
    fm, _ = common.read_note(note)
    common.emit({"ok": True, "run_note": str(note), "status": fm.get("status", "")})
    return common.EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
