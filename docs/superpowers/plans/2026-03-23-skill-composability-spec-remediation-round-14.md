# Skill Composability Spec Remediation — Round 14

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remediate all 47 canonical findings from the round-14 spec review of the skill-composability specification.

**Architecture:** All changes are spec text edits within `docs/superpowers/specs/skill-composability/`. No code changes. Edits are organized by target file to minimize context switching and cross-edit conflicts. Governance.md receives the most changes (~20 findings touch it), so it is split across multiple tasks to keep diffs reviewable.

**Tech Stack:** Markdown spec files with YAML frontmatter. No build system.

**Review report:** `.review-workspace/synthesis/report.md`
**Findings files:** `.review-workspace/findings/{reviewer-id}.md`
**Spec directory:** `docs/superpowers/specs/skill-composability/`

---

## File Change Map

| File | Findings | Change Type |
|------|----------|-------------|
| `verification.md` | CC-1..CC-6, CC-8, VR-1..VR-3, VR-5, VR-7..VR-9, VR-12, VR-4, SY-1, CE-6, IE-14 | Count fixes, deferred table entries, protocol additions, validator table addition, test case additions, rewording |
| `governance.md` | VR-4, SY-1, SY-3, SY-4, AA-1..AA-3, IE-1..IE-4, IE-6, IE-11..IE-13, CE-1, CE-3..CE-5, CE-8, SY-5, VR-5 | New gates, gate rewrites, content from delivery.md, operationalization |
| `delivery.md` | CC-1, SY-2, VR-4, AA-1, AA-3, SY-4, IE-4 | Count fix, checklist additions, content replaced with cross-refs |
| `capsule-contracts.md` | AA-4, CC-7 | Pipeline-stage removal, anchor fix |
| `foundations.md` | AA-5, AA-6 | Rewording, reference fix |
| `pipeline-integration.md` | VR-10 | Invalid posture value clause |

---

### Task 1: Fix all count mismatches in verification.md and delivery.md

**Addresses:** CC-1, CC-2, CC-3, CC-4, CC-5, CC-6

