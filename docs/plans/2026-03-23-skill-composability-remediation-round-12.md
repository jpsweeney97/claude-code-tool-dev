# Skill Composability Spec Remediation Plan — Round 12

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remediate all 48 canonical findings from the round 12 spec review

**Architecture:** Text-only spec edits across 9 files in `docs/superpowers/specs/skill-composability/`. Six design decisions resolved via Codex dialogue (thread `019d1913-2e7e-7982-8a6c-341c0ba5ee58`). Three cross-resolution consistency obligations emerged from the dialogue. All edits are mechanical or apply agreed dialogue resolutions — no open design questions remain.

**Tech Stack:** Markdown spec files, YAML authority model (spec.yaml)

---

**Source:** `.review-workspace/synthesis/report.md` (5-reviewer team, 2026-03-23)
**Scope:** 48 canonical findings (5 P0, 31 P1, 12 P2) + 3 emerged cross-resolution obligations across 9 normative files + spec.yaml
**Spec:** `docs/superpowers/specs/skill-composability/` (10 files, 9 normative + 1 supporting + spec.yaml)
**Dialogue:** Codex collaborative dialogue resolved all 6 design ambiguities (SY-4, SY-9, SY-10–13, SY-15, SY-16, SY-19)
**Dominant theme:** Governance gate completeness — 5 of 5 P0 and 20+ P1 findings trace to enforcement surface gaps where a MUST-level invariant has no corresponding governance gate

## Strategy

Eight tasks in three phases, ordered by dependency and edit-locality:

1. **Phase 1** — Three tasks, all parallel (touch different files or non-overlapping sections):
   - **T1:** Authority model + README (2 findings) — spec.yaml, README.md
   - **T2:** Corroborated P1 citation/reference fixes (4 findings) — governance.md, pipeline-integration.md, verification.md
   - **T3:** Routing prose clarifications + mapping note (2 findings) — routing-and-materiality.md

2. **Phase 2** — After T2 (governance.md citations must be correct before new gates reference them):
   - **T4:** P0 governance gate backfill + delivery activation (5 P0 + 1 emerged) — governance.md, delivery.md
   - **T5:** P1 enforcement clusters: hold_reason + supersedes (6 findings + 1 emerged) — governance.md, verification.md, delivery.md

3. **Phase 3** — After T4 (governance.md P0 gates must land before singleton gates to avoid edit conflicts):
   - **T6:** P1 singleton governance gates (7 findings) — governance.md
   - **T7:** P1 verification backfill + SY-16 semantic template rewrite (10 findings + 1 emerged) — verification.md
   - **T8:** Delivery tracking + P2 batch (12 findings) — delivery.md, verification.md, routing-and-materiality.md, README.md

**Dependency chains:**
1. SY-1/SY-2 citation fixes (T2) → SY-4/SY-8 gates cite corrected governance sections (T4)
2. SY-19 spec.yaml external_artifacts (T1) → SY-4 gate may reference authority positions (T4 — soft dependency)
3. SY-15 mapping note (T3) → SY-24 verification scenario cross-references check ordering (T7)
4. SY-10–13 cluster gate (T5) → SY-34 partial correction failure gate references hold_reason behavior (T6)

**Commit strategy:**
1. `fix(spec): add external_artifacts registry and README precedence from review round 12` (T1)
2. `fix(spec): remediate 4 corroborated P1 citation findings from review round 12` (T2)
3. `fix(spec): remediate 2 routing prose clarification findings from review round 12` (T3)
4. `fix(spec): remediate 5 P0 enforcement surface findings from review round 12` (T4)
5. `fix(spec): remediate 6 hold_reason + supersedes cluster findings from review round 12` (T5)
6. `fix(spec): remediate 7 singleton governance gate findings from review round 12` (T6)
7. `fix(spec): remediate 11 verification backfill findings from review round 12` (T7)
8. `fix(spec): remediate 12 delivery tracking + P2 findings from review round 12` (T8)

---

## Task 1 — Authority Model + README (2 findings)

**Finding count:** 1 P1, 1 P2
**Findings:** SY-19, SY-37
**Files:** spec.yaml, README.md
**Depends on:** nothing — start immediately

### [SY-19] Composition contract authority position not in spec.yaml

**Source:** AA-2
**File:** spec.yaml (after line 60, before `boundary_rules:`)
**Dialogue resolution:** Add flat `external_artifacts` registry matching existing spec.yaml style

- [ ] **Step 1: Add external_artifacts to spec.yaml**

After the `unresolved: ambiguity_finding` line and the cross-family disambiguation comment block (after line 65), before the blank line preceding `boundary_rules:`, add:

```yaml

external_artifacts:
  composition-contract:
    path: packages/plugins/cross-model/references/composition-contract.md
    status: planned  # transitions to active when file exists
    governed_by: foundation  # exact key from authorities block
    authority_context: design_and_review  # not runtime-loaded
    conflict_rule: spec_files_win  # when contract diverges from spec
    description: >
      Canonical external contract for inter-skill composition semantics.
      Used by stub authors at implementation time. Not runtime-loaded;
      stubs carry the runtime projection.
```

### [SY-37] README omits enforcement_mechanism precedence (routing > governance)

**Source:** AA-3
**File:** README.md:36

- [ ] **Step 2: Add enforcement_mechanism precedence to README**

In README.md §Precedence, after the line `- `interface_contract`: capsule-contract > lineage` (line 33), verify the line `- Fallback: foundation > decisions > ...` follows. After the `decision_record` line (line 35), add:

```markdown
- `enforcement_mechanism`: routing > governance
```

This line already exists at line 36. Verify it is present. If already present, skip this step.

- [ ] **Step 3: Commit T1**

```bash
git add docs/superpowers/specs/skill-composability/spec.yaml docs/superpowers/specs/skill-composability/README.md
git commit -m "fix(spec): add external_artifacts registry and README precedence from review round 12"
```

---

## Task 2 — Corroborated P1 Citation/Reference Fixes (4 findings)

**Finding count:** 4 P1 (all corroborated)
**Findings:** SY-1, SY-2, SY-3, SY-5
**Files:** governance.md, pipeline-integration.md, verification.md
**Depends on:** nothing — start immediately

