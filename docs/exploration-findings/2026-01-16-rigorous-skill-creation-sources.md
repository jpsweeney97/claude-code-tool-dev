# Source Material Exploration: rigorous-skill-creation

**Date:** 2026-01-16
**Purpose:** Comprehensive exploration of source materials for rigorous-skill-creation design
**Method:** 5 parallel explore agents examining source directories

## Source Directories

| Directory | Plugin | Version |
|-----------|--------|---------|
| `/Users/jp/.claude/plugins/cache/metamarket-dev/metamarket/0.1.0/` | metamarket | 0.1.0 |
| `/Users/jp/.claude/plugins/cache/superpowers-marketplace/superpowers/4.0.3/skills/writing-skills/` | superpowers | 4.0.3 |
| `/Users/jp/.claude/plugins/cache/superpowers-marketplace/superpowers/4.0.3/skills/test-driven-development/` | superpowers | 4.0.3 |

---

# 1. Skillosophy (metamarket)

**Main file:** `skills/skillosophy/SKILL.md` (405 lines)

## 1.1 Four-Phase Collaborative Workflow

### Phase 0: Triage (Steps 1-5)
- Parse user intent to identify mode: CREATE, REVIEW, VALIDATE, or ambiguous
- Mode signals: "review"/"panel"/"synthesis" + path → REVIEW; "validate"/"check"/"lint" + path → VALIDATE; "create"/"new"/"build" → CREATE
- Self-modification guard blocks skillosophy from modifying itself
- Runs optional triage script (`triage_skill_request.py`) for CREATE mode
- Routes based on match score: ≥80% USE_EXISTING, 50-79% IMPROVE_EXISTING, <50% CREATE_NEW

### Phase 1: Deep Analysis (Steps 6-13)
- Initializes TodoWrite with high-level tasks
- Requirements discovery dialogue (one question at a time)
- Applies 11 thinking lenses internally for analysis
- Captures explicit requirements in `metadata.decisions`
- Explores 2-3 alternatives with trade-offs
- Determines risk tier (Low/Medium/High)
- Selects from 21 defined skill categories
- Runs regression questioning (up to 7 rounds)
- Creates Session State at end

### Phase 2: Specification Checkpoint (Steps 14-16)
- Presents consolidated summary to user with Purpose, Requirements (Explicit/Implicit/Discovered), Approach, Rejected alternatives, Risk Tier, Category
- Iterates until user validates
- Locks decisions for generation

### Phase 3: Generation (Steps 17-20)
- Generates 11 body sections in strict order
- For each section: draft → validate against checklists (MUST/SHOULD/SEMANTIC) → present to user → approve → write → update Session State
- Manages Session State ordering (always last section)
- Runs cross-section validation after all 11 sections

### Phase 4: Synthesis Panel (Steps 21-30)
- Checks skill size (warns if >1000 lines for scope creep)
- Launches 4 parallel agents via Task tool
- Model fallback: tries Opus first, retries failed agents with Sonnet
- Collects verdicts (APPROVED or CHANGES_REQUIRED)
- Requires unanimous APPROVED
- Loop-back if needed (max 5 iterations, adaptive limits)
- Finalizes: removes Session State, confirms completion

---

## 1.2 Eleven Thinking Lenses

**File:** `references/methodology/thinking-lenses.md` (160 lines)

| # | Lens | Core Question | Application |
|---|------|---------------|-------------|
| 1 | **First Principles** | What is fundamentally needed? | Strip conventions; find atomic value unit |
| 2 | **Inversion** | What would guarantee failure? | List failure modes; create anti-patterns; design to avoid |
| 3 | **Analogy** | What similar problems exist? | Find patterns from other domains that map |
| 4 | **Abstraction** | Right level of generality? | Neither too specific nor too abstract |
| 5 | **Systems** | How do parts interact? | Map inputs, processes, outputs, feedback loops |
| 6 | **Temporal** | How does this evolve over time? | Project forward across 6 timeframes |
| 7 | **Constraint** | What are real limits? | Distinguish hard (platform) vs soft (convention) |
| 8 | **Failure** | What breaks, when, how? | Identify catastrophic, silent, adoption, evolution failures |
| 9 | **Composition** | How does this combine with others? | Assess composition with other skills; handoff format |
| 10 | **Evolution** | Still work in 2 years? | Timelessness, extension points, obsolescence risk |
| 11 | **Adversarial** | Strongest argument against this? | Devil's advocate; argue opposite; find legitimate concerns |

