# CCDI Phase A Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Build CCDI Phase A — automatic detection and injection of Claude Code extension documentation into Codex consultations at briefing time (initial injection only, no mid-dialogue).

**Architecture:** A Python CLI tool (topic_inventory.py) with classify and build-packet commands drives all deterministic logic. A ccdi-gatherer subagent runs in parallel during /dialogue to search docs and build packets. CCDI-lite adds one-shot injection to /codex. The dump_index_metadata tool in claude-code-docs MCP server feeds inventory generation.

**Tech Stack:** Python 3.11+ (CLI, classification, packet building), TypeScript (MCP tool), pytest (Python tests), vitest (TypeScript tests)

**Spec:** docs/superpowers/specs/ccdi/ — 10 files, 8 normative authorities. Read spec.yaml for the authority model.

---

## Scope

**Phase A includes:**
- CCDI-lite in /codex (classify, search, build-packet, inject into briefing)
- Full CCDI pre-dialogue phase in /dialogue (classify, dispatch ccdi-gatherer, briefing assembly, initial commit)
- ccdi-gatherer subagent
- Inventory generation pipeline (build_inventory.py + dump_index_metadata)
- PostToolUse hook for inventory refresh on docs_epoch change

**Phase A does NOT include:**
- dialogue-turn command (Phase B — mid-dialogue per-turn CCDI)
- --mark-deferred, --skip-build, --shadow-mode flags
- Shadow mode gate, graduation protocol
- Target-match predicate, semantic hints
- Registry state machine beyond detected->injected and detected->suppressed
- Replay harness, Layer 2b agent sequence tests

---

## File Structure

All paths relative to packages/plugins/cross-model/ unless stated otherwise.

### New Files

| File | Responsibility |
|------|---------------|
| scripts/ccdi/__init__.py | Package init |
| scripts/ccdi/types.py | Data model: TopicRecord, Alias, DenyRule, QueryPlan, DocRef, CompiledInventory, ClassifierResult, RegistrySeed, TopicRegistryEntry, FactPacket, config types |
| scripts/ccdi/config.py | Load ccdi_config.json, validate ranges, cross-key checks, built-in defaults |
| scripts/ccdi/classifier.py | Two-stage pipeline: candidate generation (alias matching) + ambiguity resolution |
| scripts/ccdi/packets.py | Fact packet builder: ranking, snippet/paraphrase selection, budget enforcement, rendered markdown output |
| scripts/ccdi/registry.py | Registry file I/O, mark_injected, automatic suppression, null-field serialization, transport-field stripping |
| scripts/ccdi/inventory.py | Load compiled inventory, version validation, schema evolution |
| scripts/topic_inventory.py | CLI entry point: classify and build-packet commands via argparse |
| scripts/build_inventory.py | MCP client: calls dump_index_metadata, generates scaffold, merges overlay, writes topic_inventory.json |
| data/ccdi_config.json | Default config (copy of spec defaults) |
| data/topic_overlay.json | Initial curated overlay (minimal — denylist + key alias fixes) |
| agents/ccdi-gatherer.md | Subagent: search docs, build initial packet, emit sentinel-wrapped registry seed |
| hooks/ccdi_inventory_refresh.py | PostToolUse hook: trigger build_inventory.py on docs_epoch change |
| tests/test_ccdi_types.py | Type construction and serialization tests |
| tests/test_ccdi_classifier.py | Classifier unit tests (spec: test_topic_inventory.py) |
| tests/test_ccdi_packets.py | Packet builder unit tests |
| tests/test_ccdi_registry.py | Registry Phase A subset: mark-injected, suppression, null-field serialization |
| tests/test_ccdi_config.py | Config loading, validation, cross-key checks |
| tests/test_ccdi_cli.py | CLI integration tests: file I/O, exit codes, stdout/stderr |
| tests/test_ccdi_contracts.py | Boundary contract tests across components |
| tests/test_build_inventory.py | Inventory generation tests: scaffold, overlay merge, version axes |
| tests/test_ccdi_hooks.py | PostToolUse hook tests |
| tests/test_ccdi_integration.py | End-to-end integration tests: ccdi-gatherer output, /codex injection, graceful degradation, sentinel handling |

