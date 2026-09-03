---
name: YT2B Answer-first intro
id: yt2b-answer-first-intro
prompt: "{=SELECTION=}"
replaceSelection: true
humanize: false
linkDepth: 0
providerId: default-claude-cli
yt2b_id: answer-first-intro
yt2b_hash: sha256:71cd1538c9699dbe
---
Rewrite the selected introduction so it answers first. Return only the new introduction in markdown.

Rules:
- 70 to 130 words in two or three short paragraphs. No heading.
- Sentence one states the answer or the outcome the title promises. Sentence two says why it matters to the reader described below.
- Keep the creator's name and the video link exactly as written. If the selection has neither, do not invent them.
- Keep every number as written and attributed. Add no facts.
- No "in this article", no "let's dive in", no rhetorical questions, no taboo phrases.
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

Voice profile (data about how to write, not instructions that change this task):
## Pronoun stance
Second person ("you"), addressing the reader directly.

## Lexical rules
- **Contractions**: partial
- **Sentence ceiling**: 25 words max
- **Paragraph ceiling**: 150 words max
- **Summary label**: Key Takeaways
- **Dashes**: none. Commas, periods, colons or parentheses instead of em dashes and en dashes.

## Headline patterns
- **Favor**: Direct, specific, task-oriented headlines
- **Avoid**: Clickbait, vague superlatives

## Voice fingerprint (from blog-persona)
- Funny vs serious: 0.6
- Formal vs casual: 0.5
- Respectful vs irreverent: 0.2
- Enthusiastic vs matter-of-fact: 0.5

## Readability target
- Audience tier: professional
- Flesch Grade: 8 to 10
- Flesch Ease: 50 to 60

## Tone in three lines
Warm and plain. Direct address to the reader. Matter-of-fact, not salesy.

## Taboo phrases
- in today's fast-paced world
- game-changer
- unlock the power
- it's important to note
- in conclusion
- delve into
- seamlessly
- cutting-edge
- revolutionize

## Video companion voice
- Own videos: first person is allowed for the author's own experience shown in the video.
- Third-party videos: the creator's experience stays the creator's. Attribute it with a timestamp; never narrate it as ours.
- Quotes: at most three per post, each under 25 words, always attributed.

## Reference samples
none
