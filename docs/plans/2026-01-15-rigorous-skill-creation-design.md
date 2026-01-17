# rigorous-skill-creation Design Document

**Date:** 2026-01-15
**Status:** Draft
**Location:** `.claude/skills/rigorous-skill-creation/`
**Promote to:** metamarket plugin (when stable)

## Overview

A standalone skill combining skillosophy's dialogue methodology with writing-skills' TDD-style pressure testing. Creates skills with verified behavior change, not just well-structured documentation.

**Core principles:**
1. **The Iron Law:** No skill generation without baseline failure first. If you haven't watched an agent fail without the skill, you don't know what the skill needs to prevent.
2. **Dialogue informs tests, tests validate skill.**

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Form | New standalone skill | Clean slate, cherry-pick from both sources |
| Location | `.claude/skills/` | Iterate locally, promote when stable |
| Name | rigorous-skill-creation | Clear purpose, discoverable |
| Structure | Full 11 sections | Dogfooding validates structure |
| Panel | Required for Medium + High risk | Right-sized rigor; Low-risk skills skip |
| Infrastructure | Create fresh | Tailored to Approach 2 |
| User-invocable | Yes | Complete workflow, not helper |
| Lenses | 14 total (4 understanding + 10 testing) | All skillosophy lenses + 3 new testing lenses |

## Directory Structure

```
.claude/skills/rigorous-skill-creation/
├── SKILL.md                          # Main skill (11 sections)
├── references/
│   ├── phase-1-requirements.md       # Requirements discovery + regression questioning (7 categories)
│   ├── phase-1-lenses.md             # 14 thinking lenses (4 understanding + 10 testing)
│   ├── phase-3-baseline.md           # Pressure testing methodology
│   ├── phase-4-generation.md         # Section requirements (merged checklists)
│   ├── phase-7-panel.md              # Panel agent prompts + tool permissions (adapted from metamarket)
│   ├── risk-tiers.md                 # Risk tier criteria + panel triggers
│   ├── category-integration.md       # 21 categories with DoD additions
│   ├── persuasion-principles.md      # 7 persuasion principles for skill design
│   ├── anthropic-best-practices.md   # Official Anthropic skill design guidance
│   └── testing-anti-patterns.md      # Common testing anti-patterns to avoid (from TDD skill)
├── templates/
│   ├── skill-skeleton.md             # Empty 11-section structure with Approach 2 metadata
│   ├── decisions-schema.md           # metadata.decisions schema (extended with verification)
│   └── session-state-schema.md       # Session State schema (extended with testing context)
├── examples/
│   └── worked-example.md             # Complete skill creation walkthrough
└── scripts/
    ├── triage.py                     # Check for existing skills
    ├── discover.py                   # Build skill index for triage
    └── validate.py                   # Validate skill structure
```

## Phase Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                         RIGOROUS SKILL CREATION                      │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │  Phase 0: TRIAGE              │
                    │  - Check for existing skills  │
                    │  - Route: CREATE/MODIFY/USE   │
                    └───────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
            CREATE/MODIFY                    USE EXISTING
                    │                         (exit skill)
                    ▼
    ┌───────────────────────────────┐
    │  Phase 1: REQUIREMENTS        │◄──────────────────┐
    │  - 11 thinking lenses         │                   │
    │  - Dialogue (1 Q at a time)   │                   │
    │  - Seed pressure scenarios    │                   │
    └───────────────────────────────┘                   │
                    │                                   │
                    ▼                                   │
    ┌───────────────────────────────┐                   │
    │  Phase 2: CHECKPOINT          │                   │
    │  - Present requirements       │     Corrections   │
    │  - Present scenarios          │───────────────────┘
    │  - User validates             │
    └───────────────────────────────┘
                    │ Approved
                    ▼
    ┌───────────────────────────────┐
    │  Phase 3: BASELINE (RED)      │
    │  - Run scenarios WITHOUT skill│
    │  - Capture failures           │
    │  - Build rationalization table│
    └───────────────────────────────┘
                    │
                    ▼
    ┌───────────────────────────────┐
    │  Phase 4: GENERATION          │◄──────────────────┐
    │  - Generate 11 sections       │                   │
    │  - Validate per checklist     │                   │
    │  - User approves each section │                   │
    └───────────────────────────────┘                   │
                    │                                   │
                    ▼                                   │
    ┌───────────────────────────────┐                   │
    │  Phase 5: VERIFICATION (GREEN)│                   │
    │  - Run scenarios WITH skill   │     Failures      │
    │  - Compare to baseline        │───────────────────┘
    │  - Document behavior change   │
    └───────────────────────────────┘
                    │ All pass
                    ▼
    ┌───────────────────────────────┐
    │  Phase 6: REFACTOR            │──┐
    │  - Find new rationalizations  │  │ New loopholes
    │  - Close loopholes            │◄─┘
    │  - Re-verify                  │
    └───────────────────────────────┘
                    │ Bulletproof
                    ▼
              ┌─────────────┐
              │Medium+ risk?│
              └──────┬──────┘
            Yes      │      No
        ┌────────────┴────────────┐
        ▼                         ▼
