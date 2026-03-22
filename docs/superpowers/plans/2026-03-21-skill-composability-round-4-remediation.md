# Skill Composability Spec — Round 4 Remediation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remediate 50 findings (1 P0, 26 P1, 23 P2) from the round-4 spec review, producing a single commit that addresses all findings across 9 spec files.

**Architecture:** Spec-editing remediation organized by file. Each task addresses one spec file (or logical group), applying all finding fixes in priority order (P0 → P1 → P2). Verification is grep-based cross-reference checking after each file pass.

**Review source:** `.review-workspace/synthesis/report.md` (canonical prioritized report), `.review-workspace/synthesis/ledger.md` (finding-by-finding inventory with source tracing), `.review-workspace/findings/` (5 reviewer finding files with detailed evidence and recommended fixes).

**Spec location:** `docs/superpowers/specs/skill-composability/`

**Working state:** Two changes already applied to the working tree (partial SY-4 P0 fix + CC-6 verification count update). This plan builds on those changes.

---

## Pre-Remediation: Understand the Finding Clusters

Four defect clusters drive the remediation order — fixes within a cluster are interdependent:

| Cluster | Findings | Root Cause | Critical Path |
|---------|----------|------------|---------------|
| **B: Tautology Filter** | SY-4 (P0), SY-15, SY-17, SY-21, SY-26 | `tautology_filter_applied` flag cross-file split | Fix SY-4 first → cascade |
| **A: Budget Enforcement** | SY-11, SY-18, SY-23 | Counting algorithm contradicts exclusion rules | Fix SY-11 first → cascade |
| **D: README Authority** | SY-1, SY-2, SY-3 | README not updated after spec.yaml changes | Independent |
| **C: Durable Store** | SY-13, SY-27 | Consumer contract underspecified + test gap | Fix SY-13 first → SY-27 |

---

### Task 1: routing-and-materiality.md — Tautology Filter Cluster (P0 + 4 P1)

**Files:**
- Modify: `docs/superpowers/specs/skill-composability/routing-and-materiality.md`

**Findings:** SY-4 (P0), SY-17 (P1), SY-15 (P1), and cross-file pieces of SY-21, SY-26

SY-4 (P0) is already partially applied in the working tree. This task verifies the existing fix and applies the remaining cluster-B fixes to routing-and-materiality.md.

- [ ] **Step 1: Verify SY-4 (P0) fix is complete**

The working tree already has the four-case Step 0 restructure (cases a-d) using `decomposition_seed` as the discriminating predicate. Verify the diff at lines 88-95 matches the recommended fix from CC-4/CE-14/IE-9:
- Case (a): `upstream_handoff` + `tautology_filter_applied: true` → proceed
- Case (b): no `upstream_handoff` → trivially satisfied
- Case (c): `upstream_handoff` + `decomposition_seed` used + `tautology_filter_applied: false/absent` → abort (genuine unexpected state)
- Case (d): `upstream_handoff` + `decomposition_seed` not used → trivially satisfied (filter not applicable)

Run: `grep -n 'decomposition_seed' docs/superpowers/specs/skill-composability/routing-and-materiality.md`
Expected: Cases (c) and (d) reference `decomposition_seed`, with cross-references to `pipeline-integration.md#decomposition-behavior`.

- [ ] **Step 2: Fix SY-17 (P1) — Enumerate Step 0 abort post-abort behaviors**

The Step 0 case (c) abort currently says "analogous to partial correction failure" which is informal, not normative. Replace with explicit enumeration.

At line 92, after "Surface a prose error identifying the failed precondition." add:

```markdown
Post-abort behavior for Step 0 case (c) abort (enumerated — do not rely on "analogous to" cross-references): (1) the dialogue skill MUST complete its normal prose synthesis output — the abort affects only the machine-readable capsule, not the user-facing prose, (2) the sentinel MUST NOT be emitted — suppress both the sentinel comment and the capsule body, (3) no durable file is written at `.claude/composition/feedback/`, (4) the prose error MUST identify the failed precondition (`tautology_filter_applied` is false/absent despite decomposition having run). Hop suggestion text MUST NOT be emitted in the prose output when capsule assembly is aborted — the routing classification is in an unknown state.
```

This also incorporates CE-13 (P2) — prohibiting hop suggestions in post-abort prose.

- [ ] **Step 3: Fix SY-15 (P1) — Add bidirectional cross-references for the flag**

At routing-and-materiality.md line 95 (the paragraph about `tautology_filter_applied`), add at the end:

```markdown
(flag set by [pipeline-integration.md](pipeline-integration.md#two-stage-admission) Stage B)
```

This goes at the end of the sentence: "the materiality evaluator checks this flag, not the historical execution path."

Then in pipeline-integration.md Stage B table (line 39), add to the `tautology_filter_applied` description:

```markdown
(enforcement semantics: [routing-and-materiality.md](routing-and-materiality.md#material-delta-gating) Step 0)
```

- [ ] **Step 4: Verify cross-references resolve**

Run:
```bash
grep -n 'tautology_filter_applied' docs/superpowers/specs/skill-composability/routing-and-materiality.md docs/superpowers/specs/skill-composability/pipeline-integration.md
```
Expected: Both files now cross-reference each other for the flag's definition and enforcement semantics.

---

### Task 2: routing-and-materiality.md — Budget Enforcement Cluster (3 P1 + 1 P2)

**Files:**
- Modify: `docs/superpowers/specs/skill-composability/routing-and-materiality.md`

**Findings:** SY-11/CC-16 (P1), SY-18 (P1), SY-23 (linked — test fixture in Task 5), IE-6 (P2)

- [ ] **Step 1: Fix SY-11 (P1) — Align budget counting algorithm with hop definition**

Three lines at 176-180 must be aligned. The hop definition (line 176) correctly excludes `dialogue_feedback` but the "structurally consumed" definition (line 178) and counting algorithm (line 180) do not.

At line 178 ("represents a cross-skill transition"), change:

Old: `represents a cross-skill transition (\`artifact_kind\` different from the prior artifact in the chain)`
New: `represents a cross-skill transition (\`artifact_kind ∈ {adversarial_review, next_steps_plan}\`) — \`dialogue_feedback\` artifacts are excluded per the targeted loop definition above`

At line 180 ("counts the number of valid artifacts"), change:

Old: `The budget counter counts the number of valid artifacts with distinct \`artifact_kind\` values in the lineage chain sharing the current \`lineage_root_id\`, excluding the root artifact.`
New: `The budget counter counts the number of valid non-root artifacts in the lineage chain sharing the current \`lineage_root_id\` whose \`artifact_kind\` is \`adversarial_review\` or \`next_steps_plan\`. \`dialogue_feedback\` artifacts are excluded — only AR↔NS surface hops consume budget per the targeted loop definition.`

Update the example sentence: `For example: a chain containing [AR (\`adversarial_review\`), NS (\`next_steps_plan\`)] has counter = 2 (two cross-skill hops). A chain containing [AR, NS, dialogue_feedback] also has counter = 2 (dialogue_feedback excluded).`

- [ ] **Step 2: Fix SY-18 (P1) — Replace unimplementable detection heuristic**

At line 184 ("When the scan finds fewer artifacts than expected"), replace the detection condition:

Old: `When the scan finds fewer artifacts than expected (e.g., a feedback capsule references a \`lineage_root_id\` but no prior artifacts with that ID are visible)`
New: `When a feedback capsule in the current conversation context references a \`lineage_root_id\` but no prior artifacts with that \`lineage_root_id\` are visible in available context`

This makes the detection signal concrete and computable.

- [ ] **Step 3: Fix IE-6 (P2) — Replace shorthand with explicit budget scan criteria**

At line 182 ("The scan MUST apply the same acceptance criteria as consumption discovery"), replace:

Old: `The scan MUST apply the same acceptance criteria as consumption discovery — only artifacts with valid sentinels and parseable schemas count.`
New: `The scan MUST count only artifacts with valid sentinels and parseable schemas. Continue scanning past invalid capsules (do not stop at first invalid entry) — unlike consumption discovery's no-backtrack rule, the budget scan is a full-scan algorithm. Raw sentinel text with invalid or unparseable capsule content (e.g., a sentinel comment present but the capsule block malformed) MUST NOT increment the counter.`

- [ ] **Step 4: Add budget cross-reference (CC-8, P2)**

At line 172, after the sentence about `lineage_root_id` usage, add:

```markdown
See [lineage.md](lineage.md#three-identity-keys) for key purposes and [lineage.md](lineage.md#key-propagation) for propagation rules.
```

- [ ] **Step 5: Verify budget section consistency**

Run:
```bash
grep -n 'dialogue_feedback' docs/superpowers/specs/skill-composability/routing-and-materiality.md | head -10
```
Expected: All three counting descriptions (hop definition, structurally consumed, algorithm) now consistently exclude `dialogue_feedback`.

---

### Task 3: routing-and-materiality.md — Enforcement Gates + Behavioral (6 P1 + 4 P2)

**Files:**
- Modify: `docs/superpowers/specs/skill-composability/routing-and-materiality.md`

**Findings:** SY-16, SY-5, SY-7, SY-10, SY-13, SY-19 (P1); CE-6, IE-5, IE-7, CE-9 (P2)

- [ ] **Step 1: Fix SY-16 (P1) — Add classifier_source validation to emission-time enforcement**

At line 71, after the sentence about the correction pipeline being a required gate, add a new sentence:

