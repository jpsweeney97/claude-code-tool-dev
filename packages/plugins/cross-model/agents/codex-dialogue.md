---
name: codex-dialogue
description: "[RETIRED] Cross-model dialogue agent — context-injection was removed in T-07 7d. Use codex-collaboration /dialogue instead."
tools: Bash, Read, Glob, Grep
model: opus
---

## Retired

This agent is retired. The context-injection MCP server was removed as
part of the T-07 codex-collaboration cutover (slice 7d). The per-turn
loop depended on `process_turn` and `execute_scout` tools that no longer
exist.

**Use codex-collaboration `/dialogue` instead.** It provides orchestrated
multi-turn Codex consultations with Claude-side evidence gathering.

**Do not proceed.** Report this message to the caller and stop.
