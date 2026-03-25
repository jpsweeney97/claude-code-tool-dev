# CCDI Spec P0 Remediation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix all 5 P0 findings from the CCDI spec review to eliminate ambiguous/contradictory normative claims and add missing test specifications.

**Architecture:** All changes are spec-level edits to markdown files in `docs/superpowers/specs/ccdi/`. No code changes. Each task produces a self-contained, independently verifiable edit.

**Tech Stack:** Markdown (spec files)

**Source:** Review report at `.review-workspace/synthesis/report.md`. Raw findings at `.review-workspace/findings/`.

---

## File Map

| File | Changes | Tasks |
|------|---------|-------|
| `docs/superpowers/specs/ccdi/registry.md` | Add `extends_topic` re-entry trigger to Suppression Re-Entry table | Task 1 |
| `docs/superpowers/specs/ccdi/classifier.md` | Remove semantic hint row from Injection Thresholds table; add cross-reference note | Task 2 |
| `docs/superpowers/specs/ccdi/packets.md` | Replace untestable "rhetorically dominant" claim with verifiable placement rule | Task 3 |
| `docs/superpowers/specs/ccdi/foundations.md` | Add design note elaborating "premise enrichment" with content-style guidance | Task 3 |
| `docs/superpowers/specs/ccdi/delivery.md` | Add 2 registry test entries for injection threshold boundary cases | Task 4 |

---

### Task 1: Reconcile `extends_topic` + `suppressed` re-entry contradiction (SY-12)

**Finding:** `registry.md` has two incompatible contracts for `extends_topic` on a `suppressed` topic:
- Semantic Hints table (line 152): "Re-enter as `detected`"
- Suppression Re-Entry table (lines 92-95): requires `docs_epoch` change OR new facet request — `extends_topic` satisfies neither

**Files:**
- Modify: `docs/superpowers/specs/ccdi/registry.md:92-95`

**Decision:** The Semantic Hints table is correct — `extends_topic` is explicitly designed to override weak-results suppression (it provides new signal). The Suppression Re-Entry table is incomplete — it needs `extends_topic` as a third trigger.

- [ ] **Step 1: Verify the defect**

Read `registry.md` lines 88-96 (Suppression Re-Entry) and lines 144-155 (Semantic Hints scheduling effects). Confirm:
- Line 152: `extends_topic | suppressed | Re-enter as detected`
- Lines 92-95: `weak_results` re-entry requires only `docs_epoch` change OR new facet — no mention of semantic hints

- [ ] **Step 2: Add `extends_topic` hint as third re-entry trigger**

In `registry.md`, replace the Suppression Re-Entry table (lines 92-95):

```markdown
| `suppression_reason` | Re-entry trigger |
|---------------------|-----------------|
| `weak_results` | `docs_epoch` changes (index updated) OR a new query facet is requested for the topic OR an `extends_topic` semantic hint resolves to the suppressed topic (see [Semantic Hints](#semantic-hints)) |
| `redundant` | Coverage state changes — e.g., an injected facet is later identified as insufficient, or a new leaf variant appears under the same family |
```

The only change is adding `OR an extends_topic semantic hint resolves to the suppressed topic (see [Semantic Hints](#semantic-hints))` to the `weak_results` row.

- [ ] **Step 3: Verify consistency**

Read both sections again. Confirm:
1. Semantic Hints table line 152 (`extends_topic | suppressed | Re-enter as detected`) is now consistent with the Suppression Re-Entry table
2. The `#semantic-hints` anchor resolves within registry.md
3. No other section of registry.md references suppression re-entry conditions that would conflict

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/specs/ccdi/registry.md
git commit -m "fix(ccdi): reconcile extends_topic suppression re-entry contradiction

Add extends_topic semantic hint as third re-entry trigger for
weak_results suppression in registry.md Suppression Re-Entry table.
Resolves self-contradiction between Semantic Hints table (line 152)
and Suppression Re-Entry table (lines 92-95).