```markdown
The gate MUST additionally validate `classifier_source ∈ {rule, model}` for every `feedback_candidates[]` entry — an entry with `classifier_source` outside this set is an unexpected-state error; correct to `classifier_source: rule` and log a structured warning with the original value (see also [capsule-contracts.md](capsule-contracts.md#schema-constraints) for the parallel interface-layer constraint).
```

- [ ] **Step 2: Fix SY-5 (P1) — Add materiality_source validation gate**

After the `classifier_source` validation sentence added in Step 1, add:

```markdown
The gate MUST also validate `materiality_source ∈ {rule, model}` for every `feedback_candidates[]` entry — an entry with `materiality_source` outside this set is an unexpected-state error; log a structured warning with the original value. This validation is parallel to `classifier_source` validation. The correction pipeline preserves `materiality_source` unchanged — meaning an invalid value set during materiality evaluation propagates to the wire format unless caught by this gate.
```

Also add to capsule-contracts.md Schema Constraints (Task 7).

- [ ] **Step 3: Fix SY-7 (P1) — Cross-tier guard materiality_source for Tier 1 rule + Tier 2 overlap**

At line 126 (cross-tier guard section), after "the item is material", add:

```markdown
When a Tier 1 rule exclusion is overridden by Tier 2 inclusion, set `material: true`, `materiality_source: rule` (Tier 2 determination — the Tier 2 inclusion is the operative classification, not the Tier 1 exclusion).
```

- [ ] **Step 4: Fix SY-10 (P1) — Define "informational only" placement**

At line 39 (Ambiguous Item Behavior table), after the `material: false` + `ambiguous` row's description, add:

```markdown
For `material: false` + `ambiguous` items, "reported to user" means included in prose synthesis output only — not in `feedback_candidates[]` or `unresolved[]`. These items do not appear in the machine-readable capsule. They are excluded from capsule assembly before the correction pipeline runs.
```

- [ ] **Step 5: Fix SY-13 (P1) — Clarify consumer-side record_status absent + file exists**

At line 230, after the `record_status` absent handling paragraph, add:

```markdown
When `record_status` is absent, fall through to conversation-local scan even if the durable file appears to exist at `record_path` — an absent `record_status` indicates an emitter bug that may have produced a corrupt or incomplete file. Do not attempt to read or use a file when `record_status` is absent.
```

- [ ] **Step 6: Fix SY-19 (P1) — Acknowledge no-auto-chaining enforcement gap**

At line 162, after the capsule-level prohibition paragraph, add:

```markdown
**Enforcement coverage note:** Grep-based CI and stub text review can detect direct invocation patterns and conditional branches but cannot structurally detect helper-mediated indirect delegation chains. Any helper function referenced from a composition stub's feedback capsule assembly path MUST be co-reviewed as part of the stub review and documented in the PR checklist. This is a known coverage gap in the interim enforcement — `validate_composition_contract.py` may add deeper static analysis when implemented.
```

- [ ] **Step 7: Fix IE-5 (P2) — Add record_status: ok MUST for successful write**

At line 232, after the write failure recovery paragraph, add:

```markdown
On a successful durable file write, the emitted capsule MUST set `record_status: ok`. `record_status` MUST always be present; omitting it is an emitter bug (see consumer-side contract above for how absent `record_status` is handled).
```

- [ ] **Step 8: Fix IE-7 (P2) — Standardize abort warning format**

At line 75 (post-abort behavior item 4), change "prose error" to "structured warning" to align with Step 0 abort language:

Old: `the prose error MUST include the failing entry's index`
New: `the structured warning MUST include the failing entry's index`

- [ ] **Step 9: Fix CE-9 (P2) — Clarify consequence prohibition annotation**

At line 82 (prohibition 4), change:

Old: `Material \`diagnosis\`/\`planning\` MUST NOT silently remain \`dialogue_continue\` — enforced by rules 3 and 4`
New: `Material \`diagnosis\`/\`planning\` MUST NOT silently remain \`dialogue_continue\` — enforced by rules 3 and 4, which check \`material = true\` explicitly and correct to the appropriate arc regardless of how \`dialogue_continue\` was assigned`

- [ ] **Step 10: Fix CE-6 (P2) — Add hold_reason attribution note**

At line 44, after the `hold_reason` paragraph, add:

```markdown
Implementations may set `hold_reason` either at the routing stage or at capsule assembly time, provided the value is `routing_pending` for held ambiguous items. The routing-stage attribution is architectural guidance, not a sequencing constraint.
```

---

### Task 4: capsule-contracts.md — Schema and Contract Fixes (3 P1 + 3 P2)

**Files:**
- Modify: `docs/superpowers/specs/skill-composability/capsule-contracts.md`

