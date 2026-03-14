# Codebase Concerns

**Analysis Date:** 2026-03-13

## Tech Debt

**Dual import path pattern in handoff scripts:**
- Issue: Scripts in `packages/plugins/handoff/scripts/` use a try/except import fallback to support both `uv run` (package imports) and direct `python3 scripts/foo.py` invocation. This produces `# type: ignore[no-redef]` suppressions on every sibling import and requires every script to maintain the same dual-path boilerplate.
- Files: `packages/plugins/handoff/scripts/triage.py:16-26`, `packages/plugins/handoff/scripts/distill.py:23-25`, `packages/plugins/handoff/scripts/search.py:20-23`
- Impact: Any new script added to the handoff package must reproduce the same pattern or break direct invocation. Type checkers see duplicate definitions.
- Fix approach: Commit to one invocation style (prefer `uv run`) and remove the fallback path.

**Hardcoded sidecar port 7432 duplicated in four files:**
- Issue: `DEFAULT_PORT = 7432` is defined independently in `server.py`, `start_sidecar.py`, `stop_sidecar.py`, and `context_summary.py`. No single constant source.
- Files: `packages/plugins/context-metrics/scripts/server.py:33`, `packages/plugins/context-metrics/scripts/start_sidecar.py:23`, `packages/plugins/context-metrics/scripts/stop_sidecar.py:22`, `packages/plugins/context-metrics/scripts/context_summary.py:22`
- Impact: Port change requires editing four files; mismatch causes silent connection failures.
- Fix approach: Extract to a shared `constants.py` or `config.py` in the context-metrics scripts directory.

**`extractSnippet` re-tokenizes every line on every search call (B10 — deferred):**
- Issue: `extractSnippet` in `packages/mcp-servers/claude-code-docs/src/bm25.ts:114` calls `tokenize(lines[i])` for every line in every result chunk. At max 20 results with up to 150 lines each, this is ~3000 Porter-stemmer passes per search.
- Files: `packages/mcp-servers/claude-code-docs/src/bm25.ts:92-130`
- Impact: Measurable latency degradation at max result count. Accepted as medium-term deferred work in `docs/audits/2026-03-03-claude-code-docs-full-audit.md`.
- Fix approach: Precompute `Set<string>` of tokens per line at index-build time and store alongside existing `tokens`/`termFreqs` on each `Chunk`.

**`headingBoostMultiplier` re-tokenizes headings on every search call (B9 — deferred):**
- Issue: `tokenize(heading)` is called per candidate chunk per query in `packages/mcp-servers/claude-code-docs/src/bm25.ts:84-90`. Heading tokens are stable post-index-build.
- Files: `packages/mcp-servers/claude-code-docs/src/bm25.ts:84-90`
- Impact: Minor but cumulative latency. Compound effect with B10.
- Fix approach: Precompute heading tokens on the `Chunk` struct at index-build time.

**`git_files` set is stale for long-running context-injection server processes:**
- Issue: `_load_git_files()` in `packages/plugins/cross-model/context-injection/context_injection/server.py:53-71` runs once at startup. New files added to the repo after server start are not tracked, so they fail the git gating check silently.
- Files: `packages/plugins/cross-model/context-injection/context_injection/server.py:47-71`
- Impact: Grep scouts will silently skip newly committed files until the MCP server is restarted. Low impact in practice (server restarts with sessions) but surprising behavior.
- Fix approach: Periodically refresh `git_files` on a cache TTL, or re-run `git ls-files` per `execute_scout` call (adds ~10ms latency).

**Ticket triage full-corpus YAML parse — O(n) with no index:**
- Issue: `list_tickets()` in `packages/plugins/ticket/scripts/ticket_read.py:34-44` glob-scans and YAML-parses every `.md` file in the tickets directory. Called by `triage_dashboard()`. Documented as a latency cliff at >500 tickets.
- Files: `packages/plugins/ticket/scripts/ticket_read.py:17-48`, `packages/plugins/ticket/scripts/ticket_triage.py:33-37`
- Impact: O(n) YAML parsing at triage time. Documented in `docs/audits/2026-03-02-ticket-plugin-design-review.md` as deferring indexing to v1.1.
- Fix approach: Build an in-memory or filesystem index of ticket metadata on write; triage reads the index rather than parsing all files.