### [SY-1] governance.md record_path Null-Prevention Review cites wrong source

**Source:** AA-4, CE-6, CC-2 (3 reviewers)
**File:** governance.md:58

- [ ] **Step 1: Fix governance.md record_path citation**

Change:
```markdown
Validates: capsule-contracts.md §Schema Constraints (`record_path` non-null requirement)
```
To:
```markdown
Validates: routing-and-materiality.md §Selective Durable Persistence + capsule-contracts.md §Contract 3 (Dialogue Feedback Capsule) (`record_path` non-null requirement)
```

### [SY-2] governance.md co-review gate missing pipeline-integration.md citation

**Source:** AA-1, CE-14, CC-3 (3 reviewers)
**File:** governance.md:14, pipeline-integration.md:41

- [ ] **Step 2: Add dual enforcement basis to co-review gate**

In governance.md, change:
```markdown
Validates: routing-and-materiality.md §No Auto-Chaining (enforcement basis)
```
(first occurrence, at the Stub Composition Co-Review Gate header)
To:
```markdown
Validates: routing-and-materiality.md §No Auto-Chaining + pipeline-integration.md §Two-Stage Admission Stage B (enforcement basis)
```

- [ ] **Step 3: Fix pipeline-integration.md self-citation**

In pipeline-integration.md line 41, the `tautology_filter_applied` capability flag description contains "citing this clause" as a broken forward-reference. Find the text:
```
citing this clause
```
Replace with:
```
per pipeline-integration.md §Two-Stage Admission Stage B
```

### [SY-3] dialogue-orchestrated-briefing sentinel suppression — dangling governance reference

**Source:** CE-8, IE-4, CC-6 (3 reviewers)
**File:** governance.md (append after `budget_override_pending` Initialization Check section)

- [ ] **Step 4: Add sentinel suppression placeholder to governance.md**

Append after the `budget_override_pending` Initialization Check section (after line 73):

```markdown

## `dialogue-orchestrated-briefing` Sentinel Suppression Check

Validates: capsule-contracts.md §Sentinel Registry (internal sentinel scope)

**[Activates when dialogue stub is authored]** PR checklist item: "Confirmed: `<!-- dialogue-orchestrated-briefing -->` does not appear in any code path that writes to conversation context or user-visible output. The sentinel is internal pipeline state only. Verified by reviewing all output-writing code paths in the dialogue stub."

Retirement: when `validate_composition_contract.py` includes sentinel scope enforcement.
```

### [SY-5] Abort-path parity table assertion (7) count/mapping ambiguity

**Source:** CE-1, CC-1 (2 reviewers, independent convergence)
**File:** verification.md:60 (partial correction failure row)

- [ ] **Step 5: Fix parity table assertion count**

In verification.md line 60, in the "Partial correction failure" row's abort-path parity section, find:
```
Both abort paths (Step 0 case c and partial correction failure) MUST produce identical behavior for **six** shared assertions:
```
Replace with:
```
Both abort paths (Step 0 case c and partial correction failure) MUST produce identical behavior for **seven** shared assertions:
```

In the same assertion list, after item `(f) capability flags absent from post-abort pipeline state`, add:
```
, (g) all `upstream_handoff` capability flags torn down — no prior flags carried forward
```

- [ ] **Step 6: Commit T2**

```bash
git add docs/superpowers/specs/skill-composability/governance.md docs/superpowers/specs/skill-composability/pipeline-integration.md docs/superpowers/specs/skill-composability/verification.md
git commit -m "fix(spec): remediate 4 corroborated P1 citation findings from review round 12"
```

---

## Task 3 — Routing Prose Clarifications + Mapping Note (2 findings)

**Finding count:** 1 P1, 1 P1
**Findings:** SY-15, SY-18
**Files:** routing-and-materiality.md
**Depends on:** nothing — start immediately

### [SY-15] 6 prose consumer-side cases vs 5 formal check steps

**Source:** CE-3
**File:** routing-and-materiality.md:282 (Check ordering paragraph)
**Dialogue resolution:** Add mapping note, do NOT restructure numbering

- [ ] **Step 1: Add mapping note to Check ordering section**

In routing-and-materiality.md, after the "Check ordering" paragraph (line 282) and before "Re-encounter at level 3" (line 284), add:

```markdown

**Mapping note:** The 5-step check ordering above covers durable store validation (precedence level 2). Prose case 6 (re-encounter at level 3) is a post-step-5 scenario occurring at conversation-local sentinel scan (precedence level 3), outside the durable store check sequence. The re-encounter guard is not a 6th validation step — it fires at a different precedence level after the 5-step sequence has completed and fallen through.
```

### [SY-18] Step 0 case (c) "those items" → ambiguous subset-abort

**Source:** CE-10
**File:** routing-and-materiality.md:126 (Step 0 case c)

- [ ] **Step 2: Replace ambiguous "those items" phrasing**

In routing-and-materiality.md line 126, case (c), find the text:
```
Emit a structured warning and abort materiality evaluation for those items.
```
Replace with:
```
Emit a structured warning and abort materiality evaluation entirely.
```

- [ ] **Step 3: Commit T3**

```bash
git add docs/superpowers/specs/skill-composability/routing-and-materiality.md
git commit -m "fix(spec): remediate 2 routing prose clarification findings from review round 12"
```

---

## Task 4 — P0 Governance Gate Backfill + Delivery Activation (5 P0 + 1 emerged)

**Finding count:** 5 P0, 1 emerged cross-resolution obligation
**Findings:** SY-4, SY-6, SY-7, SY-8, SY-9 + emerged (SY-4 delivery activation)
**Files:** governance.md, delivery.md
**Depends on:** T2 (governance.md citations must be stable)

### [SY-4] Post-abort capability flag teardown — no enforcement surface (P0, corroborated)

**Source:** IE-2, VR-17
**File:** governance.md (append new gate)
**Dialogue resolution:** Two-layer enforcement — phase-and-abort coverage table (governance) + corroborating reinvocation test (verification). Reinvocation is regression check, not standalone proof.

- [ ] **Step 1: Add abort teardown governance gate**

