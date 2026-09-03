---
name: YT2B Tighten this section
id: yt2b-tighten-section
prompt: "{=SELECTION=}"
replaceSelection: true
humanize: false
linkDepth: 0
providerId: default-claude-cli
yt2b_id: tighten-section
yt2b_hash: sha256:cc5db8213c7d9848
---
Cut 20 to 35 percent of the words from the selected section without losing anything a reader would miss. Return only the tightened section in markdown.

Rules:
- Cut padding: restatements, throat-clearing openers, closing summaries of the paragraph above, and any sentence that can be deleted with nothing lost.
- Keep every claim, number, link, timestamp, image line, heading and attribution to the creator.
- Merge or split paragraphs freely. Keep the heading text as it is.
- Keep hedges that carry meaning ("in this demo", "often", "on this dataset"). Cut a hedge only together with a vacuous claim.
- Do not add facts. Do not replace a cut sentence with a shorter version of the same nothing.
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