## Known Bugs

**Ticket-to-audit write ordering is unspecified (partial-write orphan):**
- Symptoms: If a ticket file is written but the audit write fails, the ticket exists with no audit record. In `auto_silent` mode this ticket is invisible to the session cap counter.
- Files: `packages/plugins/ticket/scripts/ticket_engine_core.py` (create path), `docs/audits/2026-03-02-ticket-plugin-design-review.md:203`
- Trigger: Any OS error or process kill between the ticket write and audit write.
- Workaround: Triage will surface the ticket as existing but audit will show no creation record. Manual inspection needed.

**`defer.active` state not auto-cleared on ticket status transition:**
- Symptoms: A deferred ticket transitioning to `in_progress` retains `defer.active: true`, creating inconsistent state.
- Files: `packages/plugins/ticket/scripts/ticket_engine_core.py` (update path)
- Trigger: Updating status of a ticket that was previously deferred.
- Workaround: Manually edit the ticket frontmatter to clear `defer.active`.

## Security Considerations

**Ticket engine shell obfuscation bypass (permanent without v1.1 MCP migration):**
- Risk: The `ticket_engine_guard.py` PreToolUse hook blocks shell metacharacters but cannot catch obfuscated invocations (`eval`, backtick expansion, `$()` substitution). A prompt-injection attack causing Claude to call `eval "python3 ticket_engine_core.py execute ..."` with `request_origin=user` bypasses the entire trust model.
- Files: `packages/plugins/ticket/hooks/ticket_engine_guard.py:374-379`
- Current mitigation: Shell metacharacter regex (`SHELL_METACHAR_RE`) blocks obvious cases. Documented as an accepted risk in `docs/audits/2026-03-02-ticket-plugin-design-review.md:176-181`.
- Recommendations: v1.1 MCP migration (no timeline) would eliminate the hook surface entirely. Until then, treat the trust model as defense-in-depth, not a hard boundary.

**Security hooks fail with `sys.exit(1)` on unexpected exceptions (fail-open for enforcement hooks):**
- Risk: `block-credential-content.py`, `block-keychain-extraction.py`, `block-credential-json-files.py`, and `block-production-claude-dir.py` all catch `Exception` and call `sys.exit(1)`. Per Claude Code hook semantics, exit code 1 is a non-blocking error — the tool call proceeds. An unexpected exception in a blocking hook causes it to silently pass through.
- Files: `packages/plugins/cross-model/context-injection/context_injection/server.py:125-126` (intentional fail-open, documented), `.claude/hooks/block-credential-content.py:74-76`, `.claude/hooks/block-keychain-extraction.py:62-64`
- Current mitigation: The credential pattern checks precede the broad exception handler, so the most likely failure mode is JSON parse error (not pattern match failure).
- Recommendations: Security-critical blocking hooks should exit `2` (block) on unexpected exceptions to fail closed, not `1` (non-blocking error). The context-metrics sidecar correctly fails open with `{"inject": False}` but security blocking hooks have different semantics.

**`assert` used as runtime guard in production code:**
- Risk: `packages/plugins/cross-model/context-injection/context_injection/grep.py:313` uses `assert isinstance(redact_outcome, RedactedText)` to check a postcondition. Python's `-O` flag strips assertions, making this a latent bug if ever run optimized.
- Files: `packages/plugins/cross-model/context-injection/context_injection/grep.py:313`, `packages/plugins/cross-model/scripts/codex_delegate.py:542`
- Current mitigation: Neither package is run with `-O` in practice.
- Recommendations: Replace with `if not isinstance(...)` + explicit `raise RuntimeError(...)`.

## Performance Bottlenecks

**BM25 search: `extractSnippet` + `headingBoostMultiplier` re-tokenize on every call:**
- Problem: Each search call at limit=20 triggers up to ~3000 Porter-stemmer invocations (B10) plus per-chunk heading retokenization (B9).
- Files: `packages/mcp-servers/claude-code-docs/src/bm25.ts:84-90`, `packages/mcp-servers/claude-code-docs/src/bm25.ts:113-114`
- Cause: Tokens not cached on `Chunk` struct at index-build time.
- Improvement path: Precompute and store heading tokens and per-line token sets on `Chunk`. Requires `INDEX_FORMAT_VERSION` bump in `packages/mcp-servers/claude-code-docs/src/index-cache.ts` to invalidate cached indexes.

