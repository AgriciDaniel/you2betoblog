---
type: yt2b-knowledge
title: doctor.py
kind: script
created: 2026-09-03
updated: 2026-09-03
tags:
  - yt2b
  - knowledge
  - script
---

# doctor.py

**Purpose.** Environment check for the pipeline: tools, video-analyzer and its preflight, keys by name, blog scripts and agents, browser, vault rooms, Obsidian plugins, Banana Claude state, root voice files. Run once per session; the first step of every command in [[skills/youtube-to-blog/SKILL|the skill]].

**Usage.**

```bash
python3 skills/youtube-to-blog/scripts/doctor.py --vault "<vault>"
python3 skills/youtube-to-blog/scripts/doctor.py --print analyze-dir
```

**Inputs.** The vault path (default: detected from the working directory), `VIDEO_ANALYZER_DIR` when set, `~/.config/video-analyzer/.env` (presence of names only), `~/.claude/scripts`, `~/.claude/agents`, `~/.claude/settings.json` (enabledPlugins), `.obsidian/community-plugins.json`.

**Outputs.** A table on stderr and one JSON object on stdout: `ok`, `required_failures`, `warnings`, `analyze_dir`, `whisper_key`, `vault`, `checks` (name, status ok | fail | warn | info, required, detail). `--print analyze-dir` prints only the path. No secret value is ever read into the output.

**Exit codes.** 0 every required check passes, 2 bad vault path, 4 a required check failed (also for `--print analyze-dir` when the analyzer is missing).

Related: [[06 AI Team/03 Knowledge/02 SOPs/Run the pipeline from Home|Run the pipeline from Home]].