Append to governance.md after the `dialogue-orchestrated-briefing` Sentinel Suppression Check section (added in T2):

```markdown

## `upstream_handoff` Abort Teardown Check

Validates: routing-and-materiality.md §Material-Delta Gating Step 0 case (c) + §Affected-Surface Validity post-abort behavior (flag teardown invariant)

**[Activates when dialogue abort-path code is authored]** PR checklist item: "Confirmed: all `upstream_handoff` capability flags (`decomposition_seed`, `gatherer_seed`, `briefing_context`, `tautology_filter_applied`) are torn down after each abort path. Verified using the phase-and-abort coverage table below."

**Phase-and-abort coverage table:** Each row names the stub phase where a capability flag becomes semantically live, the reachable abort condition, the required post-abort rule, and the linked reinvocation test case.

| Flag | Semantically Live At | Abort Condition | Post-Abort Rule | Reinvocation Case |
|------|---------------------|-----------------|-----------------|-------------------|
| `decomposition_seed` | Step 0 materiality precondition | Case (c): filter not applied | Any later invocation MUST recompute from currently visible inputs; no prior flag carried forward | Post-abort reinvocation: no enriched decomposition behavior |
| `gatherer_seed` | Steps 2-3 gatherer enrichment | Case (c) or partial correction failure | Same | Post-abort reinvocation: no gatherer enrichment from prior handoff |
| `briefing_context` | Briefing assembly | Case (c) or partial correction failure | Same | Post-abort reinvocation: no upstream context injection |
| `tautology_filter_applied` | Step 0 precondition check | Case (c) or partial correction failure | Same | Post-abort reinvocation: precondition re-evaluated from scratch |

The reinvocation test (verification.md) is a **corroborating regression check** — absence of capability-flag-dependent behavior is evidence of teardown, not standalone proof. The governance gate (structural reviewer trace) is the primary enforcement layer.
```

### [SY-6] decomposition_seed flag accuracy — no governance gate (P0)

**Source:** CE-5
**File:** governance.md (add to Stub Composition Co-Review Gate)

- [ ] **Step 2: Add decomposition_seed checklist item to co-review gate**

In governance.md, in the Stub Composition Co-Review Gate section, after the `tautology_filter_applied` paragraph (line 20-21), append:

```markdown

The co-review gate MUST also verify the NS adapter sets `decomposition_seed: true` only when `--plan` was active AND decomposition seeding actually ran — per pipeline-integration.md §Two-Stage Admission Stage B. A false `decomposition_seed` causes Step 0 case (c) abort with no recovery path. PR checklist item: "Confirmed: NS adapter's `decomposition_seed` assignment is conditional on `--plan` being active. Verified by tracing the adapter code path."
```

### [SY-7] Step 0 case (c)/(d) boundary — no gate verifies flag read source (P0)

**Source:** IE-9
**File:** governance.md (append new gate)

- [ ] **Step 3: Add Step 0 Flag Read Source Verification gate**

Append to governance.md:

```markdown

## Step 0 Flag Read Source Verification

Validates: routing-and-materiality.md §Material-Delta Gating Step 0 (case c/d boundary)

**[Activates when materiality evaluator code is authored]** PR checklist item: "Confirmed: materiality evaluator reads `decomposition_seed` from `upstream_handoff.decomposition_seed` (direct flag read from the capability flags set by the adapter at Stage B). The evaluator does NOT derive decomposition status from `--plan` CLI state or any other source. Verified by tracing the evaluator's data source for the case (c)/(d) branching decision."
```

### [SY-8] tautology_filter_applied conformance — no enforcement for Stage A rejection path (P0)

**Source:** IE-1
**File:** governance.md (extend Stub Composition Co-Review Gate)

- [ ] **Step 4: Extend co-review gate for Stage A rejection path**

In governance.md, in the Stub Composition Co-Review Gate section, after the `decomposition_seed` paragraph added in Step 2, append:

```markdown

The co-review gate enforcement surface covers ALL adapter exit paths, including Stage A rejection (where `upstream_handoff` is never initialized). When Stage A rejects a capsule, the adapter exits before `upstream_handoff` is constructed — `tautology_filter_applied` key-presence cannot be checked on an object that does not exist. PR checklist item: "Confirmed: adapter exit paths are exhaustively enumerated — including schema-validation-failure paths where `upstream_handoff` is never initialized. For rejection paths: verified no capability flags leak into pipeline state."
```

### [SY-9] Five-step durable store check ordering — no interim enforcement before dialogue stub merges (P0)

**Source:** VR-9
**File:** governance.md (append new gate), delivery.md (activation checklist)
**Dialogue resolution:** Dual-placement — governance.md owns gate definition (G-CONSUMER-DURABLE-ORDER), delivery.md owns activation trigger

- [ ] **Step 5: Add Consumer Durable Store Check Ordering Gate**

Append to governance.md:

```markdown

## Consumer Durable Store Check Ordering Gate

Validates: routing-and-materiality.md §Selective Durable Persistence (check ordering invariant)

PR checklist item: "Confirmed: consumer-side durable store lookup checks fields in order (1) `record_path` nullity, (2) file existence at `record_path`, (3) `record_status` field presence, (4) `record_status` value, (5) file content integrity. Step 3 precedes any file I/O. Verified by tracing the consumer code path as a sequential short-circuit chain."

Cross-reference: routing-and-materiality.md §Check ordering defines the normative 5-step sequence. Consumer-side case (3) behavioral test (absent `record_status` with file existing at path) is the specific ordering verification test per verification.md.
```

- [ ] **Step 6: Add delivery.md activation entry for SY-9 gate**

In delivery.md, in the Governance Gate Activation Checklist table (line 23-27), add a new row after "Composition stubs (AR, NS, dialogue)":

```markdown
| Dialogue consumer stub (durable store behavior) | Consumer Durable Store Check Ordering, `upstream_handoff` Abort Teardown Check |
```

Note: delivery.md MUST NOT restate the check logic — single normative source for "what" (governance.md), single normative source for "when" (delivery.md). The activation trigger is: "any PR that authors or materially edits dialogue durable-store consumer behavior."

### [Emerged] SY-4 delivery.md activation entry

