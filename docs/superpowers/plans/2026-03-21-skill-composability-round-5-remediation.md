# Skill Composability Round 5 Remediation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remediate all 31 findings (1 P0, 18 P1, 12 P2) from the round 5 spec review of the skill-composability specification.

**Architecture:** Pure spec-text remediation — no code changes. All edits target markdown files in `docs/superpowers/specs/skill-composability/`. Findings are grouped by dependency layer: behavioral contracts first (blocks verification), then authority/enforcement architecture (independent), then verification coverage (depends on behavioral contracts), then cross-references and P2s (independent). Two ambiguity resolutions (SY-4, SY-31) were resolved via Codex dialogue — fix text is prescribed.

**Tech Stack:** Markdown spec files. Git for version control.

**Spec directory:** `docs/superpowers/specs/skill-composability/`

**Review report:** `.review-workspace/synthesis/report.md`

**Review ledger:** `.review-workspace/synthesis/ledger.md`

---

## File Map

| File | Tasks | Edits |
|------|-------|-------|
| `routing-and-materiality.md` | 1, 2, 3, 4 | SY-3, SY-2, SY-4 (×2), SY-31, SY-29, SY-12, SY-25, SY-26 |
| `verification.md` | 2, 3, 4 | SY-6, SY-7, SY-17, SY-18, SY-20, SY-22, SY-23, SY-27, SY-8, SY-19, SY-21, SY-24, SY-30 |
| `foundations.md` | 2, 4 | SY-5, SY-1 |
| `spec.yaml` | 2, 4 | SY-9, SY-10 |
| `pipeline-integration.md` | 4 | SY-13, SY-15 |
| `delivery.md` | 4 | SY-16, SY-28 |
| `capsule-contracts.md` | 4 | SY-14 |
| `README.md` | 4 | SY-11 |

---

### Task 1: Fix behavioral contracts in routing-and-materiality.md

**Findings:** SY-3 (P0), SY-2 (P1★★★), SY-4 (P1★★), SY-31 (P1), SY-29 (P1)

**Files:**
- Modify: `docs/superpowers/specs/skill-composability/routing-and-materiality.md`

**Context:** This file contains the spec's most complex behavioral logic. 11 of 18 P1 findings touch it. The P0 is here. The two Codex-resolved ambiguities (SY-4, SY-31) are here. Fix these contracts before writing verification rows (Task 3 depends on this).

- [ ] **Step 1: Create working branch**

```bash
git checkout -b fix/skill-composability-round-5-remediation main
```

- [ ] **Step 2: Fix SY-3 (P0) — add materiality_source correction action**

In `routing-and-materiality.md` line 73, within the emission-time enforcement paragraph, find:

```
an entry with `materiality_source` outside this set is an unexpected-state error; log a structured warning with the original value.
```

Replace with:

```
an entry with `materiality_source` outside this set is an unexpected-state error; correct to `materiality_source: rule` and log a structured warning with the original value.
```

In the same paragraph (line 73), find:

```
The correction pipeline preserves `materiality_source` unchanged — meaning an invalid value set during materiality evaluation propagates to the wire format unless caught by this gate.
```

Replace with:

```
The correction pipeline preserves `materiality_source` unchanged — meaning an invalid value set during materiality evaluation is corrected to `rule` at this gate before reaching the wire format.
```

- [ ] **Step 3: Fix SY-2 (P1) — add hop suppression to partial correction failure post-abort**

In `routing-and-materiality.md` line 77, find the post-abort behavior paragraph ending with:

```
(4) the structured warning MUST include the failing entry's index and the unexpected state values to support debugging. The skill invocation is NOT terminated — only capsule emission is skipped.
```

Replace with:

```
(4) the structured warning MUST include the failing entry's index and the unexpected state values to support debugging, (5) hop suggestion text MUST NOT be emitted in the prose output — routing classification state is incomplete (parallel to [Step 0 case (c)](#material-delta-gating) post-abort behavior). The skill invocation is NOT terminated — only capsule emission is skipped.
```

- [ ] **Step 4: Fix SY-4 Edit 1 — update Ambiguous Item Behavior table cell**

Resolution: Two-stage model (Codex dialogue convergence, high confidence). Items enter the correction pipeline, rule 1 fires, then placement stage excludes them.

In `routing-and-materiality.md` line 39, find the table row:

```
| `material: false` + `suggested_arc: ambiguous` | Informational only. Reported to user but does not surface as a routing decision. No hop suggested. Corrected to `dialogue_continue` before capsule emission (rule 1). |
```

Replace with:

```
| `material: false` + `suggested_arc: ambiguous` | Informational only. Reported to user but does not surface as a routing decision. No hop suggested. Corrected to `dialogue_continue` (rule 1); omitted from `feedback_candidates[]` and `unresolved[]` as informational-only. |
```

- [ ] **Step 5: Fix SY-4 Edit 2 — update prose below table**

In `routing-and-materiality.md` line 42, find:

