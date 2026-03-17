# Cross-Model Plugin: Capability Analysis

**Date:** 2026-03-17
**Scope:** `packages/plugins/cross-model/` — all 4 user-facing capabilities, shared infrastructure, and bundled context-injection MCP server.

---

## Step 1: Capability Audit

### Capability 1: `/codex` — Single-Turn Consultation

**Execution path:** Argument parsing → egress preflight (Claude-cognitive §3 consent) → briefing assembly (3-section §5 format) → pre-dispatch safety record (7 fields, Claude-cognitive §7) → `codex_guard.py` PreToolUse credential scan → MCP dispatch via `mcp__plugin_cross-model_codex__codex` → `codex_guard.py` PostToolUse event log → response relay (3-part §11 format) → diagnostics capture → analytics emission via `emit_analytics.py`.

**Boundaries:**

- *Handles well:* Deterministic argument validation, tiered credential scanning, threadId canonicalization (§10 — `structuredContent.threadId` preferred over top-level), relay format enforcement, re-consent triggers (5 deterministic conditions).
- *Stops short:* The egress preflight manifest (§3) and 7-field pre-dispatch record (§7) are Claude-cognitive protocol — no Python code enforces them. If Claude skips them, only `codex_guard.py` credential patterns provide a backstop.
- *Unhandled:* `danger-full-access + approval-policy=never` policy rejection (§8) is Claude-enforced only.

**Leverage points:** `event_schema.py` (load-bearing — schema changes cascade to all consumers), `codex_guard.py` PreToolUse (sole code-level enforcement gate), `consultation-contract.md §5/§7/§11` (normative — skill must defer).

**Underutilized:** Learning retrieval (§17) is a dead path — the card model was removed and §17 is now deferred. Both `/codex` and `/dialogue` have fail-soft learning retrieval references that never activate. `docs/learnings/learnings.md` is populated by `/learn` and `/promote` but never read during consultations.

---

### Capability 2: `/dialogue` — Orchestrated Multi-Turn Consultation

**Execution path:** Optional question shaping (Step 0, `--plan` flag — debug gate, decomposition, tri-state `question_shaped`) → assumption extraction → parallel gatherer launch (Task tool, 120s timeout, model sonnet: `context-gatherer-code` + `context-gatherer-falsifier`) → deterministic briefing assembly (Steps 3a-3h-bis per tag-grammar.md: parse → retry → zero-output fallback → discard → cap 3 COUNTER → sanitize → dedup → provenance validation → group with `<!-- dialogue-orchestrated-briefing -->` sentinel) → health check → `seed_confidence` composition (sole authority: Step 4b) → delegate to `codex-dialogue` agent with scope envelope → relay synthesis → analytics emission.

**The `codex-dialogue` agent** runs a 7-step per-turn loop in `server_assisted` mode: extract claims/delta/tags/unresolved → `process_turn` (dual-claims guard, checkpoint, entity extraction, path policy, template matching, budget, ledger validation, convergence detection) → process TurnPacket → scout via `execute_scout` (HMAC-validated, spec-bound) → act on `action` directive → compose follow-up (priority: scout evidence → unresolved → unknown-provenance → unprobed → weakest claim → posture-driven) → send via `codex-reply`. Phase 3 synthesis produces 7 output sections with `<!-- pipeline-data -->` JSON epilogue.

**Boundaries:**

- *Handles well:* Sentinel-based briefing handoff, `seed_confidence` signal for early-turn scouting calibration, dual-path analytics parser (epilogue + markdown regex fallback), 3-tier unknown-provenance recovery (exact → component-boundary suffix → basename), deterministic non-LLM assembly.
- *Stops short:* Scope envelope constructed from "§3 preflight" but preflight is Claude-cognitive — no Python enforces it. The `tag-grammar.md` crosswalk is a spec for Claude to follow, not enforced code. If `codex-dialogue`'s `<!-- pipeline-data -->` epilogue is missing, markdown regex fallback has lower precision for `converged` detection.
- *Unhandled:* `provenance_unknown_count` null vs 0 semantic (schema version signal) is correctly threaded but requires all consumers to respect the distinction. If one gatherer produces 0 lines and the other produces output, the retry targets only the low-output gatherer.

**Leverage points:** `pipeline.py` 17-step pipeline (load-bearing for all server-assisted dialogues), `control.py:compute_action` (drives conversation lifecycle), `emit_analytics.py:build_dialogue_outcome` (47-field event — any change to agent output format requires coordinated update), `templates.py` HMAC token flow (security boundary between agent and server).