- [ ] **Step 7: Verify SY-4 gate is included in delivery.md activation**

The delivery.md row added in Step 6 already includes `upstream_handoff` Abort Teardown Check for the dialogue consumer stub. Verify this is present. If the abort teardown gate maps to a broader artifact class ("dialogue abort-path code"), update the Artifact column accordingly.

### [SY-10-13 emerged] hold_reason gate delivery.md activation entry

This is handled in T5 Step 5.

- [ ] **Step 8: Commit T4**

```bash
git add docs/superpowers/specs/skill-composability/governance.md docs/superpowers/specs/skill-composability/delivery.md
git commit -m "fix(spec): remediate 5 P0 enforcement surface findings from review round 12"
```

---

## Task 5 — P1 Enforcement Clusters: hold_reason + supersedes (6 findings + 1 emerged)

**Finding count:** 4 P1 (hold_reason cluster) + 2 P1 (supersedes cluster) + 1 emerged
**Findings:** SY-10, SY-11, SY-12, SY-13, SY-20, SY-38 + emerged (SY-10-13 delivery activation)
**Files:** governance.md, verification.md, delivery.md
**Depends on:** T2 (governance.md citations stable)

### [SY-10–SY-13] hold_reason four-layer enforcement cluster

**Source:** CE-2, CE-4, VR-12, IE-3
**File:** governance.md (append new gate)
**Dialogue resolution:** Governance-only provenance (assignment precedence + list-membership) + validator-visible structure. Stage differentiation deferred as governance-only in v1.

- [ ] **Step 1: Add hold_reason Assignment and Placement Review gate**

Append to governance.md:

```markdown

## `hold_reason` Assignment and Placement Review

Validates: routing-and-materiality.md §Ambiguous Item Behavior (assignment precedence) + §Affected-Surface Validity (emission-time gate, list-membership constraint)

PR checklist requires reviewer to confirm:

1. "Confirmed: exactly one authoritative write point for `hold_reason` exists — the routing stage sets `hold_reason: routing_pending` for held ambiguous items. No other code path assigns a non-null `hold_reason` value."
2. "Confirmed: later stages (capsule assembly, emission-time gate) can only propagate or omit `hold_reason` — they MUST NOT clear, replace, or default over an existing `routing_pending` value."
3. "Confirmed: `hold_reason` assignments are only present in code paths that write to `unresolved[]`, not to `feedback_candidates[]`. Verified by reviewing all code paths that populate `feedback_candidates[]` — none contain `hold_reason` field assignments."

**Accepted v1 limitation:** Stage differentiation (whether `hold_reason` was set at routing time vs capsule assembly time) cannot be proven mechanically without a new observable trace field. This governance gate is the sole enforcement for provenance claims. The behavioral test in verification.md asserts the final emitted value, not assignment timing.

**Validator scope extension:** When `validate_composition_contract.py` is implemented (delivery.md item #6), add structural checks for: `hold_reason` at correct emitted path (`unresolved[]` only), never in `feedback_candidates[]`, value from allowed set `{routing_pending, null}`.
```

- [ ] **Step 2: Add SY-12 limitation note to verification.md**

In verification.md, in the `hold_reason` routing-stage assignment row (line 68), at the end of the verification path text, verify the following note exists:
```
Note: both routing-stage-assignment and capsule-assembly-time-assignment implementations satisfy this test — code review MUST confirm no path overwrites `hold_reason` assignment during capsule assembly. The test verifies the final value, not the assignment timing.
```

If present, no edit needed. This note already acknowledges SY-12's limitation.

### [SY-20] supersedes emitter-MUST — no independent verification path

**Source:** VR-1
**File:** verification.md:123 (supersedes minting rule row)

- [ ] **Step 3: Add supersedes key-presence assertion**

In verification.md, in the supersedes minting rule row (line 123), after scenario (5), add:

```
(6) Emitter key-presence: invoke any participating skill that emits a capsule where a prior same-kind same-subject artifact exists → verify `supersedes` key is present in the emitted capsule (not omitted). The key MUST always be present — set to null when no prior artifact exists, set to the `artifact_id` when one does. This tests the emitter-side MUST independently of consumer-side tolerance (which treats absent `supersedes` as null).
```

### [SY-38] supersedes SHOULD flagging weakens MUST emitter rule

**Source:** CE-12
**File:** governance.md (append to co-review gate or as standalone note)

- [ ] **Step 4: Strengthen supersedes enforcement note**

In governance.md, in the Stub Composition Co-Review Gate section, after the Stage A rejection path paragraph (added in T4), append:

```markdown

The co-review gate MUST verify that `supersedes` is always present (not omitted) in emitted capsules, per the emitter-side MUST in lineage.md §DAG Structure. Consumer-side tolerance (treating absent `supersedes` as null) does NOT relax the emitter obligation — the consumer compatibility exception is defensive, not normative.
```

### [Emerged] SY-10-13 delivery.md activation entry

- [ ] **Step 5: Add hold_reason gate to delivery.md activation checklist**

In delivery.md, in the Governance Gate Activation Checklist table, in the "Composition stubs (AR, NS, dialogue)" row (line 26), add `hold_reason Assignment and Placement Review` to the Gates Activated column:

```markdown
| Composition stubs (AR, NS, dialogue) | Stub Composition Co-Review, Helper Function Tracking, Constrained Field Literal-Assignment, `budget_override_pending` Initialization, `hold_reason` Assignment and Placement Review |
```

- [ ] **Step 6: Commit T5**

```bash
git add docs/superpowers/specs/skill-composability/governance.md docs/superpowers/specs/skill-composability/verification.md docs/superpowers/specs/skill-composability/delivery.md
git commit -m "fix(spec): remediate 6 hold_reason + supersedes cluster findings from review round 12"
```

---

## Task 6 — P1 Singleton Governance Gates (7 findings)

**Finding count:** 7 P1
**Findings:** SY-14, SY-17, SY-26, SY-33, SY-34, SY-35, SY-36
**Files:** governance.md
**Depends on:** T4 (P0 gates landed)

### [SY-14] tautology_filter_applied key-presence — not in PR checklist format

**Source:** CE-11
**File:** governance.md:20-21 (co-review gate)

