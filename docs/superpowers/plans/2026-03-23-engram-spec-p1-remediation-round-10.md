# Engram Spec P1 Remediation — Round 10

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remediate all 25 P1 findings from Round 10, grouped into 7 coherent tasks by theme.

**Architecture:** All changes are spec-level edits to markdown/YAML files in `docs/superpowers/specs/engram/`. No code changes.

**Tech Stack:** Markdown, YAML

**Spec directory:** `docs/superpowers/specs/engram/`
**Review report:** `.review-workspace/synthesis/report.md`
**Review ledger:** `.review-workspace/synthesis/ledger.md`

---

## Finding-to-Task Map

| Task | Findings | Theme | Files |
|------|----------|-------|-------|
| 1 | SY-6, SY-10, SY-14 | validate_origin_match spec hole | types.md, enforcement.md, delivery.md |
| 2 | SY-7 | engine_trust_injection name collision | enforcement.md, delivery.md |
| 3 | SY-8, SY-11 | AuditEntry version contradiction | types.md, delivery.md |
| 4 | SY-9 | Guard activation schedule authority | enforcement.md, delivery.md |
| 5 | SY-12, SY-13, SY-15, SY-16, SY-17 | Authority placement + contract language | operations.md, enforcement.md, types.md |
| 6 | SY-19, SY-20, SY-21 | Schema precision | types.md |
| 7 | SY-18, SY-22–SY-30 | Delivery tracking + VR test gaps | delivery.md |

---

### Task 1: Define validate_origin_match (SY-6 + SY-10 + SY-14)

**Findings:**
- SY-6 (CE-1 + IE-2): enforcement.md simultaneously says "no shared runtime validator" (line 254) and "MUST use shared helper validate_origin_match" (line 261). The function is never defined.
- SY-10 (VR-2): VR-3A-14 cannot distinguish shared helper invocation from inline reimplementation.
- SY-14 (CE-5): The per-entrypoint error string format differs from collect_trust_triple_errors stable strings — unclear if validate_origin_match uses one format or the other.

**Files:**
- Modify: `docs/superpowers/specs/engram/types.md:76-99` (§Trust Validation)
- Modify: `docs/superpowers/specs/engram/enforcement.md:254-261` (§Origin-Matching)
- Modify: `docs/superpowers/specs/engram/delivery.md` (VR-3A-14)

- [ ] **Step 1: Add validate_origin_match to types.md §Trust Validation**

After the `collect_trust_triple_errors()` section (after line 99 — the "Origin-matching responsibility" paragraph), add:

```markdown
### Origin-Matching Validation

```python
# engram_core/trust.py
def validate_origin_match(expected: str, actual: str) -> None:
    """Verify hook_request_origin matches the entrypoint's expected origin.
    Raises ValueError on mismatch. Called after collect_trust_triple_errors() succeeds."""
```

**Precondition:** `actual` has already passed `collect_trust_triple_errors()` validation (non-empty, in `{"user", "agent"}`). This function does NOT re-validate the value set — it only checks the entrypoint-specific match.

**Behavior:** If `expected != actual`, raise `ValueError` with the stable error message:
`"hook_request_origin: expected {expected!r} for this entrypoint, got {actual!r}"`

**Stable error string:** `"hook_request_origin: expected {expected!r} for this entrypoint, got {actual!r}"` — this is a distinct error from `collect_trust_triple_errors()`'s structural validation error (`"hook_request_origin: must be one of {'user', 'agent'}, got {value!r}"`). The two errors cover different failure modes: structural (invalid value) vs. route-specific (valid value, wrong entrypoint).

**Caller obligation:** Each mutating Work or Knowledge engine entrypoint must call `validate_origin_match(expected, actual)` after `collect_trust_triple_errors()` succeeds. On `ValueError`, the entrypoint must reject before any side effects and surface the error message in the structured response.
```

- [ ] **Step 2: Fix the contradiction in enforcement.md §Origin-Matching**

In enforcement.md, replace lines 254 (the "Enforcement mechanism: Origin-matching has no shared runtime validator" paragraph) with:

