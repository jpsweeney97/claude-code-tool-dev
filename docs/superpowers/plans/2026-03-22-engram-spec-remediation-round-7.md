# Engram Spec Remediation Round 7 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remediate all 60 findings (29 P1, 31 P2) from spec review round 7 across the engram spec at `docs/superpowers/specs/engram/`.

**Architecture:** Three-phase commit sequence: (1) mechanical cross-reference and text fixes, (2) normative spec completions with 6 resolved design decisions, (3) verification spec updates in delivery.md. Each commit is independently reviewable. No code changes — all edits are to markdown spec files.

**Tech Stack:** Markdown editing. Spec files at `docs/superpowers/specs/engram/`. Review artifacts at `.review-workspace/`.

---

## Design Decisions

Six findings required authorial choices. Resolved via Codex dialogue (thread `019d182a-8ed1-7ca0-8dba-874d9ee2f315`, collaborative, 5 turns, all converged at high confidence).

| # | Finding | Decision | Key Detail |
|---|---------|----------|------------|
| 1 | SY-2 | Per-entrypoint rejection contract — mandate behavior, not the shared helper | Stable message: `"hook_request_origin: expected {expected!r} for this entrypoint, got {actual!r}"`. Three invariants: (1) reject before side effects, (2) no state changes, (3) error must include normalized message. |
| 2 | SY-7 | No approval UI for Branch A — implicit confirmation with two new normative invariants | (1) Branch A `transformed_text` MUST be faithful rendering (markers only). (2) `target_section` is advisory; relocation handled by Branch B2. |
| 3 | SY-10 | Accept single-session sequential guarantee — document the accepted gap | Add explicit statement + "must revisit locking if parallel promote callers are introduced" note. |
| 4 | SY-24 | AuditEntry TypedDict in types.md — 7 fields, sort_keys=True JSONL, 6th version space | Fields: `schema_version: "1.0"`, `timestamp`, `operation` (create\|update\|close), `ticket_ref`, `source_ref: str \| None`, `session_id: str \| None` (correlational), `trust_triple_present: bool`. |
| 5 | SY-29 | Positional-last argument for payload path — matches proven ticket plugin pattern | Final `sys.argv` entry, nothing after it. Engine rejects if final arg is missing, unreadable, or invalid. |
| 6 | SY-41 | Remove section count from quality validation scope | Untestable check with no defined threshold provides false coverage. Replace with required-section checks when body structure becomes normative. |

## File Map

| Phase | File | Finding Count | Findings |
|-------|------|--------------|----------|
| 1 | enforcement.md | 1 | SY-1 |
| 1 | storage-and-indexing.md | 1 | SY-11 |
| 1 | types.md, enforcement.md, skill-surface.md | 3 | SY-43, SY-44, SY-45 |
| 1 | delivery.md, enforcement.md, foundations.md, README.md, decisions.md | 6 | SY-30, SY-31, SY-32, SY-33, SY-35, SY-40 |
| 2 | types.md | 10 | SY-3, SY-12, SY-24, SY-34, SY-37, SY-39, SY-46, SY-54, SY-55, SY-56 |
| 2 | enforcement.md | 15 | SY-2, SY-4, SY-5, SY-8, SY-25, SY-26, SY-27, SY-28, SY-29, SY-36, SY-38, SY-41, SY-58, SY-59, SY-60 |
| 2 | operations.md | 4 | SY-6, SY-7, SY-9, SY-10 |
| 2 | storage-and-indexing.md | 2 | SY-53, SY-57 |
| 3 | delivery.md | 18 | SY-3t, SY-13–SY-23, SY-42, SY-47–SY-52 |

---

## Phase 1: Mechanical Fixes

### Task 1: Heading Promotions and Cross-Reference Anchor Fixes

**Files:**
- Modify: `docs/superpowers/specs/engram/enforcement.md:127`
- Modify: `docs/superpowers/specs/engram/storage-and-indexing.md:92`
- Modify: `docs/superpowers/specs/engram/types.md` (multiple headings with underscores)
- Modify: `docs/superpowers/specs/engram/enforcement.md` (multiple headings with underscores)
- Modify: `docs/superpowers/specs/engram/skill-surface.md:42`
- Modify: `docs/superpowers/specs/engram/delivery.md:203`

- [ ] **Step 1: SY-1 — Promote guard capability rollout heading in enforcement.md**

At `enforcement.md:127`, change:
```
**Guard capability rollout:** Each build step lists the `engram_guard` capabilities it requires.
```
to:
```
### Guard Capability Rollout

Each build step lists the `engram_guard` capabilities it requires.
```
This generates the `#guard-capability-rollout` anchor that `enforcement.md:262` and `delivery.md:184` link to.

- [ ] **Step 2: SY-11 — Promote RecordMeta field mapping heading in storage-and-indexing.md**

At `storage-and-indexing.md:92`, change:
```
**RecordMeta field mapping per subsystem:**
```
to:
```
### RecordMeta Field Mapping per Subsystem
```
This generates the `#recordmeta-field-mapping-per-subsystem` anchor that `types.md:414` links to.