### Application Protocol

- **Phase 1 Rapid Scan:** Apply each lens for 2-3 minutes to assess relevance (High/Medium/Low)
- **Phase 2 Deep Dive:** For High-relevance lenses, 5-10 minutes each
- **Phase 3 Conflict Resolution:** When lenses suggest conflicting approaches

### Minimum Coverage Before Proceeding to Specification

- All 11 lenses scanned for relevance
- At least 3 lenses yield actionable insights
- All High-relevance lenses fully applied
- Conflicts between lenses resolved

---

## 1.3 Regression Questioning Protocol

**File:** `references/methodology/regression-questions.md` (267 lines)

7 categories of questions applied iteratively to exhaustively explore problem space.

**Termination criteria:** 3 consecutive rounds with no new insights OR all thinking models applied OR ≥3 expert perspectives considered OR evolution/timelessness explicitly evaluated with score ≥7.

### Category 1: Missing Elements (5 questions)

- "What am I missing?" — Open-ended gap detection (every round)
- "What haven't I considered?" — Blind spot identification (after initial design)
- "What assumptions am I making?" — Expose implicit decisions (when obvious)
- "What's not in requirements but should be?" — Implicit requirement discovery (after requirements)
- "What edge cases haven't I addressed?" — Boundary condition coverage (after main flow)

**Red flag:** "I think I've covered everything" → Ask 3 more questions

### Category 2: Expert Simulation (6 expert types)

- **Domain Expert:** domain-specific patterns, jargon, conventions
- **UX Expert:** intuitive for audience, cognitive load, discoverability
- **Systems Architect:** integration, dependencies, coupling, composition
- **Security Expert:** input validation, privilege escalation, data exposure
- **Performance Expert:** token usage, iteration count, timeout risks
- **Maintenance Engineer:** clarity, documentation, extension points

### Category 3: Failure Analysis (6 failure modes)

- **Catastrophic failures:** "What would make this skill fail completely?"
- **Silent failures:** "What would produce wrong results?"
- **Adoption failures:** "What would make users abandon this?"
- **Evolution failures:** "What would make this obsolete?"
- **Technical debt:** "What would make this unmaintainable?"
- **Ecosystem failures:** "What would make this conflict with others?"

For each: assess likelihood (H/M/L) and impact (C/M/M), design mitigation, document in anti-patterns

### Category 4: Temporal Projection (7 timeframes)

| Horizon | Question | Focus |
|---------|----------|-------|
| Now | Does this solve immediate problem? | Current utility |
| 1 week | Will first users succeed? | Initial experience |
| 1 month | What feedback will arrive? | Early adoption issues |
| 6 months | How will usage patterns evolve? | Maturation |
| 1 year | What ecosystem changes likely? | External pressures |
| 2 years | Will core approach still be valid? | Fundamental soundness |
| 5 years | Is underlying problem still relevant? | Problem evolution |

### Category 5: Completeness Verification (5 checks)

- **Thinking Models:** "Which of 11 haven't I applied?"
- **Domain Coverage:** "All relevant domains (design, architecture, UX, etc.)?"
- **Stakeholder Coverage:** "All perspectives considered?"
- **Integration Coverage:** "All related skills evaluated?"
- **Quality Attributes:** "Performance, security, maintainability?"

### Category 6: Meta-Questioning (5 meta-questions)

- "Have I exhausted analysis or am I tired?"
- "What question haven't I asked?"
- "Where would I struggle defending this to critic?"
- "What would I add with unlimited time?"
- "Most controversial aspect of this design?"

### Category 7: Script and Automation Analysis (8 questions)

Determines what operations will be repeated, what outputs need validation, what state persists, how Claude verifies execution, what scripts already exist, agentic capability, fragile operations, error recovery.

**Script Categories:** Validation, State Management, Generation, Transformation, Integration, Visualization, Calculation

---

## 1.4 Risk Tier Guide

**File:** `references/methodology/risk-tiers.md` (62 lines)

