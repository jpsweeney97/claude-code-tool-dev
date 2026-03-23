# Engram Spec Remediation Plan — Round 9

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remediate 41 P0/P1 findings from engram spec review round 9 across 8 normative spec files.

**Architecture:** Three commits ordered by dependency: (1) P0 fixes + factual corrections, (2) design decisions + normative enforcement, (3) verification plan backfill. Each commit produces a self-consistent spec state. 27 P2 findings deferred.

**Tech Stack:** Markdown specification files in `docs/superpowers/specs/engram/`

---

**Source:** `.review-workspace/synthesis/report.md` (6-reviewer team, 2026-03-23)
**Scope:** 68 canonical findings (2 P0, 39 P1, 27 P2) across 10 spec files
**Spec:** `docs/superpowers/specs/engram/` (10 files, ~1350 lines)
**Dominant pattern:** enforcement underspecification (~21 findings), verification plan gaps (~22), schema table incompleteness (~14)
**Codex validation:** Thread `019d1914-496f-7ac3-86a6-743e83a5d4c1` — all 10 DD resolutions converged in 4 turns. Two proposals revised (DD-5 hard→best-effort, DD-7 raw count→auto_created-aware).

## Design Decisions

Ten behavioral gaps require design decisions. All validated by Codex dialogue.

### DD-1: Staged Sentinel Parsing Exemption (SY-4)

**Decision:** Add a sentinel exemption to the Version Evolution Policy, scoped to `RecordMeta.schema_version` only.

**Rationale:** The `"staged"` sentinel cannot be parsed as `<major>.<minor>`. The `"0.0"` value is already reserved for legacy pre-versioned entries (types.md line 580). Replacing `"staged"` with `"0.0"` would merge two orthogonal sentinel meanings. The exemption must NOT apply globally to all `schema_version` fields — ledger and audit trail version spaces have their own parsing rules where sentinels are not used.

**Spec changes:**
- types.md §Version Evolution Policy, after the Compatibility Rules table: Add: "**Sentinel exemption (record provenance only):** The `RecordMeta.schema_version` values `"staged"` and `"0.0"` are sentinel values exempt from `<major>.<minor>` parsing. Readers encountering a sentinel value MUST NOT apply same-major tolerance — route to sentinel-specific handling instead. `"staged"` identifies entries in the staging inbox (not yet published). `"0.0"` identifies pre-versioned legacy entries (see [Legacy Entries](#legacy-entries-missing-meta-version)). This exemption applies only to the record provenance version space. Ledger (`LedgerEntry.schema_version`) and audit trail (`AuditEntry.schema_version`) version spaces do not use sentinel values."
- delivery.md: Add to VR-NEW-9: "Include a test case with `RecordMeta.schema_version: "staged"` — assert reader routes to staging-specific handling, not same-major tolerance parsing."

### DD-2: collect_trust_triple_errors() Caller Obligation (CE-2)

**Decision:** Replace ambiguous "catch or suppress" language with a precise list-based obligation.

**Rationale:** The function returns `list[str]` and never raises. "Must not catch or suppress errors" implies exception-raising semantics, which is misleading. The actual obligation is: if the list is non-empty, reject. Codex confirmed the defensive contract against bare `except:` wrappers is valid, but the sentence should describe what the function actually does.

**Spec changes:**
- types.md §Trust Validation, replace the **Caller obligation** paragraph: "**Caller obligation:** If `collect_trust_triple_errors()` returns a non-empty list, the engine must reject the operation, surface those errors in the structured error response (joined with `'; '`), and make no state changes."

### DD-3: Promote Hash Unavailability — All-Branch Scope (CE-5)

**Decision:** Keep the condition scoped to all branches. Correct the rationale note.

**Rationale:** Step 3 always recomputes `drift_hash()` on the post-write marker-bounded text from CLAUDE.md, regardless of branch. The unavailability condition applies whenever Step 3 cannot locate the final text between markers. Codex identified that the C1/C2 rationale was wrong — unreadable markers is Branch C3, not C1/C2.

