# Engram Spec Remediation Round 10 — P0 Findings

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remediate all 5 P0 findings from the Round 10 spec review, resolving authority tangles, behavioral contradictions, enforcement gaps, and verification holes.

**Architecture:** All changes are spec-level edits to markdown files in `docs/superpowers/specs/engram/`. No code changes. Each task is one finding with isolated file edits and a cross-reference verification step.

**Tech Stack:** Markdown, YAML (spec.yaml)

**Spec directory:** `docs/superpowers/specs/engram/`
**Review report:** `.review-workspace/synthesis/report.md`
**Review ledger:** `.review-workspace/synthesis/ledger.md`

---

## File Map

| Task | Finding | Files Modified | Files Verified |
|------|---------|---------------|----------------|
| 1 | SY-1 | spec.yaml:43, foundations.md:38, enforcement.md:364 | operations.md, decisions.md |
| 2 | SY-2 | enforcement.md:161-163, enforcement.md:175-177 | delivery.md (VR test reference) |
| 3 | SY-3 | operations.md:30-32 | enforcement.md:376, skill-surface.md |
| 4 | SY-4 | types.md:479-502 | enforcement.md:16, delivery.md (VR-4A-20) |
| 5 | SY-5 | delivery.md:307-308 | operations.md:93-101 |

---

### Task 1: Fix enforcement exception authority tangle (SY-1)

**Finding:** spec.yaml `enforcement_mechanism: [enforcement, operations, decisions]` excludes `foundation`. foundations.md §Adding New Exceptions claims architecture_rule authority governs enforcement exception creation "per spec.yaml claim_precedence" — but foundation is absent from that chain. enforcement.md §Enforcement Exceptions defers to foundations.md as canonical, creating a three-way contradiction.

**Root cause:** `foundation` missing from `enforcement_mechanism` claim_precedence.

**Files:**
- Modify: `docs/superpowers/specs/engram/spec.yaml:43`
- Modify: `docs/superpowers/specs/engram/foundations.md:38`
- Verify: `docs/superpowers/specs/engram/enforcement.md:357-366`

- [ ] **Step 1: Add foundation to enforcement_mechanism precedence chain in spec.yaml**

In `spec.yaml` line 43, change:

```yaml
    enforcement_mechanism: [enforcement, operations, decisions]
```

to:

```yaml
    enforcement_mechanism: [enforcement, foundation, operations, decisions]
```

**Rationale:** foundation defines the architectural invariants (EBC, permitted exceptions) that bound enforcement behavior. Placing it after enforcement (which owns the mechanisms) but before operations (which owns behavioral semantics) correctly positions it as the architectural constraint authority.

**Ordering decision:** The review report (SY-1) suggested `[enforcement, operations, foundation, decisions]`. This plan uses `[enforcement, foundation, operations, decisions]` instead — foundation must outrank operations in this chain because the purpose is for foundation to govern which exceptions enforcement accommodates. If operations ranked above foundation, operations.md could override exception governance, defeating the purpose of the fix.

- [ ] **Step 2: Fix the factual claim in foundations.md §Adding New Exceptions**

In `foundations.md` line 38, the current text claims:

```
This sequencing ensures architecture_rule authority governs exception creation (per spec.yaml `claim_precedence`), preventing enforcement.md from unilaterally expanding its own exception set.
```

Replace with:

```
This sequencing ensures foundation authority governs exception creation — foundation is second in the enforcement_mechanism precedence chain (per spec.yaml claim_precedence: `[enforcement, foundation, operations, decisions]`). enforcement.md owns enforcement mechanisms but cannot unilaterally expand the set of exceptions those mechanisms must accommodate.
```

**Why:** The original text referenced `architecture_rule` claim_precedence, but the relevant chain is `enforcement_mechanism` (since exceptions modify enforcement behavior, not architecture). The new text correctly cites the `enforcement_mechanism` chain and explains the authority relationship.

- [ ] **Step 3: Verify enforcement.md §Enforcement Exceptions is consistent**

Read `enforcement.md` lines 357-366. Verify:
1. The text "The canonical source is foundations.md" is now formally correct (foundation is in the enforcement_mechanism chain)
2. The table still references foundations.md §Permitted Exceptions
3. No other text in enforcement.md claims precedence over foundations.md for exception definitions

Expected: No changes needed. The existing text becomes correct once spec.yaml is updated.

- [ ] **Step 4: Verify no other spec.yaml references are broken**

Grep for `enforcement_mechanism` across all spec files to verify no other text quotes or depends on the old 3-element chain.

Run: `rg "enforcement_mechanism" docs/superpowers/specs/engram/`