```
For `material: false` + `ambiguous` items, "reported to user" means included in prose synthesis output only — not in `feedback_candidates[]` or `unresolved[]`. These items do not appear in the machine-readable capsule. They are excluded from capsule assembly before the correction pipeline runs.
```

Replace with:

```
For `material: false` + `ambiguous` items, "reported to user" means included in prose synthesis output only. These items pass through the correction pipeline first; rule 1 normalizes `suggested_arc` to `dialogue_continue`, and the placement stage then omits them from `feedback_candidates[]` and `unresolved[]`. They appear in prose synthesis only — not in the machine-readable capsule.
```

- [ ] **Step 6: Fix SY-31 — replace budget counter example**

Resolution: "Non-root" qualifier is correct; example is wrong (Codex dialogue convergence, high confidence). Budget threshold 2 permits one complete validation loop [AR→NS→AR-re-review].

In `routing-and-materiality.md` line 184, find:

```
For example: a chain containing [AR (`adversarial_review`), NS (`next_steps_plan`)] has counter = 2 (two cross-skill hops). A chain containing [AR, NS, dialogue_feedback] also has counter = 2 (dialogue_feedback excluded). This counts per-artifact, not per-transition — each non-root artifact that passed consumption discovery and has a qualifying `artifact_kind` adds 1 to the counter.
```

Replace with:

```
For example: if AR is the root, a chain [AR, NS] has counter = 1 because NS is the only valid non-root artifact. A chain [AR, NS, AR-re-review] has counter = 2 because NS and AR-re-review are both valid non-root artifacts — this reaches the default targeted-loop limit. A chain [AR, NS, dialogue_feedback] has counter = 1 (AR excluded as root, dialogue_feedback excluded from the valid set). This counts per-artifact, not per-transition — each non-root artifact that passed consumption discovery and has a qualifying `artifact_kind` adds 1 to the counter.
```

- [ ] **Step 7: Fix SY-29 — clarify decomposition_seed detection mechanism**

In `routing-and-materiality.md` line 97, find the entire paragraph:

```
The `tautology_filter_applied` flag is set by the decomposition seeding stage when the [tautology filter](pipeline-integration.md#three-tier-tautology-filter) runs successfully (see [pipeline-integration.md](pipeline-integration.md#two-stage-admission) Stage B capability flags). This flag is the enforceable state signal — the materiality evaluator checks this flag, not the historical execution path (flag set by [pipeline-integration.md](pipeline-integration.md#two-stage-admission) Stage B). Case (c) is restricted to scenarios where decomposition was attempted (`decomposition_seed` was used) because `tautology_filter_applied: false` is expected and correct when decomposition did not run (case d).
```

Replace with:

```
The `tautology_filter_applied` flag is set by the decomposition seeding stage when the [tautology filter](pipeline-integration.md#three-tier-tautology-filter) runs successfully (see [pipeline-integration.md](pipeline-integration.md#two-stage-admission) Stage B capability flags). The materiality evaluator detects "decomposition_seed was used" by checking whether `upstream_handoff.decomposition_seed` is `true` in the capability flags set by the adapter at Stage B. This is a direct flag read, not a historical execution trace — the evaluator does not re-derive whether decomposition actually ran. Case (c) fires when both conditions hold: `decomposition_seed: true` AND `tautology_filter_applied ∈ {false, absent}`. Case (c) is restricted to scenarios where decomposition was attempted because `tautology_filter_applied: false` is expected and correct when decomposition did not run (case d).
```

- [ ] **Step 8: Verify internal consistency**

Read routing-and-materiality.md and confirm:
1. The emission-time gate (line 73) now corrects BOTH `classifier_source` and `materiality_source` (SY-3)
2. Both abort paths (line 77 partial correction, line 94 Step 0 case c) enumerate hop suppression (SY-2)
3. The table (line 39) and prose (line 42) agree on the two-stage model: correction first, then placement exclusion (SY-4)
4. The budget example (line 184) is consistent with "non-root" counting and the re-review fixture in verification.md line 77 test (4) (SY-31)
5. Step 0 case (c) mechanism at line 94/97 refers to the capability flag, not historical execution (SY-29)

- [ ] **Step 9: Commit**

```bash
git add docs/superpowers/specs/skill-composability/routing-and-materiality.md
git commit -m "fix(spec): remediate P0 + 4 P1 behavioral contracts in routing-and-materiality (SY-3,2,4,31,29)"
```

---

### Task 2: Fix authority and enforcement architecture

**Findings:** SY-5 (P1★★), SY-9 (P1), SY-12 (P1), SY-6 (P1★★), SY-7 (P1★★), SY-25 (P1)

**Files:**
- Modify: `docs/superpowers/specs/skill-composability/foundations.md`
- Modify: `docs/superpowers/specs/skill-composability/spec.yaml`
- Modify: `docs/superpowers/specs/skill-composability/routing-and-materiality.md`
- Modify: `docs/superpowers/specs/skill-composability/verification.md`

- [ ] **Step 1: Fix SY-5 — elevate drift mitigation MUST clause authority**

