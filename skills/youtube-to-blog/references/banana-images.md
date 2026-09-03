# AI images with Banana Claude

Scope: the 1200x630 hero and, when Settings `visuals` is `frames+charts+ai`, at most one grounded diagram per post. Real frames stay the primary visual; this flow never replaces them. Every provider call is paid, planned first and approved by the user in chat. The pipeline never spends without that approval.

## When

- Settings `visuals` contains `ai`: hero through Banana, optional diagram.
- Third-party rights and no hero after `hires_frames.py` (it writes `hero.jpg` only in own mode): Banana when it is enabled, otherwise the fallback ladder.
- Own mode without `ai`: the thumbnail hero from `hires_frames.py` stands; skip this file.
- `--auto`: never. A paid call needs a live approval, so `--auto` goes straight to the ladder without Banana.

## Availability check (no cost)

1. `~/.claude/settings.json`, key `enabledPlugins`, entry `banana-claude@banana-claude-marketplace` is `true` (doctor reports it; read the file with `json`, not by eye).
2. The MCP tools `banana_models`, `banana_plan` and `banana_generate` are listed in the session. If the plugin is enabled but the tools are missing, `/reload-plugins`.
3. `/banana-claude:banana doctor` once per session: read-only, no Google call, confirms Python, state folders and the key by presence.

Any failure sends the blog to the ladder and is logged in `run.md`.

## The brief the orchestrator hands over

Freeze it before planning; a changed brief needs a new plan. Sources: `strategy.md` visual notes, the brief's hero policy, the post title, and the visual language of the frames already in `images/` (so the hero matches the article).

| Field | Hero |
|---|---|
| subject | the one thing the article is about, as an object or scene, no people unless the video is about a person and the user asked |
| action | what the subject is doing or showing |
| context | setting that matches the video (desk, terminal, workshop, studio) |
| composition | 16:9, subject in the left or right two thirds, clean copy space, no borders |
| lighting | soft directional light, one source, no neon unless the frames are neon |
| style | photographic or clean illustration, consistent with the frames; no logos, no brand marks, no faces of real people |
| text | none baked in; a hero never needs text (typeset locally only when exact copy is required) |
| aspect and size | `aspect_ratio: 16:9`, `image_size: 1K`; the pipeline crops to 1200x630 |
| format | `mime_type: image/jpeg` (the current plugin rejects PNG plans) |
| output | `output_dir`: absolute path of `03 Blogs/<date> <slug>/images/` |
| label | `yt2b-hero-<slug>` (short, non-sensitive; the cost ledger stores only this) |
| privacy | `record_prompt: false`, `store: false`, no grounding |
| references | none. Never upload video frames or thumbnails as references: the rights statement Banana requires is not ours to give in third-party mode, and in own mode only the user can state it explicitly |

Model: call `banana_models` first, never route from memory. Default hero route `gemini-3.1-flash-image` at 1K. A diagram with labels uses `gemini-3-pro-image`. A plain hero may use the disclosed `planner_minimal` brief; a diagram needs a supplied structured brief that the user accepts.

## Handoffs

1. visual-architect (read-only plugin agent): for diagrams and anything with text or brand-sensitive content, hand it the brief fields, the model constraints from `banana_models` and no references; it returns the `banana.visual-brief.v1` packet and the compiled prompt. A plain hero stays inline.
2. Show the brief and the compiled prompt to the user; apply corrections.
3. `banana_plan` returns `approval_summary` (exact prompt, `brief_sha256`, model, size, nominal estimate, destination) and a single-use approval ID (30 minutes). Show the summary. Claude Code prompts for the paid tool itself; the user approves in chat. One approval, one attempt.
4. `banana_generate` with the approval ID. On any failure, stop; a retry is a new plan and a new approval.
5. visual-critic (read-only plugin agent): give it the same brief packet, `brief_sha256`, and the output path with its hash from the tool result. Verdicts: Pass, Targeted fix, Regenerate, Blocked. Targeted fix or Regenerate means asking the user for another paid attempt; Blocked or a declined retry means the ladder.
6. Post-process: keep the original output and its sidecar in `images/`; write `hero.jpg` as a 1200x630 centre crop (PIL `ImageOps.fit`, quality 88); write `hero-credit.txt`.

## Approval mirror note

The chat prompt is the gate; the note is the record. Create it before the paid call and update it after the decision.

```bash
python3 "skills/youtube-to-blog/scripts/approval.py" --vault "<vault>" create --kind image --run "<run dir>" --blog "<blog dir>" --title "AI hero for <slug>" --request-file "<file holding the approval summary: prompt, model, size, nominal estimate, destination>" --options "generate=Generate the hero, nominal estimate <usd>" --expires-hours 1
python3 "skills/youtube-to-blog/scripts/approval.py" --vault "<vault>" set "<note>" --status approved --decision "generated <images/file>, <model>, critic: Pass"
```

Fields: `kind: image`; `status` approved or declined (declined also when Banana was unavailable, with the reason in `decision`); `selected: [generate]` when approved; `cost_estimate` is the nominal estimate as text, for example `USD 0.04 nominal, one 1K JPEG output, not an invoice cap`. `approval.py` has no cost flag in its contract, so set that property with `yt2b_common.update_note("<note>", {"cost_estimate": "..."})`. The Decision section records the output path, model, `attempt_sha256` from the tool result, and the critic verdict. Never write the prompt into the note when the user asked for privacy; the hash is enough.

## hero-credit.txt

```text
AI-generated via <model> (Banana Claude <plugin version>, route <lite|flash|pro>). No attribution required.
Prompt hash: <sha256 of the compiled prompt, first 16 hex>
Brief hash: <brief_sha256>
Approval: 04 Approvals/queue/<date>-<videoId>-image.md
Generated: <YYYY-MM-DD>
Source file: images/<banana output file>
```

The first line keeps the shape `generate_hero.py` writes, so downstream checks treat both the same. No raw prompt: Banana keeps `record_prompt` off and the ledger stores only the label.

## Diagrams (only with `ai`)

At most one per post, only for a concept the video explains without a usable frame (the brief must list it as a chart or diagram candidate). Every label comes from the brief; the critic checks spelling; the image is placed as a single image with the caption "Diagram: <what it shows> (AI-generated)", never inside a layout group, and counts toward the rights cap on images.

## Fallback ladder

1. Banana Claude: enabled, allowed by Settings or by third-party need, approved, critic Pass or an accepted Targeted fix.
2. Own video: the real thumbnail hero that `hires_frames.py` already wrote. Nothing more to do.
3. Third-party video: `env -u GOOGLE_AI_API_KEY -u UNSPLASH_ACCESS_KEY -u PEXELS_API_KEY -u PIXABAY_API_KEY python3 "$HOME/.claude/scripts/generate_hero.py" --topic "<title>" --tags "<tag1,tag2,tag3>" --out "<blog dir>" --json`. The sanitized environment skips the external script's Gemini and keyed stock routes and forces Openverse (CC-licensed, credit written to `hero-credit.txt`). Output is `hero.png` or `hero.jpg`; the renderer accepts both. Do not remove the environment guard.
4. Everything failed: set the blog to `yt2b_status: blocked`, add a run log line, and tell the user to place a 1200x630 `hero.png` in the blog folder and rerun delivery. Never use a third-party frame or thumbnail as the hero.