### Tier Selection

| Tier | Criteria | Examples |
|------|----------|----------|
| **Low** | Read-only, no external deps, trivial/reversible | Documentation, exploration, analysis |
| **Medium** | Writes files/config, bounded and reversible | Code generation, config changes, test writing |
| **High** | Security, ops, data, deps, public contracts, costly to reverse | Deployments, migrations, auth changes, API changes |

### Auto-Escalation Rule

If ANY mutating action detected → treat as High until gating verified

### Tier-Specific Minimum Requirements

| Requirement | Low | Medium | High |
|-------------|-----|--------|------|
| All 11 sections | Y | Y | Y |
| 1 quick check | Y | Y | Y |
| 1 troubleshooting | Y | Y | Y |
| 1 STOP/ask (missing inputs) | Y | Y | Y |
| STOP/ask (ambiguity) | — | Y | Y |
| Explicit non-goals (≥3) | — | Y | Y |
| 2nd verification mode | — | SHOULD | Y |
| Ask-first gates | — | — | Y |
| ≥2 STOP/ask gates | — | — | Y |
| Rollback/escape guidance | — | — | Y |

---

## 1.5 Category Integration

**File:** `references/methodology/category-integration.md` (157 lines)

21 skill categories with specific DoD (Definition of Done) additions:

| Category | Typical Risk | Dominant Failure Mode |
|----------|--------------|----------------------|
| debugging-triage | Medium | Missing regression guard |
| refactoring-modernization | Medium | Behavior change without detection |
| security-changes | High | Deny-path not verified |
| agentic-pipelines | High | Missing idempotency contract |
| documentation-generation | Low | Stale content |
| code-generation | Medium | Generated code doesn't compile |
| testing | Medium | Tests don't isolate failures |
| configuration-changes | Medium | Rollback not possible |
| dependency-changes | High | Breaking changes not detected |
| api-changes | High | Contract violation |
| data-migrations | High | Data loss or corruption |
| infrastructure-ops | High | Irreversible state change |
| meta-skills | Low | Produced skills don't comply |
| review-audit | Medium | Superficial review (missed issues) |
| prompt-engineering | Medium | Overfitting to test cases |
| research-exploration | Low | Inconclusive findings |
| planning-architecture | Medium | Plan doesn't survive implementation |
| performance-optimization | Medium | Wrong bottleneck targeted |
| automation-scripting | Medium | Works locally, fails in CI |
| ui-ux-development | Medium | Functional but poor UX |
| incident-response | High | Mitigation introduces new issues |

Each has specific DoD checklist (e.g., for data-migrations: backup verified, rollback tested, data integrity checked).

---

## 1.6 Validation Checklists (14 files)

**Location:** `references/checklists/`

### frontmatter.md (30 lines)
- Required: name (kebab-case, ≤64 chars), description (≤1024 chars, single line)
- Tool Declaration: allowed-tools lists all used tools, no placeholders
- Invocation: user-invocable explicit
- Optional: license, metadata.version (semver)

### frontmatter-decisions.md (29 lines)
- MUST: metadata.decisions present/valid YAML; requirements.explicit ≥1; approach.chosen; risk_tier (value)
- SHOULD: requirements.implicit and discovered non-empty; alternatives ≥2 with rationale; methodology_insights ≥5

### triggers.md (26 lines)
- MUST: ≥3 phrases, ≤50 chars each, no duplicates
- SHOULD: Mix verb/noun phrases, cover synonyms, avoid overly generic

### when-to-use.md (15 lines)
- MUST: Section exists, primary goal in 1-2 sentences, specific triggers
- SHOULD: Example scenarios

### when-not-to-use.md (19 lines)
- MUST: ≥3 explicit non-goals, STOP conditions, prevent scope failures
- SHOULD: Default non-goals (no deps, no API changes, no destructive, no migrations unless stated)

### inputs.md (22 lines)
- MUST: Required, Optional, Constraints subsections; ≥1 input; specific/actionable; constraints declare assumptions; fallback provided

### outputs.md (22 lines)
- MUST: Artifacts and DoD subsections; ≥1 artifact; ≥1 objective DoD check
- SHOULD: Distinguish Verified/Inferred/Assumed

