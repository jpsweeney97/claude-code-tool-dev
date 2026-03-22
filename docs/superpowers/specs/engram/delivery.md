---
module: delivery
status: active
normative: true
authority: delivery
---

# Delivery

## Context

All three plugins live in the development repo. No external users, no production deployments. Old plugins can be broken freely during development.

**Approach:** Build Engram, move data, delete old code. No coexistence period.

## Build Sequence

```
Step 0a: Foundation contracts (plugin + core library + type contracts)
    |
Step 0b: Bootstrap and identity (engram init + .engram-id)
    |
Step 1: Bridge cutover (defer/ingest)
    |
Step 2: Knowledge cutover + engram_guard engine_trust_injection capability
    |
Step 3: Work cutover
    |
Step 4: Context cutover
    |
Step 5: Cleanup
```

## Step 0a: Foundation Contracts

Create plugin, core library, and type contracts. Validate the foundation before bootstrap.

| Deliverable | Detail |
|---|---|
| Plugin manifest | `packages/plugins/engram/.claude-plugin/plugin.json` |
| `engram_core/types.py` | [RecordRef, RecordMeta, IndexEntry, QueryResult, envelope types](types.md) (including [lesson-meta](types.md#knowledge-entry-format-lesson-meta-contract) contract and per-candidate fingerprints in `DistillEnvelope` [idempotency material](types.md#idempotency-same-operation-retried)) |
| `engram_core/reader_protocol.py` | [NativeReader protocol](storage-and-indexing.md#nativereader-protocol) with `root_type: Literal["shared", "private"]` parameter on `scan()` |
| `engram_core/query.py` | [Fresh-scan query engine](storage-and-indexing.md#fresh-scan-no-cached-index) |

**Exit criteria:** All types pass construction and equality tests. Query scans empty directories with correct diagnostics. NativeReader protocol compiles with `root_type` parameter.

#### Required Verification
- Construction and equality tests for all types
- Query scans empty directories with correct diagnostics
- `VERSION_UNSUPPORTED` error for unknown `envelope_version` (VR-0A-3): submit envelope with `envelope_version="99.0"`, assert `error_code == "VERSION_UNSUPPORTED"`, `received_version == "99.0"`, and `expected_version` is a single string matching the engine's built-in version (not a list or range). See [types.md §Compatibility Rules](types.md#compatibility-rules).
- Normalization boundary test (VR-0A-6): construct a string where `knowledge_normalize` and `drift_hash`-level normalization (NFC+LF only) produce different outputs (e.g., trailing whitespace). Assert `content_hash(input) != drift_hash(input)`. Separately, assert `content_hash(input) != work_dedup_fingerprint(input, [])` for a mixed-case input. This proves the three pipelines diverge — using the wrong one would produce a different hash.
- Core invariant (index-not-mutate) structural tests (VR-0A-1): (a) Assert `NativeReader` protocol has no `write()` method (static protocol check). (b) Assert `query.py` module contains no filesystem write calls (`open(..., 'w')`, `os.replace`, `shutil.copy`, etc.). (c) Integration test: run a cross-reader query against a fixture with files in all three subsystem directories, assert no files were created, modified, or deleted in the subsystem directories after the query completes.
- `canonical_json_bytes()` contract tests (VR-0A-2): (a) `canonical_json_bytes({"k": None})` raises ValueError; (b) `canonical_json_bytes({"k": 3.14})` raises TypeError; (c) `canonical_json_bytes({"b": 1, "a": 2}) == canonical_json_bytes({"a": 2, "b": 1})` (key sorting determinism); (d) same input produces byte-identical output across two calls.
- `parse_sha256_hex()` contract tests (VR-0A-4): (a) accepts 64-char lowercase hex; (b) accepts `sha256:<64-char-lowercase-hex>` (strips prefix, returns bare); (c) rejects uppercase hex; (d) rejects `SHA256:<hex>`; (e) rejects `sha384:<hex>`; (f) rejects 63-char hex; (g) round-trip: `parse_sha256_hex(f"sha256:{h}") == h` for arbitrary valid `h`.
- Degradation model tests (VR-0A-5): (a) private root path set to non-existent directory → `diagnostics.degraded_roots == ["private"]`, entries still returned from shared root; (b) knowledge reader `scan()` raises RuntimeError → `diagnostics.degraded_subsystems` contains `"knowledge"`, work and context entries still returned; (c) both roots unavailable → `diagnostics.degraded_roots == ["private", "shared"]`, `entries == []`.
- Text search contract tests (VR-0A-7): (a) `query(text="auth middleware")` returns entry with "authentication" in title and "middleware" in tags (AND + substring); (b) same query does NOT return entry with only "authentication" in title (AND semantics); (c) `query(text="AUTH")` returns same results as `query(text="auth")` (case-insensitive); (d) `query(text="nonexistent")` returns 0 entries.
- Namespace status filtering rejection (VR-0A-8): `query(status="open")` without `subsystems` raises ValueError; `query(subsystems=["work", "knowledge"], status="open")` raises ValueError; `query(subsystems=["work"], status="open")` succeeds (auto-prefixed to `"work:open"`).
- Field preservation gate (T1-gate-1, activates at Step 2a): verify that rewriting a `lesson-meta` entry with an unknown field preserves that field verbatim. Deferred from Step 0a because field preservation is only exercised when the Knowledge engine performs its first rewrite-capable operation. Scheduled here for traceability; test fixture created in Step 2a.
- Mixed-version degradation gate (T1-gate-2, activates at Step 2a): verify that a `lesson-meta` entry with `meta_version: "99.0"` is skipped per-entry (not per-file) with a warning in `QueryDiagnostics.warnings`. Deferred from Step 0a for the same reason. Scheduled here; test fixture created in Step 2a.
- Deferred gate stubs (VR-0A-9): T1-gate-1 and T1-gate-2 fixture stubs must exist as empty test files with TODO comments citing target behaviors before Step 0a is marked complete. This ensures deferred obligations are tracked structurally. (SY-25)
- IndexEntry.snippet contract test (VR-0A-10): for each NativeReader (context, work, knowledge), create a fixture file with body exceeding 500 characters. Assert: `IndexEntry.snippet` ≤ 200 characters. Assert: snippet does not end mid-word. (SY-26)
- `since` filter test (VR-0A-11): fixture with 3 entries at different timestamps. `query(since=<cutoff>)` returns only post-cutoff entries. UTC normalization: entry with +05:30 timestamp → `IndexEntry.created_at` is UTC-normalized. (SY-31)
- RecordRef serialization round-trip (VR-0A-12): for each subsystem, assert `RecordRef.from_str(ref.to_str(), ref.repo_id) == ref`. Edge case: `record_id` containing hyphens. (SY-47)

## Step 0b: Bootstrap and Identity

Create identity resolution and bootstrap command. Depends on 0a types being stable.

| Deliverable | Detail |
|---|---|
| `engram_core/identity.py` | `repo_id` generation/resolution, `worktree_id` derivation. See [identity resolution](types.md#identity-resolution). |
| `engram init` command | Generates `.engram-id` (UUIDv4), writes to repo root, stages for commit |
| `.engram-id` | Generated and committed (for this repo) |

**Exit criteria:** Identity works across worktrees. `engram init` is idempotent. [SessionStart](enforcement.md#sessionstart-hook) warns when `.engram-id` missing and points to `engram init`.

#### Required Verification
- `engram init` idempotency matrix (VR-0B-1): (a) `.engram-id` absent → creates file with valid UUIDv4, stages for commit; (b) `.engram-id` present with valid UUID → no-op, exits 0, prints "already initialized"; (c) `.engram-id` present with malformed content → error with message instructing manual repair or re-init with `--force`.

## Step 1: Bridge Cutover

The only existing cross-subsystem path with trusted writes on both ends. Proves Engram's value.

| Deliverable | Detail |
|---|---|
| [DeferEnvelope](types.md#deferenvelope-context-to-work) with [EnvelopeHeader](types.md#envelopeheader) | New envelope type |
| Bridge adapter + SourceResolver | Converts `DeferEnvelope` -> old `DeferredWorkEnvelope` JSON -> temp file -> old ticket engine ingest. SourceResolver reads source snapshot frontmatter to recover `session_id` for bridge mapping (see below). |
| Context reader | Parses handoff `---` frontmatter |
| Work reader | Parses ticket fenced YAML |
| `/defer` skill | Emits `DeferEnvelope`, adapter calls old ticket engine |

Readers point at current data locations. Data doesn't move yet. The bridge adapter is temporary scaffolding — it allows Step 1 to prove [envelope contracts](operations.md#envelope-invariants) without requiring the new Work engine (a Step 3 deliverable). The adapter preserves the old engine's existing dedup behavior.

### Bridge Field Mapping via SourceResolver

The old `DeferredWorkEnvelope` requires `source.type`, `source.ref`, and `source.session` as string fields. The new `EnvelopeHeader.source_ref` is a `RecordRef` with no `session` field. The bridge adapter uses an adapter-local `SourceResolver`:

| Old Field | Mapped From |
|---|---|
| `source.type` | `f"engram:{source_ref.subsystem}:{source_ref.record_kind}"` |
| `source.ref` | Canonical `RecordRef` serialization |
| `source.session` | `SourceResolver` reads `session_id` from the source snapshot's frontmatter |

The `SourceResolver` is adapter-local scaffolding — it dies with the bridge adapter in [Step 5](#step-5-cleanup). Do not add `session_id` to `EnvelopeHeader` or `RecordRef` to serve this temporary need.

### Cross-Step Dependency

Do not modify the `DeferEnvelope` or `EnvelopeHeader` types between Steps 1 and 3 without updating the bridge adapter. The adapter depends on both the new envelope format and the old ticket engine's ingest JSON schema.

### Bridge Compatibility Test

A behavioral contract test must accompany the bridge adapter:
1. Constructs a representative `DeferEnvelope` with full `EnvelopeHeader`
2. Runs it through the bridge adapter's conversion logic
3. Asserts the output is valid legacy `DeferredWorkEnvelope` JSON
4. Verifies `SourceResolver` field mapping (`source.type`, `source.ref`, `source.session`)

This test runs in CI across Steps 1–3. If type changes break the bridge, this test fails fast — replacing the process-level "do not modify" warning with a structural guard. The test is deleted in Step 5 cleanup alongside the bridge adapter.

**Exit criteria:** `/defer` produces envelope with RecordRef linkage. Bridge adapter successfully routes to old ticket engine. Cross-subsystem query returns results from both readers. Bridge compatibility test passes.

#### Required Verification
- Bridge compatibility test passes (Steps 1-4 as specified)
- Bridge test additionally verifies old engine accepts converted JSON (VR-1-1): call old ticket engine ingest with bridge output, assert non-error response
- SourceResolver exact-value assertion (VR-1-2): assert `source.type == f"engram:{source_ref.subsystem}:{source_ref.record_kind}"`, `source.ref == source_ref.to_str()`, `source.session == <expected_session_id>` with known fixture. (SY-33)

## Step 2: Knowledge Cutover

### Step 2a — Activate

| Deliverable | Detail |
|---|---|
| `engram/knowledge/learnings.md` | `git mv docs/learnings/learnings.md` |
| Knowledge reader, engine | Staging writes, dedup, publication, [promote-meta](types.md#promote-meta-promotion-state-record) |
| Staging inbox | `~/.claude/engram/<repo_id>/knowledge_staging/` |
| `/learn`, `/distill`, `/curate`, `/promote` | All knowledge skills |
| `engram_guard` hook (engine trust injection only) | [Engine trust injection](enforcement.md#trust-injection) for Knowledge engine. Write/Edit path authorization deferred to Step 3a. |

**Exit criteria (2a):** Full learn -> distill -> curate -> promote lifecycle. Staging dedup. [Staging inbox cap](enforcement.md#staging-inbox-cap).

#### Required Verification
- Promote-path wiring check (VR-2A-1): `PromoteMeta.transformed_text_sha256` must be produced by `drift_hash()`, not `content_hash()`. Construct promoted text with trailing whitespace. Assert `drift_hash(text)` detects the whitespace (different hash from stripped version) while `content_hash(text)` does not (same hash). This verifies the promote pipeline uses the correct — stricter — normalizer for drift detection.
- Promote hash recomputation (VR-2A-2): simulate the Approve/modify/skip flow where the user modifies transformed text during Step 2 confirmation. Assert: `PromoteMeta.transformed_text_sha256` matches `drift_hash()` of the *post-modification* text written to CLAUDE.md, not the original `PromoteEnvelope.transformed_text`. Separately, assert: if post-write text retrieval fails, Step 3 rejects the promote-meta write (lesson remains eligible for next `/promote`). See [Promote Hash Verification](types.md#promote-hash-verification).
- Write concurrency test (VR-2A-3): Spawn two threads, each calling the Knowledge engine publish path simultaneously. Assert: both entries appear in `learnings.md` without corruption and the lock file is absent post-operation. Timeout test: hold the lock externally and assert publish returns error with `"learnings.md is locked by another operation"` message within 5 seconds.
- PromoteEnvelope idempotency (VR-2A-4): Submit a PromoteEnvelope for a Branch A eligible lesson → assert promote-meta written. Submit the identical PromoteEnvelope again → assert Branch B1 rejection (no new CLAUDE.md write, same promote-meta content).
- T1-gate-1 implementation: rewrite a `lesson-meta` entry that contains an extra field `"future_field": "value"`. Assert the rewritten entry still contains `future_field` verbatim.
- T1-gate-2 implementation: create a `lesson-meta` entry with `meta_version: "99.0"`. Run `query()`. Assert: entry is skipped, `QueryDiagnostics.warnings` contains a per-entry message, other entries in the same file are still returned.

### Step 2b — Retire

- Remove old learn/distill/promote skills from repo `.claude/skills/`
- Remove deployed copies from `~/.claude/skills/{learn,distill,promote}/` (use `trash`)
- Remove knowledge-related code from handoff plugin

**Exit criteria (2b):** No old knowledge skills present in repo or deployed locations. New Engram skills are the sole providers.

## Step 3: Work Cutover

### Step 3a — Activate

| Deliverable | Detail |
|---|---|
| `engram/work/` | `git mv docs/tickets/*` |
| Work engine | 4-stage pipeline, trust model, dedup, autonomy — all preserved |
| `engram_guard` hook (full) | Extends Step 2a hook with [protected-path enforcement](enforcement.md#protected-path-enforcement) + [direct-write path authorization](enforcement.md#direct-write-path-authorization) for Work paths |
| `/ticket`, `/triage` | Work skills |
| Config | `.claude/engram.local.md` (see [autonomy configuration](enforcement.md#configuration)) |
| Bridge adapter update | `/defer` switches from bridge adapter (Step 1) to new Work engine |

**Exit criteria (3a):** All ticket operations work. Protected-path enforcement: Write/Edit to protected paths blocked reliably (verified by direct tool call attempts). Bash enforcement: representative shell write patterns tested, documented as [bounded guarantee](enforcement.md#enforcement-scope-bounded-guarantee). Trust triple works. Compatibility harness passes. `/defer` routes through new Work engine.

#### Required Verification
- Envelope idempotency (VR-3A-1): DeferEnvelope submitted twice returns same ref
- Phase-scoped idempotency regression gate (VR-3A-2): verify idempotency_key is checked by new Work engine after bridge replacement
- Staging inbox cap (VR-3A-3): cap=5, count=3, batch=3 → full rejection; cap=5, count=3, batch=2 → success
- Staging cap edge case (VR-3A-4): cap=5, count=0, batch=8 → full rejection with diagnostic message including both batch size and cap values. Assert error message contains "Batch size (8) exceeds staging cap (5)" and actionable guidance "Increase knowledge_max_stages to at least 8".
- Trust triple partial validation (VR-3A-5): (a) Submit engine payload with `hook_injected=True` only (missing `hook_request_origin` and `session_id`) → assert rejected with structured error; (b) submit with all three present but one empty string → assert rejected; (c) submit with `hook_injected=False` and other two valid → assert rejected; (d) submit with complete valid triple → assert accepted.
- Compatibility harness pass threshold (VR-3A-6): 100% of ported compatibility-critical fixtures must match on response envelope, on-disk ticket output, and audit side effects. Harness exceptions (intentional behavioral differences, e.g., new dedup logic) capped at 5, each requiring a comment explaining the intentional divergence.
- Ledger append failure isolation (VR-3A-7): Make shard file read-only (or raise IOError on flock). Run `/defer` end-to-end. Assert: (a) ticket created successfully in `engram/work/`; (b) no exception propagated to caller; (c) `QueryDiagnostics.warnings` on subsequent query notes the ledger gap.
- Trust injection path matching negative test (VR-3A-8): invoke `engram_guard` with a Bash tool call executing `python3 /tmp/engine_work.py` (valid filename, outside `<engram_scripts_dir>`). Assert: [payload file](enforcement.md#payload-file-contract) is NOT created. Then invoke with `python3 <engram_scripts_dir>/engine_work.py` (correct path). Assert: payload file IS created with valid trust triple fields.
- Trust triple call-site completeness (VR-3A-9): for each documented mutating entrypoint (Work: ticket creation, ticket update, ticket close; Knowledge: knowledge publish, staging write, promote-meta write), assert via AST scan or instrumented test that [`collect_trust_triple_errors()`](enforcement.md#collect_trust_triple_errors-contract) is called before any filesystem write. Acceptable methods: (a) `ast.parse` + visitor asserting the call appears before `open(..., 'w')` / `os.replace` / `shutil` calls; (b) mock `collect_trust_triple_errors` to raise on first call, invoke entrypoint, assert exception propagated.

### Step 3b — Retire

- Remove `packages/plugins/ticket/` package
- Remove deployed ticket plugin from `~/.claude/plugins/` (use `trash`)

**Exit criteria (3b):** No old ticket code present in repo or deployed locations.

## Step 4: Context Cutover

### Step 4a — Activate

| Deliverable | Detail |
|---|---|
| `~/.claude/engram/<repo_id>/` storage | Keyed by `repo_id` + `worktree_id`. See [storage layout](storage-and-indexing.md#dual-root-storage-layout). |
| Context engine | [Chain protocol](skill-surface.md#chain-protocol-session-lineage-tracking) updated |
| Hooks | [`engram_quality`](enforcement.md#quality-validation), [`engram_session`](enforcement.md#sessionstart-hook), `engram_register` |
| Skills | `/save`, `/load`, `/quicksave`, `/search`, `/timeline` |

**Data migration:** Copy handoffs to new location. Map project name -> `repo_id`.

**Chain state migration:** Before copying chain state files, classify each:
- **Valid fresh** (age < 24h, target snapshot exists): Migrate to new `chain/` directory
- **Stale** (age > 24h): Skip — TTL would have pruned these
- **Dangling** (target snapshot missing): Skip — archive-failure poisoning
- **Corrupt** (unparseable): Skip and log

Only migrate valid fresh state. Do not reimport defects from the old system. See [chain integrity principle](foundations.md#chain-integrity-at-migration-boundaries).

**Migration manifest:** The migration script writes `migration_report.json` to `~/.claude/engram/<repo_id>/`:

```json
{
    "schema_version": "1.0",
    "migrated_at": "<ISO 8601>",
    "source_root": "~/.claude/handoffs/<project>/",
    "target_root": "~/.claude/engram/<repo_id>/snapshots/",
    "results": {
        "copied": ["file1.md", "file2.md"],
        "skipped_exists": ["file3.md"],
        "skipped_corrupt": ["file4.md"],
        "skipped_unreadable": ["file5.md"],
        "needs_manual_mapping": ["ambiguous-project/"],
        "conflicts": [{"file": "file6.md", "reason": "content mismatch at destination"}]
    }
}
```

**Fail-closed, non-interactive:**
- Ambiguous project name -> `repo_id` mappings: skip, record as `needs_manual_mapping`
- Unreadable source files: skip, record as `skipped_unreadable`
- Existing destination with non-matching content: skip, record as `conflicts`
- Successful copy: verify destination parses through Context reader before recording as `copied`

The manifest is an [operational aid](foundations.md#auxiliary-state-authority). Re-running the migration is idempotent.

**Migration idempotency:** Run the migration script twice against the same source and destination. Assert: the manifest from run 2 equals run 1 (same `copied`, `skipped_exists` lists — no new entries). This verifies the "re-running the migration is idempotent" invariant.

**Cross-step dependency:** Steps 2a and 3a depend on the old handoff format remaining readable (Context reader parses `---` frontmatter from existing handoff files). Do not modify the handoff format until Step 4a is complete.

**Exit criteria (4a):** Save/load cycle works. Worktree isolation verified. `/save` orchestration with per-step results. `/search` spans all subsystems. `/timeline` reconstructs sessions. All hooks operational. SessionStart <500ms. Chain state migration classifies and filters old state files. All copied handoffs parse successfully through the Context reader. Migration manifest written with no `skipped_corrupt` entries for newly copied files.

#### Required Verification
- Chain state migration classification (VR-4A-1): parametric fixtures for each class (valid_fresh, stale, dangling, corrupt); assert migrated count = 1
- Migration idempotency (VR-4A-2): run twice, compare manifests. New-source test: after run 1, add two new handoff files to the source directory. Run migration again. Assert: original copied files appear in `skipped_exists`; new files appear in `copied`.
- SessionStart timing (VR-4A-3): run `engram_session` against fixture with 200 snapshots (realistic 90-day max at 2/day), 20 chain files; assert **median** wall-clock < 500ms over 5 runs. Environment qualifier: local filesystem with reasonable I/O latency. If per-file cleanup exceeds 5ms, abort remaining cleanup with warning rather than blocking. Cap enforcement: 100 expired snapshots → exactly 50 deleted, 50 remain. Run again → 50 more deleted. Environment probe: before asserting <500ms, measure median per-file read latency on a 10-file fixture. If per-file latency exceeds 10ms, mark the timing assertion as skipped/environment with a warning. (SY-34)
- /triage promote-meta detection (VR-4A-4): fixture with CLAUDE.md markers + text but no promote-meta → assert mismatch reported; fixture with stale promote-meta → assert stale reported; fixture with CLAUDE.md text but markers deleted → assert manual reconcile surfaced
- Promote marker lifecycle (VR-4A-5): Branch A inserts markers + text; Branch B1 fixture with promote-meta present, `promoted_content_sha256 == current content_sha256`, `target_section` unchanged → assert rejection with 'already promoted' status and existing promotion details (no CLAUDE.md write, no promote-meta update); Branch C1 locates markers, drift_hash matches → normal replacement with user confirmation; Branch C2 locates markers, drift_hash mismatches (user edited managed block) → drift warning + 2-way diff surfaced before user confirmation; Branch C3 missing markers → manual reconcile; Branch B2 shows old and new target_section plus existing promoted text → user confirms manual placement; Step 3 records updated target_section in promote-meta
- Snapshot intent fields (VR-4A-6): /save without flags → snapshot has orchestrated_by=save, save_expected_defer=true, save_expected_distill=true; /save --no-defer → save_expected_defer=false; /quicksave → no orchestration fields. String boolean normalization: create a snapshot file with frontmatter containing `save_expected_defer: "true"` (quoted string) → `/triage` interprets as boolean `true`.
- Archive-before-state-write ordering test (VR-4A-7): simulate archive failure (mock archive operation to raise OSError mid-write). Assert: no chain state file exists at `chain/<worktree_id>-<session_id>` after the failed `/load`. Subsequent `/load` with a healthy archive produces a valid chain file.
- `engram_quality` advisory contract (VR-4A-8): (a) simulate readback failure (make snapshot file unreadable after write completes) → assert hook returns exit code 0, not exit code 2; (b) write a snapshot with a missing required frontmatter field → assert hook emits warning text, exit code 0; (c) verify no Block decisions in `engram_quality` output path.
- Triage inference matrix (VR-4A-9): fixture with expected_defer=true + ticket exists → satisfied; expected_defer=false + no ticket → skipped; expected_defer=true + no ticket + defer_completed(emitted_count=0) → zero-output success; expected_defer=true + no ticket + no completion event → completion-not-proven
- Triage ledger-off inference (VR-4A-10): same fixture as VR-4A-9 but with `ledger.enabled=false`. Assert: cases (3) and (4) both report "completion not proven (ledger unavailable)" — no zero-output-success distinction. Assert: qualifier `reason=ledger_disabled` present on all collapsed cases.
- Triage provenance anomaly (VR-4A-11): fixture with a ticket in `engram/work/` that has no corresponding `.audit/` entry. Assert: `/triage` reports `provenance_not_established` anomaly for that ticket. Fixture with a snapshot missing `session_id` in frontmatter. Assert: `/triage` reports `provenance_not_established` for that snapshot. Fixture with a knowledge entry in `learnings.md` lacking valid `lesson-meta` (or with `producer` not in `{learn, curate}`). Assert: `/triage` reports `provenance_not_established` for that entry.
- Context call-site completeness (VR-4A-12): Context write paths do not use `collect_trust_triple_errors()` (they use [direct-write path authorization](enforcement.md#direct-write-path-authorization)). Verify: `grep -r "collect_trust_triple_errors" scripts/context/` returns no matches — Context engine must NOT call the trust validator.
- Worktree isolation test (VR-4A-13): create two worktrees from the same repo (same `repo_id`, distinct `worktree_id`). Run `/save` in each. Assert: (a) `query(subsystems=["context"])` in worktree A returns no entries from worktree B's `snapshots/` or `chain/` directories; (b) same assertion for worktree B. Assert: both entries have identical `repo_id` but distinct `worktree_id` in `RecordMeta`.
- engram_quality catch-all exception test (VR-4A-14): monkey-patch the hook's internal validation function to raise `RuntimeError`. Assert: exit code 0, `[engram_quality:error]` log entry present. Verifies the outermost catch-all, not just specific failure paths. (SY-24)
- /timeline git integration test (VR-4A-15): (a) commit a ticket to the shared root; (b) run `/timeline` for that session; (c) assert output includes at least one entry attributed via `git log` (labeled "inferred"); (d) mock `git log` to raise CalledProcessError — assert `/timeline` returns partial result with degradation warning. (SY-27)
- Context status derivation test (VR-4A-16): (a) snapshot in `snapshots/` → `query(status="context:active")` returns it; (b) same file moved to `snapshots/.archive/` → `query(status="context:archived")` returns it, `query(status="context:active")` does not. (SY-29)
- Ledger multi-producer concurrency test (VR-4A-17): spawn 10 concurrent threads, each appending one `LedgerEntry` to the same shard. Assert: shard has exactly 10 valid JSON lines, no partial lines, lock file absent post-completion. (SY-30)
- Promote Branch D exclusion test (VR-4A-18): fixture with `promote-meta` having `meta_version: "99.0"`. Run `/promote`. Assert: lesson NOT in selectable candidate list. Assert: warning containing lesson_id and "unreadable promote-meta" surfaced. (SY-32)

### Step 4b — Retire

- Remove `packages/plugins/handoff/` package
- Remove deployed handoff plugin from `~/.claude/plugins/` (use `trash`)
- Remove deployed handoff skills from `~/.claude/skills/{save,load,quicksave,search,defer,triage}/` (use `trash`)

**Exit criteria (4b):** No old handoff code present in repo or deployed locations.

## Step 5: Cleanup

- Remove bridge adapter and SourceResolver from Step 1 (temporary scaffolding must not survive as permanent code)
- Remove old marketplace entries for retired plugins
- Clean old data locations (`docs/tickets/`, `docs/learnings/`)
- Update CLAUDE.md, references, and documentation
- Verify no stale references to old plugin paths in skills, hooks, or agents

## Testing Strategy

### Compatibility Harness (Step 3)

Feed identical fixtures into old ticket engine and new Engram Work engine. Compare:
- Response envelope (state, message, error_code)
- On-disk ticket output
- Audit side effects
- Hook allow/deny behavior
- Dedup/TOCTOU/trust outcomes

**Audit side-effect assertions:** The harness must verify `.audit/` JSONL entries for each fixture that creates or updates a ticket. Each entry must contain: `timestamp` (ISO 8601), `operation` (create|update|close), `ticket_ref` (RecordRef serialization), `source_ref` (if applicable), `trust_triple_present` (bool). Assert: entry exists for each write operation, fields are non-empty, `trust_triple_present` matches expectation.

**Idempotency assertion:** Submit a `DeferEnvelope` with idempotency_key K. Assert ticket_ref R created. Submit identical envelope again. Assert: same R returned, no new ticket file created, no new `.audit/` entry. Repeat for `DistillEnvelope` against the staging inbox: submit twice, assert same staged file (not duplicated).

### Test Buckets

Triage old tests into three buckets:

| Bucket | Treatment |
|---|---|
| Compatibility-critical (~100-150) | Must pass harness. Behavioral equivalence gates migration. |
| Fixture/golden (~200-250) | Port fixtures, write fresh assertions. |
| Implementation-local (~200-300) | Don't port. Write what's needed for new engine. |

### Cross-Cutting Verification

| Invariant | Test | Step |
|---|---|---|
| /search grouping ("never interleaved") | Multi-subsystem query, assert contiguous grouping: for each adjacent pair `(entries[i], entries[i+1])` where subsystems differ, assert `entries[i+1].ref.subsystem` does not appear in `entries[0..i-1]` | 4a |
| All 13 skills functional | Automated smoke test per skill: one happy-path invocation, assert expected observable output. **Progressive:** at each step, all skills activated by or before that step must pass their smoke test. A shared smoke-test runner is invoked at each step's exit gate, parameterized by the set of activated skills. | Progressive (not Step 5 only) |
| /save shared-entrypoint delegation | (1) Spy test: mock the shared entrypoint, invoke `/save`, assert mock called exactly once for defer and once for distill with the same arguments as the standalone call. "Same entrypoint" = identical Python function object (by module + qualified name). A wrapper or reimplementation that delegates to a private helper does not satisfy this test. (2) Parity test: run `/save` and standalone `/defer` with fixture snapshot, assert identical `IndexEntry` output (same fields, same RecordRef). (3) Partial-failure parity: `/save` with distill engine disabled → same defer output as standalone `/defer`. | 4a |

**Minimal observable output per skill (SY-28):**

| Skill | Minimal Assertion |
|-------|-------------------|
| `engram init` | `.engram-id` created, valid UUIDv4 content, exit code 0 |
| `/save` | Per-step results dict present, `snapshot` field non-empty |
| `/quicksave` | Checkpoint file created, frontmatter parseable |
| `/load` | Snapshot content displayed, chain state updated |
| `/defer` | Ticket created, `RecordRef` returned |
| `/distill` | ≥1 staging file created |
| `/curate` | Published entry in `learnings.md` |
| `/learn` | Published entry in `learnings.md` with `lesson-meta` |
| `/promote` | Markers in CLAUDE.md, `promote-meta` in `learnings.md` |
| `/search` | ≥1 result returned, subsystem label present |
| `/timeline` | ≥1 entry returned, label present |
| `/ticket` | Ticket file created in `engram/work/` |
| `/triage` | Report rendered, no unhandled exceptions |

### Invariants

- All migration scripts are idempotent. Running twice produces the same result.
- Rollback: each step is a branch. Revert the branch if a step fails.

**Shared root (git-tracked):** Branch revert fully restores the pre-step state. The activate/retire split ensures old code is still in the repo during validation (substep a) and only removed after validation passes (substep b).

**Private root (`~/.claude/engram/`):** Migration steps that write to the private root (Steps 2a, 4a) are forward-only and additive — they copy data but never delete originals. Branch revert does not undo private-root writes. Orphaned private-root data after a branch revert is expected and safe — [SessionStart](enforcement.md#sessionstart-hook) cleanup handles TTL expiration, and re-running the migration step is idempotent. Deletion of original private-root data occurs only in Step 5, after all validation passes.

## Success Criteria

| Criterion | Measurement |
|---|---|
| All 13 skills functional | Manual walkthrough of each primary flow (including `engram init`) |
| Cross-subsystem query works | `/search` returns from all three subsystems |
| Session timeline reconstructs | `/timeline` with ledger-backed/inferred labels |
| Defer -> ticket linkage | Ticket's `source_ref` traces to originating snapshot |
| Distill -> staging -> curate pipeline | Full lifecycle works |
| Protected-path enforcement | Direct Write/Edit to `engram/work/` blocked; Bash best-effort |
| Worktree isolation | Two worktrees don't cross-contaminate Context |
| Compatibility harness passes | Work subsystem behavioral equivalence |
| Old plugins removed | No code in `packages/plugins/handoff/` or `packages/plugins/ticket/` |
| SessionStart < 500ms | Cleanup bounded and idempotent |