**Underutilized:** Planning pipeline fields (`question_shaped`, `shape_confidence`, `assumptions_generated_count`, `ambiguity_count`) are stored in events (schema 0.3.0) but `compute_stats.py` has no section computing plan-mode effectiveness. The `effective_delta` sequence in `CumulativeState` could support richer analytics than the current trajectory summary. Posture is stored but explicitly "posture-agnostic by design" — could drive different template selection or convergence thresholds. The `tags` field in `TurnRequest`/`LedgerEntry` has no server-side semantics.

---

### Capability 3: `/delegate` — Autonomous Codex Execution

**Execution path:** Argument parsing (no input echoing — credential scan runs in adapter) → write input JSON to `$TMPDIR` → run `codex_delegate.py` 14-step pipeline: resolve repo root → allocate output tempfile (0o600) → Phase A parse (structural, applies defaults) → credential scan (block → analytics emitted, exit 0 intentional) → Phase B validation (field validation post-scan) → version check (codex ≥ 0.111.0) → clean-tree gate (NUL-separated `git status` with rename/copy handling) → secret-file gate (gitignored files, exact names + globs, template exemptions, `_SAFE_ARTIFACT_TAILS`) → build command (with `--` separator) → subprocess run (600s timeout, 50MB stdout cap, `did_dispatch` set before `Popen`) → parse JSONL (thread_id, commands_run, token_usage, runtime_failures, summary) → emit analytics → cleanup. Then: input file cleanup via `trash` → mandatory review (git status/diff + Claude assessment).

**Boundaries:**

- *Handles well:* Most rigorous component. NUL-separated git status parsing with rename/copy handling. `did_dispatch` flag set before subprocess spawn (correct timeout attribution). Phase A/B split ensures analytics always emit for credential blocks. `_SAFE_ARTIFACT_TAILS` handles `certifi/cacert.pem` false-positive. `_output` uses assertion for required field verification.
- *Stops short:* Secret-file gate covers only gitignored files (`git ls-files --others --ignored`). Arbitrarily-named secret files not detected — gate is filename-pattern based, not content-based. Symlink targets not resolved.
- *Unhandled:* `token_usage` captures only the last `turn.completed` event — multi-turn accumulation is deferred (code comment). No `manual_legacy` equivalent — if adapter fails, no fallback.

**Leverage points:** `codex_delegate.py` is self-contained (leaf-level relative to the rest of the plugin). `_check_clean_tree` and `_check_secret_files` are the unique safety gates not present in `/codex` or `/dialogue`.

**Underutilized:** `_SAFE_ARTIFACT_TAILS` has only one entry — the mechanism is well-designed but the exemption list is sparse.

---

### Capability 4: `/consultation-stats` — Analytics

**Execution path:** Parameter determination (`--period` default 30, `--type` default all) → run `compute_stats.py --json` → `read_events.read_all()` (reads `~/.claude/.codex-events.jsonl`, skips malformed) → `_validate_events` (required fields from `event_schema.py`) → classify into 6 buckets → filter by period → apply `_SECTION_MATRIX` → compute sections: `_compute_usage` (counts, active days, posture/schema distributions), `_compute_dialogue` (convergence rate, avg turns, scout count, mode/termination distributions), `_compute_context` (seed confidence, low-seed reasons, citations, gatherer retries), `_compute_security` (block count, tier distribution, block rate), `_compute_delegation` (termination reasons, per-gate blocks, sandbox/full_auto counts).

**Boundaries:**

- *Handles well:* `_SECTION_MATRIX` cleanly scopes output. `observed_avg` excludes null/invalid from denominator. `observed_bool_slots` tracks missing data separately from false. Schema version distribution in usage detects mixed-version logs.
- *Stops short:* No quality metrics for single-turn `/codex` consultations (`_compute_dialogue` only operates on `dialogue_outcomes`). `consultation` type in `_SECTION_MATRIX` returns usage only, no dialogue section. `--json` is always True — no human-readable output path in the script itself. No custom log path support.
- *Unhandled:* `parse_truncated` and `parse_degraded` diagnostic fields have no stats section.

**Underutilized:** Planning pipeline fields stored but not surfaced. Scout impact not aggregated beyond `avg_scout_count`. `codex-reviewer` emits no events — invisible to stats.

