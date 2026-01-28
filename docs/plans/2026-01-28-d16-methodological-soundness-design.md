# D16: Methodological Soundness — Design Document

## Background

### The reviewing-skills Skill

`reviewing-skills` is a mature skill for reviewing SKILL.md files and their supporting files. It catches document quality issues before behavioral testing (testing-skills), when fixes are cheap.

**Location:** `.claude/skills/reviewing-skills/`

**Files:**
- `SKILL.md` (635 lines) — Main skill definition
- `dimension-definitions.md` (996 lines) — Detailed checking guidance for D1-D15
- `skill-type-adaptation.md` (369 lines) — Type-specific priority adjustments
- `examples.md` (172 lines) — Worked examples (BAD vs GOOD)
- `troubleshooting.md` (64 lines) — Common issues and solutions
- `verification-checklist.md` (62 lines) — Completion verification
- `framework-for-thoroughness.md` (488 lines) — Protocol specification

**Current Dimensions (D1-D15):**

| ID | Dimension | Priority | What it catches |
|----|-----------|----------|-----------------|
| D1 | Trigger clarity | P0 | Vague or overlapping descriptions that cause misfires |
| D2 | Process completeness | P0 | Missing steps, undefined decision points, unclear exit criteria |
| D3 | Structural conformance | P0 | Missing required sections, wrong frontmatter, size limits |
| D4 | Compliance strength | P1 | Weak language, missing rationalization counters |
| D5 | Precision | P1 | Vague wording allowing multiple interpretations |
| D6 | Actionability | P1 | Instructions lacking execution details |
| D7 | Internal consistency | P1 | Contradictions between sections, terminology drift |
| D8 | Scope boundaries | P1 | Missing "When NOT to Use", unclear exclusions |
| D9 | Reference validity | P2 | Broken links, outdated references |
| D10 | Edge cases | P2 | Boundary situations undefined |
| D11 | Feasibility | P2 | Requirements that can't be achieved |
| D12 | Testability | P2 | Requirements that can't be verified |
| D13 | Integration clarity | P1 | Unclear handoffs (orchestration skills only) |
| D14 | Example quality | P1 | Unrealistic or non-diverse examples |
| D15 | Cognitive manageability | P2 | Overwhelms working memory |

**Skill Types Supported:**
1. Process/Workflow
2. Quality Enhancement
3. Capability
4. Solution Development
5. Meta-cognitive
6. Recovery/Resilience
7. Orchestration
8. Template/Generation

**Ecosystem Position:**
- Upstream: `brainstorming-skills` (produces draft SKILL.md)
- Downstream: `testing-skills` (validates behavioral effectiveness)

### The Gap

Current dimensions assess **document quality** — whether a skill is clear, complete, consistent, and compliant. They do not assess **approach validity** — whether the skill teaches the right methodology for the problem it solves.

**A skill could pass all 15 dimensions while teaching an inferior or incorrect approach.**

Examples of what falls through the cracks:
- A TDD skill that recommends writing tests after implementation
- A git workflow skill that contradicts official Git documentation
- A debugging skill that recommends known anti-patterns
- A code review skill with methodology that doesn't match research on effective reviews

This is a serious gap because:
1. **reviewing-skills is invoked frequently** — every skill gets reviewed multiple times
2. **Wrong methodology is worse than unclear documentation** — a well-documented wrong approach is more dangerous than a poorly-documented right approach
3. **Current dimensions can't catch this** — D2 checks "are steps defined?" not "are these the right steps?"

---

## D16: Methodological Soundness — Design Draft

### Core Question

Does the skill teach the *right approach* to the problem, not just a *well-documented* approach?

### What It Catches

| Issue | Example |
|-------|---------|
| Wrong methodology | TDD skill that says "write tests after implementation" |
| Contradicts authoritative sources | Git skill that contradicts official Git documentation |
| Known anti-patterns recommended | Debugging skill that recommends "add print statements everywhere" |
| Approach/goal mismatch | "Fast iteration" skill with heavyweight process |
| Missing rationale | Skill prescribes approach with no "why this way" |