```
**Enforcement mechanism:** Origin-matching uses `validate_origin_match(expected, actual)` defined in [types.md §Origin-Matching Validation](types.md#origin-matching-validation) as the shared enforcement primitive. `collect_trust_triple_errors()` validates structural correctness (`hook_request_origin` is a valid string in `{"user", "agent"}`) but does not enforce per-entrypoint origin rules — `validate_origin_match()` does.
```

This removes the contradiction ("no shared runtime validator" vs "MUST use shared helper"). The rest of the §Origin-Matching section (lines 256-261) can remain as-is — it describes the per-entrypoint rejection contract and the mandate to use `validate_origin_match`, which is now defined.

- [ ] **Step 3: Add validate_origin_match call-site verification to VR-3A-14**

In delivery.md, find VR-3A-14 (around line 219). After the existing text about "regex match on the format template", add:

```
Additionally, for each mutating entrypoint, assert `validate_origin_match` is called by name (via AST scan or mock-and-assert — parallel to VR-3A-9 method (b) for `collect_trust_triple_errors()`). An inline reimplementation that produces the same output but does not call `validate_origin_match` must fail this test.
```

- [ ] **Step 4: Add validate_origin_match to foundations.md §Package Structure**

In foundations.md §Package Structure (the `engram_core/trust.py` line), verify the comment mentions both functions. The current text says `collect_trust_triple_errors() — shared trust validator`. Update to:

```
│   ├── trust.py             # collect_trust_triple_errors() + validate_origin_match() — shared trust validators
```

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/specs/engram/types.md docs/superpowers/specs/engram/enforcement.md docs/superpowers/specs/engram/delivery.md docs/superpowers/specs/engram/foundations.md
git commit -m "fix(spec): define validate_origin_match in types.md (SY-6 + SY-10 + SY-14)

Resolves the contradiction where enforcement.md says 'no shared runtime
validator' but mandates validate_origin_match. Defines the function in
types.md with signature, stable error string, and caller obligation.
Adds call-site verification to VR-3A-14."
```

---

### Task 2: Fix engine_trust_injection capability name collision (SY-7)

**Finding:** CC-4 + IE-3: Two Guard Capability Rollout rows share the name `engine_trust_injection` (Knowledge at Step 2a, Work at Step 3a). Implementation cannot distinguish scopes.

**Files:**
- Modify: `docs/superpowers/specs/engram/enforcement.md:146-153, 175, 309-317`
- Modify: `docs/superpowers/specs/engram/delivery.md` (Steps 2a, 3a references)

- [ ] **Step 1: Rename the Step 3a entry in the rollout table**

In enforcement.md, change the rollout table row at line 149 from:

```
| `engine_trust_injection` (extended) | Step 3a | Work engine mutating entrypoints |
```

to:

```
| `engine_trust_injection_work` | Step 3a | Work engine mutating entrypoints |
```

- [ ] **Step 2: Update the Guard Decision Algorithm capability gating paragraph**

In enforcement.md line 175, change:

```
**Capability gating:** Each branch is only active when its corresponding guard capability has shipped. Branch 1 activates at Step 2a (`engine_trust_injection`). Branch 3 activates at Step 3a (`work_path_enforcement`). Branch 2 activates at Step 4a (`context_direct_write_authorization`). Before a capability ships, its branch is a no-op (falls through to branch 4).
```

to:

```
**Capability gating:** Each branch is only active when its corresponding guard capability has shipped. Branch 1 activates in two phases: Step 2a (`engine_trust_injection`) covers Knowledge engine paths; Step 3a (`engine_trust_injection_work`) extends coverage to Work engine paths. Branch 3 activates at Step 3a (`work_path_enforcement`). Branch 2 activates at Step 4a (`context_direct_write_authorization`). Before a capability ships, its branch is a no-op (falls through to branch 4).
```

- [ ] **Step 3: Update Bridge Period Limitations references**

In enforcement.md, grep for references to `engine_trust_injection` in the Bridge Period Limitations section (around lines 309-317). Update any that reference the ambiguous "(extended)" notation to use `engine_trust_injection_work`.

- [ ] **Step 4: Update delivery.md Step 2a and 3a references**

Grep delivery.md for `engine_trust_injection`. Update Step 3a references to use the new name `engine_trust_injection_work` where they refer to the Work-specific extension.

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/specs/engram/enforcement.md docs/superpowers/specs/engram/delivery.md
git commit -m "fix(spec): rename engine_trust_injection Step 3a capability (SY-7)

The capability name was reused for two distinct scopes (Knowledge at 2a,
Work at 3a). Renames the Step 3a entry to engine_trust_injection_work
to make capability-gate logic unambiguous."
```

