# youtubetoblog Home

Obsidian plugin that owns the vault's landing page and default left sidebar. Empty tabs get the YouTube input, rights and mode chips, pipeline actions, discovery links and recent runs. The sidebar puts New chat, the main dashboard, feeds, discovery, sources, pipeline rooms and live counts in one place. **Queue open source** writes source-to-queue and queue-to-source links. Writing Studio remains available at the bottom without taking over startup.

## What Process does

1. Validates the link with the same four URL forms as `yt2b_common.youtube_video_id` (watch, youtu.be, shorts, live).
2. Creates `01 Queue/<YYYY-MM-DD>-<videoId>.md` with the same frontmatter as `queue.py add` (note `from the landing page`). An existing queue item opens for review without another automatic agent call; its rights and mode remain authoritative. Concurrent submissions of the same video are guarded across Home views.
3. Hands the run prompt to the Agent Client plugin with `runPromptInChat({agentId: "claude-code-acp", viewType: "right-pane", autoSend: true})`. Process runs `full` and stops at the strategy approval; Analyze only runs `analyze` and stops after the brief. Without Agent Client the queue note opens and a notice explains what is missing.

Enter processes, Esc clears the input. Both Process and Analyze only can incur provider charges, as stated beside the actions. Existing queue items can be continued by asking Agent Client to resume the linked run with the youtube-to-blog skill.

## Install

Copy `manifest.json`, `main.js` and `styles.css` into `.obsidian/plugins/youtubetoblog-home/` and enable the plugin. This folder is the canonical source; the copy under `.obsidian/plugins/` is gitignored and installed per machine. Disable Home tab and Commander, because this plugin owns both surfaces. Its workspace shortcuts open the dedicated Sources, Queue, Videos, Blogs, Approvals and Evaluations pages instead of exposing raw Base files. In Writing Studio, turn off Open on startup.

## Settings

Wordmark, replace empty tabs, open dashboard sidebar on startup, show recent runs. Rights and writing mode defaults come from `00 Home/Settings.md`. The Setup and help button opens the Home note. Blocked and completed runs are excluded from the Active count.

MIT, Daniel Agrici.

## Offline behavior tests

Run `node --test plugins/youtubetoblog-home/tests/home.test.cjs`. These use Obsidian API stubs and do not replace native Obsidian acceptance.

For optional browser layout and interaction checks, run `python3 plugins/youtubetoblog-home/tests/browser_smoke.py` with Patchright and Chromium already installed. It executes the plugin source with synthetic Obsidian APIs, blocks browser network traffic, checks three viewport sizes, and writes screenshots/results to a temporary folder. This is not a native Obsidian acceptance test.