### procedure.md (30 lines)
- MUST: Numbered steps; executable actions; ≥1 STOP for missing inputs; ≥1 STOP for ambiguity; ask-first gates before breaking actions
- SHOULD: inspect→decide→act→verify order; smallest correct change
- Command Mention Rule: Every command specifies expected result, preconditions, fallback

### decision-points.md (28 lines)
- MUST: ≥2 decision points with "If... then... otherwise"; observable triggers; not subjective
- SHOULD: Cover common branches (tests exist?, network?, breaking change?, output format?)

### verification.md (33 lines)
- MUST: Quick check subsection; concrete/executable/observable; measures primary property
- HIGH-MUST: ≥2 verification modes (quick + deep) for High risk
- SHOULD: No-network fallback; verification ladder for Medium+ risk

### troubleshooting.md (18 lines)
- MUST: ≥1 failure mode with symptoms/causes/next steps
- HIGH-MUST: Rollback/escape hatch guidance

### anti-patterns.md (27 lines)
- MUST: ≥1 entry with pattern description, consequence
- SHOULD: Min entries match risk tier (Low ≥1, Medium ≥2, High ≥2)

### extension-points.md (26 lines)
- MUST: ≥2 actionable entries (verb + object), no vague entries
- SHOULD: Span extension types (scope, integration, optimization)

### session-state.md (36 lines)
- MUST: `## Session State` heading, `phase` (0-4), `progress` (N/11), removed after Phase 4
- Lifecycle: Created end Phase 1 → Updated Phase 3 → Removed after approval

---

## 1.7 Synthesis Panel Agents (4 agents)

**Location:** `agents/`

All require Opus model, with Sonnet fallback.

### Executability Auditor (62 lines)

**Purpose:** Verify Claude can follow skill unambiguously to completion.

**Evaluates:**
- **Procedure:** Single discrete actions, no vague language ("appropriately"), explicit dependencies
- **Decision Points:** ≥2 explicit branches, decidable conditions, specified defaults
- **Verification:** Runnable checks (not "ensure X works"), specific results
- **Terminology:** Defined/unambiguous, consistent

**Verdict:** APPROVED (no High, ≤2 Medium) | CHANGES_REQUIRED (any High or >2 Medium)

### Semantic Coherence Checker (67 lines)

**Purpose:** Verify all sections tell same story.

**Evaluates:**
- **Input/Procedure:** Every input used; every used input listed
- **Output/Procedure:** Every output produced; every artifact listed
- **Output/Verification:** Every output has check
- **Procedure/Troubleshooting:** Failures have recovery
- **Terminology:** Same concept = same term
- **Triggers/When-to-use:** Triggers are literal phrases; when-to-use are conditions

**Verdict:** APPROVED (no structural inconsistencies, ≤3 terminology issues) | CHANGES_REQUIRED (any structural inconsistency)

### Dialogue Auditor (75 lines)

**Purpose:** Review collaborative process for gaps.

**Evaluates:**
- **Decision Completeness:** requirements.explicit captures stated needs
- **Alternative Exploration:** ≥2 alternatives with rationale
- **Assumption Validation:** Critical assumptions validated
- **Methodology Application:** ≥5 substantive insights that trace to sections

**Verdict:** APPROVED (no High gaps, methodology substantive) | CHANGES_REQUIRED (any High gap or superficial methodology)

### Adversarial Reviewer (85 lines)

**Purpose:** Challenge decisions and discover failure scenarios.

**Two-pronged:**
1. **Decision Challenges:** For each key decision, steelman rejected alternative, evaluate if rejection holds
2. **Failure Scenario Discovery:** Invalid inputs, edge cases, timing, resource exhaustion, dependency failures, permissions

**Verdict:** APPROVED (all decisions justified/weakly justified, no High unmitigated failures) | CHANGES_REQUIRED (unjustified decision or High unmitigated failure)

---

## 1.8 Scripts

### triage_skill_request.py (~600 lines)
Routes user requests: USE_EXISTING (≥80%), IMPROVE_EXISTING (50-79%), CREATE_NEW (<50%), CLARIFY, or handles failures gracefully.

### discover_skills.py (~600 lines)
Inventory utility for existing skills (supports REVIEW/VALIDATE workflows). Builds skill index for triage routing.