Expected: Only spec.yaml and contextual references. No file hardcodes the old `[enforcement, operations, decisions]` list.

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/specs/engram/spec.yaml docs/superpowers/specs/engram/foundations.md
git commit -m "fix(spec): add foundation to enforcement_mechanism precedence chain (SY-1 P0)

Resolves the three-way authority tangle between spec.yaml, foundations.md,
and enforcement.md. Foundation now has formal authority over enforcement
exception governance in the enforcement_mechanism claim family."
```

---

### Task 2: Fix guard Branch 1 non-existent file fallthrough (SY-2)

**Finding:** When Branch 1 matches an `engine_*.py` Bash pattern but the script file does not exist, the guard silently falls through to Branch 3/4 (allow). A non-existent engine script is not a legitimate invocation — it should block with a diagnostic.

**Root cause:** Branch 1 file-nonexistence path treats missing files as "not my problem" rather than "suspicious invocation."

**Files:**
- Modify: `docs/superpowers/specs/engram/enforcement.md:161-177`

- [ ] **Step 1: Change Branch 1 non-existent file behavior from fallthrough to block**

In `enforcement.md`, replace the guard decision algorithm block (lines 159-173) with:

```
engram_guard decision algorithm:
  1. If tool_name == Bash AND matches engine_*.py pattern:
     → Verify the Bash target matches an existing engine script file.
       If the file does not exist: block (exit code 2) with diagnostic:
         "engram_guard: engine script not found at {resolved_path} —
          invocation blocked. Expected scripts: {comma-separated list of
          existing engine_*.py files in engram_scripts_dir}."
       If the file exists: Engine trust injection (write TrustPayload, allow)
  2. If tool_name in {Write, Edit} AND path within Context private root:
     → Direct-write path authorization (allow + post-write quality)
  3. If tool_name in {Write, Edit} AND path in protected-path table:
     → Block with path-class diagnostic
  4. Otherwise:
     → Allow unconditionally (engram_guard does not restrict general writes)
Branches evaluated in this order. Step 2 failing the Context-ownership check (path not within Context private root) silently falls through — execution continues to step 3 (protected-path check) or step 4 (allow unconditionally).
No diagnostic is emitted when Step 2 fails — silent fall-through to Step 3 is correct behavior for general writes. Context path authorization failure is surfaced indirectly by /triage anomaly detection (snapshot missing session_id), not by the guard.
```

**Key changes:**
- "skip trust injection (fall through to branch 3/4)" → "block (exit code 2) with diagnostic"
- Added diagnostic message format with the resolved path and list of expected scripts
- Everything else unchanged

- [ ] **Step 2: Update the inactive capability behavior paragraph**

In `enforcement.md` line 177, the text about inactive capabilities mentions "silent allow" which is fine for inactive branches but should not apply to the non-existent file case when the capability IS active. Verify the current text at line 177 does not conflict with the new Branch 1 block behavior.

Read line 177. The text says "When a capability is inactive, its branch is skipped (no-op)." This is about inactive capabilities, not about the active-but-file-missing case. No change needed — the existing text is scoped correctly.

- [ ] **Step 3: Check degraded mode behavior is consistent**

Read `enforcement.md` lines 285-300 (worktree_id/session_id unavailable behavior). Verify that Branch 1's degraded mode ("Engine trust injection blocked" for missing worktree_id/session_id) is consistent with the new non-existent-file block.

Expected: Consistent. Both degraded mode and non-existent file now block rather than fall through. No changes needed.

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/specs/engram/enforcement.md
git commit -m "fix(spec): block non-existent engine files in guard Branch 1 (SY-2 P0)

Changes Branch 1 file-nonexistence from silent fallthrough (allow) to
block (exit code 2) with a diagnostic listing expected engine scripts.
A pattern match against a missing file is suspicious, not benign."
```

---

### Task 3: Fix gated mode definition contradiction (SY-3)

**Finding:** operations.md line 30 says "Knowledge staging requires explicit user confirmation before staging-meta is written." Line 32 says "/distill auto-stages candidates without user confirmation." These directly contradict each other. The gate point is at publication (`/curate`), not at staging (`/distill`).

**Root cause:** The `gated` definition describes the gate at the wrong point in the pipeline.

**Files:**
- Modify: `docs/superpowers/specs/engram/operations.md:30`

- [ ] **Step 1: Rewrite the gated mode definition**

In `operations.md` line 30, replace:

```
**gated:** Knowledge staging requires explicit user confirmation before staging-meta is written. The Knowledge engine presents candidates and waits for approval. Used for the Knowledge staging inbox. `gated` mode is independent of Work modes (`suggest`, `auto_audit`).
```