---

### Shared Infrastructure

| Component | Load-bearing? | What it does | Coverage gaps |
|-----------|:---:|---|---|
| `event_log.py` | **Yes** | POSIX atomic append, `0o600` permissions, single file shared by all producers | None significant — well-implemented |
| `event_schema.py` | **Yes** | Required field sets, valid enums, schema version resolution (`MappingProxyType`) | Forward-only versioning with no migration path |
| `credential_scan.py` + `secret_taxonomy.py` | **Yes** | 14-family, 3-tier taxonomy. Strict blocks, contextual blocks with placeholder bypass, broad shadows | `reason` field logs regex fragment not family name. Scan priority across multi-field payloads may log less-informative tier |
| `codex_guard.py` | **Yes** | PreToolUse credential enforcement + PostToolUse telemetry. Policy-based field selection, size caps (`_NODE_CAP=10000`, `_CHAR_CAP=256KB`), fail-closed | Only code-level enforcement gate — everything else is Claude-cognitive |
| `emit_analytics.py` | **Yes** | Constructs structured events for all 3 outcome types. Dual-path synthesis parser | `build_dialogue_outcome` tightly coupled to agent output format |
| Context injection pipeline | **Yes** | 17-step Call 1, HMAC-validated Call 2, 5 format redactors, immutable state projections | Well-implemented. Known limitations: single-flight assumption, `compact_to_budget` is O(n) and reachable when byte-size exceeds budget despite DD-2 entry-count compliance |
| `nudge_codex.py` | No (leaf) | Opt-in Bash failure counter with fcntl locking | Cross-session interference if `CLAUDE_SESSION_ID` unset (shares counter file as "unknown") |
| `codex-reviewer.md` | No (leaf) | Standalone PR review agent, 2-turn max, 3-tier diff handling | No event emission, no analytics visibility |

---

## Step 2: Enhancement Analysis

### Lens A: Capability Depth

**A1. Planning effectiveness is unmeasured.** `question_shaped`, `shape_confidence`, `assumptions_generated_count`, `ambiguity_count` are stored in `dialogue_outcome` events at schema 0.3.0 (`event_schema.py:37-46`) but `compute_stats.py` has no section analyzing whether decomposition improves convergence. Users who use `--plan` cannot tell if it's helping. The architecture already stores the data — only the computation and presentation layers are missing.

**A2. Provenance recovery is invisible.** The `codex-dialogue` agent's 3-tier unknown-provenance recovery (`codex-dialogue.md` Step 4: exact → component-boundary suffix → basename) is sophisticated infrastructure. `provenance_unknown_count` bumps schema to 0.2.0 and is stored in events, but `compute_stats.py` computes no metrics on it. Can't measure whether gatherers are failing to tag sources or whether the recovery is converting `[SRC:unknown]` claims into grounded evidence.

**A3. Single-turn consultations have no quality metrics.** `_compute_dialogue` operates only on `dialogue_outcomes`. Single-turn `/codex` consultations produce `consultation_outcome` events which have no convergence rate, seed confidence, or quality analysis. The `_SECTION_MATRIX` for `--type consultation` only returns usage, not a dedicated analysis section. This means the most frequently used capability (`/codex`) is the least measured.

**A4. Learning retrieval is architecturally ready but dead.** Consultation contract §17 defines the injection points but is marked deferred (card model dependency removed). `docs/learnings/learnings.md` exists and is populated by `/learn` and `/promote`. The briefing assembly can accommodate a `## Prior Learnings` section (§17.2 specifies placement between `## Context` and `## Material`). Every piece of the pipeline exists except the actual retrieval call — §17 is deferred, waiting for implementation.

### Lens B: User Experience Quality

**B1. Parse degradation is invisible to users.** When the `codex-dialogue` agent's `<!-- pipeline-data -->` epilogue is missing or malformed, `emit_analytics.py` falls back from `_parse_epilogue` to `_parse_markdown_synthesis` (regex-based, lower precision). The `parse_truncated` and `parse_degraded` diagnostic fields are stored in events but no stats section surfaces them. Users can't tell if their analytics data is degraded.

**B2. `--plan` flag requires deliberate opt-in for its highest-value use case.** The question-shaping pipeline (debug gate, decomposition, tautology filtering, shape_confidence cascade) is the most sophisticated preprocessing in the plugin. But it requires `--plan` — users with complex, multi-faceted questions who would benefit most are least likely to know about it. The debug gate already detects certain question patterns; the same pattern-detection infrastructure could identify plan-worthy questions.

