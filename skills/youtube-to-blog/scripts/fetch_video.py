#!/usr/bin/env python3
"""Fetch a YouTube video into a run folder: metadata, captions, thumbnail, video file.

Usage:
    fetch_video.py [--vault PATH] URL [--rights R] [--mode M] [--lang en] [--max-height 1080]
                   [--force-long] [--queue NOTE_PATH]

Steps: validate the URL, read metadata with yt-dlp (no download), trim it to
source/video.info.json, enforce the duration and size guards, download manual
captions then automatic ones (kept as source/captions.<lang>.vtt), the largest
thumbnail (https only, 10 MB cap) and the video (mp4 up to --max-height) into
.cache/video/<id>.<ext>, then write run.md and mark the queue note running.
Re-running reuses the run folder and every file that already exists.
Prints one JSON object: {run_dir, video_id, title, channel, duration_s, video_path,
captions_path, captions_source, thumbnail_path, info_path, run_note, warnings}.
Exit 0 ok, 2 invalid URL, 3 policy limit, 4 yt-dlp missing, 5 yt-dlp or network failure.
No secrets are involved; every subprocess call is an argument list with a timeout.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import yt2b_common as common  # noqa: E402
import make_run_note  # noqa: E402

# queue.py shadows the standard library module of the same name, so load it by path.
queue_mod = common.load_module(Path(__file__).resolve().parent / "queue.py", "yt2b_queue")

META_TIMEOUT = 120
SUBS_TIMEOUT = 120
VIDEO_TIMEOUT = 1800
THUMB_TIMEOUT = 20
THUMB_CAP = 10 * 1024 * 1024
SIZE_CAP = 2 * 1024 ** 3
TRIM_KEYS = ("id", "title", "channel", "channel_id", "channel_url", "uploader", "uploader_url", "webpage_url",
             "upload_date", "timestamp", "release_timestamp", "duration", "description", "tags", "categories",
             "chapters", "view_count", "like_count", "thumbnail", "license", "language")
VIDEO_EXTS = (".mp4", ".mkv", ".webm", ".mov", ".m4v")


class FetchError(Exception):
    """Failure with the exit code the CLI should return."""

    def __init__(self, code: int, message: str) -> None:
        super().__init__(message)
        self.code = code


def run_ytdlp(args: list[str], timeout: int) -> subprocess.CompletedProcess:
    """Run yt-dlp with an argument list and a timeout (never a shell)."""
    try:
        return subprocess.run(["yt-dlp", *args], capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError as exc:
        raise FetchError(common.EXIT_MISSING, "yt-dlp is not installed or not on PATH") from exc
    except subprocess.TimeoutExpired as exc:
        raise FetchError(common.EXIT_EXTERNAL, f"yt-dlp timed out after {timeout}s ({args[0]})") from exc


def classify(stderr: str) -> str:
    text = stderr.lower()
    if "private" in text or "sign in" in text or "login" in text:
        return "video requires sign-in or is private"
    if "age" in text and "restrict" in text:
        return "video is age-restricted"
    if "not available" in text or "unavailable" in text:
        return "video is unavailable in this region or was removed"
    return "yt-dlp failed"


def fetch_metadata(url: str) -> dict:
    proc = run_ytdlp(["--dump-json", "--no-download", "--no-playlist", url], META_TIMEOUT)
    if proc.returncode != 0:
        tail = proc.stderr.strip().splitlines()[-1:] or [""]
        raise FetchError(common.EXIT_EXTERNAL, f"{classify(proc.stderr)}: {tail[0][:300]}")
    lines = [ln for ln in proc.stdout.splitlines() if ln.strip()]
    try:
        return json.loads(lines[0])
    except (IndexError, ValueError) as exc:
        raise FetchError(common.EXIT_EXTERNAL, "yt-dlp returned no metadata JSON") from exc


def trim_thumbnails(items) -> list[dict]:
    rows = [t for t in (items or []) if isinstance(t, dict) and str(t.get("url", "")).startswith("https://")]
    rows.sort(key=lambda t: (t.get("width") or 0) * (t.get("height") or 0), reverse=True)
    return [{"url": t.get("url"), "width": t.get("width"), "height": t.get("height")} for t in rows[:3]]


def trim_metadata(meta: dict) -> dict:
    """Keep only the documented keys; caption maps become language code lists."""
    info = {key: meta.get(key) for key in TRIM_KEYS}
    info["thumbnails"] = trim_thumbnails(meta.get("thumbnails"))
    info["subtitles"] = sorted((meta.get("subtitles") or {}).keys())
    info["automatic_captions"] = sorted((meta.get("automatic_captions") or {}).keys())
    return info


def estimate_size(meta: dict) -> int:
    """Best available byte estimate for the selected formats (0 when unknown)."""
    parts = meta.get("requested_formats") or []
    total = sum(int(p.get("filesize") or p.get("filesize_approx") or 0) for p in parts if isinstance(p, dict))
    return total or int(meta.get("filesize") or meta.get("filesize_approx") or 0)


def largest_thumbnail(meta: dict) -> str | None:
    """Largest https thumbnail URL, preferring JPEG over WebP."""
    rows = trim_thumbnails(meta.get("thumbnails"))
    if meta.get("thumbnail") and str(meta["thumbnail"]).startswith("https://"):
        rows.append({"url": meta["thumbnail"], "width": 0, "height": 0})
    if not rows:
        return None
    jpg = [r for r in rows if str(r["url"]).split("?")[0].lower().endswith((".jpg", ".jpeg"))]
    return (jpg or rows)[0]["url"]


def http_get(url: str, dest: Path, cap: int = THUMB_CAP, timeout: int = THUMB_TIMEOUT) -> None:
    """Download an https URL to dest with a size cap (tests replace this function)."""
    if not url.startswith("https://"):
        raise ValueError("only https downloads are allowed")
    request = urllib.request.Request(url, headers={"User-Agent": "youtube-to-blog/0.1"})
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 (https enforced above)
        data = response.read(cap + 1)
    if len(data) > cap:
        raise ValueError(f"thumbnail larger than {cap} bytes")
    dest.write_bytes(data)


def caption_files(source_dir: Path) -> list[Path]:
    return sorted(p for p in source_dir.glob("captions*.vtt") if p.is_file())


def normalise_captions(source_dir: Path, lang: str) -> Path | None:
    """Keep source/captions.<lang>.vtt, drop the identical -orig duplicate, rename other variants."""
    target = source_dir / f"captions.{lang}.vtt"
    files = caption_files(source_dir)
    if not files:
        return None
    if target not in files:
        preferred = sorted(files, key=lambda p: (not p.name.startswith(f"captions.{lang}-orig"), not p.name.startswith(f"captions.{lang}"), p.name))
        preferred[0].rename(target)
    orig = source_dir / f"captions.{lang}-orig.vtt"
    if orig.exists() and target.exists():
        orig.unlink()
    return target


def download_captions(url: str, source_dir: Path, lang: str) -> tuple[Path | None, str]:
    """Manual subtitles first, automatic ones second. Returns (path, manual|auto|none)."""
    base = ["--skip-download", "--no-playlist", "--sub-langs", f"{lang}.*,{lang}", "--sub-format", "vtt",
            "-o", str(source_dir / "captions.%(ext)s"), url]
    for flag, label in (("--write-subs", "manual"), ("--write-auto-subs", "auto")):
        run_ytdlp([flag, *base], SUBS_TIMEOUT)
        path = normalise_captions(source_dir, lang)
        if path:
            return path, label
    return None, "none"


def existing_video(cache_dir: Path, video_id: str) -> Path | None:
    hits = [p for p in cache_dir.glob(f"{video_id}.*") if p.suffix.lower() in VIDEO_EXTS and p.is_file()]
    hits.sort(key=lambda p: (p.suffix != ".mp4", p.name))
    return hits[0] if hits else None


def format_ladder(max_height: int) -> list[str]:
    """Format selectors tried in order.

    Single-file formats (progressive or HLS) come first because YouTube answers
    403 for split DASH streams on this yt-dlp release when no PO token is
    available; the split selector stays as a second try, then lower caps.
    """
    ladder = [
        f"best[height<={max_height}][ext=mp4]/best[height<={max_height}]",
        f"bestvideo[height<={max_height}][ext=mp4]+bestaudio[ext=m4a]/best[height<={max_height}][ext=mp4]",
    ]
    if max_height > 720:
        ladder.append("best[height<=720]")
    ladder.append("best")
    return ladder


def download_video(url: str, cache_dir: Path, video_id: str, max_height: int) -> Path:
    last_error = ""
    for fmt in format_ladder(max_height):
        proc = run_ytdlp(["-f", fmt, "--no-playlist", "--no-progress",
                          "-o", str(cache_dir / f"{video_id}.%(ext)s"), url], VIDEO_TIMEOUT)
        if proc.returncode == 0:
            path = existing_video(cache_dir, video_id)
            if path is not None:
                return path
            last_error = "yt-dlp finished but no video file was found in the cache"
            continue
        tail = proc.stderr.strip().splitlines()[-1:] or [""]
        last_error = tail[0][:300]
        common.warn(f"format {fmt!r} failed: {last_error}")
        for stray in cache_dir.glob(f"{video_id}.*.part"):
            stray.unlink(missing_ok=True)
    raise FetchError(common.EXIT_EXTERNAL, f"video download failed: {last_error}")


def enforce_limits(meta: dict, max_minutes: int, force_long: bool) -> None:
    duration = int(meta.get("duration") or 0)
    if duration > max_minutes * 60 and not force_long:
        raise FetchError(common.EXIT_POLICY, f"video is {duration // 60} minutes, above max_video_minutes={max_minutes}; use --force-long")
    size = estimate_size(meta)
    if size > SIZE_CAP:
        raise FetchError(common.EXIT_POLICY, f"estimated size {size / 1e9:.1f} GB exceeds the 2 GB cap")


def previous_caption_source(run_dir: Path) -> str:
    note = run_dir / "run.md"
    if note.is_file():
        value = str(common.read_note(note)[0].get("captions", ""))
        if value in ("manual", "auto"):
            return value
    return ""


def fetch(vault: Path, url: str, rights: str, mode: str, lang: str, max_height: int, force_long: bool,
          queue_note: str | None, settings: dict) -> dict:
    """Run every fetch step and return the result payload."""
    video_id = common.youtube_video_id(url)
    if not video_id:
        raise FetchError(common.EXIT_INPUT, f"not a YouTube video URL: {url}")
    warnings: list[str] = []
    meta = fetch_metadata(common.watch_url(video_id))
    enforce_limits(meta, int(settings["max_video_minutes"]), force_long)
    info = trim_metadata(meta)
    run_dir = common.find_run_dir(vault, video_id) or vault / common.ROOMS["videos"] / common.run_dir_name(info.get("title") or video_id, video_id)
    source = common.ensure_dir(run_dir / "source")
    info_path = common.json_dump(source / "video.info.json", info)

    captions_path = source / f"captions.{lang}.vtt"
    captions_source = previous_caption_source(run_dir) if captions_path.is_file() else ""
    if not captions_source:
        captions_path, captions_source = download_captions(common.watch_url(video_id), source, lang)
        if captions_source == "none":
            warnings.append("no captions in the requested language; analyze needs a Whisper key for a transcript")

    thumb_path = source / "thumbnail.jpg"
    if not thumb_path.is_file():
        thumb_url = largest_thumbnail(meta)
        try:
            if not thumb_url:
                raise ValueError("no https thumbnail URL in metadata")
            http_get(thumb_url, thumb_path)
        except (ValueError, OSError, urllib.error.URLError) as exc:
            warnings.append(f"thumbnail not downloaded: {exc}")

    cache_dir = common.ensure_dir(vault / common.CACHE_DIR)
    video_path = existing_video(cache_dir, video_id) or download_video(common.watch_url(video_id), cache_dir, video_id, max_height)

    run_note = make_run_note.update_run_note(
        vault, run_dir, status="fetched",
        sets={"rights": rights, "mode": mode, "captions": captions_source,
              **({"queue": common.wikilink(common.rel(queue_mod.resolve_note(vault, queue_note), vault), Path(queue_note).stem)} if queue_note else {})},
        log=f"fetched: captions={captions_source}, video={video_path.name}, thumbnail={'yes' if thumb_path.is_file() else 'no'}")
    if queue_note:
        queue_mod.set_status(vault, queue_mod.resolve_note(vault, queue_note), "running", run_dir=str(run_dir))
    return {
        "ok": True, "run_dir": str(run_dir), "video_id": video_id, "title": info.get("title", ""),
        "channel": info.get("channel") or info.get("uploader") or "", "duration_s": int(info.get("duration") or 0),
        "video_path": str(video_path), "captions_path": str(captions_path) if captions_path and Path(captions_path).is_file() else None,
        "captions_source": captions_source, "thumbnail_path": str(thumb_path) if thumb_path.is_file() else None,
        "info_path": str(info_path), "run_note": str(run_note), "warnings": warnings,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fetch a YouTube video into a run folder.")
    parser.add_argument("url")
    parser.add_argument("--vault")
    parser.add_argument("--rights", choices=common.RIGHTS + ("ask",))
    parser.add_argument("--mode", choices=common.MODES)
    parser.add_argument("--lang", help="Caption language (default: Settings language)")
    parser.add_argument("--max-height", type=int, default=1080)
    parser.add_argument("--force-long", action="store_true")
    parser.add_argument("--queue", help="Queue note to mark running")
    args = parser.parse_args(argv)
    try:
        vault = Path(args.vault).expanduser().resolve() if args.vault else common.find_vault_root()
    except FileNotFoundError as exc:
        return common.fail(common.EXIT_INPUT, str(exc))
    if args.max_height <= 0:
        return common.fail(common.EXIT_INPUT, "--max-height must be positive")
    settings = common.load_settings(vault)
    try:
        result = fetch(vault, args.url, args.rights or settings["default_rights"], args.mode or settings["default_mode"],
                       args.lang or str(settings["language"]), args.max_height, args.force_long, args.queue, settings)
    except FetchError as exc:
        return common.fail(exc.code, str(exc))
    except (FileNotFoundError, ValueError) as exc:
        return common.fail(common.EXIT_FAIL, str(exc))
    for message in result["warnings"]:
        common.warn(f"warning: {message}")
    common.emit(result)
    return common.EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
