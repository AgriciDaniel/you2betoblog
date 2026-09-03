---
name: YT2B Key Takeaways box
id: yt2b-key-takeaways
prompt: "{=CONTEXT=}"
replaceSelection: false
humanize: false
linkDepth: 0
providerId: default-claude-cli
yt2b_id: key-takeaways
yt2b_hash: sha256:5bbc9f1609cddedb
---
Read the whole note and write its Key Takeaways box. Return only the box, in this exact shape:

> **Key Takeaways**
> - First takeaway.
> - Second takeaway.

Rules:
- Three to five bullets. Each is one sentence under 25 words and states a concrete claim, number or action from the article, not a list of sections.
- Use only facts present in the note. Keep numbers as written. Name the creator once when the article attributes results to a video.
- Most useful bullet first.
- If the voice profile defines another summary label, use that label in place of "Key Takeaways".
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
