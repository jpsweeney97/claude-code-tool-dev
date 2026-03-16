# Synthesis Guidance Reference

Operational guidance for Phase 5 (SYNTHESIS). Contains worked examples, edge cases, and anti-patterns. This is Technique-level content — one valid approach the lead can adapt, not a normative procedure. The obligations and invariants in SKILL.md are normative; this file is not.

---

## Section 1: Consolidation and Deduplication

### When to merge: same defect, different vocabulary

Two findings that describe the same defect often arrive with different terminology because each reviewer uses their lens's vocabulary.

**Raw inputs:**

```
AA-2 (authority-architecture):
- priority: P1
- violated_invariant: foundations.md#authority-boundaries
- affected_surface: architecture/decisions.md §"Schema Constraints"
- evidence: "§'Schema Constraints' declares that field X must not be null. Binding
  schema rules belong in the normative data contract, not in a non-normative ADR."
- provenance: independent

CE-4 (contracts-enforcement):
- priority: P1
- violated_invariant: data-contract.md#constraint-ownership
- affected_surface: architecture/decisions.md §"Schema Constraints"
- evidence: "data-contract.md references architecture/decisions.md as the source
  of the null constraint on field X. This creates a normative dependency on a
  non-normative file."
```

**Merge decision:** Same `affected_surface` (`architecture/decisions.md §"Schema Constraints"`). Do the violated invariants point to the same root cause? AA-2 says the constraint is misplaced; CE-4 says the contract is referencing the misplaced content. Different defect classes (authority placement vs. contract enforcement) — but the root cause is one: a binding schema constraint lives in the wrong file. Merge.

**Ledger record:**

```markdown
### [SY-1] Authority misplacement: binding schema constraint in non-normative ADR

- **source_findings:** AA-2, CE-4
- **support_type:** cross_lens_followup_confirmation
- **contributors:** authority-architecture, contracts-enforcement
- **merge_rationale:** "AA-2 identified the misplacement. CE-4 confirmed the data
  contract references the misplaced authority. Different defect classes (authority
  placement vs. contract enforcement) but single root cause — the constraint
  belongs in data-contract.md."
- **adjudication_rationale:** N/A (no contradiction)
```

### When NOT to merge: similar surface, different root cause

```
AA-3 (authority-architecture):
- affected_surface: foundations.md §"Core Invariants", lines 45-52
- violated_invariant: meta.md#invariant-placement
- evidence: "Two behavioral constraints in §'Core Invariants' make implementation
  decisions that belong in the design spec, not the foundational spec."

VR-2 (verification-regression):
- affected_surface: foundations.md §"Core Invariants", lines 45-52
- violated_invariant: test-plan.md#invariant-coverage
- evidence: "Both constraints in lines 45-52 are untested. No test plan entry
  covers either invariant."
```

**Merge decision:** Same `affected_surface`. Different `violated_invariant` — one is an authority placement error (wrong file for an implementation decision), the other is a coverage gap (the invariants exist but are untested). These are distinct defects: fixing AA-3 by moving the constraints doesn't fix VR-2's test gap. Do NOT merge. Keep as separate ledger records. Note the surface overlap in `priority_rationale` if it affects ranking.

---

## Section 2: Corroboration Assessment

### independent_convergence

Both contributors found the defect independently, without peer messages influencing either investigation.

**Example:**

AA-3 (`provenance: independent`) finds that `foundations.md:45-52` contains two invariants that have drifted from their declared authority source. CE-7 (`provenance: independent`) finds that those same invariants are referenced in a contract file, but the contract version differs from the foundational version.

Both arrived at the same surface — `foundations.md:45-52` — through separate defect-class lenses with no DM traffic between them. This is `independent_convergence`: the strongest corroboration signal, because neither finding was seeded by the other.

**Ledger entry:**

```
- **support_type:** independent_convergence
- **contributors:** authority-architecture, contracts-enforcement
```

### cross_lens_followup_confirmation

One reviewer flagged a finding; another confirmed a related (but distinct) defect at the same surface after receiving a peer message.