**B3. `codex-reviewer` is invisible to the analytics ecosystem.** This agent performs full review workflows (git diff gathering, briefing assembly, 2-turn Codex consultation, synthesis) but emits no events. Its executions are completely invisible to `/consultation-stats`. Users who use both `/dialogue` and the reviewer agent get a partial view of their Codex usage.

### Lens C: Safety and Reliability

**C1. Credential scan reason field logs regex fragments, not family names.** At `credential_scan.py:71`, the reason encodes `f"strict:{family.pattern.pattern[:60]}"`. The `SecretFamily.name` attribute exists and would be more informative for audit trail analysis. The log entry `strict:\bAKIA[A-Z0-9]{16}\b` is less actionable than `strict:aws_access_key_id`.

**C2. Multi-field scan priority may produce misleading audit entries.** Multiple fields are scanned in sequence (`codex_guard.py:208` loop). `scan_text` returns on first match per field. A prompt with a broad-tier match in field A and a strict-tier match in field B could log field A's pattern as the reason (if A is processed first). The result is still correctly a block, but the logged `reason` may point to the less-relevant pattern. This affects audit trail analysis, not enforcement correctness.

---

## Step 3: New Capability Analysis

### N1. Learning Injection into Consultations

**What it does:** Reads `docs/learnings/learnings.md` before briefing assembly and injects relevant prior learnings into a `## Prior Learnings` section (between `## Context` and `## Material` per §17.2), so Codex benefits from accumulated project knowledge.

**Why it's high-leverage:** The entire learning system pipeline (capture → stage → promote) exists and produces structured content, but the output never reaches the cross-model boundary. Consultations repeatedly re-discover context that was previously captured. Every `/learn` and `/promote` invocation is currently wasted effort for cross-model work. The injection points are defined in consultation contract §17 — currently deferred, waiting for implementation.

**What it builds on:** `/learn` skill populates `docs/learnings/learnings.md`. Consultation contract §17 defines the injection protocol. Briefing assembly (§5) has a natural insertion point. The `/dialogue` skill's Step 3 assembly can accommodate an additional section. `credential_scan.scan_text` already runs on all briefing content — learning content would be scanned automatically.

**What's needed:** A retrieval function that reads `docs/learnings/learnings.md`, selects relevant entries (likely by keyword matching against the consultation question), and formats them for the briefing. Updates to `/codex` SKILL.md and `/dialogue` SKILL.md to call retrieval and inject results. A test for the retrieval function.

**What it doesn't need:** No changes to the context-injection server, event schema, analytics pipeline, or hook infrastructure. No new MCP tools. No contract amendments beyond unblocking §17.

### N2. Consultation Continuity via Thread Discovery

**What it does:** Surfaces past consultation threads by topic and enables resumption without the user needing to track `threadId` values manually.

**Why it's high-leverage:** `threadId` is already persisted in every `consultation_outcome` and `dialogue_outcome` event (`codex_guard.py:240-248` extracts it from three possible locations). The `/codex` skill's continuation path (`codex-reply` with canonicalized `threadId` per §10) is fully implemented. But users can only continue a thread if they know the `threadId` — which means they must have seen the diagnostics output from the immediately preceding session. Cross-session continuity requires manual tracking.

**What it builds on:** `read_events.py:read_all()` already returns all events. Each outcome event contains `thread_id` (when present) and `prompt_length` / `result_length` plus timestamps. The `/codex` skill already handles `codex-reply` dispatch for continuations.

**What's needed:** A thread-listing function (filter events by `thread_id` presence, group by `thread_id`, extract first prompt summary and timestamp). Presentation in `/consultation-stats` or a new `--threads` flag on `/codex`. Thread selection UI (multiple choice) before dispatching `codex-reply`.

**What it doesn't need:** No changes to the MCP server, event schema (thread_id is already stored), credential scanning, or context injection. No new hooks.

### N3. Reviewer Analytics Integration

**What it does:** Adds event emission to `codex-reviewer.md` so review executions appear in the event log and `/consultation-stats`.

**Why it's high-leverage:** `codex-reviewer` performs full Codex consultations (briefing assembly, 1-2 turn exchange, synthesis) but is completely invisible to the analytics ecosystem. Users who rely on both `/dialogue` for deep consultations and the reviewer for PR checks get a partial view of their Codex usage. The infrastructure for emission already exists — `emit_analytics.py:build_consultation_outcome` handles single/few-turn consultations.

