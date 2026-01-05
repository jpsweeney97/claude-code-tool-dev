# Framework for Improvement

A methodology for rigorous artifact transformation. Use when changes must be justified, complete, and auditable.

**Location:** `~/.claude/references/framework-for-improvement.md` (shared by improvement skills)

---

## When NOT to Use This Framework

**Skip this framework when:**

- Changes are trivial (typos, formatting)
- Time-critical fixes (apply now, validate later)
- "Better" cannot be defined for this artifact
- The artifact doesn't exist yet (use creation methodology)
- Overhead exceeds the value of rigor

**Use this framework when:**

- Improvement criteria are defined and enumerable
- Changes affect shared or published artifacts
- Fidelity to original intent matters
- Work will be reviewed or must be justified
- Mistakes would be costly to reverse

---

## Quick Reference

### Four Key Questions

1. **Before starting:** What exactly defines "better"?
2. **Per change:** Would this violate the artifact's identity?
3. **After changes:** Have I addressed all criteria across all scope?
4. **Before claiming done:** Can someone else verify and reproduce this?

### Four Dimensions

| Dimension | Core Question |
|-----------|---------------|
| **Fidelity** | Is essential meaning/intent preserved? |
| **Validity** | Are changes justified by defined criteria? |
| **Completeness** | Are all relevant improvements made or acknowledged? |
| **Verifiability** | Is improvement demonstrable and transparent? |

---

## Core Concepts

### Three Phases

Improvement fails in distinct phases. Each phase has independent failure modes.

| Phase | Question | Failure Mode |
|-------|----------|--------------|
| **Definition** | Is "better" well-defined? | Vague criteria, missed invariants |
| **Execution** | Are changes rigorous? | Unjustified changes, identity loss |
| **Verification** | Can others audit? | Undocumented process, untraceable rationale |

### Elements by Phase

| Phase | Elements |
|-------|----------|
| Definition | Scope, Criteria, Invariants, Dependencies, Proportionality |
| Execution | Fidelity (4), Validity (2), Completeness (3) |
| Verification | Observable, Explainable, Reproducible |

**Total:** 17 elements across 3 phases

---

## Calibration

Match rigor to stakes. Light calibration done well beats full calibration done poorly.

### Stakes Assessment

| Factor | Low (1) | Medium (2) | High (3) |
|--------|---------|------------|----------|
| **Reversibility** | Easy to undo | Moderate effort | Permanent |
| **Blast radius** | Affects only me | Affects team | Affects users/org |
| **Fidelity risk** | Identity safe | Some tension | Core identity at stake |
| **Visibility** | Internal | Shared | Public/published |

**Score 4:** Micro | **Score 5-6:** Light | **Score 7-9:** Standard | **Score 10-12:** Full

### Calibration Levels

| Level | When | Application |
|-------|------|-------------|
| **Skip** | Trivial changes | Direct edit |
| **Micro** | Single criterion, single invariant | One criterion + one invariant + execute |
| **Light** | Low stakes, clear criteria | Key Definition + key Execution checks |
| **Standard** | Moderate stakes | Full Definition + systematic Execution |
| **Full** | High stakes, precedent-setting | Complete framework + independent verification |
| **Deferred** | Emergency | Fix now, validate afterward |

**Default:** When uncertain, choose more rigor. Under-rigor fails silently.

---

## Three Phases

### Phase 1: Definition

Establish what "better" means before touching the artifact.

| Element | Question | Output |
|---------|----------|--------|
| **Scope** | What exactly are we improving, and where does it end? | Boundaries stated; exclusions explicit |
| **Criteria** | What standards/goals define "better"? | Enumerable criteria with sources |
| **Invariants** | What must NOT change? | Protected elements; tension with criteria surfaced |

**Common invariants to check:**
- **Technical accuracy:** Facts, code behavior, API contracts
- **Authorial voice:** Distinctive style, perspective, personality
- **Structural promises:** Headings readers navigate by, numbered lists referenced elsewhere
- **External references:** Links, citations, cross-references

| **Dependencies** | What external factors affect this? | What depends on it; what it depends on |
| **Proportionality** | Is improvement warranted? | Proceed / Reduce scope / Stop |

