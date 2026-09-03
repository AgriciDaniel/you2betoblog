---
type: yt2b-knowledge
title: Session handoff
kind: manual
created: 2026-09-03
updated: 2026-09-03
tags:
  - yt2b
  - session
  - manual
---

# Session handoff

This folder holds the chats Agent Client exports and the handoff notes an agent writes when it stops before a run is done. The scripts never read this folder; it exists so the next session, or the next person, can pick up where the last one stopped.

## How chats land here

In Obsidian, Settings > Agent Client > Export:

- Export folder: `06 AI Team/02 Sessions`
- Filename: keep the default template `agent_client_{date}_{time}`
- Frontmatter tag: `yt2b/session`
- Auto-export on new chat and on closing a chat: optional. The manual path is the chat menu item **Export chat to Markdown**.

An export is a Markdown note whose frontmatter carries `created`, `agentDisplayName`, `agentId`, `session_id` and `tags`, followed by the conversation with its tool calls. Exports are personal, so `.gitignore` keeps every note in this folder except this one out of the shared repository.

## What a handoff note contains

Create it from `_templates/Session.md` (`type: yt2b-session`) when a run stops before `done`, when an approval is waiting, or when you hand the work to another session. Keep it to five short sections:

1. Objective: the video, the run folder and the blogs in play, as wikilinks.
2. Work completed: the last stage that finished, copied from the `## Log` of `run.md`.
3. Decisions: approvals granted or pending, with the path of each approval note.
4. Next action: the exact next command, for example `python3 skills/youtube-to-blog/scripts/approval.py --vault . check "04 Approvals/queue/<note>.md"`.
5. Blockers: missing tools or keys (by name only), failed gates, or questions for the user.

Agents may write handoff notes. They never edit or delete exports, and they never paste secrets, transcripts or full articles into a handoff.