**Files:**
- Modify: `verification.md` (5 rows in Routing/Materiality and Lineage tables)
- Modify: `delivery.md` (items #6 and #8)

- [ ] **Step 1: Fix CC-1 — validator acceptance criteria "9" → "10"**

In `delivery.md`, find and replace these three occurrences:

1. Item #6: change `all 9 acceptance criteria` to `all 10 acceptance criteria`
2. Item #8: change `all 9 acceptance criteria` to `all 10 acceptance criteria`

In `verification.md`, §Validator Acceptance Criteria, minimum fixture set description: change `passes all 9 checks` to `passes all 10 checks`

- [ ] **Step 2: Fix CC-2 — thread continuation "six" → "nine"**

In `verification.md`, thread continuation row: change `six dialogue test scenarios` to `nine dialogue test scenarios`

- [ ] **Step 3: Fix CC-3 — `--plan` not-set "three" → "four"**

In `verification.md`, `--plan` not-set row: change `three test scenarios` to `four test scenarios`

- [ ] **Step 4: Fix CC-4 — consumption discovery "four" → "six"**

In `verification.md`, consumption discovery row: change `four test scenarios` to `six test scenarios`

- [ ] **Step 5: Fix CC-5 — staleness detection "four" → "five"**

In `verification.md`, staleness detection row: change `four test scenarios` to `five test scenarios`

- [ ] **Step 6: Fix CC-6 — `supersedes` minting "five" → "six"**

In `verification.md`, `supersedes` minting rule row: change `five test scenarios` to `six test scenarios`

- [ ] **Step 7: Verify no other stale counts exist**

Search verification.md for all patterns matching `N test scenario` or `N dialogue test` and confirm each count matches the actual enumerated scenarios in its row.

Run: `grep -n 'test scenario\|test cases\|dialogue test' docs/superpowers/specs/skill-composability/verification.md`

- [ ] **Step 8: Commit**

```bash
git add docs/superpowers/specs/skill-composability/verification.md docs/superpowers/specs/skill-composability/delivery.md
git commit -m "fix(spec): correct 6 stale test scenario counts + validator criteria count (CC-1..CC-6)"
```

---

### Task 2: Fix cross-reference, formatting, and pattern issues

**Addresses:** CC-7, CC-8, AA-6, IE-14

**Files:**
- Modify: `capsule-contracts.md` (broken anchor)
- Modify: `foundations.md` (fragile spec.yaml line reference)
- Modify: `verification.md` (parity list, grep pattern)

- [ ] **Step 1: Fix CC-7 — broken anchor `lineage.md#basis-fields`**

In `capsule-contracts.md`, line 47, change:

```
(see [lineage.md](lineage.md#basis-fields))
```

to:

```
(see [lineage.md](lineage.md#basis-fields-key-minting-at-chain-root))
```

- [ ] **Step 2: Fix AA-6 — fragile spec.yaml line-number reference**

In `foundations.md`, §Three-Layer Delivery Authority (~line 73), change:

```
See `spec.yaml` lines 67–77 for the full external artifact declaration including `governed_by`, `authority_context`, and `conflict_rule` fields.
```

to:

```
See `spec.yaml` `external_artifacts.composition-contract` block for the full declaration including `governed_by`, `authority_context`, and `conflict_rule` fields.
```

- [ ] **Step 3: Fix CC-8 — abort-path parity list (f)/(g) redundancy**

In `verification.md`, partial correction failure row, abort-path parity section, merge items (f) and (g) into a single item:

Change the 7-item list `(a)-(g)` to a 6-item list `(a)-(f)` where the merged item reads:

```
(f) all `upstream_handoff` capability flags torn down — flags absent from post-abort pipeline state, no prior flags carried forward
```

Update all references to "seven shared assertions" in verification.md and governance.md to "six shared assertions."

- [ ] **Step 4: Fix IE-14 — non-POSIX `\s` in grep pattern**

In `verification.md`, `hold_reason` grep-based CI enforcement row, change the grep pattern from:

```
grep 'hold_reason' <files> | grep -Ev 'hold_reason:\s*(routing_pending|null)\s*$'
```

to:

```
grep 'hold_reason' <files> | grep -Ev 'hold_reason:[[:space:]]*(routing_pending|null)[[:space:]]*$'
```

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/specs/skill-composability/capsule-contracts.md docs/superpowers/specs/skill-composability/foundations.md docs/superpowers/specs/skill-composability/verification.md
git commit -m "fix(spec): broken anchor, fragile ref, parity redundancy, POSIX grep (CC-7, CC-8, AA-6, IE-14)"
```

---

### Task 3: P0 — `decomposition_seed` false-flag verification path

**Addresses:** VR-4

**Files:**
- Modify: `delivery.md` (activation checklist)
- Modify: `governance.md` (co-review gate)

- [ ] **Step 1: Add NS stub row to delivery.md §Governance Gate Activation Checklist**

Add a new row to the Governance Gate Activation Checklist table:

```markdown
| NS composition stub | Stub Composition Co-Review, `decomposition_seed` false-flag behavioral test (verification.md NS adapter row — P0 merge gate prerequisite) |
```

- [ ] **Step 2: Add explicit merge-blocking requirement to governance.md**

In `governance.md` §Stub Composition Co-Review Gate, after the existing `decomposition_seed` checklist item, add:

```markdown
**NS stub authoring gate:** The NS stub PR MUST include the behavioral test for `decomposition_seed: true` when `--plan` not active as a merge-blocking requirement. Absence of this test in the PR is a gate failure, not a deferral. The test MUST produce a verifiable failure (downstream dialogue hits Step 0 case (c) abort) when `decomposition_seed` is incorrectly set to `true`. See verification.md §Routing and Materiality Verification (NS adapter `decomposition_seed` row) for the test specification.
```

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/specs/skill-composability/delivery.md docs/superpowers/specs/skill-composability/governance.md
git commit -m "fix(spec): P0 — add decomposition_seed false-flag verification path (VR-4)"
```

---

### Task 4: `supersedes` enforcement + posture precedence normative gap

**Addresses:** SY-1 (CE-9 + VR-11 + IE-7), VR-10, CE-6

**Files:**
- Modify: `governance.md` (supersedes gate restructure)
- Modify: `verification.md` (validator check #11, test case addition)
- Modify: `pipeline-integration.md` (invalid posture clause)

- [ ] **Step 1: Restructure governance.md `supersedes` gate (SY-1/IE-7)**

In `governance.md` §Stub Composition Co-Review Gate, replace the `supersedes` paragraph with two separate items:

```markdown
**`supersedes` Key-Presence (Emitter Gate)**

PR checklist item: "Confirmed: emitted capsules always include the `supersedes` key (present with value `null` or prior `artifact_id`, never omitted). Verified by reviewing capsule assembly code paths for ALL three emitters (AR, NS, dialogue) — including primary emission path, fallback paths (advisory/tolerant rejection), abort-path edge cases, default initializers, and copy-construction."

Note: Consumer-side tolerance (treating absent `supersedes` as `null` per capsule-contracts.md §Shared Validity Rules) is a defensive compatibility measure only — it does NOT relax this emitter requirement.
```

- [ ] **Step 2: Add `supersedes` as validator check #11 in verification.md**

Add row #11 to the Validator Acceptance Criteria table:

```markdown
| 11 | `supersedes` key-presence | [capsule-contracts.md](capsule-contracts.md#shared-validity-rules) + [lineage.md](lineage.md#dag-structure) | Emitted capsules always include `supersedes` key (not omitted) — value `null` or prior `artifact_id` | `grep -l` key-presence check (active — covers file-level presence). Governance gate covers code-path trace (active) |
```

Update minimum fixture set: add `(f) stub that omits `supersedes` key entirely from emitted capsule (fails check 11 — `supersedes` key-presence)`.

- [ ] **Step 3: Add test case for `selected_tasks` absent-key (CE-6)**

In `verification.md` §Capsule Contract Verification, dialogue test cases, add:

```markdown
(4) invalid handoff where all required fields are present except `selected_tasks` key (key entirely absent, not empty) → verify rejection + normal pipeline proceeds. Distinct from case (2) (other missing required fields) and case (3) (present-but-empty). Confirms absent-key path exercises criterion 1 specifically.
```

- [ ] **Step 4: Add invalid posture value clause to pipeline-integration.md (VR-10)**

In `pipeline-integration.md` §Posture Precedence, after the precedence chain, add:

```markdown
**Invalid posture values:** An `upstream_handoff.recommended_posture` value outside the defined enum (`adversarial | collaborative | exploratory | evaluative | comparative`) MUST be treated as absent — default `collaborative` applies. Invalid values are not propagated.
```

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/specs/skill-composability/governance.md docs/superpowers/specs/skill-composability/verification.md docs/superpowers/specs/skill-composability/pipeline-integration.md
git commit -m "fix(spec): supersedes enforcement + posture normative gap + selected_tasks test (SY-1, VR-10, CE-6)"
```

---

### Task 5: Post-abort assertion gates + abort-path fixture conflict

**Addresses:** SY-3 (CE-2 + IE-5), SY-4 (CE-7 + VR-6)

**Files:**
- Modify: `governance.md` (abort gate split, fixture gate split)
- Modify: `delivery.md` (item #13 clarification)

- [ ] **Step 1: Split post-abort governance gate into sub-checks (SY-3)**

In `governance.md` §Partial Correction Failure Abort Gate, replace the combined checklist assertion list with individually numbered sub-checks:

```markdown
PR checklist items (verify each independently):

1. "Confirmed: no `<!-- dialogue-feedback-capsule:v1 -->` sentinel appears in output. Verified by grep of output text."
2. "Confirmed: no YAML block matching the feedback capsule schema appears in output, independently of sentinel presence. Verified by searching for `artifact_kind: dialogue_feedback` pattern regardless of sentinel."
3. "Confirmed: no durable file written at `.claude/composition/feedback/`."
4. "Confirmed: structured warning emitted containing the failing entry's index and unexpected state values (`affected_surface`, `material`, `suggested_arc`)."
5. "Confirmed: no hop suggestion text appears in prose output. Verified by tracing post-abort code path and confirming no branch emits hop suggestion text after abort."
6. "Confirmed: no `<!-- dialogue-orchestrated-briefing -->` sentinel in output."
7. "Confirmed: all `upstream_handoff` capability flags torn down — flags either evaluate to `false` or are absent from state."
```

- [ ] **Step 2: Clarify delivery.md item #13 (SY-4)**

In `delivery.md` item #13, replace:

```
A single test file (or test block) that covers all three cascade assertions
```

with:

```
A single test file containing three independent fixture functions/blocks: (1) standalone coherence assertion (4), (2) partial correction failure assertion (6), (3) Step 0 case (c) sub-assertion (vi). Assertions (2) and (3) MUST be in separate fixture functions per governance.md §Abort-Path Independent Test Fixtures Gate — they MUST NOT share a single fixture.
```

- [ ] **Step 3: Split governance.md Abort-Path Independent Test Fixtures Gate (VR-6)**

Add to the gate text:

```markdown
**Cross-activation check:** When the second abort path is authored (whichever comes second), the PR MUST verify both fixtures exist and pass independently. The reviewer confirms: "Both abort-path fixture functions exist — one for Step 0 case (c) and one for partial correction failure. Each has a complete, independent assertion set. Verified by reviewing test file structure."
```

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/specs/skill-composability/governance.md docs/superpowers/specs/skill-composability/delivery.md
git commit -m "fix(spec): post-abort gate sub-checks + fixture conflict resolution (SY-3, SY-4)"
```

---

### Task 6: Authority misplacement — move enforcement content to governance.md

**Addresses:** AA-1, AA-2, AA-3

**Files:**
- Modify: `governance.md` (new gates)
- Modify: `delivery.md` (replace content with cross-refs)

- [ ] **Step 1: Create bidirectional review gate in governance.md (AA-1)**

Add new section to `governance.md`:

```markdown
## Contract-Stub Bidirectional Review Gate

Validates: foundations.md §Versioning and Drift Detection (drift detection invariant)

**Contract → stub:** Any modification to the composition contract's routing, materiality, lineage, or capsule schema sections MUST be accompanied by a manual review of all three participating skill stubs (adversarial-review, next-steps, dialogue) against the updated contract text. The PR description MUST include a stub-impact checklist confirming which stubs were reviewed and whether updates are needed.

**Stub → contract:** Any modification to a participating skill stub's composition section MUST be accompanied by verification that the change conforms to the current contract. The PR description MUST confirm the stub change does not diverge from contract intent.
```

- [ ] **Step 2: Replace delivery.md item #8 enforcement content with cross-ref (AA-1)**

In `delivery.md` item #8, replace the two MUST paragraphs (Contract → stub and Stub → contract) with:

```markdown
Bidirectional manual review protocol. See [governance.md §Contract-Stub Bidirectional Review Gate](governance.md#contract-stub-bidirectional-review-gate) for the normative enforcement procedures.
```

Retain the scheduling/status metadata: `Active (interim, retired when item #6 passes CI covering all 10 acceptance criteria...)`

- [ ] **Step 3: Move Governance Gate Activation Checklist to governance.md (AA-2)**

Add to `governance.md` a new section:

```markdown
## Gate Activation Conditions

Governance gates become active when their referenced artifacts are first created. When authoring any of the following, the PR MUST confirm the corresponding governance gates are applied:

[Copy the full table from delivery.md §Governance Gate Activation Checklist here]
```

In `delivery.md`, replace the Governance Gate Activation Checklist with a cross-reference:

```markdown
### Governance Gate Activation Checklist

See [governance.md §Gate Activation Conditions](governance.md#gate-activation-conditions) for the authoritative table of which gates activate when each artifact is authored.
```

- [ ] **Step 4: Add Promotion Gate to governance.md (AA-3)**

Add new section to `governance.md`:

```markdown
## Promotion Gate

Validates: delivery.md §Open Items (P0 blockers #6 and #7)

Composition system MUST NOT be promoted to production (`~/.claude/`) while either P0 blocker is open:
- Item #6: `validate_composition_contract.py` (CI enforcement of contract drift)
- Item #7: Materiality validation harness

Both must pass before promotion is authorized.
```

In `delivery.md`, replace the Promotion gate row content with: `See [governance.md §Promotion Gate](governance.md#promotion-gate).`

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/specs/skill-composability/governance.md docs/superpowers/specs/skill-composability/delivery.md
git commit -m "fix(spec): move enforcement content from delivery.md to governance.md (AA-1, AA-2, AA-3)"
```

---

### Task 7: Activation checklist completions

**Addresses:** SY-2 (IE-8, IE-9, IE-10)

**Files:**
- Modify: `governance.md` (activation table, since it was moved there in Task 6)

- [ ] **Step 1: Add missing activation entries**

In `governance.md` §Gate Activation Conditions table (moved from delivery.md in Task 6), add these rows:

```markdown
| Budget override code (in dialogue composition stub) | Budget Override Context-Compression Recovery Gate |
| Materiality evaluator code (part of dialogue composition stub) | Step 0 Flag Read Source Verification |
| Dialogue correction pipeline code (correction rules 1-5) | Correction Rule Sequential Ordering Gate, Emission-Time Validation Step Ordering Gate *(add to existing row's Gates Activated column)* |
```

For the correction pipeline row, the existing entry already lists "Abort-Path Independent Test Fixtures Gate" — append the two additional gates to the same row.

- [ ] **Step 2: Commit**

```bash
git add docs/superpowers/specs/skill-composability/governance.md
git commit -m "fix(spec): add 3 missing activation entries to gate conditions table (SY-2)"
```

---

### Task 8: Missing verification activation triggers and deferred entries

**Addresses:** VR-1, VR-2, VR-3, VR-5, VR-7, VR-8, VR-9, VR-12

**Files:**
- Modify: `verification.md` (deferred table, interim protocol)
- Modify: `governance.md` (new gate for VR-5)

- [ ] **Step 1: Add deferred table entries (VR-1, VR-2, VR-3, VR-7, VR-8)**

Add to `verification.md` §Deferred Verification table:

```markdown
| Validator unit tests (minimum pass/fail per check) | verification.md §Validator Acceptance Criteria | Activates when `validate_composition_contract.py` is implemented (delivery.md item #6). Retirement: all 11 checks have at least one pass and one fail fixture |
| Standalone `materiality_source` injection test | routing-and-materiality.md §Affected-Surface Validity | Activates when materiality harness is implemented (delivery.md item #7). This is a standalone test — do NOT combine with the 7th coherence test case |
| `tautology_filter_applied` omission warning user-visibility assertion | pipeline-integration.md §Two-Stage Admission | Activates when dialogue composition stub is authored. Behavioral: dialogue's emitted text must contain substring matching "adapter omitted tautology_filter_applied" |
| Consumption discovery multi-file durable store disambiguation | lineage.md §Consumption Discovery | Activates when behavioral harness is implemented. Two durable files with same `subject_key` → consumer selects most recent `created_at` |
| `topic_key` grep check scope extension to composition contract | lineage.md §Three Identity Keys | Activates when `composition-contract.md` is authored. CI grep check must include contract file in scope |
```

- [ ] **Step 2: Add rule 5 non-firing to interim protocol (VR-9)**

In `verification.md` §Interim Materiality Verification Protocol, add step 9:

```markdown
9. Rule 5 non-firing: input a valid tuple (e.g., `diagnosis/true/adversarial-review`) and walk through correction rules 1-4 in order. Confirm none fire and the pipeline exits without reaching rule 5. Confirm rule 5 is reachable only from unexpected states outside the 24-case matrix.
```

- [ ] **Step 3: Rename structural check terminology for NL stubs (VR-12)**

In `verification.md`, NS adapter `tautology_filter_applied` row, fault injection section, change `Decision: Reclassify as structural checks` to `Decision: Reclassify as semantic review checks` and change the acceptance criteria to:

```markdown
Acceptance criteria: stub text explicitly instructs that `tautology_filter_applied` MUST be set to `false` if any tier is skipped or fails, and enumerates all three tiers as mandatory steps.
```

- [ ] **Step 4: Add briefing_context determinism governance gate (VR-5)**

In `governance.md`, add new section:

```markdown
## Briefing Context Determinism Check

Validates: pipeline-integration.md §Pipeline Threading (deterministic projection requirement)

**[Activates when dialogue skill text is authored]** PR checklist item: "Confirmed: `briefing_context` injection in the briefing assembly code path uses deterministic data transformation (templatic/enumerative projection from structured input). No conditional branch invokes model calls, prompt-based selection, or sampling for content selection. Verified by structural review of the briefing assembly path for `source_findings` and `decision_gates` projection."
```

Add to §Gate Activation Conditions: `| Dialogue skill text (briefing assembly) | Briefing Context Determinism Check |`

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/specs/skill-composability/verification.md docs/superpowers/specs/skill-composability/governance.md
git commit -m "fix(spec): add 5 deferred entries + interim protocol step + NL check rewording + determinism gate (VR-1..VR-9, VR-12)"
```

---

### Task 9: Governance gate operationalization — enforcement completeness

**Addresses:** IE-1, IE-2, IE-3, IE-4, IE-6, IE-11, IE-13, CE-1, CE-3, CE-4, CE-5, CE-8, SY-5/IE-12

**Files:**
- Modify: `governance.md` (gate additions and rewrites)
- Modify: `verification.md` (CE-5 enforcement entry)

- [ ] **Step 1: Define capsule assembly path boundary (IE-1)**

In `governance.md` §Helper Function Tracking, add after the first paragraph:

```markdown
**Assembly path boundary:** The capsule assembly path begins at the point in the dialogue composition stub where `feedback_candidates[]` construction starts (post-synthesis item classification) and terminates at sentinel emission. A function is "in the assembly path" if it is reachable from this entry point via direct calls. The entry point name is defined by the dialogue stub author and MUST be documented in `COMPOSITION_HELPERS.md` as the root.

**Enumeration completeness:** Reviewers verify completeness by running `grep -n '<entry-point-function>' <stub-file>` to locate the root, then tracing all calls reachable from it. Every function encountered MUST appear in `COMPOSITION_HELPERS.md`.
```

- [ ] **Step 2: Define `COMPOSITION_HELPERS.md` canonical path (IE-2)**

In `governance.md` §Helper Function Tracking, change `COMPOSITION_HELPERS.md (or equivalent)` to:

```markdown
`packages/plugins/cross-model/COMPOSITION_HELPERS.md` — canonical location. No "or equivalent" — use this path exactly.
```

Update the CI check in `verification.md` to reference this path and remove the `(when present)` qualifier — the file is a required deliverable.

- [ ] **Step 3: Add grep-bounded enumeration for `decomposition_seed` (IE-3)**

In `governance.md` §Stub Composition Co-Review Gate, the `decomposition_seed` checklist item, add:

```markdown
Enumeration completeness is verified by `grep -n 'decomposition_seed' <stub-files>` — all occurrences must appear in the reviewer's enumeration. If any occurrence is absent, the gate fails.
```

- [ ] **Step 4: Add helper-mediated delegation partial mitigation (IE-4)**

In `governance.md` §Stub Composition Co-Review Gate, add:

```markdown
**Helper-mediated delegation mitigation (v1):** Helper functions in the capsule assembly path MUST NOT call any function not listed in `COMPOSITION_HELPERS.md`. Additionally, the grep-based CI check MUST scan `COMPOSITION_HELPERS.md` itself for slash-command patterns (`/adversarial-review`, `/next-steps`, `/dialogue`) and delegation keywords (`invoke`, `run_skill`, `dispatch`). This is a partial mitigation, not a closure of the helper-mediated delegation gap.
```

- [ ] **Step 5: Add CI scope activation fallback (IE-6)**

In `governance.md` §Helper Function Tracking, CI scope activation section, add:

```markdown
**Continuous CI invariant:** The CI configuration MUST verify the grep check file-scope list includes `composition-contract.md` whenever that file exists in the repository — not only when the creating PR adds it. This converts a one-time PR-time obligation into a persistent invariant.
```

- [ ] **Step 6: Add `record_path` ordering CI description (IE-11)**

In `governance.md` §`record_path` Pre-Computation Ordering Check, add:

```markdown
**Interim CI check (when dialogue stub is authored):** Verify that in the capsule assembly code, the `record_path` variable assignment appears before any line containing correction rule invocation. Pattern: grep line-ordering comparison of `record_path =` vs first correction-rule reference.
```

- [ ] **Step 7: Operationalize `budget_override_pending` initialization (IE-13)**

In `governance.md` §`budget_override_pending` Initialization Check, add:

```markdown
**Per-invocation definition:** A skill invocation begins when the user explicitly invokes `/dialogue` — state initialized at this point is per-invocation. State initialized at skill file load time (e.g., in a module-level variable or skill-level constant) would be session-persistent and does NOT satisfy this requirement. Reviewer confirms: initialization appears inside the invocation handler logic, not outside it.
```

- [ ] **Step 8: Add teardown false-vs-removal spec to gate (CE-1)**

In `governance.md` §Upstream handoff Abort Teardown Check, add to checklist:

```markdown
"Confirmed: torn-down flags either evaluate to `false` in boolean checks (set to `false`) or are absent from the state object (key removed). No abort path leaves capability flags set to `true`."
```

- [ ] **Step 9: Add step-ordering cross-reference to hold_reason gate (CE-3)**

In `governance.md` §hold_reason Assignment and Placement Review, add:

```markdown
"Confirmed: `hold_reason` validation (step 4) runs after `materiality_source` validation (step 3) — verified by structural inspection of the emission-time validation code path. Cross-reference: Emission-Time Validation Step Ordering Gate."
```

- [ ] **Step 10: Add NS empty-tasks governance gate (CE-4)**

In `governance.md`, add new section:

```markdown
## NS Empty-Tasks Omission Gate

Validates: capsule-contracts.md §Emission (Contract 2) (NS MUST NOT emit handoff with empty `selected_tasks`)

**[Activates when NS composition stub is authored]** PR checklist item: "Confirmed: NS stub code path for task selection contains a branch that omits the handoff block entirely when `selected_tasks` would be empty. Verified by tracing the code path from task selection logic to handoff emission — when zero tasks qualify, no sentinel is emitted."
```

Add to §Gate Activation Conditions: `| NS composition stub | NS Empty-Tasks Omission Gate |`

- [ ] **Step 11: Add budget counter algorithm governance gate (CE-5)**

In `governance.md`, add new section:

```markdown
## Budget Counter Algorithm Gate

Validates: routing-and-materiality.md §Budget Enforcement Mechanics (algorithm distinction)

**[Activates when dialogue composition stub is authored]** PR checklist item: "Confirmed: budget counter implementation uses a complete-scan algorithm (continues past invalid/unparseable capsule entries). Verified by confirming the budget scan loop does NOT stop at the first invalid sentinel — distinct from consumption discovery's no-backtrack behavior. Budget scan loop explicitly named and traced."

Enumeration completeness: `grep -n 'lineage_root_id\|budget' <dialogue-stub>` — all budget-related code paths must appear in the reviewer's trace.
```

- [ ] **Step 12: Add record_status absent-case no-file-read gate (CE-8)**

In `governance.md` §Consumer Durable Store Check Ordering Gate, add:

```markdown
"Confirmed: when `record_status` field is absent from the capsule, the consumer code path falls through immediately to conversation-local sentinel scan WITHOUT performing any file I/O on `record_path`. Verified by tracing the absent-`record_status` branch — no file read operation appears before falling through to precedence level 3."
```

- [ ] **Step 13: Add test file requirement to sentinel suppression gate (SY-5/IE-12)**

In `governance.md` §`dialogue-orchestrated-briefing` Sentinel Suppression Check, add:

```markdown
**Test file deliverable:** Per delivery.md item #13, a test file covering all three cascade assertions MUST be created in the same PR that authors the dialogue stub. The PR checklist item is an interim gate only — the test file is the retirement condition for the interim gate.
```

- [ ] **Step 14: Commit**

```bash
git add docs/superpowers/specs/skill-composability/governance.md docs/superpowers/specs/skill-composability/verification.md
git commit -m "fix(spec): operationalize 13 governance gates with boundaries + CI checks (IE-1..IE-13, CE-1..CE-8, SY-5)"
```

---

### Task 10: Authority boundary and scope fixes

**Addresses:** AA-4, AA-5

**Files:**
- Modify: `capsule-contracts.md` (pipeline-stage enumeration)
- Modify: `foundations.md` (P0 characterization)

- [ ] **Step 1: Remove pipeline-stage enumeration from capsule-contracts.md (AA-4)**

In `capsule-contracts.md` §Consumer Class (Contract 2), line 99, change:

```
Dialogue rejects an invalid handoff block but continues its normal pipeline (gatherers, briefing assembly, delegation).
```

to:

```
Dialogue rejects an invalid handoff block but continues its normal pipeline — see [pipeline-integration.md](pipeline-integration.md) for stage-level detail.
```

- [ ] **Step 2: Remove P0 enforcement characterization from foundations.md (AA-5)**

In `foundations.md` §Versioning and Drift Detection, change:

```
Contract→stub drift is bidirectional and is a P0 prerequisite check.
```

to:

```
Contract→stub drift is bidirectional. See [governance.md](governance.md#contract-stub-bidirectional-review-gate) for review gate procedures and [delivery.md](delivery.md#open-items) item #8 for the interim manual protocol.
```

- [ ] **Step 3: Verify cross-references**

Confirm the new governance.md anchor `#contract-stub-bidirectional-review-gate` matches the heading created in Task 6 Step 1. Read `governance.md` and verify.

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/specs/skill-composability/capsule-contracts.md docs/superpowers/specs/skill-composability/foundations.md
git commit -m "fix(spec): authority boundary fixes — pipeline scope + P0 characterization (AA-4, AA-5)"
```

---

### Task 11: Final verification pass

**Files:**
- Read: all 10 spec files

- [ ] **Step 1: Verify all cross-references resolve**

Run a grep for all internal links and verify anchors exist:

```bash
grep -oP '\[.*?\]\(([^)]+)\)' docs/superpowers/specs/skill-composability/*.md | grep '#' | sort -u
```

For each anchor reference, confirm the target heading exists in the referenced file.

- [ ] **Step 2: Verify all count claims match**

Re-run the count verification from Task 1 Step 7 to confirm no new mismatches were introduced.

- [ ] **Step 3: Verify spec.yaml consistency**

Confirm `spec.yaml` authority labels, claims, and boundary rules are still consistent with all file frontmatter and content. No spec.yaml changes were made, so this is a no-change confirmation.

- [ ] **Step 4: Verify finding coverage**

Cross-reference the 47 canonical findings from `.review-workspace/synthesis/report.md` against the 10 tasks above. Confirm every finding is addressed by at least one task step. Expected mapping:

| Task | Findings Addressed |
|------|-------------------|
| 1 | CC-1, CC-2, CC-3, CC-4, CC-5, CC-6 |
| 2 | CC-7, CC-8, AA-6, IE-14 |
| 3 | VR-4 |
| 4 | SY-1 (CE-9+VR-11+IE-7), VR-10, CE-6 |
| 5 | SY-3 (CE-2+IE-5), SY-4 (CE-7+VR-6) |
| 6 | AA-1, AA-2, AA-3 |
| 7 | SY-2 (IE-8, IE-9, IE-10) |
| 8 | VR-1, VR-2, VR-3, VR-5, VR-7, VR-8, VR-9, VR-12 |
| 9 | IE-1, IE-2, IE-3, IE-4, IE-6, IE-11, IE-13, CE-1, CE-3, CE-4, CE-5, CE-8, SY-5/IE-12 |
| 10 | AA-4, AA-5 |

- [ ] **Step 5: Final commit (if any fixes needed)**

```bash
git add docs/superpowers/specs/skill-composability/
git commit -m "fix(spec): final cross-reference verification pass"
```
