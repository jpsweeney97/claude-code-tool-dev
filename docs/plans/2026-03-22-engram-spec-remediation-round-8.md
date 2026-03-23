# Engram Spec Remediation Plan — Round 8

**Source:** `.review-workspace/synthesis/report.md` (6-reviewer team, 2026-03-22)
**Scope:** 58 canonical findings (1 P0, 38 P1, 19 P2) across 10 spec files
**Spec:** `docs/superpowers/specs/engram/` (10 files, ~1350 lines)
**Dominant pattern:** verification coverage gaps (~20 findings), enforcement surface edge cases (~16), schema precision (~9)
**Codex validation:** Thread `019d18b2-f7be-7a30-84a5-e1ce0c4f9da3` — all 15 T2/T3 resolutions converged in 5 turns. Four proposals revised (SP-4, CE-4, IE-2, VR-13).

## Design Decisions

Seven behavioral gaps (T3) require design decisions. All validated by Codex dialogue.

### DD-1: Suggest Mode Trust Injection (CE-2)

**Decision:** Trust injection applies in `suggest` mode, same as `auto_audit`.

**Rationale:** `engram_guard` fires at PreToolUse on the Bash engine invocation, before the engine determines mode. The guard is mode-agnostic (enforcement.md line 335). The "no write is performed" language (operations.md line 25) refers to the target artifact, not to trust injection infrastructure.

**Spec changes:**
- operations.md §Work Mode Definitions: Add to `suggest`: "Trust injection applies — `engram_guard` validates the trust triple on the engine invocation regardless of mode. In suggest mode, abandonment prevents the target artifact write; the guard/engine plumbing still performs transient private-root writes."

### DD-2: Write-Tool Skill Ledger Emission (CE-4)

**Decision:** Library function call (`engram_core.ledger.append_event()`), not a new engine entrypoint.

**Rationale:** Context paths are intentionally outside the protected-path model (enforcement.md line 63). A new mutating entrypoint would require capability matrix, protected-path, and entrypoint inventory changes — all unnecessary. `/quicksave` calls the library function after successful Write. Failure semantics: single best-effort append attempt (not "exactly once"). Ledger append failure never invalidates a successful write (types.md Write Semantics).

**Spec changes:**
- operations.md §Snapshot Event Emission: Add: "Skills that write via the Write tool (not engine Bash) emit ledger events by calling `engram_core.ledger.append_event()` after the Write tool call succeeds. This is an orchestrator-produced event, not a new mutating entrypoint. Failure to append does not invalidate the write — emit a warning in `QueryDiagnostics.warnings`."
- types.md §Write Semantics: Add: "The `append_event()` function is a single best-effort append attempt. Callers do not retry."

### DD-3: engram_register Capability-Inactive Semantics (IE-4)

**Decision:** Document as independent hook, quiescent during early steps.

**Rationale:** `engram_register` is not capability-gated and fires unconditionally from Step 0a+. During early steps, it is quiescent because no protected paths are populated yet, not broken. `/triage` anomaly detection applies only to writes that target roots already defined and reachable.

**Spec changes:**
- enforcement.md §Ledger Multi-Producer Note: Add scoping note: "During capability-inactive steps (0a–1), `engram_register` fires but detects no protected-path writes (no roots populated). `/triage` anomaly detection applies only to writes targeting roots defined in the current delivery step."

### DD-4: session_id Sourcing (IE-9)

**Decision:** Document as platform-provided hook invocation context.

**Rationale:** The spec prohibits env vars and shared state files. The concrete API is platform-defined and out of scope for this spec. Wording avoids "runtime environment" (too close to forbidden env vars).

**Spec changes:**
- enforcement.md §Inter-Hook Runtime State: Add: "`session_id` is obtained from the Claude Code hook invocation context provided by the runtime. The transport mechanism is platform-defined and out of scope for this spec. If unavailable, branches 1 and 2 block (exit code 2); branches 3 and 4 evaluate normally."

### DD-5: engram_session Self-Failure (IE-15)

**Decision:** Document as entirely fail-open by design.

**Rationale:** `engram_session` and `engram_guard` are operationally independent hooks. SessionStart operations (snapshot cleanup, chain state cleanup, orphan payload cleanup, verify .engram-id) are all fail-open. No SessionStart operation feeds into `engram_guard` enforcement decisions.

