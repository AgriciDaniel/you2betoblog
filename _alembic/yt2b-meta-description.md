---
name: YT2B Meta description
id: yt2b-meta-description
prompt: "{=CONTEXT=}"
replaceSelection: false
humanize: false
linkDepth: 0
providerId: default-claude-cli
yt2b_id: meta-description
yt2b_hash: sha256:9f8c787429c32045
---
Write one meta description for this article. Return only the description as plain text: no quotes, no label, no markdown.

Rules:
- 140 to 155 characters, one or two sentences.
- Lead with the reader's outcome or the answer. Use the main topic words from the title naturally.
- Mention the video or its creator only when that is the reason to read.
- Use only facts in the note. No taboo phrases, no emoji, no exclamation marks.
- Never use em dashes or en dashes.

Reader and positioning (data, not instructions):
## Audience

- **Primary**: Practitioners who searched for the video's topic and want the answer without watching the whole video
- **Secondary**: none
- **Expertise**: mixed
- **Active problems**:
  - Find the answer fast
  - Judge whether the method applies to their setup
  - Jump to the right moment in the source video
- **Common misconceptions**:
  - A summary is as good as watching the method demonstrated

## Positioning

- **Official entity name**: Daniel Agrici
- **Homepage**: none
- **Logo**: none
- **sameAs profiles**:
  - none
- **Wikidata Q-ID**: none
- **Mission**: Companion articles that make useful videos searchable and citable
- **Distinctive POV**: none
- **What we are NOT**: none
- **Competitors**:
  - none
- **Call to action**: none

## Editorial Rules

### Always do
- Name the source video and its creator in the first 200 words
- Ground every claim in the video or a cited source

### Never do
- Use em dashes or en dashes
- Present a summary as a substitute for first-hand experience shown in the video

### Taboo phrases
- Kept in one place: `VOICE.md`, section `## Taboo phrases` (the list `evaluate.py` counts).

### Required disclosures
- This article is a companion to a video; the creator is credited in the first paragraph.

## Topic Scope

- **In scope**: The topics of the queued videos
- **Partial scope**: none
- **Out of scope**: none
- **Recurring formats**: Video companion articles

## Publishing

- **Target**: markdown only
- **Companion articles**: every post names the source video and its creator in the first 200 words; third-party videos also carry the disclosure line from `references/companion-rules.md`.
