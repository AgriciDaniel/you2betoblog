#!/usr/bin/env python3
"""Run video-analyzer on a fetched video and report the resulting .avt file.

Usage:
    run_analyze.py --run RUN_DIR --video PATH [--max-frames 120] [--no-whisper] [--force-long] [--analyze-dir DIR]

Resolves the analyzer exactly like doctor.py (VIDEO_ANALYZER_DIR, then the known
skill paths, then the plugin caches) and runs

    python3 <analyze-dir>/scripts/analyze.py <video> --out-dir <run>/analysis --max-frames N [--no-whisper] [--force-long]

with the analyzer's stderr streamed through and no timeout of its own (the
orchestrator runs it in the background). --no-whisper is added automatically
when no Whisper key (GROQ_API_KEY or OPENAI_API_KEY) is present. Afterwards it
globs <run>/analysis/avt_outputs/*/*.avt (the folder is the analyzer's slug of
the video file name, so it is never computed) and prints {avt_path, frames, exit_code}.
Exit 0 when the analyzer succeeded and an .avt exists, 2 bad input, 4 analyzer
not found, 5 analyzer failure.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import yt2b_common as common  # noqa: E402


def analyzer_command(analyze_dir: Path, video: Path, analysis_dir: Path, max_frames: int, no_whisper: bool, force_long: bool) -> list[str]:
    """Argument list for analyze.py (sibling imports work because Python adds the script folder to sys.path)."""
    cmd = [sys.executable, str(analyze_dir / "scripts" / "analyze.py"), str(video), "--out-dir", str(analysis_dir),
           "--max-frames", str(max_frames)]
    if no_whisper:
        cmd.append("--no-whisper")
    if force_long:
        cmd.append("--force-long")
    return cmd


def find_outputs(analysis_dir: Path) -> tuple[Path | None, int]:
    """Newest .avt under avt_outputs and the number of frames beside it."""
    hits = sorted(analysis_dir.glob("avt_outputs/*/*.avt"), key=lambda p: p.stat().st_mtime)
    if not hits:
        return None, 0
    avt = hits[-1]
    return avt, len(list((avt.parent / "frames").glob("*.jpg")))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run video-analyzer for a run folder.")
    parser.add_argument("--run", required=True)
    parser.add_argument("--video", required=True)
    parser.add_argument("--max-frames", type=int, default=120)
    parser.add_argument("--no-whisper", action="store_true")
    parser.add_argument("--force-long", action="store_true")
    parser.add_argument("--analyze-dir")
    args = parser.parse_args(argv)
    run_dir = Path(args.run).expanduser().resolve()
    video = Path(args.video).expanduser().resolve()
    if not run_dir.is_dir():
        return common.fail(common.EXIT_INPUT, f"run folder not found: {run_dir}")
    if not video.is_file():
        return common.fail(common.EXIT_INPUT, f"video file not found: {video}")
    analyze_dir = Path(args.analyze_dir).expanduser().resolve() if args.analyze_dir else common.find_analyze_dir()
    if analyze_dir is None or not (analyze_dir / "scripts" / "analyze.py").is_file():
        return common.fail(common.EXIT_MISSING, "video-analyzer not found (pass --analyze-dir or set VIDEO_ANALYZER_DIR)")
    no_whisper = args.no_whisper or not any(common.key_present(k) for k in common.WHISPER_KEYS)
    if no_whisper and not args.no_whisper:
        common.warn("no Whisper key found: adding --no-whisper")
    analysis_dir = common.ensure_dir(run_dir / "analysis")
    cmd = analyzer_command(analyze_dir, video, analysis_dir, args.max_frames, no_whisper, args.force_long)
    common.warn("running: " + " ".join(cmd))
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=None, text=True)
    avt, frames = find_outputs(analysis_dir)
    payload = {"ok": proc.returncode == 0 and avt is not None, "avt_path": str(avt) if avt else None,
               "frames": frames, "exit_code": proc.returncode, "analysis_dir": str(analysis_dir)}
    common.emit(payload)
    return common.EXIT_OK if payload["ok"] else common.EXIT_EXTERNAL


if __name__ == "__main__":
    sys.exit(main())