### Distinction from Other Dimensions

| Dimension | What it checks | D16 checks differently |
|-----------|---------------|------------------------|
| D2 (Process Completeness) | Are all steps defined? | Are these the *right* steps? |
| D5 (Precision) | Is language unambiguous? | Is the *content* correct? |
| D6 (Actionability) | Can instructions be executed? | *Should* they be executed this way? |
| D11 (Feasibility) | Can this be done? | Is this the right thing to do? |
| D12 (Testability) | Can we verify completion? | Are we verifying the right thing? |

### How to Check (Without Being a Domain Expert)

The reviewer doesn't need to be a domain expert. Instead, check:

1. **Source alignment:** Does skill cite authoritative sources? Do its instructions match those sources?
2. **Rationale presence:** Does skill explain *why* this approach vs alternatives?
3. **Anti-pattern avoidance:** Search for known anti-patterns in the domain — does skill recommend any?
4. **Goal/approach coherence:** Does the methodology actually achieve the stated goals?
5. **Alternative acknowledgment:** Does skill acknowledge other valid approaches exist?

### Red Flags

- No rationale for approach chosen
- Contradicts official documentation or established standards
- Recommends known anti-patterns
- Claims to be "the only way" without evidence
- Approach doesn't match stated goals
- No citations or references for methodology claims
- Methodology copied from another domain without adaptation

### Good Patterns

- Cites authoritative sources (official docs, research, industry standards)
- Explains why this approach was chosen over alternatives
- Acknowledges limitations and when other approaches might be better
- Methodology matches what experts in the domain recommend
- Approach clearly achieves stated goals

### Proposed Priority by Skill Type

| Skill Type | D16 Priority | Rationale |
|------------|--------------|-----------|
| Process/Workflow | **P0** | Wrong process = wrong outcome |
| Quality Enhancement | **P0** | Wrong criteria = wrong improvements |
| Solution Development | **P0** | Wrong analysis framework = wrong recommendations |
| Capability | P1 | Wrong technique may still partially work |
| Meta-cognitive | P1 | Recognition patterns are harder to "get wrong" |
| Recovery/Resilience | P1 | Recovery approaches vary by context |
| Orchestration | P1 | Coordination logic is less methodology-dependent |
| Template/Generation | P2 | Output format is less about methodology |

### Example Findings

| Finding | Priority | Proposed Fix |
|---------|----------|--------------|
| TDD skill says "write tests after code works" | P0 | Rewrite to test-first approach or rename skill |
| No rationale for chosen methodology | P1 | Add "Why This Approach" section explaining trade-offs |
| Contradicts official Claude Code docs | P0 | Align with official documentation or explain divergence |
| Claims "only correct way" without sources | P1 | Add citations or soften to "recommended approach" |

---

## Implementation Plan

### Files to Modify

| File | Change |
|------|--------|
| `SKILL.md` | Add D16 to Dimension Catalog table (after D15) |
| `dimension-definitions.md` | Add full D16 section (~100 lines) with TOC entry |
| `skill-type-adaptation.md` | Add D16 to Quick Reference Table and type-specific sections |

### Scope

- Add D16 as P1 default, elevated to P0 for Process/Workflow, Quality Enhancement, and Solution Development types
- D16 is always checked (like D1-D8), not conditional (like D13)

---

## Deep Exploration Needed

The draft above identifies the gap but doesn't deeply explore what "methodological soundness" actually means. Before implementation, the next session should explore:

### Foundational Questions

**What does "correct approach" even mean?**
- Is there always a "correct" approach, or just "better/worse" ones?
- How do we distinguish between:
  - Factually wrong (contradicts how things work)
  - Suboptimal (works but inefficient)
  - One of several valid options (matter of preference)
  - Context-dependent (right in some situations, wrong in others)
