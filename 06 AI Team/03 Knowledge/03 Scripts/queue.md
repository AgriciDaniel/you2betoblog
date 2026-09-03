---
type: yt2b-knowledge
title: queue.py
kind: script
created: 2026-09-03
updated: 2026-09-03
tags:
  - yt2b
  - knowledge
  - script
---

# queue.py

**Purpose.** Creates and updates the queue notes in `01 Queue` (`<date>-<videoId>.md`, type `yt2b-queue`) and imports the Inbox list from [[00 Home/Home|Home]].

**Usage.**

```bash
python3 skills/youtube-to-blog/scripts/queue.py --vault "<vault>" add "<url>" [--rights own|third-party|ask] [--mode companion|expand] [--priority N] [--note TEXT]
python3 skills/youtube-to-blog/scripts/queue.py --vault "<vault>" list [--status queued|running|done|failed]
python3 skills/youtube-to-blog/scripts/queue.py --vault "<vault>" next
python3 skills/youtube-to-blog/scripts/queue.py --vault "<vault>" set "<note path>" --status S [--run "<run dir>"] [--error TEXT]
python3 skills/youtube-to-blog/scripts/queue.py --vault "<vault>" import-inbox
```

**Inputs.** A YouTube video URL (watch, youtu.be, shorts, live forms; stored as the canonical watch URL), defaults from [[00 Home/Settings|Settings]] (`default_rights`, `default_mode`), and for `import-inbox` the task lines under `## Inbox` (or inside an Inbox callout): `- [ ] <url> [own|third-party] [companion|expand] [note]`.

**Outputs.** One JSON object: the note record for `add` and `set` (with `created` true or false; an existing id is returned, never duplicated), `{count, items}` for `list`, `{empty, note, path}` for `next` (priority 1 is the most urgent, then the oldest), `{created, existing, skipped}` for `import-inbox`, which also rewrites each processed line as `- [x] <url> -> [[01 Queue/<note>|queued]]` and leaves ticked or invalid lines alone. `--error` appends a failure callout to the note body once.

**Exit codes.** 0 ok, 1 missing note or Home, 2 invalid URL or status.