┌───────────────────┐   ┌───────────────────┐
│ Phase 7: PANEL    │   │ Skip panel (Low)  │
│ - 4 agents review │   │                   │
│ - Structural check│   │                   │
└───────────────────┘   └───────────────────┘
        │                       │
        └───────────┬───────────┘
                    ▼
    ┌───────────────────────────────┐
    │  Phase 8: FINALIZATION        │
    │  - Remove Session State       │
    │  - Commit skill               │
    │  - Document verification      │
    └───────────────────────────────┘
```

## SKILL.md Frontmatter

```yaml
---
name: rigorous-skill-creation
description: Use when creating skills that need verified behavior change,
  especially high-risk skills (security, agentic, data operations) or skills
  that enforce discipline.
hooks:
  PostToolUse:
    - matcher: 'Write|Edit'
      hooks:
        - type: command
          command: '${SKILL_ROOT}/scripts/validate.py'
          once: true
license: MIT
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - Task
  - AskUserQuestion
  - TodoWrite
user-invocable: true
metadata:
  version: '0.1.0'
  category: meta-skills
  risk_tier: 'Medium — creates artifacts that affect other workflows'
---
```

## 14 Thinking Lenses

### Understanding Lenses (4) — Inform design

| # | Lens | Core Question | Output |
|---|------|---------------|--------|
| 1 | **First Principles** | What is fundamentally needed? | Core value proposition |
| 2 | **Analogy** | What similar problems exist? | Patterns from other domains |
| 3 | **Abstraction** | What's the right level of generality? | Scope calibration |
| 4 | **Temporal** | How does this evolve over time? | Future-proofing insights |

### Testing Lenses (10) — Produce pressure scenarios

| # | Lens | Core Question | Scenario Type |
|---|------|---------------|---------------|
| 5 | **Inversion** | What would guarantee failure? | Failure mode test |
| 6 | **Systems** | How do components interact? | Integration test |
| 7 | **Constraint** | What are the real limits? | Constraint violation test |
| 8 | **Failure** | What breaks first under stress? | Stress test |
| 9 | **Composition** | How does this combine with other skills? | Composition test |
| 10 | **Evolution** | How might requirements change? | Regression test |
| 11 | **Adversarial** | What's the strongest argument against? | Devil's advocate test |
| 12 | **User Goals** | What does success look like? | Goal achievement test |
| 13 | **Edge Cases** | What unusual states might occur? | Boundary test |
| 14 | **Discoverability** | How will agents find this skill? | Trigger/search test |

*Lenses 1-11 from skillosophy; 12-14 added for testing focus.*

## Triggers

- "create a skill rigorously"
- "new skill with testing"
- "rigorous skill creation"
- "skill with pressure testing"
- "create a validated skill"
- "TDD skill creation"
- "skill with verification"

## When to Use

- Creating skills that enforce discipline (TDD, verification, process compliance)
- High-risk skills: security, agentic workflows, data operations
- Skills where behavior change must be verified, not assumed
- Skills with complex requirements needing dialogue to surface
- Skills that will be maintained long-term (audit trail valuable)
- When you need traceability: requirement → test → behavior change

**Symptoms that suggest this skill:**
- "I need to make sure agents actually follow this"
- "This is important enough to test properly"
- "I want to know it works, not hope it works"
- "Multiple stakeholders need to agree on requirements"

## When NOT to Use

- Simple technique documentation (use skillosophy instead)
- Low-risk, read-only skills
- One-off internal tools with clear requirements
- Time-constrained situations where speed trumps rigor
- Skills where structure matters more than behavior (use skillosophy instead)
- Modifying rigorous-skill-creation itself (circular dependency)

## Inputs

### Required
- **User intent**: Natural language description of skill goal

### Optional
- **Existing skill path**: For MODIFY mode, path to skill to improve
- **Risk tier override**: Explicit "high", "medium", "low" to skip assessment
- **Skip triage**: Flag to bypass existing skill check
- **Supporting file needs**: During Phase 1, discover if skill requires references/, examples/, scripts/

### Assumptions
- User has write access to target directory
- Python available for triage/validate scripts (graceful degradation if not)
- Task tool available for subagent operations (baseline testing, panel)
- Opus model preferred for panel agents (falls back to Sonnet)

## Outputs

### Primary Artifact
- **SKILL.md**: Complete skill with 11 sections + frontmatter

### Supporting Artifacts (skill-specific)
- **references/**: Heavy reference material that would bloat SKILL.md (>100 lines)
- **examples/**: Usage examples Claude loads when applying the skill (includes worked-example.md walkthrough)
- **scripts/**: Executable tools the skill needs at runtime (triage.py, discover.py, validate.py)

### Process Artifacts (verification evidence)
- **Baseline document**: Captured failures without skill
- **Verification evidence**: Before/after comparison proving behavior change
- **Rationalization table**: Observed excuses + counters (embedded in Anti-Patterns)

### Embedded Metadata

```yaml
metadata:
  version: "1.0.0"
  decisions:
    requirements:
      explicit: [...]
      implicit: [...]
      discovered: [...]
    approach:
      chosen: "..."
      alternatives: [...]
    risk_tier: "Medium — rationale"
    key_tradeoffs: [...]
    category: "..."
    methodology_insights:
      - "First Principles: finding → affected section"
      - "Inversion: finding → affected section"
  verification:
    baseline:
      scenarios_run: 3
      failures_observed: 3
      rationalizations_captured:
        - "exact phrase 1"
        - "exact phrase 2"
    testing:
      scenarios_passed: 3
      scenarios_failed: 0
    panel:
      status: "approved | skipped"
      agents_run: 4
