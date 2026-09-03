# Set up youtubetoblog

This guide prepares a new private-preview copy without putting personal content or API keys into the vault.

## 1. Install the basic tools

Install these on the computer that will run Obsidian:

- Obsidian Desktop
- Claude Code
- Python 3.11 or newer
- `yt-dlp`
- `ffmpeg` and `ffprobe`

The pipeline also uses the `video-analyzer` and `claude-blog` Claude Code plugins. Their pinned versions and source links are listed in `_system/plugin-lock.json`.

## 2. Open the vault

Clone the private repository, then open its folder as an Obsidian vault. When Obsidian asks about community plugins, review the list before enabling it.

The selected community plugins are:

- Agent Client, for Claude Code conversations inside Obsidian
- Writers Alembic, for focused writing actions
- Writing Studio, for finishing and exporting articles
- Image Layouts, for article image arrangements
- RSS Dashboard, an optional discovery surface

RSS Dashboard must use the pinned 2.6.0 source plus `plugins/rss-dashboard-safe-save.patch`. Do not replace that build with the unpatched community release. The main video-to-blog workflow works without RSS Dashboard.

## 3. Install the Home dashboard

The Home dashboard is local to this vault, so copy its three files into Obsidian's local plugin folder:

```bash
mkdir -p .obsidian/plugins/youtubetoblog-home
cp plugins/youtubetoblog-home/manifest.json .obsidian/plugins/youtubetoblog-home/
cp plugins/youtubetoblog-home/main.js .obsidian/plugins/youtubetoblog-home/
cp plugins/youtubetoblog-home/styles.css .obsidian/plugins/youtubetoblog-home/
```

Enable **youtubetoblog Home** in Obsidian, then reload Obsidian with `Ctrl+R`. The youtubetoblog dashboard should become the landing page and the first item in the left sidebar.

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

## 7. Personalize the workspace

Use the Setup button on Home, or run the skill's `setup` action in Claude Code. Setup creates personal brand, voice, and author-profile files. Those files are ignored by Git by default.

Start with a video you own. Add it from Home, review the proposed strategy, approve the direction in its approval note, and let the pipeline continue. Publishing remains your action in Writing Studio.

## More help

- `06 AI Team/03 Knowledge/01 Guidelines/System Manual.md`
- `06 AI Team/03 Knowledge/02 SOPs/Use the landing page.md`
- `06 AI Team/03 Knowledge/02 SOPs/Run the pipeline.md`
- `_system/plugin-lock.json`
- `skills/youtube-to-blog/SKILL.md`