- What about emerging practices vs established ones? New approaches may be better but lack "authoritative sources."

**The epistemological challenge:**
- How can a reviewer assess methodology correctness without being a domain expert?
- Is this dimension even feasible to check reliably?
- What's the failure mode if D16 can't be checked well? (False confidence? Skipped entirely?)
- Should D16 require the *skill itself* to be self-justifying rather than requiring reviewer expertise?

**What are we actually trying to prevent?**
- Skills that teach objectively wrong things?
- Skills that teach outdated practices?
- Skills that oversimplify and lose important nuance?
- Skills that cargo-cult (follow form without substance)?
- Skills that are context-inappropriate (right technique, wrong situation)?
- All of the above? Some subset?

### Taxonomy of Methodological Issues

Different types of "wrong approach" may need different checking strategies:

| Type | Example | How to detect |
|------|---------|---------------|
| **Factually incorrect** | "Git rebase merges branches" | Cross-reference with authoritative docs |
| **Outdated** | Using deprecated APIs | Check version/date of sources |
| **Oversimplified** | "Always use TDD" without nuance | Look for missing edge cases, caveats |
| **Cargo cult** | Following steps without understanding why | Check if rationale is present |
| **Context-inappropriate** | Heavyweight process for quick fixes | Check if scope/context is defined |
| **Contradicts research** | Code review practices that studies show don't work | Requires domain knowledge or citations |
| **Anti-pattern** | Known bad practices | Requires knowing anti-patterns exist |

Which of these should D16 catch? All? Some? How do we make each checkable?

### The Reviewer Capability Problem

D1-D15 can be checked by any competent reviewer — they're about document quality, not domain expertise. D16 is different: assessing whether TDD is taught correctly requires knowing TDD.

