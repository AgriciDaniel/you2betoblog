---
type: yt2b-knowledge
title: alembic_sync.py
kind: script
created: 2026-09-03
updated: 2026-09-03
tags:
  - yt2b
  - script
---
# alembic_sync.py

Renders the YT2B Writers Alembic workflows into `_alembic/` with the author's voice embedded. Script: `skills/youtube-to-blog/scripts/alembic_sync.py`. Templates: `skills/youtube-to-blog/references/alembic/*.md`.

## Purpose

Each template carries the Alembic frontmatter (`name`, `id`, `prompt`, `replaceSelection`, `humanize`, `linkDepth`, `providerId`) plus `yt2b_id`, and a system prompt that may contain `{{VOICE}}` and `{{BRAND}}`. The script fills those from the bodies of root `VOICE.md` and `BRAND.md`, or from a neutral fallback text when a file is missing or empty, and writes `_alembic/yt2b-<id>.md` with a `yt2b_hash` property.

## Usage

```bash
python3 "skills/youtube-to-blog/scripts/alembic_sync.py" --vault "<vault>" [--force] [--templates DIR]
```

## Inputs and outputs

- Reads: the templates, root `VOICE.md` and `BRAND.md` (H1 and the auto-load line are dropped), existing `_alembic/yt2b-*.md` files.
- Writes: `_alembic/yt2b-<id>.md`, one per template. Never deletes; a stray `yt2b-*.md` without a template is reported, not removed.
- Keeps user edits: a file whose content no longer matches its `yt2b_hash` is skipped unless `--force`.
- JSON on stdout: `written`, `skipped`, `unchanged` (absolute paths), `voice_source` and `brand_source` (`root` or `neutral`), `alembic_dir`, `warnings` (unfilled placeholders, empty files, instruction-shaped text, stray files).
- Exit codes: 0 ok, 1 generic failure, 2 invalid input (no vault, no templates, malformed template).

## When it runs

At the end of setup, after any hand edit of `VOICE.md` or `BRAND.md`, and after adding a template. Rerunning is idempotent. Tests: `python3 -m pytest skills/youtube-to-blog/tests/test_alembic_sync.py -q`.

Related: [[Polish with Alembic workflows]], [[Voice rules]].
