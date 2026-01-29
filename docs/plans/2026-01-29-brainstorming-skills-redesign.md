# Brainstorming-Skills Redesign Proposal

**Status:** In review
**Date:** 2026-01-29
**Updated:** 2026-01-29 (content mining complete)

## Design Principles

| Principle | Rationale |
|-----------|-----------|
| **Verification over stability** | Convergence measures stability, not correctness. Test understanding against scenarios, not just "two no-yield rounds." |
| **Early divergence, late convergence** | Explore approaches before committing to deep understanding. Different approaches need different understanding. |
| **Actionable taxonomies only** | If a classification doesn't change behavior, eliminate it. The 8-type taxonomy is post-hoc labeling, not process guidance. |
| **Integrated safeguards** | Build assumption checks into the flow as gates, not as a separate list to remember. |
| **Iteration-aware** | Design for loops back from testing. Define what happens when testing finds issues. |
| **Flexible discipline** | Default rules with explicit escape hatches, not dogmatic "YOU MUST" without exceptions. |

---

## Proposed Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│  PHASE 1: FRAMING (divergent)                                       │
│  - Understand problem space                                         │
│  - Surface 2-3 rough approaches                                     │
│  - DO NOT converge yet                                              │
└─────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────┐
│  PHASE 2: APPROACH SELECTION (narrowing)                            │
│  - Present approaches with trade-offs                               │
│  - User selects (or hybrid)                                         │
│  - Selection determines template AND what understanding is needed   │
└─────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────┐
│  PHASE 3: DEEP UNDERSTANDING (approach-specific)                    │
│  - Cover dimensions relevant to chosen approach                     │
│  - Verify with scenarios, not rounds                                │
│  - Exit when scenarios pass                                         │
└─────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────┐
│  PHASE 4: DESIGN (structured)                                       │
│  - Draft incrementally using selected template                      │
│  - Stress-test design (true adversarial)                            │
│  - Create design context document                                   │
└─────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────┐
│  PHASE 5: HANDOFF (with iteration protocol)                         │
│  - Handoff to testing-skills                                        │
│  - Define return paths based on issue severity                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Framing

**Goal:** Understand the problem space and user context. Surface multiple approaches before committing to any.

**Duration:** 3-5 questions typically. This is exploration, not deep understanding.

### Entry

Check project context first:
- Scan existing skills: `ls .claude/skills/` or Glob for `**/.claude/skills/**/SKILL.md`
- Read project CLAUDE.md for conventions
- Note patterns or standards

If arriving from ideating-extensions: acknowledge the context (problem statement, suggested approach). Don't restart from zero.

### Problem-Space Questions

Focus on the problem, not the solution:

1. **What's broken or missing?** — The problem statement
2. **What happens today that shouldn't?** — Current failure mode
3. **What should happen instead?** — Success criteria (rough)

**Do not yet ask:** detailed trigger conditions, edge cases, compliance risks. That's Phase 3.

### Surfacing Approaches

After understanding the problem space (3-5 questions), surface 2-3 rough approaches:

**Approach dimensions to consider:**

| Dimension | Spectrum |
|-----------|----------|
| Structure | Reference (knowledge only) ↔ Task (steps) ↔ Methodology (discipline) |
| Scope | Narrow (single concern) ↔ Broad (multiple concerns) |
| Compliance | Guidance (principles) ↔ Discipline (bright-line rules) |
| Composition | Standalone ↔ Orchestrates other skills |

**Example framing:**

> "I see three ways to approach this:
>
> **A. Reference skill** — Document the conventions. Claude applies them when relevant. Light touch, but relies on Claude noticing when to apply.
>
> **B. Task skill** — Numbered steps. Ensures the process is followed but doesn't guard against shortcuts under pressure.
>
> **C. Methodology skill** — Full discipline enforcement with checkpoints, anti-patterns, rationalizations. Heavier but catches more failure modes.
>
> Given that [X is the main risk], I'd recommend **B** — enough structure without the overhead of C. Thoughts?"

**Present with trade-offs and a recommendation.** Don't ask "which do you prefer?" without guidance.

### Exit Criteria

Ready for Phase 2 when:
- [ ] Problem space understood (not solution details)
- [ ] 2-3 approaches surfaced with trade-offs
- [ ] Recommendation given

---

## Phase 2: Approach Selection

**Goal:** Narrow to one approach. This determines the template AND shapes what understanding is needed in Phase 3.

### Selection Guides Template