---

### Task 3: Fix AuditEntry version contradiction (SY-8 + SY-11)

**Findings:**
- SY-8 (CC-1 + SP-1): `Literal["1.0"]` annotation contradicts starting value `"1.1"` in version spaces table.
- SY-11 (VR-5): auto_created missing-field backward-compat untested.

**Root cause:** The AuditEntry format includes `auto_created` from inception (no 1.0 version ever shipped). The `Literal["1.0"]` and "added in 1.1" language are artifacts of the writing process, not of real version history.

**Files:**
- Modify: `docs/superpowers/specs/engram/types.md:532, 546, 564`
- Modify: `docs/superpowers/specs/engram/delivery.md` (add VR test)

- [ ] **Step 1: Change AuditEntry annotation to Literal["1.1"]**

In types.md line 532, change:

```python
    schema_version: Literal["1.0"]
```

to:

```python
    schema_version: Literal["1.1"]
```

- [ ] **Step 2: Rewrite the "added in 1.1" prose**

In types.md line 546, replace:

```
The `auto_created` field was added in minor version `1.1`. Same-major readers encountering entries without `auto_created` MUST treat them as `auto_created: True` (conservative — counts toward cap). Writers at version `1.1`+ MUST emit `auto_created`.
```

with:

```
The `auto_created` field is present from the initial version (`1.1`). No `1.0` AuditEntry format was ever shipped. The defensive read rule is retained for robustness: same-major readers encountering entries without `auto_created` MUST treat them as `auto_created: True` (conservative — counts toward cap). This handles corrupt or hand-edited entries, not a version transition.
```

- [ ] **Step 3: Update the writer/reader split paragraph**

In types.md line 544, change the reference from `Literal["1.0"]` to `Literal["1.1"]`:

```
**`schema_version` writer/reader split:** The `Literal["1.1"]` annotation governs the write-time contract: writers MUST emit the version they were built for.
```

(Rest of the paragraph is fine — it describes same-major tolerance using `"1.1"` and `"2.0"` examples which still work.)

- [ ] **Step 4: Add auto_created backward-compat VR test**

In delivery.md, find VR-NEW-8 (around where AuditEntry version tests are). After it, add:

```
- **VR-3A-24 (auto_created missing-field default):** Construct a JSONL shard with a `schema_version: "1.1"` entry that lacks the `auto_created` field (simulating corruption or hand-edit). Assert the Work engine's `work_max_creates` counter treats that entry as `auto_created: True` (counts toward cap). Verify with `work_max_creates: 2`: write one legitimate auto-create ticket, then insert the corrupt entry (no `auto_created`). Assert the next auto-create attempt is rejected (cap reached: 1 explicit + 1 defaulted = 2).
```

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/specs/engram/types.md docs/superpowers/specs/engram/delivery.md
git commit -m "fix(spec): align AuditEntry annotation with starting version 1.1 (SY-8 + SY-11)