**Spec changes:**
- types.md §Promote Hash Verification, replace the existing unavailability paragraph with: "**If the exact post-write text is unavailable** (e.g., Step 2 wrote to CLAUDE.md but the skill cannot locate the final text between markers), Step 3 **must** reject the promote-meta write rather than persist a hash computed from pre-confirmation text. The lesson remains eligible for the next `/promote` run (same recovery as [Step 2 failure](operations.md#failure-handling)). This applies to any write branch because Step 3's hash source is always the post-write marker-bounded text."

### DD-4: Degraded Mode Branch-Specific Diagnostics (CE-10)

**Decision:** Add distinct diagnostic messages for branches 1 and 2, extended to both `worktree_id` and `session_id` unavailability.

**Rationale:** Same exit code (2) but different messages helps operators identify which code path is affected. Codex extended the pattern to `session_id` unavailability (enforcement.md line 285) to prevent the same ambiguity from surviving on the adjacent path.

**Spec changes:**
- enforcement.md §Degraded Mode, replace the combined diagnostic with branch-specific messages:
  - Branch 1: `"engram_guard degraded: worktree_id unavailable — {error}. Engine trust injection blocked."`
  - Branch 2: `"engram_guard degraded: worktree_id unavailable — {error}. Direct-write path authorization blocked."`
- enforcement.md §session_id unavailability, replace the combined diagnostic with:
  - Branch 1: `"engram_guard: session_id unavailable from session context. Engine trust injection blocked."`
  - Branch 2: `"engram_guard: session_id unavailable from session context. Direct-write path authorization blocked."`

### DD-5: SessionStart 500ms Budget — Best-Effort Target (IE-3)

**Decision:** Convert from hard bound to best-effort target with per-phase elapsed-time checks.

**Rationale:** `worktree_id` resolution is external process I/O (`git rev-parse --git-dir`) with no spec-level deadline. A hard `<500ms` bound is unfalsifiable when the first mandatory operation has unbounded latency. Codex countered the original 450ms bailout proposal — revised to per-phase elapsed-time checks that apply to all optional operations including `.engram-id` check.

**Spec changes:**
- enforcement.md §SessionStart Hook, replace `<500ms startup budget.` with: "`engram_session`: bounded and idempotent. Best-effort <500ms startup target."
- Add after the operations table: "**Aggregate elapsed-time guard:** Before each remaining optional SessionStart operation (snapshot cleanup, chain state cleanup, orphan payload cleanup, `.engram-id` check), check elapsed time since hook entry. If elapsed > 450ms, skip the remaining operations and log: `'engram_session: startup budget exceeded ({elapsed}ms). Remaining operations skipped — retry next session.'` This is fail-open and consistent with per-operation fail-open semantics. `worktree_id` resolution is mandatory and not subject to the elapsed-time guard (it runs first)."

### DD-6: Engine-Side Payload Containment (IE-5)

**Decision:** Add mandatory engine-side containment as defense-in-depth using `commonpath`.

**Rationale:** Without engine-side check, a pre-placed file outside `.claude/engram-tmp/` could be consumed if the guard is bypassed or the path argument is modified between guard write and engine read (TOCTOU). The engine check clarifies the already-implied obligation from enforcement.md line 189. Codex refined: use `os.path.commonpath()` or equivalent canonicalized containment, not `str.startswith()` (which has false-positive vulnerabilities like `engram-tmp-evil/`).

**Spec changes:**
- enforcement.md §Step 2 Validation, add before the `collect_trust_triple_errors()` paragraph: "**Payload containment (defense-in-depth):** Before reading the payload file, each engine must verify that `os.path.commonpath([os.path.realpath(payload_path), os.path.realpath(engram_tmp_dir)])` equals the canonicalized `engram-tmp` directory. If not, reject with: `'Trust triple rejected: payload path outside containment boundary: {path}'`. This precedes the file-exists check and the trust-triple validation. The guard remains the enforcement authority for containment; this engine-side check is defense-in-depth against TOCTOU between guard write and engine read."
- delivery.md: Add VR-3A-NEW-1 at Step 3a: "Engine invoked with payload path pointing to a file outside `.claude/engram-tmp/` (e.g., `../injected-trust.json`). Assert engine rejects with containment diagnostic before attempting trust-triple validation."