**Findings:** SY-12, SY-14 (P1), SY-5 (P1 — parallel gate), CC-11, CC-12, CE-12 (P2)

- [ ] **Step 1: Fix SY-14 (P1) — Enumerate feedback capsule recommended_posture values**

At line 192, change the feedback capsule schema:

Old: `recommended_posture: <posture or null>`
New: `recommended_posture: <adversarial | collaborative | exploratory | evaluative | comparative | null>  # same enum as NS handoff schema`

- [ ] **Step 2: Fix SY-12 (P1) — Annotate selected_tasks empty-list invalidity**

At line 110 in the NS handoff schema, change:

Old: `selected_tasks:`
New: `selected_tasks:  # MUST NOT be empty — present but empty [] is invalid per validity criterion (3)`

- [ ] **Step 3: Fix SY-5 (P1) — Add materiality_source validation to Schema Constraints**

At line 217 (Schema Constraints section), after the `classifier_source` validation bullet, add:

```markdown
- **`materiality_source` validation:** The emission-time enforcement gate MUST validate `materiality_source ∈ {rule, model}` for every `feedback_candidates[]` entry, parallel to the `classifier_source` validation. See [routing-and-materiality.md](routing-and-materiality.md#affected-surface-validity) for the enforcement-layer MUST clause.
```

- [ ] **Step 4: Fix CC-11 (P2) — Disambiguate Consumer Class anchors**

Rename heading at line 32 from `### Consumer Class` to `### Consumer Class (Contract 1)`.

Update verification.md references from `capsule-contracts.md#consumer-class` to `capsule-contracts.md#consumer-class-contract-1`.

- [ ] **Step 5: Fix CC-12 (P2) — Parallel Emission heading naming**

Rename heading at line 38 from `### Emission` to `### Emission (Contract 1)`.

Update verification.md line 45 reference from `capsule-contracts.md#emission` to `capsule-contracts.md#emission-contract-1`.

- [ ] **Step 6: Fix CE-12 (P2) — Add feedback capsule provenance MUST clause**

At the end of the Contract 3 Schema section (after line 203), add:

```markdown
The feedback capsule MUST omit `source_artifacts` entries for any upstream capsule (NS handoff) that was not structurally consumed — do not reference an NS `artifact_id` that was not validated via the [two-stage admission](pipeline-integration.md#two-stage-admission) process. Parallel to the [Contract 1 provenance rule](#consumer-class-contract-1).
```

- [ ] **Step 7: Verify anchor changes**

Run:
```bash
grep -rn 'capsule-contracts.md#consumer-class\b' docs/superpowers/specs/skill-composability/ | grep -v 'contract-'
grep -rn 'capsule-contracts.md#emission\b' docs/superpowers/specs/skill-composability/ | grep -v 'contract-'
```
Expected: No bare `#consumer-class` or `#emission` references remain (all updated to `#consumer-class-contract-1` and `#emission-contract-1`).

---

### Task 5: verification.md — Missing Verification Paths (8 P1)

**Files:**
- Modify: `docs/superpowers/specs/skill-composability/verification.md`

**Findings:** SY-20, SY-21, SY-22, SY-23, SY-24, SY-25, SY-26, SY-27

- [ ] **Step 1: Fix SY-20 (P1) — Add correction rule sequential-order test**

In the Routing and Materiality Verification table, after the "Correction rules only fire on invalid tuples" row (line 68), add a new row:

```markdown
| Correction rules MUST be evaluated in listed order (1→2→3→4→5) | [routing-and-materiality.md](routing-and-materiality.md#affected-surface-validity) | Materiality harness — structural test: construct a tuple matching rule 1 AND rule 2 (`material: false`, `affected_surface: evidence-only`, `suggested_arc: adversarial-review`). Verify correction is attributed to rule 1 (not rule 2) — confirming sequential evaluation. The tuple triggers rule 1 first (`material: false` + `suggested_arc ≠ dialogue_continue` → correct to `dialogue_continue`); rule 2 would also match but MUST NOT fire because rule 1 already corrected the tuple |
```

- [ ] **Step 2: Fix SY-21 (P1) — Add tautology_filter_applied flag-setting test**

In the Routing and Materiality Verification table, after the `--plan` not-set decomposition behavior row (line 81), add:

```markdown
| NS adapter MUST set `tautology_filter_applied: false` on partial-tier implementation | [pipeline-integration.md](pipeline-integration.md#two-stage-admission) | Behavioral: two test cases — (1) configure NS adapter to execute only Tier 1 of the tautology filter (partial-tier), verify `tautology_filter_applied` is `false` in the resulting `upstream_handoff`, (2) configure all three tiers to execute successfully, verify flag is `true`. These verify the MUST NOT (partial-tier → true) and the positive case |
```

- [ ] **Step 3: Fix SY-22 (P1) — Add NS empty-list emission producer-side test**

