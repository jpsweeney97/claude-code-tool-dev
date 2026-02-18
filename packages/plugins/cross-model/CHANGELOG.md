# Changelog

## [1.0.0] — 2026-02-18

### Added

- Context injection MCP server bundled (vendored from `packages/context-injection/`)
- `codex-reviewer` agent for single-turn code review
- Opt-in nudge hook: suggests `/codex` after repeated Bash failures (`CROSS_MODEL_NUDGE=1`)
- `context-injection-contract.md` in plugin references (canonical)

### Changed

- Renamed from `codex` to `cross-model`
- Plugin is now canonical source for consultation contract, profiles, and context injection contract
- All tool names updated for plugin rename (`mcp__plugin_cross-model_codex__*`, `mcp__plugin_cross-model_context-injection__*`)
- Context injection tools no longer require separate repo-level MCP configuration

### Migration

Uninstall old plugin and install new:
```bash
claude plugin uninstall codex@cross-model
claude plugin marketplace update cross-model
claude plugin install cross-model@cross-model
```

## [0.1.0] — 2026-02-18

### Added

- `/codex` skill (237 lines, 7 governance rules)
- `codex-dialogue` subagent for extended multi-turn consultations
- Consultation contract (16 sections, normative) and 5 named profiles
- PreToolUse enforcement hook: tiered credential detection (strict/contextual/shadow)
- PostToolUse consultation event logging to `~/.claude/.codex-events.jsonl`
- Auto-configured `codex mcp-server` MCP connection