- [ ] **Step 1: Reformat tautology_filter_applied as explicit checklist item**

In governance.md, the existing co-review gate paragraph (line 20-21) about `tautology_filter_applied` reads as prose. Verify it contains a PR checklist item format. If it reads:

```
The co-review gate MUST also verify the NS adapter sets `tautology_filter_applied` in `upstream_handoff` capability flags (key presence, not just value correctness) — absence is a gate failure requiring remediation before merge.
```

Replace with:

```
PR checklist item: "Confirmed: NS adapter sets `tautology_filter_applied` in `upstream_handoff` capability flags. Key presence verified (not just value correctness). Absence is a gate failure requiring remediation before merge."
```

### [SY-17] source_artifacts provenance rule — no governance gate for dialogue emitter

**Source:** CE-9
**File:** governance.md (append new gate)

- [ ] **Step 2: Add source_artifacts provenance gate**

Append to governance.md:

```markdown

## `source_artifacts` Provenance Review

Validates: capsule-contracts.md §Consumer Class Contract 1 + §Contract 3 (provenance rule)

PR checklist item: "Confirmed: when Stage A rejects a capsule (invalid schema), the dialogue feedback capsule emitted in that invocation omits `source_artifacts` entries for the rejected upstream artifact. Verified by tracing the rejection branch — `source_artifacts[]` is populated only from successfully consumed upstream artifacts, never from rejected capsules."
```

### [SY-26] Tier 3 calibration — no PR gate

**Source:** VR-10
**File:** governance.md (append new gate)

- [ ] **Step 3: Add Tier 3 calibration gate**

Append to governance.md:

```markdown

## Tier 3 Tautology Filter Calibration Gate

Validates: pipeline-integration.md §Three-Tier Tautology Filter (Tier 3 model calibration)

**[Activates when decomposition seeding PR is authored]** PR checklist item: "Confirmed: all 4 Tier 3 examples from pipeline-integration.md (2 valid, 2 invalid) classify correctly. PR description includes classification result for each example. Any misclassification blocks merge until Tier 3 prompt is revised."
```

### [SY-33] budget_override_pending initialization — per-invocation scoping not enforced

**Source:** IE-5
**File:** governance.md:69-72 (budget_override_pending Initialization Check)

- [ ] **Step 4: Extend budget_override_pending gate for per-invocation scoping**

In governance.md, in the `budget_override_pending` Initialization Check (line 69-72), extend the PR checklist item. Find:

```
PR checklist item: "Confirmed: `budget_override_pending` is explicitly initialized to `false` at dialogue stub entry — not left to default-falsy behavior. Verified by reviewing the initialization code path at stub entry point."
```

Replace with:

```
PR checklist item: "Confirmed: `budget_override_pending` is explicitly initialized to `false` at dialogue stub entry for each `lineage_root_id` — not left to default-falsy behavior. A new skill invocation always starts with a clean override state. Verified by reviewing the initialization code path at stub entry point — initialization is per-invocation, not session-persistent."
```

### [SY-34] Partial correction failure abort — no governance gate

**Source:** IE-6
**File:** governance.md (append new gate)

- [ ] **Step 5: Add partial correction failure abort gate**

Append to governance.md:

```markdown

## Partial Correction Failure Abort Gate

Validates: routing-and-materiality.md §Affected-Surface Validity (partial correction failure post-abort behavior)

**[Activates when correction pipeline code is authored]** PR checklist item: "Confirmed: when rule 5 fires (partial correction failure), capsule assembly aborts and all 7 post-abort assertions hold: (1) no feedback capsule sentinel emitted, (2) no capsule body emitted, (3) no durable file written, (4) structured warning with entry index and unexpected state values emitted, (5) no hop suggestion text in prose output, (6) no `dialogue-orchestrated-briefing` sentinel in output, (7) all `upstream_handoff` capability flags torn down. Verified by tracing the abort code path."
```

### [SY-35] No-auto-chaining grep — self-activates during contract authoring

**Source:** IE-7
**File:** governance.md (extend Helper Function Tracking or append note)

- [ ] **Step 6: Add conditional co-reviewer gate for CI scope activation**

In governance.md, in the Helper Function Tracking section (line 22-28), after the paragraph about `COMPOSITION_HELPERS.md`, append:

```markdown

**CI scope activation for composition contract:** The PR that creates `packages/plugins/cross-model/references/composition-contract.md` MUST enable the no-auto-chaining grep check for the contract file in CI configuration. The grep check self-activates during contract authoring — a co-reviewer MUST verify the CI scope was updated as part of the contract authoring PR.
```

### [SY-36] Correction rule sequential ordering — no governance gate

**Source:** IE-8
**File:** governance.md (append new gate)

- [ ] **Step 7: Add correction rule ordering gate**

Append to governance.md:

```markdown

## Correction Rule Sequential Ordering Gate

Validates: routing-and-materiality.md §Affected-Surface Validity (correction rule ordering)

**[Activates when correction pipeline code is authored]** PR checklist item: "Confirmed: correction rules are evaluated as a sequential if-else chain in listed order (1→2→3→4→5). An entry matching rule 1 does NOT proceed to rule 2 evaluation. Verified by structural inspection — the correction code path is a sequential short-circuit chain, not independent parallel checks."
```

- [ ] **Step 8: Commit T6**

```bash
git add docs/superpowers/specs/skill-composability/governance.md
git commit -m "fix(spec): remediate 7 singleton governance gate findings from review round 12"
```

---

## Task 7 — P1 Verification Backfill + SY-16 Semantic Template Rewrite (10 findings + 1 emerged)

**Finding count:** 10 P1 + 1 emerged cross-resolution obligation
**Findings:** SY-16, SY-24, SY-25, SY-27, SY-28, SY-29, SY-30, SY-31, SY-32, SY-44 + emerged (SY-16 verification.md rewrite)
**Files:** verification.md
**Depends on:** T4 (P0 gates landed), T3 (routing prose stable for SY-16 cross-reference)

### [SY-16 + emerged] Combined-indeterminate prose match — replace exact-text with constrained semantic template