In `foundations.md`, after line 111 (end of "Versioning and Drift Detection" section), add:

```

The interim drift mitigation protocol ([delivery.md](delivery.md#open-items) item #8) contains load-bearing MUST clauses that enforce this architectural invariant. These MUST clauses carry `architecture_rule` authority by reference — they are enforcement mechanisms for the contract→stub drift detection invariant defined in this section, not independent `implementation_plan` claims. Contradictions between item #8 and this section are spec defects (the architectural invariant governs).
```

- [ ] **Step 2: Fix SY-9 — correct spec.yaml decisions comment**

In `spec.yaml` lines 52-54, find:

```
  # decisions ranked 2nd (after foundation) because locked design decisions constrain
  # behavior — in any genuine cross-claim conflict, locked decisions override runtime
  # behavior files.
```

Replace with:

```
  # decisions ranked 2nd (after foundation) in fallback_authority_order because locked
  # design decisions constrain behavior. Conflicts are resolved via the fallback path
  # — decisions does not appear in claim_precedence and cannot override via that route.
```

- [ ] **Step 3: Fix SY-12 — remove unverifiable hold_reason origination claim**

In `routing-and-materiality.md` line 46, find:

```
The routing-stage attribution is architectural guidance, not a sequencing constraint. `hold_reason` values originate at the routing stage — the capsule schema constraint is downstream enforcement of this routing-layer rule.
```

Replace with:

```
The routing-stage attribution is architectural guidance, not a sequencing constraint — any implementation path that produces `hold_reason: routing_pending` for held ambiguous items satisfies the contract.
```

- [ ] **Step 4: Fix SY-6 — acknowledge grep boundary limitation in verification**

In `verification.md` line 111, find:

```
| `implements_composition_contract: v1` present in participating stubs | [foundations.md](foundations.md#versioning-and-drift-detection) | Automated (interim): `grep -l 'implements_composition_contract: v1'` against known stub paths (adversarial-review, next-steps, dialogue skill files). Fail if any participating stub is missing the marker. `validate_composition_contract.py` adds full semantic validation when implemented |
```

Replace with:

```
| `implements_composition_contract: v1` present in participating stubs | [foundations.md](foundations.md#versioning-and-drift-detection) | Automated (interim): `grep -l 'implements_composition_contract: v1'` against known stub paths (adversarial-review, next-steps, dialogue skill files). Fail if any participating stub is missing the marker. **Limitation:** `grep -l` verifies file-level presence only — it cannot verify the marker appears within active composition stub boundaries (vs. in a comment, example, or disabled section). Boundary-scoped verification is deferred to `validate_composition_contract.py` when implemented |
```

- [ ] **Step 5: Fix SY-7 — add emission-side sentinel enforcement**

In `verification.md` line 60, find:

```
| `dialogue-orchestrated-briefing` sentinel: no external consumers | [capsule-contracts.md](capsule-contracts.md#sentinel-registry) | Structural: verify no skill stub or consumer code path scans for or attempts to parse the `<!-- dialogue-orchestrated-briefing -->` sentinel. Grep-based CI check on stub files and composition contract — fail if any file outside of the dialogue skill's own internal pipeline references this sentinel in a consumption pattern |
```

Replace with:

```
| `dialogue-orchestrated-briefing` sentinel: no external consumers AND no emission to user-visible output | [capsule-contracts.md](capsule-contracts.md#sentinel-registry) | Structural (two checks): (1) **Consumption side:** verify no skill stub or consumer code path scans for or attempts to parse the `<!-- dialogue-orchestrated-briefing -->` sentinel. Grep-based CI check on stub files and composition contract — fail if any file outside of the dialogue skill's own internal pipeline references this sentinel in a consumption pattern. (2) **Emission side:** verify dialogue's output assembly path contains no code branch that writes `<!-- dialogue-orchestrated-briefing -->` to user-visible output. The sentinel MUST appear only in dialogue's internal pipeline state representation. Neither abort path (partial correction failure or Step 0 case c) addresses this sentinel — verify abort paths suppress all sentinel emission, not just the feedback capsule sentinel |
```

- [ ] **Step 6: Fix SY-25 — add tautology_filter_applied key-presence enforcement**

In `verification.md` line 83, find:

```
| NS adapter MUST set `tautology_filter_applied: false` on partial-tier implementation | [pipeline-integration.md](pipeline-integration.md#two-stage-admission) | Behavioral: two test cases — (1) configure NS adapter to execute only Tier 1 of the tautology filter (partial-tier), verify `tautology_filter_applied` is `false` in the resulting `upstream_handoff`, (2) configure all three tiers to execute successfully, verify flag is `true`. These verify the MUST NOT (partial-tier → true) and the positive case |
```

Replace with:

```
| NS adapter MUST set `tautology_filter_applied: false` on partial-tier implementation; explicit `false` preferred over omission | [pipeline-integration.md](pipeline-integration.md#two-stage-admission) | Behavioral: three test cases — (1) configure NS adapter to execute only Tier 1 of the tautology filter (partial-tier), verify `tautology_filter_applied` is `false` in the resulting `upstream_handoff`, (2) configure all three tiers to execute successfully, verify flag is `true`, (3) verify `tautology_filter_applied` key is present (not omitted) in the `upstream_handoff` capability flags regardless of value — assert key existence, not just value. Case (3) enforces the debuggability preference stated in [pipeline-integration.md](pipeline-integration.md#two-stage-admission): explicit `false` is preferable to omission. These verify the MUST NOT (partial-tier → true), the positive case, and key-presence enforcement |
```

- [ ] **Step 7: Verify internal consistency**

1. foundations.md now backs delivery.md item #8 MUST clauses with `architecture_rule` authority (SY-5)
2. spec.yaml comment accurately reflects `decisions` uses fallback path only (SY-9)
3. routing-and-materiality.md hold_reason section has no unverifiable claims (SY-12)
4. verification.md contract drift table acknowledges grep boundary limitation (SY-6)
5. verification.md sentinel test covers both consumption and emission sides (SY-7)
6. verification.md tautology filter test includes key-presence assertion (SY-25)

- [ ] **Step 8: Commit**

```bash
git add docs/superpowers/specs/skill-composability/foundations.md \
        docs/superpowers/specs/skill-composability/spec.yaml \
        docs/superpowers/specs/skill-composability/routing-and-materiality.md \
        docs/superpowers/specs/skill-composability/verification.md
git commit -m "fix(spec): remediate 6 P1 authority and enforcement findings (SY-5,9,12,6,7,25)"
```

---

### Task 3: Add verification coverage

**Findings:** SY-17 (P1), SY-18 (P1), SY-20 (P1), SY-22 (P1), SY-23 (P1), SY-27 (P1)

**Depends on:** Task 1 (behavioral contracts must be settled before writing test expectations)

**Files:**
- Modify: `docs/superpowers/specs/skill-composability/verification.md`

- [ ] **Step 1: Fix SY-17 — extend coherence test for materiality_source**

In `verification.md` line 54, find the end of the coherence test row:

```
Additionally assert `materiality_source` is unchanged by correction (preserved from pre-correction value). Full 24-case validity matrix via materiality harness when implemented |
```

Replace with:

```
Additionally assert `materiality_source` is unchanged by correction (preserved from pre-correction value) AND assert `materiality_source ∈ {rule, model}` on all 6 emitted entries. Add a 7th test case: inject `materiality_source: ambiguous` on one entry → verify the emission-time gate corrects to `materiality_source: rule` and logs a structured warning (exercises the SY-3 correction action). Full 24-case validity matrix via materiality harness when implemented |
```

- [ ] **Step 2: Fix SY-18 — add Step 0 case (c) abort test row**

In `verification.md` line 37, after item 5 of the interim materiality protocol (ending with `(d) `upstream_handoff` present with `decomposition_seed` not used...`), add a new item:

Find:

```
5. The Step 0 precondition: verify that materiality evaluation checks the `upstream_handoff` pipeline state. Four cases:
```

Replace with:

```
5. The Step 0 precondition: verify that materiality evaluation checks the `upstream_handoff` pipeline state. Five cases:
```

Then find:

```
(d) `upstream_handoff` present with `decomposition_seed` not used (`--plan` not set) → precondition satisfied, materiality evaluation proceeds (tautology filter not applicable to non-decomposition scenarios).
```

After this line, add:

```
   Case (c) dedicated post-abort verification (all 5 assertions): (i) no `<!-- dialogue-feedback-capsule:v1 -->` sentinel appears in output, (ii) no capsule body is emitted, (iii) no durable file written at `.claude/composition/feedback/`, (iv) a structured warning containing "tautology_filter_applied" or "precondition" appears in prose output, (v) hop suggestion text MUST NOT appear in prose output — routing classification is in an unknown state. This case is enumerated independently from the partial correction failure post-abort test; do not rely on cross-references between the two abort paths.
```

- [ ] **Step 3: Fix SY-20 — add durable-store supersedes test scenarios**

In `verification.md` line 102, find:

```
| `supersedes` minting rule: reference most recent prior same-kind same-subject artifact | [lineage.md](lineage.md#dag-structure) | Behavioral: three test scenarios — (1) no prior artifact of same kind/subject → `supersedes: null`, (2) one prior artifact of same kind/subject → `supersedes` references that artifact's `artifact_id`, (3) two prior artifacts of same kind/subject with different `created_at` → `supersedes` references the one with latest `created_at` (not earliest, not arbitrary) |
```

Replace with:

```
| `supersedes` minting rule: reference most recent prior same-kind same-subject artifact | [lineage.md](lineage.md#dag-structure) | Behavioral: five test scenarios — (1) no prior artifact of same kind/subject → `supersedes: null`, (2) one prior artifact of same kind/subject → `supersedes` references that artifact's `artifact_id`, (3) two prior artifacts of same kind/subject with different `created_at` → `supersedes` references the one with latest `created_at` (not earliest, not arbitrary), (4) `dialogue_feedback` with durable store: prior `dialogue_feedback` artifact exists at durable path (`.claude/composition/feedback/`) with matching `subject_key` → verify `supersedes` is set by checking the durable store (not just conversation context), (5) `dialogue_feedback` with durable store unavailable: prior artifact's `record_status: write_failed` → verify `supersedes` determination falls through to conversation-local scan. Scenarios (4) and (5) exercise the durable-store lookup path that applies to `dialogue_feedback` artifacts per [routing-and-materiality.md](routing-and-materiality.md#selective-durable-persistence) |
```

- [ ] **Step 4: Fix SY-22 — extend --plan not-set row 4 test for case (d) disambiguation**

In `verification.md` line 84, find:

```
| `--plan` not-set decomposition behavior (rows 4-5) | [pipeline-integration.md](pipeline-integration.md#decomposition-behavior) | Behavioral: two test scenarios — (1) `--plan` not set + `upstream_handoff` present with `gatherer_seed: true` → verify Steps 2-3 receive enriched gatherer prompts from the handoff context (capability flags active), AND verify no decomposition is attempted (Step 0 skipped). (2) `--plan` not set + no `upstream_handoff` → verify dialogue runs exactly its pre-composability behavior with no capability flag injection at any pipeline stage |
```

Replace with:

```
| `--plan` not-set decomposition behavior (rows 4-5) | [pipeline-integration.md](pipeline-integration.md#decomposition-behavior) | Behavioral: three test scenarios — (1) `--plan` not set + `upstream_handoff` present with `gatherer_seed: true` → verify Steps 2-3 receive enriched gatherer prompts from the handoff context (capability flags active), AND verify no decomposition is attempted (Step 0 skipped), AND verify materiality evaluation proceeds normally (Step 0 case d — `decomposition_seed` not used, precondition trivially satisfied). The materiality assertion disambiguates case (d) from case (c): case (c) would abort materiality evaluation, case (d) proceeds. (2) `--plan` not set + no `upstream_handoff` → verify dialogue runs exactly its pre-composability behavior with no capability flag injection at any pipeline stage. (3) `--plan` not set + `upstream_handoff` present with `decomposition_seed: false` (explicit) → verify same behavior as scenario (1): no decomposition attempted, materiality evaluation proceeds (case d). This exercises the explicit-false-vs-absent equivalence for `decomposition_seed` |
```

- [ ] **Step 5: Fix SY-23 — add material:false+ambiguous two-stage placement test**

In `verification.md`, after the `Ambiguous item non-response` row (line 78), add a new row:

Find:

```
| Ambiguous item non-response: hold behavior and unresolved reporting |
```

Before this row, insert:

```
| `material: false` + `ambiguous` two-stage placement: correction then exclusion | [routing-and-materiality.md](routing-and-materiality.md#ambiguous-item-behavior) | Behavioral: invoke dialogue with an item classified as `material: false`, `suggested_arc: ambiguous`. Verify six assertions: (1) rule 1 fires — `suggested_arc` corrected to `dialogue_continue`, (2) `classifier_source` set to `rule` after correction, (3) item does NOT appear in `feedback_candidates[]`, (4) item does NOT appear in `unresolved[]`, (5) item IS mentioned in prose synthesis output (informational-only), (6) negative: no pre-correction `ambiguous` row in machine-readable capsule. This tests the two-stage model: correction pipeline runs first, placement stage excludes afterward |
```

- [ ] **Step 6: Fix SY-27 — add asymmetric timestamp precision test case**

In `verification.md` line 89, find the thread continuation test. Locate scenario (7):

```
(7) Format variation: `thread_created_at: 2026-03-18T14:30:52Z` (no milliseconds) and capsule `created_at: 2026-03-18T14:30:52.001Z` — under string comparison `Z` (char 90) > `.` (char 46) so `52Z` > `52.001Z` (wrong ordering); under parsed numeric comparison: 52.000s < 52.001s → `created_at` is strictly after → fresh start required. This catches a string-comparison implementation bug.
```

After `This catches a string-comparison implementation bug.`, add:

```
(8) Asymmetric precision: `thread_created_at: 2026-03-18T14:30:52.100Z` (milliseconds) and capsule `created_at: 2026-03-18T14:30:52.1Z` (one fractional digit — 100ms when normalized). Both operands MUST be normalized to millisecond precision before comparison per [lineage.md](lineage.md#artifact-id-format). Under normalized comparison: 52.100s = 52.100s → NOT strictly after → continuation permitted. This catches a normalization asymmetry bug where one operand is normalized but the other is not.
```

- [ ] **Step 7: Verify internal consistency**