**Red flag:** "Make it better" with no enumerable criteria.

**Gate:** Definition can conclude "no improvement needed" — that's a valid outcome.

### Phase 2: Execution

Transform the artifact rigorously. Fidelity constrains Validity constrains Completeness.

#### Fidelity (Hard Constraint)

Changes that violate identity are forbidden.

| Component | Question | When Essential |
|-----------|----------|----------------|
| **Intent** | Does this alter what the artifact is for? | Always |
| **Content** | Does this change the facts/meaning? | When chosen, not arbitrary |
| **Expression** | Does this destroy voice/style? | When distinguishing |
| **Coherence** | Does this break connections between parts? | When structure is meaningful |

**Unifying test:** Would changing this make someone say "this isn't really the same artifact anymore"?

#### Validity

Each change must pass both checks.

| Principle | Question | Failure Signal |
|-----------|----------|----------------|
| **Grounded** | Which criterion justifies this? | "It seemed better" without criterion |
| **Applicable** | Does this case meet criterion's conditions? | Applying rule to wrong case |

**Note:** "Excess change" is a Grounded failure — the excess has no criterion. Correctness of transformation is implied by the change itself.

#### Completeness (Post-Change)

Check after all changes are made.

| Principle | Question | Failure Signal |
|-----------|----------|----------------|
| **Criteria coverage** | Was each criterion applied where relevant? | Criteria with no applications |
| **Scope coverage** | Was the entire artifact examined? | "Focused on main parts" without documenting skips |
| **Gap acknowledgment** | Are unaddressed issues documented? | No gaps listed for non-trivial work |

**Red flag:** Claiming completeness without coverage audit.

#### When Dimensions Conflict

The constraint chain (Fidelity > Validity > Completeness) establishes priority, but conflicts need resolution heuristics.

| Conflict | Resolution |
|----------|------------|
| **Fidelity vs Criteria** | If applying a criterion would violate identity, the criterion doesn't apply to this artifact. Document and skip. |
| **Criteria vs Criteria** | Apply the more specific criterion. If equal specificity, apply the criterion with clearer evidence of applicability. |
| **Completeness vs Time** | Partial coverage with explicit gaps beats abandoned coverage. Document what was skipped and why. |

**Principle:** Conflicts are surfaced, not hidden. The resolution becomes part of the audit trail.

### Phase 3: Verification

Enable retroactive audit of all phases.

| Component | Question | Output |
|-----------|----------|--------|
| **Observable** | Can someone see what was done? | Before/after available; changes enumerable |
| **Explainable** | Can someone understand why? | Rationale for each change or cluster |
| **Reproducible** | Could someone follow the same process? | Criteria source + methodology documented |

**Red flag:** "Trust me, it's better" without showing transformation.

---

## Phase Checklists by Calibration

### Phase 1: Definition

| Check | Micro | Light | Standard | Full |
|-------|-------|-------|----------|------|
| Scope defined | Implicit | Key boundaries | Complete | Exhaustive |
| Criteria enumerated | One | Main criteria | All criteria | All + prioritized |
| Invariants surfaced | One | Key only | All | All + tested against criteria |
| Dependencies mapped | — | Key | Complete | Complete + impact assessed |
| Proportionality assessed | — | Implicit OK | Explicit | Explicit + documented |

### Phase 2: Execution

| Check | Micro | Light | Standard | Full |
|-------|-------|-------|----------|------|
| Fidelity verified | Gut-check | Per change | Per change + spot check | Per change + full audit |
| Validity checked | Per change | Main changes | All changes | All + documented |
| Criteria coverage | — | Key criteria | All criteria | All + verified |
| Scope coverage | — | — | Documented | Verified |
| Gaps acknowledged | — | — | Yes | Comprehensive |

### Phase 3: Verification

| Check | Micro | Light | Standard | Full |
|-------|-------|-------|----------|------|
| Before/after visible | — | Diff available | Diff + summary | Full comparison |
| Rationale documented | — | Key decisions | Per change | Per change + criterion mapping |
| Process documented | — | — | Key decisions | Full methodology |

---