```

### Definition of Done
- [ ] All 11 sections present and validated
- [ ] Supporting files created if needed (references/, examples/, scripts/)
- [ ] Baseline failures documented
- [ ] All pressure scenarios pass with skill
- [ ] Rationalization table covers observed failure modes
- [ ] Panel unanimous (if Medium/High-risk) OR panel skipped (if Low-risk)
- [ ] Session State removed

## Procedure

### Phase 0: Triage

1. **Parse user intent** — Identify if CREATE, MODIFY, or ambiguous
   - **Default**: If genuinely unclear after one clarifying question, default to CREATE
2. **Self-modification guard** — If target path is within rigorous-skill-creation directory, **STOP with explanation**: "Cannot modify self — circular dependency. Edit plugin files directly."
3. **Run triage script** (if available):
   ```bash
   python scripts/triage.py "<user goal>" --json
   ```
3. **Handle triage result**:
   | Result | Match | Action |
   |--------|-------|--------|
   | `USE_EXISTING` | ≥80% | Recommend existing; ask to proceed or create anyway |
   | `IMPROVE_EXISTING` | 50-79% | Offer MODIFY mode |
   | `CREATE_NEW` | <50% | Proceed to Phase 1 |
   | Script unavailable | — | Warn, proceed to Phase 1 |
4. **Initialize TodoWrite** with phase-level tasks

### Phase 1: Requirements Discovery

5. **Load reference**: Read `references/phase-1-requirements.md` (includes regression questioning protocol with 7 categories) and `references/phase-1-lenses.md`

   **Regression questioning termination:** Stop when 3 consecutive rounds yield no new insights OR all thinking models applied OR ≥3 expert perspectives considered OR evolution/timelessness explicitly evaluated with score ≥7.
6. **Apply 14 thinking lenses**:
   - Understanding lenses (4): Inform design
   - Testing lenses (10): Seed pressure scenarios

   **Minimum coverage before proceeding:**
   - All 14 lenses scanned for relevance (High/Medium/Low)
   - At least 3 lenses yield actionable insights
   - All High-relevance lenses fully applied
   - Conflicts between lenses resolved

7. **Dialogue with user** (one question at a time):
   - Purpose and success criteria
   - Constraints and non-negotiables
   - Who/what will use this skill
   - Prefer multiple choice when options are clear
8. **Categorize requirements**:
   - Explicit: What user asked for
   - Implicit: What user expects but didn't state
   - Discovered: What analysis reveals
9. **Seed pressure scenarios** from each requirement (especially testing lenses)
10. **Assess risk tier**:
    | Tier | Criteria | Panel Required |
    |------|----------|----------------|
    | Low | Read-only, documentation, research | No |
    | Medium | Code generation, refactoring, testing | Yes |
    | High | Security, agentic, data operations, discipline | Yes |

    **Tier-Specific Minimums:**

    | Requirement | Low | Medium | High |
    |-------------|-----|--------|------|
    | All 11 sections | Y | Y | Y |
    | 1 quick check | Y | Y | Y |
    | 1 troubleshooting entry | Y | Y | Y |
    | 1 STOP/ask (missing inputs) | Y | Y | Y |
    | STOP/ask (ambiguity) | — | Y | Y |
    | Explicit non-goals (≥3) | — | Y | Y |
    | 2nd verification mode | — | SHOULD | Y |
    | Ask-first gates | — | — | Y |
    | ≥2 STOP/ask gates | — | — | Y |
    | Rollback/escape guidance | — | — | Y |

    **Auto-Escalation Rule:** If ANY mutating action detected → treat as High until gating verified.

11. **Select category** from 21 defined categories
12. **Create Session State** at end of Phase 1

### Phase 2: Specification Checkpoint

13. **Build metadata.decisions** with all required fields
14. **Draft initial frontmatter** (name, description, risk_tier)
15. **Present consolidated summary**:
    ```
    Based on our discussion, here's what we're building:

    **Purpose:** [one sentence]
    **Risk Tier:** [level] — [justification]

    **Requirements:**
    - Explicit: [list]
    - Implicit: [list]
    - Discovered: [list]

    **Pressure Scenarios:**
    1. [Scenario → requirement it tests]
    2. [Scenario → requirement it tests]
    3. [Scenario → requirement it tests]

    **Approach:** [chosen] because [rationale]

    Does this capture your intent? Are the pressure scenarios right?
    ```
16. **Iterate until user validates** — corrections loop back to Phase 1
17. **Lock decisions** — after validation, requirements and scenarios are stable
18. **Update Session State** with locked decisions

### Phase 3: Baseline Testing (RED)

**The Iron Law applies here:** No skill generation (Phase 4) without baseline failure first.

**Delete means delete:** If any skill content was written before baseline testing, delete it. Don't keep it as "reference." Don't "adapt" it. Don't look at it. Start fresh after baseline failures are captured.

19. **Load reference**: Read `references/phase-3-baseline.md`
20. **Determine test type by skill type**:
    - **Discipline/Technique/Pattern**: Pressure scenarios (temptation to bypass)
    - **Reference**: Retrieval scenarios (can agent find and use info correctly?)
21. **Prepare isolated context** for baseline subagent:
    - Subagent receives ONLY: scenario setup + prompt
    - Subagent does NOT receive: Phase 1-2 discussion, requirements, skill drafts
22. **Create pressure scenarios** with:
    - **Format**: Forced A/B/C choice
    - **Framing**: "IMPORTANT: This is a real scenario. Choose and act."
    - **Pressures**: Combine 3+ (time, sunk cost, authority, economic, exhaustion, social, pragmatic)
    - **Details**: Real file paths, specific times, concrete consequences
    - **No outs**: Agent must choose, can't defer to user
23. **Run baseline** via Task tool for each scenario
24. **Capture verbatim**:
    - Which option agent chose
    - Exact rationalizations used (word-for-word)
25. **Validate baseline shows failure**:
    - If no failures: strengthen scenarios or reconsider need
26. **Build rationalization table** from all observed excuses
27. **Update metadata.verification.baseline**
28. **Update Session State** with testing context

### Phase 4: Generation

29. **Load reference**: Read `references/phase-4-generation.md`
30. **Write frontmatter** (validated in Phase 2) + operational fields

    **⚠️ Description Trap Warning:** The description field must contain ONLY triggering conditions ("Use when..."). Never summarize the skill's workflow in the description. Empirically verified: when descriptions summarize workflow, Claude follows the description instead of reading the full skill body.

31. **Generate sections in order**:
    1. Triggers
    2. When to Use
    3. When NOT to Use
    4. Inputs
    5. Outputs
    6. Procedure
    7. Decision Points
    8. Verification
    9. Troubleshooting
    10. Anti-Patterns
    11. Extension Points
32. **For each section**:
    a. Draft content informed by Phase 1-2 requirements + Phase 3 failures
    b. Validate against section requirements in reference
    c. Present draft to user
    d. User approves, edits, or requests regeneration
    e. Write approved section to SKILL.md
    f. Update Session State progress
33. **Rationalization table → Anti-Patterns**:
    | Rationalization (from baseline) | Counter (in skill) |
    |---------------------------------|--------------------|
    | "[exact phrase]" | "[explicit rebuttal]" |
34. **Create supporting files if needed**

### Phase 5: Verification Testing (GREEN)

35. **Prepare skill-injected context** for verification subagent:
    ```
    You must follow this skill for the task below.

    ---BEGIN SKILL---
    [full SKILL.md content]
    ---END SKILL---

    Context: [scenario setup]
    Task: [scenario prompt]
    ```
36. **For each pressure scenario from Phase 3**:
    a. Launch verification subagent via Task tool
    b. Capture response
    c. Compare to baseline: Did behavior change?
37. **Success criteria**:
    - Agent chose correct option
    - Agent cited skill sections as justification
    - Agent acknowledged temptation but followed rule
38. **On failure**:
    - Capture new rationalization verbatim
    - Return to Phase 4 to update skill
39. **Run meta-testing** if agent fails despite skill:
    ```
    You read the skill and chose Option [X] anyway.
    How could that skill have been written differently?
    ```
    **Interpret response and fix accordingly:**
    | Response | Diagnosis | Fix |
    |----------|-----------|-----|
    | "Skill WAS clear, I chose to ignore it" | Need foundational principle | Add "violating letter = violating spirit" |
    | "Skill should have said X" | Missing guidance | Add suggestion verbatim |
    | "I didn't see section Y" | Organization problem | Make key points more prominent |

40. **Update metadata.verification.testing**
41. **All scenarios must pass before proceeding**

### Phase 6: Refactor

42. **Determine skill type** (discipline, technique, pattern, reference)
43. **Check for new rationalizations** from Phase 5
44. **For each new rationalization, add ALL 4 counters**:
    a. Explicit negation in relevant section
    b. Entry in rationalization table (Anti-Patterns)
    c. Entry in red flags list
    d. Update description with violation symptom
45. **Address "Spirit vs Letter" arguments**:
    - Add foundational principle: "Violating the letter IS violating the spirit"
46. **Re-run verification** on updated skill
47. **Continue loop** if new rationalizations emerge
48. **Termination criteria** (all must be true):
    - All scenarios pass under maximum pressure
    - No new rationalizations observed
    - Agent cites skill sections as justification
    - Meta-testing confirms skill clarity

    **Bulletproof Signs** (skill is complete when all true):
    - [ ] Agent chooses correct option under maximum pressure
    - [ ] Agent cites skill sections as justification
    - [ ] Agent acknowledges temptation but follows rule
    - [ ] Meta-testing reveals "skill was clear, I should follow it"

49. **Update Session State** with refactor iterations

### Phase 7: Panel Review (Medium + High Risk)

50. **Check risk tier**:
    - Low → Skip to Phase 8, set `panel.status: skipped`
    - Medium/High → Continue with panel
51. **Launch 4 agents in parallel** via Task tool (see `references/phase-7-panel.md` for full prompts and tool permissions):
    - **Executability Auditor**: Steps unambiguous, decisions have defaults
    - **Semantic Coherence Checker**: Sections consistent, terminology uniform
    - **Dialogue Auditor**: Requirements complete, methodology substantive
    - **Adversarial Reviewer**: Decisions justified, failures mitigated
52. **Handle model fallback**: Opus → Sonnet → skip with warning
53. **Handle verdicts**:
    - All APPROVED → Proceed to Phase 8
    - Any CHANGES_REQUIRED → Classify severity, fix, re-test, re-submit
54. **Apply iteration limits**: 5 (progress) / escalate immediately (recurring) / 3 (different issues)
55. **Re-run tests after panel fixes** (structural changes may break behavior)
56. **Update Session State** with panel status

### Phase 8: Finalization

57. **Remove Session State**:
    - Locate `## Session State` (must be last H2)
    - Truncate from that point forward
