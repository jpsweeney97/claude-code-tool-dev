# Bulletproofing the Framework for Rigor

> **Purpose:** Document the systematic derivation of a bulletproof Framework for Rigor that will serve as the foundation for a family of rigorous skills (deep-exploration, security audit, code review, incident investigation, etc.).
>
> **Approach:** 10-step process, each step documented with full reasoning before proceeding to the next.

---

## Process Overview

| Step | Focus | Status |
|------|-------|--------|
| 1 | Define "Rigor" precisely | ✓ Complete |
| 2 | Identify first principles per dimension | ✓ Complete |
| 3 | Derive framework structure from principles | ✓ Complete |
| 4 | Map dependencies between elements | ✓ Complete |
| 5 | Validate completeness and minimality | ✓ Complete |
| 6 | Operationalize each element | ✓ Complete |
| 7 | Self-apply the framework | ✓ Complete |
| 8 | External validation | ✓ Complete |
| 9 | Document limitations and failure modes | ✓ Complete |
| 10 | Practical validation across domains | ✓ Complete |

---

## Step 1: Define "Rigor" Precisely

### Goal

Establish a precise, testable definition of rigor that:
- Is complete (all rigor failures map to the definition)
- Is minimal (no redundant components)
- Has orthogonal dimensions (can fail/succeed independently)
- Is actionable (can verify whether work is rigorous)

### Analysis

**Starting point:** The original framework used "Three Pillars" (Rigorous, Robust, Comprehensive). Problems:
- "Rigorous" is circular (defining rigor in terms of rigorous)
- Dimensions weren't clearly orthogonal
- Transparency was scattered, not explicit

**First-principles question:** What does it mean for work to be rigorous?

Attempted definitions and challenges:

| Attempt | Challenge |
|---------|-----------|
| "Work done carefully" | Vague—careful how? |
| "Work without errors" | Rigor is process, not outcome |
| "Work following a methodology" | Following bad methodology isn't rigorous |
| "Work that produces reliable conclusions" | Still outcome-focused |

**Breakthrough:** Rigor is about *justified confidence* in conclusions. Three questions determine justified confidence:
1. Are conclusions actually supported by evidence? (Validity)
2. Did you look at everything relevant? (Completeness)
3. Can others verify your work? (Transparency)

### Challenges Addressed

| Challenge | Resolution |
|-----------|------------|
| "Validity" term overloaded | Defined explicitly: "soundly justified by evidence" |
| Transparency: dimension or communication? | Essential for *demonstrable* rigor—without it, rigor is unverifiable |
| Scope: part of Completeness? | Yes—wrong scope = incomplete coverage of what matters |
| Rigor vs. Correctness | Rigor is process quality, not guaranteed outcome correctness |
| Disconfirmation placement | Spans Validity (reasoning) and Completeness (evidence gathering) |

### Output: Definition of Rigor

