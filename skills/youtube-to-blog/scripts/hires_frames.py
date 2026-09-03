#!/usr/bin/env python3
"""Extract publish-quality frames for one blog from the cached video.

Reads the key moments from <run>/brief/video-brief.json (or --moments), keeps
the moments that belong to this blog, caps the count by rights, extracts each
with ffmpeg at the configured width into <blog>/images/, copies the thumbnail
to images/video-thumb.jpg, writes images/CREDITS.txt and, in own mode, a
1200x630 hero.jpg plus hero-credit.txt. The manifest is printed and saved to
<blog>/images/manifest.json.

With --delete-video the cached file under .cache/video is removed after a
successful extraction (the orchestrator passes it on the last approved blog
when Settings keep_video is false).

A key moment may carry a `crop` object (normalized x, y, w, h plus a reason
and an optional keep_aspect) decided by the analyst. A valid crop is applied
in the same ffmpeg command as the extraction (crop, then scale to the target
width, pixel values rounded to even numbers); an invalid crop is skipped with
a warning and the full frame is extracted. --no-crop ignores every crop. The
crop, its reason and the source and output sizes land in the manifest and the
reason in CREDITS.txt. A frame is re-extracted when its crop changed since the
last run.

Requires ffmpeg. ffprobe (ships with ffmpeg) reads the source size; without it
the crop is expressed relative to the input size and keep_aspect is ignored.
PIL is optional: it resizes the thumbnail, crops the hero and reads output
sizes; without PIL the thumbnail is copied as is and ffmpeg crops the hero.

Exit codes: 0 ok, 1 failure, 2 invalid input, 4 ffmpeg missing, 5 ffmpeg failed.
"""
from __future__ import annotations

import argparse
import math
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import yt2b_common as common  # noqa: E402

HERO_SIZE = (1200, 630)
THUMB_WIDTH = 1280
VIDEO_EXTS = (".mp4", ".mkv", ".webm", ".mov", ".m4v")
THUMB_EXTS = (".jpg", ".jpeg", ".png", ".webp")
FFMPEG_TIMEOUT = 120
PROBE_TIMEOUT = 30
CROP_MIN_FRACTION = 0.45
CROP_MIN_REASON_WORDS = 8
CROP_ASPECTS = {"16:9": 16 / 9, "4:3": 4 / 3, "free": None}


# ---------------------------------------------------------------------------
# Local helpers
# ---------------------------------------------------------------------------

def blog_markdown(blog_dir: Path) -> Path | None:
    mds = sorted(p for p in blog_dir.glob("*.md") if p.name != "review.md")
    return mds[0] if len(mds) == 1 else None


def blog_slug(blog_dir: Path) -> str:
    md = blog_markdown(blog_dir)
    if md is not None:
        fm, _ = common.read_note(md)
        return str(fm.get("slug") or md.stem)
    m = re.match(r"^\d{4}-\d{2}-\d{2}\s+(.+)$", blog_dir.name)
    return m.group(1) if m else blog_dir.name


def note_frontmatter(path: Path | None) -> dict:
    if path is None or not path.is_file():
        return {}
    fm, _ = common.read_note(path)
    return fm


def resolve_rights(blog_fm: dict, run_fm: dict) -> str:
    for candidate in (blog_fm.get("yt2b_rights"), run_fm.get("rights")):
        if candidate in common.RIGHTS:
            return str(candidate)
    common.warn("rights unset or 'ask': applying the third-party caps and no hero")
    return "third-party"


def video_id_for_run(run_dir: Path, run_fm: dict, info: dict) -> str:
    if run_fm.get("video_id"):
        return str(run_fm["video_id"])
    if info.get("id"):
        return str(info["id"])
    return run_dir.name.rsplit("-", 1)[-1]


def find_video(vault: Path, video_id: str, explicit: str | None) -> Path | None:
    if explicit:
        p = Path(explicit).expanduser()
        return p if p.is_file() else None
    cache = vault / common.CACHE_DIR
    for ext in VIDEO_EXTS:
        p = cache / f"{video_id}{ext}"
        if p.is_file():
            return p
    hits = sorted(p for p in cache.glob(f"{video_id}.*") if p.is_file())
    return hits[0] if hits else None