In the Capsule Contract Verification table, after the "NS handoff emits one block per NS run" row (line 49), add:

```markdown
| NS MUST NOT emit handoff block with `selected_tasks: []` | [capsule-contracts.md](capsule-contracts.md#emission-contract-2) | Behavioral: invoke NS with a scenario where no tasks qualify for dialogue recommendation → verify NS omits the handoff block entirely (no `<!-- next-steps-dialogue-handoff:v1 -->` sentinel emitted). This tests the producer-side MUST, complementing the consumer-side validity test (dialogue test case 3 above) |
```

- [ ] **Step 4: Fix SY-23 (P1) — Add budget counter re-review chain test**

In the soft iteration budget test (line 75), add a fourth fixture:

```markdown
(4) Re-review chain: pre-seed [AR (`adversarial_review`), NS (`next_steps_plan`), AR-re-review (`adversarial_review`)] all sharing the same `lineage_root_id`. The root is AR; chain = [NS, AR-re-review]. Verify budget counter = 2 (both NS and AR-re-review are qualifying `artifact_kind ∈ {adversarial_review, next_steps_plan}` artifacts). This confirms the counter counts per-artifact, not per-unique-kind.
```

- [ ] **Step 5: Fix SY-24 (P1) — Add timestamp string-vs-numeric comparison test**

In the thread continuation test (line 86), add a seventh scenario:

```markdown
(7) Format variation: `thread_created_at: 2026-03-18T14:30:52Z` (no milliseconds) and capsule `created_at: 2026-03-18T14:30:52.001Z` — under string comparison `Z` (char 90) > `.` (char 46) so `52Z` > `52.001Z` (wrong ordering). Under parsed numeric comparison: 52.000s < 52.001s → `created_at` is strictly after → fresh start required. This catches a string-comparison implementation bug.
```

- [ ] **Step 6: Fix SY-25 (P1) — Add post-abort no-durable-file assertion**

At line 55 (partial correction failure test), add to the assertion list:

```markdown
Additionally assert: (5) no durable file is written at `.claude/composition/feedback/` — verify the directory contains no new file matching the expected path pattern after the abort.
```

- [ ] **Step 7: Fix SY-26 (P1) — Extend Step 0 abort test with capsule suppression**

At line 37, the Step 0 precondition test case (c) (already updated to four cases). For case (c), extend the assertion:

After "materiality evaluation aborted with structured warning" add:

```markdown
and capsule assembly aborted — verify: (i) no `<!-- dialogue-feedback-capsule:v1 -->` sentinel appears in output, (ii) no capsule body is emitted, (iii) no durable file written, (iv) a structured warning containing "tautology_filter_applied" or "precondition" appears in prose output. Aligns with partial correction failure test structure at line 55.
```

- [ ] **Step 8: Fix SY-27 (P1) — Add consumer record_status absent test**

At line 57 (consumer-side `write_failed` handling test), add a third test case:

```markdown
(3) feedback capsule with `record_path` pointing to a file path AND `record_status` field entirely absent (emitter bug) → consumer emits one-line prose warning and falls through to conversation-local sentinel scan (precedence level 3). Verify consumer does NOT attempt to read the file at `record_path` and does NOT block. This exercises the consumer-side contract's absent `record_status` path.
```

---

### Task 6: verification.md — P2 Fixes (7 P2)

**Files:**
- Modify: `docs/superpowers/specs/skill-composability/verification.md`

**Findings:** CC-6 (already partially done), VR-3, VR-5, VR-10, VR-11, VR-13

- [ ] **Step 1: Verify CC-6 (P2) is complete**

The working tree already updated the Step 0 test count from "Two cases" to "Four cases." Verify the four cases match the SY-4 fix in routing-and-materiality.md.

Run: `grep -n 'Four cases' docs/superpowers/specs/skill-composability/verification.md`
Expected: One match at line 37.

- [ ] **Step 2: Fix VR-3 (P2) — Expand prohibition test cases**

At line 72 (Material `diagnosis`/`planning` MUST NOT silently remain `dialogue_continue` row), change from singular "dedicated prohibition test cases" to:

```markdown
Materiality harness — two dedicated prohibition test cases (one per affected surface): (1) `diagnosis/true/dialogue_continue` → corrected to `adversarial-review`, (2) `planning/true/dialogue_continue` → corrected to `next-steps`. Both exercise prohibition 4 for their respective surface.
```

- [ ] **Step 3: Fix VR-5 (P2) — Acknowledge unverifiable sub-clause**

At line 52 (record_path pre-computation structural review), add:

```markdown
**Accepted risk:** The sub-clause "error handler MUST read from pre-computed variable" is not independently verifiable by behavioral test (acknowledged infeasible in a skill context). Accepted as a code review responsibility — structural analysis of the error handler code path is the verification mechanism.
```

