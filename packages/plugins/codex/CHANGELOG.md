# Changelog

## [0.1.0] — 2026-02-18

### Added

- `/codex` skill (247 lines, 7 governance rules)
- `codex-dialogue` subagent for extended multi-turn consultations
- Consultation contract (16 sections, normative) and 5 named profiles
- PreToolUse enforcement hook: tiered credential detection (strict/contextual/shadow)
- PostToolUse consultation event logging to `~/.claude/.codex-events.jsonl`
- Auto-configured `codex mcp-server` MCP connection

### Enforcement model

Block-or-allow only (no in-flight redaction). Fail-closed by design: hook errors
block the call. Fail-open on hook process crash (OS exit code semantics — see README).
Proportionate for accidental-credential threat model.

### Known limitations

- Broad-tier patterns (generic credential assignments) are shadow-only.
  Promote to strict/contextual after real-world FP data collection.
- `updatedInput` (in-flight redaction) deferred: parallel hook merge semantics
  are undefined, making it unsafe for security-critical v0.1.

### Implementation notes

- Plugin-provided MCP tools use `mcp__plugin_<plugin>_<server>__<tool>` naming,
  not `mcp__<server>__<tool>`. Hook matcher must use the plugin-namespaced form.
  Discovered empirically — not documented in Claude Code plugin docs.
