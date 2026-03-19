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
Step 2: Knowledge cutover
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
- `VERSION_UNSUPPORTED` error for unknown `envelope_version` (VR-7): submit envelope with `envelope_version="99.0"`, assert error code and expected version range
- Normalization boundary test (VR-14): construct a string where `knowledge_normalize` and `drift_hash`-level normalization (NFC+LF only) produce different outputs (e.g., trailing whitespace). Assert `content_hash(input) != drift_hash(input)`. Separately, assert `content_hash(input) != work_dedup_fingerprint(input, [])` for a mixed-case input. This proves the three pipelines diverge — using the wrong one would produce a different hash.
- Field preservation gate (T1-gate-1, activates at Step 2a): verify that rewriting a `lesson-meta` entry with an unknown field preserves that field verbatim. Deferred from Step 0a because field preservation is only exercised when the Knowledge engine performs its first rewrite-capable operation. Scheduled here for traceability; test fixture created in Step 2a.
- Mixed-version degradation gate (T1-gate-2, activates at Step 2a): verify that a `lesson-meta` entry with `meta_version: "99.0"` is skipped per-entry (not per-file) with a warning in `QueryDiagnostics.warnings`. Deferred from Step 0a for the same reason. Scheduled here; test fixture created in Step 2a.

## Step 0b: Bootstrap and Identity

Create identity resolution and bootstrap command. Depends on 0a types being stable.

| Deliverable | Detail |
|---|---|
| `engram_core/identity.py` | `repo_id` generation/resolution, `worktree_id` derivation. See [identity resolution](types.md#identity-resolution). |
| `engram init` command | Generates `.engram-id` (UUIDv4), writes to repo root, stages for commit |
| `.engram-id` | Generated and committed (for this repo) |

**Exit criteria:** Identity works across worktrees. `engram init` is idempotent. [SessionStart](enforcement.md#sessionstart-hook) warns when `.engram-id` missing and points to `engram init`.

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
- Bridge test additionally verifies old engine accepts converted JSON (VR-9): call old ticket engine ingest with bridge output, assert non-error response

## Step 2: Knowledge Cutover

### Step 2a — Activate

| Deliverable | Detail |
|---|---|
| `engram/knowledge/learnings.md` | `git mv docs/learnings/learnings.md` |
| Knowledge reader, engine | Staging writes, dedup, publication, [promote-meta](types.md#promote-meta-promotion-state-record) |
| Staging inbox | `~/.claude/engram/<repo_id>/knowledge_staging/` |
| `/learn`, `/distill`, `/curate`, `/promote` | All knowledge skills |

**Exit criteria (2a):** Full learn -> distill -> curate -> promote lifecycle. Staging dedup. [Staging inbox cap](enforcement.md#staging-inbox-cap).

#### Required Verification
- Promote-path wiring check (VR-15): `PromoteMeta.transformed_text_sha256` must be produced by `drift_hash()`, not `content_hash()`. Construct promoted text with trailing whitespace. Assert `drift_hash(text)` detects the whitespace (different hash from stripped version) while `content_hash(text)` does not (same hash). This verifies the promote pipeline uses the correct — stricter — normalizer for drift detection.
- Promote hash recomputation (VR-16): simulate the Approve/modify/skip flow where the user modifies transformed text during Step 2 confirmation. Assert: `PromoteMeta.transformed_text_sha256` matches `drift_hash()` of the *post-modification* text written to CLAUDE.md, not the original `PromoteEnvelope.transformed_text`. Separately, assert: if post-write text retrieval fails, Step 3 rejects the promote-meta write (lesson remains eligible for next `/promote`). See [Promote Hash Verification](types.md#promote-hash-verification).
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
| `engram_guard` hook | [Protected-path enforcement](enforcement.md#protected-path-enforcement) + [trust injection](enforcement.md#trust-injection) |
| `/ticket`, `/triage` | Work skills |
| Config | `.claude/engram.local.md` (see [autonomy configuration](enforcement.md#configuration)) |
| Bridge adapter update | `/defer` switches from bridge adapter (Step 1) to new Work engine |

**Exit criteria (3a):** All ticket operations work. Protected-path enforcement: Write/Edit to protected paths blocked reliably (verified by direct tool call attempts). Bash enforcement: representative shell write patterns tested, documented as [bounded guarantee](enforcement.md#enforcement-scope-bounded-guarantee). Trust triple works. Compatibility harness passes. `/defer` routes through new Work engine.

#### Required Verification
- Envelope idempotency (SY-5): DeferEnvelope submitted twice returns same ref
- Phase-scoped idempotency regression gate (VR-11): verify idempotency_key is checked by new Work engine after bridge replacement
- Staging inbox cap (VR-8): cap=5, count=3, batch=3 → full rejection; cap=5, count=3, batch=2 → success
- Staging cap edge case (VR-17): cap=5, count=0, batch=8 → full rejection with diagnostic message including both batch size and cap values. Assert error message contains "Batch size (8) exceeds staging cap (5)".

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
- Chain state migration classification (VR-5): parametric fixtures for each class (valid_fresh, stale, dangling, corrupt); assert migrated count = 1
- Migration idempotency (SY-6): run twice, compare manifests
- SessionStart timing (VR-4): run `engram_session` against fixture with 50 snapshots, 20 chain files; assert wall-clock < 500ms
- /triage promote-meta detection (VR-6): fixture with CLAUDE.md markers + text but no promote-meta → assert mismatch reported; fixture with stale promote-meta → assert stale reported; fixture with CLAUDE.md text but markers deleted → assert manual reconcile surfaced
- Promote marker lifecycle (VR-10): Branch A inserts markers + text; Branch C1 locates markers, drift_hash matches → normal replacement with user confirmation; Branch C2 locates markers, drift_hash mismatches (user edited managed block) → drift warning + 2-way diff surfaced before user confirmation; Branch C3 missing markers → manual reconcile; Branch B2 shows old and new target_section plus existing promoted text → user confirms manual placement; Step 3 records updated target_section in promote-meta
- Snapshot intent fields (VR-12): /save without flags → snapshot has orchestrated_by=save, save_expected_defer=true, save_expected_distill=true; /save --no-defer → save_expected_defer=false; /quicksave → no orchestration fields
- Triage inference matrix (VR-13): fixture with expected_defer=true + ticket exists → satisfied; expected_defer=false + no ticket → skipped; expected_defer=true + no ticket + defer_completed(emitted_count=0) → zero-output success; expected_defer=true + no ticket + no completion event → completion-not-proven
- Triage ledger-off inference (VR-18): same fixture as VR-13 but with `ledger.enabled=false`. Assert: cases (3) and (4) both report "completion not proven (ledger unavailable)" — no zero-output-success distinction. Assert: qualifier `reason=ledger_disabled` present on all collapsed cases.
- Triage provenance anomaly (VR-19): fixture with a ticket in `engram/work/` that has no corresponding `.audit/` entry. Assert: `/triage` reports `provenance_not_established` anomaly for that ticket. Fixture with a snapshot missing `session_id` in frontmatter. Assert: `/triage` reports `provenance_not_established` for that snapshot.

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
| /search grouping ("never interleaved") | Multi-subsystem query, assert contiguous grouping | 4a |
| All 13 skills functional | Automated smoke test per skill: one happy-path invocation, assert expected observable output | 5 |
| /save shared-entrypoint delegation | Delegation test: `/save` defer sub-operation calls the same public entrypoint as standalone `/defer`; `/save` distill sub-operation calls the same public entrypoint as standalone `/distill`. Parity test: run both paths with identical input, assert identical output. Code review as backstop. | 4a |

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