58. **Update metadata.verification.panel**
59. **Verify supporting files exist** (if planned)
60. **Final validation via script**:
    ```bash
    python scripts/validate.py <skill-path>
    ```
61. **Confirm completion to user**:
    ```
    ✅ Skill created and verified.

    Created: <path>/SKILL.md
    Sections: 11/11

    Testing Evidence:
    - Baseline: N failures observed across N scenarios
    - Rationalizations captured: N
    - Verification: N/N scenarios passed
    - Refactor iterations: N

    Panel: [Unanimous APPROVED | Skipped (Medium risk)]

    Next: Test with "/<skill-name>" or promote to plugin
    ```

## Decision Points

### Triage Routing (Phase 0)

| Match Score | Action |
|-------------|--------|
| ≥80% | Recommend existing; ask to proceed or create anyway |
| 50-79% | Offer MODIFY or CREATE |
| <50% | Proceed to CREATE |
| Script unavailable | Warn, proceed to CREATE |

### Risk Tier Assessment (Phase 1)

| Tier | Criteria | Panel Required |
|------|----------|----------------|
| Low | Read-only, documentation, research | No |
| Medium | Code generation, refactoring, testing | Yes |
| High | Security, agentic, data operations, discipline-enforcing | Yes |

### Risk Tier Override Handling (Phase 1)