**Source:** CE-7
**File:** verification.md:94 (combined budget/override indeterminate row)
**Dialogue resolution:** Constrained semantic template with 6 ordered elements replacing exact-text matching

- [ ] **Step 1: Rewrite SY-16 verification row**

In verification.md line 94, in the combined budget/override indeterminate row, find:
```
matching the specific combined prose text in routing-and-materiality.md
```
Replace with:
```
satisfying the constrained semantic template: the prose warning MUST (1) mention "context compression" as the cause, (2) state that the "budget counter" is unavailable, (3) state that "override" confirmation is unavailable and requires re-confirmation, (4) state the operational policy: proceed as if budget is available, (5) instruct the user to say "continue", (6) make clear this allows only one more hop. Elements MUST appear in this order: cause, then policy, then user action. See routing-and-materiality.md §Budget Enforcement Mechanics for the canonical prose
```

### [SY-24] Consumption discovery scenario (5) — no fallback path assertion

**Source:** VR-5
**File:** verification.md:114 (consumption discovery row)

- [ ] **Step 2: Extend scenario (5) with structural ordering check**

In verification.md line 114, in scenario (5), find:
```
(5) Durable file exists with non-matching `subject_key` → verify consumer falls through to conversation-local scan (durable file not consumed despite existing at path)
```
Append after this text:
```
. Additionally verify: consumer's fallback path follows the 5-step check ordering — the non-matching `subject_key` is detected at the identity-scan stage (step 0 of durable store discovery), before any file content is read
```

### [SY-25] Standalone coherence assertion (4) — self-certification only

**Source:** VR-6
**File:** verification.md:71 (standalone coherence row)

- [ ] **Step 3: Add independent reviewer verification requirement**

In verification.md line 71, in the standalone coherence row, find the text about assertion (4) and the dialogue standalone coherence test. After the text "(dialogue assertion 4 coverage is deferred until the dialogue composition stub is authored", add:

```
— an independent reviewer (not the stub author) MUST verify assertion (4) during the authoring PR review per governance.md §`dialogue-orchestrated-briefing` Sentinel Suppression Check)"
```

### [SY-27] briefing_context determinism — "model call" undefined in skill context

**Source:** VR-11
**File:** verification.md:104 (briefing_context determinism row)

- [ ] **Step 4: Clarify "model call" terminology**

In verification.md line 104, in the briefing_context determinism structural check row, find:
```
contains no conditional branch that calls a model or uses model-variable output
```
Replace with:
```
contains no conditional branch that invokes selective/judgmental content generation (model calls, prompt-based selection, sampling) — the projection MUST be templatic/enumerative (deterministic data transformation from structured input to structured output)
```

### [SY-28] Validator fixture set missing fail cases for checks #8, #9

**Source:** VR-14
**File:** verification.md:154 (minimum fixture set paragraph)

- [ ] **Step 5: Add fail fixtures for checks #8 and #9**

In verification.md line 154, in the "Minimum fixture set" paragraph, after "one stub where the error handler re-derives `record_path` instead of reading from the pre-computed variable (fails check 7).", add:

```
, (d) one stub where the `thread_created_at` comparison uses string comparison instead of parsed numeric timestamps (fails check 8 — thread freshness comparison), (e) one contract whose routing classification rules table includes a row not present in any stub (fails check 9 — stub→contract semantic parity, detected by reverse direction mismatch).
```

### [SY-29] No-auto-chaining indirect delegation — COMPOSITION_HELPERS.md completeness unverified

**Source:** VR-15
**File:** verification.md:73 (COMPOSITION_HELPERS.md row)

- [ ] **Step 6: Add cross-reference requirement**

In verification.md line 73, in the `COMPOSITION_HELPERS.md` exists row, at the end of "Structural: verify the file lists every function called from the feedback capsule assembly path (diff-based on each PR)", append:

```
. Reviewer MUST cross-reference helper function list against actual call sites in the capsule assembly path — completeness is verified by reviewing both the list and the call graph, not by trusting the list alone
```

### [SY-30] thread_created_at precision normalization — no verification

**Source:** VR-18
**File:** verification.md:122 (created_at precision row)

- [ ] **Step 7: Add Codex API second-precision test case**

In verification.md line 122, in the `created_at` precision row, after test case (3), add:

```
(4) Codex API second-precision input: `thread_created_at: 2026-03-18T14:30:52Z` (no fractional digits — second-precision from Codex API response) → verify normalized to `20260318T143052.000` with `.000` appended (not stored as-is without milliseconds). This exercises the Codex API integration path where timestamps arrive at second precision
```

### [SY-31] Multi-file same-subject_key durable store disambiguation — not tested

**Source:** VR-19
**File:** verification.md:114 (consumption discovery row)

- [ ] **Step 8: Add multi-file same-subject_key scenario**

In verification.md line 114, in the consumption discovery row, after scenario (5), add:

```
(6) Multi-file disambiguation: two durable files in `.claude/composition/feedback/` with the same `subject_key` but different `created_at` timestamps → verify consumer selects the file with the most recent `created_at` (newest-first scan applies to durable store discovery, not just conversation-local sentinel scan). The durable store discovery algorithm uses `subject_key` matching per lineage.md §Consumption Discovery — when multiple files match, the most recent takes precedence
```

### [SY-32] supersedes cross-source max — no inverse fixture

**Source:** VR-20
**File:** verification.md:124 (supersedes cross-source max selection row)

- [ ] **Step 9: Add inverse fixture (newer in durable store)**

In verification.md line 124, in the supersedes cross-source max selection row, after "Verify `supersedes` references artifact B's `artifact_id`", add:

```
(4c) Inverse: prior `dialogue_feedback` artifact A exists in conversation context with older `created_at`; artifact B exists at durable path with same `subject_key` and newer `created_at`. Verify `supersedes` references artifact B's `artifact_id` (newer across both sources, durable store wins). This is the inverse of scenario (4b) — confirms cross-source max selection is symmetric regardless of which source contains the newer candidate
```

### [SY-44] Posture precedence — missing invalid-value test case

**Source:** VR-13
**File:** verification.md:106 (posture precedence row)

- [ ] **Step 10: Add invalid-value test case**

In verification.md line 106, in the posture precedence row, after scenario (3), add:

```
(4) Invalid value: `upstream_handoff.recommended_posture` set to an invalid value (e.g., `unknown_posture`), no `--posture` flag → verify default `collaborative` applied (invalid handoff posture treated as absent, not propagated)
```

- [ ] **Step 11: Commit T7**

```bash
git add docs/superpowers/specs/skill-composability/verification.md
git commit -m "fix(spec): remediate 11 verification backfill findings from review round 12"
```

---

## Task 8 — Delivery Tracking + P2 Batch (12 findings)

**Finding count:** 4 P1 (delivery tracking) + 8 P2
**Findings:** SY-21, SY-22, SY-23, SY-39, SY-40, SY-41, SY-42, SY-43, SY-45, SY-46, SY-47, SY-48
**Files:** delivery.md, verification.md, routing-and-materiality.md
**Depends on:** T4, T5 (governance gates stable)

### [SY-21] COMPOSITION_HELPERS.md CI check — path scope undefined

**Source:** VR-2
**File:** delivery.md (add to open items or inline note)

- [ ] **Step 1: Add CI trigger scope to delivery.md**

In delivery.md, in the open items table, after item #11 (line 65), add a new row:

```markdown
| 12 | `COMPOSITION_HELPERS.md` CI check scope | Active (interim) | CI check triggers on PRs modifying files in the feedback capsule assembly path. Scope: skill stub files (AR, NS, dialogue composition sections), composition contract, and `COMPOSITION_HELPERS.md` itself. Do NOT apply to spec files, test fixtures, or documentation. |
```

### [SY-22] topic_key grep check scope expansion — no tracking

**Source:** VR-3
**File:** delivery.md (activation checklist)

- [ ] **Step 2: Add topic_key scope expansion to activation checklist**

In delivery.md, in the Governance Gate Activation Checklist table, add a new row:

```markdown
| Composition contract (`composition-contract.md`) authored | `topic_key` Scope Guard (extend grep check scope to include contract file) |
```

Wait — the contract row already exists (line 25). Update it instead. Change:
```markdown
| Composition contract (`composition-contract.md`) | Contract Marker Verification, `topic_key` Scope Guard |
```
To:
```markdown
| Composition contract (`composition-contract.md`) | Contract Marker Verification, `topic_key` Scope Guard (extend grep scope to contract file) |
```

### [SY-23] Abort-path independent test fixture mandate — no tracking

**Source:** VR-4
**File:** delivery.md (activation checklist)

- [ ] **Step 3: Add abort-path test fixture tracking**

In delivery.md, in the Governance Gate Activation Checklist table, in the "Dialogue consumer stub" row (added in T4), update the Gates Activated column to include the abort-path test mandate:

```markdown
| Dialogue consumer stub (durable store behavior) | Consumer Durable Store Check Ordering, `upstream_handoff` Abort Teardown Check, Abort-Path Independent Test Fixtures (two separate fixtures — one per abort path, no shared fixture) |
```

### [SY-39] Budget non-consumption for held items — implicit mechanism not stated

**Source:** CE-13
**File:** routing-and-materiality.md (after the hold behavior description)

- [ ] **Step 4: State budget non-consumption explicitly**

In routing-and-materiality.md, in the ambiguous non-response section (line ~213-215 area), after the text about held items having `hold_reason: routing_pending`, find the assertion about budget count. If the text:
```
held items have no emitted capsule (no sentinel), so the budget counter naturally excludes them
```
exists in verification.md (line 91), this is already stated at the verification level. In routing-and-materiality.md, add a clarifying note in the §Ambiguous Item Behavior section. After "no hop suggestion emitted for this item", add:

```
. Held items do not consume budget — the budget counter counts qualifying artifacts (which require an emitted capsule sentinel), and held items produce no emitted capsule
```

### [SY-40] delivery.md uses non-primary term "Inline composition stub"

**Source:** CC-4
**File:** delivery.md:48

- [ ] **Step 5: Fix terminology in delivery.md**

In delivery.md line 48, find:
```
4. **Inline composition stub:** The largest stub of the three skills.
```
Replace with:
```
4. **Composition stub:** The largest stub of the three skills.
```

### [SY-41] delivery.md uses non-canonical path for governance.md reference

**Source:** CC-5
**File:** delivery.md:21

- [ ] **Step 6: Fix governance.md path**

In delivery.md line 21, find:
```
[governance.md](../skill-composability/governance.md)
```
Replace with:
```
[governance.md](governance.md)
```

### [SY-42] Budget exhaustion + continuation_warranted fixture is model-dependent

**Source:** VR-7
**File:** verification.md:89 (soft iteration budget row)

- [ ] **Step 7: Add model-dependency note**

In verification.md line 89, in the soft iteration budget row, at the end of the `continuation_warranted: true` assertion, add:

```
**Accepted limitation:** The `continuation_warranted` value depends on synthesis judgment (model-dependent). If the fixture produces `continuation_warranted: false` instead of `true`, adjust the fixture scenario to use stronger continuation signals — the test targets the interaction between `continuation_warranted` and budget enforcement, not the synthesis itself
```

### [SY-43] record_path null-prevention — only structural review, no behavioral test

**Source:** VR-8
**File:** verification.md:57 (record_path non-null happy path row)

- [ ] **Step 8: Add behavioral aspiration note**

In verification.md line 57, at the end of the record_path non-null happy path row, add:

```
**Future:** When a stub-level write-success test double is feasible, convert this from structural review to behavioral assertion — verify the emitted capsule contains a non-null `record_path` matching the expected `.claude/composition/feedback/` path pattern
```

### [SY-45] topic_key "trailing qualifier" — underspecified word boundary

**Source:** VR-16
**File:** verification.md:126 (topic_key normalization row)

- [ ] **Step 9: Specify word boundary for trailing qualifier**

In verification.md line 126, in the topic_key normalization row, test case (3), find:
```
(3) strip trailing qualifiers: "redaction pipeline implementation" → `redaction-pipeline`
```
Replace with:
```
(3) strip trailing qualifiers at word boundary: "redaction pipeline implementation" → `redaction-pipeline` (strips terminal words matching the qualifier set: `implementation`, `design`, `plan`, `proposal`, `overview`, `summary`; only the last word is checked, not recursive)
```

