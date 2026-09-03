---
type: yt2b-knowledge
title: fetch_video.py
kind: script
created: 2026-09-03
updated: 2026-09-03
tags:
  - yt2b
  - knowledge
  - script
---

# fetch_video.py

**Purpose.** Brings a video into a run folder in `02 Videos`: trimmed metadata, captions, thumbnail, the cached video file, and the first version of `run.md`. This pipeline owns the download so captions and metadata survive (video-analyzer deletes them).

**Usage.**

```bash
python3 skills/youtube-to-blog/scripts/fetch_video.py --vault "<vault>" "<url>" [--rights R] [--mode M] [--lang en] [--max-height 1080] [--force-long] [--queue "<queue note>"]
```

**Inputs.** A YouTube URL, `yt-dlp` on PATH, Settings `max_video_minutes` and `language`. Every subprocess call is an argument list with a timeout; the thumbnail download is https only with a 10 MB cap.

**Outputs.** `02 Videos/<date>-<slug40>-<videoId>/source/video.info.json` (id, title, channel fields, uploader_url, webpage_url, upload_date, timestamp, release_timestamp, duration, description, tags, categories, chapters, counts, thumbnail plus the 3 largest thumbnails, license, language, caption language codes), `source/captions.<lang>.vtt` (manual first, then automatic; the identical `-orig` duplicate is removed), `source/thumbnail.jpg`, `.cache/video/<id>.mp4` (mp4 up to `--max-height`), `run.md` with status `fetched` and a log line, and the queue note set to `running` with the run link. JSON: `run_dir, video_id, title, channel, duration_s, video_path, captions_path, captions_source (manual | auto | none), thumbnail_path, info_path, run_note, warnings`. Re-running reuses the folder and every existing file.

**Exit codes.** 0 ok, 2 invalid URL, 3 policy limit (length without `--force-long`, 2 GB estimate), 4 yt-dlp missing, 5 yt-dlp or network failure.