User may request to override assessed risk tier. Handle as follows:

**Downgrade validation (High → Medium):**
1. Check all 3 gating criteria:
   - Ask-first gates exist for every mutating step in Procedure
   - Scope is bounded and reversible (explicit scope fence)
   - Category justifies Medium (typical risk is Medium or lower)
2. If ALL pass: Allow, log "Downgraded to Medium — gating validated"
3. If ANY fail: Block, show "Cannot downgrade: [specific missing gate]"

**Cannot downgrade to Low:** User may NOT downgrade to Low if ANY mutating actions exist. This is non-negotiable — mutating actions require at minimum Medium tier with gating.

### Baseline Validation (Phase 3)

| Observation | Action |
|-------------|--------|
| Clear failures observed | Proceed to Phase 4 |
| No failures observed | Strengthen pressures; if still none, reconsider need |
| Partial failures | Add more pressures to consistent failures |

### Skill Type Testing Approach (Phase 6)

| Skill Type | Primary Test | Success Criteria |
|------------|--------------|------------------|
| Discipline-enforcing | Pressure scenarios | Follows rule under maximum pressure |
| Technique | Application scenarios | Applies correctly, handles edge cases |
| Pattern | Recognition + counter-example | Knows when to apply AND when not to |
| Reference | Retrieval + application | Finds and uses information correctly |

### Degrees of Freedom (Phase 4)

Match specificity to task fragility:

| Skill Type | Freedom Level | Guidance Style |
|------------|---------------|----------------|
| Discipline-enforcing | Low | Exact steps, explicit prohibitions |
| Technique | Medium | Steps with noted flexibility points |
| Pattern | High | Principles, not prescriptions |
| Reference | Low | Accurate information, clear retrieval paths |

**Signals to adjust:**
- Agent frequently deviates → increase specificity
- Users ignore skill as "too rigid" → increase freedom
- Edge cases cause failures → add explicit handling

### Panel Verdict Handling (Phase 7)

| Verdict | Action |
|---------|--------|
| All APPROVED | Proceed to Phase 8 |
| CHANGES_REQUIRED (Minor) | Fix, re-verify tests, re-submit panel |
| CHANGES_REQUIRED (Major) | Return to Phase 4 for regeneration |
| Agents contradict | Present to user, user decides |

**Severity classification:**
- Single section affected → Minor
- Multiple sections affected → Major
- Wording/clarity issue → Minor
- Design/decision issue → Major

**Default:** When uncertain about severity classification, escalate to Major (safer to over-correct than under-correct).

## Verification

### Quick Checks (Run After Each Phase)

| Phase | Check | Method |
|-------|-------|--------|
| 2 | Requirements locked | `metadata.decisions.requirements` has ≥1 explicit entry |
| 2 | Scenarios designed | Pressure scenarios documented with 3+ pressures each |
| 3 | Baseline captured | Failures and rationalizations documented verbatim |
| 4 | Section complete | Section present with correct H2 heading |
| 5 | Behavior changed | Same scenario, different outcome (documented) |
| 6 | Loopholes closed | All rationalizations have counters |
| 7 | Panel passed | All agents return APPROVED (or skipped) |
| 8 | Session State removed | No `## Session State` in final skill |

### Full Validation (Phase 8)

**[MUST] — Structural Requirements:**
- [ ] All 11 sections present with correct H2 headings
- [ ] Frontmatter parses as valid YAML
- [ ] `metadata.decisions` has required fields
- [ ] `metadata.verification` has required fields
- [ ] Session State removed from final skill

**[SHOULD] — Quality Requirements:**
- [ ] `requirements.implicit` non-empty
- [ ] `requirements.discovered` non-empty for non-trivial skills
- [ ] `approach.alternatives` includes ≥2 rejected with rationale
- [ ] `methodology_insights` has ≥5 substantive entries
- [ ] `verification.baseline.rationalizations_captured` non-empty
- [ ] `verification.testing.scenarios_passed` equals `baseline.scenarios_run`

### Test Quality Verification

**Pressure Scenario Quality:**

| Criterion | Good | Bad |
|-----------|------|-----|
| Pressure count | 3+ combined | Single pressure only |
| Format | Forced A/B/C choice | Open-ended question |
| Framing | "Choose and act" | "What should you do?" |
| Details | Real file paths, specific times | Abstract, vague |
| Escape routes | None | "I'd ask the user" allowed |

**Baseline Quality:**
- [ ] Test shows clear failure (agent chose wrong option)
- [ ] Failure is for expected reason (temptation, not confusion)
- [ ] Rationalizations captured verbatim
- [ ] Multiple scenarios show consistent failure pattern

**Verification Quality:**
- [ ] Same scenarios as baseline (not new ones)
- [ ] Same pressures applied (not softened)
- [ ] Agent chose correct option AND cited skill sections
- [ ] Behavior change documented (before/after comparison)

## Troubleshooting

### Triage Issues (Phase 0)

| Symptom | Cause | Recovery |
|---------|-------|----------|
| "command not found" | Python not available | Skip triage; proceed to CREATE with warning |
| Non-zero exit code | Script error | Log output; proceed to CREATE |
| Malformed JSON | Script bug | Ask user: create new or specify existing path |

### Requirements Discovery Issues (Phase 1)

| Symptom | Cause | Recovery |
|---------|-------|----------|
| User gives one-word answers | Questions too open | Switch to multiple choice |
| Dialogue going in circles | Requirements unclear | Summarize known, ask what's blocking |
| No pressure scenarios emerging | Testing lenses not applied | Re-apply Inversion, Adversarial, Constraint lenses |
| Reference file not found | Missing or moved | Warn user; proceed with inline knowledge; note degraded mode in Session State |

### Specification Checkpoint Issues (Phase 2)

| Symptom | Cause | Recovery |
|---------|-------|----------|
| User rejects specification | Requirements misunderstood | Return to Phase 1, clarify |
| User changes requirements after locking | Scope creep or correction | If correction: unlock, update. If creep: document as extension |
| Pressure scenarios rejected as unrealistic | Domain mismatch | Ask user for realistic examples |

### Baseline Testing Issues (Phase 3)

| Symptom | Cause | Recovery |
|---------|-------|----------|
| No failures observed | Scenarios too weak | Add 3+ combined pressures |
| Agent asks clarifying questions | Escape routes present | Remove "ask user" option |
| Agent fails for wrong reason | Scenario confusing | Rewrite with clearer setup |
| Agent already does right thing | Skill may not be needed | Reconsider need or find harder cases |
| Reference file not found | phase-3-baseline.md missing | Warn user; use inline pressure testing methodology; note in Session State |