Literal['1.0'] was wrong — no 1.0 format was ever shipped. Changes
annotation to Literal['1.1'], rewrites 'added in 1.1' prose, and adds
a VR test for the auto_created missing-field defensive read rule."
```

---

### Task 4: Move guard activation schedule to enforcement.md (SY-9)

**Finding:** AA-5 + CE-2 + CE-11: enforcement.md defers to delivery.md for guard capability activation timing — an enforcement_mechanism decision owned by delivery.md (implementation_plan authority).

**Files:**
- Modify: `docs/superpowers/specs/engram/enforcement.md:146-153`
- Modify: `docs/superpowers/specs/engram/delivery.md` (Steps 2a, 3a, 4a)

- [ ] **Step 1: Make enforcement.md the canonical source for guard activation schedule**

In enforcement.md, replace the note at line 153:

```
The 'Ships At' column mirrors delivery.md §Build Sequence for convenience. delivery.md is the `implementation_plan` authority — if the two diverge, delivery.md is authoritative.
```

with:

```
This table is the canonical source for guard capability activation (enforcement_mechanism authority). delivery.md §Build Sequence references this table for the implementation schedule — if the two diverge, this table is authoritative for which capabilities are active at each step.
```

- [ ] **Step 2: Update delivery.md to reference enforcement.md for guard capabilities**

In delivery.md, find the Step 2a deliverable table (around line 150) where it says:

```
| `engram_guard` hook (engine trust injection only) | [Engine trust injection](enforcement.md#trust-injection) for Knowledge engine. Write/Edit path authorization deferred to Step 3a. |
```

Add a note after the deliverable tables at Steps 2a, 3a, and 4a:

For Step 2a, after the deliverable table: `Guard capabilities for this step: see [enforcement.md §Guard Capability Rollout](enforcement.md#guard-capability-rollout) (authoritative).`

For Step 3a: Same note.

For Step 4a: Same note.

- [ ] **Step 3: Update enforcement.md §Bridge Period Limitations**

Find the text (around line 309) that says "delivery.md is the `implementation_plan` authority" and update to reference the enforcement.md rollout table as canonical, with delivery.md providing the build sequence (step ordering) that determines when each capability ships.

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/specs/engram/enforcement.md docs/superpowers/specs/engram/delivery.md
git commit -m "fix(spec): make enforcement.md canonical for guard capability schedule (SY-9)

The guard capability activation schedule was owned by delivery.md
(implementation_plan authority) but determines enforcement behavior.
Enforcement.md is now the canonical source; delivery.md references it."
```

---

### Task 5: Authority placement cleanup (SY-12 + SY-13 + SY-15 + SY-16 + SY-17)

**Findings:**
- SY-12 (AA-4): operations.md §Envelope Invariants contains bridge-period idempotency constraint (implementation_plan claim).
- SY-13 (CE-3): Trust injection mandate duplicated in operations.md + enforcement.md.
- SY-15 (CE-4): "Direct-write path authorization" label for unconditional allow.
- SY-16 (CE-7): Staging inbox cap behavioral spec in operations.md — enforcement_mechanism decision delegated to lower-precedence authority.
- SY-17 (CE-12): operations.md snapshot_written emission claims authority over data-contract interface.

**Files:**
- Modify: `docs/superpowers/specs/engram/operations.md:15, 72-74, 245, 278`
- Modify: `docs/superpowers/specs/engram/enforcement.md:267-273, 398-399`
- Modify: `docs/superpowers/specs/engram/types.md` (snapshot_written emission conditions)

- [ ] **Step 1: Replace operations.md trust injection mandate with cross-reference (SY-13)**

In operations.md line 15, replace:

```
- **Precondition:** Every mutating Work or Knowledge engine entrypoint must validate the trust triple via `collect_trust_triple_errors()` before making state changes. Operations with missing or incomplete triples are rejected. See [enforcement.md §Check ordering](enforcement.md#check-ordering) for the `.engram-id` existence check that precedes trust triple validation, and [enforcement.md §Trust Injection](enforcement.md#trust-injection) for the full enforcement mandate.
```

with:

```
- **Precondition:** All mutating Work and Knowledge engine entrypoints require trust triple validation before making state changes. Operations with missing or incomplete triples are rejected. The enforcement mandate (which validator to call, check ordering, per-entrypoint origin matching) is specified in [enforcement.md §Trust Injection](enforcement.md#trust-injection) — the authoritative source for enforcement_mechanism claims.
```

This removes the enforcement mandate (`must validate via collect_trust_triple_errors()`) from operations.md and replaces it with a behavioral consequence + cross-reference. The mandate belongs in enforcement.md.

- [ ] **Step 2: Replace operations.md bridge-period idempotency with cross-reference (SY-12)**

In operations.md, find the "Phase-scoped idempotency (migration)" paragraph at line 245. Replace:

```
**Phase-scoped idempotency (migration):** During the bridge period ([Step 1](delivery.md#step-1-bridge-cutover) through [Step 3](delivery.md#step-3-work-cutover)), the old ticket engine's legacy dedup is the active mechanism — envelope-level idempotency keys are not checked. Full envelope idempotency activates when the new Work engine replaces the bridge. This limitation is delivery-owned; see [bridge cutover](delivery.md#step-1-bridge-cutover) for migration-period semantics.
```

with:

```
**Phase-scoped idempotency (migration):** During the bridge period, envelope-level idempotency keys are not checked — the old ticket engine's legacy dedup is the active mechanism. See [delivery.md §Bridge Cutover](delivery.md#step-1-bridge-cutover) for the authoritative bridge-period specification (implementation_plan authority).
```

This keeps the behavioral note (idempotency not checked during bridge) but removes the normative implementation_plan details (which step, which mechanism replaces it) and defers to delivery.md.

- [ ] **Step 3: Rename "Direct-write path authorization" (SY-15)**

In enforcement.md, the term "Direct-write path authorization" appears in:
- The §Guard Decision Algorithm (line ~165-166): "Direct-write path authorization (allow + post-write quality)"
- The §Direct-Write Path Authorization heading (line ~266)
- The rollout table (line ~151)
- The Trust Injection mechanism table (line ~138)

Rename all occurrences from "Direct-write path authorization" to "Direct-write path recognition" where it describes the Branch 2 behavior. Keep "authorization" only in contexts that genuinely describe an authorization check.

In the §Direct-Write Path Authorization section (around line 266), add after the numbered list:

```
**Naming note:** Branch 2 performs path recognition (is this a Context-owned path?) with unconditional allow, not an authorization check. The "authorization" label is retained for continuity but the enforcement model is: recognize → allow → post-write quality → triage anomaly detection. See [decisions.md §Named Risks](decisions.md#named-risks) (Context any-source write authorization) for the accepted gap.
```

- [ ] **Step 4: Move staging inbox cap behavioral enforcement to enforcement.md (SY-16)**

In enforcement.md line 399, the text currently says:

```
This section owns the configuration schema and validation contract (`enforcement_mechanism`). The behavioral specification (rejection logic, formula, error message format, edge cases, and recovery path) is in [operations.md §Distill](operations.md#distill-context-to-knowledge-staged) (`behavior_contract`).
```

Replace with:

```
This section owns the configuration schema, validation contract, and cap enforcement behavioral specification (`enforcement_mechanism`). The behavioral specification was previously delegated to operations.md §Distill but is consolidated here per enforcement_mechanism claim_precedence.

**Cap enforcement formula:** The Knowledge engine checks the cumulative count of files in `knowledge_staging/` before writing new staged candidates. If `count + batch_size > knowledge_max_stages`, the entire batch is rejected (whole-batch reject for determinism — no partial staging). The rejection response includes current count, cap, and a suggestion to run `/curate` to clear the inbox.

**Edge case — `batch_size > knowledge_max_stages`:** If a single distill batch exceeds the configured cap, the batch is rejected even with 0 files in staging. The rejection response must include: (1) current `batch_size` and cap values, (2) the exact config change needed, (3) instruction to re-run with the `snapshot_ref` from the recovery manifest.
```

Then in operations.md lines 72-74, replace the detailed cap enforcement formula with a cross-reference:

```
**Staging inbox cap.** Cap enforcement (rejection formula, error message, edge cases) is specified in [enforcement.md §Staging Inbox Cap](enforcement.md#staging-inbox-cap) (`enforcement_mechanism` authority). The cap is cumulative (total files in directory), non-atomic (TOCTOU acceptable), and whole-batch (no partial staging). See [decisions.md §Deferred Decisions](decisions.md#deferred-decisions) for partial staging deferral.
```

- [ ] **Step 5: Remove snapshot_written authority claim from operations.md (SY-17)**

In operations.md line 278, replace:

```
All three producers emit the event. The `orchestrated_by` value distinguishes them in `/timeline` and `/triage`. This is the authoritative specification for `snapshot_written` emission — see [types.md event vocabulary](types.md#event-vocabulary-v1) for the payload schema.
```

with:

```
All three producers emit the event. The `orchestrated_by` value distinguishes them in `/timeline` and `/triage`. See [types.md §Event Vocabulary](types.md#event-vocabulary-v1) for the authoritative `snapshot_written` schema and emission rules (interface_contract authority).
```

Then in types.md, in the Event Vocabulary table at the `snapshot_written` row (line 483), expand the Purpose column to include the per-producer emission conditions that were previously claimed by operations.md:

Update the `snapshot_written` row's Purpose to:

```
Timeline fidelity — records snapshot creation. `orchestrated_by` values: `"save"` (after snapshot write, before defer/distill), `"quicksave"` (after checkpoint write), `"load"` (after archive write). See [operations.md §Snapshot Event Emission](operations.md#snapshot-event-emission) for operational context.
```

- [ ] **Step 6: Commit**

```bash
git add docs/superpowers/specs/engram/operations.md docs/superpowers/specs/engram/enforcement.md docs/superpowers/specs/engram/types.md
git commit -m "fix(spec): authority placement cleanup — 5 claims moved to correct authority files

SY-12: bridge-period idempotency → delivery.md cross-ref
SY-13: trust mandate → enforcement.md cross-ref
SY-15: direct-write 'authorization' → 'recognition' naming note
SY-16: staging cap formula → enforcement.md
SY-17: snapshot_written authority → types.md"
```

---

### Task 6: Schema precision fixes (SY-19 + SY-20 + SY-21)

**Findings:**
- SY-19 (SP-3): promote-meta example has 63-char hashes (should be 64).
- SY-20 (SP-4): Ledger shard flock missing timeout specification.
- SY-21 (SP-8): PromoteEnvelope.content_sha256 byte-range extraction obligation underspecified.

**Files:**
- Modify: `docs/superpowers/specs/engram/types.md:189, 517, 166`

- [ ] **Step 1: Fix 63-char hash examples in promote-meta (SY-19)**

In types.md line 189, the example `promote-meta` JSON contains two hash values that are 63 hex chars instead of 64. Replace the entire example line with hashes that are exactly 64 characters. Use a repeating pattern that is obviously 64 chars:

```markdown
<!-- promote-meta {"lesson_id": "550e8400-e29b-41d4-a716-446655440000", "meta_version": "1.0", "promoted_at": "2026-03-17T14:30:00Z", "promoted_content_sha256": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2", "target_section": "## Code Style", "transformed_text_sha256": "d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5"} -->
```

Count both existing hashes to confirm they're 63 chars, then add one hex char to each to reach 64. (The pattern `a1b2c3d4e5f6` repeating should produce 64 chars when repeated 5.33 times — verify the exact count.)

- [ ] **Step 2: Add ledger shard lock timeout (SY-20)**

In types.md §Write Semantics (around line 517), after "Lock scope: read-append-fsync.", add:

```
Lock timeout: 5 seconds. On timeout: log warning, do not propagate to caller. This matches the `learnings.md.lock` timeout (§Write Concurrency) and the `engram_register` failure mode documented in enforcement.md.
```

- [ ] **Step 3: Clarify PromoteEnvelope.content_sha256 byte-range obligation (SY-21)**

In types.md line 166, after the existing `content_sha256` field description, add:

```
Computed by applying `content_hash()` (which uses `knowledge_normalize` internally) to the lesson content bytes extracted using the byte-range definition in §Knowledge Entry Format. The `/promote` Step 1 engine MUST use the same byte-range extraction logic and normalization as `lesson-meta.content_sha256` — extract content from the live `learnings.md` file at Step 1 invocation time, apply `knowledge_normalize`, then `sha256`.
```

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/specs/engram/types.md
git commit -m "fix(spec): schema precision — hash examples, lock timeout, byte-range (SY-19/20/21)

SY-19: Fix 63-char promote-meta hash examples to 64 chars
SY-20: Add 5-second timeout to ledger shard flock
SY-21: Clarify PromoteEnvelope.content_sha256 byte-range extraction"
```

---

### Task 7: Delivery tracking + VR test gaps (SY-18 + SY-22–SY-30)

**Findings:**
- SY-18 (CC-3): Duplicate VR-4A-17 test identifier.
- SY-22 (VR-3): promote-meta.lesson_id cross-validation untested.
- SY-23 (VR-4): Duplicate promote-meta Branch D handling untested.
- SY-24 (VR-6): work_max_creates runtime cap enforcement untested.
- SY-25 (VR-7): engram init "prints exact git commit command" unverified.
- SY-26 (VR-9): Co-deployment test at Step 5 fires too late.
- SY-27 (VR-10): promote-meta missing meta_version Branch D exclusion untested.
- SY-28 (VR-13): Chain protocol resumed_from happy-path untested.
- SY-29 (VR-15): SessionStart 450ms aggregate guard untested.
- SY-30 (VR-16): engram_session diagnostic channel accessibility check untested.

**Files:**
- Modify: `docs/superpowers/specs/engram/delivery.md`

- [ ] **Step 1: Rename duplicate VR-4A-17 (SY-18)**

In delivery.md line 318, change:

```
- **VR-4A-17 extension (engine+hook co-producer):**
```

to:

```
- **VR-4A-38 (engine+hook co-producer concurrency):**
```

Highest existing ID is VR-4A-37; next available is VR-4A-38.

- [ ] **Step 2: Add promote-meta.lesson_id cross-validation test (SY-22)**

In delivery.md, after VR-2A-10 (Step 2a Required Verification, around line 168), add:

```
- promote-meta.lesson_id cross-validation (VR-2A-NEW-7): Construct a `learnings.md` fixture where `promote-meta.lesson_id` contains a different UUID than the immediately preceding `lesson-meta.lesson_id`. Run query or `/promote`. Assert: the entry's promotion status degrades to `unknown`, `QueryDiagnostics.warnings` contains a per-entry message for the mismatched entry. Other entries in the file are unaffected.
```

- [ ] **Step 3: Add duplicate promote-meta Branch D test (SY-23)**

After the new VR-2A-NEW-7, add:

```
- Duplicate promote-meta Branch D handling (VR-2A-NEW-8): Manually write two `promote-meta` comments with the same `lesson_id` into a `learnings.md` fixture. Run `/promote`. Assert: lesson excluded from candidate list (Branch D), warning surfaced containing the `lesson_id` and "migration".
```

- [ ] **Step 4: Add work_max_creates runtime cap test (SY-24)**

In delivery.md Step 3a Required Verification, after VR-3A-15, add:

```
- work_max_creates runtime cap enforcement (VR-3A-23): Set `work_max_creates: 3` in `.claude/engram.local.md`. Invoke `/defer` 3 times in `auto_audit` mode with distinct content. Assert 3 tickets created (3 `auto_created: True` audit entries). Invoke a 4th time. Assert rejection with cap-exceeded message. Assert no 4th ticket file. Assert counter resets for a new `session_id` (invoke with new session → succeeds).
```

- [ ] **Step 5: Add engram init output assertion (SY-25)**

In delivery.md, find VR-0B-1 (around line 87). In case (a), add to the assertion list:

After "stages for commit", add:

```
stdout contains a `git commit` command string referencing `.engram-id` (e.g., `git commit -m "Initialize engram identity"` or similar — exact format is implementation-defined but must include the filename)
```

- [ ] **Step 6: Move co-deployment test to Step 2a (SY-26)**

In delivery.md Step 2a Required Verification, add:

```
- Co-deployment invariant (VR-2A-NEW-9): Invoke the promote script with `scripts/` directory absent from the plugin root. Assert promote fails with a diagnostic referencing the missing directory. See [co-deployment invariant](enforcement.md#step-1-injection-pretooluse). This test activates at Step 2a (when `engine_trust_injection` capability first requires co-deployment) — not Step 5.
```

Then update the Step 5 VR-NEW-10 reference to note it is now a duplicate of VR-2A-NEW-9 and can be removed or retained as a final gate check.

- [ ] **Step 7: Add promote-meta missing meta_version test (SY-27)**

In delivery.md Step 4a Required Verification, after VR-4A-21, add:

```
- Promote-meta missing meta_version (VR-4A-39): Fixture with `promote-meta` that has all required fields EXCEPT `meta_version` (field absent, not empty). Run `/promote`. Assert: lesson excluded from candidate list. Assert: warning containing the `lesson_id` and "missing meta_version" surfaced. Distinct from VR-4A-18 (unknown major) and VR-4A-21 (minor bump) — tests the legacy-entry handling path.
```

- [ ] **Step 8: Add chain protocol happy-path test (SY-28)**

In delivery.md Step 4a Required Verification, add:

```
- Chain protocol resumed_from happy-path (VR-4A-40): (1) Run `/load` with a valid snapshot fixture. Assert chain state file created at `chain/<worktree_id>-<session_id>`. (2) Run `/save`. Assert the resulting snapshot frontmatter contains `resumed_from` pointing to the archived snapshot path. (3) Assert chain state file removed (or trash'd) after `/save`.
```

- [ ] **Step 9: Add SessionStart 450ms guard test (SY-29)**

In delivery.md Step 4a Required Verification, add:

```
- SessionStart aggregate elapsed-time guard (VR-4A-41): Mock the elapsed-time check to return 451ms after the first optional operation completes. Assert: remaining optional operations are not executed (mock them as raising to detect calls). Assert: log output contains `"engram_session: startup budget exceeded"` with elapsed ms. Assert: session is not blocked (hook returns 0). `worktree_id` resolution (mandatory, first operation) is exempt from this guard and must still execute.
```

- [ ] **Step 10: Add diagnostic channel accessibility test (SY-30)**

In delivery.md Step 4a Required Verification, add:

```
- engram_session diagnostic channel accessibility (VR-4A-42): Mock `os.access(ledger_dir, os.W_OK)` to return `False` (persistent permission failure). Run `engram_session`. Assert: (a) session not blocked; (b) stderr contains a diagnostic indicating structural unavailability; (c) the diagnostic is distinguishable from transient creation-race failures handled by `engram_register`. See [enforcement.md §Session Diagnostic Channel](enforcement.md#session-diagnostic-channel).
```

- [ ] **Step 11: Commit**

```bash
git add docs/superpowers/specs/engram/delivery.md
git commit -m "fix(spec): delivery tracking + 9 missing VR tests (SY-18 + SY-22-SY-30)

SY-18: Rename duplicate VR-4A-17 → VR-4A-38
SY-22: promote-meta.lesson_id cross-validation test
SY-23: Duplicate promote-meta Branch D test
SY-24: work_max_creates runtime cap test
SY-25: engram init output assertion
SY-26: Co-deployment test moved to Step 2a
SY-27: promote-meta missing meta_version test
SY-28: Chain protocol resumed_from happy-path test
SY-29: SessionStart 450ms guard test
SY-30: Diagnostic channel accessibility test"
```

---

## Verification

After all 7 tasks are complete:

- [ ] **Final Step: Cross-reference consistency check**

1. Grep for `validate_origin_match` — should appear in types.md (definition), enforcement.md (usage), delivery.md (VR test), foundations.md (package structure)
2. Grep for `engine_trust_injection` — no ambiguous duplicate names; `engine_trust_injection_work` distinct
3. Grep for `Literal\["1.0"\]` in AuditEntry context — should be gone, replaced by `Literal["1.1"]`
4. Grep for `delivery.md is.*authoritative` in enforcement.md — should be gone (enforcement.md is now canonical for guard capabilities)
5. Grep for `VR-4A-17 extension` — should be gone (renamed to VR-4A-38)
6. Count new VR tests added (expect 10: VR-2A-NEW-7/8/9, VR-3A-23, VR-4A-38/39/40/41/42, plus VR-0B-1 extension)
