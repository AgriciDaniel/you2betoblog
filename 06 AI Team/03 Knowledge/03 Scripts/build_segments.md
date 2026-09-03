---
type: yt2b-knowledge
title: build_segments.py
kind: script
created: 2026-09-03
updated: 2026-09-03
tags:
  - yt2b
  - knowledge
  - script
---

# build_segments.py

**Purpose.** Reads the video-analyzer `.avt` output with the analyzer's own parser, aligns our captions to its segments, extracts chapters, and writes the two files every later stage reads: `analysis/segments.json` and `analysis/transcript.md`. The `.avt` file is never modified (it belongs to video-analyzer, Source-Available Non-Commercial license).

**Usage.**

```bash
python3 skills/youtube-to-blog/scripts/build_segments.py --run "<run>" [--analyze-dir "<video-analyzer checkout>"]
```

**Inputs.** `<run>/analysis/avt_outputs/*/*.avt` (globbed: the folder is the analyzer's slug of the video file name), `source/video.info.json`, `source/captions.<lang>.vtt` when the analyzer had no transcript, `run.md` (`captions` manual or auto), and the analyzer modules `avt.py`, `transcribe.py`, `frames.py` from the analyze dir (resolved like doctor.py).

**Outputs.** `segments.json` (`schema yt2b/v1`, trimmed video fields, `transcript_source`, `chapters [{start_s, title}]`, `segments [{start_s, end_s, start, end, scene, visual, audio, frame}]` with frame paths relative to the run folder). Captions are assigned once each by cue midpoint (YouTube roll-up cues are normalised first); chapters come from description lines (first at 0:00, at least three, ascending) else the chapters field. `transcript.md` (type `yt2b-knowledge`, kind `transcript`) opens with the untrusted-source notice and a video card, then Chapters with deep links, the transcript grouped by chapter with `[mm:ss]` links, and a Segments table embedding the 512px frames. JSON: `segments, chapters, frames, transcript_source, segments_path, transcript_path`.

**Exit codes.** 0 ok, 1 no `.avt` yet or unparsable output, 2 bad run folder, 4 video-analyzer not found.
