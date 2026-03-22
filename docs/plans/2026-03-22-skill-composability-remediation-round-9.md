# Skill Composability Spec Remediation Plan — Round 9

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remediate 47 findings (2 P0, 25 P1, 20 P2) from the round 9 spec review of the skill-composability spec.

**Architecture:** Three commits ordered by priority: P0 surgical fixes first, P1 batch second (corroborated findings first, then by file), P2 batch third. A Codex dialogue (thread `019d173d-c11c-7482-bf0a-304d70a742a2`) confirmed CC-2 is a prose-count defect (3 edits, no cascading verification breakage) and SY-1 removal is safe.

**Tech Stack:** Markdown spec files only — no code changes.

**Source:** `.review-workspace/synthesis/report.md` (5-reviewer team, 2026-03-22)
**Scope:** 47 canonical findings across 9 spec files
**Spec:** `docs/superpowers/specs/skill-composability/` (10 files, ~1600 lines)

---

## Strategy

Three commits, linearly ordered by priority and dependency:

1. **P0 fixes** — Budget counter fixture contradiction (SY-4), constrained field enforcement gap (SY-5)
2. **P1 fixes** — 3 corroborated findings first, then 22 singletons ordered by file: routing-and-materiality.md → delivery.md → verification.md → pipeline-integration.md → spec.yaml
3. **P2 fixes** — 20 findings: authority seepage, terminology drift, test precision, enforcement completeness

Rationale: P0s are blocking and surgical. P1 corroborated findings have highest confidence (multi-reviewer convergence). Within P1 singletons, normative corrections in routing-and-materiality.md precede enforcement and verification fixes that reference them. P2s depend on P1 normative corrections being stable.

**Codex dialogue findings integrated:**
- CC-2 is a prose-count defect — validity table already has 8 valid tuples; fix is 3 edits (high confidence)
- SY-1 removal safe — authority chain flows through foundations.md independently
- Item #8 is a monolithic cell — all 5 item #8 findings should be applied in one coordinated pass
- Add explicit no-op statement for held-ambiguous items in correction pipeline (emerged)

---

### Task 1: P0 Fixes

**Finding count:** 2 P0
**Files:** verification.md, delivery.md

#### [SY-4] P0 — Budget counter test fixture contradicts normative counting algorithm

**Source:** CC-1
**File:** `verification.md:83` (budget counter fixture (1) in Routing and Materiality Verification table)

Fixture (1) claims a `[AR, NS]` 2-artifact chain produces `budget counter reads 2 (exhausted)`. The normative counting algorithm in routing-and-materiality.md:206-208 excludes the root AR from the counter — for `[AR, NS]`, only NS is a qualifying cross-skill transition, so counter = 1 (not exhausted). The correct exhaustion chain is `[AR, NS, AR-re-review]` = counter 2 (fixture (4) already tests this correctly).

- [ ] **Step 1: Fix fixture (1) in verification.md:83**

In the `| Soft iteration budget` row (line 83), find fixture (1) — the "Positive" test case:

```
OLD: (1) Positive: Artifact 1 = `ar:subject:timestamp` (`adversarial_review`) with matching `lineage_root_id`, Artifact 2 = `ns:subject:timestamp` (`next_steps_plan`) with same `lineage_root_id` → verify budget counter reads 2 (exhausted).

NEW: (1) Positive (not exhausted): Artifact 1 = `ar:subject:timestamp` (`adversarial_review`) with matching `lineage_root_id`, Artifact 2 = `ns:subject:timestamp` (`next_steps_plan`) with same `lineage_root_id` → verify budget counter reads 1 (not exhausted — the root AR is excluded from the counter per the targeted loop definition; only NS is a qualifying cross-skill transition).
```

- [ ] **Step 2: Verify no other fixture references the 2-artifact chain with counter = 2**

Run: `grep -n "counter.*=.*2\|counter reads 2\|budget counter = 2" docs/superpowers/specs/skill-composability/verification.md`

Confirm only the corrected fixture uses counter = 2, and it does so for the 3-artifact chain.

#### [SY-5] P0 — Variable-assignment paths for constrained fields lack static enforcement

