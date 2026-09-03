---
type: yt2b-knowledge
title: Add a video to the queue
kind: sop
created: 2026-09-03
updated: 2026-09-03
tags:
  - yt2b
  - sop
---

# Add a video to the queue

1. Decide the rights: `own` for a video you made or hold the rights to, `third-party` for anyone else's. When unsure, use `third-party`.
2. Decide the mode: `companion` (default) for an article that stands beside the video, `expand` for a full article that uses the video as one source.
3. From Home: add `- [ ] <url> own companion optional note` under `## Inbox` and press **Add to queue**. The line becomes `- [x] <url> -> [[01 Queue/<note>|queued]]`.
4. From the terminal: `python3 skills/youtube-to-blog/scripts/queue.py --vault . add "<url>" --rights own --mode companion --priority 2 --note "why this video"`.
5. Check the Queue table on Home. Priority 1 runs first; ties go to the oldest note. The same video is never queued twice.
6. To change a request before it runs, edit `rights`, `mode`, `priority` or `note` in the queue note. To drop it, set `status: failed` with a note, or delete the note.

Details and the accepted URL forms are in [[01 Queue/README|the queue README]].
