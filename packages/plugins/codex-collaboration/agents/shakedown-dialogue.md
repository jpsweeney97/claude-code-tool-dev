---
name: shakedown-dialogue
description: Contained pre-benchmark shakedown agent for B1 dialogue. Invoked by the shakedown-b1 skill. Do not use directly.
model: opus
maxTurns: 30
tools:
  - Read
  - Grep
  - Glob
  - mcp__plugin_codex-collaboration_codex-collaboration__codex_dialogue_start
  - mcp__plugin_codex-collaboration_codex-collaboration__codex_dialogue_reply
  - mcp__plugin_codex-collaboration_codex-collaboration__codex_dialogue_read
skills:
  - dialogue-codex
---

Execute the dialogue-codex skill procedure. Your Read, Grep, and Glob calls are constrained to the B1 scope by the containment guard — you can access any file within the scope directories. You do not need to manage containment — the harness handles it transparently.
