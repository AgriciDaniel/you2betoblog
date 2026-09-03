---
type: yt2b-knowledge
title: make_run_note.py
kind: script
created: 2026-09-03
updated: 2026-09-03
tags:
  - yt2b
  - knowledge
  - script
---

# make_run_note.py

**Purpose.** Creates or updates `02 Videos/<run>/run.md` (type `yt2b-video`), the state note of a video run: properties for the Bases views and a body that shows what the pipeline captured. Sections in order: Video (embedded YouTube player, the thumbnail when `source/thumbnail.jpg` exists, one facts line with channel, published date, duration, captions source and watch link, and a Chapters callout with deep links from `analysis/segments.json`), Summary, Key takeaways, Tags, Frames (an Image Layouts `image-layout-masonry-4` block with `fromFolder` pointing at `analysis/avt_outputs/<id>/frames`, plus a link to the transcript note where each frame sits next to its segment), Blogs (only when `blogs` is non-empty: per blog its title as a wikilink, `hero.jpg` when present and an `image-layout-masonry-3` block over the blog `images/` folder, limit 12), Artifacts (regenerated from the files that exist) and Log (one bullet per stage).

Video, Frames, Blogs and Artifacts are rewritten on every run. Summary, Key takeaways and Tags change only when passed. Sections the script does not own (added by hand) are kept after Log. The galleries need the Image Layouts community plugin; without it the block shows as a code block and the transcript link still leads to every frame.

**Usage.**

```bash
python3 skills/youtube-to-blog/scripts/make_run_note.py --vault "<vault>" --run "<run>" [--status fetched|analyzed|briefed|strategy|writing|done|blocked] [--set key=value ...] [--add-blog "<blog dir>"] [--summary FILE] [--takeaways FILE] [--tags "a,b"] [--log TEXT] [--from-brief [JSON]]
```

**Inputs.** `source/video.info.json` for the video fields (id, title, channel, channel_url, published, duration_s), the existing note when present, optional text files, and with `--from-brief` the analyst's `brief/video-brief.json` (`summary`, `key_takeaways`, `tags`).

**Outputs.** The note with the schema fields (`video_id, video_url, title, channel, channel_url, published, duration_s, rights, mode, status, captions, blogs, queue, created, updated, tags`) plus the media properties `thumbnail` (vault-relative path to `source/thumbnail.jpg`, empty when missing, usable as the image property of a Bases card view), `frames` (count of extracted frames) and `hero` (vault-relative path to the first blog's hero, only when it exists). `--add-blog` appends a wikilink to `blogs` once; `--log` appends `- <timestamp> <text>` and never duplicates a text. JSON: `run_note, status`.

**Exit codes.** 0 ok, 2 missing run folder, bad status, bad `--set` pair or missing brief file.
