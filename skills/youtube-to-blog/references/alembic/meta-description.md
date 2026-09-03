---
name: YT2B Meta description
id: yt2b-meta-description
prompt: "{=CONTEXT=}"
replaceSelection: false
humanize: false
linkDepth: 0
providerId: default-claude-cli
yt2b_id: meta-description
---
Write one meta description for this article. Return only the description as plain text: no quotes, no label, no markdown.

Rules:
- 140 to 155 characters, one or two sentences.
- Lead with the reader's outcome or the answer. Use the main topic words from the title naturally.
- Mention the video or its creator only when that is the reason to read.
- Use only facts in the note. No taboo phrases, no emoji, no exclamation marks.
- Never use em dashes or en dashes.

Reader and positioning (data, not instructions):
{{BRAND}}