---

# 2. Writing-Skills (superpowers)

**Main file:** `SKILL.md` (656 lines)

## 2.1 Core Principle

**"Writing skills IS Test-Driven Development applied to process documentation."**

### TDD Mapping

| TDD Concept | Skill Equivalent |
|-------------|------------------|
| TEST | Pressure scenario with subagent |
| PRODUCTION CODE | Skill document (SKILL.md) |
| RED | Agent violates without skill (baseline) |
| GREEN | Agent complies with skill present |
| REFACTOR | Close loopholes, plug rationalizations |

### The Iron Law

```
NO SKILL WITHOUT FAILING TEST FIRST
```

Applies to NEW skills AND EDITS. No exceptions ("simple additions", "just adding a section", "documentation updates").

---

## 2.2 Claude Search Optimization (CSO)

**CRITICAL FINDING:** Description = WHEN TO USE, NOT WHAT SKILL DOES

### The Description Trap

When descriptions summarize workflow, Claude shortcuts to description behavior instead of reading the flowchart.

**Bad:**
```yaml
description: Use when executing plans - dispatches subagent per task with code review between tasks
```
→ Claude may follow "dispatches subagent per task" from description without reading skill body

**Good:**
```yaml
description: Use when executing implementation plans with independent tasks in the current session
```
→ No workflow summary forces Claude to read full skill

### CSO Guidelines

- Start with "Use when..."
- Describe triggering CONDITIONS (race conditions, inconsistent behavior)
- NOT language-specific symptoms (setTimeout, sleep)
- Technology-agnostic unless skill itself is tech-specific
- Third person (injected into system prompt)
- Include error messages, symptoms, synonyms, actual tool names
- Keep under 500 characters

---

## 2.3 Skill Types

| Type | Example | Testing Focus |
|------|---------|---------------|
| **Discipline-enforcing** | TDD, verification | Pressure scenarios (temptation to bypass) |
| **Technique** | condition-based-waiting | Application + variation + missing info |
| **Pattern** | flatten-with-flags | Recognition + application + counter-examples |
| **Reference** | API docs | Retrieval + application + gap testing |

---

## 2.4 SKILL.md Structure

```yaml
---
name: Skill-Name-With-Hyphens
description: Use when [triggering conditions, symptoms]
---

# Skill Name

## Overview
## When to Use
## Core Pattern (if technique/pattern)
## Quick Reference
## Implementation
## Common Mistakes
## Real-World Impact (optional)
```

---

## 2.5 Token Efficiency Targets

- getting-started skills: <150 words each
- Frequently-loaded skills: <200 words total
- Other skills: <500 words
- Move details to `--help`, cross-reference other skills, compress examples

---

## 2.6 Skill Creation Checklist

### RED Phase
- Create pressure scenarios (3+ combined pressures)
- Run WITHOUT skill, document baseline verbatim
- Identify patterns in rationalizations/failures

### GREEN Phase
- Name uses letters/numbers/hyphens only
- Frontmatter with name + description (max 1024 chars)
- Description starts with "Use when...", third person
- Keywords for search
- Clear overview
- Address specific baseline failures
- Code inline OR separate file
- ONE excellent example (not multi-language)
- Run scenarios WITH skill, verify compliance

### REFACTOR Phase
- Identify NEW rationalizations from testing
- Add explicit counters (if discipline skill)
- Build rationalization table
- Create red flags list
- Re-test until bulletproof

---

# 3. Testing Skills with Subagents

**File:** `testing-skills-with-subagents.md` (385 lines)

## 3.1 Pressure Scenario Design

### Format
```
IMPORTANT: This is a real scenario. Choose and act.

[Setup with time pressure + sunk cost + exhaustion]
[Specific constraints]

Options:
A) [Correct option]
B) [Tempting wrong option]
C) [Another wrong option]

Choose A, B, or C.
```

### 7 Pressure Types

| Type | Description |
|------|-------------|
| **Time** | Emergency, deadline, window closing |
| **Sunk cost** | Hours of work, "waste" to delete |
| **Authority** | Senior/manager says skip it |
| **Economic** | Job, promotion at stake |
| **Exhaustion** | End of day, tired |
| **Social** | Looking dogmatic, inflexible |
| **Pragmatic** | "Being pragmatic vs dogmatic" |

