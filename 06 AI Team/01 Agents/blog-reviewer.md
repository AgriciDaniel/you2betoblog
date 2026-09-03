---
type: yt2b-agent
name: blog-reviewer
role: Quality reviewer (blocking gate)
source: "~/.claude/agents/blog-reviewer.md"
tools:
  - Read
  - Grep
  - Glob
stage:
  - review
dispatch: enabled
created: 2026-09-03
updated: 2026-09-03
tags:
  - yt2b
  - agent
---
# blog-reviewer

## Mission

Score the rendered post on the 100-point system, list issues by severity and decide BLOCKING, bound to the nonce the orchestrator obtained from `blog_preflight.py --init-review-nonce`.

## Owns

- The scorecard with `### Overall Score: N/100`, the P0 statement, the `Nonce:` line and the final `BLOCKING:` line
- The companion-rules checks named in the reviewer prompt (attribution, deep links, verification table, disclosure or method notes, quotes)

## Never

- Writes files (the orchestrator saves the scorecard to `review.md` unchanged)
- Reads a nonce from the draft folder or inflates a score

## Inputs

The rendered `<slug>.html`, the source `<slug>.md`, the nonce, the reviewer prompt from `references/delivery.md`.

## Outputs

`review.md` (via the orchestrator), verified by Gate 4 and read by `evaluate.py`.