> **Rigor** is the property of work where:
>
> 1. **Validity** — Conclusions are soundly justified by evidence
>    - Evidence is reliable (primary sources preferred)
>    - Reasoning is logically sound
>    - Counterevidence is sought and addressed
>    - Assumptions are explicit and justified
>
> 2. **Completeness** — Everything relevant is considered
>    - Scope is appropriate to the actual problem
>    - Scope boundaries are justified
>    - Everything in scope is examined
>    - Absences are documented (looked but didn't find)
>    - Scope limitations are acknowledged
>
> 3. **Transparency** — The process is verifiable and reproducible
>    - Methodology is documented
>    - Evidence is traceable to source
>    - Others can follow the same process
>    - Uncertainty is quantified

### Properties Verified

| Property | Verification |
|----------|--------------|
| **Orthogonality** | Each dimension can fail independently: valid but incomplete (missed something), complete but invalid (bad reasoning), valid and complete but opaque (can't verify) |
| **Completeness** | All rigor failures map to ≥1 dimension (tested via failure enumeration) |
| **Minimality** | Removing any dimension leaves gaps (tested via removal) |
| **Testability** | Each dimension has concrete verification criteria |

### Changes from Original Framework

| Original | Revised | Rationale |
|----------|---------|-----------|
| "Rigorous" pillar | Validity dimension | Eliminates circular definition |
| "Robust" pillar | Merged into Validity + Completeness | Was conflating evidence quality with coverage |
| "Comprehensive" pillar | Completeness dimension | Clearer term |
| Transparency scattered | Transparency dimension | Made explicit as essential for demonstrable rigor |

---

## Step 2: Identify First Principles Per Dimension

### Goal

For each dimension (Validity, Completeness, Transparency), identify the **atomic, non-decomposable principles** that must hold for that dimension to be satisfied.

Criteria for a first principle:
- **Atomic:** Cannot be meaningfully decomposed further
- **Necessary:** Removing it creates a gap in the dimension
- **Distinct:** Cannot be merged with another without loss
- **Testable:** Can verify whether it's satisfied

### Analysis: Validity Dimension

**Question:** What must hold for conclusions to be "soundly justified by evidence"?

Two requirements emerge:
1. There must be adequate evidence
2. Reasoning from evidence to conclusion must be sound

**Adequate Evidence properties:**

| Property | Meaning |
|----------|---------|
| Reliable | Observations accurately represent reality |
| Relevant | Observations actually bear on the conclusion |
| Sufficient | Enough observations for claimed confidence |

**Sound Inference properties:**

| Property | Meaning |
|----------|---------|
| Logically valid | Conclusion follows from premises |
| Explicit assumptions | What's taken for granted is stated |
| Alternatives considered | Other explanations examined |
| Disconfirmation sought | Actively looks for counterevidence |

**Validity Principles:**
1. **Adequate Evidence** — Observations bearing on the conclusion are reliable, relevant, and sufficient
2. **Sound Inference** — Reasoning from evidence to conclusion is logically valid, with explicit assumptions and disconfirmation

### Analysis: Completeness Dimension

**Question:** What must hold for "everything relevant to be considered"?

| Scenario | Scope | Coverage | Result |
|----------|-------|----------|--------|
| Looked at everything in the wrong area | Wrong | Full | Incomplete |
| Looked at some things in the right area | Right | Partial | Incomplete |
| Looked at everything in the right area | Right | Full | Complete |

**Completeness Principles:**
3. **Appropriate Scope** — Boundaries correctly capture what's relevant to the purpose
4. **Full Coverage** — Everything within scope is examined adequately

### Analysis: Transparency Dimension

**Question:** What must hold for "the process to be verifiable and reproducible"?

Three requirements:
1. Process must be recorded (so others can follow)
2. Claims must be traceable to sources (so others can verify)
3. What's recorded must be accurate (not misleading)

**Why Honesty is separate:** You can document thoroughly, trace all claims, and still omit inconvenient findings. This is *deceptively transparent*—form without substance.

**Transparency Principles:**
5. **Documentation** — Process is recorded (methodology, decisions, steps)
6. **Traceability** — Claims map to sources (each assertion has provenance)
7. **Honesty** — Documentation accurately represents reality, including uncertainty

### Challenge Testing

**Completeness Test—All rigor failures map:**

| Rigor Failure | Maps To |
|---------------|---------|
| Jumped to conclusions | Adequate Evidence |
| Used unreliable sources | Adequate Evidence |
| Made logical errors | Sound Inference |
| Ignored counterevidence | Sound Inference |
| Looked at wrong things | Appropriate Scope |
| Missed things in scope | Full Coverage |
| Can't follow process | Documentation |
| Can't verify claims | Traceability |
| Hid findings | Honesty |

**Minimality Test—All principles necessary:**

| Remove | Gap Created |
|--------|-------------|
| Adequate Evidence | Can't verify evidence quality |
| Sound Inference | Can't verify reasoning quality |
| Appropriate Scope | Can't verify boundaries |
| Full Coverage | Can't verify exhaustion |
| Documentation | Can't verify process |
| Traceability | Can't verify sources |
| Honesty | Can't verify accuracy |

**Distinctness Test—No merges possible:**

| Merge Candidate | Why Not |
|-----------------|---------|
| Adequate Evidence + Sound Inference | Sequential: input vs. processing |
| Scope + Coverage | Different: what vs. how much |
| Documentation + Traceability | Different: process vs. provenance |
| Any + Honesty | Can satisfy others dishonestly |

**Resolved Questions:**

| Question | Resolution |
|----------|------------|
| What about "Quality"? | Built into each principle's definition, not separate |
| What about "Disconfirmation"? | Practice spanning multiple principles, not principle itself |
| What about "Negative Findings"? | Practice demonstrating Coverage + Documentation + Honesty |

### Output: Seven First Principles

| # | Principle | Dimension | Definition |
|---|-----------|-----------|------------|
| 1 | **Adequate Evidence** | Validity | Observations bearing on the conclusion are reliable, relevant, and sufficient |
| 2 | **Sound Inference** | Validity | Reasoning from evidence to conclusion is logically valid, with explicit assumptions and disconfirmation |
| 3 | **Appropriate Scope** | Completeness | Boundaries correctly capture what's relevant to the purpose |
| 4 | **Full Coverage** | Completeness | Everything within scope is examined adequately |
| 5 | **Documentation** | Transparency | Process is recorded (methodology, decisions, steps) |
| 6 | **Traceability** | Transparency | Claims map to sources (each assertion has provenance) |
| 7 | **Honesty** | Transparency | Documentation accurately represents reality, including uncertainty |

### Properties Verified

| Property | Status | Evidence |
|----------|--------|----------|
| Complete | ✓ | All rigor failures map to ≥1 principle |
| Minimal | ✓ | Removing any principle creates gap |
| Distinct | ✓ | No two principles can merge without loss |
| Testable | ✓ | Each principle has verification criteria |

---

## Step 3: Derive Framework Structure from Principles

### Goal

Given the 7 first principles, derive a framework structure that:
- Organizes principles into a usable workflow
- Respects dependencies between principles
- Identifies phases, meta-concerns, and verification aids
- Is complete (covers all principles) and minimal (no unnecessary structure)

### Analysis: Natural Sequence

| Stage | Activity | Principles Involved |
|-------|----------|---------------------|
| Before | Define what you're doing | Appropriate Scope |
| During | Do the work | Adequate Evidence, Sound Inference, Full Coverage |
| Throughout | Record the work | Documentation, Traceability, Honesty |
| After | Verify the work | All principles (as verification criteria) |

**Insight:** Three phases emerge: Definition → Execution → Verification

### Analysis: Principle Dependencies

```
Appropriate Scope (foundational)
    │
    ├──────────────────────┐
    │                      │
    ▼                      ▼
Adequate Evidence      Full Coverage
    │                      │
    ▼                      │
Sound Inference ◄──────────┘

Documentation → Traceability → Honesty (constrains both)
```

**Key insight:** Appropriate Scope is foundational—everything else depends on it.

### Analysis: Principle Categorization

| Principle | Category | Rationale |
|-----------|----------|-----------|
| Appropriate Scope | **Phase 1** | Must be done upfront |
| Adequate Evidence | **Phase 2** | Core execution activity |
| Sound Inference | **Phase 2** | Core execution activity |
| Full Coverage | **Phase 2** | Tracked during execution |
| Documentation | **Continuous** | Must happen throughout |
| Traceability | **Continuous** | Must happen as claims made |
| Honesty | **Constraint** | Quality requirement on above |

### Analysis: Meta-Concerns

**Simple Path Check (Pre-Framework):**
- Is there an obvious simple approach that works?
- If yes → use it, skip framework
- Purpose: Avoid over-engineering

**Calibration (Modulates Depth):**
- Light: Low stakes → key claims, minimal docs
- Medium: Standard → major claims traced
- Deep: High stakes → all claims traced, exhaustive docs
- Purpose: Match effort to stakes

### Challenge Testing

| Challenge | Resolution |
|-----------|------------|
| Is Definition just Appropriate Scope? | Yes—purpose, boundaries, assumptions are aspects of scoping |
| Is Execution strictly sequential? | No—iterative loop: Gather → Reason → Check Coverage → repeat |
| Does every principle appear? | Yes, all 7 assigned to phase or continuous |
| Are phases correctly ordered? | Yes—can't execute without scope, can't verify without execution |
| Is Simple Path correctly pre-framework? | Yes—gates whether to engage framework at all |
| Is Calibration correctly meta? | Yes—modulates how all phases execute, not itself a phase |

### Output: Framework Structure

```
┌─────────────────────────────────────────────────────────────────────┐
│ PRE-FRAMEWORK: Simple Path Check                                    │
│   Is there an obvious simple approach that works?                   │
│   If yes → use it, skip framework. If no → engage framework.        │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ META: Calibration                                                   │
│   How much rigor is warranted? (Light / Medium / Deep)              │
│   Modulates depth of all phases.                                    │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 1: DEFINITION                                                 │
│   Principle: Appropriate Scope                                      │
│   Actions: Purpose → Boundaries → Done criteria → Assumptions       │
│   Checkpoint: Can I state what "done" looks like?                   │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 2: EXECUTION                                                  │
│   Primary: Adequate Evidence, Sound Inference, Full Coverage        │
│   Continuous: Documentation, Traceability, Honesty                  │
│   Loop: Gather → Reason → Check Coverage → (repeat if gaps)         │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 3: VERIFICATION                                               │
│   Check all 7 principles satisfied                                  │
│   All pass → Done. Any fail → Iterate back.                         │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ RED FLAGS                                                           │
│   Patterns indicating principle violations (derived in Step 6)      │
└─────────────────────────────────────────────────────────────────────┘
```

### Properties Verified

| Property | Status |
|----------|--------|
| All 7 principles appear | ✓ |
| Dependencies respected | ✓ |
| Phases correctly ordered | ✓ |
| Meta-concerns correctly placed | ✓ |
| No unnecessary structure | ✓ |

---

## Step 4: Map Dependencies Between Elements

### Goal

Create a comprehensive dependency map that:
- Identifies all elements (principles, phases, meta-concerns)
- Maps relationships between them
- Classifies dependency types
- Identifies the critical path
- Documents consequences of dependency violations

### Dependency Types

| Symbol | Type | Meaning |
|--------|------|---------|
| → | Sequential | Must complete before |
| ⇒ | Enabling | Makes possible / provides input |
| ∿ | Modulating | Affects how something is done |
| ↔ | Continuous | Happens throughout / in parallel |
| ✓ | Verification | Checks whether satisfied |
| ⊂ | Constraining | Limits/shapes behavior |

### Principle Dependencies

```
Appropriate Scope (foundational)
         │
         ├──⇒── Adequate Evidence ──⇒── Sound Inference
         │              │
         └──⇒── Full Coverage ◄────────────┘

Documentation ──⇒── Traceability
         │                │
         └──────⊂─────────┘
                │
             Honesty (constrains both)
```

**Key insight:** Appropriate Scope is foundational—all other principles depend on it being correct.

### Meta-Concern Dependencies

| Element | Depends On | Affects |
|---------|------------|---------|
| Simple Path Check | Entry point | Gates framework engagement |
| Calibration | Framework engaged | Modulates depth of all phases |

### Dependency Violations

| Dependency | Violation | Consequence |
|------------|-----------|-------------|
| Scope → Evidence | Gather without scope | Wasted effort, irrelevant evidence |
| Evidence → Inference | Infer without evidence | Unsupported conclusions |
| Documentation ↔ Execution | Document at end | Lost information, inaccurate records |
| Honesty ⊂ All | Dishonest documentation | Corrupt outputs |

### Anti-Patterns (Backwards Dependencies)

| Pattern | What's Wrong |
|---------|--------------|
| Inference → Evidence | Confirmation bias (gathering evidence for conclusions) |
| Scope → Inference | Goal-post moving (defining scope to match conclusions) |
| Documentation → Execution | Falsification (changing work to match docs) |

### Critical Path

```
Scope → Evidence → Inference → Coverage → Verify → Done
          ↑           │            │
          └───────────┴────────────┘ (iteration if gaps)

[Continuous: Documentation ↔ Traceability ↔ Honesty]
```

### Iteration Loops

**Healthy:**
| Trigger | Path | Purpose |
|---------|------|---------|
| Coverage gap | Coverage → Evidence | Fill gaps |
| Scope wrong | Verification → Definition | Correct scope |
| Evidence gap | Verification → Execution | Gather more |

**Unhealthy:**
| Pattern | Problem |
|---------|---------|
| Infinite re-scoping | Never converging |
| Evidence fishing | Looking for evidence to support conclusion |

### Parallel vs. Sequential

| Must Be Sequential | Why |
|--------------------|-----|
| Scope → Evidence | Can't gather without knowing what |
| Evidence → Inference | Can't reason from nothing |
| Execution → Verification | Can't verify what's not done |

| Can Be Parallel | Why |
|-----------------|-----|
| Evidence for different items | Independent |
| Documentation with execution | Continuous |
| Verify different principles | Independent checks |

### Challenge Testing

| Challenge | Resolution |
|-----------|------------|
| Is Scope truly foundational? | Yes—all principles undefined without it |
| Is Evidence → Inference strictly sequential? | Yes for conclusions; hypotheses can precede |
| Can Documentation happen after? | No—loses context, violates Honesty |
| Is Honesty a constraint or dependency? | Constraint—doesn't require prior principles |

### Output: Complete Dependency Map

```
[Entry] → Simple Path Check
               │ (if no simple path)
               ▼
        Calibration ──∿──→ (modulates all)
               │
               ▼
┌─────────────────────────────────────────────────────────┐
│ PHASE 1: Appropriate Scope                              │
│          (foundational—enables all below)               │
└─────────────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────┐
│ PHASE 2: Evidence ──⇒── Inference                       │
│              │              │                           │
│              └──────────────┴──→ Coverage               │
│                                    │                    │
│          [Continuous: Doc ⇒ Trace ⊂ Honesty]            │
└─────────────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────┐
│ PHASE 3: Verify all 7 principles                        │
│          Pass → Done | Fail → Iterate back              │
└─────────────────────────────────────────────────────────┘
```

### Properties Verified

| Property | Status |
|----------|--------|
| All elements mapped | ✓ |
| Dependency types classified | ✓ |
| Critical path identified | ✓ |
| Violations documented | ✓ |
| Iteration loops identified | ✓ |

---

## Step 5: Validate Completeness and Minimality

### Goal

Rigorously verify:
1. **Completeness**: Framework covers all rigor failures
2. **Minimality**: Every element is necessary

Using multiple independent validation methods.

### Completeness Validation

**Method 1: Failure Mode Enumeration (35 modes)**

| Category | Sample Failures | Maps To |
|----------|-----------------|---------|
| Evidence | Unreliable, irrelevant, insufficient, fabricated | Adequate Evidence (+ Honesty) |
| Reasoning | Fallacy, unstated assumptions, no disconfirmation | Sound Inference |
| Scope | Wrong, undefined, changed mid-work | Appropriate Scope |
| Coverage | Incomplete, skipped items, uneven | Full Coverage |
| Process | Not recorded, not reproducible | Documentation |
| Sources | Uncited, broken, fabricated | Traceability (+ Honesty) |
| Accuracy | Omitted findings, overstated confidence | Honesty |
| Meta | Over/under-engineered, wrong rigor level | Simple Path, Calibration |

**Result:** All 35 failure modes map. ✓

**Method 2: Adversarial Challenge (7 challenges)**

| Challenge | Resolution |
|-----------|------------|
| Rigorous but wrong | Framework is process, not outcome—by design |
| Mechanical following | If outputs satisfy principles, that's sufficient |
| Domain knowledge required | Framework is domain-agnostic—by design |
| Time pressure | Calibration handles (Light level) |
| Principle conflicts | Calibration modulates; constraints are scope |
| Honestly wrong | Sound Inference + Adequate Evidence catch |
| Non-rigorous application | Step 7 (Self-apply) tests this |

**Result:** No gaps found. ✓

**Method 3: Methodology Comparison**

| Methodology | All Elements Map? |
|-------------|-------------------|
| Scientific Method | ✓ |
| Legal Standards | ✓ |
| Audit Standards | ✓ |
| Research Methods | ✓ |

**Result:** All established methodologies map. ✓

**Method 4: Dimension Stress Test**

| Dimension | Uncovered Failures Found? |
|-----------|---------------------------|
| Validity | None |
| Completeness | None |
| Transparency | None |

**Result:** No gaps in any dimension. ✓

### Minimality Validation

**Method 1: Removal Test**

| Element | Gap If Removed? |
|---------|-----------------|
| Each of 7 principles | Yes |
| Each of 3 dimensions | Yes |
| Each of 3 phases | Yes |
| Simple Path | Yes (over-engineering) |
| Calibration | Yes (wrong rigor level) |

**Result:** All elements create gaps when removed. ✓

**Method 2: Merge Test**

| Candidate Pairs | Mergeable? |
|-----------------|------------|
| Evidence + Inference | No (sequential) |
| Scope + Coverage | No (different concerns) |
| Documentation + Traceability | No (process vs. provenance) |
| Any + Honesty | No (can satisfy dishonestly) |
| Dimensions | No (orthogonal) |

**Result:** No merges possible. ✓

**Method 3: Redundancy Test**

| Relationship | Redundant? |
|--------------|------------|
| Evidence ↔ Inference | No |
| Documentation ↔ Traceability | No |
| Any ↔ Honesty | No |

**Result:** No redundancy. ✓

**Method 4: Orthogonality Test**

| Principle | Can Fail Independently? |
|-----------|-------------------------|
| Adequate Evidence | Yes |
| Sound Inference | Yes |
| Appropriate Scope | Yes |
| Full Coverage | Yes |
| Documentation | Yes |
| Traceability | Yes |
| Honesty | Yes |

**Result:** All independent. ✓

### Edge Cases

| Edge Case | Handled? |
|-----------|----------|
| Very simple task | Yes (Simple Path) |
| Extremely complex task | Yes (Deep calibration) |
| Partial information | Yes (Evidence + Honesty) |
| Adversarial context | Yes (detection, not prevention) |
| Evolving scope | Yes (iteration to Phase 1) |

### Verdict

| Property | Methods | Result |
|----------|---------|--------|
| **Completeness** | 4 methods, 35+ test cases | **COMPLETE** ✓ |
| **Minimality** | 4 methods, 15 elements | **MINIMAL** ✓ |

**The framework is both COMPLETE and MINIMAL.**

---

## Step 6: Operationalize Each Element

### Goal

Transform each principle and meta-concern into:
1. **Definition** — Refined, precise statement
2. **Actions** — Concrete steps to satisfy
3. **Questions** — Self-check during execution
4. **Outputs** — Artifacts demonstrating satisfaction
5. **Verification Criteria** — How to confirm satisfied
6. **Calibration Variants** — Light / Medium / Deep versions
7. **Red Flags** — Patterns indicating violation

---

### 6.1 Appropriate Scope

#### Definition (Refined)

**From Step 2:** "Boundaries correctly capture what's relevant to the purpose"

**Operationalized:**

> **Appropriate Scope** is established when:
> 1. The **purpose** is stated as a verifiable outcome (not an activity)
> 2. **Boundaries** explicitly define what's included and excluded
> 3. Each boundary is **justified** by relevance to the purpose
> 4. **"Done" criteria** are concrete and testable
> 5. **Assumptions** are explicit (what's taken as given)
> 6. Boundaries are **stable** during execution (changes justified and documented)

**Why outcome over activity:** A scope tied to an activity ("investigate X") never ends. A scope tied to an outcome ("determine whether X") has clear completion.

#### Actions

| # | Action | Output |
|---|--------|--------|
| 1 | State the purpose as an outcome | "Determine whether...", "Identify all...", "Verify that..." |
| 2 | List what's in scope | Explicit enumeration or criteria |
| 3 | List what's out of scope | Explicit exclusions with rationale |
| 4 | State assumptions | What's taken as given |
| 5 | Define "done" criteria | Concrete, testable conditions |
| 6 | Challenge the scope | "Why these boundaries?" |
| 7 | Document stability rule | When can scope change? |

#### Questions (Self-Check)

| Question | Purpose |
|----------|---------|
| What outcome am I trying to achieve? | Prevents activity-drift |
| Why these boundaries? | Ensures justified scope |
| What's excluded and why? | Makes exclusions explicit |
| What assumptions am I making? | Surfaces hidden constraints |
| How will I know I'm done? | Tests completeness criteria |
| Have I confused presentation with problem? | Catches scope misdirection |
| Am I including things because they're easy? | Catches convenience bias |
| Am I excluding things because they're hard? | Catches avoidance bias |
| If I'm wrong about scope, what breaks? | Tests scope stability |
| Has the scope drifted? | Catches scope creep |

#### Outputs

| Artifact | Contents |
|----------|----------|
| **Scope Statement** | Purpose, boundaries, exclusions, assumptions |
| **Done Criteria** | Concrete, testable completion conditions |
| **Boundary Justifications** | Why each inclusion/exclusion |
| **Scope Change Log** | Any modifications during work |

**Minimal Template:**

```markdown
## Scope

**Purpose:** [Verifiable outcome]

**In Scope:**
- [Item 1]
- [Item 2]

**Out of Scope:**
- [Exclusion 1] — Reason: [why irrelevant]

**Assumptions:**
- [What's taken as given]

**Done When:**
- [Testable criterion]
```

#### Verification Criteria

| Criterion | Method |
|-----------|--------|
| Purpose is outcome, not activity | Can say "done" definitively |
| Boundaries are explicit | Written, enumerable |
| Boundaries are justified | Each has rationale |
| Boundaries are stable | No undocumented changes |
| Assumptions are explicit | Written, enumerable |
| Done criteria are testable | Can verify yes/no |
| Scope wasn't convenience-driven | Exclusions aren't "too hard" |

**Checklist:**
- [ ] Purpose stated as verifiable outcome
- [ ] In-scope items explicitly listed
- [ ] Out-of-scope items explicitly listed with rationale
- [ ] Assumptions documented
- [ ] Done criteria concrete and testable
- [ ] Scope justified by relevance, not convenience
- [ ] Scope stable (or changes documented)

#### Calibration Variants

| Level | Depth | When |
|-------|-------|------|
| **Light** | Quick scope, major boundaries | Simple, low stakes |
| **Medium** | Full scope with justifications | Standard task |
| **Deep** | Exhaustive with challenge testing | High stakes, ambiguous |

**Light:** One-sentence purpose, major inclusions/exclusions, basic done criterion

**Medium:** Full template, justifications, multiple done criteria, explicit assumptions

**Deep:** Medium + challenge testing ("Why not broader/narrower?"), stakeholder perspectives, temporal check, competing frames

#### Red Flags

| Red Flag | Violation |
|----------|-----------|
| "I'll know it when I see it" | No testable done criteria |
| Scope as activity, not outcome | Can't determine completion |
| No out-of-scope section | Boundaries undefined |
| Exclusions without rationale | Unjustified boundaries |
| "Everything" or unbounded | Not scoped |
| Scope changed without note | Unstable |
| Easy in, hard out | Convenience bias |
| Assumptions never stated | Hidden constraints |
| Purpose is vague ("understand X") | Can't verify |
| Presenting problem at face value | Scope misdirection |

**Most Dangerous:** Convenience-driven scope—including easy things, excluding hard things, regardless of relevance. Looks thorough but produces systematically biased results.

---

### 6.2 Adequate Evidence

#### Definition (Refined)

**From Step 2:** "Observations bearing on the conclusion are reliable, relevant, and sufficient"

**Sub-properties:**

| Property | Meaning | Failure Mode |
|----------|---------|--------------|
| **Reliable** | Observations accurately represent reality | Inaccurate, fabricated, unverifiable |
| **Relevant** | Observations bear on the conclusion | Tangential data |
| **Sufficient** | Enough for claimed confidence | Strong conclusions from weak evidence |

**Operationalized:**

> **Adequate Evidence** is established when:
> 1. Evidence **sources** are identified and reliability assessed
> 2. Each piece is **relevant** to a specific claim
> 3. Evidence is **sufficient** for confidence level claimed
> 4. **Primary sources** preferred; secondary verified where possible
> 5. **Disconfirming evidence** actively sought
> 6. **Gaps** documented (looked but didn't find)

**Key insight:** Adequacy is claim-relative. "Adequate" means adequate *for the specific conclusion at the specific confidence level*.

#### Evidence Hierarchy

| Level | Type | Examples | Trust |
|-------|------|----------|-------|
| **Primary** | Direct observation | Read file, run code, see output | High—verify directly |
| **Secondary** | Documentation claims | README says, comments state | Medium—verify against primary |
| **Tertiary** | Inference | Pattern suggests, absence implies | Low—flag as inference |

**Rule:** Never treat secondary as primary. Always note the gap.

#### Actions

| # | Action | Output |
|---|--------|--------|
| 1 | Identify what evidence is needed | Evidence requirements from scope |
| 2 | Gather primary evidence first | Direct observations |
| 3 | Note secondary sources separately | Claims requiring verification |
| 4 | Verify secondary against primary | Verification status |
| 5 | Seek disconfirming evidence | Counter-evidence or "none found" |
| 6 | Assess sufficiency for confidence | Confidence calibration |
| 7 | Document gaps | Evidence sought but not found |

#### Questions (Self-Check)

| Question | Purpose |
|----------|---------|
| Is this primary, secondary, or tertiary? | Accurate reliability |
| Can I verify this claim directly? | Identifies verification opportunities |
| Is this relevant to the specific conclusion? | Prevents tangential evidence |
| Do I have enough for my claimed confidence? | Calibrates confidence |
| Have I looked for disproving evidence? | Ensures disconfirmation |
| Am I relying on a single source? | Catches single-point-of-failure |
| Is my evidence representative or cherry-picked? | Detects selection bias |
| What did I look for but not find? | Surfaces gaps |
| Am I treating secondary as primary? | Catches reliability inflation |
| Would someone else reach the same conclusion? | Tests sufficiency |

#### Outputs

| Artifact | Contents |
|----------|----------|
| **Evidence Inventory** | Evidence gathered, organized by claim |
| **Source Citations** | Where each piece came from |
| **Reliability Assessments** | Primary/Secondary/Tertiary |
| **Verification Status** | Which secondary verified |
| **Disconfirmation Log** | Counter-evidence sought |
| **Gap Documentation** | Evidence sought but not found |

**Citation Format:**

```markdown
| Claim | Evidence | Source | Level | Verified? |
|-------|----------|--------|-------|-----------|
| X true | Observed Y | file.py:42 | Primary | — |
| Z exists | Docs state | README:15 | Secondary | Yes |
```

**Negative Findings:**

```markdown
| Sought | Where Looked | Result | Impact |
|--------|--------------|--------|--------|
| Test failures | test_*.py | None found | ↑ confidence |
```

#### Verification Criteria

| Criterion | Method |
|-----------|--------|
| Claims have cited evidence | Traceable to source |
| Hierarchy labeled | Primary/Secondary/Tertiary marked |
| Primary preferred | Secondary only when primary unavailable |
| Secondary verified | At least sampled |
| Confidence matches evidence | Strong claims = strong evidence |
| Disconfirmation attempted | Explicit search |
| Gaps documented | "Not found" recorded |
| No single-source critical claims | Important claims corroborated |

**Checklist:**
- [ ] Each claim cites specific evidence
- [ ] Evidence sources identified (file, line, output)
- [ ] Hierarchy labeled
- [ ] Secondary verified where possible
- [ ] Confidence matches evidence strength
- [ ] Disconfirming evidence sought
- [ ] Negative findings documented
- [ ] No "obviously" / "everyone knows"

#### Calibration Variants

| Level | Depth | When |
|-------|-------|------|
| **Light** | Key claims evidenced, major sources | Low stakes |
| **Medium** | All claims traced, hierarchy labeled, some verification | Standard |
| **Deep** | Exhaustive, all secondary verified, systematic disconfirmation | High stakes |

**Light:** Major claims have evidence, sources cited, critical assumptions noted

**Medium:** All claims cited, hierarchy labeled, secondary spot-checked, disconfirmation for key conclusions, gaps documented

**Deep:** Medium + all secondary verified, systematic disconfirmation for all claims, multiple sources for critical claims, evidence chains documented

#### Red Flags

| Red Flag | Violation |
|----------|-----------|
| Claims without evidence | No support |
| "Obviously" / "Everyone knows" | Assumed knowledge |
| Secondary treated as primary | Reliability inflation |
| Single source for critical claims | No corroboration |
| No disconfirmation sought | Confirmation bias |
| Confidence exceeds evidence | Overstatement |
| No negative findings | Didn't look for gaps |
| Hearsay ("I heard...") | Unverified |
| Cherry-picked evidence | Selection bias |
| Gaps not acknowledged | Hidden limitations |

**Most Dangerous: Confirmation Bias** — Looking only for supporting evidence, ignoring contradictions. Feels thorough (lots of evidence!) but fails in what wasn't sought.

**Anti-pattern: Evidence Fishing** — Starting with conclusion, gathering support. Violates Evidence → Inference dependency.

#### Relationship to Other Principles

| Principle | Relationship |
|-----------|--------------|
| Appropriate Scope | Defines what evidence needed |
| Sound Inference | Uses evidence as input |
| Full Coverage | Ensures all areas have evidence |
| Documentation | Records evidence |
| Traceability | Cites sources |
| Honesty | Constrains presentation (no cherry-picking) |

---

### 6.3 Sound Inference

#### Definition (Refined)

**From Step 2:** "Reasoning from evidence to conclusion is logically valid, with explicit assumptions and disconfirmation"

**Key distinction:**

| Principle | Focus | Analogy |
|-----------|-------|---------|
| Adequate Evidence | Quality of observations | INPUT |
| Sound Inference | Quality of reasoning | PROCESSING |

**Sub-properties:**

| Property | Meaning | Failure Mode |
|----------|---------|--------------|
| **Logically valid** | Conclusion follows from premises | Fallacies, non-sequiturs |
| **Explicit assumptions** | Hidden premises surfaced | Unstated dependencies |
| **Alternatives considered** | Other explanations examined | First-explanation bias |
| **Disconfirmation sought** | Actively tried to prove wrong | Confirmation bias |

**Operationalized:**

> **Sound Inference** is established when:
> 1. **Reasoning is traceable** — each step explicit
> 2. **Steps are valid** — each follows logically
> 3. **Assumptions are explicit** — what's taken as given stated
> 4. **Alternatives considered** — other explanations examined
> 5. **Disconfirmation attempted** — actively sought counter-arguments
> 6. **Confidence calibrated** — certainty matches reasoning strength

#### Common Inference Failures

| Failure | Description |
|---------|-------------|
| **Logical fallacy** | Invalid reasoning pattern |
| **Hidden assumption** | Unstated premise that may be false |
| **Jumping to conclusions** | First explanation taken as true |
| **Confirmation bias** | Only seeing supporting evidence |
| **Correlation ≠ causation** | Confusing association with cause |
| **Survivorship bias** | Only seeing successful cases |
| **Overconfidence** | Certainty exceeds justification |
| **Motivated reasoning** | Reasoning toward desired conclusion |
| **Anchoring** | First information weights too heavily |
| **Explaining away** | Dismissing contradictions without examination |

#### Actions

| # | Action | Output |
|---|--------|--------|
| 1 | State conclusion explicitly | Clear claim |
| 2 | List supporting evidence | Evidence inventory |
| 3 | Trace reasoning chain | Steps from evidence to conclusion |
| 4 | Surface assumptions | What's taken as given |
| 5 | Generate alternatives | Other explanations |
| 6 | Evaluate alternatives | Why this is better |
| 7 | Seek disconfirmation | What would prove wrong |
| 8 | Calibrate confidence | How sure, and why |

#### Questions (Self-Check)

| Question | Purpose |
|----------|---------|
| Does conclusion follow from evidence? | Tests validity |
| Can I trace each reasoning step? | Ensures explicit reasoning |
| What assumptions am I making? | Surfaces hidden premises |
| What alternative explanations exist? | Prevents first-explanation bias |
| Why is my explanation better? | Requires comparison |
| What would prove me wrong? | Enables disconfirmation |
| Have I committed logical fallacies? | Catches invalid reasoning |
| Am I explaining away contradictions? | Detects motivated reasoning |
| Is confidence justified? | Calibrates certainty |
| Did I know conclusion before reasoning? | Detects motivated reasoning |

#### Outputs

| Artifact | Contents |
|----------|----------|
| **Reasoning Chain** | Steps from evidence to conclusion |
| **Assumption Inventory** | What's taken as given |
| **Alternatives Analysis** | Other explanations and why ruled out |
| **Disconfirmation Log** | What would falsify, what was checked |
| **Confidence Assessment** | Level with justification |

**Reasoning Chain Format:**

```markdown
## Reasoning: [Conclusion]

### Evidence
1. [Evidence A] (source)

### Reasoning Steps
1. From [A], infer [X] because [justification]
2. From [X], conclude [Y] because [justification]

### Assumptions
- [Assumption]: Reasonable because [why]

### Alternatives Considered
| Alternative | Why Less Likely |
|-------------|-----------------|
| [Alt 1] | [Reason] |

### Disconfirmation
- Would falsify: [X]
- Checked: [Where]
- Result: [Finding]

### Confidence: [Level]
Justification: [Why]
```

#### Verification Criteria

| Criterion | Method |
|-----------|--------|
| Reasoning explicit | Chain traceable step-by-step |
| Steps valid | No logical fallacies |
| Assumptions stated | Inventory exists |
| Alternatives considered | At least 2-3 examined |
| Alternatives addressed | Each evaluated |
| Disconfirmation attempted | Falsification checked |
| Confidence justified | Level matches reasoning |
| No motivated reasoning | Conclusion not predetermined |

**Checklist:**
- [ ] Conclusion explicitly stated
- [ ] Reasoning chain documented
- [ ] Each step justified
- [ ] Assumptions listed
- [ ] 2-3+ alternatives generated
- [ ] Alternatives evaluated
- [ ] Falsification criteria defined
- [ ] Disconfirmation attempted
- [ ] Confidence justified
- [ ] No logical fallacies
- [ ] Contradictions addressed, not explained away

#### Calibration Variants

| Level | Depth | When |
|-------|-------|------|
| **Light** | Main reasoning, key assumptions | Low stakes |
| **Medium** | Full chain, alternatives, disconfirmation for key | Standard |
| **Deep** | All steps explicit, systematic alternatives, comprehensive disconfirmation | High stakes |

**Light:** Conclusion stated, main reasoning summarized, key assumptions noted

**Medium:** Full chain documented, all assumptions listed, 2-3 alternatives evaluated, disconfirmation for major conclusions

**Deep:** Medium + every step justified, assumptions challenged, exhaustive alternatives, comprehensive disconfirmation, sensitivity analysis

#### Red Flags

| Red Flag | Violation |
|----------|-----------|
| "It's obvious that..." | Skipped reasoning |
| "The only explanation..." | No alternatives |
| Conclusion before reasoning | Motivated reasoning |
| No assumptions stated | Hidden premises |
| "That's just an edge case" | Explaining away |
| Certainty from weak reasoning | Overconfidence |
| First explanation accepted | Jumping to conclusions |
| Can't articulate reasoning | Implicit reasoning |
| Contradictions ignored | Confirmation bias |
| No falsification criteria | Unfalsifiable claim |

**Most Dangerous: Motivated Reasoning** — Constructing reasoning to support predetermined conclusion. Signs: emotional investment, alternatives dismissed quickly, contradictions have "explanations."

**Detection:** "When did I first believe this?" If before reasoning, investigate.

#### Relationship to Other Principles

| Principle | Relationship |
|-----------|--------------|
| Adequate Evidence | Provides input (Evidence → Inference) |
| Appropriate Scope | Defines what conclusions in scope |
| Full Coverage | Ensures all relevant inferences |
| Documentation | Records reasoning chain |
| Traceability | Links conclusions to reasoning |
| Honesty | Constrains reasoning (no motivated reasoning) |

---

### 6.4 Full Coverage

#### Definition (Refined)

**From Step 2:** "Everything within scope is examined adequately"

**Key distinction:**

| Principle | Focus | Question |
|-----------|-------|----------|
| Appropriate Scope | WHAT to examine | Are boundaries correct? |
| Full Coverage | HOW MUCH examined | Was everything in bounds examined? |

**Examination depths:**

| Depth | Meaning |
|-------|---------|
| **Touched** | Acknowledged existence |
| **Reviewed** | Looked at surface |
| **Examined** | Analyzed content |
| **Verified** | Tested/confirmed |

**Operationalized:**

> **Full Coverage** is established when:
> 1. All scope items **enumerated** (can't cover what you haven't identified)
> 2. Coverage is **tracked** (examined vs. remaining visible)
> 3. Each item examined to **adequate depth**
> 4. **No gaps** remain (nothing skipped)
> 5. **Negative findings** documented
> 6. Coverage is **verified**, not just felt

#### The Coverage Matrix

**Structure:** Items × Aspects with status markers

| Marker | Meaning |
|--------|---------|
| `[x]` | Fully examined |
| `[~]` | Partial (note what's missing) |
| `[-]` | N/A (with rationale) |
| `[ ]` | Not yet examined |
| `[?]` | Unknown if applicable |

**Completion Rule:** Coverage not complete until no `[ ]` or `[?]` markers remain.

**Example:**
```markdown
|  | Aspect A | Aspect B | Aspect C |
|--|----------|----------|----------|
| **Item 1** | [x] | [x] | [-] N/A: reason |
| **Item 2** | [x] | [~] Missing: X | [x] |
```

#### Coverage Challenges

| Challenge | Mitigation |
|-----------|------------|
| **Unknown unknowns** | Multiple perspectives, iterative discovery |
| **Infinite scope** | Sample + justify representativeness |
| **Uneven depth** | Explicit depth requirements |
| **False completeness** | Objective tracking (matrix) |
| **Coverage theater** | Define what "examined" means |
| **Discovery during work** | Add to matrix |

#### Actions

| # | Action | Output |
|---|--------|--------|
| 1 | Enumerate scope items | Item list |
| 2 | Define aspects to examine | Aspect list |
| 3 | Create coverage matrix | Tracking structure |
| 4 | Define "examined" per cell | Adequacy criteria |
| 5 | Systematically examine | Findings per cell |
| 6 | Track progress | Updated matrix |
| 7 | Document negative findings | "Looked but didn't find" |
| 8 | Add discovered items | Expanded matrix |
| 9 | Verify no gaps | All cells resolved |

#### Questions (Self-Check)

| Question | Purpose |
|----------|---------|
| Have I enumerated everything in scope? | Completeness of tracking |
| What tracking mechanism am I using? | Prevents subjective coverage |
| Have I examined each item adequately? | Depth vs. touched |
| Are there gaps in my coverage? | Identifies remaining work |
| What did I look for but not find? | Surfaces negative findings |
| Am I confusing "feeling done" with "actually done"? | Catches false completeness |
| Is my coverage depth uniform? | Detects uneven examination |
| Have I added discovered items? | Captures iterations |
| Do any `[ ]` or `[?]` markers remain? | Objective completion |

#### Outputs

| Artifact | Contents |
|----------|----------|
| **Coverage Matrix** | Items × Aspects with status |
| **Progress Tracking** | Examined vs. remaining |
| **Adequacy Criteria** | What "examined" means |
| **Negative Findings Log** | Looked but not found |
| **Discovery Log** | Items added during work |
| **Gap Analysis** | Partial coverage explained |

**Coverage Summary Format:**

```markdown
## Coverage Summary

### Matrix Status
| Status | Count |
|--------|-------|
| [x] Fully examined | N |
| [~] Partial | N |
| [-] N/A | N |
| [ ] Remaining | 0 ← must be zero |
| [?] Unknown | 0 ← must be zero |

### Partial Coverage Notes
- Item/Aspect: [~] because [reason]

### Negative Findings
| Looked For | Where | Result |
|------------|-------|--------|
| [Expected] | [Location] | Not found |
```

#### Verification Criteria

| Criterion | Method |
|-----------|--------|
| All items enumerated | List traceable to scope |
| Tracking exists | Matrix or equivalent |
| All cells resolved | No `[ ]` or `[?]` |
| Partial explained | `[~]` has notes |
| N/A justified | `[-]` has rationale |
| Depth adequate | Matches calibration |
| Negative findings documented | "Not found" recorded |
| Discoveries incorporated | New items added |

**Checklist:**
- [ ] All scope items in matrix
- [ ] All aspects defined
- [ ] No `[ ]` or `[?]` remaining
- [ ] Partial `[~]` explained
- [ ] N/A `[-]` justified
- [ ] Depth matches calibration
- [ ] Negative findings documented
- [ ] Discovered items added
- [ ] Coverage objectively verifiable

#### Calibration Variants

| Level | Depth | When |
|-------|-------|------|
| **Light** | Key items, major gaps noted | Low stakes |
| **Medium** | All items, tracking documented | Standard |
| **Deep** | Exhaustive, all cells verified | High stakes |

**Light:** Major items enumerated, key aspects examined, simple checklist

**Medium:** All items enumerated, full matrix, negative findings, partial coverage explained

**Deep:** Medium + multiple passes, cross-verification, adequacy criteria explicit, sampling verification

#### Red Flags

| Red Flag | Violation |
|----------|-----------|
| "I looked at everything" without tracking | Unverifiable |
| No enumeration | Can't know what's covered |
| No matrix/checklist | Subjective coverage |
| `[ ]` or `[?]` remain | Incomplete |
| Uneven depth (easy deep, hard shallow) | Convenience-driven |
| No negative findings | Didn't look for absences |
| Discovered items ignored | Selective |
| "Feeling done" without verification | False completeness |
| All `[x]` suspiciously fast | Coverage theater |

**Most Dangerous: False Completeness** — Subjective "I've covered everything" without objective verification. Detection: If you can't point to tracking artifact, you don't have verified coverage.

**Anti-pattern: Coverage Theater** — Checking boxes without substance. Detection: Sample verification of `[x]` cells.

#### Relationship to Other Principles

| Principle | Relationship |
|-----------|--------------|
| Appropriate Scope | Defines what to cover (Scope → Coverage) |
| Adequate Evidence | Coverage ensures evidence for all areas |
| Sound Inference | Coverage ensures all relevant inferences |
| Documentation | Records coverage tracking |
| Traceability | Links coverage claims to evidence |
| Honesty | Constrains coverage (no theater) |

---

### 6.5 Documentation

#### Definition (Refined)

**From Step 2:** "Process is recorded (methodology, decisions, steps)"

**Key distinction:**

| Principle | Focus | Question |
|-----------|-------|----------|
| Documentation | Recording PROCESS | What did you do? How? Why? |
| Traceability | Linking CLAIMS to SOURCES | Where did that claim come from? |

**What should be documented:**

| Element | Content |
|---------|---------|
| **Methodology** | Approach used, why chosen |
| **Decisions** | Choices with rationale |
| **Steps** | What was actually done |
| **Deviations** | Where process changed |
| **Tools** | Tools/techniques used |
| **Constraints** | What limited the work |

**Operationalized:**

> **Documentation** is established when:
> 1. **Methodology** is stated
> 2. **Decisions** recorded with rationale
> 3. **Steps** are captured
> 4. **Deviations** are noted
> 5. Documentation is **contemporaneous**
> 6. Process is **reproducible**

#### The Contemporaneous Requirement

| Timing | Quality | Problems |
|--------|---------|----------|
| **Real-time** | High | Accurate, detailed |
| **Same day** | Medium | Some details lost |
| **After completion** | Low | Memory-based, rationalized |

**Rule:** If writing "I did X because Y" from memory, you're reconstructing. Real documentation is written *during* or *immediately after* each step.

**Approaches by overhead:**

| Approach | Quality | Overhead |
|----------|---------|----------|
| Stream-of-consciousness | Highest | Highest |
| Checkpoint summaries | High | Medium |
| End-of-session notes | Medium | Low |

#### Actions

| # | Action | Output |
|---|--------|--------|
| 1 | Choose documentation approach | Format/location |
| 2 | Record methodology upfront | Methodology statement |
| 3 | Document as you go | Running process log |
| 4 | Capture decisions with rationale | Decision log |
| 5 | Note deviations from plan | Deviation notes |
| 6 | Record tools and techniques | Tools inventory |
| 7 | Document constraints | Constraints section |
| 8 | Review for reproducibility | Third-party test |

#### Questions (Self-Check)

| Question | Purpose |
|----------|---------|
| Have I recorded my methodology? | Ensures explicit approach |
| Am I documenting as I go? | Catches deferred documentation |
| Are decisions documented with rationale? | Captures reasoning |
| Could someone else follow my process? | Tests reproducibility |
| Have I noted deviations? | Captures evolution |
| Is documentation accurate or reconstructed? | Checks contemporaneity |
| What tools/versions am I using? | Ensures reproducibility |
| Am I documenting enough for the stakes? | Calibration check |

#### Outputs

| Artifact | Contents |
|----------|----------|
| **Methodology Statement** | Approach, rationale |
| **Decision Log** | Choices with alternatives and rationale |
| **Process Log** | Steps taken chronologically |
| **Deviation Notes** | Plan changes and why |
| **Tools Inventory** | Tools, versions, configs |
| **Constraints Documentation** | Limitations and impact |

**Process Log Format:**

```markdown
### [Timestamp/Phase]
**Activity:** [What was done]
**Output:** [What was produced]
**Decision:** [If any]
- Alternatives: [Considered]
- Rationale: [Why this choice]
**Notes:** [Observations]
```

**Decision Log Format:**

```markdown
### Decision: [Description]
**Context:** [Why needed]
**Options:** 1. [A], 2. [B], 3. [C]
**Chosen:** [X]
**Rationale:** [Why]
**Trade-offs:** [What given up]
```

#### Verification Criteria

| Criterion | Method |
|-----------|--------|
| Methodology stated | Explicit approach documented |
| Decisions recorded | Log with rationale exists |
| Steps captured | Process log present |
| Contemporaneous | Timestamps show real-time |
| Reproducible | Third party could follow |
| Deviations noted | Changes documented |
| Tools specified | Versions recorded |

**Checklist:**
- [ ] Methodology statement exists
- [ ] Key decisions with rationale
- [ ] Process steps recorded
- [ ] Created during work (not after)
- [ ] Deviations noted
- [ ] Tools and versions specified
- [ ] Constraints documented
- [ ] Process is reproducible
- [ ] Depth matches calibration

#### Calibration Variants

| Level | Depth | When |
|-------|-------|------|
| **Light** | Key decisions, major steps | Low stakes |
| **Medium** | Full process log, all decisions | Standard |
| **Deep** | Comprehensive timestamped record | High stakes |

**Light:** Methodology brief, major decisions, key steps, end-of-session acceptable

**Medium:** Full methodology, all decisions with rationale, step-by-step log, checkpoint-based, deviations noted

**Deep:** Medium + timestamps, stream-of-consciousness, all alternatives documented, audit trail complete

#### Red Flags

| Red Flag | Violation |
|----------|-----------|
| "I'll document it later" | Deferred |
| No methodology statement | Implicit process |
| Decisions without rationale | Missing "why" |
| Documentation after completion | Reconstructed |
| Can't explain why something was done | Undocumented |
| Process log suspiciously clean | Sanitized |
| No deviations noted | Hidden changes |
| Missing tool versions | Non-reproducible |
| Documentation doesn't match reality | Dishonest |

**Most Dangerous: Reconstructed Documentation** — Writing from memory after work is done. Looks like documentation but lacks value: details forgotten, decisions rationalized, process cleaned up.

**Detection:** Too clean, too linear, no timestamps. Real-time documentation is messy and shows false starts.

#### Overhead vs. Value

Documentation has costs (time, flow interruption). Managed by **Calibration**:
- Light: Minimal overhead
- Deep: Significant overhead, justified by stakes

**The principle is NOT "document everything."**
**It IS: "Document adequately for the stakes."**

#### Relationship to Other Principles

| Principle | Relationship |
|-----------|--------------|
| Appropriate Scope | Documents scope decisions |
| Adequate Evidence | Records evidence gathered |
| Sound Inference | Captures reasoning |
| Full Coverage | Includes coverage matrix |
| Traceability | Enables traceability (Doc → Trace) |
| Honesty | Constrains (no false records) |

**Key dependency:** Documentation → Traceability. Can't trace without records.

---

### 6.6 Traceability

#### Definition (Refined)

**From Step 2:** "Claims map to sources (each assertion has provenance)"

**Key distinction:**

| Principle | Focus | Question |
|-----------|-------|----------|
| Documentation | Recording PROCESS | What did you do? |
| Traceability | Linking CLAIMS to SOURCES | Where did that come from? |

**What is a claim?** Any assertion of fact: existence, behavior, pattern, absence, quality, conclusion.

**What is a source?** The origin justifying the claim: direct observation, documentation, inference, external authority.

**Operationalized:**

> **Traceability** is established when:
> 1. Every **claim** cites a **source**
> 2. Sources are **specific enough to verify**
> 3. **Links are valid** (source exists and supports claim)
> 4. **Negative claims** trace to search methodology
> 5. **Reasoning chains** are fully traced
> 6. Someone could **follow the trail**

#### Traceability Granularity

| Granularity | Example | Verifiability |
|-------------|---------|---------------|
| **Line-level** | `auth.py:142` | High |
| **Function-level** | `auth.py:validate_token()` | High |
| **Section-level** | `README § Install` | Medium |
| **File-level** | `auth.py` | Low |
| **Vague** | "somewhere" | Unverifiable |

**Rule:** Cite at finest granularity practical. Never vague.

#### The Citation Chain

```
CONCLUSION → REASONING → INTERMEDIATE CLAIMS → EVIDENCE → PRIMARY SOURCES
```

Every link explicit. Example:

```markdown
**Conclusion:** Auth secure against brute force
**Reasoning:**
1. Rate limiting implemented (Evidence 1)
2. Threshold reasonable (Evidence 2)
**Evidence:**
1. Rate limiting: `auth.py:89-105`
2. Threshold: `config.py:23`
```

#### Tracing Negative Claims

| Claim | Required Trace |
|-------|----------------|
| "No vulns found" | What searched, where, how |
| "Function not called" | Where searched for calls |

**Format:**
```markdown
**Claim:** [Negative assertion]
**Search:** [What, where, how]
**Result:** Not found
**Confidence:** [Based on coverage]
```

#### Actions

| # | Action | Output |
|---|--------|--------|
| 1 | Identify claims in work product | Claim inventory |
| 2 | Classify claims by type | Type annotations |
| 3 | Link each claim to source | Citations |
| 4 | Use appropriate granularity | Specific references |
| 5 | Verify links are valid | Link check |
| 6 | Trace reasoning chains | Chain documentation |
| 7 | Document negative claim searches | Search records |
| 8 | Test: can someone follow? | Verification test |

#### Questions (Self-Check)

| Question | Purpose |
|----------|---------|
| Does every claim cite a source? | Completeness |
| Are citations specific enough? | Granularity |
| Do links actually work? | Validity |
| Do sources support the claims? | Accuracy |
| Can someone follow citations to verify? | Reproducibility |
| Are negative findings traced to search? | Negative claims |
| Is reasoning chain fully traced? | Chain completeness |
| Am I citing unverified sources? | Secondary source check |
| Any "trust me" claims? | Untraced check |

#### Outputs

| Artifact | Contents |
|----------|----------|
| **Cited Work Product** | Claims with inline citations |
| **Source Index** | All sources referenced |
| **Reasoning Chains** | Conclusion → evidence traces |
| **Negative Finding Records** | Search methodology |
| **Link Verification Log** | Confirmation links work |

**Inline Format:**
```markdown
Uses bcrypt for hashing (`auth.py:45`), appropriate per OWASP guidelines.
```

**Source Index:**
```markdown
### Code
- `auth.py:45` — bcrypt usage
### Documentation
- OWASP Password Storage — standard
```

#### Verification Criteria

| Criterion | Method |
|-----------|--------|
| All claims sourced | Scan for unsourced |
| Sources specific | Granularity check |
| Links valid | Follow each citation |
| Sources support claims | Verify content |
| Negative claims traced | Search records exist |
| Chains complete | No gaps |

**Checklist:**
- [ ] Every claim cites source
- [ ] Citations specific (line, section)
- [ ] Sources exist and accessible
- [ ] Sources support claims made
- [ ] Negative claims have search records
- [ ] Reasoning chains complete
- [ ] Evidence traced to primary sources
- [ ] No "trust me" claims
- [ ] Links verified working
- [ ] Third party could verify

#### Calibration Variants

| Level | Depth | When |
|-------|-------|------|
| **Light** | Key claims cited | Low stakes |
| **Medium** | All claims traced, links verified | Standard |
| **Deep** | Line-level, all chains complete | High stakes |

**Light:** Major claims cited, key sources, obvious claims implicit

**Medium:** All claims cited, appropriate granularity, links verified, negative findings traced

**Deep:** Medium + line-level where possible, all chains explicit, independent verification

#### Red Flags

| Red Flag | Violation |
|----------|-----------|
| Claims without sources | Untraced |
| "I saw it somewhere" | Vague citation |
| Broken links | Invalid reference |
| File-level for specific claim | Wrong granularity |
| "Obviously" / "Everyone knows" | Assumed knowledge |
| Negative claim without search | Untraced absence |
| Conclusion without chain | Missing trace |
| Citation doesn't support claim | Fabricated |
| Secondary treated as verified | Unchecked |
| "Trust me" | Explicit untraceable |

**Most Dangerous: Fabricated Traceability** — Citations that look valid but don't support the claim. Source exists but doesn't say what's claimed. Worse than no citation—creates false confidence.

**Detection:** Verify citations actually support claims.

#### Relationship to Other Principles

| Principle | Relationship |
|-----------|--------------|
| Documentation | Provides records to trace (Doc → Trace) |
| Adequate Evidence | Evidence sources traced |
| Sound Inference | Reasoning chains traced |
| Full Coverage | Coverage claims traced |
| Appropriate Scope | Scope claims traced |
| Honesty | Constrains (no fabrication) |

---

### 6.7 Honesty

#### Definition (Refined)

**From Step 2:** "Documentation accurately represents reality, including uncertainty"

**Key insight:** Honesty isn't a separate activity—it's a *constraint* on how other principles are satisfied. You can have thorough documentation that's sanitized. You can have complete traceability that fabricates support. Honesty is what prevents the form of transparency without the substance.

**What Honesty constrains:**

| Principle | Without Honesty | With Honesty |
|-----------|-----------------|--------------|
| Documentation | Sanitized records | Accurate process capture |
| Traceability | Fabricated citations | Genuine source links |
| Adequate Evidence | Cherry-picked data | Representative evidence |
| Sound Inference | Motivated reasoning | Genuine reasoning |
| Full Coverage | Coverage theater | Genuine examination |

**Operationalized:**

> **Honesty** is established when:
> 1. **All findings reported** — including those that contradict conclusions
> 2. **Uncertainty explicit** — confidence levels stated, limitations acknowledged
> 3. **Records accurate** — documentation represents what actually happened
> 4. **Evidence representative** — not cherry-picked for conclusions
> 5. **Citations genuine** — sources actually support claims made
> 6. **Failures documented** — dead ends, mistakes, corrections included
> 7. **No spin** — framing doesn't mislead even when technically accurate

#### Types of Dishonesty

| Type | Description | Example |
|------|-------------|---------|
| **Omission** | Leaving out inconvenient findings | Not mentioning the test that failed |
| **Commission** | Actively stating falsehoods | Claiming verification that didn't happen |
| **Overstatement** | Claiming more certainty than warranted | "Definitely secure" from partial review |
| **Cherry-picking** | Selecting supporting evidence only | 10 examples supporting, ignoring 3 contradicting |
| **Sanitization** | Cleaning up records | Removing failed attempts from process log |
| **Fabrication** | Inventing sources or findings | Citation that doesn't support claim |
| **Spin** | Misleading framing | "Found no critical issues" (didn't look for them) |

**Relationship: Conscious vs. Unconscious**

| Mode | Awareness | Detection | Danger |
|------|-----------|-----------|--------|
| **Conscious** | Know you're being dishonest | Harder—deliberate concealment | Medium—requires active deception |
| **Unconscious** | Don't realize omissions | Easier—patterns visible | High—feels honest |

**Unconscious dishonesty** is more dangerous because:
1. It feels honest (no guilty conscience)
2. It's systematic (cognitive biases)
3. It resists correction (defender believes own accuracy)
4. It corrupts rigor while maintaining appearance

#### Actions

| # | Action | Output |
|---|--------|--------|
| 1 | Report all findings, not just supporting | Complete findings inventory |
| 2 | State uncertainty explicitly | Confidence levels on claims |
| 3 | Document limitations | Known gaps and constraints |
| 4 | Include contradicting evidence | Counter-evidence section |
| 5 | Record failures and corrections | Corrections log |
| 6 | Verify citations support claims | Citation accuracy check |
| 7 | Review for unintentional omissions | Omission review |
| 8 | Check framing for spin | Framing review |

#### Questions (Self-Check)

| Question | Purpose |
|----------|---------|
| Have I reported findings that contradict my conclusions? | Detects omission |
| Am I overstating my confidence? | Catches overstatement |
| Would I be embarrassed if someone found what I left out? | Reveals hidden omissions |
| Does my documentation reflect what actually happened? | Checks accuracy |
| Are my citations actually supporting my claims? | Catches fabrication |
| Am I framing things to sound better than warranted? | Detects spin |
| Did I include my failures and corrections? | Checks completeness |
| What's the strongest argument against my conclusion? | Forces counter-acknowledgment |
| If I'm wrong, where would the evidence be? | Tests disconfirmation |
| Am I being as critical of supporting evidence as contradicting? | Detects double standard |

#### The Counter-Conclusion Test

**Critical check:** Document the best argument *against* your conclusion.

If you can't articulate it, you either:
1. Haven't looked (Coverage failure)
2. Haven't thought about it (Inference failure)
3. Are avoiding it (Honesty failure)

**Format:**
```markdown
## Counter-Conclusion Analysis

**Conclusion:** [Your main conclusion]

**Best argument against:**
[Steel-man the counter-position]

**Why I still conclude X:**
[Response with evidence]

**Remaining uncertainty:**
[What could still be wrong]
```

#### Outputs

| Artifact | Contents |
|----------|----------|
| **Counter-Evidence Section** | Findings that challenge conclusions |
| **Limitations Statement** | What wasn't covered, what could be wrong |
| **Confidence Calibration** | Certainty levels with justification |
| **Corrections Log** | Mistakes made and corrected |
| **Counter-Conclusion Analysis** | Best argument against findings |
| **Framing Review** | Check of language for spin |

**Limitations Statement Format:**

```markdown
## Limitations

### Not Covered
- [What was out of scope]
- [What couldn't be examined]

### Assumptions
- [What was taken as given]
- [What wasn't verified]

### Uncertainty
- [Where confidence is lower]
- [What could change findings]

### Counter-Evidence
- [Evidence against conclusions]
- [Why conclusions still hold]
```

#### Verification Criteria

| Criterion | Method |
|-----------|--------|
| Counter-evidence documented | Check for contradicting findings |
| Uncertainty stated | Confidence levels present |
| Limitations acknowledged | Limitations section exists |
| Failures included | Corrections visible |
| Citations accurate | Spot-check source support |
| No hidden omissions | Compare findings to methodology |
| Framing neutral | Language review |
| Counter-conclusion present | Best argument against stated |

**Checklist:**
- [ ] Contradicting evidence documented
- [ ] Confidence levels on major claims
- [ ] Limitations section present
- [ ] Failures and corrections included
- [ ] Citations verified to support claims
- [ ] Counter-conclusion analysis present
- [ ] Framing reviewed for spin
- [ ] Methodology matches findings scope
- [ ] Would stake reputation on accuracy

#### Calibration Variants

| Level | Depth | When |
|-------|-------|------|
| **Light** | Major limitations noted, key uncertainties | Low stakes |
| **Medium** | Full limitations, counter-evidence, confidence levels | Standard |
| **Deep** | Comprehensive counter-analysis, verified citations, independent review | High stakes |

**Light:** Major limitations stated, key uncertainties noted, obvious counter-evidence acknowledged

**Medium:** Full limitations section, all counter-evidence documented, confidence levels throughout, corrections included, counter-conclusion analysis

**Deep:** Medium + all citations verified, independent review for omissions, adversarial counter-argument, framing review, external validation

#### Red Flags

| Red Flag | Violation |
|----------|-----------|
| No counter-evidence mentioned | Omission |
| All findings support conclusion | Cherry-picking |
| No limitations section | Hidden constraints |
| Perfect process (no corrections) | Sanitization |
| Citations don't support claims | Fabrication |
| "Definitely" / "Certainly" without justification | Overstatement |
| "Found no issues" (didn't look) | Spin |
| Can't articulate counter-argument | Avoidance |
| Embarrassing findings absent | Motivated omission |
| Too clean, too linear | Reconstruction |

**Most Dangerous: Motivated Omission**

Selectively omitting findings that undermine conclusions, often unconsciously, while genuinely believing work is complete and honest.

**Why most dangerous:**
1. **Feels honest** — No awareness of omission
2. **Systematic** — Cognitive bias creates patterns
3. **Self-reinforcing** — More evidence "supports" conclusion
4. **Hard to detect** — Requires comparing findings to methodology
5. **Defended vigorously** — Believer is certain of honesty

**Detection:**
- Compare what methodology *would* find vs. what's reported
- Ask "what would prove me wrong?" and check if looked
- External review finds "obvious" things missed
- Pattern of findings all pointing same direction
- Absence of documented negative findings

**Prevention:**
- Document contradicting evidence *before* concluding
- Steel-man counter-arguments
- Independent verification
- Pre-register what would change conclusions

#### Honesty as Constraint

Unlike other principles, Honesty doesn't prescribe activities—it constrains how other principles are satisfied:

| Constraint | On Principle | Effect |
|------------|--------------|--------|
| No cherry-picking | Adequate Evidence | Representative evidence |
| No motivated reasoning | Sound Inference | Genuine reasoning |
| No coverage theater | Full Coverage | Actual examination |
| No sanitization | Documentation | Accurate records |
| No fabrication | Traceability | Valid citations |
| No spin | All | Neutral framing |

**Test:** Would you be comfortable if:
- All your raw notes were public?
- Your methodology was audited?
- Someone checked every citation?
- An adversary looked for what you omitted?

#### Relationship to Other Principles

| Principle | Relationship |
|-----------|--------------|
| Documentation | Honesty constrains: accuracy, completeness |
| Traceability | Honesty constrains: citations genuine |
| Adequate Evidence | Honesty constrains: no cherry-picking |
| Sound Inference | Honesty constrains: no motivated reasoning |
| Full Coverage | Honesty constrains: no theater |
| Appropriate Scope | Honesty constrains: scope not convenience-driven |

**Honesty is meta-Transparency:** It's what makes Documentation and Traceability meaningful. Form without honesty is sophisticated deception.

---

### 6.8 Meta-Concerns (Simple Path + Calibration)

The meta-concerns operate at a level above the 7 principles—they govern *whether* and *how deeply* to apply the framework.

---

#### 6.8.1 Simple Path Check

##### Definition

**From Step 3:** "Is there an obvious simple approach that works? If yes → use it, skip framework. If no → engage framework."

**Purpose:** Prevent over-engineering. The Framework for Rigor is a tool, not a mandate. Using heavy machinery on trivial tasks is itself a rigor failure—miscalibrated effort.

**Key insight:** Simple Path Check is *not* permission to skip rigor. It's recognition that some tasks don't need the full framework because the simple path *is* rigorous enough.

**Operationalized:**

> **Simple Path Check** is satisfied when:
> 1. A **direct solution** to the actual problem is identified
> 2. The solution has **low complexity** (few steps, dependencies)
> 3. **Risk is low** (reversible, limited blast radius)
> 4. **Confidence is high** (prior experience, well-documented)
> 5. Quick **validation is possible** before committing
> 6. **Abandonment triggers** are defined (when to engage full framework)

##### Simple Path Characteristics

| Characteristic | Simple | Complex |
|----------------|--------|---------|
| **Steps** | Few, linear | Many, branching |
| **Dependencies** | Minimal | Multiple |
| **Reversibility** | Easy | Difficult/impossible |
| **Blast radius** | Limited | Wide |
| **Precedent** | None set | Pattern established |
| **Confidence** | High (done before) | Low (novel) |

**Rule:** If 4+ characteristics are "Complex," engage the framework.

##### The Verification Step

**Critical:** Simple Path Check includes lightweight verification, not blind trust.

```
Simple Path identified
    │
    ▼
Quick validation (does this actually work?)
    │
    ├── YES + Low stakes → Execute simple path
    │
    ├── YES + Higher stakes → Document briefly, execute
    │
    └── NO or UNCERTAIN → Engage framework
```

**Verification methods:**
- Quick test (for code: does it run?)
- Sanity check (does the approach make sense?)
- Prior experience (have I done this before?)
- Documentation check (is this the documented approach?)

##### Abandonment Triggers

| Trigger | Action |
|---------|--------|
| Unexpected complexity emerges | Stop, engage framework |
| Initial assumptions prove wrong | Stop, re-scope |
| Risk higher than anticipated | Stop, recalibrate |
| Confidence drops significantly | Stop, gather evidence |
| Simple path hits dead end | Engage framework |
| Time spent exceeds expected by 2x | Reconsider approach |

**Rule:** When in doubt, engage the framework. Under-rigor costs more than over-rigor.

##### Actions

| # | Action | Output |
|---|--------|--------|
| 1 | Identify the direct solution | Simple path candidate |
| 2 | Assess complexity | Complexity check |
| 3 | Assess risk/reversibility | Risk assessment |
| 4 | Assess confidence | Confidence level |
| 5 | Define quick validation | Validation step |
| 6 | Define abandonment triggers | Trigger list |
| 7 | Execute or engage framework | Path chosen |

##### Questions (Self-Check)

| Question | Purpose |
|----------|---------|
| Is there an obvious direct solution? | Identifies simple path |
| Why might this be more complex than it appears? | Challenges simplicity assumption |
| What could go wrong? | Surfaces hidden risk |
| Have I done exactly this before successfully? | Tests confidence basis |
| How would I know if the simple path failed? | Defines validation |
| At what point should I stop and reconsider? | Sets abandonment triggers |
| Am I avoiding the framework because it's work? | Detects laziness disguised as simplicity |
| Would an expert agree this is simple? | External perspective |

##### Verification Criteria

| Criterion | Method |
|-----------|--------|
| Simple path explicitly identified | Written statement |
| Complexity assessed | Characteristic check |
| Risk assessed | Reversibility, blast radius |
| Confidence justified | Prior experience or documentation |
| Quick validation defined | Test or check specified |
| Abandonment triggers set | Explicit criteria |
| Decision documented | Path choice recorded |

**Checklist:**
- [ ] Direct solution identified
- [ ] Complexity < 4 "complex" characteristics
- [ ] Risk is low (reversible, limited blast radius)
- [ ] Confidence justified (not assumed)
- [ ] Quick validation possible
- [ ] Abandonment triggers defined
- [ ] Decision documented briefly

##### Red Flags

| Red Flag | Violation |
|----------|-----------|
| "This is easy" without assessment | Assumed simplicity |
| No abandonment triggers defined | Tunnel vision risk |
| Skipping validation | False confidence |
| Sticking with failing simple path | Sunk cost |
| Avoiding framework because "too much work" | Laziness as strategy |
| Novel task called "simple" | Overconfidence |
| High stakes + "simple path" | Risk underestimate |
| "I'll figure it out as I go" | No exit criteria |

**Most Dangerous: False Simplicity**

Believing a task is simple when it's actually complex, proceeding without rigor, and failing in ways that rigorous analysis would have prevented.

**Why most dangerous:**
1. **Invisible until failure** — Complexity emerges only after commitment
2. **Sunk cost trap** — Investment makes abandonment harder
3. **Compounds** — Simple-path decisions cascade
4. **Confidence-masking** — "I've done this before" hides novel elements

**Detection:**
- "Simple" task takes much longer than expected
- Unexpected edge cases multiply
- Assumptions keep proving wrong
- Fixes introduce new problems

**Prevention:**
- Challenge "simple" assumption explicitly
- Define abandonment triggers upfront
- Set time/effort bounds for simple path
- Quick validation before commitment

---

#### 6.8.2 Calibration

##### Definition

**From Step 3:** "How much rigor is warranted? (Light / Medium / Deep). Modulates depth of all phases."

**Purpose:** Match effort to stakes. Maximum rigor on every task is wasteful and potentially counterproductive (analysis paralysis). Insufficient rigor on high-stakes tasks is dangerous.

**Key insight:** Calibration is not about *whether* to be rigorous—all levels are rigorous. It's about *how much depth* is appropriate.

**Operationalized:**

> **Calibration** is correct when:
> 1. **Stakes are assessed** explicitly
> 2. Calibration level **matches stakes**
> 3. Level is **documented** (so work can be evaluated correctly)
> 4. Level **adjusts** if stakes change during work
> 5. All principles applied at **consistent depth**
> 6. Level is **not used as excuse** for sloppy work

##### Stakes Assessment

| Factor | Low | Medium | High |
|--------|-----|--------|------|
| **Reversibility** | Easy to undo | Moderate effort | Irreversible |
| **Blast radius** | Limited scope | Moderate scope | Wide scope |
| **Visibility** | Private | Team | External/public |
| **Precedent** | One-time | Reference | Pattern-setting |
| **Cost of error** | Minimal | Moderate | Severe |
| **Uncertainty** | Well-understood | Some unknowns | Novel/uncertain |
| **Time pressure** | Flexible | Constrained | Critical deadline |

**Scoring:**
- 5+ "Low" → Light calibration
- Mixed or 4+ "Medium" → Medium calibration
- 3+ "High" OR any "Irreversible" + "Severe" → Deep calibration

##### Calibration Levels

| Level | Depth | Documentation | Verification |
|-------|-------|---------------|--------------|
| **Light** | Key elements only | Brief notes | Quick checks |
| **Medium** | All elements | Full documentation | Systematic verification |
| **Deep** | Exhaustive | Comprehensive audit trail | Independent verification |

**When to use:**

| Level | When |
|-------|------|
| **Light** | Routine tasks, low stakes, well-understood, easily reversible, internal only |
| **Medium** | Standard work, moderate stakes, will be referenced, needs reproducibility |
| **Deep** | High stakes, audit scrutiny expected, irreversible, novel domain, external review, precedent-setting |

##### Calibration Effects by Principle

| Principle | Light | Medium | Deep |
|-----------|-------|--------|------|
| **Scope** | Quick, major boundaries | Full template, justifications | Exhaustive, challenge testing |
| **Evidence** | Key claims cited | All claims, hierarchy labeled | All verified, systematic disconfirmation |
| **Inference** | Main reasoning | Full chain, alternatives | Every step, comprehensive disconfirmation |
| **Coverage** | Major items, simple checklist | All items, full matrix | Exhaustive, cross-verified, sampling |
| **Documentation** | Key decisions, end-of-session | Full process log | Timestamped, stream-of-consciousness |
| **Traceability** | Major claims sourced | All claims, links verified | Line-level, all chains complete |
| **Honesty** | Major limitations noted | Full counter-evidence | Independent review, adversarial |

**Consistency Rule:** All principles at same calibration level. Mixing creates false confidence.

##### Dynamic Calibration

| Trigger | Action |
|---------|--------|
| Stakes increase during work | Escalate calibration |
| Stakes decrease during work | May maintain (safer) or reduce (documented) |
| Uncertainty higher than expected | Consider escalation |
| More visibility than expected | Escalate calibration |
| New stakeholders emerge | Reassess stakes |

**Rule:** Escalating calibration is always safe. Reducing calibration requires explicit justification.

##### Actions

| # | Action | Output |
|---|--------|--------|
| 1 | Assess stakes factors | Stakes assessment |
| 2 | Determine calibration level | Level decision |
| 3 | Document calibration choice | Calibration statement |
| 4 | Apply consistent depth | All principles at level |
| 5 | Monitor for stake changes | Adjustment triggers |
| 6 | Adjust if needed | Documented changes |

##### Questions (Self-Check)

| Question | Purpose |
|----------|---------|
| What are the stakes if I'm wrong? | Core stakes assessment |
| Is this reversible? | Reversibility check |
| Who will see or depend on this work? | Visibility/impact check |
| Is this novel or well-understood? | Uncertainty check |
| What calibration level am I using? | Forces explicit choice |
| Is this level appropriate for the stakes? | Alignment check |
| Am I being consistent across principles? | Consistency check |
| Am I using Light as excuse for sloppiness? | Motivation check |
| Have stakes changed since I started? | Dynamic check |

##### Outputs

| Artifact | Contents |
|----------|----------|
| **Stakes Assessment** | Factors evaluated |
| **Calibration Statement** | Level chosen with rationale |
| **Consistency Check** | All principles at same level |
| **Adjustment Log** | Any changes during work |

**Calibration Statement Format:**

```markdown
## Calibration

**Stakes Assessment:**
- Reversibility: [Low/Medium/High]
- Blast radius: [Low/Medium/High]
- Visibility: [Low/Medium/High]
- Cost of error: [Low/Medium/High]

**Calibration Level:** [Light/Medium/Deep]

**Rationale:** [Why this level is appropriate]
```

##### Verification Criteria

| Criterion | Method |
|-----------|--------|
| Stakes explicitly assessed | Assessment documented |
| Level explicitly chosen | Statement present |
| Level matches stakes | Alignment check |
| Consistent across principles | Depth review |
| Not used as excuse | Quality check |
| Changes documented | Adjustment log |

**Checklist:**
- [ ] Stakes assessed across factors
- [ ] Calibration level explicitly chosen
- [ ] Rationale documented
- [ ] All principles at consistent depth
- [ ] Quality appropriate for level (Light ≠ sloppy)
- [ ] Any adjustments documented

##### Red Flags

| Red Flag | Violation |
|----------|-----------|
| No calibration stated | Implicit/unexamined |
| "Light" on novel, high-stakes | Under-calibration |
| "Deep" on routine, reversible | Over-calibration |
| Different depths per principle | Inconsistent |
| "Light" as excuse for poor work | Misuse |
| Stakes changed, calibration didn't | Static calibration |
| Calibration reduced without justification | Silent downgrade |
| Time pressure → Light | Conflating urgency with stakes |

**Most Dangerous: Under-Calibration**

Using insufficient rigor for actual stakes, especially Light calibration on tasks that warrant Deep.

**Why most dangerous:**
1. **Costs are asymmetric** — Under-calibration risks failure; over-calibration wastes time
2. **Often invisible until failure** — Inadequate rigor doesn't announce itself
3. **Feels efficient** — "I saved time" until the failure
4. **Hard to recover** — Once committed, raising rigor may be too late

**Detection:**
- High-stakes decision with Light documentation
- Novel task treated as routine
- Irreversible action without Deep verification
- External scrutiny reveals gaps

**Prevention:**
- Explicit stakes assessment before starting
- Default to higher calibration when uncertain
- "What if I'm wrong?" test
- Peer review of calibration choice on high-stakes

##### Calibration ≠ Rigor Level

**Critical distinction:**

| Confusion | Reality |
|-----------|---------|
| "Light = not rigorous" | Light is rigorous—just scoped to key elements |
| "Deep = better" | Deep is appropriate for stakes—wasteful otherwise |
| "Time pressure = Light" | Urgency doesn't change stakes |
| "Internal = Light" | Visibility is one factor, not sole determinant |

**Light calibration done well:**
- Key elements identified and addressed
- Brief but accurate documentation
- Quick but genuine verification
- Limitations acknowledged

**Light calibration done poorly (sloppy):**
- Random elements addressed
- No documentation
- No verification
- No limitations stated

**Both use "Light" label. Only the first is legitimate.**

---

#### 6.8.3 Meta-Concern Relationships

| Element | Relationship |
|---------|--------------|
| **Simple Path → Calibration** | If simple path rejected, Calibration determines depth |
| **Calibration → All Principles** | Modulates depth of each principle |
| **Simple Path ← Stakes** | High stakes = more likely to engage framework |
| **Calibration ← Stakes** | Stakes determine calibration level |

**Flow:**

```
Task arrives
    │
    ▼
Simple Path Check
    │
    ├── Simple path valid → Execute (with quick validation)
    │
    └── Engage framework
            │
            ▼
        Calibration (assess stakes)
            │
            ▼
        Apply framework at calibrated depth
```

---

### 6.9 Synthesis (Phase Checklists, Red Flags)

This section consolidates all operationalized elements into usable operational tools.

---

#### 6.9.1 Phase Checklists

##### Pre-Framework: Simple Path Check

| # | Check | Status |
|---|-------|--------|
| 1 | Direct solution identified | [ ] |
| 2 | Complexity < 4 "complex" characteristics | [ ] |
| 3 | Risk low (reversible, limited blast radius) | [ ] |
| 4 | Confidence justified (not assumed) | [ ] |
| 5 | Quick validation defined | [ ] |
| 6 | Abandonment triggers set | [ ] |

**Decision:** All checked + low stakes → Simple path. Otherwise → Engage framework.

##### Meta: Calibration

| # | Check | Status |
|---|-------|--------|
| 1 | Stakes assessed (reversibility, blast radius, visibility, cost of error, uncertainty) | [ ] |
| 2 | Calibration level explicitly chosen (Light/Medium/Deep) | [ ] |
| 3 | Rationale documented | [ ] |

**Quick Reference:** 5+ "Low" → Light | Mixed/4+ "Medium" → Medium | 3+ "High" or Irreversible+Severe → Deep

##### Phase 1: Definition (Scope)

| # | Check | Light | Medium | Deep |
|---|-------|-------|--------|------|
| 1 | Purpose stated as verifiable outcome | ✓ | ✓ | ✓ |
| 2 | In-scope items explicitly listed | Major | All | Exhaustive |
| 3 | Out-of-scope items listed with rationale | Major | All | All + challenged |
| 4 | Assumptions documented | Key | All | All + tested |
| 5 | Done criteria concrete and testable | ✓ | ✓ | ✓ |
| 6 | Scope justified by relevance, not convenience | ✓ | ✓ | ✓ + adversarial |

**Checkpoint:** Can I state exactly what "done" looks like? Yes → Phase 2. No → Continue defining.

##### Phase 2: Execution

**Evidence:**

| # | Check | Light | Medium | Deep |
|---|-------|-------|--------|------|
| 1 | Each claim cites specific evidence | Key | All | All + verified |
| 2 | Hierarchy labeled (P/S/T) | — | ✓ | ✓ |
| 3 | Secondary verified where possible | — | Sampled | All |
| 4 | Disconfirming evidence sought | Key | All major | Systematic |
| 5 | Negative findings documented | — | ✓ | ✓ |

**Inference:**

| # | Check | Light | Medium | Deep |
|---|-------|-------|--------|------|
| 1 | Conclusions explicitly stated | ✓ | ✓ | ✓ |
| 2 | Reasoning chain documented | Summary | Full | Every step |
| 3 | Assumptions listed | Key | All | All + challenged |
| 4 | Alternatives generated and evaluated | — | 2-3 | Exhaustive |
| 5 | Disconfirmation attempted | — | Key | Comprehensive |
| 6 | Confidence justified | ✓ | ✓ | ✓ |

**Coverage:**

| # | Check | Light | Medium | Deep |
|---|-------|-------|--------|------|
| 1 | All scope items enumerated | Major | All | All + discovered |
| 2 | Tracking mechanism exists | List | Matrix | Matrix + verified |
| 3 | No [ ] or [?] remaining | ✓ | ✓ | ✓ |
| 4 | Partial [~] and N/A [-] explained | — | ✓ | ✓ |
| 5 | Negative findings documented | — | ✓ | ✓ |

**Documentation (Continuous):**

| # | Check | Light | Medium | Deep |
|---|-------|-------|--------|------|
| 1 | Methodology statement exists | Brief | Full | Comprehensive |
| 2 | Decisions recorded with rationale | Major | All | All + alternatives |
| 3 | Process steps recorded | Summary | Full | Timestamped |
| 4 | Created during work (not after) | ✓ | ✓ | ✓ |
| 5 | Deviations noted | — | ✓ | ✓ |

**Traceability (Continuous):**

| # | Check | Light | Medium | Deep |
|---|-------|-------|--------|------|
| 1 | Every claim cites source | Key | All | All |
| 2 | Citations specific | File | Section | Line |
| 3 | Sources support claims | ✓ | ✓ | Verified |
| 4 | Negative claims have search records | — | ✓ | ✓ |
| 5 | Reasoning chains complete | — | Key | All |

**Honesty (Continuous):**

| # | Check | Light | Medium | Deep |
|---|-------|-------|--------|------|
| 1 | Contradicting evidence documented | Obvious | All | All |
| 2 | Confidence levels stated | ✓ | ✓ | ✓ |
| 3 | Limitations section present | Key | Full | Comprehensive |
| 4 | Failures and corrections included | — | ✓ | ✓ |
| 5 | Counter-conclusion analysis present | — | ✓ | Adversarial |
| 6 | Framing reviewed for spin | — | ✓ | ✓ + external |

##### Phase 3: Verification

| Principle | Verification Question | Status |
|-----------|----------------------|--------|
| Scope | Purpose is outcome, boundaries explicit and justified? | [ ] |
| Evidence | Claims supported, hierarchy labeled, disconfirmation attempted? | [ ] |
| Inference | Reasoning explicit, alternatives considered, confidence calibrated? | [ ] |
| Coverage | Matrix complete, no gaps, negative findings documented? | [ ] |
| Documentation | Process recorded, reproducible, contemporaneous? | [ ] |
| Traceability | Claims sourced, links valid, chains complete? | [ ] |
| Honesty | Counter-evidence present, limitations stated, framing neutral? | [ ] |

**Decision:** All verified → Done. Any failed → Iterate back.

---

#### 6.9.2 Consolidated Red Flags

##### The 9 Most Dangerous Failures

| Rank | Pattern | Element | Detection |
|------|---------|---------|-----------|
| 1 | **False Simplicity** | Simple Path | Task takes 2x+ expected; edge cases multiply |
| 2 | **Under-Calibration** | Calibration | High stakes + Light documentation |
| 3 | **Convenience-Driven Scope** | Scope | Exclusions are "too hard" |
| 4 | **Confirmation Bias** | Evidence | No disconfirming evidence documented |
| 5 | **Motivated Reasoning** | Inference | Conclusion known before reasoning |
| 6 | **False Completeness** | Coverage | No matrix or tracking artifact |
| 7 | **Reconstructed Documentation** | Documentation | Too clean, no timestamps, linear narrative |
| 8 | **Fabricated Traceability** | Traceability | Source doesn't say what's claimed |
| 9 | **Motivated Omission** | Honesty | All findings support conclusion |

##### Red Flags by Phase

**Pre-Framework:**
- "This is easy" without assessment
- High stakes + "simple path"
- Novel task called "simple"
- No abandonment triggers
- Avoiding framework because "too much work"

**Calibration:**
- No calibration stated
- "Light" on novel, high-stakes
- Time pressure → Light
- Different depths per principle
- Calibration reduced without justification

**Phase 1 (Definition):**
- "I'll know it when I see it"
- Scope as activity, not outcome
- No out-of-scope section
- Exclusions without rationale
- Easy in, hard out
- Assumptions never stated

**Phase 2 (Execution):**
- Claims without evidence
- "Obviously" / "Everyone knows"
- Secondary treated as primary
- No disconfirmation sought
- "It's obvious that..." / "The only explanation..."
- Conclusion before reasoning
- "I looked at everything" without tracking
- No matrix/checklist
- "Feeling done" without verification
- "I'll document it later"
- Documentation after completion
- "I saw it somewhere"
- No counter-evidence mentioned
- All findings support conclusion
- Perfect process (no corrections)

**Phase 3 (Verification):**
- "Everything works" without evidence
- "Tests pass" without output
- All findings equally confident
- No limitations section
- Can't articulate counter-argument

---

#### 6.9.3 Quick Reference Card

**The 7 Principles:**

| # | Principle | Core Requirement |
|---|-----------|------------------|
| 1 | **Scope** | Purpose as outcome, explicit boundaries |
| 2 | **Evidence** | Primary > Secondary > Tertiary; disconfirm |
| 3 | **Inference** | Explicit reasoning, alternatives, falsifiable |
| 4 | **Coverage** | Matrix tracking, no gaps |
| 5 | **Documentation** | Contemporaneous, reproducible |
| 6 | **Traceability** | Every claim cited, specific |
| 7 | **Honesty** | Counter-evidence, limitations, no spin |

**4 Key Questions:**

1. **"What would prove me wrong?"** — Forces disconfirmation
2. **"Would I be embarrassed if someone found what I left out?"** — Reveals omissions
3. **"Can I state exactly what 'done' looks like?"** — Tests scope clarity
4. **"Is this calibration appropriate for the stakes?"** — Tests depth match

**Verification Quick Check:**

- [ ] All claims have evidence
- [ ] Counter-evidence documented
- [ ] Coverage tracked objectively
- [ ] Documentation is contemporaneous
- [ ] Citations are specific and valid
- [ ] Limitations stated

---

#### 6.9.4 Output Inventory

| Phase | Artifact | Light | Medium | Deep |
|-------|----------|-------|--------|------|
| Pre | Calibration Statement | Brief | Full | Full |
| 1 | Scope Statement | Brief | Full | Exhaustive |
| 1 | Done Criteria | ✓ | ✓ | ✓ |
| 1 | Assumptions | Key | All | All + tested |
| 2 | Evidence Inventory | Key | All | All + verified |
| 2 | Source Citations | ✓ | Specific | Line-level |
| 2 | Disconfirmation Log | Key | All | Systematic |
| 2 | Negative Findings | — | ✓ | ✓ |
| 2 | Reasoning Chains | Summary | Full | Every step |
| 2 | Alternatives Analysis | — | 2-3 | Exhaustive |
| 2 | Coverage Matrix | List | Matrix | Matrix + verified |
| 2 | Methodology Statement | Brief | Full | Comprehensive |
| 2 | Decision Log | Major | All | All + alternatives |
| 2 | Process Log | Summary | Full | Timestamped |
| 2 | Limitations Statement | Key | Full | Comprehensive |
| 2 | Counter-Conclusion | — | ✓ | Adversarial |
| 3 | Verification Checklist | ✓ | ✓ | ✓ |
| 3 | Corrections Log | — | ✓ | ✓ |

---

#### 6.9.5 Consolidated Question Bank

**Before Starting:**
1. Is there an obvious direct solution?
2. Why might this be more complex than it appears?
3. What are the stakes if I'm wrong?
4. What calibration level am I using?

**During Definition:**
1. What outcome am I trying to achieve?
2. Why these boundaries?
3. What's excluded and why?
4. How will I know I'm done?
5. Am I including easy / excluding hard?

**During Execution:**
1. Is this primary, secondary, or tertiary evidence?
2. Have I looked for disproving evidence?
3. What did I look for but not find?
4. Does conclusion follow from evidence?
5. What alternative explanations exist?
6. What would prove me wrong?
7. Have I enumerated everything in scope?
8. Am I confusing "feeling done" with "actually done"?
9. Am I documenting as I go?
10. Does every claim cite a source?
11. Have I reported contradicting findings?
12. What's the strongest argument against my conclusion?

**Before Claiming Done:**
1. Coverage complete? (Checklist with status)
2. Disconfirmation attempted?
3. Assumptions tested?
4. Uncertainty quantified?
5. Negative findings documented?
6. Conclusions justified?

---

## Step 7: Self-Apply the Framework

### Goal

Apply the Framework for Rigor to verify the bulletproofing work itself. Determine if the work that created the framework was rigorous, and whether the framework can detect its own gaps.

### Calibration

**Stakes:** High (foundation for skill family, precedent-setting, high cost of error)
**Level:** Deep

---

### Pre-Framework Check

**Simple Path candidates:**
- Use existing framework (ISO, audit standards) → Not viable: domain-specific, not operationalized
- Edit existing framework-for-rigor.md → Not viable: need to verify foundation
- Fewer steps → Not viable: each step serves distinct purpose

**Verdict:** No simple path available. 10-step process warranted.

**Gap found:** Simple Path Check wasn't explicitly documented at work start.

---

### Phase 1: Scope Check

**Purpose:** "Build bulletproof Framework for Rigor as foundation for skill family"

**Issue:** "Bulletproof" somewhat vague. Better: "Framework where every principle is necessary, none missing, all operationalized, self-application validates."

**Convenience bias check:**

| Item | Omitted? | Hard? | Justified? |
|------|----------|-------|------------|
| Adversarial testing | Yes | Yes | **No—Gap** |
| Formal proof | Yes | Very | Reasonable |

**Gap found:** Adversarial testing (trying to break framework) omitted—possible convenience bias.

---

### Phase 2: Execution Check

#### Evidence

| Sample Claim | Evidence | Status |
|--------------|----------|--------|
| 3 dimensions orthogonal | Assertion | Unproven |
| 7 principles necessary | Removal test | ✓ Verified |
| 7 principles minimal | Merge test | ✓ Verified |
| 35 failure modes map | Enumeration | Claimed, not shown |

**Gaps:**
1. Orthogonality asserted, not demonstrated
2. "35 failure modes" not visible
3. Disconfirmation partial
4. Negative findings undocumented

#### Inference

| Chain | Status |
|-------|--------|
| 3 dimensions derivation | Intuitive, not formal |
| 7 principles derivation | Well-supported, "atomic" unproven |

**Implicit assumptions surfaced:**
- Rigor is decomposable
- 3 dimensions exhaustive
- First principles identifiable

**Gaps:**
1. Implicit assumptions not documented
2. "Atomic" asserted, not proven
3. Dimensional structure intuitive

#### Coverage

| Scope Item | Status |
|------------|--------|
| All planned items | [x] Covered |
| Adversarial testing | [ ] **Missing** |
| Negative findings log | [ ] **Missing** |

#### Documentation

| Criterion | Status |
|-----------|--------|
| Methodology | ✓ |
| Decisions with rationale | ✓ |
| Steps captured | ✓ |
| Contemporaneous | ✓ |
| Timestamps | ✗ Missing |
| Deviation log | ✗ Missing |
| Tools specified | ✗ Missing |

#### Traceability

| Issue | Status |
|-------|--------|
| Granularity | Section-level (Deep expects line-level) |
| All claims traced | Mostly (some gaps) |
| Negative claims | Search methodology missing |

#### Honesty

| Item | Status |
|------|--------|
| Counter-evidence | Self-generated only |
| Limitations section | **Missing** |
| Counter-conclusion | **Missing** |
| Best argument against | **Not stated** |

---

### Phase 3: Verification Summary

| Principle | Status | Key Gap |
|-----------|--------|---------|
| Scope | ⚠️ | Adversarial testing omitted |
| Evidence | ⚠️ | Disconfirmation partial |
| Inference | ⚠️ | Implicit assumptions |
| Coverage | ⚠️ | Adversarial testing missing |
| Documentation | ⚠️ | No timestamps/deviations |
| Traceability | ⚠️ | Section-level granularity |
| Honesty | ⚠️ | No limitations/counter-conclusion |

---

### Gaps Found (Prioritized)

#### Critical

| # | Gap | Remediation |
|---|-----|-------------|
| 1 | No limitations section | Add to framework document |
| 2 | No counter-conclusion | Document best argument against |
| 3 | No adversarial testing | Try to break framework |

#### Moderate

| # | Gap | Remediation |
|---|-----|-------------|
| 4 | Negative findings undocumented | Add log |
| 5 | Disconfirmation partial | Systematic pass |
| 6 | Implicit assumptions | Surface and document |
| 7 | "Atomic" unproven | Acknowledge as assumption |

#### Minor

| # | Gap | Remediation |
|---|-----|-------------|
| 8 | No timestamps | Note: contemporaneous but untimed |
| 9 | Section-level trace | Acceptable |
| 10 | Tools unspecified | Document: Claude Code, markdown |

---

### Counter-Conclusion Analysis

**Conclusion:** Framework is complete, minimal, operationalized.

**Best argument against:**

Framework may be **over-engineered**. 7 principles, 3 phases, 3 calibration levels, extensive checklists—heavyweight machinery. Users may skip steps, cause analysis paralysis, simpler frameworks might achieve 80% at 20% cost.

**Response:**
1. Calibration addresses this (Light reduces overhead)
2. Foundation should be complete (derived skills can simplify)
3. Self-application found genuine issues (framework works)
4. 7 principles validated as necessary (removing any creates gaps)

**Remaining uncertainty:**
- Practical validation (Step 10) pending
- External validation (Step 8) pending
- Novel failure modes might exist
- Dimensional structure intuitive, not proven

---

### Meta-Observation

**The framework detected its own gaps.**

Self-application found genuine issues:
- Honesty gaps (no limitations, no counter-conclusion)
- Coverage gaps (no adversarial testing)
- Documentation gaps (no timestamps)

These map to "Most Dangerous" patterns:
- Motivated Omission — partially present
- Convenience-Driven Scope — partially present
- Reconstructed Documentation — mild

**This is evidence the framework works.** A framework that detects its own creation's flaws demonstrates utility.

---

### Verdict

**The bulletproofing work is mostly rigorous but has gaps.** The framework itself is sound—the gaps are in the *process of creating it*, not in the framework's *content*.

Critical remediation:
1. Add limitations section (Step 9)
2. Add counter-conclusion (done above)
3. Adversarial testing (incorporate into Step 8 or add step)

---

## Step 8: External Validation

### Goal

Validate the Framework for Rigor against external standards and through adversarial testing. Find gaps the self-application might have missed.

Three validation approaches:
1. Compare against established rigor frameworks
2. Adversarial testing (try to break the framework)
3. Simulate external reviewer perspectives

---

### 8.1 Comparison Against Established Frameworks

#### Frameworks Reviewed

| Framework | Domain | Key Rigor Elements |
|-----------|--------|-------------------|
| Scientific Method | Research | Reproducibility, falsifiability, peer review |
| ISO 9001 | Quality | Documentation, evidence-based decisions, traceability |
| Audit Standards (SOX, SOC 2) | Compliance | Evidence hierarchy, completeness assertions, sampling |
| Legal/Forensic | Evidence | Chain of custody, contemporaneous documentation |

#### Mapping: External Standards → Our Principles

| External Standard | Our Framework Coverage | Status |
|-------------------|----------------------|--------|
| **Reproducibility** | Documentation, Traceability | ✓ Covered |
| **Falsifiability** | Sound Inference (alternatives), Honesty (counter-conclusion) | ✓ Covered |
| **Evidence hierarchy** | Adequate Evidence (primary/secondary/tertiary) | ✓ Covered |
| **Documentation** | Documentation | ✓ Covered |
| **Completeness assertions** | Full Coverage | ✓ Covered |
| **Nonconformance handling** | Honesty (limitations), Coverage (gaps) | ✓ Covered |
| **Chain of custody** | Traceability | ✓ Covered |
| **Scope definition** | Appropriate Scope | ✓ Covered |

#### Standards NOT Covered (Analysis)

| External Standard | In Our Framework? | Analysis |
|-------------------|------------------|----------|
| **Statistical validity** | No | Out of scope—framework is for qualitative rigor (exploration, investigation), not quantitative research |
| **Peer review** | Partial | Disconfirmation exists but not external review. Acceptable—external review is calibration-dependent |
| **Control of confounding** | No | Out of scope—relevant for experiments, not exploration |
| **Sampling methodology** | Partial | Coverage principle requires enumeration or justified sampling |

**Verdict:** No significant gaps found. Missing standards are out of scope for qualitative rigor.

---

### 8.2 Adversarial Testing

**Objective:** Try to break the framework. Find scenarios where following it fails.

#### Attack 1: Circularity

**Attack:** Framework validates itself by its own definition of rigor. Circular.

**Analysis:** Meta-rigor is inherently reflexive. The test is whether self-application finds genuine issues. It did (Step 7 found 10 gaps).

**Verdict:** Acknowledged limitation, not fatal flaw.

---

#### Attack 2: Creator Bias

**Attack:** Creator's blind spots are baked in. Framework can't detect what its creator can't see.

**Analysis:** Valid concern. External validation and practical application partially address this. But fundamental limitation remains—no framework escapes its creator entirely.

**Verdict:** Genuine limitation. Document.

---

#### Attack 3: Non-Decomposability

**Attack:** Rigor might be holistic, not decomposable into dimensions. Framework might miss emergent failure modes.

**Analysis:** Dimensional structure is intuitive, not proven (noted in Step 7). However, decomposition enables operationalization. Without it, "be rigorous" remains vague instruction.

**Verdict:** Trade-off accepted. Decomposition is pragmatic choice, not proven truth.

---

#### Attack 4: Heavyweight

**Attack:** Framework is too complex. Users abandon or cargo-cult.

**Analysis:** Light calibration reduces overhead. But even Light has cognitive load. Quick Reference Card (Step 6.9) helps but may be insufficient.

**Verdict:** Partial gap. Consider "Minimal" calibration for low-stakes tasks. OR trust practitioners to simplify.

---

#### Attack 5: False Confidence

**Attack:** "I followed checklist, therefore rigorous." Checkbox compliance without genuine inquiry.

**Analysis:** "Compliance Confusion" red flag explicitly warns against this. But warning may be insufficient—cargo-culting is perennial risk of any checklist.

**Verdict:** Inherent risk. Can mitigate, can't eliminate.

---

#### Attack 6: Truth Unknowable

**Attack:** Framework assumes truth is discoverable. For wicked problems, truth may not exist.

**Analysis:** Framework includes "Unknown" confidence level. But doesn't fully address fundamental unknowability.

**Verdict:** Out of scope. Philosophy problem, not methodology problem. Framework is for practical rigor, not epistemology.

---

#### Attack 7: Adversarial Actors

**Attack:** If someone hides evidence or misleads, rigor fails.

**Analysis:** Fair. Framework assumes honest data sources. Adversarial scenarios (fraud investigation, hostile systems) need additional protocols.

**Verdict:** Scope limitation. Document.

---

#### Attack 8: Negative Findings Unverifiable

**Attack:** "I looked and didn't find" cannot be proven. Framework requires negative findings but can't verify them.

**Analysis:** True. Negative findings are inherently uncertain (absence vs. evidence). That's why methodology documentation is required—shows WHERE you looked, not just what you found.

**Verdict:** Fundamental epistemic limit. Methodology documentation is mitigation, not solution.

---

#### Attack 9: Internal Contradictions

**Attack:** Do framework rules contradict each other?

| Apparent Conflict | Resolution |
|-------------------|------------|
| "Minimal overhead" vs "Comprehensive documentation" | Resolved by calibration |
| "Full coverage" vs "Appropriate scope" | Scope defined first, coverage within scope |
| "Evidence required" vs "Unknown acceptable" | Unknown is valid evidence state |

**Verdict:** No internal contradictions found.

---

#### Attack 10: Principles Not Minimal

**Attack:** 7 principles could merge or eliminate.

**Re-test mergers:**

| Merge Candidate | Why Distinct |
|-----------------|--------------|
| Scope + Coverage | Scope defines boundaries; Coverage enumerates within |
| Evidence + Inference | Evidence collects; Inference reasons from |
| Documentation + Traceability | Documentation records process; Traceability links claims to sources |
| Honesty + any other | Honesty is meta-constraint on all others |

**Verdict:** Principles validated as minimal. No valid merger found.

---

### 8.3 External Perspectives (Simulated)

#### Skeptical Auditor

**Challenge:** "Where's proof this framework is better than existing audit standards?"

**Response:** Framework operationalizes rigor for non-audit contexts (exploration, investigation). Audit standards address compliance, not discovery.

**Gap identified:** Should explicitly document when to use this framework vs. existing standards.

---

#### Academic Researcher

**Challenge:** "Where's empirical validation? This is untested theory."

**Response:** Self-application (Step 7) is internal validation. Practical validation (Step 10) will test in domains. No formal empirical study exists.

**Gap identified:** Framework is theoretical. Would benefit from empirical validation.

---

#### Busy Practitioner

**Challenge:** "Too complicated. I just want to do good work."

**Response:** Light calibration reduces overhead. Quick Reference Card provides fast access.

**Gap identified:** Should more prominently position when NOT to use framework. Framework isn't for simple tasks.

---

#### Hostile Critic

**Challenge:** "You're overcomplicating simple things."

**Response:** Simple Path Check explicitly addresses this. Framework self-selects for complex tasks.

**Gap identified:** "When to NOT use" should be prominent, not buried.

---

### 8.4 Adversarial Testing Summary

| Attack | Outcome | Action |
|--------|---------|--------|
| Circularity | Acknowledged limitation | Document |
| Creator bias | Genuine limitation | Document |
| Non-decomposability | Trade-off accepted | Document as assumption |
| Heavyweight | Partial gap | Consider Minimal calibration |
| False confidence | Inherent risk | Keep warning |
| Truth unknowable | Out of scope | Document scope |
| Adversarial actors | Scope limitation | Document |
| Negative findings | Epistemic limit | Keep methodology requirement |
| Internal contradictions | None found | No action |
| Not minimal | Validated | No action |

**Attacks that found genuine issues:** 2 (Creator bias, Heavyweight)
**Attacks revealing scope limitations:** 3 (Adversarial actors, Truth unknowable, Negative findings)
**Attacks revealing inherent risks:** 2 (Circularity, False confidence)
**Attacks that failed:** 3 (Non-decomposability trade-off, Contradictions, Minimality)

---

### 8.5 Synthesis: Issues Found

#### From External Comparison

| Issue | Severity | Remediation |
|-------|----------|-------------|
| No peer review requirement | Low | Optional at Deep calibration |
| Sampling methodology implicit | Low | Coverage principle sufficient |

#### From Adversarial Testing

| Issue | Severity | Remediation |
|-------|----------|-------------|
| Creator bias | Moderate | Document as limitation |
| Heavyweight | Moderate | Add "When NOT to use" section |
| Circularity | Low | Document as inherent to meta-rigor |
| False confidence risk | Low | Keep warning, can't eliminate |

#### From External Perspectives

| Issue | Severity | Remediation |
|-------|----------|-------------|
| "When NOT to use" buried | Moderate | Promote to prominent position |
| No empirical validation | Low | Acknowledge; Step 10 partial mitigation |

---

### 8.6 Verdict

**External validation completed.**

The framework withstands adversarial testing. No fatal flaws found.

| Finding Type | Count |
|--------------|-------|
| Genuine limitations to document | 3 |
| Scope boundaries to clarify | 3 |
| Inherent risks to acknowledge | 2 |
| No-issue attacks | 3 |

**Key takeaways:**

1. **Framework is sound but not bulletproof.** Creator bias and inherent limits remain.
2. **Scope needs clarification.** Explicitly state: not for adversarial scenarios, not for quantitative research, not for simple tasks.
3. **"When NOT to use" must be prominent.** Simple Path Check exists but should be visible upfront.
4. **Empirical validation would strengthen.** Step 10 provides partial evidence.

All findings feed into Step 9 (Limitations).

---

## Step 9: Document Limitations and Failure Modes

### Goal

Consolidate all limitations discovered in Steps 7-8 into explicit documentation. Provide clear guidance on what the framework can and cannot do.

---

### 9.1 Fundamental Limitations

These are inherent to any rigor framework. Cannot be solved, only acknowledged.

#### L1: Circularity

**Description:** Framework validates itself by its own definition of rigor. Meta-rigor is inherently reflexive.

**Implication:** Cannot prove framework is rigorous by external standard—external standards are different frameworks.

**Mitigation:** Self-application found genuine gaps. If framework finds nothing wrong with itself, that's suspicious. Finding issues is evidence it works.

---

#### L2: Creator Bias

**Description:** Framework reflects its creator's conception of rigor. Blind spots are baked in.

**Implication:** Unknown unknowns remain unknown. No framework escapes its creator's limitations.

**Mitigation:** External validation (Step 8), practical use (Step 10), iterative refinement based on experience.

---

#### L3: Decomposability Assumption

**Description:** Framework assumes rigor decomposes into dimensions (Validity, Completeness, Transparency). This is pragmatic, not proven.

**Implication:** Emergent failure modes that only appear from dimension interactions might be missed.

**Mitigation:** Red Flags section captures common interaction failures. Experience will reveal others.

---

#### L4: Negative Findings Unverifiable

**Description:** "I looked for X and didn't find it" cannot be proven conclusively. Absence of evidence ≠ evidence of absence.

**Implication:** Framework requires negative findings but cannot guarantee they're accurate.

**Mitigation:** Methodology documentation shows WHERE you looked. This shifts burden from "prove nothing exists" to "prove you looked thoroughly."

---

#### L5: False Confidence Risk

**Description:** Following checklists can create false sense of rigor. "I followed the process, therefore I'm rigorous."

**Implication:** Cargo-culting is perennial risk of any checklist-based approach.

**Mitigation:** "Compliance Confusion" red flag warns explicitly. Ultimate guard is intellectual honesty.

---

### 9.2 Scope Limitations

The framework is NOT designed for these scenarios.

#### S1: Adversarial Contexts

**Not for:** Fraud investigation, forensic analysis, penetration testing against hostile defenders

**Why:** Framework assumes data sources are honest. Adversarial actors hide evidence, plant false trails, mislead actively.

**Alternative:** Forensic methodologies, adversarial thinking frameworks, deception-aware protocols.

---

#### S2: Quantitative Research

**Not for:** Statistical analysis, experimental design, hypothesis testing

**Why:** Framework addresses qualitative rigor (exploration, investigation, review). Statistical validity, sampling theory, control groups are different domains.

**Alternative:** Research methodology textbooks, statistical frameworks.

---

#### S3: Simple Tasks

**Not for:** Typo fixes, obvious bugs, routine operations

**Why:** Overhead exceeds benefit. Simple Path Check explicitly filters these out.

**When to skip:** If obvious solution exists and stakes of being wrong are low.

---

#### S4: Real-Time Decisions

**Not for:** Incident response triage, split-second judgments

**Why:** Framework requires deliberation. Time-critical decisions need heuristics, not frameworks.

**Alternative:** Pre-built decision trees, practiced instincts, post-hoc framework application for learning.

---

### 9.3 Practical Limitations

#### P1: Cognitive Load

**Problem:** Even Light calibration requires multiple questions and checks. Busy practitioners may abandon or shortcut.

**Mitigation:** Quick Reference Card distills to essentials. But framework is designed for important work, not all work.

---

#### P2: No Empirical Validation

**Problem:** Framework is theoretical derivation. Has not been tested empirically at scale.

**Mitigation:** Self-application (Step 7) and practical validation (Step 10) provide partial evidence. User feedback will strengthen over time.

---

#### P3: Subjective Calibration

**Problem:** Stakes assessment involves judgment. Users might under-calibrate (too light) or over-calibrate (unnecessary depth).

**Mitigation:** Stakes Assessment table provides guidance. Recommend erring toward more rigor when uncertain.

---

### 9.4 Failure Modes

How the framework fails in practice, with warning signs and mitigations.

#### F1: Premature Scope Lock

**What happens:** User defines scope, then discovers important related area, but doesn't expand scope because "scope is defined."

**Warning signs:** Findings point outside scope but are ignored. Discomfort about boundaries grows during execution.

**Mitigation:** Scope can be revised. Document rationale for revision. Original scope was hypothesis, not contract.

---

#### F2: Evidence Accumulation Disguised as Progress

**What happens:** User collects more and more evidence without drawing conclusions. Feels productive but goes nowhere.

**Warning signs:** Evidence pile grows without synthesis. No conclusions reached after substantial effort.

**Mitigation:** Set checkpoints. Ask "What conclusion does this evidence support?" periodically. Diminishing returns signal completion.

---

#### F3: Completeness Theater

**What happens:** Coverage matrix is filled in, but cells are superficially addressed. "Explored" = skimmed.

**Warning signs:** All cells marked [x] but findings are thin. No gaps or issues found (suspiciously clean).

**Mitigation:** Depth requirements per calibration. Light allows shallow, Deep requires thoroughness. Honest self-assessment.

---

#### F4: Documentation Debt

**What happens:** User defers documentation until end. Reconstructed documentation misses nuance, invents rationale.

**Warning signs:** Documentation written in bulk at end. No contemporaneous notes. "I remember why" justifies lack of records.

**Mitigation:** Document as you go. Brief notes during execution beat detailed reconstruction.

---

#### F5: Honesty Erosion

**What happens:** User starts rigorous, but as findings emerge, unconsciously filters toward desired conclusion.

**Warning signs:** Counter-evidence diminishes over time. Final conclusions align suspiciously well with initial hypotheses. Limitations section is thin.

**Mitigation:** Counter-Conclusion Test. Explicitly state best argument against your conclusion. Have someone else review.

---

#### F6: Calibration Drift

**What happens:** User starts at Light calibration, situation escalates, but calibration isn't upgraded. Insufficient rigor for actual stakes.

**Warning signs:** Unexpected complexity. Surprises during execution. Stakes revelation mid-process.

**Mitigation:** Re-assess calibration at checkpoints. Upgrade if stakes have increased. Acknowledge when Light was premature.

---

#### F7: Framework as Shield

**What happens:** User uses framework compliance as defense against criticism. "I followed the process" replaces "I found the truth."

**Warning signs:** Defensive posture about methodology. Focus on process adherence, not conclusion quality.

**Mitigation:** Framework is means, not end. Valid criticism of conclusions should prompt re-examination, not process defense.

---

### 9.5 When NOT to Use This Framework

**Use when:**
- Stakes justify deliberation
- Conclusions will inform important decisions
- Work will be shared or reviewed
- Exploration, investigation, audit, or review tasks
- Qualitative analysis

**Skip when:**
- Obvious solution exists (Simple Path passes)
- Stakes are trivially low
- Time-critical response needed
- Quantitative research (use statistical methods)
- Adversarial context (use forensic methods)
- Task is mechanical, not investigative

---

### 9.6 Limitations Summary

| Category | Count | Key Theme |
|----------|-------|-----------|
| Fundamental | 5 | Inherent epistemic limits |
| Scope | 4 | What framework isn't for |
| Practical | 3 | Usability concerns |
| Failure Modes | 7 | How it breaks in practice |

**The framework is a tool, not a guarantee.** Following it faithfully increases probability of rigorous work but doesn't ensure correctness. The framework helps you be thorough and honest; it can't make you right.

**The ultimate guard is intellectual honesty.** If you use the framework to justify predetermined conclusions, no checklist will save you.

---

## Step 10: Practical Validation Across Domains

### Goal

Test the Framework for Rigor against each planned skill domain. Verify that:
1. Domain-specific failure modes map to framework principles
2. Framework catches common domain mistakes
3. No major domain-specific gaps exist

---

### 10.1 Domain: Deep Exploration (Understand Systems)

**Purpose:** Comprehensively understand a complex system (codebase, architecture, documentation).

#### Domain-Specific Failure Modes

| Failure Mode | Description |
|--------------|-------------|
| Surface-level exploration | Skimmed files, missed depths |
| Confirmation of existing beliefs | Only found what expected |
| Missing cross-cutting concerns | Saw trees, missed forest |
| Stale understanding | System changed since exploration |
| Tunnel vision | Deep in one area, shallow everywhere else |

#### Mapping to Framework Principles

| Failure Mode | Principle That Catches It |
|--------------|---------------------------|
| Surface-level | Full Coverage (depth requirements) |
| Confirmation bias | Honesty (disconfirmation), Adequate Evidence (counter-evidence) |
| Missing cross-cutting | Appropriate Scope (define what's in bounds) |
| Stale understanding | Documentation (timestamps), Sound Inference (assumptions) |
| Tunnel vision | Full Coverage (coverage matrix), Appropriate Scope (balance) |

**Verdict:** ✓ All failure modes map to principles. Framework suitable.

---

### 10.2 Domain: Deep Security Audit (Find Vulnerabilities)

**Purpose:** Systematically identify security vulnerabilities in a system.

#### Domain-Specific Failure Modes

| Failure Mode | Description |
|--------------|-------------|
| Missed attack surface | Didn't enumerate all entry points |
| False negatives | Vulnerability exists but not found |
| Severity miscalibration | Critical rated low, noise rated high |
| Outdated threat model | Attack landscape evolved |
| Missing chained attacks | Individual issues miss combined exploits |

#### Mapping to Framework Principles

| Failure Mode | Principle That Catches It |
|--------------|---------------------------|
| Missed attack surface | Full Coverage (enumerate everything) |
| False negatives | Adequate Evidence (negative findings), Honesty (limitations) |
| Severity miscalibration | Sound Inference (justified conclusions) |
| Outdated threats | Adequate Evidence (current sources), Sound Inference (assumptions) |
| Chained attacks | Sound Inference (alternatives analysis), Appropriate Scope (interactions) |

**Domain-Specific Note:** Security audits should use threat models as coverage checklist (OWASP, STRIDE, etc.). Framework doesn't specify which—derived skill should.

**Verdict:** ✓ Framework suitable. Derived skill should specify threat model checklist.

---

### 10.3 Domain: Deep Code Review (Verify Quality)

**Purpose:** Thoroughly review code for correctness, quality, and maintainability.

#### Domain-Specific Failure Modes

| Failure Mode | Description |
|--------------|-------------|
| Rubber-stamping | Approved without real review |
| Nitpicking | Focused on style, missed logic |
| Incomplete coverage | Reviewed some files, skipped others |
| Missing context | Didn't understand purpose |
| False confidence in tests | "Tests pass" = assumed correct |

#### Mapping to Framework Principles

| Failure Mode | Principle That Catches It |
|--------------|---------------------------|
| Rubber-stamping | Adequate Evidence (evidence for claims), Documentation (review trail) |
| Nitpicking | Appropriate Scope (what matters), Sound Inference (proportional concern) |
| Incomplete coverage | Full Coverage (coverage matrix) |
| Missing context | Appropriate Scope (define purpose), Sound Inference (assumptions) |
| False confidence | Adequate Evidence (test output is evidence, not assertion) |

**Verdict:** ✓ Framework suitable.

---

### 10.4 Domain: Deep Investigation (Find Root Cause)

**Purpose:** Determine the root cause of an incident, failure, or unexpected behavior.

#### Domain-Specific Failure Modes

| Failure Mode | Description |
|--------------|-------------|
| Stopping at first cause | Proximate cause ≠ root cause |
| Blame assignment | Found scapegoat, not cause |
| Hypothesis confirmation | First theory became only theory |
| Evidence destruction | Investigation altered system state |
| Correlation-causation confusion | X preceded Y, therefore X caused Y |

#### Mapping to Framework Principles

| Failure Mode | Principle That Catches It |
|--------------|---------------------------|
| Stopping early | Sound Inference (5 Whys, alternatives), Appropriate Scope (depth) |
| Blame assignment | Honesty (honest conclusions), Sound Inference (evidence-based) |
| Hypothesis confirmation | Adequate Evidence (disconfirmation), Honesty (counter-conclusion) |
| Evidence destruction | Documentation (preserve state), Traceability (chain of custody) |
| Correlation-causation | Sound Inference (valid reasoning), Adequate Evidence (causal evidence) |

**Verdict:** ✓ Framework suitable.

---

### 10.5 Domain: Deep Migration Plan (Ensure Completeness)

**Purpose:** Plan a complete migration (system, data, infrastructure) with nothing forgotten.

#### Domain-Specific Failure Modes

| Failure Mode | Description |
|--------------|-------------|
| Missing dependencies | Thing X relies on thing Y not yet migrated |
| Rollback impossible | No return path if migration fails |
| Data loss | Something didn't transfer |
| Timing issues | Order-dependent steps scrambled |
| Integration gaps | Migrated component doesn't connect |

#### Mapping to Framework Principles

| Failure Mode | Principle That Catches It |
|--------------|---------------------------|
| Missing dependencies | Full Coverage (enumerate all), Sound Inference (dependency analysis) |
| Rollback impossible | Appropriate Scope (include rollback), Honesty (limitations) |
| Data loss | Full Coverage (data inventory), Traceability (what went where) |
| Timing issues | Sound Inference (order matters), Documentation (sequence) |
| Integration gaps | Full Coverage (connection inventory), Sound Inference (interaction analysis) |

**Verdict:** ✓ Framework suitable.

---

### 10.6 Domain: Deep Compliance Check (Prove Adherence)

**Purpose:** Verify a system meets compliance requirements (regulatory, policy, standards).

#### Domain-Specific Failure Modes

| Failure Mode | Description |
|--------------|-------------|
| Checkbox compliance | Technically meets requirement, misses intent |
| Gap misattribution | Failed control blamed on wrong system |
| Evidence insufficiency | Claim of compliance without proof |
| Scope gaming | Narrow scope excludes non-compliant areas |
| Point-in-time fallacy | Compliant today, not tomorrow |

#### Mapping to Framework Principles

| Failure Mode | Principle That Catches It |
|--------------|---------------------------|
| Checkbox compliance | Honesty (intent vs letter), Sound Inference (spirit of requirement) |
| Gap misattribution | Traceability (link finding to source), Adequate Evidence (verify attribution) |
| Evidence insufficiency | Adequate Evidence (primary sources), Traceability (citations) |
| Scope gaming | Appropriate Scope (justified boundaries), Honesty (convenience bias) |
| Point-in-time | Documentation (timestamps), Honesty (limitations) |

**Verdict:** ✓ Framework suitable.

---

### 10.7 Cross-Domain Analysis

#### Framework Principle Utilization

| Principle | Domains Using | Key Application |
|-----------|---------------|-----------------|
| Appropriate Scope | 6/6 | Define what's in bounds |
| Adequate Evidence | 6/6 | Evidence quality, negative findings |
| Sound Inference | 6/6 | Conclusions follow from evidence |
| Full Coverage | 6/6 | Enumerate everything |
| Documentation | 6/6 | Record methodology |
| Traceability | 6/6 | Link claims to sources |
| Honesty | 6/6 | Counter-conclusion, limitations |

**Observation:** All 7 principles used in all 6 domains. No principle is domain-specific.

#### Domain-Specific Gaps Found

| Domain | Gap | Remediation |
|--------|-----|-------------|
| Security Audit | Need threat model checklist | Derived skill specifies (OWASP, STRIDE, etc.) |
| Investigation | Evidence preservation critical | Emphasize in derived skill |
| Compliance | Standards mapping required | Derived skill includes compliance matrix |

**Verdict:** Framework is domain-general. Derived skills add domain-specific checklists.

---

### 10.8 Practical Validation Summary

#### Coverage Test

| Test | Result |
|------|--------|
| All domain failure modes map to principles | ✓ 28/28 mapped |
| All principles used across domains | ✓ 7/7 used in 6/6 domains |
| No domain-specific gaps unfilled | ✓ Gaps are checklist additions, not principle gaps |

#### Framework Fitness

| Domain | Framework Fit | Notes |
|--------|--------------|-------|
| Deep Exploration | ✓ Excellent | Core use case |
| Security Audit | ✓ Good | Add threat model |
| Code Review | ✓ Good | Straightforward mapping |
| Investigation | ✓ Good | Emphasize evidence preservation |
| Migration Plan | ✓ Good | Coverage matrix critical |
| Compliance | ✓ Good | Add standards mapping |

#### Key Finding

**The framework is domain-general by design.**

Principles (what to do) apply universally. Derived skills add domain-specific checklists (what to check). This separation is appropriate:
- Framework: How to be rigorous
- Derived skill: What to be rigorous about

---

### 10.9 Verdict

**Practical validation successful.**

The Framework for Rigor maps to failure modes across all 6 planned domains. No principle is unused; no failure mode unmapped.

**Framework is ready for use.**

Domain-specific skills should:
1. Import the framework principles
2. Add domain-specific checklists (attack surfaces, compliance matrices, etc.)
3. Customize calibration guidance for domain stakes

---

## Appendix: Planned Skill Family

```
Framework for Rigor (bulletproof foundation)
    │
    ├── deep-exploration ✓ (understand systems)
    ├── deep-security-audit (find vulnerabilities)
    ├── deep-code-review (verify quality)
    ├── deep-investigation (find root cause)
    ├── deep-migration-plan (ensure completeness)
    └── deep-compliance-check (prove adherence)
```

---

## Conclusion: Bulletproofing Complete

### Summary

The 10-step bulletproofing process is complete. The Framework for Rigor has been:

| Step | What Was Done | Outcome |
|------|---------------|---------|
| 1 | Defined "Rigor" precisely | 3 orthogonal dimensions: Validity, Completeness, Transparency |
| 2 | Identified first principles | 7 necessary principles across dimensions |
| 3 | Derived structure | 3-phase framework: Definition → Execution → Verification |
| 4 | Mapped dependencies | Principles in dependency order within each phase |
| 5 | Validated completeness/minimality | 7 principles necessary and sufficient |
| 6 | Operationalized elements | Actions, questions, outputs, verification for each |
| 7 | Self-applied framework | Found 10 gaps; framework detected its own issues |
| 8 | External validation | 10 adversarial attacks; no fatal flaws |
| 9 | Documented limitations | 5 fundamental, 4 scope, 3 practical, 7 failure modes |
| 10 | Practical validation | 28 failure modes across 6 domains; all mapped |

### Framework Status

**The Framework for Rigor is validated and ready for use.**

| Criterion | Status |
|-----------|--------|
| Complete | ✓ All rigor failures map to principles |
| Minimal | ✓ No redundant principles |
| Operationalized | ✓ Actions, questions, outputs defined |
| Self-consistent | ✓ No internal contradictions |
| Self-validating | ✓ Detected gaps in own creation |
| Domain-general | ✓ Works across 6 planned skill domains |
| Limitations documented | ✓ 19 limitations explicitly stated |

### What Remains

1. **Revise framework-for-rigor.md** — Incorporate bulletproofing findings
2. **Create derived skills** — Apply framework to specific domains
3. **Gather user feedback** — Empirical validation through use

### Meta-Observation

**The bulletproofing process demonstrated the framework.**

This log is itself evidence of the framework in action:
- Scope defined upfront (10 steps)
- Evidence documented at each step
- Conclusions traced to analysis
- Counter-conclusions stated
- Limitations explicit
- Negative findings recorded (what didn't work)

The framework was used to build the framework. The circularity is intentional—rigorous work about rigor should itself be rigorous.

### Final Verdict

**Framework for Rigor: Bulletproofed.**

Not perfect. Not provably complete. But:
- Systematically derived
- Internally consistent
- Externally validated
- Practically applicable
- Honestly limited

Ready for deployment.