with:

```
**gated:** Staged Knowledge candidates require explicit user review via `/curate` before publication to `learnings.md`. The staging write itself (`/distill`) is automatic — no user confirmation is required to write staging-meta. The gate is at publication, not at staging. `gated` mode is independent of Work modes (`suggest`, `auto_audit`).
```

**Why:** The gate point is `/curate` (publication), not `/distill` (staging). Line 32 already says "/distill auto-stages candidates without user confirmation" — the rewrite makes line 30 consistent with line 32 rather than contradicting it.

- [ ] **Step 2: Verify line 32 is now consistent (no edit needed)**

Read `operations.md` line 32. Expected:

```
**Knowledge staging autonomy:** `/distill` auto-stages candidates without user confirmation; `/learn` publishes directly via the Knowledge engine. Staged candidates require user review via `/curate` before publication.
```

This is consistent with the new line 30. No change needed.

- [ ] **Step 3: Verify enforcement.md §Autonomy Model references are consistent**

Read `enforcement.md` line 376. Expected: `| Knowledge staging | gated | See operations.md §Work Mode Definitions |`. The enforcement table delegates to operations.md for behavioral semantics — it doesn't restate the contradiction. No change needed.

- [ ] **Step 4: Verify skill-surface.md /curate description matches**

Grep for `/curate` in `skill-surface.md` to confirm the skill description matches the corrected `gated` semantics (review staged candidates before publication).

Run: `rg "curate" docs/superpowers/specs/engram/skill-surface.md`

Expected: `/curate` description mentions reviewing staged candidates. Consistent with corrected definition.

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/specs/engram/operations.md
git commit -m "fix(spec): correct gated mode gate point — publication, not staging (SY-3 P0)

The gated definition said staging requires user confirmation, directly
contradicting /distill's auto-staging behavior two lines later. The actual
gate is at /curate (publication), not /distill (staging)."
```

---

### Task 4: Define engram_register event type in Event Vocabulary (SY-4)

**Finding:** `engram_register` hook's sole purpose is ledger append, but no event type is defined in the Event Vocabulary v1. No `event_type` string, no payload shape, no `record_ref` population rule. The hook cannot be implemented from the spec.

**Root cause:** Event Vocabulary v1 lists only engine/orchestrator events. The "hook" producer class is described in §Producer Classes but has zero event types.

**Files:**
- Modify: `docs/superpowers/specs/engram/types.md:479-502`
- Verify: `docs/superpowers/specs/engram/enforcement.md:16` (hook table reference)

- [ ] **Step 1: Add write_observed event type to Event Vocabulary table**

In `types.md`, after line 485 (the `distill_completed` row), add a new row to the Event Vocabulary table:

```
| `write_observed` | hook | `{path: str, tool_name: str, path_class: str}` | `null` | Protected-path write observation. `engram_register` fires on Write/Edit to paths in the protected-path table where "Register Fires? = Yes". `path_class` matches the path class name from enforcement.md §Protected-Path Enforcement. |
```

- [ ] **Step 2: Add write_observed record_ref population rule**

After the existing `record_ref` population rule paragraph (line 487), add:

```
For `write_observed`, `record_ref` is `null` — hook events observe file paths, not Engram records. Producers must not attempt to construct a `RecordRef` from the file path. The `path` field in the payload serves as the human-readable locator.
```

- [ ] **Step 3: Add write_observed to the "Excluded from v1" note context**

Read line 497. The text says "Excluded from v1: /learn, /curate, and /promote do not emit completion events." This is about completion events from those skills. `write_observed` is not a completion event — it's an observation event. No conflict. No change needed.

- [ ] **Step 4: Verify enforcement.md hook table reference resolves**

Read `enforcement.md` line 16. Expected: `engram_register` links to `types.md#producer-classes`. Verify the link anchor still resolves after the vocabulary addition.

The link target is `types.md#producer-classes` (line 499+). The new row is added to the Event Vocabulary table (above §Producer Classes). The anchor is unchanged. No fix needed.

However, the hook table at line 16 says "Ledger append (hook-class events)" — this is now properly grounded by `write_observed`. No text change needed; the reference is now satisfied.

- [ ] **Step 5: Verify VR-4A-20 test compatibility**

Read `delivery.md` for VR-4A-20 references. The test requires ledger events from `engram_register`. Verify the test description is compatible with the new `write_observed` event type.

Run: `rg "VR-4A-20" docs/superpowers/specs/engram/delivery.md`

