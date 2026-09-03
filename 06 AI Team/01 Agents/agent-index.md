---
type: yt2b-knowledge
title: Agent index
kind: manual
created: 2026-09-03
updated: 2026-09-03
tags:
  - yt2b
  - knowledge
  - agents
---
# Agent index

One orchestrating Claude Code session runs the stages in order; agents are
dispatched with file handoffs and narrow tool sets. Scripts are deterministic;
agents make editorial judgments; approval notes sit between consequential steps.

| Stage | Agent | Source | Note |
|---|---|---|---|
| doctor, setup, queue, fetch, analyze, segments | none (scripts and the orchestrator) | `skills/youtube-to-blog/scripts/` | |
| brief | [[06 AI Team/01 Agents/yt2b-analyst\|yt2b-analyst]] | `agents/yt2b-analyst.md` | packet in `references/brief-template.md` |
| strategy | [[06 AI Team/01 Agents/yt2b-strategist\|yt2b-strategist]] | `agents/yt2b-strategist.md` | packet in `references/strategy-template.md`; approval follows |
| frames, hero | none (`hires_frames.py`, `generate_hero.py`) | | |
| images (AI, optional) | [[06 AI Team/01 Agents/visual-architect\|visual-architect]], [[06 AI Team/01 Agents/visual-critic\|visual-critic]] | Banana Claude plugin | only when the plugin is enabled; image approval note |
| research | [[06 AI Team/01 Agents/blog-researcher\|blog-researcher]] | `~/.claude/agents/` | companion or expanded scope |
| write, repair | [[06 AI Team/01 Agents/blog-writer\|blog-writer]] | `~/.claude/agents/` | packet in `references/writer-packet.md` |
| seo | [[06 AI Team/01 Agents/blog-seo\|blog-seo]] | `~/.claude/agents/` | |
| delivery | none (`layout_convert.py`, `blog_render.py`, `finalize_html.py`, `blog_preflight.py`) | | `references/delivery.md` |
| review | [[06 AI Team/01 Agents/blog-reviewer\|blog-reviewer]] | `~/.claude/agents/` | nonce-bound, blocking |
| evaluate, record | none (`evaluate.py`, `make_run_note.py`, `queue.py`) | | `05 Evaluations/pipeline-rubric.md` |

`dispatch: enabled` in an agent note means the orchestrator may call it in a
normal run; `disabled` means it needs the plugin enabled or a user decision.