| Approach | Template | Phase 3 Focus |
|----------|----------|---------------|
| Reference | template-reference | Completeness of knowledge; when to apply |
| Task | template-task | Step sequence; verification; common failures |
| Methodology | template-methodology | Compliance risks; rationalizations; checkpoints |

**Hybrid skills:** If the skill has both reference content AND a process, start with template-task. Add methodology sections only if discipline enforcement is the core concern.

### User Selects

Present options conversationally. User picks one, or proposes a hybrid, or asks for clarification.

**If user is uncertain:** Default to the simpler option. Complexity can be added later; removing it is harder.

**If user has strong preference:** Follow it. Note trade-offs in design context.

### Exit Criteria

Ready for Phase 3 when:
- [ ] Approach selected (reference, task, or methodology)
- [ ] Template determined
- [ ] User understands what the approach entails

---

## Phase 3: Deep Understanding

**Goal:** Build detailed understanding of the skill's requirements — specific to the chosen approach.

### Approach-Specific Dimensions

Different approaches need different understanding:

**Reference skills — focus on:**
| Dimension | Question |
|-----------|----------|
| Content scope | What knowledge should be included? Excluded? |
| Application signals | How does Claude know when to apply this? |
| Conflicts | Does this contradict other guidance in CLAUDE.md or existing skills? |

**Task skills — focus on:**
| Dimension | Question |
|-----------|----------|
| Trigger conditions | When should this skill activate? |
| Step sequence | What's the order of operations? |
| Verification | How do we know each step succeeded? |
| Common failures | What typically goes wrong? |

**Methodology skills — focus on:**
| Dimension | Question |
|-----------|----------|
| Trigger conditions | When should this skill activate? |
| Compliance risks | What would make Claude skip steps or rationalize around this? |
| Pressure points | Where will agents be tempted to shortcut? |
| Checkpoints | Where should the skill force a pause? |
| Failure recovery | What happens when a step fails? |

### Question Discipline

**Default:** One question per message. Build understanding incrementally.

**Exception:** Bundle naturally paired questions ("What's the format?" + "Show me an example?") when separating them would feel artificial.

**Escape hatch:** If user signals preference for faster dialogue ("ask me everything at once"), you may bundle 2-3 related questions. But never more than 3.

### Assumption Gates

Instead of a separate list of "assumption traps," build checks into the flow:

**Gate 1 — After initial questions:**
> "Before I continue — the pattern here looks similar to [X]. Is this case different in ways I should know about?"

**Gate 2 — When user seems confident:**
> "You seem clear on the approach. Is there anything about this context that's unusual or that might surprise me?"

**Gate 3 — When you have a coherent interpretation:**
> "Let me check my understanding: [summary]. Is there anything I'm missing or getting wrong?"

These are NOT optional. Each gate must be passed before proceeding.

### Verification via Scenarios

**Replace "two no-yield rounds" with scenario-based verification.**

When you believe understanding is complete, test it:

1. **Define 2-3 test scenarios:**
   - Success case — skill activates and produces correct behavior
   - Edge case — boundary condition or unusual input
   - Failure case — skill should NOT activate, or should handle gracefully

2. **Walk through each scenario:**
   > "Given this scenario: [describe situation]. Based on my understanding, the skill would [predicted behavior]. Is that correct?"

3. **User validates predictions:**
   - If predictions correct → understanding verified
   - If any prediction wrong → more understanding needed; return to questions

**Why this works:** Testing predictions against scenarios verifies *correctness*, not just *stability*. You can converge on a wrong model and pass "two no-yield rounds," but you can't pass scenario verification with a wrong model.

### Exit Criteria

Ready for Phase 4 when:
- [ ] All approach-relevant dimensions covered
- [ ] All three assumption gates passed
- [ ] 2-3 scenarios defined and predictions validated
- [ ] User confirmed predictions match intent

---

## Phase 4: Design

**Goal:** Draft the SKILL.md using the selected template. Stress-test before finalizing.

### Pre-Draft Checklist

Before writing any content:
- [ ] Read skill-writing-guide.md (the consolidated reference)
- [ ] Verify you can articulate: description must be trigger-only; persuasion principles; ~500 line guideline

### Incremental Drafting

Present draft one section at a time:
1. Frontmatter (name, description)
2. Overview / When to Use
3. Process / Steps
4. Decision Points (if applicable)
5. Examples (if applicable)
6. Verification
7. Anti-Patterns / Troubleshooting / Rationalizations (methodology only)

After each section: "Does this look right so far?"

