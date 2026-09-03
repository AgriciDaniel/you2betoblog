# Connect Gemini to your agent

The block between the markers is the README section, verbatim. The troubleshooting list after it feeds `06 AI Team/03 Knowledge/02 SOPs/Connect Gemini.md` and the doctor's hints.

<!-- readme:start -->
## Connect Gemini to your agent

One Gemini API key feeds three optional consumers. Each is configured its own way, always by name. Never paste the key into chat, a note, a command line or a repository.

1. Create the key in Google AI Studio: https://aistudio.google.com/apikey. Video analysis runs on any Gemini API project. Banana Claude image generation needs a billing-enabled project: enable billing and set the monthly spend cap in AI Studio before the first paid image.

2. video-analyzer, used by the analyze stage, reads `GOOGLE_API_KEY` from `~/.config/video-analyzer/.env`. First resolve the installed analyzer directory:

   ```bash
   python3 skills/youtube-to-blog/scripts/doctor.py --vault . --print analyze-dir
   ```

   Change to the reported directory, then run `python3 scripts/preflight.py` without `--check` to scaffold the file. Add the key with a text editor.

   When the key is missing the command creates `~/.config/video-analyzer/.env` (mode 600) with an empty `GOOGLE_API_KEY=` line and exits 3. Fill the line and run it again; it exits 0 when ffmpeg, ffprobe, yt-dlp and the key are all present. Optional `GROQ_API_KEY` or `OPENAI_API_KEY` in the same file turn on Whisper transcripts for videos without captions.

3. Banana Claude, optional, makes AI heroes and diagrams. It takes the key as the sensitive plugin setting `google_ai_api_key` and never reads files or shell variables. Install and enable it from Claude Code:

   ```text
   /plugin marketplace add AgriciDaniel/banana-claude
   /plugin install banana-claude@banana-claude-marketplace
   /plugin enable banana-claude@banana-claude-marketplace
   /reload-plugins
   ```

   Claude Code asks for `google_ai_api_key` when you enable the plugin. It installs disabled because every image is a paid call; before each one it shows the prompt, the model and a nominal estimate and waits for your approval.

4. The automatic third-party hero fallback runs claude-blog's `generate_hero.py` with `GOOGLE_AI_API_KEY` and the keyed stock variables removed from its process environment. That forces the no-key Openverse route. Direct paid Gemini heroes are not part of this fallback; use Banana Claude's approved plan when you want one.

Claude itself needs no key. Agent Client, the `claude-agent-acp` adapter and Writers Alembic's Claude CLI provider all run the logged-in `claude` command.

Run the Setup check (`doctor.py`) at any time: it reports each key by name and presence only.
<!-- readme:end -->

## Troubleshooting

- `preflight.py` exits 3: the `GOOGLE_API_KEY=` line is empty. Edit `~/.config/video-analyzer/.env`; the format is `KEY=value` with no quotes or spaces.
- Doctor reports `GOOGLE_API_KEY` missing although the file has it: check for a BOM, quotes or a trailing space, then confirm doctor found the right analyze folder (`doctor.py --print analyze-dir`, override with `VIDEO_ANALYZER_DIR`).
- `/banana-claude:banana doctor` says the key is missing: run `/plugin enable banana-claude@banana-claude-marketplace` again; it prompts for `google_ai_api_key`. Do not write the key into `settings.json` or `.mcp.json`.
- A Banana plan is rejected for PNG output: request `image/jpeg`; the current plugin refuses PNG plans as a conservative API policy.
- A non-Banana hero unexpectedly attempts Gemini: stop the run and verify that the command contains every `env -u` guard from `references/banana-images.md`. Do not add `GOOGLE_AI_API_KEY` to Agent Client for this fallback.
- HTTP 429 or quota errors from Gemini during analysis: wait, or enable billing on the project; rerunning the analyze stage is safe.
- Rotated key: update the `.env` file, re-enter the Banana plugin setting, update the shell export. Pending Banana approvals expire on their own (30 minutes).