### DD-7: work_max_creates Counter — Audit Trail Counting (IE-10)

**Decision:** Count from `.audit/<session_id>.jsonl` at each invocation. Add `auto_created: bool` field to `AuditEntry`.

**Rationale:** The spec says "read at engine invocation time — no session-level caching" (enforcement.md line 377). Transient in-memory state would be inconsistent with this principle. Codex identified that `work_max_creates` limits automatic creates only (operations.md line 23-26), but the current `AuditEntry` lacks a field to distinguish automatic from user-approved creates. TOCTOU between count and create is a soft limit (consistent with staging cap model).

**Spec changes:**
- types.md §AuditEntry, add field: `auto_created: bool  # True for auto_audit-mode creates, False for user-approved creates`
- types.md §AuditEntry writer/reader split note, add: "The `auto_created` field was added in minor version `1.1`. Same-major readers encountering entries without `auto_created` MUST treat them as `auto_created: True` (conservative — counts toward cap). Writers at version `1.1`+ MUST emit `auto_created`."
- types.md §Version Spaces table, update Work audit trail format current version from `"1.0"` to `"1.1"`.
- enforcement.md §Autonomy Model, add after `work_max_creates` config line: "**Counter mechanism:** The Work engine counts `auto_created: True` entries in `.audit/<session_id>.jsonl` at each invocation to enforce `work_max_creates`. No transient counter or session-scoped state file is required. Reset is implicit — a new session has a new `session_id` with no audit entries. TOCTOU between count and create is a soft limit, consistent with the staging inbox cap model."

### DD-8: Cross-User Home Expansion (IE-14)

**Decision:** Document as unsupported with simplified wording.

**Rationale:** Engram uses `os.path.expanduser()` for `~` expansion, which resolves against the invoking process's HOME. Cross-user scenarios are out of scope. Codex refined: optional warning should not be normative unless detection is precisely defined.

**Spec changes:**
- enforcement.md §Protected-Path Enforcement, add after the path canonicalization paragraph: "All `~` paths resolve against the invoking process's home directory (`os.path.expanduser()`). Cross-user invocation (where a different user's Claude session accesses Engram data owned by another user) is unsupported and out of scope for this spec."

### DD-9: Staged Entry Snippet Excludes Title (SP-2)

**Decision:** Snippet starts after the title line.

**Rationale:** The `title` field already captures the first line of the markdown body. Including it in `snippet` would be redundant. Codex added precision about newline removal.

**Spec changes:**
- storage-and-indexing.md §Staged entry IndexEntry population table, replace the `snippet` row value: "First 200 chars of markdown body, starting from the remainder after removing the line used for `title`. If no remainder exists after the title line, `snippet` is empty string."

### DD-10: Ledger source_ref Always Required (SP-8)

**Decision:** `source_ref` is always required in `defer_completed` and `distill_completed` payloads. Reader handles missing/malformed as producer bug.

**Rationale:** `source_ref` identifies which envelope/operation was attempted, regardless of outcome. When `emitted_count == 0`, it tells `/triage` what was attempted but produced nothing. Codex added reader-side handling: missing or malformed `source_ref` is treated as a producer bug — skip the event with a warning, do not use for completion inference or causal linking.

**Spec changes:**
- types.md §Event Vocabulary, add after the payload schema for `defer_completed`/`distill_completed`: "Both `source_ref` and `emitted_count` are required fields. `source_ref` identifies the attempted operation; `emitted_count` reports the outcome. If a reader encounters an event with missing or malformed `source_ref`, treat the event as a producer bug: skip with a warning in `QueryDiagnostics.warnings`. Do not use the event for completion inference or causal linking."

---

## Strategy

Three commits, ordered by dependency and priority:

