# Changelog

## [Unreleased]

### Removed

- CCDI (Claude Code Documentation Intelligence) subsystem — Codex has native access to `mcp__claude_code_docs__search_docs`, making the content delivery pipeline obsolete; 88 files removed (~25k lines, 616 tests); `"ccdi": {"status": "removed"}` retained in pipeline epilogue for analytics backward compatibility

### Added

- `DELEGATION_POLICY` config in `consultation_safety.py` — separate safety policy for delegation credential scanning (#82)
- MCP tool name drift detection tests and `codex exec` guardrail tests (#82)

### Changed

- `codex-dialogue` agent instruction volume reduced by 50%
- `codex_delegate.py` credential scan routed through `consultation_safety.check_tool_input` with `DELEGATION_POLICY` for boundary canonicalization (#82)
- `_parse_markdown_synthesis` fallback in `codex_guard.py` now lazy — only runs when JSON epilogue absent or unusable; adds `parse_fallback_used` observability signal (#82)
- `TIER_RANK` deduplicated — single definition in `consultation_safety.py`, removed from `codex_guard.py` (#82)

### Fixed

- Allow large prompts through delegation credential scan without false-positive blocking (#82)

## [3.1.3] — 2026-03-20

### Fixed

- Add `--skip-git-repo-check` to `codex_delegate.py` `_build_command()` — prevents delegation failures when the MCP server process runs from a directory Codex doesn't trust as a git repo

## [3.1.2] — 2026-03-20

### Fixed

- Remove `-s` (sandbox) flag from `codex exec resume` command — `resume` subcommand does not accept this flag; sandbox is inherited from the original session. Fixes reply path failing with "unexpected argument '-s'" when called through MCP shim

### Changed

- `codex_consult.py` `_build_command()` now applies `-s <sandbox>` only to new conversations, not resume conversations

## [3.1.1] — 2026-03-20

### Fixed

- Add `--skip-git-repo-check` to `codex exec` command in `codex_consult.py` — prevents consultation failures when the MCP server process runs from a directory Codex doesn't trust as a git repo

## [3.1.0] — 2026-03-20

### Added

- `codex_consult.py` adapter — wraps `codex exec` CLI as a programmatic `consult()` API for new conversations and thread resumption
- `consultation_safety.py` — extracted shared safety module from `codex_guard.py` (`ToolScanPolicy`, `SafetyVerdict`, `check_tool_input`, `extract_strings`)
- `codex_shim.py` — thin FastMCP MCP server exposing `codex` and `codex-reply` tools backed by the `consult()` adapter, with `structuredContent.threadId` for backward compatibility
- `.mcp.json` wiring validation tests (`test_mcp_wiring.py`) — 4 tests ensuring codex entry uses local shim
- `event_schema.py` — single source of truth for event field definitions, with frozen `REQUIRED_FIELDS_BY_EVENT` dict and disjointness assertion (#74)
- `retrieve_learnings.py` script for §17 learning injection — queries `docs/learnings/learnings.md` for project-relevant learnings (#76, #80)
- 4 new analytics sections in `compute_stats.py`: planning effectiveness, provenance health, parse diagnostics, consultation quality (#77)
- `--threads` CLI flag in `compute_stats.py` for thread discovery and grouping (#77)
- Reviewer analytics integration with `consultation_source` discriminator in `emit_analytics.py` (#77)

### Changed

- `.mcp.json` codex entry now uses local `codex_shim.py` via `uv run` instead of upstream `codex mcp-server` binary — eliminates tight coupling to upstream CLI parameter changes
- `codex_guard.py` imports safety utilities from `consultation_safety.py` instead of inline implementation
- `approval_policy` (underscore) added to `START_POLICY.expected_fields` alongside `approval-policy` (hyphen) for shim schema compatibility
- `mcp>=1.9.0` added to root plugin dependencies (previously only in context-injection sub-package)
- Learning retrieval wired into `/codex` and `/dialogue` skills; consultation contract §17 activated (#76)
- `codex_guard.py` delegates event logging to `event_log.py` for POSIX atomic writes with 0o600 file permissions (#74)
- Tier-filtered credential family tuples cached at module level in `credential_scan.py` (#74)
- Event consumers migrated to shared `event_schema.py` field definitions (#74)
- `thread_id` extracted as actual string value (not just boolean) in `codex_guard.py`; added to `consultation_outcome` required fields (#75)
- 370 cross-model tests migrated from repo root into `packages/plugins/cross-model/tests/`
- Plugin version bumped from 3.0.0 to 3.1.0

### Fixed

- Split `_AUTH_HEADER_RE` into `_BEARER_AUTH_RE` and `_BASIC_AUTH_RE` to prevent false positives on bearer tokens shorter than 20 chars (#74)
- Use `family.name` in credential scan reason field; multi-field scan selects highest-tier result across all fields (#75)
- Validate epilogue `convergence_reason_code` before use — prevents analytics emission failure on malformed Codex output
- Degrade gracefully on synthesis parse failure instead of raising
- Harden analytics instructions with explicit prohibitions against LLM-constructed field values
- Deterministic imports via `__package__` guard in 5 cross-model scripts
- Improve `codex_guard.py` error handling — log PostToolUse errors, narrow stdin catch, surface audit failures
- Include learnings in Step 3c zero-output fallback briefing (#76)
- Remediate 5 design review findings: per-event delegation validation, profile §14 invariant enforcement, credential assignment split policy (#80)

## [3.0.0] — 2026-03-14

### Added

- `/delegate` skill — autonomous Codex execution with sandbox containment, clean-tree gate, and secret-file gate (#53)
- `delegation_outcome` analytics event type for tracking delegation results
- `credential_scan.py` shared module — extracted credential detection logic for reuse across hooks and delegation
- `event_log.py` shared module — extracted event logging logic for reuse across analytics emitters
- `secret_taxonomy.py` shared module — consolidates all credential pattern families with independent `redact_enabled`/`egress_enabled` controls; adds Basic Auth and Slack token families (#55)
- Phase-local convergence detection — each phase in a multi-phase profile gets independent plateau detection and closing probe opportunity
- Phase delegation in `/dialogue` — `phases` array wired from SKILL.md through `codex-dialogue` agent with `phase_turns_completed` counter for unambiguous transition timing
- `debugging` composed profile (exploratory → evaluative → collaborative) with 3-phase consultation
- `comparative` posture type added to posture taxonomy
- `context-injection` consolidated into `packages/plugins/cross-model/context-injection/` — canonical location replacing vendored copy and legacy `packages/context-injection/` (#58)

### Changed

- `codex_guard.py` refactored to import credential detection from `credential_scan.py` (no behavior change)
- `emit_analytics.py` refactored to import event logging from `event_log.py` (no behavior change)
- `read_events.py` updated to parse and validate `delegation_outcome` events
- `compute_stats.py` updated with delegation section (usage counts, success rates, sandbox mode distribution)
- `consultation-stats` skill updated with `--type delegation` filter
- `approval-policy` default changed from `on-failure` to `on-request` for workspace-write sandboxes; `on-failure` remains valid for legacy compatibility (#57)
- Analytics parsing migrated from `<!-- pipeline-data -->` comment blocks to JSON epilogue as sole machine contract; `thread_id` now always emitted when available (previously `null` in `manual_legacy` mode) (#56)
- Closing probe policy changed from once-per-conversation to once-per-phase — ensures each phase in multi-phase profiles can independently detect convergence
- Vendoring sync script and vendored marker file removed (#58)
- `docs/references/context-injection-contract.md` symlink removed in favor of the plugin reference path (#58)
- Dev dependencies migrated to PEP 735 dependency-groups (#34)

### Fixed

- Exempt `certifi/cacert.pem` CA bundle from secret-file gate via `_SAFE_ARTIFACT_TAILS` frozenset (component-based matching) — `*.pem` glob was blocking all delegation in repos with a `.venv/` directory (#54)
- Tighten credential scan placeholder bypass window from 200 to 100 chars — reduces risk of a nearby "example" token suppressing a real credential match; `PLACEHOLDER_BYPASS_WINDOW` now exported from `secret_taxonomy.py` and shared by both `credential_scan.py` and `check_placeholder_bypass` (#58)

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
- `read_events.py` — typed JSONL event reader with per-event-type required field validation
- `parse_truncated` field in `dialogue_outcome` events — surfaces unclosed-fence truncation
- §17 learning retrieval and injection section in consultation contract
- Replay-based conformance test fixtures (`consultation_simple`, `dialogue_converged`, `dialogue_manual_legacy`, `dialogue_scope_breach`, `dialogue_with_planning`)

### Changed

- `/codex` and `/dialogue` analytics rewritten to use shared `emit_analytics.py` script
- Falsifier no-assumptions fallback constrained to rationale surfaces only

### Fixed

- PR #14 structured review — 13 findings across 9 files (REPO_ROOT env, stale paths)
- PR review round 2 — 4 spec fixes, cross-field invariant, 12 new tests
- `codex-guard` thread_id_present now checks `structuredContent.threadId`
- Enhancement review findings from 4-agent review + Codex triage (#21)
- Explicit mode propagation from `codex-dialogue` to analytics pipeline
- `build_consultation_outcome` uses `_resolve_schema_version` for resolver symmetry
- Non-dict JSON guard and error handling in event processing
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