**If user asks for "the rest" or "everything":** Present ONE more section, then ask again. Incremental presentation catches errors early.

### Draft Requirements

| Field | Requirement |
|-------|-------------|
| `name` | kebab-case, ≤64 chars, gerund form (`commenting-code` not `code-comments`) |
| `description` | ≤1024 chars, trigger conditions ONLY, third person |
| Body | ~500 lines guideline; split to reference files if significantly larger |
| References | One level deep from SKILL.md |

### Stress-Testing (True Adversarial)

After draft is complete, stress-test with these questions:

| Question | What It Catches |
|----------|-----------------|
| "What if an agent follows this skill perfectly but the outcome is still wrong?" | Design gaps — skill doesn't guarantee success |
| "What behavior might this skill encourage that you DON'T want?" | Perverse incentives |
| "How would a rushing agent game this skill?" | Compliance theater — appearing to follow without substance |
| "What's the worst outcome from misuse?" | Risk assessment |
| "If this skill didn't exist, what would go wrong?" | Necessity check — is the skill actually needed? |

**Present findings to user.** If stress-testing reveals issues:
- Minor → fix in draft
- Significant → may need to revisit understanding (return to Phase 3)
- Fundamental → approach may be wrong (return to Phase 2)

### Design Context Document

Create `docs/plans/YYYY-MM-DD-<skill-name>-design.md`:

```markdown
## Design Context: <skill-name>

**Approach:** Reference | Task | Methodology
**Template:** template-reference | template-task | template-methodology

### Problem Statement
> [What's broken/missing? From Phase 1]

### Success Criteria
> [What should happen instead? From Phase 1]

### Approach Trade-offs
- Chose [approach] because: [rationale]
- Rejected [alternative] because: [rationale]

### Verification Scenarios
1. [Success case]: Expected behavior: [X]
2. [Edge case]: Expected behavior: [Y]
3. [Failure case]: Expected behavior: [Z]

### Stress-Test Findings
- [Finding 1]: [Resolution]
- [Finding 2]: [Resolution]

### Compliance Risks
- [Risk 1]: Mitigated by [section/mechanism]
```

### Exit Criteria

Ready for Phase 5 when:
- [ ] Draft SKILL.md complete
- [ ] All sections reviewed by user
- [ ] Stress-testing completed; findings addressed
- [ ] Design context document created

---

## Phase 5: Handoff

**Goal:** Hand off to testing-skills with clear iteration protocol.

### Commit and Branch

If on protected branch (main/develop):
```bash
git checkout -b feature/<skill-name>
```

Commit:
- Draft SKILL.md at `.claude/skills/<skill-name>/SKILL.md`
- Design context at `docs/plans/YYYY-MM-DD-<skill-name>-design.md`

### Iteration Protocol

Define what happens when testing-skills finds issues:

| Issue Severity | Definition | Return To |
|----------------|------------|-----------|
| **Minor** | Wording, formatting, missing detail | Edit draft directly (no re-brainstorm) |
| **Moderate** | Missing section, unclear decision point, weak example | Phase 4 (Design) with findings |
| **Major** | Wrong template, missing compliance mechanism, structural flaw | Phase 2 (Approach Selection) |
| **Fundamental** | Wrong problem, skill unnecessary, should be hook/agent instead | Phase 1 (Framing) |

**Handoff message:**
> "Draft complete. Ready to test? Use testing-skills to validate.
>
> If testing finds issues:
> - Minor issues → edit draft directly
> - Moderate issues → return here to Phase 4
> - Major issues → return here to Phase 2
> - Fundamental issues → return here to Phase 1"

### Exit Criteria

Handoff complete when:
- [ ] Draft committed to working branch
- [ ] Design context committed
- [ ] Iteration protocol communicated
- [ ] User knows next step is testing-skills

---

## What's Removed

### 8-Type Taxonomy → Eliminated

The previous skill defined 8 types (Process/workflow, Quality enhancement, Capability, Solution development, Meta-cognitive, Recovery/resilience, Orchestration, Template/generation).

**Why removed:** The types were post-hoc classification, not process guidance. They didn't change how you brainstorm — they were labels applied after the fact. The approach selection (Reference/Task/Methodology) is the actionable choice that determines process.

**Type-specific examples → Approach patterns:** The useful content from type-example files can be reframed as "patterns within approaches" rather than a separate taxonomy.

### Risk Tier → Moved to Stress-Testing

Previously captured as Low/Medium/High during classification. Now addressed via stress-testing question: "What's the worst outcome from misuse?"