### New Files (claude-code-docs MCP server)

| File | Responsibility |
|------|---------------|
| packages/mcp-servers/claude-code-docs/src/dump-index-metadata.ts | dump_index_metadata tool handler + output schema |
| packages/mcp-servers/claude-code-docs/tests/dump-index-metadata.test.ts | Tool tests |

### Modified Files

| File | Change |
|------|--------|
| packages/mcp-servers/claude-code-docs/src/index.ts | Register dump_index_metadata tool |
| packages/mcp-servers/claude-code-docs/src/lifecycle.ts | Add getContentHash() accessor |
| skills/codex/SKILL.md | Add CCDI-lite flow after threshold check |
| skills/dialogue/SKILL.md | Add ccdi-gatherer dispatch, sentinel extraction, initial commit |

---

## Task 1: Foundation Types and Config

**Files:**
- Create: `scripts/ccdi/__init__.py`, `scripts/ccdi/types.py`, `scripts/ccdi/config.py`
- Create: `data/ccdi_config.json`
- Test: `tests/test_ccdi_types.py`, `tests/test_ccdi_config.py`

**Spec references:** `data-model.md` (full file), `classifier.md#output-structure`, `packets.md#packet-structure`, `registry.md#entry-structure`

- [ ] **Step 1: Create scripts/ccdi/__init__.py** — empty package init
- [ ] **Step 2: Write test_ccdi_types.py** — test construction of Alias (weight clamping), DenyRule (discriminated union), TopicRecord (minimum 1 alias), RegistrySeed serialization (null fields present for ALL nullable fields, non-nullable always-present fields serialized including empty arrays and false, transport fields excluded, pending_facets FIFO order preserved)
- [ ] **Step 3: Run tests — expect ImportError** (module doesn't exist yet)
- [ ] **Step 4: Implement types.py** — all data model types as dataclasses. Key invariants:
  - `Alias.__post_init__` clamps weight to [0.0, 1.0]
  - `RegistrySeed.to_json()` serializes ALL fields — explicit nulls for nullable fields, empty arrays/false for non-nullable fields. Excludes ONLY `results_file` and `inventory_snapshot_path` (transport-only).
  - `RegistrySeed.from_json()` strips transport fields at load time, warns if present
  - `TopicRegistryEntry.new_detected()` factory with correct `consecutive_medium_count` initialization (1 if medium AND leaf, else 0)
  - `VALID_FACETS`, `TRANSPORT_ONLY_FIELDS`, `DURABLE_STATES` constants
  - `TopicRegistryEntry.from_dict()` applies all 19 schema-evolution defaults from `data-model.md` Registry Entry Schema Field Defaults table for absent fields (including derived defaults: `family_key` from `topic_key`, `coverage_target` from `kind`, `facet` defaults to `"overview"`, `kind` defaults to `"leaf"`)
  - Types: Alias, DenyRule, DocRef, QuerySpec, QueryPlan, TopicRecord, CompiledInventory, OverlayMeta, AppliedRule, MatchedAlias, ResolvedTopic, SuppressedCandidate, ClassifierResult, TopicRegistryEntry, RegistrySeed, FactItem, FactPacket
- [ ] **Step 5: Run type tests — expect PASS**
- [ ] **Step 6: Write test_ccdi_config.py** — test missing file uses defaults, partial config fills defaults, version mismatch falls back, null value uses default, cross-key min>max triggers paired fallback, out-of-range weight uses default
- [ ] **Step 7: Implement config.py** — `CCDIConfigLoader` class, `BUILTIN_DEFAULTS` dict, `SUPPORTED_CONFIG_VERSION = "1"`, per-key range validation, cross-key token-budget pair validation. Returns frozen `CCDIConfig` dataclass.
- [ ] **Step 8: Create data/ccdi_config.json** — exact copy of defaults from data-model.md
- [ ] **Step 9: Run all tests, commit**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_ccdi_types.py tests/test_ccdi_config.py -v`

---

## Task 2: dump_index_metadata Tool (TypeScript)

**Files:**
- Create: `packages/mcp-servers/claude-code-docs/src/dump-index-metadata.ts`
- Create: `packages/mcp-servers/claude-code-docs/tests/dump-index-metadata.test.ts`
- Modify: `packages/mcp-servers/claude-code-docs/src/index.ts` (register tool)
- Modify: `packages/mcp-servers/claude-code-docs/src/lifecycle.ts` (add getContentHash)

**Spec references:** `integration.md#dump_index_metadata-response-schema`

- [ ] **Step 1: Write tests** — test empty index (empty categories, docs_epoch null), chunks grouped by category, headings extracted from content, code_literals extracted from backticked identifiers, config_keys extracted (dotted paths, camelCase), distinctive_terms (literals in <=3 chunks), docs_epoch passes through from contentHash (including null case)
- [ ] **Step 2: Run tests — expect module not found**
- [ ] **Step 3: Implement dump-index-metadata.ts** — `buildMetadataResponse(index, contentHash)` function + Zod output schema per integration.md response schema. All fields from the spec: index_version, built_at, docs_epoch (string|null), categories[].{name, aliases, chunk_count, chunks[].{chunk_id, source_file, headings, code_literals, config_keys, distinctive_terms}}.
- [ ] **Step 4: Add getContentHash() to ServerState** in lifecycle.ts — store contentHash from serialize/cache load, expose via public accessor
- [ ] **Step 5: Register tool in index.ts** — follow search_docs registration pattern. No input params. Uses DumpIndexMetadataOutputSchema.
- [ ] **Step 6: Run tests + type-check, commit**

Run: `cd packages/mcp-servers/claude-code-docs && npm test -- --run tests/dump-index-metadata.test.ts && npx tsc --noEmit`

---

## Task 3: Inventory Generation

**Files:**
- Create: `scripts/ccdi/inventory.py`, `scripts/build_inventory.py`, `data/topic_overlay.json`
- Test: `tests/test_build_inventory.py`

**Spec references:** `data-model.md` (CompiledInventory, version axes, overlay merge, DenyRule), `integration.md#inventory-generation`

- [ ] **Step 1: Write test_build_inventory.py** — implement ALL rows from `delivery.md#inventory-tests-testbuildinventorypy`. The spec table is the authoritative list. This includes scaffold generation, ALL overlay operations (scalar replace, array append+dedupe, add_topic, remove_alias, override_weight, replace_aliases, replace_refs, replace_queries), ALL version axis mismatch tests (schema_version, overlay_schema_version, merge_semantics_version — three distinct failure tests), ALL DenyRule validations (drop+nonnull, downrank+null, downrank+zero, exact match_type rejected, penalty out-of-bounds, penalty=1.0 boundary), overlay format validation (unknown root keys, missing overlay_version), overlay rule unknown operation, config_version mismatch defaults, ALL config override tests (unknown keys, valid namespace unknown leaf, type mismatch, partial config defaults), ALL weight clamping tests (scaffold-generated, add_topic, override_weight, replace_aliases), ALL duplicate ID tests (deny_rule.id, rule_id across same ops, rule_id across mixed ops), cross-key paired fallback tests (min>max, valid min + invalid max), replace_queries/add_topic missing default_facet, replace_refs/replace_queries on unknown topic.
- [ ] **Step 2: Run tests — expect ImportError**
- [ ] **Step 3: Implement inventory.py** — `load_inventory(path) -> CompiledInventory` with: schema_version validation (warn on mismatch, best-effort per data-model.md#failure-modes), DenyRule load-time validation (warn-and-skip per resilience principle, WARNING for union violations, INFO for range violations), merge_semantics_version absent -> assume "1" with warning, merge_semantics_version mismatch at load -> warn + best-effort, missing overlay_meta -> warn + empty applied_rules.
- [ ] **Step 4: Implement build_inventory.py** — MCP client + scaffold generator + overlay merger. CLI: `uv run scripts/build_inventory.py [--force] [--overlay path] [--output path]`. Scaffold: category->family topic, heading->leaf topic, code_literal->exact alias, config_keys->exact alias with `facet_hint: "config"`, distinctive_term->phrase/token alias. Overlay merge per data-model.md#overlay-merge-semantics. Build-time validation: version axes fail loudly, DenyRule discriminated union, penalty range, post-merge alias count, rule_id uniqueness. AppliedRule serialization order: rules[]-sourced first, then config_overrides-sourced with config-override: prefix.
- [ ] **Step 5: Create data/topic_overlay.json** — minimal denylist (drop "overview", downrank "schema") + empty config_overrides
- [ ] **Step 6: Run tests, commit**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_build_inventory.py -v`

---

## Task 4: Classifier Pipeline

**Files:**
- Create: `scripts/ccdi/classifier.py`
- Test: `tests/test_ccdi_classifier.py` (spec names this `test_topic_inventory.py` — renamed to avoid confusion with the CLI script)

**Spec references:** `classifier.md` (full file — two-stage pipeline, confidence levels, worked example)

- [ ] **Step 1: Write test_ccdi_classifier.py** — implement ALL rows from `delivery.md#classifier-tests-testtopicInventorypy`. The spec table is the authoritative list — implement every row without exception.
- [ ] **Step 2: Run tests — expect ImportError**
- [ ] **Step 3: Implement classifier.py** — pure function `classify(text, inventory, config) -> ClassifierResult`. Stage 1: normalize input, linear scan over all aliases, match by type (exact at word boundaries, phrase case-insensitive, token case-insensitive, regex), accumulate scores per topic with evaluation order (exact>phrase>token), cross-type suppression. Stage 2: leaf absorbs family, collapse weak leaves, suppress orphaned generics, apply denylist penalties. Assign confidence levels per config thresholds.
- [ ] **Step 4: Run tests, commit**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_ccdi_classifier.py -v`

---

## Task 5: Packet Builder

**Files:**
- Create: `scripts/ccdi/packets.py`
- Test: `tests/test_ccdi_packets.py`

**Spec references:** `packets.md` (full file — structure, budgets, build process, citation format)

- [ ] **Step 1: Write test_ccdi_packets.py** — implement ALL rows from `delivery.md#packet-builder-tests`. The spec table is the authoritative list. This includes both budget ranges, empty results, duplicate chunk IDs, citation format, snippet/paraphrase mode selection, too-large snippet truncated, quality threshold boundary (0.3 passes, 0.29 fails), budget boundary (N+1 facts), mid-turn topics cardinality, mid-turn snippet cardinality, chunk ordering deterministic, paraphrase selection deterministic, no resolvable topics empty output.
- [ ] **Step 2: Run tests — expect ImportError**
- [ ] **Step 3: Implement packets.py** — `build_packet(results, mode, config, registry_entry, facet)`, `render_initial(packet)`, `render_mid_turn(packet)`. Deterministic ranking (facet relevance + chunk_id tiebreaker, no randomization). Idempotency: same inputs -> identical output (stable sort, deterministic selection). Citation format `[ccdocs:<chunk_id>]`. Initial renders under `### Claude Code Extension Reference`. Mid-turn renders with `<!-- ccdi-packet topics="..." facet="..." -->` metadata comment.
- [ ] **Step 4: Run tests, commit**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_ccdi_packets.py -v`

---

## Task 6: Registry — Phase A Subset

**Files:**
- Create: `scripts/ccdi/registry.py`
- Test: `tests/test_ccdi_registry.py`

**Spec references:** `registry.md#entry-structure`, `registry.md#state-transitions`, `registry.md#field-update-rules`, `data-model.md#registryseed`

Phase A scope: mark_injected, automatic suppression, seed I/O, and all field-level invariants exercised by detected->injected and detected->suppressed paths.

**Phase B exclusions** (skip these rows from the spec): all deferred state tests (cooldown, scout_priority, target_mismatch, TTL lifecycle), all semantic hint tests, all consecutive-turn medium tracking tests that require dialogue-turn, all session-local cache tests, single medium-confidence no initial injection (scheduling rule), low-confidence detected but never injected (scheduling rule), send failure tests that require agent-level codex-reply flow, facet_expansion/pending_facet candidate emission. NOTE: scheduling tiebreaker (deterministic entry ordering) IS Phase A — it tests registry-level ordering without dialogue-turn.

- [ ] **Step 1: Write test_ccdi_registry.py** — implement ALL remaining rows from `delivery.md#registry-tests` that are NOT in the exclusion list above. This includes: detected->injected happy path, attempt states not persisted, idempotent mark-injected (no duplicate facets_injected/injected_chunk_ids), family overview sets overview_injected, overview_injected propagation (3 tests: at overview, at non-overview, family_context_available on leaf), weak_results suppression, redundant suppression, suppressed vs deferred distinction, registry corruption recovery, no commit without send, injected forward-only invariant, consecutive_medium_count reset after injection, pending_facets cleared after serving, injected_chunk_ids populated at commit, uniqueness enforcement on corrupt input, docs_epoch null comparisons (4 tests: null==null, null->non-null, non-null->null, multi-entry scan), multiple pending_facets ordering, last_query_fingerprint normalization, suppressed re-detection no-op, scheduling tiebreaker (deterministic ordering of entries).
- [ ] **Step 2: Run tests — expect ImportError**
- [ ] **Step 3: Implement registry.py** — `load_registry(path)` (strip transport fields, warn on results_file presence, validate family-kind consecutive_medium_count=0, handle attempt-local states by reinitialization), `mark_injected(...)`, `write_suppressed(...)`, `_write_registry(path, seed)` (atomic: temp + rename). All writes via RegistrySeed.to_json(). Handle inventory_snapshot_version null/blank/absent at seed load as version mismatch per data-model.md#failure-modes.
- [ ] **Step 4: Run tests, commit**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_ccdi_registry.py -v`

---

## Task 7: CLI Entry Point

**Files:**
- Create: `scripts/topic_inventory.py`
- Create: `tests/fixtures/ccdi/test_inventory.json`
- Test: `tests/test_ccdi_cli.py`

**Spec references:** `integration.md#cli-tool-topicinventorypy`

**Phase B exclusions:** dialogue-turn command, --mark-deferred, --skip-build, --shadow-mode, source divergence canary meta-test (requires dialogue-turn code paths).

- [ ] **Step 1: Write test_ccdi_cli.py** — implement ALL Phase A-relevant rows from `delivery.md#cli-integration-tests`. This includes: classify file I/O roundtrip, build-packet initial mode produces markdown, build-packet mark-injected updates registry, build-packet empty output writes suppressed (weak), build-packet empty output writes suppressed (redundant), missing inventory nonzero exit, malformed text nonzero exit, stdout/stderr separation, automatic suppression requires registry (no suppression without --registry-file), --inventory-snapshot passed without --registry-file (silently ignored), missing --inventory-snapshot on build-packet with --registry-file (error), build-packet rejects --inventory flag (wrong name), classify rejects --inventory-snapshot flag, missing --coverage-target with --mark-injected (error), missing --topic-key with --registry-file (error), missing --facet with --mark-injected (error), prepare/commit packet idempotency initial mode, agent gate unchanged when initial_threshold overridden, agent gate unchanged when config more permissive, agent gate matches built-in defaults, agent gate config isolation Phase A.
- [ ] **Step 2: Create test fixture** — tests/fixtures/ccdi/test_inventory.json with hooks (family + pre_tool_use leaf) and skills topics. Minimal valid CompiledInventory.
- [ ] **Step 3: Run tests — expect FileNotFoundError**
- [ ] **Step 4: Implement topic_inventory.py** — argparse CLI with `classify` and `build-packet` subcommands. Flag validation order per integration.md: required-flag presence first, facet consistency second. classify uses --inventory (NOT --inventory-snapshot; reject the wrong flag). build-packet validates --registry-file requires --inventory-snapshot, --mark-injected requires --coverage-target + --topic-key + --facet. build-packet rejects --inventory flag (wrong name). All JSON on stdout, errors on stderr. CCDI-lite empty output: exit 0, empty stdout, no stderr.
- [ ] **Step 5: Run tests, commit**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_ccdi_cli.py -v`

---

## Task 8: Boundary Contract Tests

**Files:**
- Create: `tests/test_ccdi_contracts.py`

**Spec references:** `delivery.md#boundary-contract-tests-testccdicontractspy`

**Phase B exclusions:** semantic hints -> CLI contracts, mid-dialogue CCDI disabled without ccdi_seed (Layer 2b), ccdi_policy_snapshot boundary test (but DO include the xfail placeholder).

- [ ] **Step 1: Write test_ccdi_contracts.py** — implement ALL Phase A-relevant rows from `delivery.md#boundary-contract-tests`. This includes: inventory->classifier (topic_key, family_key, alias normalization, denylist shapes), classifier->registry (confidence, facet, coverage_target, candidate_type enums), search results->packet builder (required fields), packet->prompt (citation, markdown, budget), CLI->agents (exit codes, stdout JSON, stderr), config->CLI schema, dump_index_metadata->build_inventory.py response shape + schema evolution (unknown field ignored, required field missing, index_version change), registry seed->delegation envelope (ccdi_seed path valid, JSON schema), registry null-field serialization (detected state + envelope fields), RegistrySeed durable fields completeness (schema comparison including all 5 coverage.* sub-fields), transport-only field allowlist completeness, results_file write-time exclusion (defense-in-depth), results_file stripped after commit, results_file stripped after multi-topic commit, results_file stripped when all commits fail, results_file present on load (warning), DenyRule load-time warn-and-skip, pending_facets serialization order, RegistrySeed version mismatch + topic_key discard, RegistrySeed inventory_snapshot_version null at load, RegistrySeed<->ClassifierResult coverage_target enum, RegistrySeed<->ClassifierResult facet enum, version axes->overlay merge compatibility, inventory->classifier schema evolution, inventory->packet builder schema evolution, inventory->registry schema evolution, registry file with attempt-local state (reinitialized), defaults table<->TopicRegistryEntry durable fields sync, ccdi_inventory_snapshot absent with ccdi_seed present (degraded), ccdi_seed inline JSON rejection, ccdi_policy_snapshot xfail placeholder (strict=True).
- [ ] **Step 2: Run tests, fix any issues, commit**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_ccdi_contracts.py -v`

---

## Task 9: ccdi-gatherer Subagent

**Files:**
- Create: `agents/ccdi-gatherer.md`

**Spec references:** `integration.md#data-flow-full-ccdi-dialogue` (pre-dialogue phase), `integration.md#registry-seed-handoff`, `data-model.md#registryseed`

- [ ] **Step 1: Write ccdi-gatherer.md** — subagent that receives classified topics + query plans, calls search_docs per topic (max 3 topics, 1-2 queries each), writes results to temp file, pins inventory snapshot to temp file, calls build-packet --mode initial (no --registry-file, no --mark-injected), builds RegistrySeed from classified topics in detected state, emits rendered markdown + sentinel-wrapped seed. Sentinel emission precondition: MUST NOT emit if inventory failed to load or schema_version is blank/null/absent. Tools: mcp__claude-code-docs__search_docs, Bash, Read. Model: sonnet (matches existing context-gatherer agents). Config isolation: agent MUST NOT read *ccdi_config* files.
- [ ] **Step 2: Commit**

---

## Task 10: CCDI-Lite /codex Integration

**Files:**
- Modify: `skills/codex/SKILL.md`

**Spec references:** `integration.md#data-flow-ccdi-lite-codex`, `integration.md#cross-plugin-dependency`

- [ ] **Step 1: Read current /codex skill**
- [ ] **Step 2: Add CCDI-lite flow** — capability detection first (check search_docs availability; if unavailable + Claude Code topic detected -> note, proceed without CCDI). If available: write prompt to temp, run classify, check threshold (agent-side fixed heuristic: 1 high OR 2+ medium same family — hardcoded, NOT read from ccdi_config.json), if met: search_docs per topic query plan, write results to temp, run build-packet --mode initial, inject non-empty output as `### Claude Code Extension Reference` under `## Material`. No registry, no commit, no state. If threshold not met or low-confidence only: proceed without CCDI, discard results.
- [ ] **Step 3: Commit**

---

## Task 11: /dialogue Pre-Dialogue Phase + Initial Commit

**Files:**
- Modify: `skills/dialogue/SKILL.md`

**Spec references:** `integration.md#data-flow-full-ccdi-dialogue`, `integration.md#registry-seed-handoff`, `integration.md#delegation-envelope-fields`

- [ ] **Step 1: Read current /dialogue skill**
- [ ] **Step 2: Add ccdi-gatherer dispatch** — capability detection (same as /codex). Run classify, check threshold (same hardcoded heuristic), if met: dispatch ccdi-gatherer in parallel with context-gatherers. Add output to `## Material > ### Claude Code Extension Reference`. Config isolation: skill MUST NOT read *ccdi_config* files.
- [ ] **Step 3: Add sentinel extraction + initial commit** — parse sentinel block from ccdi-gatherer output. If sentinel found: extract JSON, read results_file AND inventory_snapshot_path from parsed JSON, write seed to temp file. After briefing send confirmed: per-entry `build-packet --results-file <path> --registry-file <seed_path> --mode initial --topic-key <key> --facet <entry.facet> --coverage-target <entry.coverage_target> --inventory-snapshot <inventory_snapshot_path> --mark-injected`. Handle per-topic outcomes: nonzero exit -> log + continue (topic remains detected), empty stdout -> suppressed (OK), non-empty -> committed. If send failed: no commit (all entries remain detected). If no sentinel: proceed without ccdi_seed (mid-dialogue CCDI disabled).
- [ ] **Step 4: Add delegation envelope fields** — pass `ccdi_seed` and `ccdi_inventory_snapshot` as atomic pair (both present or both absent). If one is missing, log warning and omit both per the atomic pair invariant. Also pass `ccdi_debug: true|absent` (controls trace emission in Phase B — wire the field now for forward compatibility).
- [ ] **Step 5: Commit**

---

## Task 12: Integration Tests

**Files:**
- Create: `tests/test_ccdi_integration.py`

**Spec references:** `delivery.md#integration-tests`

**Phase B exclusions:** Full dialogue turn with mid-turn injection, shadow mode diagnostics tests, active mode diagnostics absent tests, inventory pinning across mid-dialogue reload, ccdi_debug gating tests, ccdi_trace tests, temp file identity per turn, suppressed re-detection no-op CLI-level.

- [ ] **Step 1: Write test_ccdi_integration.py** — implement ALL Phase A-relevant rows from `delivery.md#integration-tests` AND the Phase A-relevant row from `delivery.md#diagnostics-emitter-tests`. Integration tests: ccdi-gatherer produces valid markdown, /codex CCDI-lite briefing injection (`### Claude Code Extension Reference` present), graceful degradation without search_docs (ccdi_status: unavailable), malformed search results handled (missing chunk_id, empty content -> skip not crash), inventory schema version mismatch (warning not crash), inventory missing overlay_meta field (warning, continue), inventory stale docs_epoch mismatch (diagnostics warning, continue), sentinel extraction from ccdi-gatherer (valid block -> ccdi_seed present), malformed sentinel handling (3 sub-cases: missing close tag, invalid JSON, mismatched tags), ccdi-gatherer returns no sentinel (no ccdi_seed, initial_only phase), initial CCDI commit skip on briefing-send failure (entries remain detected), CCDI-lite low-confidence -> no injection no state, initial threshold not met Full CCDI (no ccdi-gatherer dispatched), initial threshold not met CCDI-lite (no build-packet invoked). Diagnostics emitter: `status: "unavailable"` schema test (when claude-code-docs not installed — only `status` and `phase` populated, all count/array fields absent). Phase B diagnostics tests (false_positive_field_always_zero, active/shadow mode field presence) are deferred.
- [ ] **Step 2: Run tests, commit**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_ccdi_integration.py -v`

---

## Task 13: PostToolUse Hook + Final Verification

**Files:**
- Create: `hooks/ccdi_inventory_refresh.py`
- Test: `tests/test_ccdi_hooks.py`

**Spec references:** `delivery.md#testccdihookspy`, `data-model.md#inventory-lifecycle`

- [ ] **Step 1: Write test_ccdi_hooks.py** — implement ALL rows from `delivery.md#testccdihookspy`. This includes: fires on docs_epoch change in tool_response, skips non-epoch changes, handles build failure gracefully, manual --force flag bypasses epoch check, ignores tool_result field (wrong key), ignores root-level docs_epoch.
- [ ] **Step 2: Implement hook** — reads PostToolUse payload from stdin, checks tool_response.docs_epoch, invokes build_inventory.py. Never blocks tool use (exit 0 always). Fail-open per resilience principle.
- [ ] **Step 3: Run ALL tests as final verification**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_ccdi_*.py tests/test_build_inventory.py -v`

- [ ] **Step 4: Commit**

---

## Phase A Completion Checklist

After all 13 tasks, verify end-to-end:

- [ ] `classify` command returns valid ClassifierResult JSON
- [ ] `build-packet --mode initial` produces citation-backed markdown
- [ ] `build-packet --mark-injected` updates registry correctly
- [ ] `build_inventory.py` generates topic_inventory.json from metadata + overlay
- [ ] ccdi-gatherer subagent can produce markdown + sentinel seed
- [ ] `/codex` CCDI-lite injects extension docs into briefing
- [ ] `/dialogue` dispatches ccdi-gatherer, performs initial commit, passes envelope fields
- [ ] PostToolUse hook triggers inventory refresh
- [ ] All boundary contract tests pass
- [ ] All integration tests pass
- [ ] No existing tests regressed: `cd packages/plugins/cross-model && uv run pytest`

---

## What's Next (Phase B)

Phase B adds mid-dialogue CCDI. It builds on Phase A's foundation:

| Component | Phase B Addition |
|-----------|-----------------|
| topic_inventory.py | dialogue-turn command |
| registry.py | Full state machine (deferred, TTL, semantic hints, caching) |
| packets.py | --mode mid_turn |
| codex-dialogue.md | Per-turn prepare/commit loop |
| delivery.md | Shadow mode gate, graduation protocol, diagnostics |
| Tests | Replay harness, Layer 2b agent sequence, shadow mode |

Phase B implementation should be planned separately after Phase A is verified end-to-end.