**Spec changes:**
- enforcement.md §SessionStart Hook: Add explicit invariant: "`engram_session` operations are fail-open; no SessionStart operation blocks a session from starting. `engram_session` and `engram_guard` are operationally independent — SessionStart failures do not affect guard enforcement decisions."

### DD-6: engram init --force with Valid .engram-id (VR-10)

**Decision:** Require `--yes` flag for valid overwrite.

**Rationale:** Overwriting a valid `.engram-id` changes the `repo_id`, which breaks cross-session record continuity. A destructive action should require explicit confirmation.

**Spec changes:**
- delivery.md VR-0B-1(e): Replace "specify and test the chosen behavior: either refuse... or require an additional `--yes` flag" with: "`engram init --force` with a valid `.engram-id` → assert the command refuses with warning 'this will change repo_id; use --force --yes to confirm'. `engram init --force --yes` with a valid `.engram-id` → assert the file is overwritten with a new UUIDv4."
- skill-surface.md §engram init: Add `--force --yes` to the flags description.

### DD-7: IndexEntry.updated_at Source (SP-5)

**Decision:** Filesystem mtime with None fallback.

**Rationale:** v1 is strictly local-filesystem-only, making `os.stat().st_mtime` the correct and complete source. `None` when `stat()` fails (file deleted between index build and access).

**Spec changes:**
- storage-and-indexing.md §RecordMeta Field Mapping: Add `updated_at` row to the mapping table for all subsystems: "Source: `os.stat(native_path).st_mtime` as UTC datetime. `None` if stat fails."

---

## Strategy

Three commits, ordered by dependency and priority:

1. **P0 + contradictions (T1 + T2)** — the version space count fix plus all 8 internal contradictions. Must land first because contradictions block correct enforcement and verification work downstream.
2. **Behavioral gaps + authority/schema (T3 + T4)** — 7 design decisions plus 10 mechanical authority/schema fixes. Depends on commit 1 for resolved contradiction context (CE-3, IE-2).
3. **Enforcement surface + verification backfill (T5 + T6)** — 5 enforcement edge cases plus 11 missing/underspecified tests. Depends on commits 1–2 for correct spec state before writing tests.

**P2 findings (19)** are deferred to a separate remediation session after P0/P1 is complete.

---

## Commit 1 — P0 + Contradictions (T1 + T2)

**Finding count:** 1 P0 + 8 P1 = 9 findings
**Files:** delivery.md, types.md, enforcement.md, foundations.md

### P0 Finding

#### [SY-1] Version space count mismatch — AuditEntry has zero verification coverage

**Corroboration:** Independent convergence (AA-1 + CC-1 + VR-1)
**Files:** delivery.md, types.md
**Fix — delivery.md §Cross-Cutting Verification:** Change "All 5 version spaces (envelope, record provenance, ledger format, knowledge entry, promotion state)" to "All 6 version spaces (envelope, record provenance, ledger format, knowledge entry, promotion state, work audit trail)."

**Fix — delivery.md:** Add VR-NEW-8 (AuditEntry version handling) at Step 3a Required Verification:
- VR-NEW-8: JSONL shard with three `AuditEntry` entries — `schema_version: "1.0"` (current), `"2.0"` (future major), `"1.1"` (same-major minor). Assert reader returns entries 1 and 3; entry 2 skipped without exception, warning in `QueryDiagnostics.warnings`.

### Contradiction Resolutions

#### [CE-1] PromoteEnvelope idempotency mechanism misdescribed

**Files:** types.md
**Resolution:** Fix types.md to match operations.md Branch B1 (operations.md is behavior_contract authority).
**Fix:** Update the PromoteEnvelope row in §Idempotency Enforcement Per Envelope Type. Replace "Engine checks `idempotency_key` against `promote-meta` state" with: "State-machine re-entry detection via content-hash comparison (implemented by Branch B1: `promoted_content_sha256 == current content_sha256`). The `idempotency_key` is computed and present in `EnvelopeHeader` but is not compared against `promote-meta`."
**Codex note:** Semantic-first wording preferred. The Branch B1 reference is acceptable because types.md line 346 already references it in the rationale column.

#### [CE-3] work_path_enforcement Bridge Period scope contradiction