1. **P0 + factual corrections (Commit 1)** — the two P0 enforcement mandate fixes plus 7 factual/cross-reference corrections. Must land first because they fix wrong facts that downstream fixes depend on.
2. **Design decisions + normative enforcement (Commit 2)** — 10 design decisions applied plus 9 additional normative P1 fixes. Depends on Commit 1 for correct base text.
3. **Verification backfill (Commit 3)** — 13 P1 verification plan items in delivery.md. Depends on Commits 1–2 for finalized normative claims.

**P2 findings (27)** are deferred to a separate remediation session.

---

## Commit 1 — P0 + Factual Corrections

**Finding count:** 2 P0 + 7 P1 = 9 findings
**Files:** enforcement.md, delivery.md, storage-and-indexing.md, operations.md

### P0 Findings

#### [SY-1] Origin-matching enforcement mandate gap

**Corroboration:** Independent convergence (VR-1, CE-1, IE-2, CE-13)
**Files:** enforcement.md, delivery.md

- [ ] **Fix — enforcement.md §Per-entrypoint rejection contract:** Replace "Each entrypoint should use the shared helper function `validate_origin_match(expected, actual)`" with: "Each entrypoint MUST use the shared helper function `validate_origin_match(expected, actual)`. Inline reimplementation of origin-matching logic is prohibited — the shared helper is the single enforcement primitive."

- [ ] **Fix — delivery.md VR-3A-14:** Expand the test specification. After the existing rejection assertion, add: "Additionally, assert the error message matches the stable format: `'hook_request_origin: expected {expected!r} for this entrypoint, got {actual!r}'`. A regex match on the format template is sufficient — the assertion must verify both the field name and the quoting pattern, not just that rejection occurred."

#### [SY-2] Protected-path table missing context row for register scope

**Corroboration:** Cross-lens followup (CE-7, IE-16)
**Files:** enforcement.md

- [ ] **Fix — enforcement.md §Protected-Path Enforcement table:** Add fourth row:

| Path Class | Protected Paths | Allowed Mutators | Register Fires? |
|---|---|---|---|
| `context_private` | `~/.claude/engram/<repo_id>/snapshots/**`, `checkpoints/**` | Direct-write path authorization (branch 2) | No (branch 2 — register excluded by design) |

### Factual Corrections

#### [CC-1] VR-3A-22 uses wrong field name

**Files:** delivery.md
- [ ] **Fix:** In VR-3A-22, replace all occurrences of `source_file` with `key_file_paths`.

#### [CC-2] Wrong staging path in bridge-period note

**Files:** storage-and-indexing.md
- [ ] **Fix:** In the bridge-period accepted-gap note, replace `engram/knowledge/staging/` with `~/.claude/engram/<repo_id>/knowledge_staging/`.

#### [CC-3] Provenance list omits timestamp

**Files:** enforcement.md
- [ ] **Fix — enforcement.md §Direct-Write Path Authorization, step 4:** Replace the field list `schema_version, session_id, worktree_id, orchestrated_by` with `schema_version, session_id, worktree_id, timestamp` and add note: "`orchestrated_by` is included when applicable (per [types.md §Snapshot Orchestration Intent](types.md#snapshot-orchestration-intent))."

#### [SY-3] Work Ticket YAML Schema missing required fields

**Corroboration:** Independent convergence (CC-11, CE-14, SP-3, SP-10, VR-22)
**Files:** storage-and-indexing.md
- [ ] **Fix:** Add two rows to the Work Ticket YAML Schema table:

| Field | Type | Required | Description |
|---|---|---|---|
| `session_id` | `str` | Required | Claude session UUID. Maps to `RecordMeta.session_id`. |
| `schema_version` | `str` | Required | Record provenance version (e.g., `"1.0"`). Maps to `RecordMeta.schema_version`. |

#### [SY-5] Gated mode authority misplacement

