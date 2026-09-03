# Setup interview: the `setup` command

`setup` captures the author's audience, positioning, voice and credentials once, writes the files every later stage reads, and refreshes the Writers Alembic workflows. The orchestrator runs it at stage 2 when root `VOICE.md` or `BRAND.md` is missing, and whenever the user asks for `setup`. It writes files inside the vault (plus the persona JSON that blog-persona owns); it never publishes, never commits and never prints a secret.

## Inputs, tools and rules

- Tools: AskUserQuestion for the rounds, Read, Write, Bash for `alembic_sync.py` and the Settings update.
- Pre-fill from what exists: root `BRAND.md` and `VOICE.md`, `06 AI Team/03 Knowledge/04 Voice/Author Profile.md`, `00 Home/Settings.md`, the active persona (`~/.claude/skills/blog-persona/references/active-persona.json`). Show the current value as the default and let the user confirm or change it; never re-ask what a default already answers.
- Templates: `_templates/BRAND.md`, `_templates/VOICE.md`, `_templates/Author Profile.md`. Placeholders look like `{{name}}`. An inline placeholder takes one line. A placeholder alone on a line takes one or more bullet lines with the same indentation. Numbered placeholders (`{{taboo_phrase_1}}`, `{{author_same_as_1}}`, `{{author_expertise_1}}`) are list items: fill as many as answered, delete the unused lines, add lines when there are more answers. `{{date}}` is today (YYYY-MM-DD). No `{{` may survive in a written file; write `none` for an empty answer.
- One round per AskUserQuestion call, at most four questions per call, options where they exist, free text through "Other". When the chat surface cannot show AskUserQuestion (some ACP clients), ask the same questions as one plain chat message per round and wait for the reply.
- No em dashes or en dashes in anything written. Minimal, professional wording; no marketing filler.

## Rounds

Round 1, Audience (BRAND.md, Audience)
1. Primary reader: role and context. Optional secondary reader.
2. Expertise level: beginner | intermediate | advanced | mixed.
3. Three problems the reader is actively trying to solve.
4. One or two misconceptions the reader holds (used for information-gain angles).

Round 2, Positioning and differentiation (BRAND.md, Positioning and Topic Scope)
1. Official entity name (person or brand) and one-sentence mission.
2. Distinctive point of view, and what the brand is not.
3. Up to three competitors or alternatives with one differentiator each (`none` allowed).
4. Topics in scope, partial scope (only with an original angle) and out of scope.

Round 3, Voice (VOICE.md)
1. Tone: matter-of-fact and formal | warm and plain | casual and direct | playful (maps to the persona sliders, table below).
2. Person: second person "you" | first person "I" | first person plural "we" | mixed.
3. Sentence ceiling in words: 20 | 25 | 30 | other. Contractions: full | partial | none. Summary box label (default Key Takeaways).
4. Taboo phrases: phrases the author never uses, one per line. Offer the default list below as the starting answer.

Round 4, Expertise and credentials for E-E-A-T (Author Profile, BRAND.md sameAs and disclosures, Settings `author`)
1. Full name and job title.
2. Years in the field and one or two notable works (projects, employers, publications, talks).
3. Author page URL and official profile URLs (LinkedIn, GitHub, YouTube, X, Mastodon).
4. Disclosure sentence (affiliations, sponsorships, AI assistance) and expertise limits (topics written as a reporter rather than a practitioner).

Round 5, Site and call to action (Settings `site_url`, BRAND.md)
1. Site URL (canonical, https). Used for the `canonical` field and the Person `url` fallback.
2. Call to action for the end of a post: newsletter | product or service | community | none.

Round 6, Visuals (Settings `visuals`)
1. frames | frames+charts | frames+charts+ai. Explain in the question: frames are the video's real key moments; charts are inline SVG when the brief lists data points (no cost); ai adds Banana Claude heroes and diagrams (paid, one approval per image, plugin must be enabled).

Round 7, Publishing target (BRAND.md, Publishing)
1. Writing Studio export (Manuscript HTML, PDF, DOCX) | WordPress from Writing Studio | another CMS through the publish kit | markdown only.
2. Optional: paths to 5 to 10 published posts in the author's voice for style learning.

## Where each answer goes

| Answer | Destination |
|---|---|
| Round 1 | `BRAND.md` Audience |
| Round 2 | `BRAND.md` Positioning, Topic Scope |
| Round 3 tone, person, ceilings, label | `VOICE.md` Pronoun stance, Lexical rules, Voice fingerprint, Readability target, Tone in three lines; persona JSON |
| Round 3 taboo phrases | `VOICE.md` `## Taboo phrases`, one phrase per bullet (evaluate.py counts them); `BRAND.md` keeps a pointer, not a copy |
| Round 4 | `Author Profile.md` properties `name`, `url`, `job_title`, `same_as`, `expertise`, `disclosure`, `bio_short` plus the body sections; `BRAND.md` sameAs and Required disclosures; Settings `author` copied from the profile `name` |
| Round 5 | Settings `site_url`; `BRAND.md` Homepage and Call to action |
| Round 6 | Settings `visuals` |
| Round 7 | `BRAND.md` Publishing; style learning below |

Write order:

