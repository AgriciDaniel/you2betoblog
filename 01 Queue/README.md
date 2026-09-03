---
type: yt2b-knowledge
title: Queue
kind: manual
created: 2026-09-03
updated: 2026-09-03
tags:
  - yt2b
  - queue
  - manual
---

# Queue

One note per video request, named `<YYYY-MM-DD>-<videoId>.md` with `type: yt2b-queue`. The Queue table on [[00 Home/Home|Home]] lists them newest first.

## Discovery is not queueing

RSS Dashboard is the optional discovery and reading surface. Its feeds, stars, tags and saved state do not authorize the pipeline. Saved research items live under [[01 Queue/Discovery/README|Discovery]] with `type: yt2b-source` and are excluded from queue selection.

To promote a saved YouTube discovery, open its source note and click **Queue open source** in the left sidebar. A real queue note is created here, deduplicated by `video_id`, with rights left as `ask`. The queue records the source and the source records the queue. Inbox and the landing-page input remain direct intake for URLs that do not need saved-source provenance.

## How a note gets here

- Inbox on Home: add a task line under `## Inbox`, then press **Add to queue** (or run `python3 skills/youtube-to-blog/scripts/queue.py --vault . import-inbox`). Processed lines are rewritten as `- [x] <url> -> [[01 Queue/<note>|queued]]`; ticked lines are skipped.
- Saved source: open a `yt2b-source` note, then click **Queue open source** in the left sidebar to preserve two-way lineage.
- Terminal: `python3 skills/youtube-to-blog/scripts/queue.py --vault . add <url> [--rights own|third-party|ask] [--mode companion|expand] [--priority N] [--note TEXT]`.
- Manual: copy `_templates/Queue item.md`, fill `video_url` and `video_id`, keep `status: queued`.

Adding the same video twice returns the existing note instead of a duplicate.

## Inbox line format

```
- [ ] <youtube url> [own|third-party] [companion|expand] [free text note]
```

Accepted URLs: `youtube.com/watch?v=`, `youtu.be/`, `youtube.com/shorts/`, `youtube.com/live/`. Rights and mode are optional; when missing they come from `default_rights` and `default_mode` in [[00 Home/Settings|Settings]], and `ask` makes the agent ask once before fetching. Anything after the mode is stored in the `note` property.

## Properties

`video_url`, `video_id`, `rights` (own, third-party, ask), `mode` (companion, expand), `priority` (integer, 1 is first, default 3), `status`, `run` (wikilink to the run note once fetched), `note`, `created`, `updated`, `tags`. Landing-page entries also record `discovered_via: home`.

## Statuses

- `queued`: waiting; `queue.py next` picks the highest priority, then the oldest.
- `running`: fetched; `run` points to `02 Videos/<run>/run`.
- `done`: every approved blog delivered and evaluated.
- `failed`: a stage stopped the run; the error text sits in the note and in `run.md`. See [[06 AI Team/03 Knowledge/02 SOPs/Recover a blocked run|Recover a blocked run]].

`queue.py set <note> --status <s> [--run <dir>] [--error TEXT]` changes a status by hand; `queue.py list [--status s]` prints the queue as JSON.