- [ ] **Step 3: SY-43 — Fix 8 underscore-containing heading anchors**

Rename headings that contain underscores (GitHub slugification strips `_`). For each affected heading, replace underscores with hyphens in the heading text, then update all source links to match the new slug.

Affected headings (check each file for current heading text):
- `types.md`: `### Legacy Entries (Missing meta_version)` — rename to `### Legacy Entries: Missing meta-version` (update 1 inbound link from operations.md:150)
- `types.md`: `### Trust Validation — collect_trust_triple_errors()` — rename to `### Trust Validation` (update 3 inbound links from enforcement.md:189, enforcement.md:191 ×2)
- Check remaining 6 anchors from the SY-43 finding in `.review-workspace/findings/completeness-coherence.md` (CC-8) for the full list of affected headings and source locations.

- [ ] **Step 4: SY-44 — Fix em-dash heading anchor in skill-surface.md**

At `skill-surface.md:42`, change:
```
## Chain Protocol — Session Lineage Tracking
```
to (using a colon instead of em-dash):
```
## Chain Protocol: Session Lineage Tracking
```
Then update inbound links at `foundations.md:80` and `delivery.md:223` from `#chain-protocol-session-lineage-tracking` (which now matches the colon-based slug).

- [ ] **Step 5: SY-45 — Fix fragile duplicate-heading suffix anchor in delivery.md**

At `delivery.md:203`, find the link `(#required-verification-4)` and replace with a direct citation: change `"Mirrors [VR-3A-11](#required-verification-4) for..."` to `"Mirrors VR-3A-11 (see Step 3a Required Verification above) for..."`. This removes the fragile GitHub-generated suffix anchor.

- [ ] **Step 6: Verify cross-references resolve**

Run a manual spot-check: confirm that `enforcement.md:262` and `delivery.md:184` now resolve to the guard capability rollout heading, and that `types.md:414` resolves to the RecordMeta field mapping heading.

- [ ] **Step 7: Commit**

```bash
git add docs/superpowers/specs/engram/enforcement.md docs/superpowers/specs/engram/storage-and-indexing.md docs/superpowers/specs/engram/types.md docs/superpowers/specs/engram/skill-surface.md docs/superpowers/specs/engram/delivery.md
git commit -m "fix(spec): remediate heading and cross-reference anchor defects from review round 7

Promote 2 bold-text paragraphs to headings (SY-1, SY-11), fix 8
underscore anchors (SY-43), fix 2 em-dash anchors (SY-44), and
replace 1 fragile duplicate-heading suffix (SY-45)."
```

### Task 2: Text Alignment and Authority Delegation

**Files:**
- Modify: `docs/superpowers/specs/engram/delivery.md`
- Modify: `docs/superpowers/specs/engram/enforcement.md`
- Modify: `docs/superpowers/specs/engram/foundations.md`
- Modify: `docs/superpowers/specs/engram/README.md`
- Modify: `docs/superpowers/specs/engram/decisions.md`

- [ ] **Step 1: SY-30 — Convert delivery.md enforcement restatement to reference**

At `delivery.md` Step 3a and Step 4a intra-step ordering clauses, replace the inline restatement of the enforcement constraint with a reference. Change any text like `"no subsystem may activate a mutating route before the guard capabilities required for that route are active"` to: `"(per [Guard Capability Rollout](enforcement.md#guard-capability-rollout))"`. Remove the paraphrased constraint text.

- [ ] **Step 2: SY-31 — Convert enforcement.md Enforcement Boundary Constraint restatement to delegation**

At `enforcement.md:110-114`, change the assertion pattern from:
`"Implementation must never return exit code 2 (Block)."`
to a delegation pattern:
`"Per the [Enforcement Boundary Constraint](foundations.md#enforcement-boundary-constraint-invariant), exit code 2 is prohibited here."`

- [ ] **Step 3: SY-32 — Add enforcement_mechanism precedence to README.md**

At `README.md:27`, append a third sentence to the precedence summary:
```
`enforcement` wins for `enforcement_mechanism` claims, with `operations` as secondary authority — see boundary rules in spec.yaml.
```

- [ ] **Step 4: SY-33 — Trim foundations.md Permitted Exceptions to architectural authorization only**

At `foundations.md:30`, replace the inline behavioral description with a reference. Change:
```
The [/promote](operations.md#promote-knowledge-to-claudemd) Step 2 writes transformed text wrapped in [paired markers](types.md#promotion-markers-in-claudemd). See the [promote state machine](operations.md#promote-knowledge-to-claudemd) for the full behavioral specification (step sequencing, drift detection, branch logic).
```
to:
```
The [/promote](operations.md#promote-knowledge-to-claudemd) Step 2 writes to CLAUDE.md. See [operations.md §Promote](operations.md#promote-knowledge-to-claudemd) for the full behavioral specification.
```

- [ ] **Step 5: SY-35 — Add error-joining cross-reference to enforcement.md**

At `enforcement.md` §Step 2: Validation, after the enforcement mandate paragraph, add:
```
Error strings from `collect_trust_triple_errors()` must be joined with `'; '` in the rejection response — see [types.md §TrustPayload](types.md#trustpayload--trust-triple-wire-format) for the stable error string formats.
```