Expected: VR-4A-20 should reference `engram_register` failure producing `.diag` entries. The test is about the failure path, not the success event. No conflict with the new event type definition.

- [ ] **Step 6: Commit**

```bash
git add docs/superpowers/specs/engram/types.md
git commit -m "fix(spec): add write_observed event type for engram_register (SY-4 P0)

The hook producer class had zero defined event types. Adds write_observed
(hook producer, null record_ref) with path, tool_name, and path_class
payload fields. engram_register can now be implemented from the spec."
```

---

### Task 5: Add distill arm to triage inference matrix tests (SY-5)

**Finding:** VR-4A-9 and VR-4A-10 test only the `save_expected_defer` arm of the 4-case triage inference matrix. The `save_expected_distill` arm — with staged Knowledge candidates and `distill_completed` events — has zero VR coverage.

**Root cause:** Test was written for the defer arm and the distill arm was never added.

**Files:**
- Modify: `docs/superpowers/specs/engram/delivery.md:307-308`

- [ ] **Step 1: Read the normative inference matrix in operations.md**

Read `operations.md` lines 93-101 to confirm the 4-case matrix applies symmetrically. Expected:

```
(1) expected_X: true + downstream record exists         -> satisfied
(2) expected_X: false + no downstream                   -> intentionally skipped
(3) expected_X: true + no downstream + X_completed      -> zero-output success
(4) expected_X: true + no downstream + no completion    -> "completion not proven"
```

where `X` is a placeholder for both `defer` and `distill`. Confirm the matrix is symmetric before writing tests.

- [ ] **Step 2: Extend VR-4A-9 with distill arm cases**

In `delivery.md`, after line 307 (the VR-4A-9 defer test), add the distill extension:

```
- Triage inference matrix — distill arm (VR-4A-9 extension): fixture with expected_distill=true + staged Knowledge candidate exists → satisfied; expected_distill=false + no staged candidate → skipped; expected_distill=true + no staged candidate + distill_completed(emitted_count=0) → zero-output success; expected_distill=true + no staged candidate + no completion event → completion-not-proven. These four cases mirror the defer arm exactly, substituting `save_expected_distill` for `save_expected_defer`, staged Knowledge candidates for ticket records, and `distill_completed` for `defer_completed`.
```

- [ ] **Step 3: Extend VR-4A-10 with distill arm cases**

In `delivery.md`, after line 308 (the VR-4A-10 ledger-off test), add the distill extension:

```
- Triage ledger-off inference — distill arm (VR-4A-10 extension): same distill fixture as VR-4A-9 extension but with `ledger.enabled=false`. Assert: cases (3) and (4) both report "completion not proven (ledger unavailable)" — no zero-output-success distinction. Assert: qualifier `reason=ledger_disabled` present on all collapsed cases. Mirrors the defer ledger-off test exactly.
```

- [ ] **Step 4: Verify the VR-4A-NEW-1 test is not a duplicate**

Read delivery.md for VR-4A-NEW-1 references. The VR-1 finding notes that "VR-4A-NEW-1 tests that `distill_completed` emits `emitted_count: 0` on full-dedup, but does not test `/triage` reading it through the inference matrix."

Run: `rg "VR-4A-NEW-1" docs/superpowers/specs/engram/delivery.md`

Verify VR-4A-NEW-1 is about event emission (engine side), not inference (triage side). The new tests are about triage reading the events — no overlap.

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/specs/engram/delivery.md
git commit -m "fix(spec): add distill arm to triage inference matrix tests (SY-5 P0)

VR-4A-9 and VR-4A-10 tested only the defer arm of the 4-case inference
matrix. Adds symmetric distill test cases covering save_expected_distill
with staged candidates and distill_completed events."
```

---

## Verification

After all 5 tasks are complete, run a final cross-reference check:

- [ ] **Final Step: Verify all P0 changes are consistent**

1. Read `spec.yaml` — confirm `enforcement_mechanism` chain is `[enforcement, foundation, operations, decisions]`
2. Read `enforcement.md` lines 159-177 — confirm Branch 1 blocks non-existent files
3. Read `operations.md` lines 30-32 — confirm gated definition and Knowledge staging autonomy are consistent
4. Read `types.md` Event Vocabulary table — confirm `write_observed` row present
5. Read `delivery.md` lines 307-310 — confirm both defer and distill VR-4A-9/10 cases present
6. Run: `rg "enforcement_mechanism" docs/superpowers/specs/engram/` — no references to old 3-element chain
7. Run: `rg "fall through" docs/superpowers/specs/engram/enforcement.md` — no fallthrough for non-existent files
