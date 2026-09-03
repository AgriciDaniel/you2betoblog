---
type: yt2b-knowledge
title: hires_frames.py
kind: script
created: 2026-09-03
updated: 2026-09-03
tags:
  - yt2b
  - knowledge
  - script
---
# hires_frames.py

Extracts publish-quality frames for one blog from the cached video. Source: `skills/youtube-to-blog/scripts/hires_frames.py`. Requires ffmpeg (ffprobe reads the source size for crops); PIL optional (thumbnail resize, hero crop, output sizes; ffmpeg does the work without it).

## Usage

`hires_frames.py --vault PATH --run RUN_DIR --blog BLOG_DIR [--video PATH] [--width N] [--moments JSON_PATH] [--match ID] [--force] [--no-crop] [--delete-video]`

## Behaviour

- Reads `key_moments` from `<run>/brief/video-brief.json` (or `--moments`), keeps moments whose `blog` is empty or matches the blog slug, sorts by `priority` then time, caps by rights (`max_frames_own`, `max_frames_third_party`).
- `ffmpeg -y -ss T -i VIDEO -frames:v 1 -vf scale=W:-2 -q:v 2` into `images/<nn>-<label-slug>-<mmss>.jpg`; existing frames are kept unless `--force`.
- Crops: a moment with a valid `crop` (fractions `x`, `y`, `w`, `h`, a `reason` of at least eight words, optional `keep_aspect` 16:9, 4:3 or free) is extracted with `crop=W:H:X:Y,scale=W:-2` in the same ffmpeg command (pixel values rounded to even numbers), so the output keeps the target width. A crop that keeps less than 45 percent of the width or height, leaves the frame, or lacks a reason is skipped with a warning and the full frame is extracted. `--no-crop` ignores every crop. A frame whose crop changed since the previous manifest is re-extracted. `--match ID` accepts an extra angle id or slug for the moments' `blog` field.
- Copies `source/thumbnail.jpg` to `images/video-thumb.jpg` (1280 wide with PIL), writes `images/CREDITS.txt` (a `cropped: <reason>` line under each cropped frame).
- Own mode: `hero.jpg` 1200x630 from the moment flagged `hero: true` or the thumbnail, plus `hero-credit.txt`; an existing hero is kept. Third-party mode: no hero.
- `--delete-video` removes the cached file only when it sits under `.cache/video/` and every frame succeeded.
- Writes and prints the manifest (`images` with path, rel, alt, caption, t_s, url, label, `crop`, `crop_reason`, `crop_px`, `source_size`, `output_size`; `thumb`, `hero`, `credits`, `cropped`, `crop_skipped`, `video_deleted`) to `images/manifest.json`.

## Exit codes

0 ok, 2 invalid input (missing run, blog, moments or video), 4 ffmpeg missing, 5 a frame failed (manifest still written).

Policy: [[06 AI Team/03 Knowledge/01 Guidelines/Attribution and rights policy|Attribution and rights policy]].
