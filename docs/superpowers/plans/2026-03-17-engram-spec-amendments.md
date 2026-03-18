# Engram Spec Amendments Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Amend the Engram spec (10 files in `docs/superpowers/specs/engram/`) to incorporate findings from the adversarial review and Codex dialogue (`019cfefb-b796-78b2-9348-69b7fc6f7696`), addressing three strategic tasks: T1 (promote text-location), T2 (/save recovery model), T3 (operational contracts).

**Architecture:** Surgical spec amendments — no code, no implementation. Each task modifies 2-4 spec files with precise before/after edits. The spec uses a formal authority model (`spec.yaml`), so amendments to `data-contract` authority files (`types.md`, `storage-and-indexing.md`) trigger review obligations for `operations` and `enforcement` authorities per `spec.yaml` boundary rules.

**Tech Stack:** Markdown spec files. No runtime dependencies.

**Source material:** Adversarial review + Codex dialogue synthesis earlier in this conversation. The Codex thread ID is `019cfefb-b796-78b2-9348-69b7fc6f7696`.

---

## File Map

| File | Authority | Amendments |
|------|-----------|------------|
| `types.md` | data-contract | T1: PromoteMeta marker fields, T2: snapshot intent fields, T3: LedgerEntry type |
| `operations.md` | operations | T1: Branch A/B/C state machine + B1/B2, T2: /save snapshot intent + /triage inference matrix, failure handling table |
| `storage-and-indexing.md` | data-contract | T2: snapshot frontmatter fields, T3: ledger schema + search semantics |
| `foundations.md` | foundation | T1: permitted exceptions amendment for markers |
| `enforcement.md` | enforcement | T3: engram_register observation scope note, multi-producer ledger |
| `delivery.md` | delivery | T1: VR-6 marker test cases, T2: intent field verification |
| `decisions.md` | decisions | T1: marker loss risk, T2: never-emitted envelope resolution, T3: ledger schema resolution |
| `skill-surface.md` | skill-contract | T2: /save intent field documentation |
| Design doc (`2026-03-16-engram-design.md`) | n/a | Deprecation header |

**Boundary rule obligations (from `spec.yaml`):**
- Changes to `types.md` and `storage-and-indexing.md` (data-contract) → review `operations.md` and `enforcement.md`
- Changes to `operations.md` → review `skill-surface.md` and `enforcement.md`

These cross-checks are built into the task ordering: T1 and T2 amend data-contract files first, then operations, then downstream authorities.

---

## Task 1: Deprecate Design Document

The design doc contains `.failed/` directory references (lines 222, 244, 551, 658) that contradict the spec's transient-envelope model. Per the Codex dialogue, this must happen before any spec amendments.

**Files:**
- Modify: `docs/superpowers/specs/2026-03-16-engram-design.md:1-6`

- [ ] **Step 1: Add deprecation header**

Insert after the title line (line 1):

```markdown
> **DEPRECATED:** This design document was the input to the modular spec at `docs/superpowers/specs/engram/`. The spec is authoritative. This document is retained for historical context only. Notable divergences: the spec removed `.failed/` envelope storage (transient-envelope model instead), and subsequent amendments added sentinel markers for promote text-location, snapshot intent fields for /save recovery, and a ledger entry schema.
```

- [ ] **Step 2: Verify no spec files reference the design doc as authoritative**

Search for links to `2026-03-16-engram-design.md` in the spec directory. Links should be informational ("compiled from"), not normative ("see design doc for behavior").

Run: `grep -r "2026-03-16-engram-design" docs/superpowers/specs/engram/`
Expected: Only `README.md` line 10 — informational reference. No normative references.

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/specs/2026-03-16-engram-design.md
git commit -m "docs(engram): deprecate design doc in favor of modular spec"
```

---

## Task 2: T1 — Amend PromoteMeta Type with Marker Fields

**Files:**
- Modify: `docs/superpowers/specs/engram/types.md:102-123`

- [ ] **Step 1: Replace PromoteMeta dataclass**

Replace the current `PromoteMeta` dataclass (types.md lines 106-113) with:

```python
@dataclass(frozen=True)
class PromoteMeta:
    target_section: str           # Advisory: last requested destination / insertion hint
    promoted_at: str              # ISO 8601
    promoted_content_sha256: str  # Hash of lesson content at promotion time
    transformed_text_sha256: str  # Hash of text between markers (excluding markers themselves)
    lesson_id: str                # Matches lesson-meta lesson_id — used for marker pair identification