**BEST:** Combine 3+ pressures

---

## 3.2 RED-GREEN-REFACTOR Cycle

### RED Phase: Baseline Testing
1. Create pressure scenarios with multiple combined pressures
2. Run WITHOUT skill
3. Document exact behavior and rationalizations verbatim
4. Identify patterns in failures

### GREEN Phase: Write Minimal Skill
1. Write skill addressing specific baseline failures only
2. Run same scenarios WITH skill
3. Agent should now comply
4. If still fails: skill is unclear/incomplete

### REFACTOR Phase: Close Loopholes
For each new rationalization found during testing:

1. **Explicit negation in rules** — forbid specific workarounds
2. **Entry in rationalization table**
3. **Red flag entry** — make violations obvious
4. **Update description** — add violation symptoms
5. **Re-verify** — same scenarios with updated skill

---

## 3.3 Meta-Testing Protocol

When GREEN isn't working, ask agent:
```
How could that skill have been written differently to make
it crystal clear that Option A was the only acceptable answer?
```

**Three possible responses:**
1. "Skill WAS clear, I chose to ignore it" → Need foundational principle
2. "Skill should have said X" → Add suggestion verbatim
3. "I didn't see section Y" → Organization problem, make key points prominent

---

## 3.4 Bulletproof Signs

1. Agent chooses correct option under maximum pressure
2. Agent cites skill sections as justification
3. Agent acknowledges temptation but follows rule
4. Meta-testing reveals "skill was clear, I should follow it"

---

## 3.5 Testing Checklist

### RED Phase
- [ ] Pressure scenarios (3+ combined)
- [ ] Scenarios WITHOUT skill
- [ ] Agent failures + rationalizations verbatim

### GREEN Phase
- [ ] Skill addresses specific baseline failures
- [ ] Scenarios WITH skill
- [ ] Agent now complies

### REFACTOR Phase
- [ ] NEW rationalizations identified
- [ ] Explicit counters for each loophole
- [ ] Rationalization table updated
- [ ] Red flags list updated
- [ ] Description updated with violation symptoms
- [ ] Re-tested - agent still complies
- [ ] Meta-tested for clarity
- [ ] Agent follows rule under maximum pressure

---

# 4. Anthropic Best Practices

**File:** `anthropic-best-practices.md` (1150 lines)

## 4.1 Core Principles

### Conciseness
- Context window is public good
- Only add context Claude doesn't already have
- Challenge each piece: "Does Claude really need this?"
- Default: Claude is already very smart

### Degrees of Freedom

| Freedom Level | Use When | Example |
|---------------|----------|---------|
| **High** | Multiple approaches valid, heuristics guide | Code review |
| **Medium** | Preferred pattern exists, some variation acceptable | Reports |
| **Low** | Operations fragile, consistency critical | Database migrations |

### Test with All Models
- **Haiku:** Does it provide enough guidance?
- **Sonnet:** Is it clear and efficient?
- **Opus:** Does it avoid over-explaining?

---

## 4.2 Writing Effective Descriptions

- Always third person (injected into system prompt)
- Include what the skill does AND when to use it
- Be specific with triggers/contexts
- One description field for choosing from 100+ skills
- Include error messages, specific situations

**Bad:**
```yaml
description: Helps with documents
description: Processes data
```

**Good:**
```yaml
description: Extract text and tables from PDF files, fill forms, merge documents.
  Use when working with PDF files or when user mentions PDFs, forms, or document extraction.
```

---

## 4.3 Progressive Disclosure Patterns

### Pattern 1: High-level guide with references
```markdown
# PDF Processing

## Quick start
[Overview and basic example]

## Advanced features
**Form filling**: See [FORMS.md](FORMS.md)
**API reference**: See [REFERENCE.md](REFERENCE.md)
```

### Pattern 2: Domain-specific organization
```
bigquery-skill/
├── SKILL.md (overview, navigation)
└── reference/
    ├── finance.md
    ├── sales.md
    └── marketing.md
```

**Critical:** Avoid deeply nested references — Claude may use `head -100` on nested files. Keep references one level deep from SKILL.md.

---

## 4.4 MCP Tool References

