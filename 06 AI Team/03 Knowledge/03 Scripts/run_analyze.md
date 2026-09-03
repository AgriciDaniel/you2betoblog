---
type: yt2b-knowledge
title: run_analyze.py
kind: script
created: 2026-09-03
updated: 2026-09-03
tags:
  - yt2b
  - knowledge
  - script
---

# run_analyze.py

**Purpose.** Thin wrapper around video-analyzer's `analyze.py` so the orchestrator runs one allowlisted command in the background: it resolves the analyzer like doctor.py, streams the analyzer's progress, and reports the resulting `.avt` file.

**Usage.**

```bash
python3 skills/youtube-to-blog/scripts/run_analyze.py --run "<run>" --video "<.cache/video/<id>.mp4>" [--max-frames 120] [--no-whisper] [--force-long] [--analyze-dir DIR]
```

**Inputs.** The run folder, the cached video file, `GOOGLE_API_KEY` in `~/.config/video-analyzer/.env` (read by the analyzer, never by this script), optional Whisper keys (`--no-whisper` is added automatically when none is present).

**Outputs.** `<run>/analysis/avt_outputs/<slug>/<slug>.avt` and `frames/` written by the analyzer (the slug is the lowercased, underscore-stripped video file stem, so the path is always globbed). JSON: `avt_path, frames, exit_code, analysis_dir`. Re-running the same command resumes from the analyzer's checkpoints.

**Exit codes.** 0 ok, 2 missing run or video, 4 analyzer not found, 5 analyzer failure.