### [SY-46] record_path null-prevention exception scope narrowed

**Source:** IE-10
**File:** governance.md:56-62 (record_path Null-Prevention Review)

- [ ] **Step 10: Broaden exception scope**

In governance.md, in the record_path Null-Prevention Review section, find:
```
including exception paths before write attempt (path construction failure)
```
Replace with:
```
including all exception paths before write attempt (path construction failure, permission errors, directory creation failures, and any other pre-write exception)
```

### [SY-47] Single-writer durable file constraint — unsupported with no detection

**Source:** IE-11
**File:** routing-and-materiality.md (Selective Durable Persistence section)

- [ ] **Step 11: Add single-writer acknowledgment**

In routing-and-materiality.md, in the §Selective Durable Persistence section, after the "Write failure recovery" paragraph (line 286), add:

```markdown

**Single-writer assumption:** The durable file mechanism assumes a single writer per `subject_key` at any given time. Concurrent writers (e.g., parallel dialogue invocations producing feedback for the same subject) are unsupported in v1 — the last writer wins with no detection of the race condition. This is accepted because dialogue invocations within a single session are sequential, and cross-session concurrency is not a v1 target.
```

### [SY-48] Emission-time steps 2-4 ordering — no enforcement surface

**Source:** IE-12
**File:** verification.md (deferred verification table)

- [ ] **Step 12: Add deferred verification entry for steps 2-4 ordering**

In verification.md, in the Deferred Verification table (line 158+), add a new row:

```markdown
| Emission-time validation steps 2-4 ordering | [routing-and-materiality.md](routing-and-materiality.md#affected-surface-validity) | Code review responsibility — verify steps 2 (`classifier_source`), 3 (`materiality_source`), and 4 (`hold_reason`) are evaluated in listed order for reproducible diagnostic output. Activation trigger: when emission-time validation code is authored. |
```

- [ ] **Step 13: Commit T8**

```bash
git add docs/superpowers/specs/skill-composability/delivery.md docs/superpowers/specs/skill-composability/verification.md docs/superpowers/specs/skill-composability/routing-and-materiality.md docs/superpowers/specs/skill-composability/governance.md
git commit -m "fix(spec): remediate 12 delivery tracking + P2 findings from review round 12"
```

---

## Finding Coverage Matrix

| SY | Priority | Task | Finding |
|----|----------|------|---------|
| SY-1 | P1 (3 reviewers) | T2 | record_path gate wrong citation |
| SY-2 | P1 (3 reviewers) | T2 | Co-review gate missing pipeline citation |
| SY-3 | P1 (3 reviewers) | T2 | Sentinel suppression dangling reference |
| SY-4 | **P0** (2 reviewers) | T4 | Post-abort flag teardown no enforcement |
| SY-5 | P1 (2 reviewers) | T2 | Parity table assertion (7) ambiguity |
| SY-6 | **P0** | T4 | decomposition_seed flag accuracy |
| SY-7 | **P0** | T4 | Step 0 flag read source |
| SY-8 | **P0** | T4 | tautology_filter_applied Stage A rejection |
| SY-9 | **P0** | T4 | 5-step check ordering interim enforcement |
| SY-10 | P1 | T5 | hold_reason assignment precedence |
| SY-11 | P1 | T5 | hold_reason emission-time gate |
| SY-12 | P1 | T5 | hold_reason behavioral test limitation |
| SY-13 | P1 | T5 | hold_reason grep structural misplacement |
| SY-14 | P1 | T6 | tautology_filter_applied checklist format |
| SY-15 | P1 | T3 | 6 prose cases vs 5 formal steps |
| SY-16 | P1 | T7 | Combined-indeterminate prose match |
| SY-17 | P1 | T6 | source_artifacts provenance gate |
| SY-18 | P1 | T3 | "those items" ambiguity |
| SY-19 | P1 | T1 | Composition contract in spec.yaml |
| SY-20 | P1 | T5 | supersedes key-presence test |
| SY-21 | P1 | T8 | COMPOSITION_HELPERS.md CI scope |
| SY-22 | P1 | T8 | topic_key grep scope expansion |
| SY-23 | P1 | T8 | Abort-path test fixture tracking |
| SY-24 | P1 | T7 | Consumption discovery fallback assertion |
| SY-25 | P1 | T7 | Standalone coherence reviewer requirement |
| SY-26 | P1 | T6 | Tier 3 calibration gate |
| SY-27 | P1 | T7 | "model call" terminology |
| SY-28 | P1 | T7 | Validator fixture checks #8, #9 |
| SY-29 | P1 | T7 | COMPOSITION_HELPERS.md completeness |
| SY-30 | P1 | T7 | Timestamp precision normalization |
| SY-31 | P1 | T7 | Multi-file same-subject_key |
| SY-32 | P1 | T7 | supersedes cross-source inverse |
| SY-33 | P1 | T6 | budget_override_pending scoping |
| SY-34 | P1 | T6 | Partial correction failure gate |
| SY-35 | P1 | T6 | No-auto-chaining CI scope |
| SY-36 | P1 | T6 | Correction rule ordering gate |
| SY-37 | P2 | T1 | README enforcement_mechanism precedence |
| SY-38 | P1 | T5 | supersedes SHOULD vs MUST |
| SY-39 | P2 | T8 | Budget non-consumption stated |
| SY-40 | P2 | T8 | delivery.md terminology |
| SY-41 | P2 | T8 | delivery.md path |
| SY-42 | P2 | T8 | Model-dependent fixture note |
| SY-43 | P2 | T8 | record_path behavioral note |
| SY-44 | P2 | T7 | Posture precedence invalid value |
| SY-45 | P2 | T8 | topic_key word boundary |
| SY-46 | P2 | T8 | record_path exception scope |
| SY-47 | P2 | T8 | Single-writer acknowledgment |
| SY-48 | P2 | T8 | Steps 2-4 ordering deferral |
| E-1 | emerged | T4 | SY-4 delivery activation |
| E-2 | emerged | T5 | SY-10-13 delivery activation |
| E-3 | emerged | T7 | SY-16 verification rewrite |