- [ ] **Step 4: Fix VR-10 (P2) — Revise standalone coherence test description**

At line 62, change:

Old: `without any upstream capsule present and without access to the composition contract`
New: `without any upstream capsule present and with only the skill's inline stub available (no additional context injection, no composition contract file in context) — the contract is not runtime-loaded, so this describes the default runtime state`

- [ ] **Step 5: Fix VR-11 (P2) — Add semantic spot-check to drift verification**

At line 110, after the CI check description, add:

```markdown
**Semantic spot-check (interim):** For PRs touching the composition contract, the PR description MUST include a one-line conformance statement for each of the three most drift-prone sections: routing classification rules, materiality tiers, and correction pipeline. This reduces the "necessary but not sufficient" gap until `validate_composition_contract.py` is implemented.
```

- [ ] **Step 6: Fix VR-13 (P2) — Reframe Tier 3 deferred entry**

At line 116, add a prefix note:

```markdown
**Note:** This entry contains active MUST prerequisites for the decomposition seeding PR — it is deferred from automated verification but has an active interim gate (manual evaluation of 4 examples). Treat as "gated interim verification," not as a skippable deferral.
```

---

### Task 7: pipeline-integration.md — Stage A and Terminology (1 P1 + 1 P2)

**Files:**
- Modify: `docs/superpowers/specs/skill-composability/pipeline-integration.md`

**Findings:** SY-8 (P1), CC-9 (P2)

- [ ] **Step 1: Fix SY-8 (P1) — Specify Stage A rejection behavior**

At line 24, after "proceed as if no upstream handoff exists", add:

```markdown
On rejection, `upstream_handoff` MUST NOT be initialized — it remains absent. Stage B is skipped. All capability flags are treated as absent (equivalent to `false`). The pipeline proceeds with the "no `upstream_handoff`" rows in the Decomposition Behavior table. The `tautology_filter_applied` flag is absent (consistent with "no upstream handoff" — see [routing-and-materiality.md](routing-and-materiality.md#material-delta-gating) Step 0 case b).
```

- [ ] **Step 2: Fix CC-9 (P2) — Correct abbreviated consumer class term**

At line 24, change:

Old: `strict consumer class`
New: `strict/deterministic consumer class`

- [ ] **Step 3: Apply SY-15 cross-reference (from Task 1)**

At line 39 (`tautology_filter_applied` description in Stage B table), add at the end:

```markdown
(enforcement semantics: [routing-and-materiality.md](routing-and-materiality.md#material-delta-gating) Step 0)
```

---

### Task 8: lineage.md — supersedes Minting Rule (1 P1)

**Files:**
- Modify: `docs/superpowers/specs/skill-composability/lineage.md`

**Findings:** SY-9 (P1)

- [ ] **Step 1: Fix SY-9 (P1) — Extend supersedes minting rule to check durable store**

At line 105 (supersedes minting rule), amend:

Old: `\`supersedes\` MUST reference the most recent prior artifact of the same \`artifact_kind\` and \`subject_key\` visible in conversation context at the time of capsule emission.`

New: `\`supersedes\` MUST reference the most recent prior artifact of the same \`artifact_kind\` and \`subject_key\` visible in conversation context at the time of capsule emission. For \`dialogue_feedback\` artifacts, also check the durable store at \`.claude/composition/feedback/\` (per the step-0 durable store check in [consumption discovery](#consumption-discovery)) before determining \`supersedes\` — the most recent prior artifact across both conversation context and the durable store is the correct supersession target.`

---

### Task 9: foundations.md + spec.yaml — Authority Model (1 P1 + 3 P2)

**Files:**
- Modify: `docs/superpowers/specs/skill-composability/foundations.md`
- Modify: `docs/superpowers/specs/skill-composability/spec.yaml`

**Findings:** SY-6 (P1), CC-10 (P2), AA-5 (P2), AA-6 (P2)

- [ ] **Step 1: Fix SY-6 (P1) — Add behavior_contract precedence note to spec.yaml**

At spec.yaml line 44, after the `behavior_contract` precedence line, add a comment:

```yaml
    # Foundation's behavior_contract claims define cross-cutting invariants
    # (consumer classes, capsule externalization) that downstream authorities
    # must not contradict. Foundation ranks last in precedence for conflict
    # resolution, but its behavioral invariants are architectural constraints
    # referenced by all three behavior authorities — contradictions indicate
    # a spec defect, not a precedence override.
```

- [ ] **Step 2: Fix CC-10 (P2) — Correct "below" to "above"**

At foundations.md line 75, change:

Old: `see [Consumer Classes](#consumer-classes) below`
New: `see [Consumer Classes](#consumer-classes) above`

