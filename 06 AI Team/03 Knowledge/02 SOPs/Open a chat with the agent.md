---
type: yt2b-knowledge
title: Open a chat with the agent
kind: sop
created: 2026-09-03
updated: 2026-09-03
tags:
  - yt2b
  - sop
---

# Open a chat with the agent

The agent is Claude Code, reached through the Agent Client plugin and the `claude-agent-acp` adapter. Every chat starts in the vault root, so the `youtube-to-blog` skill and the `yt2b-*` agents are already loaded.

1. **New chat button.** At the top of the left sidebar, under the `YouTube to blog` wordmark, press the **New chat** pill. It runs the Agent Client command `Open new chat view` (id `agent-client:open-new-chat-view`) and opens a fresh Claude Code session in the right pane. The button is a Commander action, so it is also in the command palette as `Commander: New chat`.
2. **Ribbon icon.** The left ribbon shows a chat bubble (`Open agent client`). It opens the existing chat view, or creates one when none is open. Use it to get back to a conversation you already started.
3. **Home buttons.** The `agent-command` cards on [[00 Home/Home|Home]] (Add to queue, Setup check, Analyze queue, Propose blog strategy, Write approved blogs, Run the full pipeline) each open a chat in the right pane with a prepared prompt and send it at once. Use them for pipeline work; use New chat for a free question.
4. **What the right pane shows.** The chat view has the agent picker and model selector at the top, the conversation in the middle (tool calls fold into blocks, file edits show as diffs), and the input box at the bottom. With `Auto-mention active note` on, the note you are editing is attached as context, and wikilinks in your prompt expand to the note contents. Press Enter to send, Shift+Enter for a new line, and the stop button (or `Cancel current message`) to interrupt.
5. **Permission prompts.** `Auto-allow permissions` is off, so whenever the agent wants to run a command, write a file or read outside the vault, a prompt appears inline in the conversation with **Allow** and **Reject** buttons (also the commands `Approve active permission` and `Reject active permission`). Nothing runs until you answer. Read the command line in the prompt before allowing; a declined request is reported back to the agent, which then asks or stops.
6. **Export a session.** Press the export button in the chat header, or run the command `Agent Client: Export chat`. The transcript lands in `06 AI Team/02 Sessions` as `agent_client_<date>_<time>.md` with the `agent-client` tag in its frontmatter and opens after export. Add the important decisions to [[06 AI Team/02 Sessions/handoff|the handoff note]] so the next session starts from them.

If the chat shows a connection error, check the adapter from a terminal (`claude-agent-acp --version`) and see the Install section of the README for the Flatpak wrapper. Versions are pinned in `_system/plugin-lock.json`.