**Corroboration:** Independent convergence (AA-2, CE-9, CC-15)
**Files:** enforcement.md, operations.md
- [ ] **Fix — operations.md §Work Mode Definitions:** Add `gated` mode definition: "**gated:** Knowledge staging requires explicit user confirmation before staging-meta is written. The Knowledge engine presents candidates and waits for approval. Used for the Knowledge staging inbox. `gated` mode is independent of Work modes (`suggest`, `auto_audit`)."
- [ ] **Fix — enforcement.md §Autonomy Model table:** Remove behavioral descriptions from the Rationale column. Replace with enforcement-relevant labels only (e.g., "See operations.md §Work Mode Definitions"). Remove the redundant second deferral statement after the table (CC-15).

#### [AA-1] Guard Capability Rollout table carries implementation_plan claims

**Files:** enforcement.md, delivery.md
- [ ] **Fix:** Add cross-reference note to enforcement.md §Guard Capability Rollout table: "The 'Ships At' column mirrors delivery.md §Build Sequence for convenience. delivery.md is the `implementation_plan` authority — if the two diverge, delivery.md is authoritative."

#### [IE-1] Guard branch-2 ordering comment misleading

**Files:** enforcement.md
- [ ] **Fix — enforcement.md §Guard Decision Algorithm:** Replace "Step 2 failing (not Context-owned) routes to step 3." with: "Step 2 failing the Context-ownership check (path not within Context private root) silently falls through — execution continues to step 3 (protected-path check) or step 4 (allow unconditionally)."

- [ ] **Commit**

```
git add docs/superpowers/specs/engram/enforcement.md docs/superpowers/specs/engram/delivery.md docs/superpowers/specs/engram/storage-and-indexing.md docs/superpowers/specs/engram/operations.md
git commit -m "fix(spec): remediate 2 P0 and 7 factual correction findings from review round 9

Fixes SY-1 (origin-matching MUST mandate + VR-3A-14 stable string assertion),
SY-2 (protected-path table context row), CC-1 (VR-3A-22 field name),
CC-2 (staging path), CC-3 (provenance timestamp), SY-3 (Work ticket YAML
schema fields), SY-5 (gated mode authority), AA-1 (Ships At cross-reference),
IE-1 (branch-2 comment)."
```

---

## Commit 2 — Design Decisions + Normative Enforcement

**Finding count:** 10 DDs + 9 normative P1s = 19 findings
**Files:** types.md, enforcement.md, storage-and-indexing.md, delivery.md

### Design Decision Fixes

- [ ] Apply DD-1 through DD-10 as specified in the Design Decisions section above.

**Files touched:** types.md (DD-1, DD-2, DD-3, DD-7, DD-10), enforcement.md (DD-4, DD-5, DD-6, DD-8), storage-and-indexing.md (DD-9), delivery.md (DD-1 VR-NEW-9 extension, DD-6 VR-3A-NEW-1).

### Additional Normative P1 Fixes

#### [CE-3] Payload containment scope description misleading

**Files:** enforcement.md
- [ ] **Fix — enforcement.md §Payload File Contract, Containment row:** Add clarification: "The containment check validates the path `engram_guard` itself constructs (catching internal implementation bugs such as path traversal in path construction), not external injection. The check is scoped to Branch 1 — only engine Bash invocations trigger containment validation."

#### [CE-4] Enforcement exceptions table restatement creates drift risk

**Files:** enforcement.md
- [ ] **Fix — enforcement.md §Enforcement Exceptions table:** Collapse the Rationale column to pointers. Replace independent prose with: "See foundations.md §Permitted Exceptions" for each row. Remove any behavioral elaboration that is not in foundations.md — enforcement.md should reference, not restate.

#### [CE-8] Branch B2 Step 3 missing precondition check

**Files:** types.md
- [ ] **Fix — types.md §promote-meta, Branch B2 description:** Add precondition: "Before updating `target_section`, the scan-and-replace verifies the entry's current `target_section` differs from the user-confirmed value. If they already match, Branch B2 is a no-op (Branch B1 rejection applies instead)."

#### [IE-4] engram_quality Edit-path frontmatter parse failure unspecified

**Files:** enforcement.md
- [ ] **Fix — enforcement.md §Quality Validation:** Add: "If the file is readable but frontmatter is unparseable (no `---` delimiter, malformed YAML), emit `'[engram_quality:warn] snapshot frontmatter unparseable: {reason}'` and return exit code 0. Treat as a missing-field warning, not a hook failure."

