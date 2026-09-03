---
type: yt2b-knowledge
title: Voice room
kind: voice
created: 2026-09-03
updated: 2026-09-03
tags:
  - yt2b
  - voice
---
# Voice

This room holds who writes and how. The pipeline's voice has one source at the vault root and one profile here.

## What lives here

- [[Author Profile]]: name, job title, author page, official profiles (`same_as`), expertise, disclosure and the short bio. The Person node in every post's JSON-LD and the author block come from it. Created by the setup command from `_templates/Author Profile.md`.
- Root `BRAND.md` ([[BRAND]]): audience, positioning, editorial rules, topic scope, publishing target.
- Root `VOICE.md` ([[VOICE]]): pronoun stance, sentence and paragraph ceilings, summary label, fingerprint, readability target, `## Taboo phrases` (counted by `evaluate.py`).
- Persona JSON, outside the vault: `~/.claude/skills/blog-persona/references/personas/<name>.json`, owned by the blog-persona skill; `VOICE.md` mirrors its sliders.
- Workflows in `_alembic/` embed `VOICE.md` and `BRAND.md` through [[alembic_sync]].

## Why the root files are real files

claude-blog auto-loads `BRAND.md` and `VOICE.md` from the project root through `load_untrusted_root.py`, which refuses symlinks and fences the text as data. They are not shipped with the vault; the setup writes them from `_templates/BRAND.md` and `_templates/VOICE.md`. Until then every consumer uses a neutral voice.

## How it is written and refreshed

- SOP: [[Set up voice and expertise]]. Rules the writer follows: [[Voice rules]].
- Refresh: run setup again (it pre-fills), or edit the root files by hand and run [[alembic_sync]].
