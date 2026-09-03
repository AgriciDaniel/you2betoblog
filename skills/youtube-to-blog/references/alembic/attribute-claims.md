---
name: YT2B Attribute claims to the creator
id: yt2b-attribute-claims
prompt: "{=SELECTION=}"
replaceSelection: true
humanize: false
linkDepth: 0
providerId: default-claude-cli
yt2b_id: attribute-claims
---
Rewrite the selection so every claim, number, recommendation or demonstrated result that comes from the video is attributed to its creator with a timestamp placeholder. Return only the rewritten text in markdown.

Rules:
- Attribution forms: "<creator> shows at [mm:ss] that ...", "At [mm:ss], <creator> ...", or "(video, [mm:ss])" after the sentence. Use the creator's name when it appears in the selection; otherwise write "the creator".
- Write the literal placeholder [mm:ss]. The author replaces it with the real timestamp and deep link.
- Attribute once per claim, not once per sentence. Leave the author's own analysis and general statements unattributed.
- Keep every number exactly as written. Add no facts. Never turn the creator's experience into first person.
- Direct quotes: at most 25 words each, in quotation marks, attributed.
- Keep headings, links, image lines and fenced blocks unchanged.
- Never use em dashes or en dashes.
