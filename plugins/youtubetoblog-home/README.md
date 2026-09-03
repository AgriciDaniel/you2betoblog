# youtubetoblog Home

Obsidian plugin that owns the vault's landing page and default left sidebar. Empty tabs get the YouTube input, rights and mode chips, pipeline actions, discovery links and recent runs. The sidebar puts New chat, the main dashboard, feeds, discovery, sources, pipeline rooms and live counts in one place. **Queue open source** writes source-to-queue and queue-to-source links. Writing Studio remains available at the bottom without taking over startup.

## What Process does

1. Validates the link with the same four URL forms as `yt2b_common.youtube_video_id` (watch, youtu.be, shorts, live).
2. Creates `01 Queue/<YYYY-MM-DD>-<videoId>.md` with the same frontmatter as `queue.py add` (note `from the landing page`), or reports that the video is already queued.
3. Hands the run prompt to the Agent Client plugin with `runPromptInChat({agentId: "claude-code-acp", viewType: "right-pane", autoSend: true})`. Process runs `full` and stops at the strategy approval; Analyze only runs `analyze` and stops after the brief. Without Agent Client the queue note opens and a notice explains what is missing.

Enter processes, Esc clears the input.

## Install

Copy `manifest.json`, `main.js` and `styles.css` into `.obsidian/plugins/youtubetoblog-home/` and enable the plugin. This folder is the canonical source; the copy under `.obsidian/plugins/` is gitignored and installed per machine. Disable Home tab and Commander, because this plugin owns both surfaces. Its workspace shortcuts open the dedicated Sources, Queue, Videos, Blogs, Approvals and Evaluations pages instead of exposing raw Base files. In Writing Studio, turn off Open on startup.

## Settings

Wordmark, default rights, default mode, replace empty tabs, open dashboard sidebar on startup, show recent runs.

MIT, Daniel Agrici.
