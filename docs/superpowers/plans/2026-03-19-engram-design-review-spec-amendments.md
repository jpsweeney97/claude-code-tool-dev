# Engram Design Review Spec Amendments

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Amend 7 Engram spec files to address findings F1-F7 and tension T1 from the system design review + Codex dialogue evaluation.

**Architecture:** All changes are markdown spec amendments — no code. Tasks are ordered by file following `spec.yaml` boundary rules: data-contract files first (referenced by later files), normative authority files next, delivery last (verification references all normative changes). Each task edits exactly one file but may address multiple findings.

**Tech Stack:** Markdown spec files at `docs/superpowers/specs/engram/`

**Source of truth:** System design review (this session) + Codex dialogue thread `019d0724-bf36-7181-99a3-ef87a02a121d`. Gate classification:
- **Pre-implementation:** F2, F4, F5, F7
- **Pre-subsystem:** F3, F6, T1
- **Delivery coverage only:** F1

---

### Finding-to-File Map

| Finding | types.md | operations.md | skill-surface.md | storage-and-indexing.md | enforcement.md | decisions.md | delivery.md |
|---------|----------|---------------|-------------------|-------------------------|----------------|--------------|-------------|
| F1 | | | | | | | T1 gates |
| F2 | hash rule | Step 3 contract | | | | | VR new |
| F3 | | B2 change | | | | deferral | VR-10 update |
| F4 | | | rule reframe | | | | cross-cutting |
| F5 | | inference matrix | | degradation row | config note | named risk | VR new |
| F6 | | | | | edge case | | VR new |
| F7 | | anomaly class | | | | risk update | VR new |

---

### Task 1: types.md — Promote Hash Verification Rule (F2)

**Files:**
- Modify: `docs/superpowers/specs/engram/types.md:265` (after Engine Hash Verification section)

This adds the promote-path analog of the existing DistillCandidate hash verification at line 265. The dialogue narrowed F2 from "normalization foot-gun" to a precise gap: Step 3 must recompute from the exact post-write text, not from the pre-edit PromoteEnvelope.

- [ ] **Step 1: Add Promote Hash Verification section**

After the existing "### Engine Hash Verification" section (line 265), insert:

```markdown
### Promote Hash Verification

The Knowledge engine **must** recompute [`drift_hash()`](#hash-producing-functions) on the exact text written to CLAUDE.md in [Step 2](operations.md#promote-knowledge-to-claudemd) and use that value for `PromoteMeta.transformed_text_sha256` in Step 3. The hash input is the final post-confirmation text between markers — not the `PromoteEnvelope.transformed_text` from Step 1.

**Rationale:** The Approve/modify/skip confirmation in Step 2 (Branches C1, C2) allows the user to modify the transformed text before writing. If Step 3 uses the pre-confirmation hash from the envelope, `transformed_text_sha256` would not match the actual CLAUDE.md content, causing spurious drift detection on the next `/promote` run.

**If the exact post-write text is unavailable** (e.g., Step 2 wrote to CLAUDE.md but the skill cannot retrieve the final text between markers), Step 3 **must** reject the promote-meta write rather than persist a hash computed from pre-confirmation text. The lesson remains eligible for the next `/promote` run (same recovery as [Step 2 failure](operations.md#failure-handling)).
```

- [ ] **Step 2: Verify cross-references**

Check that the following anchors exist and resolve correctly:
- `operations.md#promote-knowledge-to-claudemd` (the promote section header)
- `operations.md#failure-handling` (the failure handling table)
- `#hash-producing-functions` (same-file anchor to drift_hash definition)

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/specs/engram/types.md
git commit -m "spec(engram): add promote hash verification rule (F2)