- [ ] **Step 6: SY-40 — Fix decisions.md staging cap formula**

At `decisions.md:56`, change:
```
Whole-batch rejection when `batch_size > knowledge_max_stages`
```
to:
```
Whole-batch rejection when `count + batch_size > knowledge_max_stages` (cumulative check — existing staged files count toward the cap)
```

- [ ] **Step 7: Commit**

```bash
git add docs/superpowers/specs/engram/delivery.md docs/superpowers/specs/engram/enforcement.md docs/superpowers/specs/engram/foundations.md docs/superpowers/specs/engram/README.md docs/superpowers/specs/engram/decisions.md
git commit -m "fix(spec): remediate text alignment and authority delegation findings from review round 7

Convert enforcement restatements to references (SY-30, SY-31), add
enforcement_mechanism precedence to README (SY-32), trim foundations.md
to architectural authorization (SY-33), add error-joining cross-ref
(SY-35), fix staging cap formula in decisions.md (SY-40)."
```

---

## Phase 2: Normative Spec Completions

### Task 3: types.md Completions (10 findings)

**Files:**
- Modify: `docs/superpowers/specs/engram/types.md`

- [ ] **Step 1: SY-3 — Add explicit trace-only prohibition for DistillEnvelope.idempotency_key**

At `types.md:346` (end of the DistillEnvelope trace-only paragraph), append:
```
The engine MUST NOT check `idempotency_key` for `DistillEnvelope` dedup — doing so would incorrectly deduplicate re-extractions with improved logic. This is an active prohibition, not just the absence of a check.
```

- [ ] **Step 2: SY-12 — Add `timestamp` to required snapshot frontmatter fields**

At `types.md:413-416` (the required fields list in Snapshot Orchestration Intent), the fields `schema_version`, `session_id`, and `worktree_id` are listed. Add `timestamp` to the required fields:
```
- **`timestamp`**: ISO 8601 UTC creation time of the snapshot/checkpoint. Maps to `IndexEntry.created_at` for the Context reader. Required for enforcement.md quality validation.
```
Place this after the `worktree_id` bullet.

- [ ] **Step 3: SY-24 — Add AuditEntry TypedDict and Work Audit Trail section**

After the `LedgerEntry` section (after approximately `types.md:489`), add a new section:

```markdown
## AuditEntry — Work Audit Trail

Each line in a work audit file (`engram/work/.audit/<session_id>.jsonl`) records an effective mutation to the Work subsystem.

```python
class AuditEntry(TypedDict):
    schema_version: Literal["1.0"]
    timestamp: str              # ISO 8601 UTC
    operation: str              # "create" | "update" | "close"
    ticket_ref: str             # RecordRef canonical serialization
    source_ref: str | None      # RecordRef canonical serialization, if applicable
    session_id: str | None      # Correlational — see invariant below
    trust_triple_present: bool
```

**Serialization:** UTF-8 JSONL, compact, `sort_keys=True`, one object per line, newline-terminated.

**Write semantics:** Append-only. An AuditEntry is written after a successful effective mutation (ticket created, updated, or closed). No `.audit/` entry on duplicate idempotent retry — the idempotency check prevents the effective mutation, so no audit entry is warranted.

**`session_id` invariant:** If `trust_triple_present` is `True`, `session_id` must equal the validated trust-triple session ID. If `trust_triple_present` is `False`, `session_id` must be `null`. `session_id` is correlational metadata — provenance is established only when `trust_triple_present` is `True`.

**TTL:** None in v1. Retention policy deferred.
```

Also add a 6th version space entry to the Version Spaces table at `types.md:497-503`:
```
| Work audit trail format | `AuditEntry.schema_version` | Work audit JSONL entries | `"1.0"` |
```

And add a corresponding row to the Compatibility Rules table:
```
| Work audit trail format | **Same-major tolerance.** Same rules as ledger format — parse `schema_version` major, skip on mismatch, unknown fields ignored. | Writers emit the version they were built for. |
```

- [ ] **Step 4: SY-34 — Clarify that engines must emit completion events even for zero-output**

At `types.md:459` (end of the `emitted_count` paragraph), append:
```
Engines must emit `defer_completed` / `distill_completed` even when `emitted_count` is 0 — a zero-output operation is a successful completion and must be recorded. Omitting the event makes `/triage` report "completion not proven" for a successful operation.
```

- [ ] **Step 5: SY-37 — Add engine/orchestrator ledger append failure modes**

At `types.md:487` (after "Ledger append failure never invalidates a successful write."), add:
```
**Engine/orchestrator append failure modes:** Lock timeout (5 seconds) → log warning, do not propagate to caller. Disk full / permission denied → log error, do not propagate. Failed appends are observable via `diagnostics.warnings` on the next query. These mirror the `engram_register` failure modes in [enforcement.md](enforcement.md#hooks).
```

- [ ] **Step 6: SY-39 — Add checkpoint frontmatter specification to types.md**