Options to explore:
1. **Require skills to be self-justifying** — Skill must cite sources; reviewer checks skill matches its sources (doesn't require reviewer to know the domain)
2. **Scope D16 narrowly** — Only check for internal coherence (does approach match stated goals?) not external correctness
3. **Make D16 conditional** — Only check when reviewer has domain expertise; otherwise mark "not assessed"
4. **Separate D16 into sub-dimensions** — D16a (internal coherence) always checked; D16b (external correctness) conditional

### Relationship to Skill Types

Does "methodological soundness" mean the same thing for all skill types?

| Skill Type | What would "wrong methodology" look like? |
|------------|------------------------------------------|
| Process/Workflow | Wrong sequence, missing steps, inefficient order |
| Quality Enhancement | Wrong quality criteria, unmeasurable goals |
| Capability | Technique that doesn't achieve the capability |
| Solution Development | Analysis framework that misses important factors |
| Meta-cognitive | Recognition patterns that over/under-trigger |
| Recovery/Resilience | Recovery steps that make things worse |
| Orchestration | Wrong skill sequencing, lost state |
| Template/Generation | Output format that doesn't serve its purpose |

These seem quite different. Should D16 have type-specific guidance like other dimensions?

### Making It Concrete

For D16 to be as useful as D1-D15, we need:
- **Specific red flags** (not just "wrong approach")
- **Checking procedures** (what to do, not just what to look for)
- **Evidence requirements** (what counts as E1, E2, E3 for methodology)
- **Example findings** (realistic BAD/GOOD showing what D16 catches)

The current draft has sketches of these but they're not rigorous enough.

### Risks of Getting D16 Wrong

If D16 is too vague:
- Reviewers skip it ("I don't know enough to assess this")
- Reviewers rubber-stamp it ("looks reasonable to me")
- D16 becomes theater that doesn't catch real issues

If D16 is too strict:
- Valid skills fail because they don't cite enough sources
- Innovation is penalized (new approaches lack authoritative backing)
- Review becomes gatekeeping by "experts"

### Open Questions (Narrower)

1. **Source alignment strictness:** Require citations, or just not contradicting known sources?

2. **Domain expertise fallback:** What should reviewer do when they can't assess methodology?

3. **Contested approaches:** How to handle genuinely debated methodologies?

4. **Anti-pattern discovery:** How should reviewers find domain anti-patterns?

5. **Evidence levels:** What counts as E1/E2/E3 for methodology correctness?

---

## Next Session: Deep Exploration

The next session should focus on **ideation and exploration**, not implementation. Specifically:

1. **Explore the foundational questions** — What does "correct approach" mean? Can this be checked without domain expertise?

2. **Develop the taxonomy** — Which types of methodological issues should D16 catch? How do we check each type?

3. **Solve the reviewer capability problem** — Design a checking approach that doesn't require the reviewer to be a domain expert

4. **Make it concrete** — Draft specific red flags, checking procedures, and example findings that are as rigorous as D1-D15

5. **Stress-test the design** — Apply D16 mentally to several existing skills and see what it would find (or miss)

**Do not implement until the design is rigorous.** A vague D16 is worse than no D16 — it creates false confidence that methodology is being checked when it isn't.

---

## Implementation Status

**Status: IMPLEMENTED** (2026-01-28)

D16 has been formalized and added to reviewing-skills:

### Files Modified

| File | Change |
|------|--------|
| `dimension-definitions.md` | Added D16 entry (~200 lines) with full checking guidance |
| `SKILL.md` | Added D16 to dimension catalog table |
| `skill-type-adaptation.md` | Added D16 to type-specific priority tables (P0 for Process/Quality/Solution, P1/P2 for others) |
| `verification-checklist.md` | Updated "15 dimensions" → "16 dimensions" |

### Design Decisions Made During Exploration

1. **Two-tier structure:** D16 split into D16a (internal validity, always checkable) and D16b (external validity, may need domain search)

2. **Source requirements:** Rationale required, citations recommended but not required. P1 for missing rationale, P2 for "could benefit from sources"

3. **Contested approaches:** Skill can teach one valid approach but cannot claim universality without evidence. Contested approaches should acknowledge debate.

4. **Evidence levels:** D16a requires E1 (step/goal trace), D16b requires E1-E2 depending on finding severity

5. **Priority by type:** P0 for Process/Quality/Solution (wrong methodology = wrong outcome), P1 for Capability/Meta/Recovery/Orchestration, P2 for Template

### Stress Testing Performed

D16 was stress-tested against 9 existing skills:

| Skill | D16a | D16b | Key Finding |
|-------|------|------|-------------|
| brainstorming-skills | PASS | P1 | Strong claim without external evidence |
| writing-clearly-and-concisely | PASS | P2 | Contested rules not acknowledged |
| exploring-codebases | PASS | P2 | Custom methodology |
| making-recommendations | PASS | P2 | No citations |
| reviewing-code | PASS | P2 | Custom dimensions |
| testing-skills | PASS | PASS | Cites TDD and research |
| using-frameworks | PASS | P2 | Custom wrapper |
| ideating-extensions | PASS | P2 | Follows design thinking |
| reviewing-documents | PASS | P2 | Aligns with inspections |

**Calibration validated:** D16a catches hard failures (none found — skills are well-designed). D16b differentiates meaningfully: P1 for strong unjustified claims, P2 for "could strengthen with sources", PASS for actually citing sources.

---

## Additional Enhancements Identified (Future Work)

During this exploration, three other enhancements were identified for reviewing-skills:

1. **Fast Path for Experienced Reviewers** — Condensed checklist for repeat reviewers
2. **Automated Validation** — Hook/script for structural pre-validation
3. **Batch Review & Dependency Tracking** — Guidance for reviewing multiple skills together

These should be designed and implemented separately after D16 is complete.

---

## References

- reviewing-skills SKILL.md: `.claude/skills/reviewing-skills/SKILL.md`
- Recent self-review: `docs/audits/2026-01-28-reviewing-skills-review.md`
- Framework for thoroughness: `.claude/skills/reviewing-skills/framework-for-thoroughness.md`