## Criteria Sourcing

Improvement requires defined criteria. Common sources:

| Source | Example | Trust |
|--------|---------|-------|
| **Established standards** | Strunk's rules, CWE Top 25 | High |
| **Domain conventions** | PEP 8, refactoring catalogs | High |
| **Explicit goals** | "Make more concise," "Reduce attack surface" | Medium |
| **Comparative reference** | "Match the quality of X" | Medium |
| **Purpose definition** | "Communicate Y to audience Z" | Low (needs elaboration) |

**Rule:** Prefer enumerable, external criteria. Verify subjective criteria are explicit.

---

## Red Flags: Seven Most Dangerous Failures

| Rank | Failure | Why Dangerous |
|------|---------|---------------|
| 1 | **Criteria-free improvement** | "Better" undefined; changes are arbitrary |
| 2 | **Fidelity erosion** | Identity destroyed while "following rules" |
| 3 | **Convenience-driven scope** | Improved easy parts, skipped hard ones |
| 4 | **Grounding theater** | Citations exist but don't justify changes |
| 5 | **Coverage confusion** | "Felt done" without checking coverage |
| 6 | **Proportionality bypass** | Proceeded without assessing worth |
| 7 | **Reconstructed documentation** | Rationale invented after the fact |

**If you notice any of these:** Stop. Reassess. Correct before continuing.

---

## Limitations

This framework has boundaries. Know them.

### Fundamental Limits

| Limit | Implication |
|-------|-------------|
| **Criteria-dependent** | Cannot function without defined criteria |
| **Transformation-assumed** | Creation needs reframing as "empty to populated" |
| **Content-optimized** | Expression/Coherence tuned for content artifacts |
| **Valid not optimal** | Ensures rigor, not best outcome |

### Scope Limits

| Not For | Why | Use Instead |
|---------|-----|-------------|
| Trivial changes | Overhead exceeds value | Direct edit |
| Emergency fixes | Time-critical | Fix now, validate later |
| Undefined "better" | No criteria possible | Don't call it improvement |
| Pure creation | No artifact to transform | Creation methodology |

### What This Framework Cannot Catch

| Failure | Why Not Caught | Mitigation |
|---------|----------------|------------|
| **Wrong criteria** | Applies, doesn't validate | Vet criteria sources |
| **Criteria conflicts** | Surfaces, doesn't resolve | Explicit prioritization |
| **Suboptimal choice** | Valid isn't optimal | Add optimization criteria |
| **Tacit knowledge gaps** | Can't document all expertise | Acknowledge in gaps |

---

## Failure Modes

How the framework breaks in practice.

| Mode | Warning Signs | Fix |
|------|---------------|-----|
| **Premature Definition lock** | Discovered invariant mid-Execution | Return; resurface; reassess |
| **Fidelity creep** | Aggregate changes altered identity | Periodic identity check |
| **Completeness theater** | All cells checked, findings thin | Honest self-assessment |
| **Documentation debt** | Notes written in bulk at end | Document as you go |
| **Calibration drift** | Stakes rose, rigor didn't | Reassess at checkpoints |
| **Framework as shield** | "I followed the process" defends bad work | Framework is means, not end |

---

## The Checkpoint

Before claiming improvement is complete, answer:

> **Can I point to each criterion, show where it was applied, and demonstrate the artifact's identity is preserved?**

If no: continue Definition or Execution.
If yes: proceed with Verification artifacts.

---

## This Framework's Improvement Criteria

This document was improved using its own methodology.

| Criterion | Source | Application |
|-----------|--------|-------------|
| **Actionability** | Pragmatic assessment | Added worked example, invariant heuristics, conflict resolution |
| **Proportionality** | Cost/benefit analysis | Added Micro calibration, reduced Light verification burden |
| **Cognitive load** | Usability research | Simplified Validity from 3 to 2 checks |

**Invariant:** Framework identity (four dimensions, three phases, stakes-based calibration)

**Fidelity check:** Same core structure? Yes. Same purpose? Yes. Same rigor philosophy? Yes.

---

## Derivation

This framework was systematically derived through a 10-step process:

1. Define "improvement" precisely
2. Identify first principles per dimension
3. Derive framework structure from principles
4. Map dependencies between elements
5. Validate completeness and minimality
6. Operationalize each element
7. Self-apply the framework
8. External validation (domain transfer)
9. Document limitations and failure modes
10. Practical validation across domains

For full derivation, rationale, and detailed operationalization, see:
`docs/plans/2026-01-01-framework-for-improvement-development.md`

---

## Compact Checklist

```
DEFINITION (before touching artifact)
[ ] Scope: What exactly? Where does it end?
[ ] Criteria: What standards define "better"? (enumerated, sourced)
[ ] Invariants: What must NOT change? (tension surfaced?)
[ ] Dependencies: What affects/is affected?
[ ] Proportionality: Worth it? (Proceed / Reduce / Stop)

EXECUTION (per change)
    FIDELITY (hard constraint)
    [ ] Intent preserved?
    [ ] Content preserved?
    [ ] Expression preserved? (when distinguishing)
    [ ] Coherence preserved?

    VALIDITY
    [ ] Grounded: Which criterion?
    [ ] Applicable: Criterion fits here?

COMPLETENESS (after all changes)
[ ] Criteria coverage: Each criterion applied where relevant?
[ ] Scope coverage: All parts examined?
[ ] Gap acknowledgment: Issues documented?

VERIFICATION (enable audit)
[ ] Observable: Before/after visible?
[ ] Explainable: Rationale documented?
[ ] Reproducible: Process documented?
```

---

## Worked Example: Light Calibration

Applying the framework to a documentation paragraph.

### Before

> The system processes data by first validating it, then it transforms the data into the required format, and finally the data is stored in the database. This process is very important for ensuring data integrity.

### Definition (30 seconds)

- **Scope:** This paragraph only
- **Criteria:** Strunk's Rules 11 (active voice), 13 (omit needless words), 17 (omit needless words)
- **Invariant:** Technical accuracy (three-step process: validate → transform → store)
- **Proportionality:** Low stakes, clear criteria → Light calibration

### Transformation

> The system validates incoming data, transforms it to the required format, and stores it in the database. This process ensures data integrity.

### Verification

| Change | Criterion | Fidelity Check |
|--------|-----------|----------------|
| "processes data by first validating it" → "validates incoming data" | Rule 11 (active voice) | ✓ Same meaning |
| "then it transforms the data" → "transforms it" | Rule 13 (omit needless words) | ✓ Same meaning |
| "and finally the data is stored" → "and stores it" | Rule 11 (active voice) | ✓ Same meaning |
| "is very important for ensuring" → "ensures" | Rule 17 (omit needless words) | ✓ Same meaning |

**Fidelity gut-check:** Still describes the same three-step process? Yes. Still the same paragraph? Yes.

**Coverage:** All criteria applied. No gaps.

---

## Usage

**To apply this framework:**

1. Check "When NOT to Use" — skip if criteria met
2. Assess stakes — choose calibration level
3. Complete Definition phase — establish criteria, invariants, scope
4. Execute with Fidelity constraint — check each change
5. Verify Completeness — coverage and gaps
6. Document for Verification — enable audit
7. State limitations — be honest about what you didn't cover

**The framework helps you transform rigorously. It cannot tell you what "better" means.**

---

## Skills Using This Framework

- `writing-clearly-and-concisely` — Apply Strunk's style rules rigorously
- `markdown-formatter` — Normalize markdown structure with lossless guarantee

### Roadmap

- `code-improvement` — Systematic code quality improvements (planned)
- `security-hardening` — Security posture improvements (planned)
- Improvement skill template (planned)

---

## Relationship to Framework for Rigor

| Aspect | Framework for Rigor | Framework for Improvement |
|--------|---------------------|---------------------------|
| Work type | Analysis | Transformation |
| Core question | Did I reason well? | Did I transform well? |
| Prerequisite | Scope to investigate | Criteria for "better" |
| Blind spot | Right questions? | Right criteria? |
| Phases | Definition, Execution, Verification | Definition, Execution, Verification |

Both frameworks share the same arc but serve different work types. Use Rigor for investigation; use Improvement for transformation.