def find_thumbnail(run_dir: Path) -> Path | None:
    for ext in THUMB_EXTS:
        p = run_dir / "source" / f"thumbnail{ext}"
        if p.is_file():
            return p
    return None


def existing_hero(blog_dir: Path) -> Path | None:
    for ext in ("jpg", "jpeg", "png", "webp"):
        p = blog_dir / f"hero.{ext}"
        if p.is_file():
            return p
    return None


def mmss_tag(t_s: float) -> str:
    s = int(round(float(t_s)))
    m, sec = divmod(s, 60)
    return f"{m:02d}{sec:02d}"


def moment_matches_blog(moment: dict, slug: str, extra: tuple[str, ...] = ()) -> bool:
    """True when the moment is unassigned or assigned to this blog.

    `blog` may hold the blog slug, the strategist's angle id (blog-1) or the
    strategist's own slug; `extra` carries those aliases (--match).
    """
    wanted = {slug, *[e.strip() for e in extra if e and e.strip()]}
    blog = moment.get("blog")
    if not blog:
        return True
    if isinstance(blog, str):
        return blog.strip() in wanted
    if isinstance(blog, (list, tuple)):
        return any(str(b).strip() in wanted for b in blog)
    return True


def select_moments(moments: list, slug: str, cap: int, extra: tuple[str, ...] = ()) -> tuple[list[dict], int]:
    keep = [m for m in moments if isinstance(m, dict) and m.get("t_s") is not None
            and moment_matches_blog(m, slug, extra)]
    keep.sort(key=lambda m: (int(m.get("priority") or 99), float(m["t_s"])))
    selected = keep[:cap]
    skipped = len(keep) - len(selected)
    selected.sort(key=lambda m: float(m["t_s"]))
    return selected, skipped


def validate_crop(crop) -> tuple[dict | None, str]:
    """Return (normalized crop, "") for a usable crop, (None, "") when absent, (None, problem) when invalid.

    Rules: numeric x, y, w, h as fractions of the source inside 0 to 1, at
    least CROP_MIN_FRACTION of the width and of the height kept, a reason of
    at least CROP_MIN_REASON_WORDS words, keep_aspect one of CROP_ASPECTS.
    The editorial rules (no cut through referenced text, no removing a person
    from a talking-head frame) are the analyst's and are documented in
    references/brief-template.md.
    """
    if crop is None or crop == {} or crop is False:
        return None, ""
    if not isinstance(crop, dict):
        return None, "crop is not an object"
    try:
        x, y, w, h = (float(crop.get(k)) for k in ("x", "y", "w", "h"))
    except (TypeError, ValueError):
        return None, "crop needs numeric x, y, w and h"
    if not all(math.isfinite(v) for v in (x, y, w, h)):
        return None, "crop values must be finite"
    if x < 0 or y < 0 or w <= 0 or h <= 0 or x + w > 1.0001 or y + h > 1.0001:
        return None, "crop must stay inside the frame (fractions from 0 to 1)"
    if w < CROP_MIN_FRACTION or h < CROP_MIN_FRACTION:
        return None, (f"crop keeps {w:.0%} of the width and {h:.0%} of the height; "
                      f"at least {CROP_MIN_FRACTION:.0%} of each is required")
    reason = " ".join(str(crop.get("reason") or "").split())
    if len(reason.split()) < CROP_MIN_REASON_WORDS:
        return None, f"crop reason needs at least {CROP_MIN_REASON_WORDS} words naming what it keeps and why"
    aspect = str(crop.get("keep_aspect") or "free").strip()
    if aspect not in CROP_ASPECTS:
        return None, f"keep_aspect must be one of {', '.join(CROP_ASPECTS)}"
    return {"x": round(x, 4), "y": round(y, 4), "w": round(w, 4), "h": round(h, 4),
            "keep_aspect": aspect, "reason": reason}, ""


