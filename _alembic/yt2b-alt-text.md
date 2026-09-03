---
name: YT2B Alt text for this image
id: yt2b-alt-text
prompt: "{=SELECTION=}"
replaceSelection: true
humanize: false
linkDepth: 0
providerId: default-claude-cli
yt2b_id: alt-text
yt2b_hash: sha256:fffb1f83184a1737
---
The selection is one image line from a blog draft, either `![alt](path)` or `![[file|caption]]`, possibly followed by a caption line. Return the same line(s) with descriptive text and nothing else.

Rules:
- Describe what a reader would see: subject, action, setting, and visible text worth knowing. 8 to 18 words.
- Start with the subject. Say "screenshot" or "slide" only when the medium matters.
- Keep the path or file name exactly as it is.
- `![alt](path)`: replace only the alt text.
- `![[file|caption]]`: the text after the pipe is the visible caption. Make it descriptive and keep any attribution in it (creator name, timestamp).
- If a caption line follows the image, keep it unchanged.
- Never use em dashes or en dashes.
