---
type: yt2b-knowledge
title: Generate images with Banana Claude
kind: sop
created: 2026-09-03
updated: 2026-09-03
tags:
  - yt2b
  - sop
---
# Generate images with Banana Claude

Every image is a paid Gemini call. Nothing is generated without your approval in the chat.

1. Set `visuals` to `frames+charts+ai` in [[Settings]] (or leave it and rely on the third-party hero rule).
2. Enable the plugin ([[Connect Gemini]] step 3) and run `/banana-claude:banana doctor` in the chat once.
3. Run "Write approved blogs". When a blog needs an AI hero, the agent shows the brief, the exact prompt, the model and the nominal estimate, then Claude Code asks for the paid call. Approve or decline.
4. The image lands in `03 Blogs/<blog>/images/`, the critic's verdict appears in the chat, `hero.jpg` is cropped from it, and the approval note in [[Home]] (Approvals view, kind image) records the estimate and the decision.
5. Want a change: ask for a targeted fix or a regeneration. Each attempt is a new plan and a new approval.
6. Declined, disabled or failed: the fallback ladder runs (real thumbnail for own videos, `generate_hero.py` for third-party videos). Nothing is charged without step 3.

Flow and brief fields: `skills/youtube-to-blog/references/banana-images.md`.
