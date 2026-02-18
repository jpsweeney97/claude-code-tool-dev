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

- Contract stub paths in SKILL.md point to `docs/references/` (repo-relative).
  Works within this repo; update paths before external distribution.
- Broad-tier patterns (generic credential assignments) are shadow-only.
  Promote to strict/contextual after real-world FP data collection.
- `updatedInput` (in-flight redaction) deferred: parallel hook merge semantics
  are undefined, making it unsafe for security-critical v0.1.