**Example:**

AA-2 sends a targeted message to `contracts-enforcement`: "Found authority misplacement in architecture/decisions.md §'Schema Constraints' — you may want to check if your contracts reference this section." CE-4 investigates and confirms: the data contract does reference that section, creating a normative dependency on a non-normative file. CE-4 records `provenance: followup, prompted_by: authority-architecture`.

This is `cross_lens_followup_confirmation`. CE-4's finding is real and adds the "downstream contract" dimension that AA-2 could not see through its lens. The confirmation strengthens confidence but does not count as independent convergence — the investigation was prompted.

### related_pattern_extension

Distinct findings at the same surface that reveal a larger pattern of the same maintenance failure.

**Example:**

CC-1 (`completeness-coherence`) finds a count mismatch: the spec introduction says there are "four core invariants" but only three are defined in `foundations.md`. VR-2 (`verification-regression`) finds that one of the three defined invariants has a test plan entry that references a constraint no longer present in the spec. CC-1 is a count/coherence defect; VR-2 is a regression/coverage defect. Neither prompted the other (`provenance: independent` for both).

The shared pattern: `foundations.md §"Core Invariants"` is under-maintained — count, content, and test coverage have all drifted. These are not the same defect (do not merge), but they belong in the same pattern cluster. Record `support_type: related_pattern_extension` and surface the cluster in the report's corroboration table.

### singleton

A single-lens finding with no corroboration from other reviewers.

**Example:** AA-5 finds that a governance rule is stated in `architecture/principles.md` but never enforced in the enforcement-surface files. No other reviewer mentions this section.

Singletons can still be P0. Corroboration affects confidence, not priority. Note singleton status in the report so readers understand the confidence basis.

---

## Section 3: Contradiction Resolution

### Worked contradiction example

**Conflicting findings:**

```
AA-2 (authority-architecture):
- priority: P1
- evidence: "§'Validation Rules' in design-spec.md makes a binding decision about
  field ordering. Binding decisions belong in the normative spec, not the design doc."
- confidence: high

CC-3 (completeness-coherence):
- priority: P2
- evidence: "§'Validation Rules' in design-spec.md is consistent with all
  cross-references. Every other file that references validation rules points here."
- confidence: medium
```

**Resolution:** The authority map shows `design-spec.md` has `normative: false`. AA-2's violated invariant (`meta.md#binding-decision-placement`) is a first-tier authority rule: binding decisions must live in normative files. CC-3's consistency observation does not override it — a non-normative file can be consistently referenced while still being the wrong location for a binding decision. Apply the authority map: normative > non-normative takes precedence when placement is in conflict.

**Ledger record:**

```markdown
### [SY-3] Binding validation rule in non-normative design spec

- **source_findings:** AA-2, CC-3
- **support_type:** singleton (AA-2); CC-3 does not corroborate, it contradicts
- **contributors:** authority-architecture, completeness-coherence
- **merge_rationale:** N/A (contradiction, not duplicate)
- **adjudication_rationale:** "Authority map: design-spec.md is non-normative.
  AA-2's violated_invariant (meta.md#binding-decision-placement) is a first-tier
  authority rule. CC-3's internal consistency observation does not override the
  placement requirement. AA-2 finding adopted. CC-3 observation noted as
  context — consistency of references is accurate but does not resolve authority."
```

### Edge cases

**Empty reviewer — no findings and no coverage notes.**
Do NOT treat as a clean bill of health. Record in `reviewers_failed`: "findings file present but contains neither findings nor coverage notes." This is a reviewer failure, not evidence of a defect-free surface.

**All-identical findings — 3 reviewers find the same issue.**
Merge into one ledger record with all three as `contributors`. Set `support_type: independent_convergence` if all three have `provenance: independent`. If one was a followup, the support type depends on the provenance chain of the merged set — use `cross_lens_followup_confirmation` if any contributor is a followup, since the convergence is partially seeded.

