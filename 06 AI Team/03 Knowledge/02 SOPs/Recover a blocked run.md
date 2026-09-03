---
type: yt2b-knowledge
title: Recover a blocked run
kind: sop
created: 2026-09-03
updated: 2026-09-03
tags:
  - yt2b
  - sop
---

# Recover a blocked run

1. Find the run: the Videos table shows `blocked` and the queue note shows `failed`. Open `run.md` and read the last `## Log` line; it names the stage and the error.
2. Missing tool or key (exit code 4): press **Setup check**, install or configure what it lists, then rerun the failed stage from the terminal with the same command.
3. External failure (exit code 5: yt-dlp, ffmpeg, network): retry once. For age-gated, private or removed videos set the queue note to `failed` with a note and move on.
4. Policy limit (exit code 3: too long or too large): pass `--force-long`, fetch with `--max-height 720`, or raise `max_video_minutes` in [[00 Home/Settings|Settings]] on purpose.
5. Expired or declined approval: set the note back to `status: requested` and decide again, or create a fresh one with `python3 skills/youtube-to-blog/scripts/approval.py --vault . create --kind strategy --run "<run>"`, then press **Write approved blogs**.
6. Failed delivery gates (the article is `blocked`): open `review.md` and `preflight-report.json` in the blog folder, fix the draft or let the agent run one more repair, then rerun `blog_preflight.py --draft "<blog>" --strict` and `evaluate.py`.
7. When the run is healthy again: `python3 skills/youtube-to-blog/scripts/make_run_note.py --vault . --run "<run>" --status <stage> --log "recovered: what changed"` and `queue.py --vault . set "<note>" --status queued` (or `running`).
8. If the cause can recur, write a learning note from `_templates/Learning.md` into `06 AI Team/03 Knowledge/05 Learnings`.
