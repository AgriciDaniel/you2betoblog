# Set up you2toblog

This guide prepares a new preview copy without putting personal content or API keys into the vault.

## Before you start

The repository is under release review. Use the public claude-blog v2.1.1 release pinned below. Earlier documentation linked its private development mirror; that link is not needed for this setup.

The required video analyzer is licensed for personal, educational, and non-commercial use. Review its [pinned license](https://github.com/docusphere/video-analyzer/blob/151e8782c564093c3aa7339e2adc744aab25001b/LICENSE) before using this workflow for business or client work. Commercial use requires written permission from that project's copyright holder.

## 1. Install the basic tools

Install these on the computer that will run Obsidian:

- Obsidian Desktop 1.13.0 or newer (the Home plugin minimum)
- Claude Code
- Node.js with npm, used to reproduce the pinned patched plugins
- Python 3.11 or newer
- `yt-dlp`
- `ffmpeg` and `ffprobe`

The pipeline also uses the `video-analyzer` and `claude-blog` Claude Code plugins. These are separate from the Obsidian plugin installer below; installing the Obsidian plugins does not install the analysis or writing tools. Their pinned versions and source links are listed in `_system/plugin-lock.json`.

### Install the analysis and writing tools

The Obsidian plugin installer does not install these tools. Review their licenses and install scripts first. These commands install Claude skills and agents into your user profile; run them yourself after reviewing any existing installation you need to preserve.

For claude-blog, use the public v2.1.1 tag and verify its commit:

```bash
git clone --depth 1 --branch v2.1.1 https://github.com/AgriciDaniel/claude-blog.git
cd claude-blog
git rev-parse HEAD
```

The result must be `aec971ac511370c6216cd93776c9cf2fec97b32a`. Inspect `install.sh`, then run `bash install.sh`. It installs scripts, agents, templates, and supporting references, and attempts to install the Python dependencies. It can overwrite a previous user installation, so back up existing files first. Follow any dependency warnings it prints. Return to this vault before running its commands.

For video-analyzer, follow the [upstream setup instructions at the pinned commit](https://github.com/docusphere/video-analyzer/tree/151e8782c564093c3aa7339e2adc744aab25001b). Install that exact commit, its Python dependencies, and run its preflight. The canonical skill location is `~/.claude/skills/analyze`; the doctor also accepts `VIDEO_ANALYZER_DIR` pointing to the checkout. Do not replace an existing analyzer installation without reviewing it.

The analyzer and claude-blog renderer have separate Python/browser dependencies. A successful `doctor.py` check is required before using the pipeline. The required scripts and agent hashes for the public blog release are recorded in `_system/plugin-lock.json`.

## 2. Open the vault

Clone this repository, then open its folder as an Obsidian vault. When Obsidian asks about community plugins, review the list before enabling it.

The selected community plugins are:

- Agent Client, for Claude Code conversations inside Obsidian
- Writers Alembic, for focused writing actions
- Writing Studio, for finishing and exporting articles
- Image Layouts, for article image arrangements
- RSS Dashboard, an optional discovery surface

RSS Dashboard must use the pinned 2.6.0 source plus `plugins/rss-dashboard-safe-save.patch`. Writing Studio must use its pinned 3.1.0 source plus `plugins/writing-studio-no-startup-restore.patch`. Do not replace either with an unpatched community build. The main video-to-blog workflow works without RSS Dashboard.

## 3. Install the pinned Obsidian plugins

First inspect the exact plan. This is read-only:

```bash
python3 skills/youtube-to-blog/scripts/install_plugins.py --vault . plan
```

Then run the installer. It downloads only the pinned releases, builds the two patched plugins from exact upstream commits, audits production dependencies, runs RSS tests, verifies every installed hash, and enables the selected plugin ids in this vault:

```bash
python3 skills/youtube-to-blog/scripts/install_plugins.py --vault . install
```

If a plugin is already installed with different files, the command stops. Review why it differs, then rerun with `install --replace` if replacement is intended. The old folder is moved to a timestamped backup for rollback. Existing plugin data is preserved, and an unsafe RSS save template is refused.

Reload Obsidian with `Ctrl+R`. The you2toblog dashboard should become the landing page and the first item in the left sidebar.

## 4. Connect Agent Client

Install the pinned Claude Agent Protocol adapter:

```bash
npm install --global @agentclientprotocol/claude-agent-acp@0.73.0
```

In Agent Client settings, choose `claude-agent-acp` as the Claude Code command, leave automatic permission approval off, and set chat exports to `06 AI Team/02 Sessions`.

If Obsidian is installed through Flatpak, it may not see the computer's normal Node.js path. The System Manual explains the small wrapper needed for that setup.

## 5. Add provider keys safely

Never paste a key into a note, a chat, a command argument, or this repository.

Video analysis uses `GOOGLE_API_KEY` from the video-analyzer configuration outside the vault. Locate the installed analyzer with:

```bash
python3 skills/youtube-to-blog/scripts/doctor.py --vault . --print analyze-dir
```

From that directory, run its `scripts/preflight.py` once. It prepares the private configuration file under the user's configuration directory. Add the key there with a text editor, without printing it in the terminal.

Optional features may use these key names:

- `GROQ_API_KEY` or `OPENAI_API_KEY` for Whisper transcription when captions are unavailable
- `GOOGLE_AI_API_KEY` for separately approved AI image generation

The current workflow does not need a YouTube Data API key. RSS uses public feeds and video fetching uses `yt-dlp`.

## 6. Run the setup check

From the vault root, run:

```bash
python3 skills/youtube-to-blog/scripts/doctor.py --vault .
```

The check reports whether each key exists by name only. It does not print secret values, spend money, call a paid provider, or prove that billing and quotas are active.

Before the first article is written, set `author` and a real `site_url` in `00 Home/Settings.md`, then run the stricter check:

```bash
python3 skills/youtube-to-blog/scripts/doctor.py --vault . --for-write
```

## 7. Personalize the workspace

Open the Home note and use **Set up my voice**, or run `/youtube-to-blog setup` in Claude Code. Setup creates personal brand, voice, and author-profile files. Those files are ignored by Git by default.

Start with a video you own. Add it from Home, review the proposed strategy, approve the direction in its approval note, and let the pipeline continue. Publishing remains your action in Writing Studio.

## More help

- `06 AI Team/03 Knowledge/System Manual.md`
- `06 AI Team/03 Knowledge/02 SOPs/Use the landing page.md`
- `06 AI Team/03 Knowledge/02 SOPs/Run the pipeline from Home.md`
- `docs/ACCEPTANCE.md`
- `_system/plugin-lock.json`
- `skills/youtube-to-blog/SKILL.md`