**Circular deferrals — AA defers to CE, CE defers back to AA.**
Neither deferral was resolved. Both become meta-findings in the ledger: one for the unresolved CE deferral, one for the unresolved AA deferral. Prefix `SY`, priority P1. Record under `unverified_deferrals` in audit metrics.

**Provenance ambiguity — reviewer received a message but was already independently investigating the same surface.**
Tag `provenance: independent`. The SKILL.md rule is: independent if found without a peer message. A message arriving after the investigation began does not retroactively change provenance. If genuinely uncertain (investigation timeline unclear), use `provenance: independent` and note the ambiguity in `merge_rationale`.

---

## Section 4: Anti-Patterns

**Conviction maximizing.** Merging two findings because they share a surface even when their `violated_invariant` and root cause differ. This inflates the `duplicate_clusters_merged` metric and produces a consolidated finding that is harder to act on than two specific ones. Check root cause before merging.

**Premature merging.** Consolidating before checking the provenance chain of each contributor. If you merge first and classify `support_type` second, you may misclassify a followup-seeded finding as `independent_convergence`. Establish provenance first, then merge.

**Ignoring provenance.** Treating all multi-reviewer findings as `independent_convergence` regardless of whether peer messages were involved. This overstates corroboration confidence for seeded findings. The provenance field exists for this reason — read it before classifying.

**Priority inflation.** Raising a finding from P1 to P0 because it is corroborated, without evidence that the impact warrants P0. Corroboration is a secondary tiebreaker, not a primary priority driver. The baseline is P0 > P1 > P2 by impact. Use `priority_rationale` when departing from the baseline — do not inflate silently.

**Silent contradiction dropping.** Choosing one side of a contradiction without recording `adjudication_rationale`. This violates Ledger Invariant 3. Every resolved contradiction needs a rationale; every unresolvable contradiction becomes a `SY` finding.

---

## Section 5: Precedence Resolution (Full Contract Mode)

When `spec.yaml` provides precedence rules, contradiction resolution follows a mechanical procedure instead of domain reasoning.

### Worked example: `claim_precedence` application

**Conflicting findings on the same surface:**

```
AA-2 (authority-architecture):
- claim_family: behavior_contract
- priority: P1
- affected_surface: config/validation.md §"Input Rules"
- evidence: "Config contract declares input validation rules that conflict
  with command contract's declared input handling."

CE-5 (contracts-enforcement):
- claim_family: behavior_contract
- priority: P1
- affected_surface: config/validation.md §"Input Rules"
- evidence: "Command contract's input handling contradicts config contract's
  validation rules at the same surface."
```

**Resolution steps:**

1. Both files are `normative: true` → normative_first does not resolve (tie).
2. Finding's `claim_family: behavior_contract` → check `claim_precedence.behavior_contract`.
3. `claim_precedence` lists: `[command-contract, config-contract, foundation, delivery, decisions]`.
4. AA-2 cites the config contract's perspective; CE-5 cites the command contract's perspective. The command contract is listed first → command contract's position wins.
5. Record `adjudication_rationale`: "Per claim_precedence for behavior_contract, command-contract takes precedence over config-contract."

**Ledger record:**

```markdown
### [SY-4] Config input validation conflicts with command input handling

- **source_findings:** AA-2, CE-5
- **support_type:** independent_convergence
- **contributors:** authority-architecture, contracts-enforcement
- **merge_rationale:** "Same surface (config/validation.md §Input Rules), same
  claim_family (behavior_contract), same root cause — conflicting validation rules."
- **adjudication_rationale:** "Per claim_precedence for behavior_contract,
  command-contract (position 1) takes precedence over config-contract (position 2).
  Config's validation rules should align with command's input handling."
```

### Worked example: fallback_authority_order

When a finding's `claim_family` has no `claim_precedence` entry, or the conflicting authorities are not listed in the applicable entry:

```
VR-3 (verification-regression):
- claim_family: verification_strategy
- affected_surface: delivery/testing.md §"Coverage Goals"
- evidence: "Delivery testing plan claims 90% coverage, but the foundation's
  architectural constraints make 90% infeasible for the async subsystem."
```