Fixes: SY-12 (CE-1) — P0"
```

---

### Task 2: Remove semantic hint trigger from classifier injection thresholds (SY-9)

**Finding:** `classifier.md` Injection Thresholds table (line 76) includes "OR agent provides semantic hint" as a mid-dialogue trigger. But semantic hints bypass the classifier entirely — they are processed by `dialogue-turn` CLI via `--semantic-hints-file`. The classifier's `ClassifierResult` has no hint-related field. This creates a false single-gating model.

**Files:**
- Modify: `docs/superpowers/specs/ccdi/classifier.md:76-79`

- [ ] **Step 1: Verify the defect**

Read `classifier.md` lines 69-80. Confirm:
- Line 76: mid-dialogue row includes "OR agent provides semantic hint (see registry.md#semantic-hints)"
- The `ClassifierResult` output structure (lines 54-67) has no field for semantic hints
- The `Config keys` column for the mid-dialogue row has no key for the hint trigger

- [ ] **Step 2: Remove semantic hint from table and add cross-reference note**

In `classifier.md`, replace lines 76-79:

Old:
```markdown
| Mid-dialogue | 1 high-confidence uncovered leaf, OR 1 medium-confidence leaf in 2+ consecutive turns, OR agent provides semantic hint (see [registry.md](registry.md#semantic-hints)) | `mid_turn_consecutive_medium_turns` |
| `/codex` (CCDI-lite) | Same as initial | *(same keys)* |

Low-confidence detections are recorded in the [topic registry](registry.md) but never trigger injection alone.
```

New:
```markdown
| Mid-dialogue | 1 high-confidence uncovered leaf, OR 1 medium-confidence leaf in 2+ consecutive turns | `mid_turn_consecutive_medium_turns` |
| `/codex` (CCDI-lite) | Same as initial | *(same keys)* |

Semantic hints (see [registry.md#semantic-hints](registry.md#semantic-hints)) are an additional mid-dialogue injection trigger processed by the scheduling layer, independent of classifier output. The classifier does not process or output semantic hints.

Low-confidence detections are recorded in the [topic registry](registry.md) but never trigger injection alone.
```

- [ ] **Step 3: Verify consistency**

Confirm:
1. The mid-dialogue row now only lists classifier-owned triggers
2. The new paragraph cross-references `registry.md#semantic-hints` (anchor exists)
3. `registry.md` Semantic Hints section (lines 122-155) remains consistent — it already defines hint processing as a `dialogue-turn` CLI input
4. The Injection Thresholds section heading and intro (lines 69-71) still accurately describe the table's scope

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/specs/ccdi/classifier.md
git commit -m "fix(ccdi): remove semantic hint trigger from classifier injection thresholds

Semantic hints bypass the classifier entirely — they are processed
by dialogue-turn CLI via --semantic-hints-file. The classifier's
ClassifierResult has no hint-related field. Moved to a cross-reference
note below the table pointing to registry.md#semantic-hints.

Fixes: SY-9 (AA-2) — P0"
```

---

### Task 3: Split source hierarchy claim into verifiable and design-note parts (SY-6)

**Finding:** `packets.md` line 53 makes a normative `behavior_contract` claim ("must not produce rhetorically dominant content") that has no operational definition. No test or shadow mode kill criterion can verify "rhetorically dominant." The verifiable sub-claim (CCDI placed under `## Material`, source-separated by citation format) is testable.

**Files:**
- Modify: `docs/superpowers/specs/ccdi/packets.md:53`
- Modify: `docs/superpowers/specs/ccdi/foundations.md:40`

- [ ] **Step 1: Verify the defect**

Read `packets.md` line 53. Confirm: the sentence "The packet builder must not produce rhetorically dominant content that could override Codex's assessment of repo-specific code" is present and is a normative `behavior_contract` claim.

Read `delivery.md` shadow mode kill criteria (lines 23-29). Confirm: no kill criterion addresses source hierarchy inversion or rhetorical dominance.

Read `foundations.md` line 40. Confirm: "CCDI is premise enrichment, not retargeting" design principle exists.

- [ ] **Step 2: Replace packets.md source hierarchy paragraph**

In `packets.md`, replace line 53:

Old:
```markdown
**Source hierarchy:** CCDI packets are premise enrichment — they provide background knowledge, not primary evidence. When both CCDI docs content and repo evidence (`@ path:line`) address the same concept, repo evidence takes precedence. The packet builder must not produce rhetorically dominant content that could override Codex's assessment of repo-specific code.
```

New:
```markdown
**Source hierarchy:** CCDI packets are premise enrichment — they provide background knowledge, not primary evidence. When both CCDI docs content and repo evidence (`@ path:line`) address the same concept, repo evidence takes precedence. CCDI content is placed under `## Material` source-separated from repo evidence (`[ccdocs:...]` citations vs `@ path:line` citations). See [foundations.md#design-principles](foundations.md#design-principles) for the "premise enrichment, not retargeting" architectural constraint.
```

- [ ] **Step 3: Add design note to foundations.md**

In `foundations.md`, replace the design principles table row for "CCDI is premise enrichment" (line 40):

Old:
```markdown
| CCDI is premise enrichment, not retargeting | CCDI adds context to the follow-up prompt; it never changes what the agent asks Codex about |
```

New:
```markdown
| CCDI is premise enrichment, not retargeting | CCDI adds context to the follow-up prompt; it never changes what the agent asks Codex about. Packet content should provide background, not prescriptive directives — repo evidence is always the primary signal for Codex's assessment |
```

- [ ] **Step 4: Verify consistency**

Confirm:
1. `packets.md` source hierarchy now contains only operationally verifiable claims (placement, citation format)
2. `foundations.md#design-principles` anchor exists and contains the content-style guidance
3. The cross-reference from packets.md to foundations.md resolves
4. `delivery.md` shadow mode kill criteria (lines 23-29) are not affected — the removed claim had no kill criterion, and the retained claims are already covered by existing boundary contract tests

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/specs/ccdi/packets.md docs/superpowers/specs/ccdi/foundations.md
git commit -m "fix(ccdi): split source hierarchy claim into verifiable and design parts

Move untestable 'rhetorically dominant' normative claim from
packets.md (behavior_contract) to foundations.md (architecture_rule
design note). Keep verifiable sub-claim in packets.md: placement
under ## Material, source-separated by citation format.

Fixes: SY-6 (CE-10 + VR-3) — P0"
```

---

### Task 4: Add missing injection threshold boundary tests (SY-21 + SY-22)

**Finding:** Two normative prohibitions have no corresponding test specification:
- SY-21: "2+ medium-confidence in same family" has no negative boundary test (1 medium alone must NOT trigger)
- SY-22: "Low-confidence detections never trigger injection alone" has no test

**Files:**
- Modify: `docs/superpowers/specs/ccdi/delivery.md:161`

- [ ] **Step 1: Verify the defects**

Read `delivery.md` lines 127-161 (Registry Tests table). Confirm:
- No test for "1 medium-confidence topic alone → no injection candidates"
- No test for "low-confidence topic → detected state AND excluded from injection candidates"

Read `classifier.md` lines 73-79 (Injection Thresholds). Confirm the normative claims:
- "2+ medium-confidence in same family" (initial threshold)
- "Low-confidence detections are recorded in the topic registry but never trigger injection alone" (line 79)

- [ ] **Step 2: Add two test entries to Registry Tests table**

In `delivery.md`, after line 161 (the last entry in Registry Tests: `Malformed hints file | Invalid JSON → ignored with warning`), add before the `### Packet Builder Tests` heading:

```markdown
| Single medium-confidence → no initial injection | 1 medium-confidence topic (no same-family companion) → injection candidates empty; no CCDI packet built |
| Low-confidence topic → detected but never injected | Topic with `confidence: low` → enters `detected` state AND is excluded from `dialogue-turn` injection candidates output; no injection fires regardless of turn count |
```

- [ ] **Step 3: Verify consistency**

Confirm:
1. The new test entries reference concepts defined in `classifier.md` Injection Thresholds (lines 73-79)
2. The existing "Consecutive-turn medium threshold" test (line 150) covers the positive case; the new SY-21 test covers the negative boundary
3. The low-confidence test is distinct from "Generic token alone suppressed" (line 112 in Classifier Tests) — the classifier test verifies suppression at classification time; the registry test verifies scheduling exclusion
4. The table formatting (pipe separators, column alignment) matches existing rows

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/specs/ccdi/delivery.md
git commit -m "fix(ccdi): add injection threshold boundary tests to registry test spec

Add two missing test specifications:
- Single medium-confidence topic → no initial injection (negative boundary)
- Low-confidence topic → detected but excluded from candidates

Fixes: SY-21 (VR-1) + SY-22 (VR-2) — P0"
```

---

## Pre-Execution Checklist

- [ ] Create feature branch: `git checkout -b fix/ccdi-p0-remediation`
- [ ] Tasks 1-4 are independent — can be executed in any order or in parallel
- [ ] After all tasks: re-read all 5 modified files to verify no introduced inconsistencies
- [ ] Cross-reference check: verify all new `[anchor](file#anchor)` links resolve

## Dependencies

None between tasks. All 4 tasks modify different files (Task 3 modifies two files, neither of which is touched by other tasks). Safe for parallel execution.
