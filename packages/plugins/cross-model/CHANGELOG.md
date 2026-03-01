# Changelog

## [Unreleased]

## [2.0.0] — 2026-03-01

### Added

- `/dialogue` skill — orchestrated multi-turn consultation with parallel context gathering, `--posture`, `--turns`, `--profile` flags
- `/consultation-stats` skill — analytics dashboard for consultations, dialogues, and security events
- `context-gatherer-code` agent — pre-dialogue codebase explorer emitting prefix-tagged `CLAIM`/`OPEN` lines with citations
- `context-gatherer-falsifier` agent — pre-dialogue assumption tester emitting `COUNTER`/`CONFIRM`/`OPEN` lines
- `--plan` flag on `/dialogue` with Step 0 question shaping, debug gate, and tri-state `question_shaped` tracking (#20)
- Scope enforcement via `scope_envelope` — allowed roots and source classes checked before Codex delegation (#23, #24)
- `[SRC:<source>]` provenance tags in tag grammar, code explorer (`[SRC:code]`), and falsifier (`[SRC:docs]`)
- Step 3h-bis provenance validation with `provenance_unknown_count` plumbing
- Step 4b `seed_confidence` composition collecting reasons from all pipeline stages
- External briefing detection and `seed_confidence` pass-through in `codex-dialogue`
- Synthesis Checkpoint block (RESOLVED/UNRESOLVED/EMERGED) in `codex-dialogue` output
- `emit_analytics.py` script for deterministic analytics emission
- `dialogue_outcome` event emission in `/dialogue` Step 7
- `consultation_outcome` event emission in `/codex` post-diagnostics
- Governance sections added to all 4 agents (consultation contract §15 alignment)
- Step numbering crosswalk between SKILL.md and tag-grammar.md
- `compute_stats.py` — 4-section analytics computation (usage overview, dialogue quality, context quality, security)
- `stats_common.py` — shared analytics primitives for time windowing, rate computation, and formatting

### Changed

- `/codex` and `/dialogue` analytics rewritten to use shared `emit_analytics.py` script
- `codex-dialogue` outputs actual thread ID value instead of boolean
- Falsifier no-assumptions fallback constrained to rationale surfaces only

### Fixed

- PR #14 structured review — 13 findings across 9 files (REPO_ROOT env, stale paths)
- PR review round 2 — 4 spec fixes, cross-field invariant, 12 new tests
- `codex-guard` thread_id_present now checks `structuredContent.threadId`
- Enhancement review findings from 4-agent review + Codex triage (#21)
- P0 system polish — resolver symmetry, mode truthfulness, event reader, contract §17 (#22)
- `codex-reviewer` hardcoded model removed (§9 violation)
- `emit_analytics.py` hardened — null enum rejection, bool count rejection, turn_budget null guard
- `provenance_unknown_count` explicitly set to null in Step 3c zero-output fallback
- `content_conflict_count` added for retry-wins tie-break auditing
- Scope-breach data flow, contract fixes, and validator improvements from PR reviews (#23, #24)
- Command wrappers added then removed to avoid FQN skill resolution bug
- Stale marketplace name references updated from `cross-model` to `turbo-mode`
- Analytics pipeline hardened against malformed data and edge cases

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
claude plugin marketplace update turbo-mode
claude plugin install cross-model@turbo-mode
```

## [0.1.0] — 2026-02-18 (originally released as the `codex` plugin)

### Added

- `/codex` skill (237 lines, 7 governance rules)
- `codex-dialogue` subagent for extended multi-turn consultations
- Consultation contract (16 sections, normative) and 5 named profiles
- PreToolUse enforcement hook: tiered credential detection (strict/contextual/shadow)
- PostToolUse consultation event logging to `~/.claude/.codex-events.jsonl`
- Auto-configured `codex mcp-server` MCP connection