### Generation Issues (Phase 4)

| Symptom | Cause | Recovery |
|---------|-------|----------|
| Section fails checklist | Content gaps | Review checklist, regenerate |
| User rejects section repeatedly | Misunderstanding requirements | Return to Phase 2, clarify |
| Skill exceeds 1000 lines | Scope creep | Split into focused skills |
| Reference file not found | phase-4-generation.md missing | Warn user; use inline section requirements; quality may be reduced |

### Verification Issues (Phase 5)

| Symptom | Cause | Recovery |
|---------|-------|----------|
| Agent fails despite skill | Skill incomplete | Meta-test, identify gap, update |
| Agent creates hybrid approach | Loopholes not closed | Add explicit negations |
| Agent argues skill is wrong | Foundational principle missing | Add "violating letter = violating spirit" |
| Agent complies but doesn't cite skill | Not discoverable | Improve triggers/description |

### Refactor Issues (Phase 6)

| Symptom | Cause | Recovery |
|---------|-------|----------|
| Same rationalization keeps appearing | Counter not strong enough | Make negation more explicit |
| New rationalizations each iteration | Fundamental gaps | Return to Phase 1, reconsider |
| Can't close after 5 iterations | Scope too broad | Split into focused skills |

### Panel Issues (Phase 7)

| Symptom | Cause | Recovery |
|---------|-------|----------|
| Model error on Opus | Quota/availability | Retry with Sonnet |
| All agents timeout | Network issue | Skip panel with warning |
| Contradictory verdicts | Genuine ambiguity | Present both, user decides |
| Same issues after 3 iterations | Design flaw | Return to Phase 2, reconsider |

### Finalization Issues (Phase 8)

| Symptom | Cause | Recovery |
|---------|-------|----------|
| validate.py fails with [MUST] | Missing required field | Fix violation, re-run |
| Supporting files not created | Forgot during Phase 4 | Create before finalizing |
| Session State still present | Finalization incomplete | Remove, re-save |

### Subagent Issues

| Symptom | Cause | Recovery |
|---------|-------|----------|
| Task tool returns error | Model unavailable | Retry with different model |
| Subagent doesn't return | Timeout | Kill, retry with simpler prompt |
| Baseline subagent has skill access | Isolation failed | Verify prompt contains ONLY scenario |

### Context Exhaustion

| Symptom | Cause | Recovery |
|---------|-------|----------|
| Responses becoming terse | Context filling | Save Session State, continue new session |
| Forgot earlier requirements | Context truncated | Re-read metadata.decisions |
| Skill sections inconsistent | Lost context | Run Semantic Coherence check |

## Anti-Patterns

### Process Anti-Patterns

| Pattern | Consequence | Instead |
|---------|-------------|---------|
| Skipping baseline testing | Don't know what to prevent | Always run WITHOUT skill first |
| Weak pressure scenarios | False confidence | Combine 3+ pressures |
| Paraphrasing rationalizations | Counters miss wording | Quote verbatim |
| Softening verification | Tests don't prove | Same pressure as baseline |
| Testing after writing skill | Violated Iron Law | Delete, start with baseline |

### Dialogue Anti-Patterns

| Pattern | Consequence | Instead |
|---------|-------------|---------|
| Multiple questions per message | User overwhelmed | One question at a time |
| Open-ended when options exist | Slower | Multiple choice when possible |
| Not seeding scenarios during dialogue | Disconnect | Each requirement → scenario |

### Lens Anti-Patterns

| Pattern | Consequence | Instead |
|---------|-------------|---------|
| All lenses superficially | "No findings" | Deep dive on High-relevance |
| Skipping testing lenses | No scenarios | Apply all 7 testing lenses |
| Not tracing to sections | Disconnected | "Lens: finding → section" |

### Testing Anti-Patterns

| Pattern | Consequence | Instead |
|---------|-------------|---------|
| Single pressure scenarios | Agent resists easily | Combine 3+ pressures |
| Open-ended scenarios | Agent theorizes | Force A/B/C choice |
| "What should you do?" | Agent won't act | "What do you do?" |
| Escape routes | Agent defers | Remove "ask user" option |
| No meta-testing after failure | Don't know why | Ask how skill could be clearer |

### Refactor Anti-Patterns

| Pattern | Consequence | Instead |
|---------|-------------|---------|
| Generic counters | Doesn't prevent | Quote exact phrase |
| Only updating Anti-Patterns | Loopholes remain | Update all 4 locations |
| Not re-verifying after changes | May break | Always re-verify |
| Stopping after first pass | New rationalizations | Continue until none |

### Panel Anti-Patterns