**What it builds on:** `emit_analytics.py` structured event construction. `event_schema.py` `consultation_outcome` type. `compute_stats.py` `_compute_usage` already counts consultation outcomes. The reviewer agent has access to the Write tool (needed for temp file creation) and Bash (needed for running `emit_analytics.py`).

**What's needed:** Analytics emission instructions added to `codex-reviewer.md` Phase 4 (post-synthesis). A `review_outcome` event type in `event_schema.py` (or reuse `consultation_outcome` with a distinguishing field). A stats section for review-specific metrics (files reviewed, finding counts by severity, source attribution distribution). Updates to `_SECTION_MATRIX` in `compute_stats.py`.

**What it doesn't need:** No changes to the MCP servers, hook infrastructure, credential scanning, or context injection. No new scripts — reuses existing `emit_analytics.py`.

---

## Step 4: Prioritized Findings

| # | Finding | Type | Leverage | Effort | Evidence | Components |
|---|---------|------|----------|--------|----------|------------|
| 1 | **Learning injection into consultations** — §17 is deferred, learning system produces content that never reaches Codex | New | **High** — every consultation re-discovers context that was previously captured; learning pipeline ROI is currently zero for cross-model work | S (2-3 files) | §17 deferred in contract; fail-soft references in both skill files; `docs/learnings/learnings.md` populated by `/learn`+`/promote`; §17.2 specifies `## Prior Learnings` placement | `skills/codex/SKILL.md`, `skills/dialogue/SKILL.md`, `references/consultation-contract.md` §17 |
| 2 | **Planning effectiveness metrics** — plan-mode fields stored but never analyzed | Enhance | **High** — `--plan` users can't measure impact; data already exists, only computation missing | S (1 file + tests) | `event_schema.py:37-46` version resolution keys on `question_shaped`; `compute_stats.py` has no plan section; `dialogue/SKILL.md` Step 7 emits `shape_confidence`, `assumptions_generated_count`, `ambiguity_count` | `scripts/compute_stats.py`, `scripts/stats_common.py` |
| 3 | **Provenance recovery metrics** — unknown-provenance tracking stored but unmeasured | Enhance | **High** — 3-tier recovery in `codex-dialogue` is sophisticated infrastructure with no feedback loop; can't tell if gatherers are degrading | S (1 file + tests) | `provenance_unknown_count` bumps schema to 0.2.0 (`event_schema.py:41`); `codex-dialogue.md` Step 4 three-tier matching; `compute_stats.py` has no provenance section | `scripts/compute_stats.py`, `scripts/stats_common.py` |
| 4 | **Single-turn consultation quality metrics** — `/codex` is most-used but least-measured capability | Enhance | **Medium** — `consultation_outcome` events have prompt/result length and thread presence but no dedicated quality analysis | S (1 file + tests) | `_compute_dialogue` only operates on `dialogue_outcomes` (`compute_stats.py:175`); `_SECTION_MATRIX` consultation type returns usage only | `scripts/compute_stats.py` |
| 5 | **Credential scan reason clarity** — logs regex fragments instead of family names | Enhance | **Medium** — affects audit trail analysis for every block/shadow event; fix is trivial | S (1 file + tests) | `credential_scan.py:71` uses `family.pattern.pattern[:60]`; `SecretFamily.name` attribute exists at `secret_taxonomy.py:48` | `scripts/credential_scan.py` |
| 6 | **Parse degradation visibility** — epilogue fallback is invisible in stats | Enhance | **Medium** — users can't tell if their analytics data is degraded; fields already stored | S (1 file + tests) | `parse_truncated`/`parse_degraded` in `dialogue_outcome` events; `emit_analytics.py` dual-path parser; `compute_stats.py` has no section | `scripts/compute_stats.py` |
| 7 | **Consultation continuity via thread discovery** — threadId persisted but not surfaceable | New | **Medium** — cross-session continuity requires manual `threadId` tracking; every event already stores it | M (3-4 files) | `codex_guard.py:240-248` extracts threadId from 3 locations; `read_events.py:read_all()` returns all events; `/codex` already handles `codex-reply` dispatch | `scripts/compute_stats.py` or new `scripts/thread_discovery.py`, `skills/codex/SKILL.md` |
| 8 | **Reviewer analytics integration** — `codex-reviewer` is invisible to analytics | New | **Medium** — full Codex consultations emitting no events; partial usage visibility | M (3-4 files) | `codex-reviewer.md` has no analytics emission; `emit_analytics.py:build_consultation_outcome` handles few-turn consultations; `event_schema.py` has consultation_outcome type | `agents/codex-reviewer.md`, `scripts/event_schema.py`, `scripts/compute_stats.py` |
| 9 | **Automatic plan-mode suggestion** — `--plan` requires deliberate opt-in for its highest-value use | Enhance | **Low** — the debug gate already detects patterns; extending pattern detection is modest effort but the UX integration is tricky (must not be annoying) | M (2-3 files) | `dialogue/SKILL.md` Step 0 debug gate checks for `traceback`, `exception`, intent+failure-lexeme pairs; same infrastructure could detect plan-worthy patterns | `skills/dialogue/SKILL.md`, `skills/codex/SKILL.md` |
| 10 | **Multi-field scan priority audit accuracy** — logged reason may reference less-relevant pattern | Enhance | **Low** — affects audit analysis only, not enforcement; fix requires collecting all results before selecting | S (1 file + tests) | `codex_guard.py:208` loop returns on first block; `scan_text` returns first match per tier priority; cross-field priority is field-iteration-order dependent | `scripts/codex_guard.py` |

