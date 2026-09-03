#!/usr/bin/env python3
"""Turn a video-analyzer .avt file plus our captions into segments.json and transcript.md.

Usage:
    build_segments.py --run RUN_DIR [--analyze-dir DIR]

Reads <run>/analysis/avt_outputs/*/*.avt with video-analyzer's own parser
(imported from <analyze-dir>/scripts; the .avt file is never modified). When the
analyzer had no transcript and source/captions.<lang>.vtt exists, each caption
cue is assigned once to the segment holding its midpoint (YouTube roll-up cues
are normalised first). Chapters come from the description (first at 0:00, at
least three, ascending) or from the chapters field. Writes analysis/segments.json
and analysis/transcript.md (untrusted-source notice, video card, chapters,
transcript with deep links, segment table with the 512px frames).
Prints {segments, chapters, frames, transcript_source, segments_path, transcript_path}.
Exit 0 ok, 1 no .avt yet, 2 bad run folder, 4 video-analyzer not found.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import yt2b_common as common  # noqa: E402

CHAPTER_LINE = re.compile(r"^\s*((?:\d{1,2}:)?\d{1,2}:\d{2})\s+(.+?)\s*$")
VTT_TIMING = re.compile(r"^\d{1,2}:\d{2}(?::\d{2})?\.\d{3}\s*-->\s*")
TAGGED = re.compile(r"<[^>]+>")
VIDEO_KEYS = ("id", "title", "channel", "channel_url", "webpage_url", "upload_date", "duration", "view_count",
              "license", "language", "thumbnail")


def load_analyzer(analyze_dir: Path):
    """Import avt, transcribe and frames from the analyzer checkout."""
    scripts = analyze_dir / "scripts"
    avt = common.load_module(scripts / "avt.py", "yt2b_va_avt")
    transcribe = common.load_module(scripts / "transcribe.py", "yt2b_va_transcribe")
    frames = common.load_module(scripts / "frames.py", "yt2b_va_frames")
    return avt, transcribe, frames


def find_avt(run_dir: Path) -> Path | None:
    """Newest .avt under analysis/avt_outputs. Always glob: video-analyzer names the folder
    after the slugified video file stem (lowercased, underscores stripped), never compute it."""
    hits = sorted((run_dir / "analysis" / "avt_outputs").glob("*/*.avt"), key=lambda p: p.stat().st_mtime)
    if len(hits) > 1:
        common.warn(f"warning: {len(hits)} .avt files found, using the newest: {hits[-1]}")
    return hits[-1] if hits else None


def normalize_rollup_vtt(text: str) -> str:
    """Drop YouTube roll-up duplicates: keep only tagged lines in tagged cues, drop plain repeat cues.

    Cues are delimited by timing lines (not by blank lines: YouTube writes a
    space-only line right after each timing line)."""
    if "<c>" not in text and not re.search(r"<\d{1,2}:\d{2}:\d{2}\.\d{3}>", text):
        return text
    header: list[str] = []
    cues: list[tuple[str, list[str]]] = []
    for line in text.splitlines():
        if VTT_TIMING.match(line.strip()):
            cues.append((line, []))
        elif not cues:
            header.append(line)
        elif line.strip():
            cues[-1][1].append(line)
    out = [ln for ln in header if ln.strip()]
    for timing, body in cues:
        tagged = [ln for ln in body if TAGGED.search(ln)]
        if tagged:
            out += ["", timing, *tagged]
    return "\n".join(out) + "\n"


def dedupe_cues(cues: list[dict]) -> list[dict]:
    """Remove repeated text between consecutive cues (identical, prefix or tail repeats)."""
    kept: list[dict] = []
    for cue in cues:
        text = cue.get("text", "").strip()
        if not text:
            continue
        if kept:
            prev = kept[-1]["text"]
            if text == prev or prev.endswith(text):
                continue
            if text.startswith(prev + " "):
                text = text[len(prev) + 1:]
        kept.append({**cue, "text": text})
    return kept


def segment_for(mid: float, segments: list[dict]) -> int:
    """Index of the segment containing mid, else the nearest one."""
    for i, seg in enumerate(segments):
        last = i == len(segments) - 1
        if seg["start_s"] <= mid < seg["end_s"] or (last and mid == seg["end_s"]):
            return i

    def distance(i: int) -> float:
        seg = segments[i]
        return min(abs(mid - seg["start_s"]), abs(mid - seg["end_s"]))

    return min(range(len(segments)), key=distance)


def assign_cues(cues: list[dict], segments: list[dict]) -> None:
    """Assign every cue exactly once to a segment by its midpoint."""
    buckets: dict[int, list[str]] = {}
    for cue in cues:
        mid = (float(cue["start_seconds"]) + float(cue["end_seconds"])) / 2
        buckets.setdefault(segment_for(mid, segments), []).append(cue["text"])
    for i, seg in enumerate(segments):
        seg["audio"] = " ".join(buckets.get(i, []))


def parse_description_chapters(description: str) -> list[dict]:
    chapters = []
    for line in (description or "").splitlines():
        m = CHAPTER_LINE.match(line)
        if m:
            chapters.append({"start_s": int(common.mmss_to_seconds(m.group(1))), "title": m.group(2).lstrip("-:|)] ").strip()})
    starts = [c["start_s"] for c in chapters]
    if len(chapters) >= 3 and starts[0] == 0 and all(a < b for a, b in zip(starts, starts[1:])):
        return chapters
    return []


def chapters_from_info(info: dict) -> list[dict]:
    chapters = parse_description_chapters(info.get("description") or "")
    if chapters:
        return chapters
    return [{"start_s": int(float(c.get("start_time") or 0)), "title": str(c.get("title") or "").strip()}
            for c in (info.get("chapters") or []) if isinstance(c, dict)]


def build_segment_records(parsed: dict, avt_path: Path, run_dir: Path, to_seconds) -> list[dict]:
    rel_dir = avt_path.parent.relative_to(run_dir).as_posix()
    records = []
    for seg in parsed["segments"]:
        frame = seg.get("frame")
        records.append({
            "start_s": to_seconds(seg["start"]), "end_s": to_seconds(seg["end"]),
            "start": seg["start"], "end": seg["end"], "scene": seg.get("scene", ""),
            "visual": seg.get("visual", ""), "audio": seg.get("audio", ""),
            "frame": f"{rel_dir}/{frame}" if frame else None,
        })
    return records


def caption_source_label(run_dir: Path) -> str:
    note = run_dir / "run.md"
    value = str(common.read_note(note)[0].get("captions", "")) if note.is_file() else ""
    return f"captions-{value}" if value in ("manual", "auto") else "captions"


def cell(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).replace("|", "\\|").strip()


def render_transcript(info: dict, video_id: str, chapters: list[dict], segments: list[dict], source: str) -> str:
    """Markdown body for analysis/transcript.md (paths relative to the analysis folder)."""
    watch = common.watch_url
    lines = [common.untrusted_notice("transcript, descriptions and captions"), ""]
    channel = info.get("channel") or info.get("uploader") or ""
    channel_link = f"[{channel}]({info['channel_url']})" if info.get("channel_url") else channel
    lines += [f"> [!info] {info.get('title', '')}", f"> Channel: {channel_link}",
              f"> Published: {common.upload_date_to_iso(info.get('upload_date')) or 'unknown'}",
              f"> Duration: {common.seconds_to_mmss(info.get('duration') or 0)}",
              f"> Watch: {watch(video_id)}", f"> Transcript source: {source}", ""]
    lines.append("## Chapters\n")
    lines += [f"- [{common.seconds_to_mmss(c['start_s'])}]({watch(video_id, c['start_s'])}) {c['title']}" for c in chapters] or ["- (no chapters)"]
    lines.append("\n## Transcript\n")
    groups = chapters or [{"start_s": 0, "title": "Full transcript"}]
    for i, chapter in enumerate(groups):
        end = groups[i + 1]["start_s"] if i + 1 < len(groups) else float("inf")
        lines.append(f"### {common.seconds_to_mmss(chapter['start_s'])} {chapter['title']}\n")
        spoken = [s for s in segments if chapter["start_s"] <= s["start_s"] < end and s["audio"].strip()]
        lines += [f"- [{s['start']}]({watch(video_id, s['start_s'])}) {s['audio'].strip()}" for s in spoken] or ["- (no speech)"]
        lines.append("")
    lines += ["## Segments\n", "| Time | Scene | Visual | Frame |", "|---|---|---|---|"]
    for seg in segments:
        frame = seg["frame"].split("/", 1)[1] if seg["frame"] else ""
        embed = f"![frame\\|240]({frame})" if frame else ""
        lines.append(f"| [{seg['start']}]({watch(video_id, seg['start_s'])}) | {cell(seg['scene'])} | {cell(seg['visual'])} | {embed} |")
    return "\n".join(lines) + "\n"


def build(run_dir: Path, analyze_dir: Path) -> dict:
    avt_path = find_avt(run_dir)
    if avt_path is None:
        raise FileNotFoundError("no .avt file under analysis/avt_outputs; run analyze first")
    avt, transcribe, frames = load_analyzer(analyze_dir)
    parsed = avt.parse_avt(str(avt_path))
    segments = build_segment_records(parsed, avt_path, run_dir, frames.timestamp_to_seconds)
    info = common.json_load(run_dir / "source" / "video.info.json", {}) or {}
    video_id = info.get("id") or run_dir.name.rsplit("-", 1)[-1]
    source = str(parsed["metadata"].get("transcript_source") or "none")
    captions = sorted((run_dir / "source").glob("captions.*.vtt"))
    if (source == "none" or not any(s["audio"].strip() for s in segments)) and captions and segments:
        text = normalize_rollup_vtt(captions[0].read_text(encoding="utf-8"))
        assign_cues(dedupe_cues(transcribe.parse_vtt_content(text)), segments)
        source = caption_source_label(run_dir)
    chapters = chapters_from_info(info)
    analysis = common.ensure_dir(run_dir / "analysis")
    payload = {"schema": common.SCHEMA_VERSION, "video": {k: info.get(k) for k in VIDEO_KEYS},
               "avt": {"path": avt_path.relative_to(run_dir).as_posix(), **{k: parsed["metadata"].get(k) for k in ("model", "analyzed", "frames_extracted")}},
               "transcript_source": source, "chapters": chapters, "segments": segments}
    segments_path = common.json_dump(analysis / "segments.json", payload)
    frontmatter = {"type": common.NOTE_TYPES["knowledge"], "kind": "transcript", "title": info.get("title", ""),
                   "video_id": video_id, "transcript_source": source, "segments": len(segments),
                   "created": common.today(), "updated": common.today(), "tags": ["yt2b", "knowledge", "transcript"]}
    existing = analysis / "transcript.md"
    if existing.is_file():
        frontmatter["created"] = common.read_note(existing)[0].get("created", frontmatter["created"])
    transcript_path = common.write_note(existing, frontmatter, render_transcript(info, video_id, chapters, segments, source))
    return {"ok": True, "segments": len(segments), "chapters": len(chapters), "frames": sum(1 for s in segments if s["frame"]),
            "transcript_source": source, "segments_path": str(segments_path), "transcript_path": str(transcript_path)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build segments.json and transcript.md for a run.")
    parser.add_argument("--run", required=True)
    parser.add_argument("--analyze-dir", help="video-analyzer checkout (default: resolved like doctor.py)")
    args = parser.parse_args(argv)
    run_dir = Path(args.run).expanduser().resolve()
    if not run_dir.is_dir():
        return common.fail(common.EXIT_INPUT, f"run folder not found: {run_dir}")
    analyze_dir = Path(args.analyze_dir).expanduser().resolve() if args.analyze_dir else common.find_analyze_dir()
    if analyze_dir is None or not (analyze_dir / "scripts" / "avt.py").is_file():
        return common.fail(common.EXIT_MISSING, "video-analyzer not found (pass --analyze-dir or set VIDEO_ANALYZER_DIR)")
    try:
        result = build(run_dir, analyze_dir)
    except FileNotFoundError as exc:
        return common.fail(common.EXIT_FAIL, str(exc))
    except ValueError as exc:
        return common.fail(common.EXIT_FAIL, f"cannot parse analyzer output: {exc}")
    common.emit(result)
    return common.EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