**Source:** IE-1
**File:** `delivery.md:52` (item #8)

`classifier_source`, `materiality_source`, and `hold_reason` have MUST constraints. Grep-based CI catches literal assignments only. Variable-assignment paths bypass all interim checks.

- [ ] **Step 3: Add literal-assignment assertion to delivery.md item #8**

In delivery.md line 52, within item #8's text, after the **Contract marker verification (interim)** paragraph, add:

```markdown
**Constrained field literal-assignment assertion (interim):** PRs introducing helper functions that assign `classifier_source`, `materiality_source`, or `hold_reason` MUST use literal values only (e.g., `classifier_source = "rule"`, not `classifier_source = src`). The PR checklist item: "Confirmed: all assignments to `classifier_source`, `materiality_source`, and `hold_reason` in the feedback capsule assembly path use literal string values from the permitted set — no variable-mediated assignments." This gate closes the grep-evasion gap for the interim enforcement period. Retirement: when `validate_composition_contract.py` includes static analysis for variable-assigned constrained fields.
```

- [ ] **Step 4: Commit P0 fixes**

```bash
git add docs/superpowers/specs/skill-composability/verification.md docs/superpowers/specs/skill-composability/delivery.md
git commit -m "fix(spec): remediate 2 P0 findings from skill-composability spec review round 9"
```

---

### Task 2: P1 Fixes

**Finding count:** 25 P1 (3 corroborated + 22 singletons)
**Files:** routing-and-materiality.md, delivery.md, verification.md, pipeline-integration.md, spec.yaml

#### Corroborated Findings (3)

##### [SY-1] P1 — False authority attribution in delivery.md item #8 Governance clause

**Source:** AA-2 + CC-6 + IE-15 (3-reviewer convergence)
**File:** `delivery.md:52`

The Governance clause states "The normative enforcement authority for these rules resides with routing-and-materiality.md per spec.yaml." spec.yaml makes no such assignment — routing's `enforcement_mechanism` covers routing/pipeline enforcement, not PR governance. Codex dialogue confirmed removal is safe (authority chain flows through foundations.md independently).

- [ ] **Step 1: Remove the false attribution sentence**

In delivery.md line 52, within the **Governance:** paragraph of item #8, find and remove:

```
OLD: The normative enforcement authority for these rules resides with routing-and-materiality.md per spec.yaml. They are implementation guidance, not independent architectural constraints.

NEW: They are implementation guidance, not independent architectural constraints.
```

##### [SY-2] P1 — `dialogue-orchestrated-briefing` normal-path enforcement gap

**Source:** CE-4 + VR-4 (2-reviewer convergence)
**File:** `verification.md:65`

The MUST NOT prohibition on this sentinel in externalized output has no active enforcement for the normal execution path. Abort paths have structural assertions; the normal path has only self-attestation.

- [ ] **Step 2: Add interim grep-based CI check for the normal path**

In verification.md line 65, at the end of the existing `dialogue-orchestrated-briefing` verification row, after "(2) **Emission side:**" paragraph, add:

```
(3) **Normal-path CI check (interim):** Add to the grep-based CI check suite: `grep -n 'dialogue-orchestrated-briefing' <dialogue-stub-output-assembly-path>` — fail if the sentinel appears in any output-writing code path (not just abort paths). This supplements the emission-side structural check with an automated gate active at stub authoring time, not deferred to the validator. Activation: immediate when the dialogue stub is authored.
```

##### [SY-3] P1 — `record_path` pre-computation ordering lacks enforcement path

**Source:** VR-9 + IE-5 (2-reviewer convergence)
**File:** `verification.md:128-143` (validator acceptance criteria table)

The MUST for `record_path` pre-computation has no CI check and no upgrade path.

- [ ] **Step 3: Add as validator check #7**

In verification.md, after validator acceptance criteria check #6 row (line ~139), add:

```markdown
| 7 | `record_path` pre-computation ordering | [routing-and-materiality.md](routing-and-materiality.md#selective-durable-persistence) | Error handler reads `record_path` from a variable assigned before the correction pipeline gate — no re-derivation within the error handler |
```

Update the minimum fixture set to note: "one stub where the error handler re-derives `record_path` instead of reading from the pre-computed variable (fails check 7)."

#### Singletons by File — routing-and-materiality.md (6)

##### [CC-2] P1 — "6 valid pass-throughs" count should be 8

**Source:** CC-2
**File:** `routing-and-materiality.md:67,86,91`

Codex dialogue confirmed (high confidence): the validity table already encodes 8 valid tuples. Fix is exactly 3 prose edits. No cascading verification breakage.

- [ ] **Step 4: Fix line 67 header**

```
OLD: 6 valid pass-throughs out of 24 total cases. Invalid tuples (18 total)

NEW: 8 valid pass-throughs out of 24 total cases. Invalid tuples (16 total)
```

- [ ] **Step 5: Fix line 86 preamble**

```
OLD: Rules 1-4 collectively cover all 18 invalid tuple combinations in the 24-case validity matrix (24 total minus 6 valid pass-throughs)

NEW: Rules 1-4 collectively cover all 16 invalid tuple combinations in the 24-case validity matrix (24 total minus 8 valid pass-throughs)
```

- [ ] **Step 6: Rewrite line 91 "Remaining" bullet**

The current text describes the 2 `material:true/ambiguous` tuples as "remaining" invalids held before rule 5. They are valid pass-throughs.

```
OLD: - Remaining: `material: true, affected_surface: {diagnosis, planning}` with `suggested_arc: ambiguous` (2 tuples) — these are held in `unresolved[]` with `hold_reason: routing_pending` before reaching rule 5.

NEW: - The 2 `material: true` + `suggested_arc: ambiguous` tuples (`diagnosis/true/ambiguous` and `planning/true/ambiguous`) are valid pass-throughs — they are not covered by rules 1-4 because `ambiguous` is in their valid set. These items traverse the correction pipeline as no-ops and proceed to the placement stage, where they are routed to `unresolved[]` with `hold_reason: routing_pending` (see Post-Correction Placement table above).
```

##### [CE-1] P1 — Cross-tier guard omits `materiality_source` when Tier 1 model exclusion stands

**Source:** CE-1
**File:** `routing-and-materiality.md:152`

- [ ] **Step 7: Add `materiality_source: model` to the "Tier 2 does not match" branch**

```
OLD: - If Tier 2 does not match → the Tier 1 model exclusion stands. Set `material: false`.

NEW: - If Tier 2 does not match → the Tier 1 model exclusion stands. Set `material: false`, `materiality_source: model` (retaining the Tier 1 model judgment as the operative classification).
```

##### [CE-2] P1 — Completeness proof implies ambiguous items exit inside correction pipeline

**Source:** CE-2
**File:** `routing-and-materiality.md:91` (already rewritten in Step 6)

The Step 6 rewrite already addresses this by clarifying that valid pass-throughs "proceed to the placement stage." No additional edit needed — Step 6 subsumes CE-2.

##### [CC-3] P1 — Case (d) cites "rows 3-5" but row 5 has no `upstream_handoff`

**Source:** CC-3
**File:** `routing-and-materiality.md:121`

- [ ] **Step 8: Fix row reference**

```
OLD: rows 3-5

NEW: rows 3-4
```

##### [IE-2] P1 — `budget_override_pending` initialization requirement only in deferred verification

**Source:** IE-2
**File:** `routing-and-materiality.md:226`

- [ ] **Step 9: Add initialization clause to normative spec**

After the `budget_override_pending` description in line 226, add at the end of that paragraph:

```
`budget_override_pending` MUST be initialized to `false` at stub entry for each `lineage_root_id`. A new skill invocation always starts with a clean override state.
```

##### [IE-9] P1 — Thread freshness numeric comparison MUST has no interim structural check

**Source:** IE-9
**File:** `delivery.md:52` (item #8) + `verification.md:128-143` (validator table)

- [ ] **Step 10: Add thread freshness to item #8 PR checklist**

In delivery.md item #8, after the `record_path` pre-computation ordering checklist item, add:

```
**Thread freshness numeric comparison (mandatory check):** PR checklist item: "Confirmed: thread continuation vs. fresh start comparison uses parsed numeric timestamps (millisecond precision), not string comparison. Verified by reviewing the comparison code path for `created_at` vs `thread_created_at`."
```

- [ ] **Step 11: Add as validator check #8**

In verification.md, after the new check #7 row, add:

```markdown
| 8 | Thread freshness comparison | [routing-and-materiality.md](routing-and-materiality.md#thread-continuation-vs-fresh-start) | `created_at` vs `thread_created_at` comparison uses parsed numeric timestamps at millisecond precision — not string comparison |
```

#### Singletons by File — delivery.md (1, beyond SY-1)

##### [IE-6] P1 — No-auto-chaining co-review gate has no fallback if `COMPOSITION_HELPERS.md` absent

**Source:** IE-6
**File:** `delivery.md:52` (item #8)

- [ ] **Step 12: Make COMPOSITION_HELPERS.md a required deliverable**

In delivery.md item #8, find the `COMPOSITION_HELPERS.md` tracking paragraph and append:

```
`COMPOSITION_HELPERS.md` (or equivalent) is a required deliverable for any PR that introduces helper functions called from the feedback capsule assembly path. The file MUST exist before the co-review gate can pass — absence of the file when helper functions exist is a gate failure, not a deferral.
```

#### Singletons by File — verification.md (11)

##### [IE-3] P1 — Correction pipeline ordering: no interim enforcement for rule 5 relative positioning

**Source:** IE-3
**File:** `verification.md:75-76` (correction rules ordering row)

- [ ] **Step 13: Add walk-through fixture for rule 5 non-firing**

In verification.md, at the end of the correction rules ordering row (line 76), add:

```
Additionally, add a walk-through fixture for rule 5 non-firing: input a valid tuple (e.g., `diagnosis/true/adversarial-review`) → verify correction pipeline completes without reaching rule 5, confirming rule 5 fires only as a defensive fallback for unexpected states.
```

##### [IE-8] P1 — Boundary rule compliance has no enforcement

**Source:** IE-8
**File:** `verification.md:159`

- [ ] **Step 14: Escalate CODEOWNERS to MUST deliverable**

```
OLD: Recommend adding a CODEOWNERS or review checklist entry

NEW: Participating skill stubs MUST include a CODEOWNERS entry (or review checklist entry)
```

##### [IE-10] P1 — Stage A rejection: no verification that `upstream_handoff` remains fully absent

**Source:** IE-10
**File:** `verification.md:37` (Step 0 precondition, case c)

- [ ] **Step 15: Add absence assertion for capability flags after rejection**

In verification.md line 37-38, within the Step 0 case (c) post-abort verification assertions, add a 7th assertion:

```
(vii) verify all `upstream_handoff` capability flags (`decomposition_seed`, `gatherer_seed`, `briefing_context`, `tautology_filter_applied`) remain absent from pipeline state after rejection — no partial initialization.
```

##### [IE-11] P1 — Stub→contract drift: acknowledged insufficient with no remediation path

**Source:** IE-11
**File:** `verification.md:126,139`

- [ ] **Step 16: Add bidirectional semantic parity to validator table**

In verification.md line 126 (Contract Drift Verification), update the directionality note:

```
OLD: Stub→contract drift detection is manual-only ([delivery.md](delivery.md#open-items) item #8 protocol). This asymmetry is accepted for v1 — bidirectional automated detection is deferred

NEW: Stub→contract drift detection is manual-only ([delivery.md](delivery.md#open-items) item #8 protocol). `validate_composition_contract.py` MUST include bidirectional semantic parity (check #6 covers contract→stub; add check #9 for stub→contract) when implemented
```

Add to the validator acceptance criteria table (after check #8):

```markdown
| 9 | Stub→contract semantic parity | [Contract Drift Verification](#contract-drift-verification) above | Routing classification rules, materiality tier definitions, and consumer class assignments in contract match stub implementations (reverse of check 6) |
```

##### [VR-1] P1 — `tautology_filter_applied` absent-key warning test doesn't assert prose output

**Source:** VR-1
**File:** `verification.md:91` (NS adapter test case 5)

- [ ] **Step 17: Extend test to assert warning in prose synthesis text**

In verification.md line 91, in test case (5) for `tautology_filter_applied`, find the assertion about structured warning and add:

```
AND verify the warning appears in the skill's user-visible prose output (not only internal logging) — assert by checking the dialogue's emitted text contains a substring matching "adapter omitted tautology_filter_applied" or equivalent.
```

##### [IE-4] P1 — `tautology_filter_applied` presence check: no enforcement mechanism

**Source:** IE-4
**File:** `delivery.md:52` (item #8 co-review gate)

- [ ] **Step 18: Add to item #8 co-review gate**

In delivery.md item #8, within the co-review gate paragraph, add:

```
The co-review gate MUST also verify the NS adapter sets `tautology_filter_applied` in `upstream_handoff` capability flags (key presence, not just value correctness) — absence is a gate failure requiring remediation before merge.
```

##### [VR-2] P1 — Budget override context-compression recovery test infeasible

**Source:** VR-2
**File:** `verification.md:87` (budget override test case 4)

- [ ] **Step 19: Reclassify as structural check**

In verification.md line 87, in the budget override context-compression recovery test (case 4), add:

```
**Accepted limitation:** Context compression cannot be simulated in a behavioral test — the compaction mechanism is outside this spec's control boundary. Reclassify as structural check: verify the stub code path checks for visible "continue" message absence and emits the re-confirmation prompt. Add to deferred verification table as a code review responsibility with activation trigger: when budget override code is authored.
```

##### [VR-3] P1 — Tier 3 model-failure → `tautology_filter_applied: false` has no test case

**Source:** VR-3
**File:** `verification.md:91` (NS adapter test cases)

- [ ] **Step 20: Add test case (6)**

In verification.md line 91, after test case (5), add:

```
(6) Configure the NS adapter's Tier 3 model call to fail (timeout or indeterminate result) → verify `tautology_filter_applied` is `false` in the resulting `upstream_handoff`. This exercises the "For model-based tiers (Tier 3), a tier is not completed if the model call fails" clause from pipeline-integration.md.
```

##### [VR-5] P1 — `continuation_warranted: true` + budget exhausted: hop-suppression precedence untested

**Source:** VR-5
**File:** `verification.md:83` (budget enforcement test)

- [ ] **Step 21: Add precedence assertion**

In verification.md line 83, within the soft iteration budget test, add an explicit assertion:

```
Additionally assert: when `continuation_warranted: true` AND budget is exhausted (2/2 hops), the hop suggestion block MUST be omitted regardless of `continuation_warranted` value — omit-hop-suggestion rule takes precedence. Verify by: pre-seed a 2-hop exhausted chain where the synthesis produces `continuation_warranted: true`, confirm hop suggestion is suppressed.
```

##### [VR-6] P1 — 24-case walk-through claims to test "rules 1-5" but rule 5 is unreachable

**Source:** VR-6
**File:** `verification.md:75`

- [ ] **Step 22: Fix claim**

In verification.md line 75, in the "Correction rules only fire on invalid tuples" row:

```
OLD: Test both valid tuples (pass through uncorrected) and invalid tuples (corrected per rules 1-5)

NEW: Test both valid tuples (pass through uncorrected) and invalid tuples (corrected per rules 1-4). Rule 5 is unreachable from the closed 24-case validity matrix — it fires only for unexpected states outside the defined `affected_surface`/`suggested_arc` sets. Rule 5 is tested separately via the partial correction failure fixture.
```

##### [VR-7] P1 — `selected_tasks: []` producer test: no acceptance criterion

**Source:** VR-7
**File:** `verification.md:53`

- [ ] **Step 23: Add pass criterion for non-deterministic test**

In verification.md line 53, at the end of the `selected_tasks: []` producer test row, add:

```
**Pass criterion:** The fixture MUST produce the expected result (no handoff block emitted) in 5/5 consecutive runs. If the model selects tasks despite the fixture being designed to prevent it, the fixture needs redesign — do not accept non-deterministic pass/fail. A fixture that produces inconsistent results is a fixture bug, not a model calibration issue.
```

##### [VR-8] P1 — Upstream-source routing boundary test is negative-only

**Source:** VR-8
**File:** `verification.md:99`

- [ ] **Step 24: Add paired positive case**

In verification.md line 99, at the end of the upstream-source routing boundary test row, add:

```
**Paired positive case:** Same AR finding IDs forwarded via NS handoff `source_findings[]` → verify deterministic routing fires on those IDs, `classifier_source: rule` set on resulting entries. This confirms the boundary is directional (handoff IDs → deterministic routing, conversation-context IDs → model classification) rather than a blanket suppression of AR IDs.
```

##### [VR-10] P1 — Thread continuation scenario (9) doesn't verify prior `thread_id` absence

**Source:** VR-10
**File:** `verification.md:100`

- [ ] **Step 25: Rephrase as absence assertion**

In verification.md line 100, in thread continuation scenario (9), find the assertion about Codex API call and strengthen:

```
OLD: verify the Codex API call uses a new thread (no prior `thread_id` parameter passed to the API)

NEW: verify the Codex API call MUST NOT include the prior `thread_id` parameter — assert absence of `thread_id` in the API call, not just presence of a new thread. The distinction matters: some API implementations accept `thread_id: null` differently from omitting the parameter.
```

#### Singletons by File — pipeline-integration.md (1)

##### [IE-7] P1 — Erroneous `decomposition_seed: true` by adapter causes false abort

**Source:** IE-7
**File:** `pipeline-integration.md:36` (capability flags table)

- [ ] **Step 26: Add MUST clause for decomposition_seed truthfulness**

In pipeline-integration.md line 36, in the `decomposition_seed` capability flag row, append to the "NS Adapter Sets" cell:

```
The NS adapter MUST set `decomposition_seed: true` only when `--plan` was active during the NS skill run that produced this handoff AND the decomposition seeding stage actually ran. Setting `decomposition_seed: true` when `--plan` was not active causes a false Step 0 case (c) abort in the downstream dialogue with no recovery path — the materiality evaluator sees `decomposition_seed: true` + `tautology_filter_applied: false` and aborts.
```

#### Singletons by File — spec.yaml (1)

##### [AA-1] P1 — `delivery_layers` duplicates foundations.md with no conflict resolution

**Source:** AA-1
**File:** `spec.yaml:62-77`

- [ ] **Step 27: Annotate as informational-only**

In spec.yaml, add a comment before the `delivery_layers` key:

```yaml
  # NOTE: delivery_layers is informational — a convenience summary of the three-layer
  # authority hierarchy defined normatively in foundations.md §Three-Layer Delivery Authority.
  # On conflict, foundations.md is authoritative per fallback_authority_order.
```

- [ ] **Step 28: Commit P1 fixes**

```bash
git add docs/superpowers/specs/skill-composability/routing-and-materiality.md docs/superpowers/specs/skill-composability/delivery.md docs/superpowers/specs/skill-composability/verification.md docs/superpowers/specs/skill-composability/pipeline-integration.md docs/superpowers/specs/skill-composability/spec.yaml
git commit -m "fix(spec): remediate 25 P1 findings from skill-composability spec review round 9"
```

---

### Task 3: P2 Fixes

**Finding count:** 20 P2
**Files:** routing-and-materiality.md, verification.md, delivery.md, capsule-contracts.md, lineage.md, decisions.md, README.md

#### Authority Seepage Cluster (AA-3, AA-4, AA-5, AA-6)

##### [AA-3] P2 — capsule-contracts.md Design Notes duplicates normative claim

**File:** `capsule-contracts.md:234`

- [ ] **Step 1: Replace MUST with cross-reference**

```
OLD: The `implements_composition_contract: v1` drift detection marker is a presence signal only — it does not guarantee semantic conformance. Until `validate_composition_contract.py` is implemented ([delivery.md](delivery.md#open-items) item #6), the marker MUST be treated as a necessary but not sufficient conformance indicator.

NEW: The `implements_composition_contract: v1` marker is a presence signal only — see [foundations.md §Versioning and Drift Detection](foundations.md#versioning-and-drift-detection) for the normative conformance semantics and the necessary-but-not-sufficient interpretation.
```

##### [AA-4] P2 — lineage.md embeds delivery-state claim

**File:** `lineage.md:169`

- [ ] **Step 2: Remove delivery-state assertion**

```
OLD: NS does not write files today. If `docs/plans/` is added later, use the same `artifact_id` scheme. See [delivery.md](delivery.md#open-items) for pending implementation items.

NEW: NS file persistence is not implemented in v1 (delivery scope — see [delivery.md](delivery.md#open-items)). If added later, use the same `artifact_id` scheme.
```

##### [AA-5] P2 — routing-and-materiality.md embeds delivery PR co-review MUSTs

**File:** `routing-and-materiality.md:192`

- [ ] **Step 3: Replace enforcement coverage note with cross-reference**

In routing-and-materiality.md line 192, replace the enforcement coverage note's co-review directive:

```
OLD: Any helper function referenced from a composition stub's feedback capsule assembly path MUST be co-reviewed as part of the stub review and documented in the PR checklist. This is a known coverage gap in the interim enforcement

NEW: Helper-mediated indirect delegation chains are a known coverage gap in the interim grep-based enforcement. See [delivery.md](delivery.md#open-items) item #8 for the co-review gate that addresses this gap. This is a known coverage gap
```

##### [AA-6] P2 — README.md boundary rules table omits routing's enforcement_mechanism

**File:** `README.md` (boundary rules summary table)

- [ ] **Step 4: Add footnote to README boundary rules table**

In README.md, at the end of the boundary rules table, add a footnote:

```
Note: `routing` carries the `enforcement_mechanism` claim in addition to `behavior_contract` — changes to routing trigger enforcement review as well as behavioral review.
```

#### Spec Clarity (CE-3, CE-8)

##### [CE-3] P2 — `hold_reason` MUST immediately relaxed by timing flexibility

**File:** `routing-and-materiality.md:50`

- [ ] **Step 5: Rewrite as behavioral outcome**

In routing-and-materiality.md line 50, find the hold_reason MUST clause within the Non-response behavior paragraph:

```
OLD: The routing stage MUST set `hold_reason` to exactly `routing_pending` (no other value) when an ambiguous item is held. Implementations may set `hold_reason` either at the routing stage or at capsule assembly time, provided the value is `routing_pending` for held ambiguous items. The routing-stage attribution is architectural guidance, not a sequencing constraint — any implementation path that produces `hold_reason: routing_pending` for held ambiguous items satisfies the contract.

NEW: `hold_reason` MUST be `routing_pending` for every held ambiguous item in `unresolved[]`; MAY be set at routing stage or capsule assembly time (implementation timing is flexible — both approaches satisfy the invariant). Any implementation path that produces `hold_reason: routing_pending` for held ambiguous items satisfies the contract.
```

##### [CE-8] P2 — `classifier_source: rule` asymmetry undocumented

**File:** `routing-and-materiality.md:97` (near `classifier_source` description)

- [ ] **Step 6: Add clarifying statement**

After the existing `classifier_source` description in routing-and-materiality.md line 97, add:

```
**Asymmetry note:** Valid pass-through items retain their routing-stage `classifier_source` value (typically `model` for model-classified items, `rule` for deterministic routing matches). Corrected items always receive `classifier_source: rule` — the correction mechanism is the operative classifier, regardless of the original classification source. This asymmetry is intentional: corrections are deterministic rule applications, so `rule` is accurate.
```

#### Count and Cross-Reference Fixes (CC-4, CC-5, CC-7)

##### [CC-4] P2 — delivery.md "5 evaluation steps" count unsupported

**File:** `delivery.md:50` (item #7 notes)

- [ ] **Step 7: Replace unsupported count**

```
OLD: The most complex behavioral logic (5 evaluation steps with ordering dependencies)

NEW: The most complex behavioral logic (Step 0 precondition, novelty veto, three-tier materiality evaluation, and the correction pipeline — with ordering dependencies)
```

##### [CC-5] P2 — verification.md self-referential link uses roundabout path

**File:** `verification.md:83`

- [ ] **Step 8: Fix cross-reference path**

```
OLD: ../skill-composability/lineage.md#consumption-discovery

NEW: lineage.md#consumption-discovery
```

##### [CC-7] P2 — decisions.md D2 terminology drift

**File:** `decisions.md:22`

- [ ] **Step 9: Align terminology with foundations.md**

```
OLD: fall back to non-capsule behavior if absent or invalid

NEW: fall back to the appropriate alternative source if absent or invalid (see [foundations.md](foundations.md#consumer-classes) for per-arc fallback sources)
```

#### Enforcement Scope and Edge Cases (CE-5, CE-6, CE-7)

##### [CE-5] P2 — Dimension Independence co-review gate scope mismatch

**File:** `delivery.md:52` (item #8)

- [ ] **Step 10: Add constrained field check to co-review gate**

In delivery.md item #8, within the co-review gate, add to the checklist:

```
For each named helper function: confirm no assignment of `classifier_source` or `materiality_source` outside the literal set `{rule, model}`.
```

##### [CE-6] P2 — Budget counter + override both indeterminate

**File:** `routing-and-materiality.md:224` (budget enforcement mechanics)

- [ ] **Step 11: Add combined-indeterminate case**

After the override context-compression recovery paragraph (line 224), add:

```
**Combined indeterminate state:** When both the budget counter AND `budget_override_pending` are indeterminate (e.g., all conversation context compressed), apply the respective default for each independently: counter defaults to not-exhausted (permissive — heuristic), override defaults to not-pending (suppressive — governance boundary). If the counter default would permit a hop but the override default would suppress it, the override default takes precedence — governance re-confirmation MUST NOT be bypassed by a heuristic default.
```

##### [CE-7] P2 — `record_path` pre-computation ordering: authority scope concern

**File:** `routing-and-materiality.md:274`

- [ ] **Step 12: Reframe as behavioral outcome**

In routing-and-materiality.md line 274, in the "Path construction rule" paragraph, find the ordering MUST and add a scope clarification at the end of the paragraph:

```
OLD (last sentence of the paragraph): The pre-computation ordering is a code review responsibility — see verification.md for the accepted deferral.

NEW (last sentence of the paragraph): The pre-computation ordering is a code review responsibility — see verification.md for the accepted deferral. Note: the ordering constraint is a behavioral requirement on the output (the error message includes the correct pre-computed path), not a mandatory implementation strategy — any code organization that achieves the same observable outcome satisfies the contract.
```

#### Test Precision (VR-11, VR-12, VR-13, VR-14, VR-15)

##### [VR-11] P2 — Consumption discovery test missing reverse-scan ordering in fixture

**File:** `verification.md:106`

- [ ] **Step 13: Add explicit ordering note to fixture**

In verification.md line 106, in consumption discovery scenario (2), add:

```
Fixture ordering note: the invalid-newer capsule MUST be positioned newest-first in the test context (matching the reverse-scan discovery algorithm). The no-backtrack behavior is verified by: invalid entry encountered first → discovery stops → no capsule consumed (not "skip invalid, consume older").
```

##### [VR-12] P2 — Validator check #6 fail fixture underspecified

**File:** `verification.md:143`

- [ ] **Step 14: Specify minimum fail fixture**

In verification.md line 143, in the minimum fixture set description, update the check #6 reference:

```
OLD: Check 6 (semantic parity) uses the existing well-formed stub vs. a drift-injected version.

NEW: Check 6 (semantic parity) uses the existing well-formed stub vs. a drift-injected version. Minimum drift-injection: stub whose routing classification rules table omits the AR-precedence row (`diagnosis/true → adversarial-review`) — this is a single-row deletion that creates a detectable semantic gap.
```

##### [VR-13] P2 — `hold_reason` test verifies value but not timing-flexibility

**File:** `verification.md:67`

- [ ] **Step 15: Add timing-flexibility note**

In verification.md line 67, at the end of the `hold_reason` test row, add:

```
Note: both routing-stage-assignment and capsule-assembly-time-assignment implementations satisfy this test — code review MUST confirm no path overwrites `hold_reason` assignment during capsule assembly. The test verifies the final value, not the assignment timing.
```

##### [VR-14] P2 — Tier 3 tautology filter deferred entry: no merge-block on failure

**File:** `verification.md:151`

- [ ] **Step 16: Add merge-block clause**

In verification.md line 151, in the Tier 3 tautology filter deferred entry, add:

```
**Merge gate:** If any of the 4 Tier 3 examples misclassifies during the mandatory pre-merge evaluation, the PR MUST NOT be merged until the Tier 3 prompt is revised and all 4 examples classify correctly. A misclassification is a regression indicator, not a known-flaky test.
```

##### [VR-15] P2 — `source_artifacts[]` test misses standalone dialogue case

**File:** `verification.md:119`

- [ ] **Step 17: Add standalone dialogue test scenario**

In verification.md line 119, at the end of the `source_artifacts[]` test row, add:

```
Additionally test: standalone dialogue invocation where an AR capsule is visible in conversation context but no NS handoff was consumed (AR visible, no NS consumed) → verify feedback capsule's `source_artifacts[]` is empty (no entries). This confirms `source_artifacts[]` records consumption edges, not visibility.
```

#### Enforcement Completeness (IE-12, IE-13, IE-14)

##### [IE-12] P2 — `dialogue-orchestrated-briefing` consumption-side grep deferred

**File:** `verification.md:65`

- [ ] **Step 18: Add consumption-side grep as interim CI check**

In verification.md line 65, in the `dialogue-orchestrated-briefing` verification row, add to the consumption-side check:

```
**Consumption-side interim CI check:** `grep -rn 'dialogue-orchestrated-briefing' <stub-files-excluding-dialogue>` — fail if any non-dialogue skill stub or consumer code references this sentinel in a consumption pattern. Active immediately for stub authoring PRs, not deferred to the validator.
```

##### [IE-13] P2 — Budget scan vs consumption discovery: no enforcement prevents conflation

**File:** `routing-and-materiality.md:208` (budget enforcement mechanics)

- [ ] **Step 19: Add clarifying note distinguishing algorithms**

After the "What counts as structurally consumed" paragraph (line 208), add:

```
**Algorithm distinction:** The budget scan uses a complete-scan algorithm (continue past invalid entries to count all qualifying artifacts). This is DIFFERENT from consumption discovery ([lineage.md §Consumption Discovery](lineage.md#consumption-discovery)), which uses a no-backtrack algorithm (stop at first invalid entry). Implementations MUST NOT conflate these two algorithms — the budget counter continues past invalid entries to maintain an accurate count; consumption discovery stops to prevent stale capsule consumption. The budget test fixture (3) in [verification.md](verification.md) specifically tests this distinction.
```

##### [IE-14] P2 — `implements_composition_contract: v1` boundary-scope gap

**File:** `delivery.md:52` (item #8, contract marker verification paragraph)

- [ ] **Step 20: Strengthen the existing PR checklist item**

In delivery.md item #8, find the "**Contract marker verification (interim):**" paragraph:

```
OLD: **Contract marker verification (interim):** During stub authoring, reviewer MUST verify that `implements_composition_contract: v1` appears in active composition stub frontmatter (not in a comment, example, or disabled section). PR checklist item: "Confirmed: implements_composition_contract marker is within active stub boundaries."

NEW: **Contract marker verification (interim):** During stub authoring, reviewer MUST verify that `implements_composition_contract: v1` appears in active composition stub frontmatter (not in a comment, example, or disabled section). PR checklist item: "Confirmed: `implements_composition_contract: v1` appears in active composition stub frontmatter (not in a comment, example, or disabled section). Verified by inspecting the marker's location in the stub file — `grep -l` file-level presence is insufficient for this gate (it matches markers in comments)."
```

- [ ] **Step 21: Commit P2 fixes**

```bash
git add docs/superpowers/specs/skill-composability/routing-and-materiality.md docs/superpowers/specs/skill-composability/verification.md docs/superpowers/specs/skill-composability/delivery.md docs/superpowers/specs/skill-composability/capsule-contracts.md docs/superpowers/specs/skill-composability/lineage.md docs/superpowers/specs/skill-composability/decisions.md docs/superpowers/specs/skill-composability/README.md
git commit -m "fix(spec): remediate 20 P2 findings from skill-composability spec review round 9"
```

---

## Verification

After all three commits:

- [ ] **Step 1: Cross-reference consistency check**

Run: `grep -n "6 valid\|18 invalid\|18 total" docs/superpowers/specs/skill-composability/*.md`

Verify no stale "6 valid" or "18 invalid" counts remain anywhere in the spec.

- [ ] **Step 2: Verify delivery.md item #8 internal consistency**

Read delivery.md item #8 end-to-end. Confirm:
- The false authority sentence is gone (SY-1)
- The literal-assignment assertion is present (SY-5)
- The COMPOSITION_HELPERS.md requirement is present (IE-6)
- The thread freshness checklist item is present (IE-9)
- The tautology_filter_applied co-review check is present (IE-4)
- The constrained field dimension check is present (CE-5)
- The contract marker boundary-scope clarification is present (IE-14)

- [ ] **Step 3: Verify validator acceptance criteria table**

Read verification.md validator table. Confirm checks #7, #8, #9 are present and well-formed.

- [ ] **Step 4: Verify count consistency in routing-and-materiality.md**

Read routing-and-materiality.md lines 67-93. Confirm:
- Header says "8 valid pass-throughs"
- Proof says "16 invalid"
- "Remaining" bullet is rewritten to describe valid pass-throughs
- Rule 1-4 individual counts still sum to 16 (9+3+2+2)