1. Coherence test (line 54) now asserts materiality_source validity and exercises SY-3 correction (SY-17)
2. Step 0 test now has dedicated case (c) row with all 5 post-abort assertions including hop suppression (SY-18)
3. Supersedes test has durable-store scenarios for dialogue_feedback (SY-20)
4. --plan not-set test disambiguates case (d) from case (c) with materiality assertion (SY-22)
5. New row tests two-stage placement model for material:false+ambiguous (SY-23)
6. Thread continuation test has asymmetric precision case (SY-27)

- [ ] **Step 8: Commit**

```bash
git add docs/superpowers/specs/skill-composability/verification.md
git commit -m "fix(spec): add 6 P1 verification coverage findings (SY-17,18,20,22,23,27)"
```

---

### Task 4: Fix cross-references and P2 findings

**Findings:** SY-13 (P1), SY-21 (P1), SY-1 (P2), SY-8 (P2), SY-10 (P2), SY-11 (P2), SY-14 (P2), SY-15 (P2), SY-16 (P2), SY-19 (P2), SY-24 (P2), SY-26 (P2), SY-28 (P2), SY-30 (P2)

**Files:**
- Modify: `docs/superpowers/specs/skill-composability/pipeline-integration.md`
- Modify: `docs/superpowers/specs/skill-composability/verification.md`
- Modify: `docs/superpowers/specs/skill-composability/foundations.md`
- Modify: `docs/superpowers/specs/skill-composability/spec.yaml`
- Modify: `docs/superpowers/specs/skill-composability/delivery.md`
- Modify: `docs/superpowers/specs/skill-composability/capsule-contracts.md`
- Modify: `docs/superpowers/specs/skill-composability/README.md`

#### P1 cross-references

- [ ] **Step 1: Fix SY-13 — add NS fallback provenance cross-reference in pipeline-integration.md**

In `pipeline-integration.md` line 24, find the Stage A rejection paragraph ending with:

```
The pipeline proceeds with the "no `upstream_handoff`" rows in the Decomposition Behavior table. The `tautology_filter_applied` flag is absent (consistent with "no upstream handoff" — see [routing-and-materiality.md](routing-and-materiality.md#material-delta-gating) Step 0 case b).
```

After this sentence, add:

```
When operating in fallback mode (no valid NS handoff consumed), the dialogue feedback capsule MUST omit `source_artifacts` entries for any NS artifact — see [capsule-contracts.md](capsule-contracts.md#contract-3-dialogue-feedback-capsule) provenance rule and the parallel [Contract 1 provenance rule](capsule-contracts.md#consumer-class-contract-1).
```

- [ ] **Step 2: Fix SY-21 — add "when authored" qualifier to topic_key grep scope**

In `verification.md` line 104, find:

```
Structural: grep-based check on skill stub files and composition contract — fail if `topic_key` appears in any conditional branch, budget counter expression, or staleness detection predicate. Confirm `lineage_root_id` (not `topic_key`) is the variable used in budget enforcement logic. Scope: all three participating skill stubs and the composition contract file |
```

Replace with:

```
Structural: grep-based check on skill stub files and composition contract (when authored) — fail if `topic_key` appears in any conditional branch, budget counter expression, or staleness detection predicate. Confirm `lineage_root_id` (not `topic_key`) is the variable used in budget enforcement logic. Scope: all three participating skill stubs; the composition contract file is included in scope when authored (see [delivery.md](delivery.md#open-items) item #6 — the contract is a P0 open item that does not yet exist). Interim scope is skill stub files only |
```

#### P2 findings — foundations.md

- [ ] **Step 3: Fix SY-1 — correct stale spec.yaml line reference**

In `foundations.md` line 69, find:

```
See spec.yaml lines 57-61 for the external authority positioning comment (composition contract and inline stubs positioned in the authority hierarchy).
```

Replace with:

```
See spec.yaml lines 63-67 for the external authority positioning comment (composition contract and inline stubs positioned in the authority hierarchy).
```

#### P2 findings — spec.yaml

- [ ] **Step 4: Fix SY-10 — add rationale for decisions fallback placement**

In `spec.yaml` line 55, find:

```
  fallback_authority_order: [foundation, decisions, capsule-contract, routing, pipeline, lineage, delivery-plan, delivery-verification, supporting]
```

After this line, add a comment:

```
  # decisions above capsule-contract in fallback: decisions (D1-D5) define structural
  # constraints that interface contracts must respect. decisions does not hold
  # interface_contract claims, so claim_precedence never applies — only fallback.
```

#### P2 findings — verification.md

- [ ] **Step 5: Fix SY-8 — add file-exists fixture for consumer record_status absent test**

In `verification.md` line 58, find the consumer test case (3):

```
(3) feedback capsule with `record_path` pointing to a file path AND `record_status` field entirely absent (emitter bug) → consumer emits one-line prose warning and falls through to conversation-local sentinel scan (precedence level 3); verify consumer does NOT attempt to read the file at `record_path` and does NOT block.
```

Replace with:

```
(3) feedback capsule with `record_path` pointing to a file path that exists on disk AND `record_status` field entirely absent (emitter bug) → consumer emits one-line prose warning and falls through to conversation-local sentinel scan (precedence level 3); verify consumer does NOT attempt to read the file at `record_path` (even though it exists) and does NOT block. The file-exists fixture is required to distinguish this test from case (2) — without a real file at the path, absent `record_status` and missing file are indistinguishable.
```