**Files:** enforcement.md
**Resolution:** Update Bridge Period text to match capability table (enforcement.md is enforcement_mechanism authority, table is the normative definition).
**Fix:** In §Bridge Period Limitations, replace "Step 3a extends the guard with `work_path_enforcement` for Work paths" with: "Step 3a extends the guard with `work_path_enforcement` for Write/Edit blocking on both Work and Knowledge protected paths."

Add accepted-gap statement: "During Steps 2a–3a, Write/Edit to Knowledge protected paths is not blocked by branch 3 — only engine-Bash invocations are covered by `engine_trust_injection`. Direct Write/Edit to `engram/knowledge/**` is allowed unconditionally via branch 4 (allow). This gap is accepted because Knowledge skills in this window use the Bash engine path exclusively."

#### [IE-2] Guard degraded-mode branch 2 contradiction

**Files:** enforcement.md
**Resolution:** Clarify execution ordering — capability check is branch-local, degraded mode is hook-global. Capability check happens FIRST within each branch.
**Fix:** Rewrite §Degraded-Mode behavior. Replace "Branches 1 and 2 block (exit code 2)" with: "Degraded-mode blocking applies only to active branches that require the degraded resource. When a capability is inactive (no-op), degraded-mode blocking for that branch does not apply — the branch skips itself before checking degraded-dependent state."

Add explicit ordering sentence: "Within each branch, the capability-active check executes first. If the capability is inactive, the branch is a no-op regardless of degraded-mode state. If the capability is active and the required resource (e.g., `worktree_id`) is unavailable, the branch blocks."
**Codex note:** The spec's architecture is coherent — the contradiction was in the prose, not the design. A truth table is recommended for implementer clarity.

#### [VR-13] VR-3A-9 AST-scan method (a) contradiction

**Files:** delivery.md
**Resolution:** Rewrite dual-method requirement as suite-level precedence rule, not per-entrypoint.
**Fix:** Replace VR-3A-9's absolute dual-method sentence with: "The test suite MUST exercise both method (a) and method (b) across all 6 mutating entrypoints. Method (a) — AST scan — is applicable only to single-function entrypoints where both calls appear in the same function body. For class-based or OOP entrypoints, use method (b) exclusively. If no single-function entrypoints exist, method (b) covers all entrypoints and the dual-method requirement is satisfied by exhaustive method (b) coverage."

#### [CC-2] Enforcement exceptions table incomplete

**Files:** enforcement.md
**Resolution:** Add marker management row (foundations.md is architecture_rule authority, defines 2 exceptions; enforcement.md must reflect all).
**Fix:** Add second row to §Enforcement Exceptions table:

| Exception | Scope | Rationale |
|-----------|-------|-----------|
| CLAUDE.md marker insertion/deletion | Single skill (`/promote`), markers only | Locator hints for re-promotion. Authority: foundations.md §Permitted Exceptions. Marker deletion by user degrades automation, not system state. |

#### [CC-4] VR-3A-14 scope mismatch — 6 vs 3 entrypoints