```

- [ ] **Step 2: Add marker specification section after PromoteMeta**

Insert after the serialization example (after line 119), before "Re-promotion detection":

```markdown
### Promotion Markers in CLAUDE.md

When `/promote` writes transformed text to CLAUDE.md, it wraps the text in paired HTML comment markers:

~~~markdown
<!-- engram:lesson:start:<lesson_id> -->
Promoted text here...
<!-- engram:lesson:end:<lesson_id> -->
~~~

**Marker semantics:**
- Markers are **locator hints**, not authoritative state. `promote-meta` in `learnings.md` remains the authority for Branch A/B/C decisions.
- `lesson_id` in markers matches `lesson-meta.lesson_id` — stable for the life of the lesson.
- User can delete markers. Consequence: reduced automation (degradation to manual reconcile), not invalid system state.
- `transformed_text_sha256` hashes the text **between** markers (excluding markers themselves). Used for drift detection, not location.

**Marker validity rules:**
- One `start` + one `end` with the same `lesson_id`, properly ordered
- Non-nested (no marker pair inside another marker pair)
- Unique per `lesson_id` in the file (at most one pair per lesson)
- Violation of any rule: treat as "markers not found" and fall through to manual reconcile

**Marker loss is expected.** Users edit CLAUDE.md freely. The promote state machine treats marker absence as degraded automation, not an error state. See [Branch C location strategy](operations.md#promote-knowledge-to-claudemd).
```

- [ ] **Step 3: Update re-promotion detection paragraph**

Replace the existing "Re-promotion detection" paragraph (types.md line 123) with:

```markdown
**Re-promotion detection:** If a lesson's `content_sha256` changes after promotion, the `PromoteEnvelope` idempotency key changes (because `content_sha256` is part of the material). The engine detects this as a stale promotion: existing `promote-meta.promoted_content_sha256` != current `content_sha256`. `/promote` surfaces stale promotions for user review. `/triage` reports them as a mismatch class alongside the Step-3-failure case.

**`target_section` is advisory.** It records the last requested destination for the promoted text. It is used as an insertion hint for new promotions (Branch A) and as context in the manual reconcile flow. It is **not** the primary locator — marker search is. If the user moves a managed block to a different section, `target_section` becomes stale; `/promote` updates it on the next successful promotion.
```

- [ ] **Step 4: Update PromoteEnvelope docstring**

In the `PromoteEnvelope` dataclass (types.md line 97), update the `target_section` comment:

Replace:
```python
    target_section: str            # Where in CLAUDE.md
```
With:
```python
    target_section: str            # Advisory: insertion hint for CLAUDE.md section
```

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/specs/engram/types.md
git commit -m "docs(engram): add sentinel markers to PromoteMeta type contract"
```

---

## Task 3: T1 — Amend Promote State Machine in Operations

**Files:**
- Modify: `docs/superpowers/specs/engram/operations.md:71-98`

- [ ] **Step 1: Replace the promote operation flow**

Replace the `/promote` section (operations.md lines 71-97) with:

````markdown
### Promote: Knowledge to CLAUDE.md

Three-step state machine with marker-based location and reconciliation recovery. CLAUDE.md is an external sink, not an Engram-managed record. The Knowledge engine owns the promotion *state*. The CLAUDE.md edit is a skill-level operation — a [documented exception](foundations.md#permitted-exceptions) to the core invariant.

```
/promote
    -> query(subsystems=["knowledge"], status="knowledge:published")
    -> Rank by maturity signals (age, breadth, reuse evidence) — advisory ordering only
    -> User selects
    -> Step 1 (engine): Knowledge engine validates promotability via state machine:
        Branch A (no promote-meta): Eligible. Returns promotion plan with target_section.
        Branch B (promote-meta exists, promoted_content_sha256 == current content_sha256):
            B1 (target_section unchanged): Reject — already promoted. Return existing details.
            B2 (target_section changed by user request): Relocation. Search CLAUDE.md for
                markers with lesson_id. If found: move block to new target_section, update
                promote-meta target_section. If not found: manual reconcile flow.
        Branch C (promote-meta exists, promoted_content_sha256 != current content_sha256):
            Stale promotion. Search CLAUDE.md globally for markers with lesson_id.
            If found: replace enclosed text with new transformed text, update markers in place.
            If not found: manual reconcile flow (show old target_section, old content hash,
                new content — user places manually).
    -> Step 2 (skill): Skill writes transformed text to CLAUDE.md wrapped in markers
        For Branch A: insert at target_section with paired markers
        For Branch B2: relocate existing marker-enclosed block
        For Branch C with markers: replace text between existing markers
        For Branch C without markers: manual reconcile — user confirms placement
    -> Step 3 (engine): Knowledge engine writes/updates promote-meta with current hashes
```

**Ranking is advisory, not contractual.** Maturity signals determine display ordering only — they are not part of the storage contract. Engine promotability validation must not depend on undocumented maturity scores.

**Location strategy:** Branch C and B2 search CLAUDE.md globally for `<!-- engram:lesson:start:<lesson_id> -->` / `<!-- engram:lesson:end:<lesson_id> -->` marker pairs. Global search (not section-scoped) supports user relocation of managed blocks — if the user moves a promoted block to a different section, the marker search still finds it. See [marker specification](types.md#promotion-markers-in-claudemd) for validity rules.

**Recovery:** Step 1 validates but does not record durable state — it returns a promotion plan. Step 3 writes [promote-meta](types.md#promote-meta-promotion-state-record) only after the CLAUDE.md write succeeds. If Step 2 fails, no promote-meta exists (Branch A) or stale promote-meta persists (Branch C), so the lesson remains eligible for future `/promote` runs. If Step 3 fails, `/triage` detects the mismatch:
- **Missing promote-meta:** CLAUDE.md has markers + text, no promote-meta at all (Step 3 never ran)
- **Stale promote-meta:** CLAUDE.md has updated text between markers, promote-meta has old hashes (Step 3 failed on re-promotion)
````

- [ ] **Step 2: Update failure handling table**

In the failure handling table (operations.md line 179), replace the "Promote Step 2 failure" row:

Replace:
```
| Promote Step 2 failure | CLAUDE.md unchanged, no promote-meta written | Lesson remains eligible for next `/promote` run |
```
With:
```
| Promote Step 2 failure (Branch A/C with markers) | CLAUDE.md unchanged, no promote-meta written | Lesson remains eligible for next `/promote` run |
| Promote Step 2 manual reconcile (Branch C without markers) | User shown old target_section, content diff | User places text manually; Step 3 records result |
```

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/specs/engram/operations.md
git commit -m "docs(engram): replace hash-based promote location with sentinel markers"
```

---

## Task 4: T1 — Amend Foundations Permitted Exceptions

**Files:**
- Modify: `docs/superpowers/specs/engram/foundations.md:26-30`

- [ ] **Step 1: Expand the permitted exceptions section**

Replace the current "Permitted Exceptions" content (foundations.md lines 26-30) with:

```markdown
### Permitted Exceptions

CLAUDE.md is an external sink, not an Engram-managed record. Two operations are permitted on CLAUDE.md:

1. **Content write:** The [/promote](operations.md#promote-knowledge-to-claudemd) Step 2 writes transformed text wrapped in [paired markers](types.md#promotion-markers-in-claudemd). The Knowledge engine owns promotion *state* (via [promote-meta](types.md#promote-meta-promotion-state-record)); the CLAUDE.md edit is a skill-level operation that bypasses the engine write path.

2. **Marker management:** Markers (`<!-- engram:lesson:start/end:<lesson_id> -->`) are locator hints embedded in CLAUDE.md for re-promotion and relocation. They broaden the ownership posture (Engram places content in CLAUDE.md) without shifting authority (promote-meta remains the source of truth). Marker deletion by the user degrades automation (manual reconcile), not system state.

No other skill-level write to a protected or externally-owned path is permitted without an explicit clause in this section.
```

- [ ] **Step 2: Commit**

```bash
git add docs/superpowers/specs/engram/foundations.md
git commit -m "docs(engram): expand permitted exceptions for promotion markers"
```

---

## Task 5: T2 — Add Snapshot Intent Fields to Types

**Files:**
- Modify: `docs/superpowers/specs/engram/types.md` (after Write Concurrency section, before EOF)

- [ ] **Step 1: Add snapshot orchestration intent section**

Append to the end of `types.md`:

```markdown
## Snapshot Orchestration Intent

When `/save` creates a snapshot, it embeds orchestration intent as flat scalar fields in the snapshot frontmatter:

```yaml
orchestrated_by: save
save_expected_defer: true
save_expected_distill: true
```

**Fields:**
- **`orchestrated_by`**: `"save"` when created by `/save` orchestrator. Absent when created by `/quicksave` or standalone `/load`. Presence indicates the snapshot was part of an orchestrated flow with expected sub-operations.
- **`save_expected_defer`**: `true` if `/save` was invoked without `--no-defer`. `false` if `--no-defer` was passed. Absent when `orchestrated_by` is absent.
- **`save_expected_distill`**: `true` if `/save` was invoked without `--no-distill`. `false` if `--no-distill` was passed. Absent when `orchestrated_by` is absent.

**Immutability:** Snapshots are immutable after creation. These fields record the intent at creation time. If a user later retries a failed sub-operation standalone (e.g., `/defer --snapshot-ref`), the snapshot's intent fields are not updated — the downstream record's existence is the proof of completion.

**Parse normalization:** Frontmatter parsers must normalize string `"true"`/`"false"` to boolean. YAML native booleans (`true`/`false` without quotes) are preferred but string representations must be accepted.

**Relationship to /triage:** These fields enable `/triage` to distinguish "intentionally skipped" from "crashed before running." See [/triage inference matrix](operations.md#triage-read-work-and-context).
```

- [ ] **Step 2: Commit**

```bash
git add docs/superpowers/specs/engram/types.md
git commit -m "docs(engram): add snapshot orchestration intent fields"
```

---

## Task 6: T2 — Amend /save Orchestration and /triage in Operations

**Files:**
- Modify: `docs/superpowers/specs/engram/operations.md:129-181`

- [ ] **Step 1: Update /save orchestration flow**

Replace the `/save` flow block (operations.md lines 131-141) with:

````markdown
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
````

- [ ] **Step 2: Update /triage operation with inference matrix**

Replace the `/triage` flow block (operations.md lines 57-65) with:

````markdown
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
    -> Cross-reference: orphaned items, stale tickets, blocked chains
    -> Report pending staged knowledge candidates
    -> Report promote-meta mismatches (missing or stale)
    -> Return structured triage report with per-subsystem sections
```
````

- [ ] **Step 3: Update failure handling table**

Replace the "Crash before envelope write" row (operations.md line 178) with:

```
| Crash before envelope write | Snapshot has `save_expected_defer: true` but no downstream record and no `defer_completed` ledger event | `/triage` reports "completion not proven" for expected sub-operations. User retries via standalone `/defer --snapshot-ref`. |
```

Replace the "Crash after envelope write" row (operations.md line 177) with:

```
| Crash after envelope write | Envelope emitted but downstream record not created. `defer_completed` ledger event may exist. | `/triage` infers from `source_ref` scan + ledger events. User retries; idempotency key prevents duplicates. |
```

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/specs/engram/operations.md
git commit -m "docs(engram): add snapshot intent fields and triage inference matrix"
```

---

## Task 7: T3 — Add Ledger Entry Schema to Types

**Files:**
- Modify: `docs/superpowers/specs/engram/types.md` (append after Snapshot Orchestration Intent)

- [ ] **Step 1: Add LedgerEntry type**

Append to the end of `types.md`:

```markdown
## LedgerEntry — Event Record

Each line in a ledger shard (`ledger/<worktree_id>/<session_id>.jsonl`) is a single JSON object conforming to this schema:

~~~python
@dataclass(frozen=True)
class LedgerEntry:
    schema_version: str           # "1.0"
    ts: str                       # ISO 8601 UTC — primary sort key
    event_type: str               # From event vocabulary below
    producer: str                 # "engine" | "orchestrator" | "hook"
    session_id: str               # Claude session UUID
    worktree_id: str              # Derived from git rev-parse --git-dir
    record_ref: str | None        # RecordRef canonical serialization, if applicable
    operation_id: str | None      # Groups related events (e.g., all events from one /save)
    payload: dict                 # Event-type-specific data
~~~

### Event Vocabulary (v1)

| Event Type | Producer | Payload Fields | Purpose |
|---|---|---|---|
| `snapshot_written` | orchestrator | `{ref: RecordRef, orchestrated_by: str}` | Timeline fidelity — records snapshot creation |
| `defer_completed` | engine | `{source_ref: RecordRef, emitted_count: int}` | Completion evidence for /triage inference |
| `distill_completed` | engine | `{source_ref: RecordRef, emitted_count: int}` | Completion evidence for /triage inference |

**Completion events are success-only.** Their presence proves the operation ran to completion. Their absence means "not proven completed" — not "failed." Failure events are [deferred](decisions.md#deferred-decisions) to a future recovery-phase extension.

### Producer Classes

- **`engine` / `orchestrator`**: Events from subsystem engines and skill orchestrators (e.g., `/save`). These are authoritative completion signals. Only engine/orchestrator events qualify for the "ledger-backed" label in [/timeline](operations.md#session-timeline).
- **`hook`**: Events from `engram_register` PostToolUse hook. Observational only. `engram_register` does not observe engine Bash writes — it fires on Write/Edit tool calls to protected paths. Hook events provide supplementary timeline data but do not qualify as "ledger-backed."

### Timeline Label Semantics

- **"ledger-backed"**: A defined event from an `engine` or `orchestrator` producer exists for this record/operation.
- **"inferred"**: Reconstructed from `created_at` timestamps in `IndexEntry`, `source_ref` field scanning, or `git log` history.

### Ordering

- Primary sort: `ts` (ISO 8601 string comparison)
- Tie-break: file order (append-order within the JSONL shard)
- Grouping: `operation_id` links related events from the same orchestrated flow

### Write Semantics

All ledger producers use a shared locked append primitive in `engram_core/`. Advisory lock (`fcntl.flock`) on the shard file. Lock scope: read-append-fsync. Multi-producer integrity replaces the previous "single writer by sharding" assumption (which broke when engines became ledger producers).

**Ledger append failure never invalidates a successful write.** If a `defer_completed` event fails to append after a successful ticket creation, the ticket exists — the ledger gap is a diagnostic degradation, not data loss.
```

- [ ] **Step 2: Commit**

```bash
git add docs/superpowers/specs/engram/types.md
git commit -m "docs(engram): add LedgerEntry type and event vocabulary"
```

---

## Task 8: T3 — Amend Ledger and Search in Storage-and-Indexing

**Files:**
- Modify: `docs/superpowers/specs/engram/storage-and-indexing.md:197-219`

- [ ] **Step 1: Replace the Ledger section**

Replace the current Ledger section (storage-and-indexing.md lines 197-208) with:

```markdown
## Ledger

Architecturally optional, operationally default-on. Sharded as `ledger/<worktree_id>/<session_id>.jsonl` in private root. Each line is a [LedgerEntry](types.md#ledgerentry-event-record) JSON object.

**Producers:** Engines and orchestrators append completion events post-commit. The `engram_register` hook appends observational events for Write/Edit tool calls. See [producer classes](types.md#producer-classes) for the distinction and its impact on timeline labels.

**Sharding:** Per worktree and session. Multi-producer writes to the same shard are coordinated via a [shared locked append primitive](types.md#write-semantics).

Session timeline reconstructs from:
1. `created_at` timestamps from `IndexEntry` (parsed during scan)
2. `session_id` in `RecordMeta` to group records by session
3. Ledger events matching `session_id` (engine/orchestrator events are "ledger-backed")
4. `git log` for shared-root change attribution (called once per timeline request, not per query)

No ledger means timeline still works but at lower fidelity (no completion evidence, no sub-file-creation event granularity). This is a documented trade-off, not a silent degradation.
```

- [ ] **Step 2: Add search semantics section**

Insert after the "Namespaced Status Filtering" section (after line 189), before "Fresh Scan":

```markdown
### Text Search Semantics

The `query()` `text` parameter searches `title`, `snippet`, and `tags` fields of each `IndexEntry`:

- **Case-insensitive:** All comparisons use Unicode case-folded values.
- **Tokenization:** Split on whitespace and punctuation boundaries. `"auth middleware"` produces tokens `["auth", "middleware"]`.
- **Multi-token behavior:** AND — all tokens must match somewhere across the searched fields. A token matching in `title` and another in `tags` satisfies the query.
- **Matching:** Substring within tokens. `"auth"` matches `"authentication"`. Exact-match is not required.
- **Ordering within subsystem groups:** `created_at` descending (newest first). Deterministic — no relevance ranking in v1.

Ranking (BM25, TF-IDF, recency-weighted scoring) is [deferred](decisions.md#deferred-decisions). The current ordering is simple and predictable.
```

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/specs/engram/storage-and-indexing.md
git commit -m "docs(engram): specify ledger producers and search semantics"
```

---

## Task 9: T3 — Amend Enforcement for Multi-Producer Ledger

**Files:**
- Modify: `docs/superpowers/specs/engram/enforcement.md:16`

- [ ] **Step 1: Update engram_register row in hooks table**

Replace the `engram_register` row (enforcement.md line 16):

Replace:
```
| `engram_register` | PostToolUse (Write, Edit) | 3rd | Ledger append | **Silent** (best-effort) |
```
With:
```
| `engram_register` | PostToolUse (Write, Edit) | 3rd | Ledger append ([hook-class events](types.md#producer-classes)) | **Silent** (best-effort) |
```

- [ ] **Step 2: Add observation scope note**

Insert after the hooks table (after line 17), before "Protected-Path Enforcement":

```markdown
### Ledger Multi-Producer Note

`engram_register` fires on Write and Edit tool calls to protected paths. It does **not** observe engine Bash invocations (`python3 engine_*.py`). Engine-authored ledger events ([`defer_completed`](types.md#event-vocabulary-v1), [`distill_completed`](types.md#event-vocabulary-v1)) are appended by engines post-commit, not by hooks. This separation means:
- Hook events and engine events have distinct observation scopes — no dedup concern between producer classes
- The "ledger-backed" timeline label applies only to engine/orchestrator events, not hook events
- All producers use the shared locked append primitive defined in [types.md](types.md#write-semantics)
```

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/specs/engram/enforcement.md
git commit -m "docs(engram): document multi-producer ledger and observation scope"
```

---

## Task 10: Amend Delivery Verification Requirements

**Files:**
- Modify: `docs/superpowers/specs/engram/delivery.md:211-215`

- [ ] **Step 1: Expand VR-6 for marker tests**

Replace the VR-6 line (delivery.md line 215):

Replace:
```
- /triage promote-meta detection (VR-6): fixture with CLAUDE.md text but no promote-meta → assert mismatch reported; fixture with stale promote-meta → assert stale reported
```
With:
```
- /triage promote-meta detection (VR-6): fixture with CLAUDE.md markers + text but no promote-meta → assert mismatch reported; fixture with stale promote-meta → assert stale reported; fixture with CLAUDE.md text but markers deleted → assert manual reconcile surfaced
- Promote marker lifecycle (VR-10): Branch A inserts markers + text; Branch C locates markers, replaces enclosed text; Branch B2 relocates marker-enclosed block to new section; missing markers → manual reconcile
```

- [ ] **Step 2: Add intent field and completion event verification**

Insert after the VR-6/VR-10 lines:

```
- Snapshot intent fields (VR-12): /save without flags → snapshot has orchestrated_by=save, save_expected_defer=true, save_expected_distill=true; /save --no-defer → save_expected_defer=false; /quicksave → no orchestration fields
- Triage inference matrix (VR-13): fixture with expected_defer=true + ticket exists → satisfied; expected_defer=false + no ticket → skipped; expected_defer=true + no ticket + defer_completed(emitted_count=0) → zero-output success; expected_defer=true + no ticket + no completion event → completion-not-proven
```

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/specs/engram/delivery.md
git commit -m "docs(engram): add marker lifecycle and triage inference verification"
```

---

## Task 11: Amend Decisions — Resolve Risks and Update Deferrals

**Files:**
- Modify: `docs/superpowers/specs/engram/decisions.md`

- [ ] **Step 1: Add marker loss risk to Named Risks table**

Insert after the "Chain protocol limitations" row (decisions.md line 22):

```
| **Promotion marker loss** | Low | User deletes `<!-- engram:lesson:start/end -->` markers from CLAUDE.md. Consequence: Branch C/B2 degrades to manual reconcile. Promote-meta remains authoritative — no invalid state. [Marker specification](types.md#promotion-markers-in-claudemd). | `/promote` on a previously-promoted lesson produces manual reconcile instead of automatic replacement? |
```

- [ ] **Step 2: Update open questions — resolve "never-emitted envelope" gap**

The "never-emitted envelope" problem identified in the adversarial review is now resolved by snapshot intent fields + ledger completion events. No new open question needed — the solution is in the spec amendments above.

Add to the open questions table:

```
| Bounded candidate search within CLAUDE.md sections — should Step 0a include section-scoped fuzzy matching as fallback? | Step 0a implementation. Start with markers + manual reconcile only. Add section search if marker loss frequency warrants. |
```

- [ ] **Step 3: Update deferred decisions**

Add to the deferred decisions table:

```
| Ledger failure taxonomy | Success-only events for v1. Add failure events, phase attribution, and error classification when recovery-phase automation is warranted. |
| Search relevance ranking | Deterministic `created_at` ordering for v1. Add BM25/TF-IDF when query volume and result set size warrant ranking. |
| Promotion bounded search | Marker-based location only for v1. Add section-scoped candidate matching if marker loss data shows need. |
```

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/specs/engram/decisions.md
git commit -m "docs(engram): add marker loss risk and resolve recovery model gap"
```

---

## Task 12: Amend Skill-Surface for /save Intent Documentation

**Files:**
- Modify: `docs/superpowers/specs/engram/skill-surface.md:14`

- [ ] **Step 1: Update /save row in skills table**

Replace the `/save` row (skill-surface.md line 14):

Replace:
```
| `/save` | Context (orchestrator) | Orchestrates [defer + distill](operations.md#save-as-session-orchestrator). Per-step results. `--no-defer`, `--no-distill`. |
```
With:
```
| `/save` | Context (orchestrator) | Orchestrates [defer + distill](operations.md#save-as-session-orchestrator). Embeds [orchestration intent](types.md#snapshot-orchestration-intent) in snapshot frontmatter. Per-step results. `--no-defer`, `--no-distill`. |
```

- [ ] **Step 2: Commit**

```bash
git add docs/superpowers/specs/engram/skill-surface.md
git commit -m "docs(engram): document /save orchestration intent in skills table"
```

---

## Task 13: Cross-Reference Verification

Final pass to verify all cross-references are consistent across the amended spec.

**Files:**
- Read: All 8 spec files + `spec.yaml`

- [ ] **Step 1: Verify all new anchors resolve**

Check that every new cross-reference link added in Tasks 2-12 resolves to an existing section:

```bash
# Extract all markdown links from spec files and check anchors
grep -roh '\[.*\](.*\.md#[^)]*)\|](.*\.md#[^)]*)' docs/superpowers/specs/engram/ | sort -u
```

Manually verify each new anchor:
- `types.md#promotion-markers-in-claudemd` → exists (added in Task 2)
- `types.md#snapshot-orchestration-intent` → exists (added in Task 5)
- `types.md#ledgerentry-event-record` → exists (added in Task 7)
- `types.md#producer-classes` → exists (added in Task 7)
- `types.md#event-vocabulary-v1` → exists (added in Task 7)
- `types.md#write-semantics` → exists (added in Task 7)
- `operations.md#triage-read-work-and-context` → exists (updated in Task 6)

- [ ] **Step 2: Verify boundary rule compliance**

Per `spec.yaml` boundary rules:
- `data-contract` changed (types.md, storage-and-indexing.md) → review `operations.md` and `enforcement.md`: both amended in Tasks 3, 6, 9 ✓
- `operations.md` changed → review `skill-surface.md` and `enforcement.md`: both amended in Tasks 12, 9 ✓

- [ ] **Step 3: Verify no stale references to old promote behavior**

```bash
grep -rn "transformed_text_sha256.*locat" docs/superpowers/specs/engram/
grep -rn "locate.*text.*hash" docs/superpowers/specs/engram/
```

Expected: No results referencing the old hash-based text-location strategy (all replaced by marker-based).

- [ ] **Step 4: Final commit (if any cross-reference fixes needed)**

```bash
git add docs/superpowers/specs/engram/
git commit -m "docs(engram): fix cross-references from spec amendments"
```

If no fixes needed, skip this step.
