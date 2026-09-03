---
type: yt2b-knowledge
title: Run the pipeline from Home
kind: sop
created: 2026-09-03
updated: 2026-09-03
tags:
  - yt2b
  - sop
---

# Run the pipeline from Home

1. Open [[00 Home/Home|Home]] with the Agent Client plugin enabled and Claude Code set as its agent.
2. Press **Setup check** the first time on a machine. Fix what the table lists as missing, then press it again until every required check is OK.
3. Press **Setup voice and expertise** once per vault. Answer the interview; it writes `BRAND.md`, `VOICE.md` and the Author Profile and refreshes the Alembic workflows.
4. Add one task line per video under `## Inbox` and press **Add to queue**. Check the Queue table.
5. Press **Analyze queue**. The agent fetches, analyzes, segments and briefs every queued video, then stops. Answer the rights question if it appears.
6. Press **Propose blog strategy**. Open the approval note it names in `04 Approvals/queue`, tick the angles you want, answer the questions, set `status: approved` (see [[06 AI Team/03 Knowledge/02 SOPs/Approve a strategy|Approve a strategy]]).
7. Press **Write approved blogs**. When `pause_for_outline` is on, approve the outline note the same way and press the button again.
8. Read the completion summary, open the evaluation note from the Evaluations table, then open the article in Writing Studio to polish and publish.

**Run the full pipeline** does steps 5 and 6 for every queued video in one go and continues with step 7 for approvals that are already approved. Use the Chat section for follow-up questions in the same session.