#### [IE-8] Degraded mode + inactive capability swallows worktree_id failures

**Files:** enforcement.md
- [ ] **Fix — enforcement.md §Inactive capability behavior:** Add: "Even when a capability is inactive, if `identity.get_worktree_id()` returns an error, the guard MUST log the git error to stderr. Diagnostic emission is independent of capability activation. This ensures git state problems are surfaced during the capability-inactive delivery period."

#### [IE-9] Write/Edit path canonicalization failure mode unspecified

**Files:** enforcement.md
- [ ] **Fix — enforcement.md §Protected-Path Enforcement, path canonicalization paragraph:** Add: "If canonicalization of a Write/Edit target path fails (broken symlink, permission denied), `engram_guard` blocks the operation (exit code 2) with diagnostic: `'engram_guard: path canonicalization failed for {raw_path}: {error}'`. Fail-closed — a path that cannot be resolved is treated as potentially protected."

#### [SP-1] DistillEnvelope idempotency_key staging exclusion not co-located

**Files:** types.md
- [ ] **Fix — types.md §Staging File Format:** Add after the field list: "The `DistillEnvelope.header.idempotency_key` MUST NOT be included in staging-meta. Its omission is an active constraint — see [§Idempotency Enforcement Per Envelope Type](#idempotency-enforcement-per-envelope-type)."

#### [SP-4] PromoteEnvelope.content_sha256 byte-range not anchored

**Files:** types.md
- [ ] **Fix — types.md §PromoteEnvelope, `content_sha256` field:** Replace description with: "`content_hash(lesson_content)` at envelope creation time, where `lesson_content` is the same byte range used for `lesson-meta.content_sha256` — see [§Knowledge Entry Format](types.md#knowledge-entry-format--lesson-meta-contract). Must equal `lesson-meta.content_sha256` if no edit occurred between publication and promotion."

#### [SP-7] Promote-meta lock scope ambiguity

**Files:** types.md
- [ ] **Fix — types.md §promote-meta, Uniqueness Invariant:** Add: "The promote-meta scan-and-replace and the publish path are never concurrent within the same engine call. Step 3 (promote-meta write) runs as a distinct operation from any publish path run. Both acquire `fcntl.flock(LOCK_EX)` on `learnings.md.lock` independently."

- [ ] **Commit**

```
git add docs/superpowers/specs/engram/types.md docs/superpowers/specs/engram/enforcement.md docs/superpowers/specs/engram/storage-and-indexing.md docs/superpowers/specs/engram/delivery.md
git commit -m "fix(spec): apply 10 design decisions and 9 normative P1 fixes from review round 9

Design decisions: DD-1 sentinel exemption, DD-2 caller obligation rewrite,
DD-3 promote hash all-branch scope, DD-4 branch-specific diagnostics,
DD-5 best-effort 500ms budget, DD-6 engine containment defense-in-depth,
DD-7 auto_created AuditEntry field, DD-8 cross-user unsupported,
DD-9 snippet excludes title, DD-10 source_ref always required.

Additional fixes: CE-3 containment scope, CE-4 exceptions table pointers,
CE-8 B2 precondition, IE-4 Edit frontmatter parse, IE-8 inactive-capability
git logging, IE-9 Write/Edit canonicalization fail-closed, SP-1 idempotency_key
exclusion, SP-4 content_sha256 byte-range, SP-7 lock scope."
```

---

## Commit 3 — Verification Backfill

**Finding count:** 13 P1 findings
**Files:** delivery.md

All fixes below are additions or extensions to existing VR items in delivery.md.

#### [VR-2] Trust triple call-site test excludes Knowledge Step 2a entrypoints

- [ ] **Fix:** Add Step 2a verification: "VR-2A-NEW-1: Assert `collect_trust_triple_errors()` is invoked at every Knowledge mutating entrypoint (publish, staging write, promote-meta write) using the same dual-method approach as VR-3A-9. Knowledge entrypoints ship at Step 2a — this verification must not be deferred to Step 3a."

