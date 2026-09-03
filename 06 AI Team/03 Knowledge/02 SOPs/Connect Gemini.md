---
type: yt2b-knowledge
title: Connect Gemini
kind: sop
created: 2026-09-03
updated: 2026-09-03
tags:
  - yt2b
  - sop
---
# Connect Gemini

One key from Google AI Studio can serve video analysis and optional approved Banana images. Never paste the key into the chat or a note.

1. Create the key at https://aistudio.google.com/apikey. Enable billing on the project and set a spend cap only if you want AI images.
2. Video analysis: locate the analyzer with `python3 skills/youtube-to-blog/scripts/doctor.py --vault . --print analyze-dir`, then run `python3 scripts/preflight.py` from that reported directory. It creates `~/.config/video-analyzer/.env` when the key is missing. Put the key on the `GOOGLE_API_KEY=` line with a text editor, run the command again, expect exit 0.
3. Banana Claude, optional: `/plugin marketplace add AgriciDaniel/banana-claude`, `/plugin install banana-claude@banana-claude-marketplace`, `/plugin enable banana-claude@banana-claude-marketplace`, `/reload-plugins`. Claude Code asks for `google_ai_api_key` on enable.
4. The automatic non-Banana hero fallback explicitly removes Gemini and stock-key variables and uses Openverse. Do not configure `GOOGLE_AI_API_KEY` for that pipeline path. Direct paid hero generation is reserved for Banana's plan and approval flow.
5. Press "Setup check" in [[Home]]: doctor reports each key by name and presence.
6. Claude needs no key; Agent Client, the ACP adapter and Writers Alembic use the logged-in `claude`.

Troubleshooting and the README text: `skills/youtube-to-blog/references/gemini-connection.md`.