**Always use fully qualified names:** `ServerName:tool_name`

Prevents "tool not found" errors.

---

## 4.5 Evaluation-First Development

1. **Identify gaps** — run Claude on representative tasks WITHOUT skill
2. **Create evaluations** — 3 scenarios testing these gaps
3. **Establish baseline** — measure performance without skill
4. **Write minimal instructions** — just enough to address gaps
5. **Iterate** — execute evaluations, compare, refine

---

## 4.6 Checklist for Effective Skills

**Core quality:**
- [ ] Description specific
- [ ] SKILL.md <500 lines
- [ ] Separate files if needed
- [ ] No time-sensitive info
- [ ] Consistent terminology
- [ ] Concrete examples
- [ ] One-level references
- [ ] Progressive disclosure
- [ ] Clear workflows

**Code/scripts:**
- [ ] Solve problems, don't punt
- [ ] Explicit error handling
- [ ] Justified constants
- [ ] Packages listed
- [ ] Scripts documented
- [ ] Forward slashes in paths
- [ ] Validation for critical ops
- [ ] Feedback loops

**Testing:**
- [ ] 3+ evaluations
- [ ] Tested with Haiku/Sonnet/Opus
- [ ] Real usage scenarios
- [ ] Team feedback

---

# 5. Persuasion Principles

**File:** `persuasion-principles.md` (188 lines)

## 5.1 Research Foundation

Meincke et al. (2025) tested 7 principles with N=28,000 AI conversations.

**Key finding:** Persuasion techniques doubled compliance (33% → 72%, p < .001)

## 5.2 The Seven Principles

| Principle | Implementation | Use For |
|-----------|----------------|---------|
| **Authority** | "YOU MUST", "Never", "Always", "No exceptions" | Discipline-enforcing, safety-critical |
| **Commitment** | Require announcements, force explicit choices | Multi-step processes, accountability |
| **Scarcity** | "Before proceeding", "Immediately after X" | Immediate verification, time-sensitive |
| **Social Proof** | "Every time", "Always", "X without Y = failure" | Universal practices, common failures |
| **Unity** | "our codebase", "we're colleagues" | Collaborative workflows |
| **Reciprocity** | (Use sparingly, rarely needed) | — |
| **Liking** | **DON'T USE for compliance** | Creates sycophancy |

## 5.3 Principle Combinations by Skill Type

| Skill Type | Use | Avoid |
|------------|-----|-------|
| Discipline-enforcing | Authority + Commitment + Social Proof | Liking, Reciprocity |
| Guidance/technique | Moderate Authority + Unity | Heavy authority |
| Collaborative | Unity + Commitment | Authority, Liking |
| Reference | Clarity only | All persuasion |

**Key insight:** Bright-line rules reduce rationalization. "YOU MUST" removes decision fatigue.

---

# 6. Test-Driven Development

**Main file:** `SKILL.md` (372 lines)

## 6.1 The Iron Law

```
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```

### Corollaries (absolute, no exceptions)

- Write code before the test? Delete it. Start over.
- Don't keep it as "reference"
- Don't "adapt" it while writing tests
- Don't look at it
- Delete means delete
- Implement fresh from tests. Period.

---

## 6.2 Red-Green-Refactor Cycle

### RED - Write Failing Test
- One minimal test showing what should happen
- One behavior only
- Clear name (not `test('retry works')`, but `test('retries failed operations 3 times')`)
- Real code (no mocks unless unavoidable)

### Verify RED - Watch It Fail (MANDATORY)
- [ ] Test fails (not errors)
- [ ] Failure message is expected
- [ ] Fails because feature missing (not typos)

**Red flag:** Test passes → you're testing existing behavior, fix test

### GREEN - Minimal Code
- Simplest code to pass the test
- No added features beyond what test requires
- No refactoring of other code

### Verify GREEN - Watch It Pass (MANDATORY)
- [ ] Test passes
- [ ] Other tests still pass
- [ ] Output pristine (no errors, warnings)

**Red flag:** Other tests fail → fix now, don't continue

### REFACTOR - Clean Up
After green only:
- Remove duplication
- Improve names
- Extract helpers
- Keep tests green, don't add behavior

---