#### [VR-3] No .engram-id ordering test for Knowledge engine

- [ ] **Fix:** Add Step 2a verification: "VR-2A-NEW-2: For each Knowledge mutating entrypoint, invoke with `.engram-id` absent. Assert the entrypoint returns the initialization error *before* attempting trust-triple validation. Verify ordering: `.engram-id` check → trust triple validation."

#### [VR-4] content_sha256 byte-range boundary not exercised

- [ ] **Fix:** Extend VR-0A-14: "Add parametric boundary tests: (a) content ending with trailing blank lines — assert `content_hash` excludes them per the byte-range rule, (b) content with exactly one trailing newline — assert stable hash, (c) content with no trailing newline — assert `knowledge_normalize` adds one before hashing."

#### [VR-5] No VR item verifies engines emit emitted_count=0 on zero-output

- [ ] **Fix:** Add Step 4a verification: "VR-4A-NEW-1: Submit a `DeferEnvelope` that would be deduplicated (same `idempotency_key` as existing ticket). Assert the Work engine emits a `defer_completed` ledger event with `emitted_count: 0`. Same test for `DistillEnvelope` where all candidates are deduped via `content_sha256` — assert `distill_completed` with `emitted_count: 0`."

#### [VR-7] Staging content JSON-vs-body divergence warning untested

- [ ] **Fix:** Add Step 2a verification: "VR-2A-NEW-3: After staging a lesson via `/distill`, manually modify the staging file's JSON `content` field (without changing the markdown body). Run `/curate`. Assert a per-entry warning in `QueryDiagnostics.warnings` for the body-vs-JSON divergence. Assert `IndexEntry.snippet` is derived from the markdown body (not the modified JSON `content`)."

#### [VR-8] Promote-meta uniqueness invariant — no concurrent test

- [ ] **Fix:** Add Step 2a verification: "VR-2A-NEW-4: Invoke two concurrent `/promote` calls for the same `lesson_id`. Assert exactly one succeeds and one either (a) detects the existing `promote-meta` via Branch B1 rejection, or (b) blocks on `flock` and completes after the first — but in no case are two `promote-meta` entries written for the same `lesson_id`."

#### [VR-9] VR-4A-5 Branch B2 target_section assertion underspecified

- [ ] **Fix:** Amend VR-4A-5: "After Branch B2 completes, assert `promote-meta.target_section` equals the user-confirmed new section value (not the pre-update value). The assertion must verify the specific field, not just that the operation completed."

#### [VR-12] session_id unavailability guard behavior untested

- [ ] **Fix:** Extend VR-NEW-3: "Add test case: mock `session_id` as unavailable from the Claude Code session context. Assert branches 1 and 2 block (exit code 2) with diagnostic containing `'session_id unavailable'`. Assert branches 3 and 4 evaluate normally (no `session_id` dependency)."

#### [VR-13] All-opaque .diag file triage behavior untested

- [ ] **Fix:** Extend VR-4A-31: "Add edge case: `.diag` file where ALL entries have unrecognized `schema_version` (all treated as opaque). Assert `/triage` surfaces `'ledger unavailable in session <session_id>'` — the conservative approach. A non-empty `.diag` file implies hook failures occurred."

#### [VR-15] Normalizer call-site audit missing

- [ ] **Fix:** Add Step 2a verification: "VR-2A-NEW-5: Mock each normalizer (`knowledge_normalize`, `work_normalize`, NFC+LF) to return a tagged output that identifies which normalizer ran. For each hash call-site (`content_hash`, `drift_hash`, `work_dedup_fingerprint`), assert the correct normalizer was invoked. A swapped normalizer produces different hashes silently — this call-site audit catches the swap."

#### [VR-17] record_ref non-null assertion untested for snapshot_written

