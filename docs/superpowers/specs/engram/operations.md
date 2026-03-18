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
    -> Open native ticket files for subsystem-specific reasoning
    -> Cross-reference: orphaned items, stale tickets, blocked chains, failed envelopes
    -> Report pending staged knowledge candidates
    -> Return structured triage report with per-subsystem sections
```

Uses the [index](storage-and-indexing.md#indexentry) for *discovery*, opens native files for *reasoning*.

## New Operations (Engram-Only)

### Promote: Knowledge to CLAUDE.md

Three-step state machine with reconciliation-based recovery. CLAUDE.md is an external sink, not an Engram-managed record. The Knowledge engine owns the promotion *state*. The CLAUDE.md edit is a skill-level operation — a [documented exception](foundations.md#permitted-exceptions) to the core invariant.

```
/promote
    -> query(subsystems=["knowledge"], status="knowledge:published")
    -> Rank by maturity signals (age, breadth, reuse evidence) — advisory ordering only
    -> User selects
    -> Step 1 (engine): Knowledge engine validates promotability via 3-branch state machine:
        Branch A (no promote-meta): Eligible. Returns promotion plan.
        Branch B (promote-meta exists, promoted_content_sha256 == current content_sha256):
            Reject — already promoted. Return existing promotion details.
        Branch C (promote-meta exists, promoted_content_sha256 != current content_sha256):
            Stale promotion. Return reconciliation plan: old target_section,
            old transformed_text_sha256 (for locating text in CLAUDE.md), new content.
    -> Step 2 (skill): Skill writes transformed text to CLAUDE.md
        For Branch C: attempts to locate and replace old text using transformed_text_sha256
        If old text not found: surfaces manual reconcile flow to user
    -> Step 3 (engine): Knowledge engine writes/updates promote-meta with current hashes
```

**Ranking is advisory, not contractual.** Maturity signals determine display ordering only — they are not part of the storage contract. Engine promotability validation must not depend on undocumented maturity scores.

**Recovery:** Step 1 validates but does not record durable state — it returns a promotion plan. Step 3 writes [promote-meta](types.md#promote-meta-promotion-state-record) only after the CLAUDE.md write succeeds. If Step 2 fails, no promote-meta exists (Branch A) or stale promote-meta persists (Branch C), so the lesson remains eligible for future `/promote` runs. If Step 3 fails, `/triage` detects the mismatch:
- **Missing promote-meta:** CLAUDE.md has text, no promote-meta at all (Step 3 never ran)
- **Stale promote-meta:** CLAUDE.md has updated text, promote-meta has old hashes (Step 3 failed on re-promotion)

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
    -> Context engine writes snapshot -> snapshot_ref
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
| Crash after envelope write | Envelope is transient — no persistent queue. `/triage` infers missing downstream records by scanning `source_ref` fields. | User retries the operation; idempotency key prevents duplicates. |
| Crash before envelope write | No envelope exists; downstream record missing expected upstream link | `/triage` infers unlinked records by scanning native content and cross-checking `source_ref` fields |
| Promote Step 2 failure | CLAUDE.md unchanged, no promote-meta written | Lesson remains eligible for next `/promote` run |
| Promote Step 3 failure | CLAUDE.md written but promote-meta absent | `/triage` detects mismatch; surfaces for user resolution |
| Legacy artifact lacks session_id | Appears in timeline as "unattributed" | Not silently omitted |
