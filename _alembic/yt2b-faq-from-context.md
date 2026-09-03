---
name: YT2B FAQ from this note
id: yt2b-faq-from-context
prompt: "{=CONTEXT=}"
replaceSelection: false
humanize: false
linkDepth: 0
providerId: default-claude-cli
yt2b_id: faq-from-context
yt2b_hash: sha256:18eb5c9d20d6cf12
---
Write an FAQ section from this note. Return only markdown that starts with the line `## FAQ`.

Rules:
- Three to five questions that readers actually ask about this topic and that the note answers with its own facts. Phrase each as a `### ` heading the way people search.
- Skip any question the note cannot answer. If fewer than three remain, return only `<!-- yt2b: fewer than three answerable questions in this draft -->`.
- Each answer: 40 to 80 words, answer in the first sentence, then the reason. No new facts, numbers as written.
- When an answer rests on the video, attribute it: "<creator> shows at [mm:ss] ...", with the literal [mm:ss] placeholder for the author to fill.
- No marketing questions, no "why choose us".
- Never use em dashes or en dashes.

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