- [ ] **Step 3: Fix AA-6 (P2) — Replace interim protocol duplicate with cross-reference**

At foundations.md lines 109 (the "Interim drift mitigation" paragraph), replace:

Old: `Interim drift mitigation (until CI enforcement exists): Contract→stub drift is bidirectional — both contract changes and stub changes can introduce it. See [delivery.md](delivery.md#open-items) item #8 for the interim manual review protocol (PR MUST clauses and stub-impact checklist). This protocol is a P0 prerequisite — merging changes without cross-checking recreates the silent correctness bug this section warns about.`

New: `Interim drift mitigation protocol: see [delivery.md](delivery.md#open-items) item #8. Contract→stub drift is bidirectional and is a P0 prerequisite check.`

- [ ] **Step 4: Fix AA-5 (P2) — Add cross-reference for external authorities**

At foundations.md line 69 (Three-Layer Delivery Authority table), add after the table:

```markdown
See spec.yaml lines 57-61 for the external authority positioning comment.
```

---

### Task 10: README.md — Authority Model Corrections (3 P1)

**Files:**
- Modify: `docs/superpowers/specs/skill-composability/README.md`

**Findings:** SY-1, SY-2, SY-3 (Cluster D)

- [ ] **Step 1: Fix SY-1 (P1) — Add behavior_contract to foundation's default claims**

At README.md line 18, change:

Old: `| \`foundation\` | Composability model, scope, consumer classes, cross-cutting invariants | \`architecture_rule\` |`
New: `| \`foundation\` | Composability model, scope, consumer classes, cross-cutting invariants | \`architecture_rule\`, \`behavior_contract\` |`

- [ ] **Step 2: Fix SY-2 (P1) — Add foundation to behavior_contract precedence**

At README.md line 31, change:

Old: `` `behavior_contract`: routing > pipeline > lineage ``
New: `` `behavior_contract`: routing > pipeline > lineage > foundation ``

- [ ] **Step 3: Fix SY-3 (P1) — Correct fallback authority order**

At README.md line 33, change:

Old: `Fallback: foundation > capsule-contract > routing > pipeline > lineage > decisions > delivery-plan > delivery-verification > supporting`
New: `Fallback: foundation > decisions > capsule-contract > routing > pipeline > lineage > delivery-plan > delivery-verification > supporting`

- [ ] **Step 4: Verify README matches spec.yaml**

Run:
```bash
grep 'fallback_authority_order' docs/superpowers/specs/skill-composability/spec.yaml
grep 'Fallback:' docs/superpowers/specs/skill-composability/README.md
```
Expected: Both show `foundation > decisions > capsule-contract > routing > pipeline > lineage > ...`

---

### Task 11: delivery.md + foundations.md — Cross-Reference and Documentation Fixes (3 P2)

**Files:**
- Modify: `docs/superpowers/specs/skill-composability/delivery.md`
- Modify: `docs/superpowers/specs/skill-composability/foundations.md`

**Findings:** CC-7, CC-14, CE-11

- [ ] **Step 1: Fix CC-7 (P2) — Update materiality fixture count in delivery.md**

