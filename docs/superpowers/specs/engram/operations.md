---
module: operations
status: active
normative: true
authority: operations
---

# Cross-Subsystem Operations

Six operations justify Engram's plugin scope. Three migrate and improve existing cross-plugin behaviors (Defer and Distill write flows; Triage query behavior); three are new Engram-only capabilities. All cross-subsystem writes use [typed envelope contracts](types.md#envelope-types) with idempotent retry semantics.

## Core Rules

- Target subsystem engine validates and writes. Envelopes are requests, not commands. Work and Knowledge engine invocations go through [`engram_guard`](enforcement.md#trust-injection) for trust injection before any mutating operation. Context subsystem writes use Write/Edit tools natively and are [excluded from trust triple validation](enforcement.md#step-2-validation-engine-entrypoint).
- **Precondition:** All mutating Work and Knowledge engine entrypoints require trust triple validation before making state changes. Operations with missing or incomplete triples are rejected. The enforcement mandate (which validator to call, check ordering, per-entrypoint origin matching) is specified in [enforcement.md §Trust Injection](enforcement.md#trust-injection) — the authoritative source for `enforcement_mechanism` claims.
- Every envelope carries a `source_ref: RecordRef` pinned at creation time. Downstream operations target this ref, never "latest file at path."
- Every envelope carries an `idempotency_key`. Target engines deduplicate retried operations.
- `/save` orchestrates cross-subsystem flows but each sub-operation is independently callable and retryable. See [/save orchestration rules](skill-surface.md#save-orchestration-rules).
- No reactive pipelines. No cross-subsystem transactions.

### Work Mode Definitions

The Work subsystem operates in one of two modes, configured via `work_mode` in [`.claude/engram.local.md`](enforcement.md#configuration):

- **`suggest`:** Engine prepares the operation but surfaces it to the user for confirmation before writing. The user sees what will be created and approves or rejects. If the user abandons the session without confirming, the proposed operation is discarded — no write is performed. The `suggest` flow is entirely in-session; there is no queued state to persist. Trust injection applies — `engram_guard` validates the trust triple on the engine invocation regardless of mode. In suggest mode, abandonment prevents the target artifact write; the guard/engine plumbing still performs transient private-root writes.
- **`auto_audit`:** Engine creates the work item automatically. The item is marked for user review at next `/triage`. `work_max_creates` limits cumulative automatic creations per session. Trust injection still applies — `engram_guard` validates the trust triple regardless of mode. Cap enforcement (`work_max_creates`) is the engine's responsibility, not the guard's — `engram_guard` is mode-agnostic.

**Context subsystem autonomy:** No autonomy gate. Agents save their own session state — snapshots and checkpoints are agent-authored artifacts, not user-reviewed outputs.

**gated:** Staged Knowledge candidates require explicit user review via `/curate` before publication to `learnings.md`. The staging write itself (`/distill`) is automatic — no user confirmation is required to write staging-meta. The gate is at publication, not at staging. `gated` mode is independent of Work modes (`suggest`, `auto_audit`).

**Knowledge staging autonomy:** `/distill` auto-stages candidates without user confirmation; `/learn` publishes directly via the Knowledge engine. Staged candidates require user review via `/curate` before publication. Staging inbox cap (`knowledge_max_stages`) and content-addressed idempotency bound autonomous volume. See [enforcement.md §Autonomy Model](enforcement.md#autonomy-model) for configuration schema and enforcement caps.

## Existing Operations (Migrate and Improve)

### Defer: Context to Work

```
/save (or /defer standalone)
    -> Context engine writes snapshot, returns snapshot_ref
    -> Skill extracts deferred items
    -> DeferEnvelope per item (with idempotency_key)
    -> Work engine ingests via 4-stage pipeline
    -> Duplicate check (two-stage):
        (1) Envelope-level: check idempotency_key against existing tickets
            -> If match: returns existing ticket_ref (same retry)
        (2) Content-level: check work_dedup_fingerprint(problem, key_file_paths)
            against tickets created within the past 24 hours
            -> If match: returns existing ticket_ref (semantically identical)
    -> If no match at either stage: creates ticket, returns ticket_ref
```

**Dedup scope:** The `DeferEnvelope.context` field is excluded from idempotency material because two defer operations with the same title, problem, and key_file_paths represent the same semantic intent regardless of any contextual snippet provided. See [types.md §Idempotency](types.md#idempotency--same-operation-retried) for the full material specification.

### Distill: Context to Knowledge (Staged)

```
/save (or /distill standalone)
    -> Context reader parses snapshot
    -> Distill engine extracts candidates (parse -> subsections -> classify durability -> dedup)
    -> DistillEnvelope per candidate batch (with idempotency_key)
    -> Knowledge engine writes to staging inbox (private, not repo-visible)
    -> Per-candidate dedup: content_sha256 against staged + published entries
    -> If match: skip that candidate
    -> If new: creates staged candidate (atomic via O_CREAT|O_EXCL)
```

**Distill dedup:** Per-candidate `content_sha256` dedup via atomic `O_CREAT | O_EXCL` staging file creation. Identical candidates from concurrent operations coalesce at the filesystem level. Within a single batch, candidates with identical `content_sha256` are deduplicated (only one written). The `DistillEnvelope.idempotency_key` is not persisted or checked for distill operations — see [types.md §Idempotency Enforcement Per Envelope Type](types.md#idempotency-enforcement-per-envelope-type).

**Trust boundary: staged != published.** Distill writes to a private staging area (`knowledge_staging/`), not to `engram/knowledge/`. Staged candidates are reviewed before publication via `/curate`.

**Staging inbox cap.** Cap enforcement (rejection formula, error message, edge cases) is specified in [enforcement.md §Staging Inbox Cap](enforcement.md#staging-inbox-cap) (`enforcement_mechanism` authority). The cap is cumulative (total files in directory), non-atomic (TOCTOU acceptable), and whole-batch (no partial staging). See [decisions.md §Deferred Decisions](decisions.md#deferred-decisions) for partial staging deferral.

**Edge case: `batch_size > knowledge_max_stages`.** If a single distill batch produces more candidates than the configured cap (e.g., a rich snapshot yields 15 candidates against a cap of 10), the batch is rejected even with 0 files in staging — the cap applies to `count + batch_size`, and `0 + 15 > 10`. The rejection response must include: (1) current `batch_size` and cap values, (2) the exact config change needed (`knowledge_max_stages: N` where N >= batch_size in `.claude/engram.local.md`), (3) instruction to re-run the failed distill with the `snapshot_ref` from the [recovery manifest](#recovery-manifest). This is a deliberate consequence of whole-batch rejection. Partial staging (accepting the first N candidates) is a [deferred decision](decisions.md#deferred-decisions).

**`/curate` mechanics:** Lists staged candidates sorted by `durability` (likely_durable first), then by `staged_at` (oldest first). Shows snippet, source section, and durability classification. The user reviews and selects candidates to publish. `likely_ephemeral` candidates are surfaced with a warning but not filtered — the user decides. On publish, the knowledge engine deduplicates via `content_sha256` against both existing published entries and other staged entries (to remove or skip duplicates in the staging inbox), writes to `engram/knowledge/learnings.md`, and removes the staged file (plus any other staged files with identical `content_sha256`). **`/curate` publish dedup ordering (TOCTOU invariant):** The dedup check against published entries must occur within the same lock scope as the write (after acquiring `fcntl.flock(LOCK_EX)` on `learnings.md.lock`). This ensures no concurrent `/learn` write can interleave between dedup check and append.

### Triage: Read Work and Context

```
/triage
    -> query(subsystems=["work"]) -> IndexEntries for tickets
    -> query(subsystems=["context"]) -> IndexEntries for snapshots
    -> Open native snapshot files for orchestration intent metadata
    -> For each session being evaluated, check for <session_id>.diag file.
        (`.diag` non-empty, including all-opaque entries where all entries have
        unrecognized schema_version — see enforcement.md §Session Diagnostic Channel)
        If present and non-empty: cases (3) and (4) for that session surface
            "ledger unavailable in session <session_id>" rather than
            "zero-output success" or "completion not proven". This is
            session-scoped hook-failure degradation, distinct from
            config-scoped ledger.enabled=false.
    -> Apply inference matrix for each orchestrated snapshot:
        (1) expected_X: true + downstream record exists         -> satisfied
        (2) expected_X: false + no downstream                   -> intentionally skipped
        (3) expected_X: true + no downstream + X_completed      -> zero-output success (satisfied)
            ledger event exists (emitted_count=0)
        (4) expected_X: true + no downstream + no completion    -> "completion not proven"
            event (if the completion event is present but `emitted_count` key is absent
            from the payload dict, treat as "completion not proven" — this is a
            producer bug, distinct from case where the event itself is absent)
        Cross-reference: emitted_count field defined in types.md
            §Event Vocabulary.
    -> When ledger unavailable (ledger.enabled=false — see
        storage-and-indexing.md §Degradation Model for authoritative rule):
        Cases (3) and (4) collapse: expected_X true + no downstream
            -> "completion not proven (ledger unavailable)"
        /triage surfaces reason=ledger_disabled qualifier on all
            collapsed cases. Policy: ledger.enabled=false is supported
            for storage and basic query, but unsupported for
            production-grade /triage completion inference.
    -> Cross-reference: orphaned items, stale tickets, blocked chains
    -> Report pending staged knowledge candidates
    -> Report promote-meta mismatches (missing, stale, or unreadable/Branch D)
    -> Anomaly detection (provenance_not_established):
        Work: tickets in engram/work/ with no corresponding .audit/ entry
        Context: snapshots missing session_id in frontmatter (required for
            RecordMeta population and timeline attribution)
        Knowledge: entries in learnings.md lacking valid lesson-meta, or
            with producer field not in {learn, curate}. This detects
            unauthorized Bash writes that lack valid lesson-meta or use
            invalid producer values — it does not detect adversarial Bash
            writes that forge valid lesson-meta. See decisions.md §Named
            Risks (Bash enforcement gap) for the bounded-guarantee context.
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
        Step 1 reads CLAUDE.md to perform marker search and drift detection.
        The Branch C1/C2 determination is complete before Step 2 begins.
        The engine returns the branch classification to the skill as part of the promotion plan.
        Branch A (no promote-meta): Eligible. Returns promotion plan with target_section.
            User sees proposed text and target_section, confirms before write. User confirmation
            is implicit in lesson selection — the user chose this lesson for promotion. No
            separate approval prompt.
            **Branch A invariants:** (1) `transformed_text` MUST be a faithful rendering of the selected lesson, differing only by required promotion markers — no content transformation beyond marker wrapping. (2) `target_section` is advisory; if the user later moves the promoted block to a different section, relocation is handled by Branch B2 on subsequent `/promote`.
        Branch D (promote-meta present, AND any of: meta_version unrecognized or missing, OR promote-meta.lesson_id does not match the immediately preceding lesson-meta.lesson_id):
            Exclude from candidate list. Surface warning per cause:
            - Missing/unrecognized meta_version: "Lesson <lesson_id> has
              unreadable promote-meta (missing or unrecognized meta_version). Run
              migration before re-promoting."
            - lesson_id mismatch: "Lesson <lesson_id> has corrupt promote-meta
              (lesson_id mismatch with lesson-meta). Run migration before
              re-promoting."
            The exclusion occurs before the lesson
            appears as a selectable candidate. See [legacy entries](types.md#legacy-entries-missing-meta-version).
        Branch B (promote-meta exists, promoted_content_sha256 == current content_sha256):
            B1 (target_section unchanged): Reject — already promoted. Return: `{"status": "already_promoted", "lesson_id": "<id>", "promoted_at": "<ISO8601>", "target_section": "<section>", "promoted_content_sha256": "<hex>"}`.
            B2 (target_section mismatch — promote-meta.target_section differs from
                detected marker location via global marker search): Manual reconcile.
                On re-entry after a prior B2 Step 3 failure, this mismatch is detected
                structurally (promote-meta has old target_section, markers at new location)
                without requiring an active user request.
                Show old
                target_section, new target_section, and existing promoted text (located
                via marker search if markers exist). User places block in new section
                manually. Automated relocation deferred to v1.1 (see
                [deferred decisions](decisions.md#deferred-decisions)).
                After the user confirms manual placement in the new section, the skill
                writes the promoted text wrapped in markers at the user-confirmed location.
                Step 3 then reads back the text between markers at the new location and
                computes `transformed_text_sha256` via `drift_hash()`. Step 3 also updates
                `promote-meta.target_section` to the user-confirmed section. If the skill
                cannot locate markers at the new location after user confirmation, Step 3
                rejects the promote-meta write (lesson remains eligible for next `/promote`).
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
        For Branch B2: after user confirms placement and skill wraps in markers (end of Step 2),
            the engine retrieves the text between the newly-placed markers, recomputes
            drift_hash(), and writes promote-meta with updated target_section set to the
            user-confirmed section. This occurs within the same /promote invocation — Step 3
            is not deferred to a future run.
        If post-write text is unavailable, rejects the write (lesson remains eligible).
```

**Ranking is advisory, not contractual.** Maturity signals determine display ordering only — they are not part of the storage contract. Engine promotability validation must not depend on undocumented maturity scores.

**Location strategy:** Branch C searches CLAUDE.md globally for `<!-- engram:lesson:start:<lesson_id> -->` / `<!-- engram:lesson:end:<lesson_id> -->` marker pairs. Global search (not section-scoped) supports user relocation of managed blocks — if the user moves a promoted block to a different section, the marker search still finds it. Branch B2 uses the same search for display (showing the user where the current text lives) but does not automate relocation in v1. See [marker specification](types.md#promotion-markers-in-claudemd) for validity rules.

**Branch C drift detection:** Before replacing text between markers, Step 1 computes [`drift_hash()`](types.md#hash-producing-functions) on the current text enclosed by markers and compares it against `promote-meta.transformed_text_sha256`. `drift_hash` uses NFC + LF normalization only (stricter than `content_hash`) so that user formatting edits to promoted blocks count as drift. This activates the `transformed_text_sha256` field as a drift sentinel — see [types.md rationale table](types.md#hash-producing-functions) for why `drift_hash` is intentionally stricter than `content_hash`.

**Recovery:** Step 1 validates but does not record durable state — it returns a promotion plan. Step 3 writes [promote-meta](types.md#promote-meta--promotion-state-record) only after the CLAUDE.md write succeeds. If Step 2 fails, no promote-meta exists (Branch A) or stale promote-meta persists (Branch C), so the lesson remains eligible for future `/promote` runs. If Step 3 fails, `/triage` detects the mismatch:
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
    -> Merge and sort chronologically (ledger ts strings parsed to
        datetime.timezone.utc before sort; malformed ts → place at epoch
        with per-entry warning, not dropped)
    -> Events labeled as "ledger-backed" or "inferred"
    -> Causal links resolved by scanning target records' source_ref fields (O(n), scoped by session_id)
    -> Legacy artifacts lacking session_id appear under "unattributed" group
```

## Envelope Invariants

- Target engine validates and writes (envelope is a request, not a command)
- Target engine can reject any envelope (duplicate, version mismatch, validation failure)
- Unknown `envelope_version` produces explicit `VERSION_UNSUPPORTED` error with expected version (singular — exact-match, no forward compatibility)
- Idempotent: same `idempotency_key` produces same result, no side effects on retry

**Phase-scoped idempotency (migration):** During the bridge period, envelope-level idempotency keys are not checked — the old ticket engine's legacy dedup is the active mechanism. See [delivery.md §Bridge Cutover](delivery.md#step-1-bridge-cutover) for the authoritative bridge-period specification (`implementation_plan` authority).

## /save as Session Orchestrator

`/save` must invoke the same public entrypoint function as `/defer` and `/distill` respectively — it is a thin orchestrator, not a reimplementation.

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

### Snapshot Event Emission

Each snapshot producer emits a [`snapshot_written`](types.md#event-vocabulary-v1) ledger event after successful write:

| Producer | `orchestrated_by` value | When |
|----------|------------------------|------|
| `/save` | `"save"` | After snapshot write succeeds (before defer/distill sub-operations) |
| `/quicksave` | `"quicksave"` | After snapshot write succeeds |
| `/load` (archive path) | `"load"` | After archive write succeeds |

All three producers emit the event. The `orchestrated_by` value distinguishes them in `/timeline` and `/triage`. See [types.md §Event Vocabulary](types.md#event-vocabulary-v1) for the authoritative `snapshot_written` schema and emission rules (`interface_contract` authority).

Skills that write via the Write tool (not engine Bash) emit ledger events by calling `engram_core.ledger.append_event()` after the Write tool call succeeds. This is an orchestrator-produced event, not a new mutating entrypoint. Failure to append does not invalidate the write — emit a warning in `QueryDiagnostics.warnings`.

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

The manifest is an [operational aid](foundations.md#auxiliary-state-authority), not authoritative state. Primary records remain authoritative. Overwritten on each `/save` invocation (only the most recent is useful for retry). Not part of the Engram storage contract. The `save_recovery.json` schema does not include a `schema_version` field — recovery manifests are ephemeral operational aids, not versioned contracts. The file is overwritten on every `/save`, so no cross-version reader tolerance is needed. (Note: `migration_report.json` includes `schema_version: "1.0"` despite also being an operational aid — it may outlive its creating step and be read by downstream validation tools, unlike `save_recovery.json` which is consumed immediately on retry.)

The `idempotency_key` in `EnvelopeHeader` is computed by the caller at envelope construction time (see [types.md §Idempotency](types.md#idempotency--same-operation-retried)). The engine uses the provided key — it does not recompute from fields.

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
| Promote Step 3 failure (Branch A/C) | CLAUDE.md written but promote-meta absent or stale | `/triage` detects mismatch; next `/promote` re-enters the same branch. Lesson remains eligible. |
| Promote Step 3 failure (Branch B2) | CLAUDE.md has new markers + text at user-confirmed section, but promote-meta has old `target_section` | `/triage` detects `target_section` mismatch (markers at new section, promote-meta at old). Next `/promote` re-enters Branch B2 if promote-meta `target_section` differs from marker location. |
| Legacy artifact lacks session_id | Appears in timeline as "unattributed" | Not silently omitted |
| Plugin co-deployment violation | Promote script aborts with diagnostic | Verify both `hooks/` and `scripts/` exist before retrying promote |