**Context-injection entity deduplication is O(n²):**
- Problem: `_overlaps()` in `packages/plugins/cross-model/context-injection/context_injection/entities.py:232-241` does an O(n) scan per entity, making entity extraction O(n²) for n entities per turn.
- Files: `packages/plugins/cross-model/context-injection/context_injection/entities.py:232-241`
- Cause: Span overlap is checked against a linear list. Documented as "acceptable for MVP" because `MAX_TEXT_LEN=2000` bounds entity count to ~20 in practice.
- Improvement path: Replace with interval tree or sort-based merge if entity count increases. Low priority until text length limits increase.

## Fragile Areas

**Context-injection HMAC token flow — "looks like magic" without `state.py`:**
- Files: `packages/plugins/cross-model/context-injection/context_injection/state.py`, `packages/plugins/cross-model/context-injection/context_injection/templates.py`, `packages/plugins/cross-model/context-injection/context_injection/execute.py`
- Why fragile: `templates.py` generates HMAC-signed scout tokens during Call 1. `execute.py` validates them during Call 2 without importing `state.py` directly. The connection is non-obvious; developers modifying `execute.py` without reading `state.py` may break token validation silently.
- Safe modification: Always read `state.py` alongside `execute.py` when touching scout dispatch. The CLAUDE.md for this package documents the flow explicitly.
- Test coverage: Covered by `packages/plugins/cross-model/context-injection/tests/test_execute.py` and `tests/test_types.py`.

**Context-injection pipeline import-time invariant check:**
- Files: `packages/plugins/cross-model/context-injection/context_injection/pipeline.py:59-67`
- Why fragile: `MAX_CONVERSATION_TURNS >= MAX_ENTRIES_BEFORE_COMPACT` raises `RuntimeError` at import time. This is intentional (DD-2 invariant), but it means any change to these constants in separate modules can cause the server to refuse to start with a cryptic error.
- Safe modification: When changing either constant, verify the invariant holds before committing. The check will catch violations at startup.
- Test coverage: Implicitly tested by any test that imports `pipeline.py`.

**Context-metrics sidecar: file descriptor leak on startup:**
- Files: `packages/plugins/context-metrics/scripts/start_sidecar.py:71-79`
- Why fragile: `log_fd = open(LOG_FILE, "a")` is opened, passed to `subprocess.Popen`, then closed. The `# noqa: SIM115` comment documents this as intentional because the fd must outlive the close call to be inherited by the subprocess. Any refactor that moves the `log_fd.close()` before `Popen` will silently break log inheritance.
- Safe modification: Do not move `log_fd.close()` before `subprocess.Popen`. The pattern is intentional.

**Ticket engine concurrent session create cap is not lock-based:**
- Files: `packages/plugins/ticket/scripts/ticket_engine_core.py` (create path), `packages/plugins/ticket/scripts/ticket_id.py`
- Why fragile: Session create cap enforcement and ID allocation use optimistic checks without file-system locks. Two concurrent autonomous creates can both pass the cap check and both allocate the same ID, resulting in a collision or cap overrun.
- Safe modification: Avoid triggering autonomous ticket creation from concurrent sessions. Documented as a known limitation in `docs/plans/ticket-plugin-v1.1-hardening-patch.md:152-153`.
- Test coverage: Concurrency path not tested (would require subprocess coordination).

## Scaling Limits

**Ticket triage:**
- Current capacity: Designed for ~100-500 active tickets.
- Limit: At >500 tickets, `triage_dashboard()` YAML-parses all files in one call. At 1700 tickets this becomes a multi-second latency hit.
- Scaling path: Build a ticket metadata index (v1.1 milestone). See `docs/audits/2026-03-02-ticket-plugin-design-review.md:252`.