### Convergence Tracking → Replaced with Scenario Verification

"Two consecutive no-yield rounds" replaced with explicit scenario verification. Tests correctness, not stability.

### Separate Assumption Traps List → Integrated as Gates

The 9 assumption traps are now built into the flow as 3 gates that must be passed.

---

## What's Added

### Approach-First Exploration

In the old skill, ALL 7 dimensions (Problem statement, Trigger conditions, Success criteria, Constraints, Edge cases, Compliance risks, Conflicts) are covered BEFORE exploring approaches. This means detailed understanding is gathered without knowing which approach will be chosen.

In the redesign, rough problem-space understanding comes first (3-5 questions), THEN approaches are surfaced, THEN approach-specific dimensions are covered. This prevents gathering detailed understanding for dimensions that won't matter for the chosen approach.

### Scenario Verification

Explicit mechanism to test understanding correctness, not just stability.

### True Adversarial Stress-Testing

Five questions that stress-test the design for gaps, perverse incentives, and gaming.

### Iteration Protocol

Explicit return paths based on issue severity found during testing.

---

## Open Questions — Resolved

| Question | Resolution |
|----------|------------|
| **1. Type examples → approach patterns?** | Mine and reorganize — extract useful content from 8 type-example files into approach-specific guidance |
| **2. Scenario verification detail?** | Minimal — current proposal guidance ("success, edge, failure" + walkthrough prompt) is sufficient |
| **3. 3-gate model sufficient?** | Yes — gates at assumption-crystallization moments + scenario verification + stress-testing provide defense in depth |
| **4. User literacy check / fast mode?** | Remove entirely — Claude adapts naturally without formal mechanism |
| **5. Reviewing-skills integration?** | No explicit integration — skill descriptions handle routing naturally |

---

## Implementation Notes

**Content mining complete.** See "Content Mining Analysis" section below for:
- File inventory with dispositions (keep/remove/move)
- Pattern mapping from 8 types to 3 approaches
- Approach-specific patterns to inline in Phase 3
- Decision to inline patterns (not separate file)

**Sections NOT needed in the new skill** (based on review):
- Examples section (BAD/GOOD scenarios)
- Anti-Patterns section
- Troubleshooting section
- Rationalizations table
- When NOT to Use section
- When to Use section