After the Snapshot Orchestration Intent section (approximately `types.md:427`), add:
```markdown
## Checkpoint Frontmatter

Checkpoints created by `/quicksave` use the following frontmatter:

| Field | Type | Source |
|---|---|---|
| `schema_version` | `str` | `"1.0"` |
| `session_id` | `str` | From Claude session context |
| `worktree_id` | `str` | From `identity.get_worktree_id()` |
| `timestamp` | `str` | ISO 8601 UTC creation time |
| `source_skill` | `str` | `"quicksave"` |

Cross-reference: [enforcement.md §Quality Validation Scope](enforcement.md#quality-validation-scope) uses this field set for checkpoint frontmatter completeness checks.
```

- [ ] **Step 7: SY-46 — Define canonical record_kind for published knowledge entries**

At `types.md:378` (after the sentence about entries lacking `lesson-meta` being assigned `record_kind: "legacy"`), add:
```
Published knowledge entries (those with valid `lesson-meta`) are assigned `record_kind: "lesson"` by the Knowledge reader. Staged entries (in `knowledge_staging/`) use `record_kind: "staged"`.
```

- [ ] **Step 8: SY-54 — Add path normalization constraint for work_dedup_fingerprint**

At `types.md:281` (the `work_dedup_fingerprint` formula row), after the formula description, add a note:
```
`key_file_paths` must be stored and used as relative paths from the repo root (consistent with how `source_ref` uses repo-relative addressing). Callers constructing `DeferEnvelope` must normalize paths via `os.path.relpath(path, repo_root)` before inclusion. This is a caller obligation — `work_dedup_fingerprint` does not normalize paths.
```

- [ ] **Step 9: SY-55 — Add PromoteMeta.lesson_id cross-validation rule at read time**

At `types.md:190` (after the corrupt promote-meta rule), add:
```
**Read-time cross-validation:** If `promote-meta.lesson_id` does not match the immediately preceding `lesson-meta.lesson_id` in the same entry block, treat the `promote-meta` as corrupt (same behavior as a missing required field: promotion status degrades to `unknown` with a per-entry warning in `QueryDiagnostics.warnings`).
```

- [ ] **Step 10: SY-56 — Clarify "index-only" permitted uses for staging content field**

At `types.md:150` (after "The `content` field in the staging-meta JSON is index-only"), add:
```
"Index-only" means: the Knowledge reader MUST derive `IndexEntry.snippet` from the markdown body (after the staging-meta comment), not from the JSON `content` field. The `content` field may be used for internal staging operations (e.g., logging, diagnostics) but must not drive display output.
```

- [ ] **Step 11: Verify consistency**

Check that all new type definitions follow existing patterns (TypedDict style, `sort_keys=True` serialization notes, version space references). Verify the AuditEntry definition cross-references correctly.

- [ ] **Step 12: Commit**

```bash
git add docs/superpowers/specs/engram/types.md
git commit -m "fix(spec): remediate 10 types.md findings from spec review round 7

Add trace-only prohibition (SY-3), timestamp field (SY-12), AuditEntry
TypedDict + 6th version space (SY-24), zero-output obligation (SY-34),
engine append failure modes (SY-37), checkpoint frontmatter spec (SY-39),
record_kind values (SY-46), path normalization (SY-54), promote-meta
cross-validation (SY-55), index-only clarification (SY-56)."
```

### Task 4: enforcement.md Completions (15 findings)

**Files:**
- Modify: `docs/superpowers/specs/engram/enforcement.md`

- [ ] **Step 1: SY-2 — Add per-entrypoint origin-matching rejection contract**

At `enforcement.md:224` (end of the Origin-Matching by Entrypoint section), replace the last paragraph with:

```markdown
**Enforcement mechanism:** Origin-matching has no shared runtime validator. `collect_trust_triple_errors()` validates structural correctness (`hook_request_origin` is a valid string in `{"user", "agent"}`) but does not enforce per-entrypoint origin rules. Each entrypoint is responsible for checking that the origin value matches its expected category (see table above).

**Per-entrypoint rejection contract:** When origin mismatch is detected, the entrypoint must:
1. Reject before any side effects (no state changes).
2. Return failure with the stable error message: `"hook_request_origin: expected {expected!r} for this entrypoint, got {actual!r}"`.
3. Surface the error in the structured response — the normalized message must be present.

A shared helper `validate_origin_match(expected, actual)` is recommended but not mandated. VR-3A-14 verifies the rejection contract across all 6 mutating entrypoints to catch contract drift.
```

- [ ] **Step 2: SY-4 — Add authority caption to Autonomy Model table**

At `enforcement.md:312` (before the Autonomy Model table), add a table caption:
```
**Mode definitions (behavioral semantics):** [operations.md §Work Mode Definitions](operations.md#work-mode-definitions) (authoritative). This table owns configuration schema and enforcement caps only (`enforcement_mechanism` authority).
```

Also extend the disclaimer at `enforcement.md:322` to cover the entire table: change "rationale column entries" to "all table content".

- [ ] **Step 3: SY-5 — Add caller identity cross-reference for Branch 2**

At `enforcement.md:239` (end of the Direct-Write Path Authorization section), add after "Identity verification is intentionally omitted":
```
See [decisions.md §Named Risks](decisions.md#named-risks) (Context any-source write authorization) for the accepted gap and rationale.
```