---

## Step 5: Recommended Roadmap

### Phase 1: Analytics Foundation + Learning Injection

**Findings: #1, #2, #3, #5, #6**

Build the measurement and feedback infrastructure that makes every subsequent enhancement evaluable, plus activate the learning system's cross-model path.

- **#1 (Learning injection):** Unblock §17 — retrieval function, skill updates, contract amendment. This is the highest-leverage single change because it converts the entire learning system from a local-only tool into a cross-model asset.
- **#2 (Planning metrics):** Add `_compute_planning` section to `compute_stats.py`. Correlation between `question_shaped=true` and convergence rate. Shape confidence distribution. Assumption count vs. outcome quality.
- **#3 (Provenance metrics):** Add `_compute_provenance` section. Distribution of `provenance_unknown_count`. Recovery rate (unknown claims that got scouted → resolved). Gatherer source-tag failure rate.
- **#5 (Reason clarity):** Change `credential_scan.py` reason format from regex fragment to `f"{tier}:{family.name}"`. One-line fix with high audit trail impact.
- **#6 (Parse degradation):** Add `_compute_diagnostics` section for `parse_truncated`/`parse_degraded` counts.

**When done:** Users can measure whether `--plan` helps, whether gatherers are tagging sources correctly, and whether their analytics data is clean. Consultations benefit from accumulated project knowledge. Audit trails are human-readable.

**Unblocks:** Phase 2 — planning metrics inform whether automatic plan-mode suggestion (#9) is worth pursuing. Provenance metrics inform whether gatherer improvements are needed.

### Phase 2: Capability Completeness

**Findings: #4, #7, #8**

Fill the measurement gaps for the two unmeasured capabilities (single-turn `/codex` and `codex-reviewer`) and add thread continuity.

- **#4 (Single-turn quality):** Add `_compute_consultation` section. Prompt/result length distributions, thread continuation rate, repeat-topic detection.
- **#7 (Thread discovery):** Thread listing from event log, presentation via new `--threads` flag or `/consultation-stats --type threads`, selection UI for resumption.
- **#8 (Reviewer analytics):** Event emission in `codex-reviewer.md`, optional new event type or `consultation_outcome` with `source: review` field, stats section.

**When done:** All four capabilities and the reviewer agent are measured. Users can resume past consultations without manual threadId tracking. The analytics ecosystem provides complete Codex usage visibility.

**Unblocks:** Phase 3 — complete analytics baseline enables informed decisions about whether automatic plan-mode suggestion is worth the UX complexity.

### Phase 3: Precision Improvements

**Findings: #9, #10**

Lower-leverage refinements that improve precision without changing capabilities.

- **#9 (Automatic plan suggestion):** Extend pattern detection to identify plan-worthy questions. UX design needed to avoid being intrusive — likely a one-line suggestion, not automatic activation.
- **#10 (Multi-field scan priority):** Collect all field scan results before selecting the highest-tier reason for logging. Enforcement correctness is already correct; this only affects audit trail informativeness.

**When done:** The system proactively guides users toward more effective consultation patterns and produces maximally informative audit trails.