**Files:** delivery.md
**Resolution:** Expand VR-3A-14 to cover all 6 mutating entrypoints (enforcement.md's "all 6" claim is authoritative).
**Fix:** Expand VR-3A-14 specification to explicitly cover Knowledge engine entrypoints in addition to Work: (a) publish entrypoint (expected origin: `"user"`); (b) staging write entrypoint `/distill` (expected origin: `"agent"`); (c) promote-meta write entrypoint (expected origin: `"user"`).

#### [SY-2] T1-gate-2 double-mapped to two version spaces

**Corroboration:** Independent convergence (CC-5 + VR-14)
**Files:** delivery.md
**Resolution:** Unmap T1-gate-2 from "record provenance" (it only tests knowledge entry `lesson-meta.meta_version`), add dedicated test.
**Fix:** In the version space coverage map, change "record provenance → T1-gate-2" to "record provenance → VR-NEW-9". Add VR-NEW-9 at Step 0a:
- VR-NEW-9: Context snapshot and Work ticket with `RecordMeta.schema_version: "2.0"` — assert reader skips entry per-entry with warning in `QueryDiagnostics.warnings`, entries with `"1.0"` and `"1.1"` are returned.

#### [SP-4] AuditEntry Literal["1.0"] vs same-major tolerance

**Files:** types.md
**Resolution (Codex-revised):** Keep `Literal["1.0"]` — do NOT change to `str`. Add explicit writer/reader split note.
**Fix:** Add note below `AuditEntry.schema_version: Literal["1.0"]`: "The `Literal["1.0"]` annotation governs the write-time contract: writers MUST emit the version they were built for. Readers MUST apply same-major tolerance per the Version Evolution Policy — entries with `schema_version` matching the current major version (e.g., `"1.1"`) are accepted; entries with a different major version (e.g., `"2.0"`) are skipped with a warning. The Python type annotation constrains writers, not readers."
**Codex note:** Original proposal to change to `str` was wrong — would destroy writer discipline. The writer/reader split is the correct approach, matching the pattern already used by the Compatibility Rules section.

---

## Commit 2 — Behavioral Gaps + Authority/Schema (T3 + T4)

**Finding count:** 7 T3 + 10 T4 = 17 findings
**Files:** operations.md, enforcement.md, types.md, storage-and-indexing.md, delivery.md, skill-surface.md, foundations.md

### Behavioral Gap Fixes (T3)

Apply the 7 design decisions (DD-1 through DD-7) as specified in the Design Decisions section above.

**Files touched:** operations.md (DD-1, DD-2), enforcement.md (DD-3, DD-4, DD-5), delivery.md (DD-6), skill-surface.md (DD-6), storage-and-indexing.md (DD-7), types.md (DD-2).

### Authority Placement + Schema Precision Fixes (T4)

#### [AA-2] enforcement.md autonomy table has behavior_contract claims

**Files:** enforcement.md, operations.md
**Fix:** Remove behavioral characterization text from the Rationale column of the Autonomy Model table. Replace with short labels (e.g., "user-approval required" for suggest, "automated with audit trail" for auto_audit). Move behavioral definitions to operations.md §Work Mode Definitions.

#### [AA-3] /save delegation rule in lower-precedence file

**Files:** operations.md
**Fix:** Add normative statement to operations.md §/save as Session Orchestrator: "/save must invoke the same public entrypoint function as /defer and /distill respectively — it is a thin orchestrator, not a reimplementation." skill-surface.md retains its current text as a restatement.

#### [SP-2] LedgerEntry.record_ref null for snapshot_written

**Files:** types.md
**Fix:** Add per-event-type population rule to the Event Vocabulary table footnote: "For `snapshot_written`, `record_ref` must be non-null (`= payload.ref`). Producers must assert non-null before appending; skip the append with a diagnostic warning if `payload.ref` is unavailable. Readers processing `snapshot_written` with `record_ref = None` must skip the entry with a warning in `QueryDiagnostics.warnings`."

#### [SP-3] Staging body-identity invariant unenforced

**Files:** types.md
**Fix:** Add explicit note to §Staging File Format: "The JSON `content` field is not integrity-checked separately. Only the body + `content_sha256` pair matters for correctness. If `content_hash(body) == content_sha256` but `json_content != body`, the body is authoritative. `/curate` logs a per-entry warning in `QueryDiagnostics.warnings` (not corrupt-skip) for this divergence."

#### [SP-7] Work ticket YAML schema not canonically defined

**Files:** types.md or storage-and-indexing.md
**Fix:** Add canonical Work ticket fenced-YAML field table to types.md §Work Subsystem or storage-and-indexing.md §Work Storage Layout. Fields: `ticket_id`, `status`, `worktree_id`, `created_at`, `updated_at`, `source_ref`, `tags`. Mark which are required vs optional.

#### [SY-3] knowledge_normalize rule 6 trailing newline — unspecified and untested

**Corroboration:** Cross-lens followup (SP-6 + VR-19)
**Files:** types.md, delivery.md
**Fix — types.md:** Add rule 11 to §knowledge_normalize: "Rule 11: Ensure the document ends with exactly one `\n`." Update the `content_sha256` citation from "per rule 6" to "per rule 11."
**Fix — delivery.md:** Add test to VR-0A-6: Assert that `knowledge_normalize()` applied to content ending with no newline, one newline, and multiple newlines all produce a document ending with exactly one `\n`, and the resulting `content_sha256` is identical for all three inputs.

#### [IE-1] .diag directory creation failure understated

**Files:** enforcement.md
**Fix:** Add classification to §Session Diagnostic Channel: "When directory creation fails due to persistent permission issues (not transient race), `engram_session` logs to stderr AND emits a separate indicator in the session diagnostic output that the diagnostic channel is structurally unavailable. This is distinct from transient creation races. The 'accepted limitation' applies to transient failures only."

#### [IE-3] Origin-matching no shared runtime validator

**Files:** enforcement.md
**Fix:** Add to §Origin-Matching by Entrypoint: "Each entrypoint should use the shared helper function `validate_origin_match(expected, actual)` that raises or returns an error on mismatch. This converts the per-entrypoint self-enforcement pattern into a shared enforcement primitive with a single test surface."

#### [CC-3] VR-ID collision — two tests share VR-0A-12

**Files:** delivery.md
**Fix:** Rename the extension item (slash-in-record_id test) from VR-0A-12 to VR-0A-18 (next available sequential ID after VR-0A-17).

#### [IE-5] Engine script path canonicalization incomplete

**Files:** enforcement.md
**Fix:** Add to §Engine Script Resolution: "Engine script paths must be canonicalized (resolve symlinks, collapse `..`) before pattern matching. If canonicalization fails (broken symlink, permission denied), `engram_guard` blocks the Bash call (exit code 2) with diagnostic."

---

## Commit 3 — Enforcement Surface + Verification Backfill (T5 + T6)

**Finding count:** 5 T5 + 11 T6 = 16 findings
**Files:** enforcement.md, delivery.md, operations.md

### Enforcement Surface (T5)

#### [SY-4] Co-deployment invariant — no enforcement or test

**Corroboration:** Cross-lens followup (IE-13 + VR-20)
**Files:** delivery.md, operations.md
**Fix:** Add promote-time validation: "The promote script must verify that both `hooks/` and `scripts/` directories are present in the deployed plugin root. If either is missing, abort with diagnostic." Add VR-NEW-10: Unit test for missing `scripts/` directory — assert promote fails with specific error message.

#### [SY-5] PostToolUse AST scan file list drift

**Corroboration:** Cross-lens followup (VR-16 + IE-16)
**Files:** delivery.md
**Fix:** Replace the manually maintained file list in VR-4A-23 with a meta-assertion: "Dynamically derive the PostToolUse hook list from `settings.json` (or the hook registration source). Assert every PostToolUse hook file is included in the AST scan. A new PostToolUse hook added to settings.json but not to the scan triggers a test failure."

#### [IE-8] engram_quality before authorization at Step 4a

**Files:** enforcement.md
**Fix:** Add accepted-gap statement to §Bridge Period Limitations for the Step 2a–4a window: "During Steps 2a–4a, `engram_quality` fires on Context snapshot writes before `context_direct_write_authorization` is active. Quality feedback is advisory during this window — the guard allows Context writes unconditionally via branch 4."

#### [IE-10] Guard branch 1 missing engine-file-exists check

**Files:** enforcement.md
**Fix:** Add to §Guard Decision Algorithm branch 1: "Before writing TrustPayload, verify the Bash target matches an existing engine script file. If the file does not exist at the resolved path, skip trust injection (branch falls through to branch 3/4). This prevents injection into non-engine Bash calls that happen to match the naming pattern."

#### [IE-14] Unauthorized staging writes only detectable at /curate

**Files:** enforcement.md
**Fix:** Add explicit note to §Direct-Write Path Authorization or §Bridge Period: "Between Step 2a and Step 3a, a Bash-bypassing write to `engram/knowledge/staging/` is not blocked by branch 3 (inactive). The staging file passes integrity checks (content_sha256) but lacks a trust triple. Detection occurs at `/curate` time when `trust_triple_present: false` is flagged. This is the accepted enforcement boundary for the bridge period."

### Verification Backfill (T6)

#### [VR-2] AuditEntry session_id invariant untested

**Files:** delivery.md
**Fix:** Add VR-3A-N at Step 3a: "Assert that an AuditEntry with `trust_triple_present: false` has `session_id: null`. Assert that an AuditEntry with `trust_triple_present: true` has `session_id` matching the session's UUID."

#### [VR-3] Engine content_sha256 hash verification untested

**Files:** delivery.md
**Fix:** Add VR-2A-N at Step 2a: "Submit a `DistillEnvelope` where `content_sha256` does not match `content_hash(content)`. Assert the Knowledge engine rejects the candidate with a hash-mismatch error."

#### [VR-4] promote-meta cross-validation untested

**Files:** delivery.md
**Fix:** Add VR-2A-N at Step 2a: "After a successful promote, read `promote-meta` and assert `promoted_content_sha256 == content_hash(original lesson content)` and `lesson_id` matches the promoted lesson's RecordRef."

#### [VR-5] DeferEnvelope context=None idempotency untested

**Files:** delivery.md
**Fix:** Add VR-3A-N at Step 3a: "Submit a `DeferEnvelope` with `context=None`. Assert the Work engine creates a ticket with no context field. Submit the identical envelope again — assert idempotency (no duplicate ticket)."

#### [VR-6] work_dedup_fingerprint path normalization untested

**Files:** delivery.md
**Fix:** Add VR-3A-N at Step 3a: "Submit two `DeferEnvelope`s with `source_file` paths that differ only by normalization (e.g., `./src/foo.py` vs `src/foo.py`). Assert both produce the same `work_dedup_fingerprint`."

#### [VR-7] Staging body-identity invariant untested

**Files:** delivery.md
**Fix:** Add VR-2A-N at Step 2a: "After staging a lesson via `/distill`, read the staging file. Assert the markdown body is byte-identical to `DistillCandidate.content` and `content_hash(body) == content_sha256`."

#### [VR-8] VR-3A-2 underspecified (13 words)

**Files:** delivery.md
**Fix:** Expand VR-3A-2 specification: "Create a ticket via the old Work engine (bridge adapter). Replace the old engine with the new engine. Submit a `DeferEnvelope` with the same `idempotency_key` as the existing ticket. Assert the new engine detects the idempotency key collision and skips ticket creation (returns existing ticket ref)."

#### [VR-9] VR-1-1 depends on old engine availability

**Files:** delivery.md
**Fix:** Add note to VR-1-1: "This test requires the old ticket engine to be available (bridge period). It must be executed during Step 1 before the bridge is removed. After Step 3a (bridge replacement), this test is no longer executable — mark as bridge-only in the test suite."

#### [VR-11] VR-NEW-3 missing branch 2 coverage

**Files:** delivery.md
**Fix:** Add to VR-NEW-3: "Include a branch 2 test case: Write to a Context snapshot path when `context_direct_write_authorization` is active and `worktree_id` resolution fails (degraded mode). Assert the write is blocked by branch 2 (exit code 2). Also test: same write when `context_direct_write_authorization` is inactive (before Step 4a) — assert branch 2 is a no-op, write allowed via branch 4."

#### [VR-12] VR-4A-3 flaky under CI load

**Files:** delivery.md
**Fix:** Add stability note to VR-4A-3: "This test measures timing-dependent behavior. Use a generous timeout (10x expected duration) and allow 1 retry before failure. If flaky in CI, investigate whether the CI runner's filesystem introduces non-deterministic latency."

#### [VR-15] VR-5-1–5-4 pytest conversion unowned

**Files:** delivery.md
**Fix:** Add ownership note to Step 5 Required Verification: "VR-5-1 through VR-5-4 are grep/filesystem assertions. They may be implemented as pytest tests or as shell assertions in a CI script. The implementer chooses the framework; the pass criteria are the same."

---

## Parked — P2 (19 findings)

Deferred to a separate remediation session after P0/P1 is complete:

| ID | Title | Reviewer |
|----|-------|----------|
| AA-4 | README omits enforcement exclusion from behavior_contract chain | AA |
| CC-6 | README/spec.yaml data-contract description variance | CC |
| CC-7 | /save structural placement ambiguity | CC |
| CC-8 | Circular cross-reference operations.md ↔ storage-and-indexing.md | CC |
| CC-9 | operations.md self-declares authority for snapshot_written | CC |
| CC-10 | .diag read protocol duplicated in operations.md + enforcement.md | CC |
| SP-1 | AuditEntry missing worktree_id field | SP |
| SP-8 | .diag and migration_report.json implicit version spaces | SP |
| SP-9 | RecordMeta.visibility unvalidated at construction | SP |
| VR-17 | Compatibility harness fixture count unverifiable | VR |
| VR-18 | Knowledge reader snippet source untested | VR |
| IE-6 | In-flight payload orphaning between sessions | IE |
| IE-7 | Containment diagnostic unsanitized path | IE |
| IE-11 | engram_register non-file shard path unhandled | IE |
| IE-12 | Hook ordering table conflates trigger phases | IE |

Plus 4 additional P2 findings from individual reviewer files.