- [ ] **Step 4: SY-8 — Add trust triple scope rationale for worktree_id blocking**

At `enforcement.md:243` (end of the Trust Triple Scope section), add:
```
Although `worktree_id` is not part of the trust triple payload, the guard requires `worktree_id` to construct the payload file path (used for trust injection delivery) and to populate `RecordMeta.worktree_id` in the written record. A `worktree_id` resolution failure blocks *delivery* of the trust triple, not *validation* of it — these are distinct failure modes.
```

- [ ] **Step 5: SY-25, SY-26 — Add diagnostic channel specification for guard failure paths**

At `enforcement.md:173` (containment failure mode), append: `Log to stderr.`

At `enforcement.md:179` (atomic write failure mode), append: `Log to stderr.`

Both follow the degraded-mode pattern at `enforcement.md:256` which explicitly says "Log the git error to stderr."

- [ ] **Step 6: SY-27 — Add session_id degraded mode**

At `enforcement.md:256` (after the worktree_id degraded mode bullets), add a new paragraph:
```
**`session_id` unavailability:** If `session_id` is unavailable from the Claude Code session context, branches 1 and 2 block (exit code 2) with diagnostic: `"engram_guard: session_id unavailable from session context — engine trust injection and direct-write authorization require session_id."` Branches 3 and 4 evaluate normally (no `session_id` dependency). Log to stderr.
```

- [ ] **Step 7: SY-28 — Clarify engram_register firing on blocked writes**

At `enforcement.md:17` (after the hooks table) or in the Ledger Multi-Producer Note section, add:
```
**Platform guarantee:** `engram_register` only fires when the underlying Write/Edit tool call completes. PostToolUse does not fire for tool calls blocked by PreToolUse exit code 2. A guard-blocked write does not produce a ledger event.
```

- [ ] **Step 8: SY-29 — Specify payload path argument protocol**

At `enforcement.md:177`, change:
```
The file path is passed to the engine via the Bash command's argument list (matching the proven ticket plugin pattern).
```
to:
```
The file path is the **final positional argument** in the engine's `sys.argv` (matching the proven ticket plugin pattern). No arguments may follow it. The engine must reject before mutation if the final argument is missing, unreadable, or not a valid payload file within the `.claude/engram-tmp/` containment boundary.
```

- [ ] **Step 9: SY-36 — Add Bash bypass recovery note for staging**

In the Protected-Path Enforcement section or Enforcement Scope section, add:
```
Staging files lacking a valid `staging-meta` comment (e.g., from a Bash write bypass) are treated as corrupt by `/curate` — skipped with a warning in `QueryDiagnostics.warnings`, excluded from the inbox count and cap enforcement.
```

- [ ] **Step 10: SY-38 — Fix Autonomy Model rationale for auto_audit**

At `enforcement.md:316` (Autonomy Model table, Work row), change the rationale from:
```
Trust boundary: agents propose, users approve
```
to:
```
Trust boundary: `suggest` — agents propose, users approve before write; `auto_audit` — agents create automatically, users review post-write via `/triage`
```

- [ ] **Step 11: SY-41 — Remove section count from quality validation scope**

