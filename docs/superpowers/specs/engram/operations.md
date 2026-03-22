---
module: operations
status: active
normative: true
authority: operations
---

# Cross-Subsystem Operations

Six operations justify Engram's plugin scope. Three exist today as cross-plugin calls; three are new capabilities. All cross-subsystem writes use [typed envelope contracts](types.md#envelope-types) with idempotent retry semantics.

## Core Rules

- Target subsystem engine validates and writes. Envelopes are requests, not commands. Engine invocations go through [`engram_guard`](enforcement.md#trust-injection) for trust injection before any mutating operation.
- **Precondition:** Every mutating engine entrypoint must validate the trust triple via `collect_trust_triple_errors()` before making state changes. Operations with missing or incomplete triples are rejected. See [trust injection](enforcement.md#trust-injection).
- Every envelope carries a `source_ref: RecordRef` pinned at creation time. Downstream operations target this ref, never "latest file at path."
- Every envelope carries an `idempotency_key`. Target engines deduplicate retried operations.
- `/save` orchestrates cross-subsystem flows but each sub-operation is independently callable and retryable. See [/save orchestration rules](skill-surface.md#save-orchestration-rules).
- No reactive pipelines. No cross-subsystem transactions.

## Existing Operations (Migrate and Improve)

### Defer: Context to Work

```
/save (or /defer standalone)
    -> Context engine writes snapshot, returns snapshot_ref
    -> Skill extracts deferred items
    -> DeferEnvelope per item (with idempotency_key)
    -> Work engine ingests via 4-stage pipeline
    -> Duplicate check: idempotency_key against existing tickets
    -> If duplicate: returns existing ticket_ref (no new ticket)
    -> If new: creates ticket, returns ticket_ref
```

### Distill: Context to Knowledge (Staged)

```
/save (or /distill standalone)
    -> Context reader parses snapshot
    -> Distill engine extracts candidates (parse -> subsections -> classify durability -> dedup)
    -> DistillEnvelope per candidate batch (with idempotency_key)
    -> Knowledge engine writes to staging inbox (private, not repo-visible)
    -> Duplicate check: idempotency_key against staged + published entries
    -> If duplicate: skip
    -> If new: creates staged candidate
```

**Distill dedup sequence:** (1) Envelope-level: check `idempotency_key` against existing staged/published envelopes. If match, return existing result. (2) Per-candidate: check each `DistillCandidate.content_sha256` against existing staged/published files. If match, skip that candidate. Within a single batch, candidates with identical `content_sha256` are deduplicated (only one written).

**Trust boundary: staged != published.** Distill writes to a private staging area (`knowledge_staging/`), not to `engram/knowledge/`. Staged candidates are reviewed before publication via `/curate`.

**`/curate` mechanics:** Lists staged candidates sorted by `durability` (likely_durable first), then by `created_at`. Shows snippet, source section, and durability classification. The user reviews and selects candidates to publish. `likely_ephemeral` candidates are surfaced with a warning but not filtered — the user decides. On publish, the knowledge engine deduplicates via `content_sha256` against existing published entries, writes to `engram/knowledge/learnings.md`, and removes the staged file.

### Triage: Read Work and Context

```
/triage
    -> query(subsystems=["work"]) -> IndexEntries for tickets
    -> query(subsystems=["context"]) -> IndexEntries for snapshots
    -> Open native snapshot files for orchestration intent metadata
    -> Apply inference matrix for each orchestrated snapshot:
        (1) expected_X: true + downstream record exists         -> satisfied
        (2) expected_X: false + no downstream                   -> intentionally skipped
        (3) expected_X: true + no downstream + X_completed      -> zero-output success (satisfied)
            ledger event exists (emitted_count=0)
        (4) expected_X: true + no downstream + no completion    -> "completion not proven"
            event
    -> When ledger unavailable (ledger.enabled=false):
        Cases (3) and (4) collapse: expected_X true + no downstream
            -> "completion not proven (ledger unavailable)"
        /triage surfaces reason=ledger_disabled qualifier on all
            collapsed cases. Policy: ledger.enabled=false is supported
            for storage and basic query, but unsupported for
            production-grade /triage completion inference.
    -> Cross-reference: orphaned items, stale tickets, blocked chains
    -> Report pending staged knowledge candidates
    -> Report promote-meta mismatches (missing or stale)
    -> Anomaly detection (provenance_not_established):
        Work: tickets in engram/work/ with no corresponding .audit/ entry
        Context: snapshots missing session_id in frontmatter (required for
            RecordMeta population and timeline attribution)
        Knowledge: entries in learnings.md lacking valid lesson-meta, or
            with producer field not in {learn, curate}. This detects
            unauthorized Bash writes that bypass engram_guard trust injection.
        Note: trust triples are transient (hook-to-engine input, not persisted
            in RecordMeta), so generic trust-triple detection is not possible.
            Detection is subsystem-specific using native artifacts.
    -> Return structured triage report with per-subsystem sections
```

Uses the [index](storage-and-indexing.md#indexentry) for *discovery*, opens native files for *reasoning*.

## New Operations (Engram-Only)

### Promote: Knowledge to CLAUDE.md

Three-step state machine with marker-based location and reconciliation recovery. CLAUDE.md is an external sink, not an Engram-managed record. The Knowledge engine owns the promotion *state*. The CLAUDE.md edit is a skill-level operation — a [documented exception](foundations.md#permitted-exceptions) to the core invariant.

```
/promote
    -> query(subsystems=["knowledge"], status="knowledge:published")
    -> Rank by maturity signals (age, breadth, reuse evidence) — advisory ordering only
    -> User selects
    -> Step 1 (engine): Knowledge engine validates promotability via state machine:
        Branch A (no promote-meta): Eligible. Returns promotion plan with target_section.
        Branch D (promote-meta present, meta_version unrecognized or missing):
            Exclude from candidate list. Surface warning: "Lesson <lesson_id> has
            unreadable promote-meta (missing or unrecognized meta_version). Run
            migration before re-promoting." The exclusion occurs before the lesson
            appears as a selectable candidate. See [legacy entries](types.md#legacy-entries-missing-meta_version).
        Branch B (promote-meta exists, promoted_content_sha256 == current content_sha256):
            B1 (target_section unchanged): Reject — already promoted. Return existing details.
            B2 (target_section changed by user request): Manual reconcile. Show old
                target_section, new target_section, and existing promoted text (located
                via marker search if markers exist). User places block in new section
                manually. Automated relocation deferred to v1.1 (see
                [deferred decisions](decisions.md#deferred-decisions)).
        Branch C (promote-meta exists, promoted_content_sha256 != current content_sha256):
            Stale promotion. Search CLAUDE.md globally for markers with lesson_id.
            C1 (markers found, no drift): drift_hash(current_enclosed_text) ==
                promote-meta.transformed_text_sha256. Normal in-place replacement.
                Show proposed replacement with Approve/modify/skip confirmation.
            C2 (markers found, drift detected): drift_hash(current_enclosed_text) !=
                promote-meta.transformed_text_sha256. User edited the managed block.
                Show drift warning + 2-way diff (current managed block vs new transformed
                text) within same Approve/modify/skip UI.
            C3 (markers missing/invalid): manual reconcile flow (show old target_section,
                old content hash, new content — user places manually).
    -> Step 2 (skill): Skill writes transformed text to CLAUDE.md wrapped in markers
        For Branch A: insert at target_section with paired markers
        For Branch B2: manual reconcile — user confirms new placement, skill wraps in markers
        For Branch C1: replace text between existing markers (user approved)
        For Branch C2: replace text between existing markers (user approved after seeing diff)
        For Branch C3: manual reconcile — user confirms placement, skill wraps in markers
    -> Step 3 (engine): Knowledge engine recomputes transformed_text_sha256 via
        drift_hash() on the exact post-write text between markers (see
        [Promote Hash Verification](types.md#promote-hash-verification)), then writes/updates promote-meta.
        For Branch B2: also updates promote-meta.target_section to the user-confirmed section.
        If post-write text is unavailable, rejects the write (lesson remains eligible).
```

**Ranking is advisory, not contractual.** Maturity signals determine display ordering only — they are not part of the storage contract. Engine promotability validation must not depend on undocumented maturity scores.

**Location strategy:** Branch C searches CLAUDE.md globally for `<!-- engram:lesson:start:<lesson_id> -->` / `<!-- engram:lesson:end:<lesson_id> -->` marker pairs. Global search (not section-scoped) supports user relocation of managed blocks — if the user moves a promoted block to a different section, the marker search still finds it. Branch B2 uses the same search for display (showing the user where the current text lives) but does not automate relocation in v1. See [marker specification](types.md#promotion-markers-in-claudemd) for validity rules.

**Branch C drift detection:** Before replacing text between markers, Step 1 computes [`drift_hash()`](types.md#hash-producing-functions) on the current text enclosed by markers and compares it against `promote-meta.transformed_text_sha256`. `drift_hash` uses NFC + LF normalization only (stricter than `content_hash`) so that user formatting edits to promoted blocks count as drift. This activates the `transformed_text_sha256` field as a drift sentinel — see [types.md rationale table](types.md#hash-producing-functions) for why `drift_hash` is intentionally stricter than `content_hash`.

**Recovery:** Step 1 validates but does not record durable state — it returns a promotion plan. Step 3 writes [promote-meta](types.md#promote-meta-promotion-state-record) only after the CLAUDE.md write succeeds. If Step 2 fails, no promote-meta exists (Branch A) or stale promote-meta persists (Branch C), so the lesson remains eligible for future `/promote` runs. If Step 3 fails, `/triage` detects the mismatch:
- **Missing promote-meta:** CLAUDE.md has markers + text, no promote-meta at all (Step 3 never ran)
- **Stale promote-meta:** CLAUDE.md has updated text between markers, promote-meta has old hashes (Step 3 failed on re-promotion)

### Unified Search

```
/search "auth middleware"
    -> query(text="auth middleware") across all subsystems
    -> QueryResult with entries grouped by subsystem (never interleaved)
    -> User selects entry -> open native file
```

### Session Timeline

```
/timeline [session_id]
    -> query(session_id=<id>) -> all IndexEntries from that session
    -> git log --since=<session_start> for shared-root changes
    -> Merge and sort chronologically
    -> Events labeled as "ledger-backed" or "inferred"
    -> Causal links resolved by scanning target records' source_ref fields (O(n), scoped by session_id)
    -> Legacy artifacts lacking session_id appear under "unattributed" group
```

## Envelope Invariants

- Target engine validates and writes (envelope is a request, not a command)
- Target engine can reject any envelope (duplicate, version mismatch, validation failure)
- Unknown `envelope_version` produces explicit `VERSION_UNSUPPORTED` error with expected range
- Idempotent: same `idempotency_key` produces same result, no side effects on retry

**Phase-scoped idempotency (migration):** During the bridge period ([Step 1](delivery.md#step-1-bridge-cutover) through [Step 3](delivery.md#step-3-work-cutover)), the old ticket engine's legacy dedup is the active mechanism — envelope-level idempotency keys are not checked. Full envelope idempotency activates when the new Work engine replaces the bridge. This limitation is delivery-owned; see [bridge cutover](delivery.md#step-1-bridge-cutover) for migration-period semantics.

## /save as Session Orchestrator

```
/save [title] [--no-defer] [--no-distill]
    -> Context engine writes snapshot with orchestration intent fields:
        orchestrated_by: save
        save_expected_defer: true/false (based on --no-defer flag)
        save_expected_distill: true/false (based on --no-distill flag)
    -> snapshot_ref returned
    -> If not --no-defer: defer sub-operation
    -> If not --no-distill: distill sub-operation
    -> Return per-step results:
        {
            snapshot: {status: "ok", ref: snapshot_ref},
            defer: {status: "ok", created: 2, skipped: 1} | {status: "skipped"},
            distill: {status: "ok", staged: 3, skipped: 0} | {status: "skipped"},
        }
```

### Recovery Manifest

On completion (success or partial failure), `/save` writes `save_recovery.json` to `~/.claude/engram/<repo_id>/`:

```json
{
    "snapshot_ref": "<RecordRef canonical serialization>",
    "emitted_at": "<ISO 8601>",
    "results": {
        "snapshot": {"status": "ok", "ref": "..."},
        "defer": {"status": "error", "error": "..."},
        "distill": {"status": "ok", "staged": 3}
    }
}
```

The manifest is an [operational aid](foundations.md#auxiliary-state-authority), not authoritative state. Primary records remain authoritative. Overwritten on each `/save` invocation (only the most recent is useful for retry). Not part of the Engram storage contract.

**Retry path:** On partial failure, retry the failed sub-operation standalone with the `snapshot_ref` from the manifest:

```
/defer --snapshot-ref <ref_from_manifest>
/distill --snapshot-ref <ref_from_manifest>
```

## Failure Handling

| Failure | Behavior | Recovery |
|---|---|---|
| Envelope version mismatch | `VERSION_UNSUPPORTED` error | User upgrades Engram |
| Target engine rejects envelope | Specific error (duplicate, validation) | User fixes and retries |
| Idempotent duplicate detected | Returns existing ref, no side effects | Automatic (transparent) |
| `/save` partial success | Per-step results show which failed. Recovery manifest written. | Retry failed steps standalone with `--snapshot-ref` from manifest. |
| Crash after envelope write | Envelope emitted but downstream record not created. `defer_completed` ledger event may exist. | `/triage` infers from `source_ref` scan + ledger events. User retries; idempotency key prevents duplicates. |
| Crash before envelope write | Snapshot has `save_expected_defer: true` but no downstream record and no `defer_completed` ledger event | `/triage` reports "completion not proven" for expected sub-operations. User retries via standalone `/defer --snapshot-ref`. |
| Promote Step 2 failure (Branch A/B2/C1/C2/C3) | CLAUDE.md unchanged, no promote-meta written (or stale promote-meta persists for re-promotion branches) | Lesson remains eligible for next `/promote` run |
| Promote Step 2 user declines (C2 drift) | User sees diff of their edits vs new text, chooses "skip" | Lesson remains eligible; user edits preserved in CLAUDE.md |
| Promote Step 2 B2 manual reconcile | User shown old and new target_section; existing promoted text shown if markers locatable | User places block in new section; Step 3 records result |
| Promote Step 2 manual reconcile (C3 — markers missing) | User shown old target_section, content diff | User places text manually; Step 3 records result |
| Promote Step 3 failure | CLAUDE.md written but promote-meta absent | `/triage` detects mismatch; surfaces for user resolution |
| Legacy artifact lacks session_id | Appears in timeline as "unattributed" | Not silently omitted |
