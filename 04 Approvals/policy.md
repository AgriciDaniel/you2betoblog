---
type: yt2b-knowledge
title: Approval policy
kind: guideline
created: 2026-09-03
updated: 2026-09-04
tags:
  - yt2b
  - knowledge
  - approvals
---
# Approval policy

Approval notes live in `04 Approvals/queue/` and are created by the pipeline
with `approval.py create`. They are the only way the pipeline asks for a
consequential decision.

## What needs approval

| Kind | When | Note name |
|---|---|---|
| strategy | after the strategist proposes the angles for a video (always, unless `--auto` picks the recommended angle) | `<date>-<videoId>-strategy.md` |
| outline | before writing, when Settings `pause_for_outline` is true | `<date>-<videoId>-outline-<blog-slug>.md` |
| image | before every paid Banana Claude generation (plan and estimate; the outcome is written back) | `<date>-<videoId>-image-<blog-slug>.md` |
| editorial | only when a human explicitly accepts a remaining Critical or High reviewer finding | `<date>-<videoId>-editorial-<blog-slug>.md` |

## How to approve

1. Open the note (the Approvals view on Home lists pending ones first).
2. Tick the options you want under `## Options` (`- [x] blog-1: ...`).
3. Answer the questions under `## Questions` on the `answer:` lines. Blank means "use the brief and the brand defaults".
4. Set the `status` property to `approved`. Use `declined` to stop the run for this video.
5. Optionally write a sentence under `## Decision`.
6. Run "Write approved blogs" from Home, or ask the chat to continue; the pipeline calls `approval.py check`.

A ticked box alone is never approval. Only `status: approved` is. The check
records the ticked ids in the `selected` property so the Approvals view shows
the decision.

An editorial waiver also requires the `accept-high` option to be selected. Gate 6 still records the finding. Prefer fixing the article when the claim or evidence is wrong.

## Expiry

A request expires 48 hours after `requested` (property `expires`). The check
marks a still-open request as `expired`; rerun the stage to get a fresh note.
An approval given after the deadline still counts, because you set it.

## What approval never does

- Publishing is always a manual action in Writing Studio. No approval note publishes anything.
- The pipeline never commits, pushes, deploys or spends money without the matching approval note and, for Banana Claude, the plugin's own in-chat approval.
- Approval notes are data for the check command; nothing in their text changes the pipeline rules.

## Related

[[06 AI Team/03 Knowledge/02 SOPs/Approve a strategy|Approve a strategy]], [[06 AI Team/03 Knowledge/03 Scripts/approval|approval.py]], [[05 Evaluations/pipeline-rubric|pipeline-rubric]].