| Pattern | Consequence | Instead |
|---------|-------------|---------|
| Panel before tests pass | Review broken skill | Tests first |
| Skipping panel for High-risk | Issues missed | Panel required |
| Treating panel as behavioral | Doesn't prove works | Panel = structure; tests = behavior |

### Content Anti-Patterns

| Pattern | Consequence | Instead |
|---------|-------------|---------|
| Vague triggers | False positives | Specific verb+noun |
| "as appropriate" | Unexecutable | Exact action + condition |
| Description summarizes workflow | Claude skips body | Triggers only |
| Rationalization table without quotes | Miss nuance | Exact phrases |

### CSO Anti-Patterns

| Pattern | Consequence | Instead |
|---------|-------------|---------|
| First-person description | Inconsistent | Third-person ("Use when...") |
| **Description summarizes workflow** | **Claude skips skill body** | **Triggers only, never workflow** |
| No keyword coverage | Not found | Error messages, symptoms |
| Name is noun-based | Less discoverable | Verb-first, gerunds |

**Description Trap (Empirically Verified):** When skill description says "Use when X — does Y then Z", Claude may execute Y→Z from the description without reading SKILL.md body. Only include triggering conditions in description, never process summary.

### Red Flags — STOP and Reassess

- Baseline shows no failures
- Agent passes without citing skill
- Same rationalization 3+ iterations
- Panel finds issues tests didn't catch
- Skill exceeds 1000 lines
- User repeatedly rejects sections
- Verification softer than baseline

## Extension Points

### 1. Skill Type-Specific Workflows

Specialize process by skill type (discipline, technique, pattern, reference).

### 2. Batch Validation Mode

```bash
python scripts/validate.py --batch <skills-directory>
```

### 3. Category-Specific Integration

21 categories with tailored guidance. See `references/category-integration.md`.

| Category | Typical Risk | Dominant Failure Mode |
|----------|--------------|----------------------|
| debugging-triage | Medium | Missing regression guard |
| security-changes | High | Deny-path not verified |
| agentic-pipelines | High | Missing idempotency contract |
| data-migrations | High | Data loss or corruption |
| meta-skills | Low | Produced skills don't comply |
| ... | ... | ... |

### 4. Custom Panel Agents

Add domain-specific reviewers to panel configuration.

### 5. Panel Feedback History

Track what previous iterations flagged in metadata.

### 6. CI/CD Integration

Exit codes and JSON output for pipelines.

### 7. Skill Composition

Explicit requires/enhances/conflicts declarations.

### 8. Pressure Scenario Library

Reusable scenarios: time-pressure.md, sunk-cost.md, combined/.

### 9. Rationalization Pattern Library

Common rationalizations with proven counters.

### 10. Multi-Session Continuity

Enhanced Session State for resuming across sessions.

### 11. Skill Versioning

Track skill evolution with changelog.

### 12. Test Coverage Metrics

Track which requirements have corresponding tests.

### 13. Skill Deprecation

Mark deprecated with migration path.

## Core Differentiators

| From skillosophy | From writing-skills | New in Approach 2 |
|------------------|--------------------|--------------------|
| 11-section structure | TDD pressure testing | Combined 14 lenses (4+10) |
| Dialogue phases | Rationalization tables | Requirement→scenario traceability |
| Panel review (all skills) | Meta-testing | Panel for Medium+High only |
| metadata.decisions | Red flags lists | metadata.verification |
| Session State | Loophole closing | Phase 3 (RED) before Phase 4 |
| 21 categories | Skill types | Category + type + freedom integration |
| Regression questioning | Iron Law | Degrees of freedom calibration |

## Intentional Deviations

Documented decisions that differ from source materials:

| Source Guidance | Design Choice | Rationale |
|-----------------|---------------|-----------|
| writing-skills: "Only name and description in frontmatter" | Extended frontmatter (hooks, allowed-tools, metadata) | Source may be outdated; current platform supports extended fields |
| skillosophy: Panel required for all CREATE | Panel for Medium+High only | Right-sized rigor; Low-risk skills don't need structural review |
| writing-skills: Token efficiency targets (<150, <200, <500 words) | Not incorporated | Deferred; focus on correctness first, optimize later |
| skillosophy: Mode confidence percentages displayed | Thresholds only (≥80%, 50-79%, <50%) | Thresholds already communicate confidence; explicit % is implementation detail |

## Next Steps

1. Create working branch: `feature/rigorous-skill-creation`
2. Implement SKILL.md with all 11 sections
3. Create reference files (phase-1-requirements.md, phase-1-lenses.md, phase-3-baseline.md, phase-4-generation.md, phase-7-panel.md, risk-tiers.md, category-integration.md, persuasion-principles.md, anthropic-best-practices.md, testing-anti-patterns.md)
4. Create template files (skill-skeleton.md, decisions-schema.md, session-state-schema.md)
5. Create examples (worked-example.md)
6. Implement scripts (triage.py, discover.py, validate.py)
7. Test with real skill creation
8. Promote to metamarket when stable