- [ ] **Step 6: Fix SY-19 — add budget override re-suppression verification**

In `verification.md` line 80, find:

```
(3) after the override hop completes, hop suggestions are again omitted (budget does not reset — each override permits exactly one more hop) |
```

Replace with:

```
(3) after the override hop completes, hop suggestions are again omitted (budget does not reset — each override permits exactly one more hop). Verify re-suppression explicitly: after the override hop, simulate one more material hop → verify hop suggestion is suppressed again (not permanently re-enabled by the override) |
```

- [ ] **Step 7: Fix SY-24 — correct consumption discovery test mechanism**

In `verification.md` line 95, find the durable store test scenario (3):

```
(3) durable store step-0 (`dialogue_feedback` only): durable file exists at `record_path` → prefer durable result over conversation-local scan;
```

Replace with:

```
(3) durable store step-0 (`dialogue_feedback` only): durable file exists with matching `subject_key` → prefer durable result over conversation-local scan (discovery uses `subject_key` matching per [lineage.md](lineage.md#consumption-discovery), not `record_path` lookup);
```

- [ ] **Step 8: Fix SY-30 — acknowledge grep CI variable-assignment limitation**

In `verification.md` line 57, find:

```
Grep-based CI check on skill stub files and composition contract: fail if `classifier_source.*ambiguous` appears in any assignment.
```

Replace with:

```
Grep-based CI check on skill stub files and composition contract: fail if `classifier_source.*ambiguous` appears in any direct assignment. **Limitation:** grep cannot detect variable-assigned paths where `classifier_source` is set to a variable that evaluates to `ambiguous` at runtime. This is an accepted coverage gap for the interim grep-based check — `validate_composition_contract.py` may add static analysis when implemented.
```

#### P2 findings — pipeline-integration.md

- [ ] **Step 9: Fix SY-15 — clarify tautology_filter_applied: false MUST inertness**

In `pipeline-integration.md` line 39, find the `tautology_filter_applied` capability flag row's NS Adapter Sets cell. At the end of the cell, after `but explicit `false` is preferable for debuggability.`, add:

```
**Functional note:** absence and explicit `false` are treated identically by the materiality evaluator — both result in Step 0 case (c) firing when `decomposition_seed: true`. The MUST for explicit `false` exists for debuggability (distinguishing "adapter ran and failed" from "adapter did not set the flag"), not for behavioral differentiation.
```

#### P2 findings — delivery.md

- [ ] **Step 10: Fix SY-16 — add cross-reference from delivery.md item #7 to verification.md**

In `delivery.md` line 50, find the item #7 row:

```
| 7 | Materiality validation harness | **P0 blocker** | Materiality fixtures per [verification.md](verification.md#interim-materiality-verification-protocol) (authoritative test design), 24-case validity matrix table, clause dependency manifest, Tier 3 calibration suite. The most complex behavioral logic (5 evaluation steps with ordering dependencies) has no test cases. Interim manual verification protocol added — see [verification.md](verification.md#interim-materiality-verification-protocol). See [verification.md](verification.md) for the full verification map. Section references are provisional — use semantic names (e.g., "the Materiality Fixtures section" and "the Correction Rules Table section") rather than numeric references until the composition contract is authored. |
```

In the Notes column, after `Interim manual verification protocol added — see [verification.md](verification.md#interim-materiality-verification-protocol).`, add:

```
The verification test design (table rows, test scenarios, assertion criteria) lives in [verification.md](verification.md#routing-and-materiality-verification) — this item tracks the harness implementation, not the test specification.
```

- [ ] **Step 11: Fix SY-28 — add closure timeline note for helper-mediated delegation gap**

In `delivery.md` line 50, after the item #9 row (end of table), add a note after the table:

```

**Note on enforcement coverage gap:** The helper-mediated indirect delegation detection gap (see [routing-and-materiality.md](routing-and-materiality.md#no-auto-chaining) enforcement coverage note) has no closure timeline in v1. The gap is documented and mitigated by the co-review requirement; deeper static analysis is deferred to `validate_composition_contract.py` (item #6).
```

#### P2 findings — capsule-contracts.md

- [ ] **Step 12: Fix SY-14 — add symmetric cross-references for source_artifacts exclusion**

In `capsule-contracts.md` line 205, find:

```
The feedback capsule MUST omit `source_artifacts` entries for any upstream capsule (NS handoff) that was not structurally consumed — do not reference an NS `artifact_id` that was not validated via the [two-stage admission](pipeline-integration.md#two-stage-admission) process. Parallel to the [Contract 1 provenance rule](#consumer-class-contract-1).
```

Replace with:

```
The feedback capsule MUST omit `source_artifacts` entries for any upstream capsule (NS handoff) that was not structurally consumed — do not reference an NS `artifact_id` that was not validated via the [two-stage admission](pipeline-integration.md#two-stage-admission) process. Parallel to the [Contract 1 provenance rule](#consumer-class-contract-1). Both provenance rules share the same principle: `source_artifacts` entries represent structurally validated provenance, not prose-derived references (see [Contract 1](#consumer-class-contract-1) for the AR→NS direction).
```

#### P2 findings — routing-and-materiality.md

- [ ] **Step 13: Fix SY-26 — note durable file path pre-computation ordering**

In `routing-and-materiality.md` line 240, at the end of the "Path construction rule" paragraph, add:

```
The path pre-computation MUST occur before the correction pipeline gate — the fully-resolved path is needed by the error handler regardless of whether the correction pipeline succeeds or aborts. Ordering relative to the correction gate: compute path → run correction pipeline → write file (if correction succeeds) or reference path in error handler (if correction fails).
```

#### P2 findings — README.md

- [ ] **Step 14: Fix SY-11 — add decisions fallback-only resolution explanation to README**

In `README.md`, locate the Precedence section (line 28). Find:

```
- Fallback: foundation > decisions > capsule-contract > routing > pipeline > lineage > delivery-plan > delivery-verification > supporting
```

After this line, add:

```

**`decisions` conflict resolution:** The `decisions` authority uses the `fallback_authority_order` path for conflict resolution (ranked 2nd, after `foundation`). It does not appear in `claim_precedence` and cannot override via the claim-specific route. See `spec.yaml` for the full precedence rules.
```

- [ ] **Step 15: Verify all cross-references resolve**

For each added cross-reference, confirm the target anchor exists in the target file:
- `capsule-contracts.md#contract-3-dialogue-feedback-capsule` ✓
- `capsule-contracts.md#consumer-class-contract-1` ✓
- `lineage.md#consumption-discovery` ✓
- `pipeline-integration.md#two-stage-admission` ✓
- `routing-and-materiality.md#no-auto-chaining` ✓
- `verification.md#routing-and-materiality-verification` ✓
- `delivery.md#open-items` ✓

- [ ] **Step 16: Commit**

```bash
git add docs/superpowers/specs/skill-composability/pipeline-integration.md \
        docs/superpowers/specs/skill-composability/verification.md \
        docs/superpowers/specs/skill-composability/foundations.md \
        docs/superpowers/specs/skill-composability/spec.yaml \
        docs/superpowers/specs/skill-composability/delivery.md \
        docs/superpowers/specs/skill-composability/capsule-contracts.md \
        docs/superpowers/specs/skill-composability/routing-and-materiality.md \
        docs/superpowers/specs/skill-composability/README.md
git commit -m "fix(spec): remediate 2 P1 cross-refs + 12 P2 findings (SY-13,21,1,8,10,11,14,15,16,19,24,26,28,30)"
```

---

## Finding Coverage Verification

Every SY finding maps to exactly one task and step:

| SY | Priority | Task | Step | Status |
|----|----------|------|------|--------|
| SY-1 | P2 | 4 | 3 | |
| SY-2 | P1 | 1 | 3 | |
| SY-3 | P0 | 1 | 2 | |
| SY-4 | P1 | 1 | 4-5 | |
| SY-5 | P1 | 2 | 1 | |
| SY-6 | P1 | 2 | 4 | |
| SY-7 | P1 | 2 | 5 | |
| SY-8 | P2 | 4 | 5 | |
| SY-9 | P1 | 2 | 2 | |
| SY-10 | P2 | 4 | 4 | |
| SY-11 | P2 | 4 | 14 | |
| SY-12 | P1 | 2 | 3 | |
| SY-13 | P1 | 4 | 1 | |
| SY-14 | P2 | 4 | 12 | |
| SY-15 | P2 | 4 | 9 | |
| SY-16 | P2 | 4 | 10 | |
| SY-17 | P1 | 3 | 1 | |
| SY-18 | P1 | 3 | 2 | |
| SY-19 | P2 | 4 | 6 | |
| SY-20 | P1 | 3 | 3 | |
| SY-21 | P1 | 4 | 2 | |
| SY-22 | P1 | 3 | 4 | |
| SY-23 | P1 | 3 | 5 | |
| SY-24 | P2 | 4 | 7 | |
| SY-25 | P1 | 2 | 6 | |
| SY-26 | P2 | 4 | 13 | |
| SY-27 | P1 | 3 | 6 | |
| SY-28 | P2 | 4 | 11 | |
| SY-29 | P1 | 1 | 7 | |
| SY-30 | P2 | 4 | 8 | |
| SY-31 | P1 | 1 | 6 | |

## Dependency Summary

```
Task 1 (behavioral contracts) ──→ Task 3 (verification coverage)
Task 2 (authority/enforcement) ──→ (no downstream dependencies)
Task 4 (cross-refs + P2s)     ──→ (no downstream dependencies)

Parallel tracks: [Task 1, Task 2, Task 4] can all start simultaneously.
Task 3 must wait for Task 1 to complete.
```