**Context-injection checkpoint size:**
- Current capacity: 16 KB cap (`MAX_CHECKPOINT_PAYLOAD_BYTES` in `packages/plugins/cross-model/context-injection/context_injection/checkpoint.py`).
- Limit: Conversations with many large evidence blocks approach the cap. Compact triggers before the cap but the margin narrows over long conversations.
- Scaling path: Increase cap with corresponding MCP transport testing; or implement more aggressive compaction.

## Dependencies at Risk

**MCP SDK: `mcp>=1.9.0` unpinned:**
- Risk: `packages/plugins/cross-model/context-injection/pyproject.toml` pins only a lower bound. Breaking changes in a future MCP SDK minor release could silently break the FastMCP server integration (discriminated union serialization, tool registration, lifespan protocol).
- Impact: `context-injection` server startup or `process_turn`/`execute_scout` tool behavior breaks on `uv update`.
- Migration plan: Pin to a specific minor version (e.g., `mcp>=1.9.0,<2.0.0`) and test before upgrading.

## Missing Critical Features

**`nudge_codex.py` and `stats_common.py` have no tests:**
- Problem: `packages/plugins/cross-model/scripts/nudge_codex.py` (95 lines) and `packages/plugins/cross-model/scripts/stats_common.py` (251 lines) are not covered by any test file. All other cross-model scripts have corresponding `test_*.py` files.
- Blocks: Refactoring or debugging these scripts requires manual verification.

**Stale cache accepted without age limit by default in claude-code-docs:**
- Problem: `DOCS_CACHE_MAX_STALE_MS` defaults to `0` (disabled) in `packages/mcp-servers/claude-code-docs/src/loader.ts:41`. On network failure, arbitrarily old cached docs are served without warning beyond a log line. Documented as B7 in `docs/audits/2026-03-03-claude-code-docs-full-audit.md:88-92`.
- Blocks: Users on flaky networks silently receive outdated documentation with no indication of staleness.
- Fix: Set a default max stale age (e.g., 7 days) or surface cache age prominently in tool output.

**Ticket-to-audit one-way traceability (no back-pointer from ticket to its audit record):**
- Problem: Audit records reference tickets, but tickets contain no reference to their audit trail. Finding all audit events for a given ticket requires scanning all audit files.
- Files: `packages/plugins/ticket/scripts/ticket_engine_core.py` (create/update paths)
- Blocks: Ticket-centric audit history view requires O(n) audit file scan.

## Test Coverage Gaps

**`nudge_codex.py` — no test file:**
- What's not tested: Full nudge logic, HTTP response handling, error paths.
- Files: `packages/plugins/cross-model/scripts/nudge_codex.py`
- Risk: Behavior changes during refactoring go undetected.
- Priority: Low (utility script, not on critical path).

**`stats_common.py` — no test file:**
- What's not tested: Shared statistics computation utilities used by `compute_stats.py` and `emit_analytics.py`.
- Files: `packages/plugins/cross-model/scripts/stats_common.py`
- Risk: Correctness bugs in shared statistics silently affect all analytics output.
- Priority: Medium.

**`reload_docs` MCP tool handler has no tests (B11 — deferred):**
- What's not tested: Waiting-on-in-progress loads, clearing index cache, forcing refresh, returning parse warnings.
- Files: `packages/mcp-servers/claude-code-docs/src/index.ts:205-247`
- Risk: Reload behavior can regress without detection. Documented in `docs/audits/2026-03-03-claude-code-docs-full-audit.md:112-116`.
- Priority: Medium.

**14 of 24 search categories have no golden query (B12 — deferred):**
- What's not tested: Categories without golden queries in `packages/mcp-servers/claude-code-docs/tests/golden-queries.test.ts`.
- Files: `packages/mcp-servers/claude-code-docs/tests/golden-queries.test.ts`
- Risk: Chunking or BM25 regressions for low-coverage categories (notably `commands`, `plugins`, `settings`) go undetected.
- Priority: Low-Medium.

**Ticket concurrent create path:**
- What's not tested: Two concurrent autonomous creates hitting the session cap simultaneously.
- Files: `packages/plugins/ticket/scripts/ticket_engine_core.py`, `packages/plugins/ticket/scripts/ticket_id.py`
- Risk: ID collision or cap overrun under concurrent agent activity.
- Priority: Low (single-user tool; concurrency is edge case).

---

*Concerns audit: 2026-03-13*
