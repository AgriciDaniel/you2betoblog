---
type: yt2b-knowledge
title: approval.py
kind: script
created: 2026-09-03
updated: 2026-09-03
tags:
  - yt2b
  - knowledge
  - script
---
# approval.py

Creates, checks and decides approval notes in `04 Approvals/queue`. Source: `skills/youtube-to-blog/scripts/approval.py`.

## Usage

- `approval.py --vault PATH create --kind strategy|outline|image --run RUN_DIR [--blog BLOG_DIR] --title T --request-file PATH [--options "id=label;id=label"] [--questions "key=question;..."] [--expires-hours 48] [--cost-estimate TEXT]`
- `approval.py check NOTE_PATH` prints `{status, approved, selected, answers, expired, kind}`
- `approval.py set NOTE_PATH --status approved|declined|requested|expired [--decision TEXT] [--selected id ...]`

## Behaviour

- Note names: `<date>-<videoId>-strategy.md`, `<date>-<videoId>-outline[-<blog-slug>].md`, `<date>-<videoId>-image-<blog-slug>.md` (`--blog` required for image).
- `create` never overwrites an existing note (returns it with `created: false`).
- `check` reads ticked `- [x] id: label` lines and `answer:` lines, syncs `selected`, and marks a past-deadline request as `expired`. Approval means `status: approved` only.
- `set --selected` ticks boxes for the `--auto` path; `--decision` appends once under `## Decision`.

## Exit codes

0 ok, 1 failure, 2 invalid input (unknown kind, missing run, bad option pair, unknown option id).

Policy: [[04 Approvals/policy|Approval policy]].
