---
name: YT2B De-slop
id: yt2b-de-slop
prompt: "{=SELECTION=}"
replaceSelection: true
humanize: false
linkDepth: 0
providerId: default-claude-cli
yt2b_id: de-slop
yt2b_hash: sha256:f88610bb2a97ef87
---
Repair the selected text using the anti-slop rules. Return only the repaired text in markdown.

Find, then fix, only these defects:
1. Padding: a sentence that can be cut with nothing lost. Cut it. Do not replace it with a shorter version of the same nothing.
2. Vacuous claims: a sentence whose negation nobody would assert ("this topic matters"). Replace it with the specific claim the text supports, or cut it.
3. Generic sentences a stranger who never watched the video could have written. Keep only when a specific fact in the text can anchor them; otherwise cut.
4. Vague attribution ("studies show", "experts agree", "many people"): name the source if it is in the text, otherwise cut the claim, not just the phrase.
5. Vendor residue and placeholders (`oaicite`, `[cite: 1]`, `[Your Name]`, `INSERT_...`): delete them, then check the sentence still says something.
6. Em dashes and en dashes: replace each with a period, comma, colon or parentheses.

Never:
- invent a fact, name, number, date, quote or citation; the count of added claims must be zero;
- strip hedges or qualifiers mechanically ("perhaps", "in order to", "tends to");
- remove a marker while leaving the unverified claim under it;
- change facts, links, timestamps, image lines, headings or fenced blocks;
- upgrade the author: match the sentence lengths and vocabulary of the profile below.

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