Step 3 must recompute transformed_text_sha256 from exact post-write
text, not pre-edit PromoteEnvelope. Closes the hash ownership gap
identified in the design review Codex dialogue."
```

---

### Task 2: operations.md — Promote, Triage, and Anomaly Amendments (F2, F3, F5, F7)

**Files:**
- Modify: `docs/superpowers/specs/engram/operations.md:62-73,88-118,199-214`

Four amendments in one file. Order: F3 (promote B2 change), F2 (Step 3 contract), F5 (inference matrix), F7 (anomaly class). This order minimizes diff conflicts since F3 and F2 are in the promote section (lines 88-118) while F5 and F7 are in the triage section (lines 57-73).

- [ ] **Step 1: Amend Branch B2 to manual reconcile (F3)**

At lines 92-94, replace:

```
            B2 (target_section changed by user request): Relocation. Search CLAUDE.md for
                markers with lesson_id. If found: move block to new target_section, update
                promote-meta target_section. If not found: manual reconcile flow.
```

With:

```
            B2 (target_section changed by user request): Manual reconcile. Show old
                target_section, new target_section, and existing promoted text (located
                via marker search if markers exist). User places block in new section
                manually. Automated relocation deferred to v1.1 (see
                [deferred decisions](decisions.md#deferred-decisions)).
```

- [ ] **Step 2: Amend Step 2 B2 action (F3)**

At line 108, replace:

```
        For Branch B2: relocate existing marker-enclosed block
```

With:

```
        For Branch B2: manual reconcile — user confirms new placement
```

- [ ] **Step 3: Amend Step 3 with hash recomputation contract (F2)**

At line 112, replace:

```
    -> Step 3 (engine): Knowledge engine writes/updates promote-meta with current hashes
```

With:

```
    -> Step 3 (engine): Knowledge engine recomputes transformed_text_sha256 via
        drift_hash() on the exact post-write text between markers (see
        [Promote Hash Verification](types.md#promote-hash-verification)), then writes/updates promote-meta.
        If post-write text is unavailable, rejects the write (lesson remains eligible).
```

- [ ] **Step 4: Update location strategy note (F3)**

At line 117, replace:

```
**Location strategy:** Branch C and B2 search CLAUDE.md globally for `<!-- engram:lesson:start:<lesson_id> -->` / `<!-- engram:lesson:end:<lesson_id> -->` marker pairs. Global search (not section-scoped) supports user relocation of managed blocks — if the user moves a promoted block to a different section, the marker search still finds it. See [marker specification](types.md#promotion-markers-in-claudemd) for validity rules.
```

With:

```
**Location strategy:** Branch C searches CLAUDE.md globally for `<!-- engram:lesson:start:<lesson_id> -->` / `<!-- engram:lesson:end:<lesson_id> -->` marker pairs. Global search (not section-scoped) supports user relocation of managed blocks — if the user moves a promoted block to a different section, the marker search still finds it. Branch B2 uses the same search for display (showing the user where the current text lives) but does not automate relocation in v1. See [marker specification](types.md#promotion-markers-in-claudemd) for validity rules.
```

- [ ] **Step 5: Update failure handling table entry for B2 (F3)**

At line 211, replace:

```
| Promote Step 2 B2 relocation (markers not found) | CLAUDE.md unchanged | Manual reconcile — user places block in new section; Step 3 records result |
```

With:

```
| Promote Step 2 B2 manual reconcile | User shown old and new target_section, existing promoted text | User places block in new section; Step 3 records result |
```

- [ ] **Step 6: Add ledger-conditional behavior to triage inference matrix (F5)**

After line 68 (the `(4)` case in the inference matrix), insert before the `-> Cross-reference` line:

```
    -> When ledger unavailable (ledger.enabled=false):
        Cases (3) and (4) collapse: expected_X true + no downstream
            -> "completion not proven (ledger unavailable)"
        /triage surfaces reason=ledger_disabled qualifier on all
            collapsed cases. Policy: ledger.enabled=false is supported
            for storage and basic query, but unsupported for
            production-grade /triage completion inference.
```

- [ ] **Step 7: Add anomaly detection class to triage (F7)**

After line 71 (`-> Report promote-meta mismatches (missing or stale)`), insert:

```
    -> Anomaly detection (provenance_not_established):
        Work: tickets in engram/work/ with no corresponding .audit/ entry
        Context/Knowledge: records with malformed or missing native
            provenance fields (e.g., missing session_id in snapshot frontmatter)
        Note: trust triples are transient (hook-to-engine input, not persisted
            in RecordMeta), so generic trust-triple detection is not possible.
            Detection is subsystem-specific using native artifacts.
```

- [ ] **Step 8: Verify cross-references**

Check that these anchors resolve:
- `decisions.md#deferred-decisions` (from Step 1 B2 change)
- `types.md#promote-hash-verification` (from Step 3 — this anchor was created in Task 1)

- [ ] **Step 9: Commit**

```bash
git add docs/superpowers/specs/engram/operations.md
git commit -m "spec(engram): amend promote, triage, and anomaly operations (F2,F3,F5,F7)

F3: B2 branch changes from automated relocation to manual reconcile (v1.1 deferral).
F2: Step 3 now explicitly recomputes transformed_text_sha256 from post-write text.
F5: Triage inference matrix collapses cases 3+4 when ledger unavailable.
F7: Triage gains provenance_not_established anomaly detection (subsystem-specific)."
```

---

### Task 3: skill-surface.md — /save Orchestration Rule Reframing (F4)

**Files:**
- Modify: `docs/superpowers/specs/engram/skill-surface.md:36,40`

The dialogue agreed that "same code paths" is too vague for enforcement. The fix reframes the rule to define a shared programmatic seam and tests delegation at that seam.

- [ ] **Step 1: Reframe rule 1**

At line 36, replace:

```
1. **No unique business logic.** Same code paths as standalone skills.
```

With:

```
1. **Shared entrypoint delegation.** Each `/save` sub-operation must delegate to the same public entrypoint function as its standalone counterpart (`/defer`, `/distill`). The entrypoint is the shared programmatic seam — `/save` is a thin wrapper that calls it, not a reimplementation.
```

- [ ] **Step 2: Update structural verification paragraph**

At line 40, replace:

```
**Structural verification:** `/save` sub-operations should call the same implementation functions as their standalone counterparts. Recommended pattern: thin wrapper that delegates to shared implementation. Verified by code review; structural guard in [delivery.md exit criteria](delivery.md#step-4-context-cutover).
```

With:

```
**Structural verification:** `/save` sub-operations **must** call the same public entrypoint functions as their standalone counterparts. Verified by automated delegation test (spy/parity test that asserts `/save` invokes the shared entrypoint) and code review as backstop. See [delivery.md cross-cutting verification](delivery.md#cross-cutting-verification) for test specification.
```

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/specs/engram/skill-surface.md
git commit -m "spec(engram): reframe /save orchestration rule to shared entrypoint delegation (F4)

Replace vague 'same code paths' with explicit shared-entrypoint delegation
requirement. Verification upgraded from code-review-only to automated
spy/parity test with code review as backstop."
```

---

### Task 4: storage-and-indexing.md — Degradation Model Expansion (F5)

**Files:**
- Modify: `docs/superpowers/specs/engram/storage-and-indexing.md:237`

The current "No ledger" row mentions lower timeline fidelity but doesn't mention the /triage inference degradation. This makes the cost of disabling the ledger visible at the point of decision.

- [ ] **Step 1: Expand ledger degradation row**

At line 237, replace:

```
| No ledger | Timeline uses file timestamps only | Lower fidelity, documented |
```

With:

```
| No ledger | Timeline uses file timestamps only. `/triage` inference cases (3) and (4) [collapse](operations.md#triage-read-work-and-context): zero-output success becomes indistinguishable from incomplete execution. All collapsed cases carry `reason=ledger_disabled` qualifier. | Lower fidelity timeline. `/triage` reports `completion not proven (ledger unavailable)` instead of distinguishing zero-output success. Policy: `ledger.enabled=false` is supported for storage and basic query, but unsupported for production-grade `/triage` completion inference. |
```

- [ ] **Step 2: Verify cross-reference**

Check that `operations.md#triage-read-work-and-context` resolves to the triage section (it uses the section heading "Triage: Read Work and Context").

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/specs/engram/storage-and-indexing.md
git commit -m "spec(engram): expand ledger degradation to include triage inference cost (F5)

Make /triage false-positive risk visible in the degradation model table,
not just in the operations section. Adds explicit policy statement about
ledger.enabled=false support scope."
```

---

### Task 5: enforcement.md — Config Clarification and Staging Cap Edge Case (F5, F6)

**Files:**
- Modify: `docs/superpowers/specs/engram/enforcement.md:143,148-150`

- [ ] **Step 1: Add ledger config note (F5)**

After line 143 (`enabled: true               # Default on. Opt-out here.`), within the YAML code block, add a comment:

```yaml
                                    # Disabling degrades /triage inference —
                                    # see storage-and-indexing.md degradation model.
```

- [ ] **Step 2: Document batch_size > cap edge case (F6)**

After line 150 (the existing Staging Inbox Cap section ending), insert:

```markdown
**Edge case: `batch_size > knowledge_max_stages`.** If a single distill batch produces more candidates than the configured cap (e.g., a rich snapshot yields 15 candidates against a cap of 10), the batch is rejected even with 0 files in staging — the cap applies to `count + batch_size`, and `0 + 15 > 10`. The rejection response must include a diagnostic: `"Batch size (N) exceeds staging cap (M). Increase knowledge_max_stages to at least N in .claude/engram.local.md, or curate existing items to make room."` This is a deliberate consequence of whole-batch rejection. Partial staging (accepting the first N candidates) is a [deferred decision](decisions.md#deferred-decisions).
```

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/specs/engram/enforcement.md
git commit -m "spec(engram): add ledger config note and staging cap edge case (F5, F6)

F5: Inline note in ledger config pointing to degradation consequences.
F6: Document batch_size > cap edge case with required diagnostic message."
```

---

### Task 6: decisions.md — Risks, Deferrals, and Risk Updates (F3, F5, F7)

**Files:**
- Modify: `docs/superpowers/specs/engram/decisions.md:12-23,37-51`

Three changes: add a Named Risk (F5), update an existing risk (F7), add a Deferred Decision (F3).

- [ ] **Step 1: Add ledger-off triage degradation to Named Risks (F5)**

After line 23 (the last risk row for "Promotion marker loss"), insert a new row:

```
| **Ledger-off triage degradation** | Medium | `/triage` inference [cases (3) and (4) collapse](operations.md#triage-read-work-and-context) when `ledger.enabled=false`. Zero-output success becomes indistinguishable from incomplete execution. All collapsed cases carry `reason=ledger_disabled` qualifier. [Degradation model](storage-and-indexing.md#degradation-model). | Disable ledger, run `/save` that produces 0 deferred items, run `/triage` — reports "completion not proven (ledger unavailable)" instead of "zero-output success"? |
```

- [ ] **Step 2: Update Bash enforcement gap risk with anomaly surfacing (F7)**

At line 17, replace the existing Detection column for "Bash enforcement gap":

```
| Bash write to `engram/work/` bypasses guard? Created ticket has no `.audit/` entry? |
```

With:

```
| Bash write to `engram/work/` bypasses guard? Created ticket has no `.audit/` entry? `/triage` [anomaly detection](operations.md#triage-read-work-and-context) surfaces `provenance_not_established` for Work records missing `.audit/` correlation. |
```

- [ ] **Step 3: Add automated promote relocation to Deferred Decisions (F3)**

After line 51 (the last deferred decision for "Promotion bounded search"), insert:

```
| Automated promote relocation (Branch B2) | B2 (target_section changed) uses manual reconcile in v1. Automated marker-enclosed block relocation adds implementation complexity for a rare triggering condition. Add when promote relocation frequency warrants. |
```

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/specs/engram/decisions.md
git commit -m "spec(engram): add risks, update detection, add deferral (F3, F5, F7)

F5: Add ledger-off triage degradation as Medium Named Risk.
F7: Update Bash enforcement gap detection with /triage anomaly surfacing.
F3: Add automated promote relocation (B2) to Deferred Decisions."
```

---

### Task 7: delivery.md — Verification and Compatibility Gates (F1-F7, T1)

**Files:**
- Modify: `docs/superpowers/specs/engram/delivery.md:51,125,153,220,222,271`

This is the largest task — all 8 amendments add or modify verification entries. The amendments are spread across Step 0a (T1), Step 2a (F2), Step 3a (F6), Step 4a (F3, F5, F7), and Cross-Cutting (F4). Apply from earliest step to latest to avoid line-number drift.

- [ ] **Step 1: Add compatibility gate note to Step 0a (T1/F1)**

After line 51 (the VR-14 normalization boundary test), insert:

```markdown
- Field preservation gate (T1-gate-1, activates at Step 2a): verify that rewriting a `lesson-meta` entry with an unknown field preserves that field verbatim. Deferred from Step 0a because field preservation is only exercised when the Knowledge engine performs its first rewrite-capable operation. Scheduled here for traceability; test fixture created in Step 2a.
- Mixed-version degradation gate (T1-gate-2, activates at Step 2a): verify that a `lesson-meta` entry with `meta_version: "99.0"` is skipped per-entry (not per-file) with a warning in `QueryDiagnostics.warnings`. Deferred from Step 0a for the same reason. Scheduled here; test fixture created in Step 2a.
```

- [ ] **Step 2: Add promote hash recomputation verification to Step 2a (F2)**

After line 125 (the VR-15 promote-path wiring check), insert:

```markdown
- Promote hash recomputation (VR-16): simulate the Approve/modify/skip flow where the user modifies transformed text during Step 2 confirmation. Assert: `PromoteMeta.transformed_text_sha256` matches `drift_hash()` of the *post-modification* text written to CLAUDE.md, not the original `PromoteEnvelope.transformed_text`. Separately, assert: if post-write text retrieval fails, Step 3 rejects the promote-meta write (lesson remains eligible for next `/promote`). See [Promote Hash Verification](types.md#promote-hash-verification).
- T1-gate-1 implementation: rewrite a `lesson-meta` entry that contains an extra field `"future_field": "value"`. Assert the rewritten entry still contains `future_field` verbatim.
- T1-gate-2 implementation: create a `lesson-meta` entry with `meta_version: "99.0"`. Run `query()`. Assert: entry is skipped, `QueryDiagnostics.warnings` contains a per-entry message, other entries in the same file are still returned.
```

- [ ] **Step 3: Add staging cap edge case verification to Step 3a (F6)**

After line 153 (the existing VR-8 staging inbox cap test), insert:

```markdown
- Staging cap edge case (VR-17): cap=5, count=0, batch=8 → full rejection with diagnostic message including both batch size and cap values. Assert error message contains "Batch size (8) exceeds staging cap (5)".
```

- [ ] **Step 4: Update VR-10 B2 entry (F3)**

At line 220, in the VR-10 specification, replace:

```
Branch B2 relocates marker-enclosed block to new section; Branch B2 markers missing → manual reconcile (same flow as C3)
```

With:

```
Branch B2 shows old and new target_section plus existing promoted text → user confirms manual placement; Step 3 records updated target_section in promote-meta
```

- [ ] **Step 5: Add F5 and F7 verifications to Step 4a (F5, F7)**

After line 222 (the VR-13 triage inference matrix test), insert:

```markdown
- Triage ledger-off inference (VR-18): same fixture as VR-13 but with `ledger.enabled=false`. Assert: cases (3) and (4) both report "completion not proven (ledger unavailable)" — no zero-output-success distinction. Assert: qualifier `reason=ledger_disabled` present on all collapsed cases.
- Triage provenance anomaly (VR-19): fixture with a ticket in `engram/work/` that has no corresponding `.audit/` entry. Assert: `/triage` reports `provenance_not_established` anomaly for that ticket. Fixture with a snapshot missing `session_id` in frontmatter. Assert: `/triage` reports `provenance_not_established` for that snapshot.
```

- [ ] **Step 6: Replace /save code review entry in Cross-Cutting Verification (F4)**

At line 271, replace:

```
| /save no-unique-logic | Code review: verify `/save` sub-operations delegate to shared implementation | 4a |
```

With:

```
| /save shared-entrypoint delegation | Delegation test: `/save` defer sub-operation calls the same public entrypoint as standalone `/defer`; `/save` distill sub-operation calls the same public entrypoint as standalone `/distill`. Parity test: run both paths with identical input, assert identical output. Code review as backstop. | 4a |
```

- [ ] **Step 7: Verify all VR-ID uniqueness**

Ensure no duplicate VR-IDs exist: VR-1 through VR-15 are pre-existing, new entries are VR-16 (F2), VR-17 (F6), VR-18 (F5), VR-19 (F7). Scan the file for `VR-` to confirm no collisions.

Run: `grep -n 'VR-' docs/superpowers/specs/engram/delivery.md`

- [ ] **Step 8: Commit**

```bash
git add docs/superpowers/specs/engram/delivery.md
git commit -m "spec(engram): add verification entries and compatibility gates (F1-F7, T1)

T1: Wire field preservation and mixed-version degradation gates at Step 2a.
F2: VR-16 promote hash recomputation verification.
F3: Update VR-10 B2 entry to manual reconcile.
F4: Replace code-review-only entry with delegation + parity test.
F5: VR-18 ledger-off triage inference test.
F6: VR-17 staging cap batch_size > cap edge case.
F7: VR-19 provenance anomaly detection test."
```

---

### Task 8: Cross-Reference Validation

**Files:**
- Read: all 7 spec files (verify only, no edits)

After all amendments are committed, validate cross-file references.

- [ ] **Step 1: Verify new anchors resolve**

New anchors created by these amendments:
- `types.md#promote-hash-verification` (created in Task 1, referenced by Task 2 and Task 7)
- `operations.md#triage-read-work-and-context` (existing anchor, newly referenced by Tasks 4, 6)

Run: `grep -rn 'promote-hash-verification\|triage-read-work-and-context' docs/superpowers/specs/engram/`

Confirm each reference has a matching heading anchor in the target file.

- [ ] **Step 2: Verify no broken spec.yaml boundary violations**

Per spec.yaml boundary rules:
- `types.md` changed (data-contract) → review `operations.md` and `enforcement.md` for consistency
- `operations.md` changed → review `skill-surface.md` and `enforcement.md`
- `enforcement.md` changed → review `operations.md`

All of these files were already amended in this plan. Verify:
- The `drift_hash()` reference in operations.md Step 3 (Task 2, Step 3) is consistent with the rule added in types.md (Task 1)
- The anomaly detection added in operations.md (Task 2, Step 7) is not contradicted by enforcement.md
- The staging cap edge case in enforcement.md (Task 5) is consistent with the VR-17 test in delivery.md (Task 7)

- [ ] **Step 3: Final commit (if any corrections needed)**

If cross-reference validation found issues, fix them and commit:

```bash
git add docs/superpowers/specs/engram/
git commit -m "spec(engram): fix cross-references from design review amendments"
```

If no issues: skip this step.