## 6.3 Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "Too simple to test" | Simple code breaks; test takes 30 seconds |
| "I'll test after" | Tests passing immediately prove nothing |
| "Tests after achieve same goals" | Tests-after = "what does this do?" Tests-first = "what should this do?" |
| "Already manually tested" | Ad-hoc ≠ systematic |
| "Deleting X hours is wasteful" | Sunk cost fallacy; keeping unverified code is technical debt |
| "Keep as reference, write tests first" | You'll adapt it; that's testing after; delete means delete |
| "Need to explore first" | Fine; throw away exploration, start with TDD |
| "Test hard = design unclear" | Listen to test; hard to test = hard to use |
| "TDD will slow me down" | TDD faster than debugging; pragmatic = test-first |
| "Manual test faster" | Manual doesn't prove edge cases; you'll re-test every change |
| "Existing code has no tests" | You're improving it; add tests for existing code |

---

## 6.4 Red Flags — STOP and Start Over

All of these mean: Delete code. Start over with TDD.

- Code before test
- Test after implementation
- Test passes immediately
- Can't explain why test failed
- Tests added "later"
- Rationalizing "just this once"
- "I already manually tested it"
- "Tests after achieve the same purpose"
- "It's about spirit not ritual"
- "Keep as reference" or "adapt existing code"
- "Already spent X hours, deleting is wasteful"
- "TDD is dogmatic, I'm being pragmatic"
- "This is different because..."

---

## 6.5 Verification Checklist

Before marking work complete:

- [ ] Every new function/method has a test
- [ ] Watched each test fail before implementing
- [ ] Each test failed for expected reason (feature missing, not typo)
- [ ] Wrote minimal code to pass each test
- [ ] All tests pass
- [ ] Output pristine (no errors, warnings)
- [ ] Tests use real code (mocks only if unavoidable)
- [ ] Edge cases and errors covered

**Gate:** Can't check all boxes? You skipped TDD. Start over.

---

# 7. Testing Anti-Patterns

**File:** `testing-anti-patterns.md` (300 lines)

## 7.1 The Iron Laws

```
1. NEVER test mock behavior
2. NEVER add test-only methods to production classes
3. NEVER mock without understanding dependencies
```

## 7.2 Anti-Pattern Summary

| Anti-Pattern | Problem | Fix |
|--------------|---------|-----|
| Assert on mock elements | Testing mock works, not component | Test real component or unmock |
| Test-only methods in production | Pollutes production, dangerous | Move to test utilities |
| Mock without understanding | Mock breaks test logic | Understand deps first, mock minimally |
| Incomplete mocks | False confidence, silent integration failures | Mirror real API completely |
| Tests as afterthought | Violated TDD, low confidence | TDD - tests first |
| Over-complex mocks | Fragile, hard to maintain | Consider integration tests |

## 7.3 The Bottom Line

```
Mocks are tools to isolate, not things to test.

If TDD reveals you're testing mock behavior, you've gone wrong.

Fix: Test real behavior or question why you're mocking at all.
```

---

# Summary: Key Patterns for Design

## From Skillosophy
- 4-phase collaborative workflow
- 11 thinking lenses
- 7 regression question categories
- 14 validation checklists
- 4 synthesis panel agents
- 21 skill categories with DoD additions
- Risk tier system with per-tier minimums

## From Writing-Skills
- TDD for skills: RED → GREEN → REFACTOR
- The Iron Law: No skill without failing test first
- CSO: Description = triggers only, never workflow summary
- Pressure testing: 3+ combined pressures
- Rationalization capture: Quote verbatim, counter explicitly
- Bulletproof criteria: 4 signs of complete coverage

## From Test-Driven-Development
- The Iron Law: No production code without failing test first
- Delete code written before tests — no exceptions
- Verification checklist: 8-item gate before claiming complete
- Testing anti-patterns to avoid

## From Anthropic Best Practices
- Conciseness: Context window is public good
- Test with all models: Haiku, Sonnet, Opus
- Progressive disclosure: One-level references
- MCP: Always fully qualified tool names
- Evaluation-first development

## From Persuasion Principles
- 7 principles, doubled compliance (33% → 72%)
- Authority + Commitment + Social Proof for discipline-enforcing
- Never use Liking for compliance (creates sycophancy)