- [ ] **Fix:** Add Step 4a verification: "VR-4A-NEW-2: Emit a `snapshot_written` event where `payload.ref` is `None`. Assert the producer skips the append with a diagnostic warning (does not append an entry with `record_ref: None`). Separately, process a `snapshot_written` entry that somehow has `record_ref: None` in the ledger — assert the reader skips it with a warning in `QueryDiagnostics.warnings`."

#### [VR-19] Staged entry snippet body-vs-JSON source untested

- [ ] **Fix:** Add Step 2a verification: "VR-2A-NEW-6: Stage a lesson where the markdown body and JSON `content` field have different first 200 characters (by manually modifying the JSON after staging). Assert `IndexEntry.snippet` is derived from the markdown body, not the JSON field. This verifies the 'MUST NOT drive display output' constraint on the JSON `content` field."

#### [CC-8] Version space coverage gap for Knowledge RecordMeta

- [ ] **Fix:** Extend VR-NEW-9: "Include a Knowledge-subsystem test fixture: `lesson-meta` with `meta_version: "2.0"` (future major). Assert `RecordMeta.schema_version` derivation from `lesson-meta.meta_version` produces `"2.0"`. Assert reader skips entry per same-major tolerance rule with warning."

- [ ] **Commit**

```
git add docs/superpowers/specs/engram/delivery.md
git commit -m "fix(spec): backfill 13 verification plan items from review round 9

VR-2 (Knowledge trust triple at Step 2a), VR-3 (.engram-id ordering for
Knowledge), VR-4 (content_sha256 byte-range boundary), VR-5 (emitted_count=0
producer), VR-7 (staging content divergence), VR-8 (concurrent promote-meta),
VR-9 (B2 target_section assertion), VR-12 (session_id degraded guard),
VR-13 (all-opaque .diag triage), VR-15 (normalizer call-site audit),
VR-17 (record_ref non-null snapshot_written), VR-19 (staged snippet source),
CC-8 (Knowledge version space coverage)."
```

---

## Parked — P2 (27 findings)

Deferred to a separate remediation session after P0/P1 is complete:

| ID | Title | Reviewer |
|----|-------|----------|
| AA-3 | spec.yaml operations description omits Work Mode content | AA |
| AA-4 | README authority table descriptions diverge from spec.yaml | AA |
| CE-6 | worktree_id payload path claim inconsistency | CE |
| CE-9 | Autonomy Model table behavioral descriptions (merged into SY-5 for P1 fix; residual P2 cleanup) | CE |
| CE-11 | Ledger payload validation mechanism unspecified | CE |
| CE-12 | engram_quality Edit-path field scope underspecified | CE |
| CC-4 | README omits promote-meta from data-contract description | CC |
| CC-6 | docs/learnings/ source path inconsistency | CC |
| CC-14 | Staged snippet cross-reference to types.md missing | CC |
| CC-15 | Dual deferral statement (merged into SY-5 for P1 fix; residual cleanup) | CC |
| VR-6 | 24h window boundary test precision | VR |
| VR-10 | parse_sha256_hex bridge-period deprecation test | VR |
| VR-11 | knowledge_normalize tilde fence test coverage | VR |
| VR-14 | Migration manifest exclusivity assertion | VR |
| VR-16 | VR-0A-16b untethered stub — assign or defer | VR |
| VR-18 | Compatibility harness CI timing assertion | VR |
| VR-20 | Payload field access pattern assertion | VR |
| SP-5 | AuditEntry Literal serialization guarantee | SP |
| SP-6 | idempotency_key bridge-period format scope | SP |
| SP-9 | Fence info string backtick edge case | SP |
| SP-11 | save_recovery.json upgrade path | SP |
| SP-12 | Rule 11 vs rule 10 precedence at unclosed fence | SP |
| SP-14 | drift_hash empty string Branch C2 consequence | SP |
| IE-6 | engram_register during capability-inactive steps | IE |
| IE-7 | Double-failure detection path | IE |
| IE-11 | Staging trust_triple_present field reference | IE |
| IE-12 | Enforcement exceptions table divergence risk | IE |
| IE-13 | Orphan payload accumulation reporting | IE |
| IE-15 | Checkpoint source_skill value validation | IE |