1. Check `claim_precedence.verification_strategy` → lists `[delivery, command-contract, config-contract, decisions]`.
2. Foundation is NOT in the list → fall through to `fallback_authority_order`.
3. `fallback_authority_order: [foundation, command-contract, ...]` → foundation is position 1, delivery is position 5.
4. Foundation wins. The architectural constraint overrides the delivery plan's coverage target.

### Worked example: ambiguity finding

When an authority appears in neither `claim_precedence` nor `fallback_authority_order`:

1. Neither resolution path produces a winner.
2. Emit ambiguity finding: prefix `SY`, priority P1.
3. `adjudication_rationale`: "Authority X not listed in claim_precedence for [claim] or fallback_authority_order. Escalating as ambiguity — human resolution required."

---

## Section 6: Boundary Coverage Analysis (Full Contract Mode)

When `spec.yaml` defines `boundary_rules`, synthesis verifies that coupled authorities received adequate cross-reviewer attention.

### Procedure

For each boundary rule:
1. Identify all findings whose `affected_surface` touches a file under any authority in `on_change_to`.
2. For each such finding, check whether at least one reviewer also examined files under each `review_authorities` authority for defects related to the boundary rule's `reason`.
3. Evidence sources: findings files (direct examination), coverage notes (explicit scope declarations), DM summaries (collaboration indicators).

### What counts as "examined"

- A finding whose `affected_surface` is under the review authority → examined.
- A coverage note listing the review authority's files in `scope_checked` → examined.
- A DM summary showing a reviewer discussed the boundary topic with another reviewer who examined it → examined (indirect).

### Unexamined boundary

When a `review_authorities` authority has no examination evidence:

```markdown
### [SY-N] Boundary coverage gap: [authority] not examined for [reason]

- **source_findings:** (none — this is a meta-finding)
- **support_type:** singleton
- **contributors:** synthesis-lead
- **priority:** P1
- **adjudication_rationale:** "Boundary rule requires examining [review_authority]
  when [on_change_to authority] is affected. No reviewer examined [review_authority]
  files for defects related to: [boundary rule reason]."
```

---

## Section 7: Exemplar Ledger Entry

A complete ledger record, all fields populated:

```markdown
### [SY-1] Authority misplacement: binding schema constraint in non-normative rationale file

- **source_findings:** AA-2, CE-4
- **support_type:** cross_lens_followup_confirmation
- **contributors:** authority-architecture, contracts-enforcement
- **merge_rationale:** "AA-2 identified the misplacement. CE-4 confirmed contracts
  reference the misplaced authority. Different defect classes (authority vs. contract
  enforcement) but same root cause — binding constraint in wrong file."
- **adjudication_rationale:** N/A (no contradiction)
- **priority_rationale:** "Ranked above CC-1 (same P1) because this boundary is
  the spec's primary normative source — misplacement here affects all downstream
  contracts that reference it."
```

**Field notes:**
- `source_findings` — IDs from reviewer findings files, not synthesized IDs.
- `support_type` — derived from provenance chains; do not guess.
- `contributors` — role IDs only; must match spawned reviewers.
- `merge_rationale` — required for any multi-source finding.
- `adjudication_rationale` — required when a contradiction was resolved; "N/A" only when no contradiction existed.
- `priority_rationale` — omit with "N/A" when ranking follows P0 > P1 > P2 baseline; write rationale only when departing from baseline.

---

## Section 8: Audit Metric Notes

SKILL.md defines all 10 required metrics. Two require synthesis-time attention:

- **`duplicate_clusters_merged`:** One merge of N findings = 1 cluster, regardless of N. Three reviewers reporting the same issue → 1 merge, `duplicate_clusters_merged` increments by 1.
- **`corroborated_findings`:** Counts ledger records with `independent_convergence` or `cross_lens_followup_confirmation`. Singletons and `related_pattern_extension` do not count toward this metric even when they appear alongside corroborated findings at the same surface.

All other metrics are counts or values carried forward from earlier phases — compute them during canonicalization and pass them to Phase 6 unchanged.