**Implementation checklist:**
- [ ] Draft new SKILL.md with 5-phase structure
- [ ] Inline approach patterns in Phase 3
- [ ] Remove redundant files (skills-best-practices.md, persuasion-principles.md)
- [ ] Remove type-example files (examples/*.md)
- [ ] Move framework-for-thoroughness to docs/frameworks/
- [ ] Test new skill with a sample brainstorming session

**Rationale:** The redesigned process structure (gates, scenario verification, stress-testing, iteration protocol) prevents failure modes rather than documenting them as warnings.

---

## Content Mining Analysis

Content inventory and disposition decisions for files in `.claude/skills/brainstorming-skills/`.

### File Inventory

| File | Lines | Disposition | Rationale |
|------|-------|-------------|-----------|
| **SKILL.md** | 493 | Replace | Core deliverable of this redesign |
| **skill-writing-guide.md** | 410 | Keep | Primary reference — consolidates best practices, persuasion, quality |
| **template-methodology.md** | 239 | Keep | Maps to Methodology approach |
| **template-reference.md** | 43 | Keep | Maps to Reference approach |
| **template-task.md** | 62 | Keep | Maps to Task approach |
| **semantic-quality.md** | 119 | Keep | 9 quality dimensions — useful supporting reference |
| **task-list-guide.md** | — | Keep | TaskCreate/TaskUpdate guidance for complex skills |
| **skills-best-practices.md** | 683 | Remove | Redundant — duplicates skill-writing-guide (official Anthropic docs) |
| **persuasion-principles.md** | — | Remove | Redundant — already consolidated in skill-writing-guide |
| **framework-for-thoroughness_v1.0.0.md** | — | Move | Belongs in `docs/frameworks/`, not skill directory |
| **examples/type-example-*.md** | ~200 each | Remove | Content mined into approach patterns below |

### Type-Example → Approach Pattern Mapping

The 8 type-example files contained patterns organized by skill *outcome type*. The redesign needs patterns organized by *approach*. Below is the extracted valuable content.

**Old types → New approach mapping:**

| Old Type | Primary Approach | Key Patterns Extracted |
|----------|------------------|------------------------|
| Capability | Reference | Domain knowledge structure, diagnostic branching |
| Process/Workflow | Task + Methodology | Step characteristics, pressure resistance |
| Meta-cognitive | Cross-cutting | Recognition + response structure, calibration |
| Quality Enhancement | Cross-cutting | Criteria definition, quality tradeoffs |
| Orchestration | Methodology | Phase structure, checkpoint placement, handoffs |
| Recovery/Resilience | Task | Failure type → strategy mapping |
| Solution Development | Methodology | Analysis framework phases, tradeoff explicitness |
| Template/Generation | Task | Exact structure definition, format adaptation |

### Approach-Specific Patterns (to inline in Phase 3)

**Reference Approach — Patterns:**

| Pattern | Source | Use For |
|---------|--------|---------|
| Domain knowledge structure | type-example-capability | Organizing knowledge content |
| Application signals | type-example-meta-cognitive | Helping Claude know when to apply |
| Conflict checking | type-example-capability | Ensuring no contradiction with existing guidance |

Content structure: "Organize around core concepts needed, common patterns/solutions, edge cases and gotchas."

**Task Approach — Patterns:**

| Pattern | Source | Use For |
|---------|--------|---------|
| Step characteristics | type-example-process-workflow | Designing atomic, verifiable, sequential steps |
| Output structure definition | type-example-template-generation | Specifying exact formats with field requirements |
| Failure type → recovery | type-example-recovery-resilience | Mapping failures to appropriate responses |
| Verification strategies | type-example-template-generation | Confirming each step succeeded |

Step design: "Each step should be atomic (one action), verifiable (you can tell if it happened), sequential (depends on prior steps)."

Format specification: "Define exact output structure with required fields table: Field | Required | Constraints."

**Methodology Approach — Patterns:**

| Pattern | Source | Use For |
|---------|--------|---------|
| Pressure point identification | type-example-process-workflow | Finding where agents shortcut |
| Checkpoint placement | type-example-orchestration | Forcing pauses at critical moments |
| Phase structure with handoffs | type-example-orchestration | Coordinating multi-phase workflows |
| Backtrack paths | type-example-orchestration | Returning to earlier phases when issues found |
| Analysis framework | type-example-solution-development | Structuring deliberate analysis |

Pressure handling: "What happens when steps are challenged? What if there's pressure to skip? What if earlier steps invalidate later ones?"

Checkpoint design: "All checkpoints require explicit user approval before proceeding. Silence or ambiguous response → ask for explicit confirmation."

**Cross-Cutting Patterns (all approaches):**

| Pattern | Source | Use For |
|---------|--------|---------|
| Diagnostic branching | type-example-capability | Decision Points — what to check based on findings |
| Recognition + response | type-example-meta-cognitive | Awareness-based decision logic |
| Calibrated confidence | type-example-meta-cognitive | When to flag uncertainty |
| Criteria/framework structure | type-example-quality-enhancement | Defining what "good" means |
| Tradeoff explicitness | type-example-solution-development | Surfacing what's sacrificed in choices |

### Implementation Decision

**Decision:** Inline approach patterns in Phase 3 (not separate file)

**Rationale:**
- Approach-specific content from type-examples is mostly about which questions to ask and what structure to use — not verbose
- Keeps all Phase 3 guidance in one place
- Avoids "one more file to read" friction
- The patterns are brief enough to not push SKILL.md over ~500 lines

**Structure in new SKILL.md:**
```
Phase 3: Deep Understanding
├── Approach-Specific Dimensions (tables already in proposal)
├── Reference Skills — Patterns (brief, inline)
├── Task Skills — Patterns (brief, inline)
├── Methodology Skills — Patterns (brief, inline)
├── Question Discipline
├── Assumption Gates
├── Verification via Scenarios
└── Exit Criteria
```

---

## Comparison: Old vs New

| Aspect | Old | New |
|--------|-----|-----|
| Flow order | Understanding + All Dimensions → Approaches → Convergence → Checkpoint | Framing (rough) → Approaches → Approach-specific Understanding → Design |
| Convergence | Two no-yield rounds | Scenario verification |
| Taxonomy | 8 types + 3 templates | 3 approaches (= templates) |
| Assumption handling | Separate list of 9 traps | 3 integrated gates |
| Adversarial check | 5-item sanity check | 5 stress-test questions |
| Iteration | One-directional handoff | Severity-based return paths |
| Question discipline | "One question per message" (dogmatic) | "Default one; exceptions allowed" |
