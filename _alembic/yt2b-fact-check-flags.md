---
name: YT2B Fact-check flags
id: yt2b-fact-check-flags
prompt: "{=SELECTION=}"
replaceSelection: true
humanize: false
linkDepth: 0
providerId: default-claude-cli
yt2b_id: fact-check-flags
yt2b_hash: sha256:da382f1e880b73f2
---
Return the selected text unchanged except for inserted markers. After each claim that needs support, insert a marker of exactly this form: [VERIFY: what to confirm, under 12 words].

Flag a claim when it carries a number, statistic, date, price, version, benchmark, superlative ("fastest", "the only", "always") or a quoted study, and the text does not support it with one of: a named source in the same or previous sentence, a timestamp such as [12:34] or a watch link, or a linked citation. Also flag first-person experience claims about work the video's creator did.

Rules:
- Place the marker right after the sentence that carries the claim. One marker per claim.
- Do not change, reorder or remove any word. Do not touch headings, links, image lines or fenced blocks.
- If nothing needs a marker, return the text exactly as it was.
- Never use em dashes or en dashes.

The author resolves each marker (adds a source, a timestamp, or rewrites the claim as qualitative) and deletes it.