def _even(value: float) -> int:
    return max(2, int(value // 2) * 2)


def crop_pixels(crop: dict, source: tuple[int, int]) -> tuple[list[int] | None, str]:
    """Even pixel rectangle [w, h, x, y] for a validated crop on a source of the given size.

    keep_aspect widens or heightens the rectangle around its centre to the
    requested ratio, clamped to the frame; when that leaves less than
    CROP_MIN_FRACTION of a dimension the crop is rejected.
    """
    sw, sh = source
    x, y, w, h = crop["x"] * sw, crop["y"] * sh, crop["w"] * sw, crop["h"] * sh
    ratio = CROP_ASPECTS[crop["keep_aspect"]]
    if ratio:
        cx, cy = x + w / 2, y + h / 2
        if w / h < ratio:
            w = min(h * ratio, sw)
            h = w / ratio
        else:
            h = min(w / ratio, sh)
            w = h * ratio
        x = min(max(cx - w / 2, 0), sw - w)
        y = min(max(cy - h / 2, 0), sh - h)
        if w / sw < CROP_MIN_FRACTION - 1e-9 or h / sh < CROP_MIN_FRACTION - 1e-9:
            return None, f"keep_aspect {crop['keep_aspect']} leaves less than {CROP_MIN_FRACTION:.0%} of the frame"
    wp, hp = _even(w), _even(h)
    xp, yp = _even(x), _even(y)
    xp = min(xp, max(0, sw - wp))
    yp = min(yp, max(0, sh - hp))
    wp, hp = min(wp, sw - xp), min(hp, sh - yp)
    return [wp, hp, xp, yp], ""


def crop_filter(crop: dict | None, source: tuple[int, int] | None) -> tuple[str, list[int] | None, str]:
    """Return (ffmpeg crop filter or "", pixel rectangle or None, problem or "")."""
    if crop is None:
        return "", None, ""
    if source is None:
        if crop["keep_aspect"] != "free":
            common.warn(f"source size unknown (no ffprobe): keep_aspect {crop['keep_aspect']} ignored")
        expr = ",".join(f"2*floor({dim}*{val}/2)" for dim, val in
                        (("iw", crop["w"]), ("ih", crop["h"]), ("iw", crop["x"]), ("ih", crop["y"])))
        return f"crop={expr}", None, ""
    rect, problem = crop_pixels(crop, source)
    if rect is None:
        return "", None, problem
    return "crop={}:{}:{}:{}".format(*rect), rect, ""


def probe_size(ffprobe: str | None, path: Path) -> tuple[int, int] | None:
    if not ffprobe:
        return None
    cmd = [ffprobe, "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
           "-of", "csv=p=0", str(path)]
    try:
        proc = subprocess.run(cmd, check=True, timeout=PROBE_TIMEOUT, capture_output=True, text=True)
        parts = [p for p in proc.stdout.strip().splitlines()[0].split(",") if p.strip()]
        w, h = int(parts[0]), int(parts[1])
    except (subprocess.SubprocessError, OSError, ValueError, IndexError):
        return None
    return (w, h) if w > 0 and h > 0 else None


def image_size(path: Path, ffprobe: str | None) -> list[int] | None:
    try:
        from PIL import Image  # type: ignore
        with Image.open(path) as im:
            return [im.width, im.height]
    except ImportError:
        size = probe_size(ffprobe, path)
        return list(size) if size else None
    except OSError:
        return None


def extract_frame(ffmpeg: str, video: Path, t_s: float, width: int, out: Path, crop_vf: str = "") -> None:
    vf = f"{crop_vf},scale={int(width)}:-2" if crop_vf else f"scale={int(width)}:-2"
    cmd = [ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-ss", f"{float(t_s):.3f}", "-i", str(video),
           "-frames:v", "1", "-vf", vf, "-q:v", "2", str(out)]
    subprocess.run(cmd, check=True, timeout=FFMPEG_TIMEOUT, capture_output=True, text=True)
    if not out.is_file() or out.stat().st_size == 0:
        if out.exists():
            out.unlink()
        raise RuntimeError(f"no frame written at {t_s}s (past the end of the video?)")


def copy_thumbnail(src: Path, dst: Path) -> str:
    try:
        from PIL import Image  # type: ignore
    except ImportError:
        shutil.copyfile(src, dst)
        return "copy"
    with Image.open(src) as im:
        im = im.convert("RGB")
        if im.width > THUMB_WIDTH:
            im = im.resize((THUMB_WIDTH, max(1, round(im.height * THUMB_WIDTH / im.width))), Image.LANCZOS)
        im.save(dst, "JPEG", quality=88)
    return "pil"


def make_hero(ffmpeg: str | None, src: Path, dst: Path) -> str:
    try:
        from PIL import Image, ImageOps  # type: ignore
        with Image.open(src) as im:
            ImageOps.fit(im.convert("RGB"), HERO_SIZE, Image.LANCZOS, centering=(0.5, 0.5)).save(dst, "JPEG", quality=90)
        return "pil"
    except ImportError:
        pass
    if not ffmpeg:
        return ""
    cmd = [ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-i", str(src),
           "-vf", f"scale={HERO_SIZE[0]}:{HERO_SIZE[1]}:force_original_aspect_ratio=increase,crop={HERO_SIZE[0]}:{HERO_SIZE[1]}",
           "-frames:v", "1", "-q:v", "2", str(dst)]
    subprocess.run(cmd, check=True, timeout=FFMPEG_TIMEOUT, capture_output=True, text=True)
    return "ffmpeg"


def build_caption(label: str, mmss: str, rights: str, title: str, channel: str) -> str:
    if rights == "own":
        return f"{label} ({mmss})"
    return f'{label} ({mmss} in "{title}" by {channel})'


def credits_text(info: dict, video_id: str, rights: str, entries: list[dict], thumb: Path | None) -> str:
    title = info.get("title") or video_id
    channel = info.get("channel") or info.get("uploader") or "unknown channel"
    channel_url = info.get("channel_url") or ""
    lic = info.get("license") or "not stated (YouTube Standard License assumed)"
    lines = [
        f"Video: {title}",
        f"Channel: {channel}" + (f" ({channel_url})" if channel_url else ""),
        f"Watch: {common.watch_url(video_id)}",
        f"License: {lic}",
        f"Rights mode: {rights}",
        f"Retrieved: {common.today()}",
        "",
        "Frames (file, timestamp, deep link, label):",
    ]
    for e in entries:
        lines.append(f"{Path(e['path']).name}  {e['mmss']}  {e['url']}  {e['label']}")
        if e.get("crop"):
            lines.append(f"  cropped: {e['crop_reason']}")
    if thumb is not None:
        lines.append(f"{thumb.name}  thumbnail  {info.get('thumbnail') or 'source/thumbnail'}  Video thumbnail")
    if rights != "own":
        lines += ["", "Third-party frames are reproduced at reduced size for commentary and criticism.",
                  "Each frame carries a caption naming the video, the creator and the timestamp."]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--vault", help="Vault root (default: auto-detect)")
    parser.add_argument("--run", required=True, help="Run folder (02 Videos/<run>)")
    parser.add_argument("--blog", required=True, help="Blog folder (03 Blogs/<blog>)")
    parser.add_argument("--video", help="Video file (default: .cache/video/<id>.*)")
    parser.add_argument("--width", type=int, help="Frame width in pixels (default: Settings frame_width)")
    parser.add_argument("--moments", help="JSON file with key_moments (default: <run>/brief/video-brief.json)")
    parser.add_argument("--match", action="append", default=[],
                        help="extra id the moments' blog field may carry for this blog (angle id such as blog-1, "
                             "or the strategist's slug); repeatable")
    parser.add_argument("--force", action="store_true", help="Re-extract frames that already exist")
    parser.add_argument("--no-crop", action="store_true", help="Ignore the crop field of every moment (full frames)")
    parser.add_argument("--delete-video", action="store_true",
                        help="Delete the cached video (only inside .cache/video) after a successful extraction")
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

    info = common.json_load(run_dir / "source" / "video.info.json", {}) or {}
    run_fm = note_frontmatter(run_dir / "run.md")
    blog_fm = note_frontmatter(blog_markdown(blog_dir))
    video_id = video_id_for_run(run_dir, run_fm, info)
    slug = blog_slug(blog_dir)
    rights = resolve_rights(blog_fm, run_fm)
    settings = common.load_settings(vault)
    cap = int(settings["max_frames_own" if rights == "own" else "max_frames_third_party"])
    width = int(args.width or settings["frame_width"])

    moments_path = Path(args.moments).expanduser() if args.moments else run_dir / "brief" / "video-brief.json"
    if not moments_path.is_file():
        return common.fail(common.EXIT_INPUT, f"moments file not found: {moments_path}")
    data = common.json_load(moments_path, {})
    moments = data.get("key_moments") if isinstance(data, dict) else data
    if not isinstance(moments, list):
        return common.fail(common.EXIT_INPUT, f"no key_moments list in {moments_path}")
    selected, skipped = select_moments(moments, slug, cap, tuple(args.match or ()))
    if skipped:
        common.warn(f"{skipped} moment(s) dropped by the {rights} cap of {cap}")

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        return common.fail(common.EXIT_MISSING, "ffmpeg not found on PATH")
    video = find_video(vault, video_id, args.video)
    if selected and video is None:
        return common.fail(common.EXIT_INPUT, f"cached video for {video_id} not found (run fetch_video.py first or pass --video)")

    images_dir = common.ensure_dir(blog_dir / "images")
    ffprobe = shutil.which("ffprobe")
    source_size = probe_size(ffprobe, video) if video is not None else None
    if selected and source_size is None:
        common.warn("source size unknown (ffprobe missing or failed): crops use ffmpeg input-relative expressions")
    previous = common.json_load(images_dir / "manifest.json", {}) or {}
    previous_crops = {e.get("rel"): e.get("crop") for e in previous.get("images", []) if isinstance(e, dict)}
    title = info.get("title") or video_id
    channel = info.get("channel") or info.get("uploader") or "the creator"
    entries: list[dict] = []
    failures: list[str] = []
    crop_skipped: list[str] = []
    for index, moment in enumerate(selected, 1):
        t_s = float(moment["t_s"])
        label = str(moment.get("label") or f"Moment {index}").strip()
        name = f"{index:02d}-{common.slugify(label, 30)}-{mmss_tag(t_s)}.jpg"
        out = images_dir / name
        crop: dict | None = None
        crop_vf, crop_px = "", None
        if not args.no_crop:
            crop, problem = validate_crop(moment.get("crop"))
            if crop is not None:
                crop_vf, crop_px, problem = crop_filter(crop, source_size)
                if problem:
                    crop = None
            if problem:
                crop_skipped.append(f"{name}: {problem}")
                common.warn(f"crop skipped for {name}: {problem}; extracting the full frame")
        crop_stored = {k: crop[k] for k in ("x", "y", "w", "h", "keep_aspect")} if crop else None
        crop_changed = out.is_file() and previous_crops.get(f"images/{name}") != crop_stored
        status = "existing"
        if args.force or crop_changed or not out.is_file() or out.stat().st_size == 0:
            try:
                extract_frame(ffmpeg, video, t_s, width, out, crop_vf)
                status = "re-extracted" if crop_changed and not args.force else "extracted"
            except subprocess.CalledProcessError as exc:
                failures.append(f"{name}: ffmpeg exit {exc.returncode}: {(exc.stderr or '').strip()[:200]}")
                continue
            except (subprocess.TimeoutExpired, RuntimeError) as exc:
                failures.append(f"{name}: {exc}")
                continue
        mmss = common.seconds_to_mmss(t_s)
        entries.append({
            "path": str(out.resolve()),
            "rel": f"images/{name}",
            "alt": str(moment.get("alt") or label),
            "caption": build_caption(label, mmss, rights, title, channel),
            "t_s": t_s,
            "mmss": mmss,
            "url": common.watch_url(video_id, t_s),
            "label": label,
            "why": str(moment.get("why") or ""),
            "section": str(moment.get("section") or ""),
            "hero": bool(moment.get("hero")),
            "id": str(moment.get("id") or ""),
            "status": status,
            "crop": crop_stored,
            "crop_reason": crop["reason"] if crop else "",
            "crop_px": crop_px,
            "source_size": list(source_size) if source_size else None,
            "output_size": image_size(out, ffprobe),
        })

    thumb_src = find_thumbnail(run_dir)
    thumb_dst = images_dir / "video-thumb.jpg"
    thumb: Path | None = None
    if thumb_src is not None:
        if args.force or not thumb_dst.is_file():
            try:
                copy_thumbnail(thumb_src, thumb_dst)
            except Exception as exc:  # corrupt image: keep going
                common.warn(f"thumbnail copy failed: {exc}")
        if thumb_dst.is_file():
            thumb = thumb_dst
    else:
        common.warn("no source/thumbnail.* in the run folder; images/video-thumb.jpg not written")

    credits = images_dir / "CREDITS.txt"
    credits.write_text(credits_text(info, video_id, rights, entries, thumb), encoding="utf-8")

    hero: Path | None = existing_hero(blog_dir)
    hero_note = ""
    if rights == "own":
        if hero is not None:
            hero_note = f"kept existing {hero.name}"
        else:
            source: Path | None = None
            source_desc = ""
            for e in entries:
                if e["hero"]:
                    source, source_desc = Path(e["path"]), f"frame at {e['mmss']}"
                    break
            if source is None and thumb is not None:
                source, source_desc = thumb, "video thumbnail"
            if source is not None:
                dst = blog_dir / "hero.jpg"
                try:
                    method = make_hero(ffmpeg, source, dst)
                except subprocess.CalledProcessError as exc:
                    failures.append(f"hero: ffmpeg exit {exc.returncode}")
                    method = ""
                if method and dst.is_file():
                    hero = dst
                    (blog_dir / "hero-credit.txt").write_text(
                        f'Hero: {source_desc} from "{title}" by {channel} (own video). '
                        f"Source: {common.watch_url(video_id)}. Cropped to {HERO_SIZE[0]}x{HERO_SIZE[1]} "
                        f"by hires_frames.py ({method}) on {common.today()}.\n",
                        encoding="utf-8",
                    )
                    hero_note = f"written from {source_desc} ({method})"
            else:
                hero_note = "no hero source (no hero moment and no thumbnail)"
    else:
        hero_note = ("third-party mode: hero must come from Banana Claude or generate_hero.py, never the creator's thumbnail"
                     if hero is None else f"kept existing {hero.name}")

    video_deleted = False
    if args.delete_video and not failures and video is not None:
        cache_root = (vault / common.CACHE_DIR).resolve()
        try:
            video.resolve().relative_to(cache_root)
            video.unlink()
            video_deleted = True
        except ValueError:
            common.warn(f"not deleting {video}: outside {cache_root}")
        except OSError as exc:
            common.warn(f"could not delete {video}: {exc}")

    manifest = {
        "schema": common.SCHEMA_VERSION,
        "video_id": video_id,
        "slug": slug,
        "rights": rights,
        "cap": cap,
        "width": width,
        "images": entries,
        "thumb": str(thumb.resolve()) if thumb else None,
        "hero": str(hero.resolve()) if hero else None,
        "hero_note": hero_note,
        "credits": str(credits.resolve()),
        "skipped": skipped,
        "cropped": sum(1 for e in entries if e["crop"]),
        "crop_skipped": crop_skipped,
        "no_crop": bool(args.no_crop),
        "failures": failures,
        "video_deleted": video_deleted,
    }
    manifest_path = common.json_dump(images_dir / "manifest.json", manifest)
    manifest["manifest"] = str(manifest_path.resolve())
    for line in failures:
        common.warn(f"frame failure: {line}")
    common.emit(manifest)
    return common.EXIT_EXTERNAL if failures else common.EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