At delivery.md line 50 (item #7), change:

Old: `12 executable materiality fixtures`
New: `Materiality fixtures per [verification.md](verification.md#interim-materiality-verification-protocol) (authoritative test design)`

- [ ] **Step 2: Fix CC-14 (P2) — Add explicit contract path to foundations.md**

At foundations.md line 105, change:

Old: `See [delivery.md](delivery.md#skill-text-changes) for the contract file path.`
New: `Contract file: \`packages/plugins/cross-model/references/composition-contract.md\`. See [delivery.md](delivery.md#skill-text-changes) for the full delivery specification.`

This makes the path directly discoverable in foundations.md rather than requiring a cross-reference hop.

- [ ] **Step 3: Fix CE-11 (P2) — Specify drift marker location in foundations.md**

At foundations.md line 103, after "drift detection marker", add:

```markdown
The marker MUST appear in the skill's composition stub frontmatter or as a top-level key in the composition stub block — not in examples, comments, or disabled sections. The grep-based CI check (verification.md) MUST verify the marker appears within the active composition stub boundaries.
```

---

### Task 12: Cross-File Consistency Check

**Files:**
- All 9 spec files (read-only verification)

- [ ] **Step 1: Verify all cross-references resolve**

Run:
```bash
# Check for broken anchor references
grep -rn '\[.*\](.*\.md#' docs/superpowers/specs/skill-composability/ | grep -o '#[a-z-]*' | sort -u > /tmp/anchors-referenced.txt
# Manually spot-check the high-risk anchors:
grep -n 'consumer-class-contract-1\|emission-contract-1' docs/superpowers/specs/skill-composability/capsule-contracts.md
grep -n 'consumer-class-contract-1\|emission-contract-1' docs/superpowers/specs/skill-composability/verification.md
```
Expected: Renamed anchors appear in both source and reference files.

- [ ] **Step 2: Verify budget counting consistency across files**

Run:
```bash
grep -n 'dialogue_feedback.*budget\|budget.*dialogue_feedback\|adversarial_review.*next_steps_plan' docs/superpowers/specs/skill-composability/routing-and-materiality.md
grep -n 'dialogue_feedback' docs/superpowers/specs/skill-composability/verification.md
```
Expected: Budget counting exclusion of `dialogue_feedback` is consistent between normative spec and verification test fixtures.

- [ ] **Step 3: Verify README matches spec.yaml authority model**

Run:
```bash
grep 'default_claims' docs/superpowers/specs/skill-composability/spec.yaml
grep 'Default Claims' docs/superpowers/specs/skill-composability/README.md
```
Expected: Foundation shows `architecture_rule, behavior_contract` in both files.

- [ ] **Step 4: Verify Step 0 case count consistency**

Run:
```bash
grep -n 'Four cases\|four cases\|case (a)\|case (b)\|case (c)\|case (d)' docs/superpowers/specs/skill-composability/routing-and-materiality.md docs/superpowers/specs/skill-composability/verification.md
```
Expected: Both files reference four cases (a-d) consistently.

- [ ] **Step 5: Verify tautology_filter_applied cross-references are bidirectional**

Run:
```bash
grep -n 'tautology_filter_applied' docs/superpowers/specs/skill-composability/routing-and-materiality.md docs/superpowers/specs/skill-composability/pipeline-integration.md | grep -c 'routing-and-materiality\|pipeline-integration'
```
Expected: Cross-references in both directions.

- [ ] **Step 6: Commit all changes**

```bash
git add docs/superpowers/specs/skill-composability/routing-and-materiality.md \
       docs/superpowers/specs/skill-composability/verification.md \
       docs/superpowers/specs/skill-composability/capsule-contracts.md \
       docs/superpowers/specs/skill-composability/pipeline-integration.md \
       docs/superpowers/specs/skill-composability/lineage.md \
       docs/superpowers/specs/skill-composability/foundations.md \
       docs/superpowers/specs/skill-composability/spec.yaml \
       docs/superpowers/specs/skill-composability/README.md \
       docs/superpowers/specs/skill-composability/delivery.md
git commit -m "fix(spec): remediate 50 findings (1 P0, 26 P1, 23 P2) from skill-composability round-4 review"
```

---

## Finding Coverage Matrix

Every canonical finding (SY-1 through SY-50) maps to a task and step:

| Finding | Priority | Task | Description |
|---------|----------|------|-------------|
| SY-4 | P0 | T1.1 | Step 0 four-case restructure (verify existing) |
| SY-1 | P1 | T10.1 | README foundation default claims |
| SY-2 | P1 | T10.2 | README behavior_contract precedence |
| SY-3 | P1 | T10.3 | README fallback order |
| SY-5 | P1 | T3.2, T4.3 | materiality_source validation gate |
| SY-6 | P1 | T9.1 | Foundation behavior_contract precedence note |
| SY-7 | P1 | T3.3 | Cross-tier guard materiality_source |
| SY-8 | P1 | T7.1 | Stage A rejection upstream_handoff |
| SY-9 | P1 | T8.1 | supersedes minting rule durable store |
| SY-10 | P1 | T3.4 | Ambiguous item placement |
| SY-11 | P1 | T2.1 | Budget counting alignment |
| SY-12 | P1 | T4.2 | selected_tasks annotation |
| SY-13 | P1 | T3.5 | Consumer record_status absent |
| SY-14 | P1 | T4.1 | Feedback capsule posture enum |
| SY-15 | P1 | T1.3 | Bidirectional cross-references |
| SY-16 | P1 | T3.1 | classifier_source validation gate |
| SY-17 | P1 | T1.2 | Step 0 abort post-abort behaviors |
| SY-18 | P1 | T2.2 | Budget indeterminate detection |
| SY-19 | P1 | T3.6 | No-auto-chaining enforcement gap |
| SY-20 | P1 | T5.1 | Sequential-order test |
| SY-21 | P1 | T5.2 | Flag-setting test |
| SY-22 | P1 | T5.3 | NS empty-list emission test |
| SY-23 | P1 | T5.4 | Budget re-review chain test |
| SY-24 | P1 | T5.5 | Timestamp comparison test |
| SY-25 | P1 | T5.6 | Post-abort no-durable-file test |
| SY-26 | P1 | T5.7 | Step 0 abort capsule suppression test |
| SY-27 | P1 | T5.8 | Consumer record_status absent test |
| SY-28–50 | P2 | T1–T11 | See individual task steps |