1. Render `_templates/BRAND.md` to root `BRAND.md` and `_templates/VOICE.md` to root `VOICE.md`. They must be real files at the vault root (never symlinks) because claude-blog auto-loads them through `load_untrusted_root.py`, which refuses symlinks. The `Last updated` line gets today's date on every write.
2. Render `_templates/Author Profile.md` to `06 AI Team/03 Knowledge/04 Voice/Author Profile.md`. `bio_short` is one or two sentences: the topic fit ("writes about X after N years doing Y") and the expertise limit ("does not cover Z"). `expertise` lists the in-scope topics as short nouns. `same_as` holds only official profile URLs.
3. Update Settings without touching its body:

   ```bash
   python3 - <<'PY'
   import sys; sys.path.insert(0, "skills/youtube-to-blog/scripts")
   import yt2b_common as c
   root = c.find_vault_root()
   c.update_note(root / c.SETTINGS_NOTE, {"author": "<profile name>", "site_url": "<site url or empty>", "visuals": "<frames|frames+charts|frames+charts+ai>"})
   PY
   ```

4. Persona (next section).
5. Optional style learning (section after).
6. `python3 "skills/youtube-to-blog/scripts/alembic_sync.py" --vault "<vault>"`.
7. Verify: from the vault root, `python3 "$HOME/.claude/scripts/load_untrusted_root.py" BRAND.md` and the same for `VOICE.md` exit 0 with no `[!] WARNING` line; `grep -n "{{" BRAND.md VOICE.md "06 AI Team/03 Knowledge/04 Voice/Author Profile.md"` prints nothing.

## Tone to persona mapping

| Tone choice | funny_serious | formal_casual | respectful_irreverent | enthusiastic_matter_of_fact |
|---|---|---|---|---|
| matter-of-fact and formal | 0.8 | 0.2 | 0.2 | 0.8 |
| warm and plain | 0.6 | 0.5 | 0.2 | 0.5 |
| casual and direct | 0.5 | 0.8 | 0.4 | 0.5 |
| playful | 0.3 | 0.8 | 0.6 | 0.3 |

Readability from Round 1: beginner gives the consumer tier (Flesch grade 6 to 8, ease 60 to 80); intermediate or mixed gives professional (grade 8 to 10, ease 50 to 60); advanced gives technical (grade 10 to 12, ease 30 to 50). Sentence length mean is about 0.65 times the ceiling, standard deviation about 0.25 times the ceiling, both rounded. Contraction frequency: full 0.8, partial 0.5, none 0.0.

## Persona through blog-persona

Command: `/blog persona create <persona-name>` (Skill tool: `blog-persona`, args `create <persona-name>`). Persona name: `yt2b-` plus the slug of the entity name (fallback: the author name). Answer its six steps from the rounds instead of asking again: brand basics from Rounds 2 and 4, tone sliders from the table, vocabulary tier and readability from Round 1, do and don't lists from `BRAND.md` Always do and Never do (each taboo phrase becomes a "Don't use <phrase>" entry), summary label from Round 3, voice samples from Round 7 (local paths are not URLs; leave `voice_samples` empty and use style learning instead). Then `/blog persona use <persona-name>`. The JSON lands in `~/.claude/skills/blog-persona/references/personas/<persona-name>.json` and the active pointer in `~/.claude/skills/blog-persona/references/active-persona.json`. Copy the four slider values into the `VOICE.md` fingerprint section. If a persona with that name exists, blog-persona asks before overwriting; on a refresh, overwrite.

## Optional: learn from existing posts

`/blog style learn <paths>` (Skill tool: `blog-style`) with the 5 to 10 posts from Round 7. The skill runs `style_learn.py` (installed with the claude-blog plugin; on this machine under `~/.claude/plugins/cache/agricidaniel-blog/claude-blog/<version>/scripts/`, not under `~/.claude/scripts/`). Paste its markdown block into `VOICE.md` under `## Reference samples` in place of the placeholder. If the measured mean sentence length differs from the Round 3 answer by more than four words, tell the user and offer to adjust the persona.

## `--auto`

No questions. Defaults, neutral voice:

- Audience: practitioners who searched for the video's topic and want the answer without watching the whole video; expertise mixed; problems: find the answer fast, judge whether the method applies to their setup, jump to the right moment; misconception: a summary is as good as the method.
- Positioning: entity is the author name; mission "companion articles that make useful videos searchable and citable"; POV none; competitors none; scope: the topics of the queued videos.
- Voice: warm and plain, second person, ceiling 25, paragraph ceiling 150, contractions partial, label Key Takeaways, default taboo list: in today's fast-paced world, game-changer, unlock the power, it's important to note, in conclusion, delve into, seamlessly, cutting-edge, revolutionize.
- Author: Settings `author`; if empty, `git config --get user.name`; if empty, the login name, flagged in the summary as "replace before publishing". Job title "Author", `url` and `same_as` `none`, disclosure "This article is a companion to a video; the creator is credited in the first paragraph." Expertise: the video's topic.
- Site URL: existing Settings value or empty (no canonical). Call to action: none. Visuals: `frames+charts`. Publishing target: markdown only.
- No persona, no style learning. Then `alembic_sync.py`. The summary states that the voice is neutral and that `setup` without `--auto` replaces it.

## Refresh later

Run `setup` again: every round pre-fills from the current files, all four destinations are rewritten, the persona is overwritten, then `alembic_sync.py` runs and lists user-edited workflows under `skipped`. Offer `--force` for those; never add it on the user's behalf. Hand edits to `BRAND.md` or `VOICE.md` need only `alembic_sync.py` afterwards (SOP: `06 AI Team/03 Knowledge/02 SOPs/Set up voice and expertise.md`).

## Completion summary

List the files written with vault-relative paths, the persona name, the Settings properties changed, the workflow counts (written, unchanged, skipped) and the two verification lines. End with the next step: queue a video (`queue add <url>`) or run the full pipeline.