At `enforcement.md:82` (quality validation scope table, snapshot row), change:
```
| `snapshot` | `~/.claude/engram/<repo_id>/snapshots/**` | Frontmatter completeness, section count |
```
to:
```
| `snapshot` | `~/.claude/engram/<repo_id>/snapshots/**` | Frontmatter completeness |
```

- [ ] **Step 12: SY-58 — Add engram_register failure mode for capability-inactive period**

In the Ledger Multi-Producer Note or the engram_register failure modes, add:
```
`engram_register` fires on all Write/Edit tool calls to protected paths regardless of guard state (including during capability-inactive delivery steps 0a–1). `/triage` audit-entry anomaly detection is the detection mechanism for registered writes during the capability-inactive period.
```

- [ ] **Step 13: SY-59 — Add engram_quality failure mode for absent tool_input.content**

At `enforcement.md:73` (after "Write: reads `tool_input.content` from the payload"), add:
```
If `tool_input.content` is absent or not a string, emit `[engram_quality:warn]: "snapshot write content unavailable in hook payload — quality check skipped"` and return exit code 0.
```

- [ ] **Step 14: SY-60 — Add cross-reference for SessionStart double-failure channel**

At `enforcement.md:286` (hooks table, `.engram-id` check row), change:
```
Warn if missing (diagnostic only — does not create)
```
to:
```
Warn if missing (diagnostic channel if worktree_id available; otherwise stderr — see [WorktreeID Resolution Failure](#worktreeid-resolution-failure)). Does not create.
```

- [ ] **Step 15: Verify enforcement.md consistency**

Check that all new text follows the spec's existing voice and references resolve correctly. Verify the Autonomy Model table changes are consistent with the operations.md work mode definitions.

- [ ] **Step 16: Commit**

```bash
git add docs/superpowers/specs/engram/enforcement.md
git commit -m "fix(spec): remediate 15 enforcement.md findings from spec review round 7

Add origin-matching rejection contract (SY-2), autonomy model authority
caption (SY-4), Branch 2 identity cross-ref (SY-5), trust triple scope
rationale (SY-8), diagnostic channels for guard failures (SY-25/26),
session_id degraded mode (SY-27), engram_register clarification (SY-28),
payload argument protocol (SY-29), bash bypass recovery (SY-36),
auto_audit rationale (SY-38), remove section count (SY-41), and
3 additional failure mode specs (SY-58/59/60)."
```

### Task 5: operations.md Completions (4 findings)

**Files:**
- Modify: `docs/superpowers/specs/engram/operations.md`

- [ ] **Step 1: SY-6 — Define Branch B1 rejection return structure**

At `operations.md:152` (Branch B1), change:
```
B1 (target_section unchanged): Reject — already promoted. Return existing details.
```
to:
```
B1 (target_section unchanged): Reject — already promoted. Return: `{"status": "already_promoted", "lesson_id": "<id>", "promoted_at": "<ISO8601>", "target_section": "<section>", "promoted_content_sha256": "<hex>"}`.
```

- [ ] **Step 2: SY-7 — Add Branch A invariants (no approval UI)**

At `operations.md:143-145` (Branch A description), after "No separate approval prompt.", add:
```
**Branch A invariants:** (1) `transformed_text` MUST be a faithful rendering of the selected lesson, differing only by required promotion markers — no content transformation beyond marker wrapping. (2) `target_section` is advisory; if the user later moves the promoted block to a different section, relocation is handled by Branch B2 on subsequent `/promote`.
```

- [ ] **Step 3: SY-9 — Clarify dedup-within-lock scope in operations.md**

At `operations.md:70` (the `/curate` mechanics paragraph), label the dedup-within-lock rule explicitly. Change:
```
The dedup check against published entries must occur within the same lock scope as the write
```
to:
```
**`/curate` publish dedup ordering (TOCTOU invariant):** The dedup check against published entries must occur within the same lock scope as the write
```

- [ ] **Step 4: SY-10 — Document single-session sequential guarantee for promote**

At `operations.md:394` (or nearby, in the CLAUDE.md section of Write Concurrency — note: this text is actually in types.md:394), find the sentence "Same-worktree concurrent promotion is not expected (single user, single session)." and expand it:
```
Same-worktree concurrent promotion is single-session sequential by runtime design — Claude Code sessions are sequential, and `/promote` is invoked interactively. The TOCTOU window between Step 1 (unlocked read) and Step 3 (locked write) is accepted under this invariant. Must revisit locking scope if parallel promote callers are introduced in a future platform change.
```

Note: this text may be in `types.md:394` rather than `operations.md`. Check both files. The normative location is whichever file contains "Same-worktree concurrent promotion is not expected."

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/specs/engram/operations.md docs/superpowers/specs/engram/types.md
git commit -m "fix(spec): remediate 4 operations/behavioral findings from spec review round 7

Define Branch B1 return structure (SY-6), add Branch A invariants
(SY-7), clarify dedup-within-lock scope label (SY-9), document
single-session sequential guarantee for promote (SY-10)."
```

### Task 6: storage-and-indexing.md Completions (2 findings)

**Files:**
- Modify: `docs/superpowers/specs/engram/storage-and-indexing.md`

- [ ] **Step 1: SY-53 — Clarify staged dedup lock scope**

At `storage-and-indexing.md` (or in `types.md` §Write Concurrency, wherever the dedup-within-lock rule is), add after the published-entries lock requirement:
```
Staged-file removal (cleaning staging files with identical `content_sha256` after publish) occurs after lock release — it does not affect `learnings.md` consistency. The staged-entries dedup check is advisory; the published-entries check within lock is the correctness boundary.
```

- [ ] **Step 2: SY-57 — Add IndexEntry population rules for staged entries**

At `storage-and-indexing.md:104` (after the RecordMeta field mapping table), add:
```markdown
**Staged entry IndexEntry population** (for entries from `knowledge_staging/`):

| Field | Source |
|---|---|
| `title` | First line of markdown body (after staging-meta comment) |
| `snippet` | Body first 200 chars (from markdown body, not JSON `content` field) |
| `status` | `"staged"` unconditionally |
| `tags` | Empty list |
| `schema_version` | `"staged"` (sentinel — not a real version; distinguishes from published entries) |
| `worktree_id` | `None` (private root, single-worktree by design) |
| `session_id` | `None` |
```

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/specs/engram/storage-and-indexing.md docs/superpowers/specs/engram/types.md
git commit -m "fix(spec): remediate 2 storage-and-indexing findings from spec review round 7

Clarify staged dedup lock scope (SY-53) and add IndexEntry population
rules for staged entries (SY-57)."
```

### Phase 2 Integration Commit

- [ ] **Squash Phase 2 commits**

After completing Tasks 3-6 and verifying all cross-references, squash the 4 task commits into a single Phase 2 commit:

```bash
git reset --soft HEAD~4
git commit -m "fix(spec): remediate 31 normative spec findings from review round 7

types.md (10): trace-only prohibition (SY-3), timestamp field (SY-12),
AuditEntry TypedDict + 6th version space (SY-24), zero-output obligation
(SY-34), engine append failures (SY-37), checkpoint frontmatter (SY-39),
record_kind values (SY-46), path normalization (SY-54), promote-meta
cross-validation (SY-55), index-only clarification (SY-56).

enforcement.md (15): origin-matching rejection contract (SY-2), autonomy
model caption (SY-4), Branch 2 cross-ref (SY-5), trust triple rationale
(SY-8), diagnostic channels (SY-25/26), session_id degraded mode (SY-27),
engram_register clarification (SY-28), payload protocol (SY-29), bash
bypass (SY-36), auto_audit rationale (SY-38), remove section count
(SY-41), 3 failure modes (SY-58/59/60).

operations.md (4): B1 return structure (SY-6), Branch A invariants
(SY-7), dedup scope label (SY-9), single-session guarantee (SY-10).

storage-and-indexing.md (2): staged dedup lock scope (SY-53), staged
IndexEntry population (SY-57)."
```

---

## Phase 3: Verification Spec Updates

### Task 7: delivery.md P1 Test Additions (8 findings)

**Files:**
- Modify: `docs/superpowers/specs/engram/delivery.md`

- [ ] **Step 1: SY-3 (test) — Add DistillEnvelope trace-only negative test**

Add to Step 2a or Step 3a Required Verification:
```
**VR-NEW-1 (DistillEnvelope trace-only regression):** Submit two `DistillEnvelope`s with different `idempotency_key` values but identical candidate content (same `content_sha256`). Assert: the second submission deduplicates via `O_CREAT|O_EXCL` (content-addressed), not via `idempotency_key` rejection. Assert: staging-meta does NOT contain `idempotency_key` field.
```

- [ ] **Step 2: SY-13 — Add Promote B2 Step 3 failure path test**

Add to Step 2a Required Verification:
```
**VR-NEW-2 (Promote B2 Step 3 failure):** Simulate Branch B2 Step 3 failure: mock the `promote-meta` write (after markers placed in Step 2) to raise OSError. Assert: Step 3 rejected, CLAUDE.md has new markers+text, promote-meta still has old `target_section`, and subsequent `/triage` reports `target_section_mismatch` anomaly.
```

- [ ] **Step 3: SY-14 — Add guard degraded-mode blocking test**

Add to Step 4a Required Verification:
```
**VR-NEW-3 (Guard degraded-mode blocking):** Mock `git rev-parse --git-dir` to fail. Invoke `engram_guard` with a Bash engine call (branch 1 path). Assert exit code 2 with diagnostic containing `"worktree_id unavailable"`. Separately, invoke with Write to a non-protected path (branch 4). Assert allowed. Verifies branches 1-2 block and branches 3-4 are unaffected.
```

- [ ] **Step 4: SY-15 — Add worktree_id collision diagnostic test**

Add to Step 0b or Step 4a Required Verification:
```
**VR-NEW-4 (worktree_id collision diagnostic):** Mock `sha256(git_dir_path.encode())[:16]` to return identical values for two distinct paths. Assert the diagnostic is surfaced (to stderr or `.diag`).
```

- [ ] **Step 5: SY-16 — Add multi-producer ledger interleave test**

Extend VR-4A-17:
```
**VR-4A-17 extension (engine+hook co-producer):** Spawn two producers simultaneously: (a) an engine producer appending `defer_completed` with payload and (b) a hook producer appending a `snapshot_written` event. Assert: both entries appear in shard, no partial writes, correct JSON per line, `producer` field distinguishes them.
```

- [ ] **Step 6: SY-17 — Add /timeline malformed timestamp test**

Add to Step 4a Required Verification:
```
**VR-NEW-5 (/timeline malformed timestamp):** Construct a JSONL shard with one valid entry and one entry with `ts: "not-a-timestamp"`. Run `/timeline`. Assert: both entries appear in output (malformed entry NOT dropped). Assert per-entry warning for the malformed entry. Assert malformed entry sorts before valid entries (epoch < any real timestamp).
```

- [ ] **Step 7: SY-18 — Add RecordRef.from_str() slash-in-record_id test**

Extend VR-0A-12:
```
**VR-0A-12 extension (slash in record_id):** `RecordRef.from_str("work/ticket/T-2026-03/01", repo_id)` → assert `subsystem="work"`, `record_kind="ticket"`, `record_id="T-2026-03/01"`. Verifies split-on-first-two-slashes rule.
```

- [ ] **Step 8: SY-19 — Add PromoteEnvelope content_sha256 divergence test**

Add to Step 2a Required Verification:
```
**VR-NEW-6 (content_sha256 divergence):** Create a `PromoteEnvelope` for lesson L. Edit the lesson body between Step 1 and Step 3 (simulating user edit). Run Step 3. Assert: promote-meta is written (not rejected), `promoted_content_sha256` matches the *current* (edited) content hash, and a warning is logged referencing the divergence.
```

- [ ] **Step 9: Commit (do not push yet — continue to Task 8)**

### Task 8: delivery.md Test Design Fixes (4 findings)

**Files:**
- Modify: `docs/superpowers/specs/engram/delivery.md`

- [ ] **Step 1: SY-20 — Fix VR-3A-9 AST scan coverage for OOP**

At the VR-3A-9 specification, add:
```
At least one mutating entrypoint must be verified by method (a) and at least one by method (b), to ensure both verification paths are exercised. If all entrypoints are class-based, method (b) is exclusive — document which entrypoint exercises each method.
```

- [ ] **Step 2: SY-21 — Fix SessionStart timing test to separate behavioral and performance**

At the VR-4A-3 specification, add:
```
Separate the timing assertion: (a) The 500ms *behavioral* requirement (cleanup runs without blocking) is verified in standard CI via a mock filesystem. (b) The 500ms *wall-clock* measurement is a performance test appropriately marked `@pytest.mark.slow`. The behavioral test verifies the algorithm; the slow test measures it on real hardware.
```

- [ ] **Step 3: SY-22 — Fix VR-4A-19 to use portable paths**

At the VR-4A-19 specification, replace hardcoded `/home/user/` paths with:
```
Use parameterized path construction: `Path(os.path.expanduser("~")) / ".claude" / "engram" / <repo_id> / "snapshots" / "test.md"`. The test should derive paths from `expanduser("~")` to be portable across macOS and Linux.
```

- [ ] **Step 4: SY-23 — Add version space coverage mapping**

At the cross-cutting verification table (delivery.md, "Version space coverage" row), add a mapping table:
```
**Version space coverage map:** envelope → VR-0A-3; record provenance → T1-gate-2; ledger format → VR-4A-22; knowledge entry → T1-gate-2; promotion state → VR-4A-21; work audit trail → VR-NEW (to be added with AuditEntry tests).
```

- [ ] **Step 5: Commit (do not push yet — continue to Task 9)**

### Task 9: delivery.md P2 Test Updates (6 findings)

**Files:**
- Modify: `docs/superpowers/specs/engram/delivery.md`

- [ ] **Step 1: SY-42 — Split VR-0A-16 to defer invalid subsystem test**

At the VR-0A-16 specification, split into: (a) `RecordRef(subsystem="")` → `ValueError` (testable now — empty string is always invalid). (b) Defer `RecordRef(subsystem="invalid")` test to the step when allowed value sets are resolved.

- [ ] **Step 2: SY-47 — Add cross-worktree learnings.md append test**

Add as optional integration test:
```
**VR-NEW-7 (cross-worktree append merge):** Append two independent `lesson-meta` entries in parallel to separate worktree copies of `learnings.md`. Confirm clean merge (no conflict markers).
```

- [ ] **Step 3: SY-48 — Add engram init --force with valid UUID test**

Extend VR-0B-1 with case (e):
```
**VR-0B-1 case (e):** `engram init --force` with valid `.engram-id` → specify behavior (refuse with warning: "this will change repo_id" or require `--yes` flag) and test it.
```

- [ ] **Step 4: SY-49 — Add save_recovery.json schema_version absence test**

Extend VR-4A-34:
```
Assert `"schema_version"` key is absent from the written `save_recovery.json`.
```

- [ ] **Step 5: SY-50, SY-51, SY-52 — Add test mechanism definitions and CI wiring**

For SY-50: Specify `HARNESS_EXCEPTIONS` mechanism: "Maintain a `HARNESS_EXCEPTIONS` list in `tests/compatibility/exceptions.py`. Each entry is `{fixture_name: str, reason: str}`. Harness asserts `len(HARNESS_EXCEPTIONS) <= 5`."

For SY-51: Add a note that VR-5-1 through VR-5-4 must be converted to pytest assertions and run in the same CI suite as VR-5-5.

For SY-52: Add a minimum fixture count requirement: "The triage must identify at least 50 compatibility-critical fixtures. If fewer than 50 are identified, the triage methodology must be reviewed."

- [ ] **Step 6: Commit**

```bash
git add docs/superpowers/specs/engram/delivery.md
git commit -m "fix(spec): remediate 18 delivery.md verification findings from review round 7

Add 8 new test specs for untested normative behaviors (SY-3t/13-19),
fix 4 test design issues (SY-20/21/22/23), and update 6 P2 test
specifications (SY-42/47/48/49/50-52)."
```

---

## Verification

After all three phases are complete:

- [ ] **Cross-reference spot check:** Verify all inbound links from the SY-1 and SY-11 fixes resolve to the new headings.
- [ ] **AuditEntry consistency:** Verify the new AuditEntry TypedDict in types.md matches the delivery.md harness assertions (fields, types).
- [ ] **Version spaces table:** Verify the Version Spaces table now has 6 entries.
- [ ] **Enforcement scope table:** Verify "section count" is removed from the quality validation scope table.
- [ ] **Design decision traceability:** Each of the 6 design decisions should be findable in the spec text by searching for their key phrases.

## Reference

- Review report: `.review-workspace/synthesis/report.md`
- Synthesis ledger: `.review-workspace/synthesis/ledger.md`
- Individual findings: `.review-workspace/findings/{reviewer-id}.md`
- Codex dialogue thread: `019d182a-8ed1-7ca0-8dba-874d9ee2f315`
