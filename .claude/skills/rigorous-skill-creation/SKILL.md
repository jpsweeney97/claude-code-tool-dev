---
name: rigorous-skill-creation
description: Use when creating skills that need verified behavior change, especially
  high-risk skills (security, agentic, data operations) or skills that enforce discipline.
hooks:
  PostToolUse:
    - matcher: 'Write|Edit'
      hooks:
        - type: command
          command: '${SKILL_ROOT}/scripts/validate_skill.sh'
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

# rigorous-skill-creation

Orchestrated skill creation with structured requirements dialogue, baseline testing, and risk-based panel review. Creates skills with verified behavior change.

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
- **Skip triage**: Flag to bypass existing skill check (say "skip triage" or "create new skill")
- **Supporting file needs**: Discovered during Phase 1 if skill requires references/, examples/, scripts/

### Assumptions

- User has write access to target directory
- Python available for triage/validate scripts (graceful degradation if not)
- Task tool available for subagent operations (baseline testing, panel)
- Opus model preferred for panel agents (falls back to Sonnet)

### Critical Dependencies

**Subagent Context Isolation:** Baseline testing (Phase 3) depends on Task tool subagents starting with fresh context. Per Claude Code: "Each invocation creates a new instance with fresh context."

If isolation fails, baseline tests become contaminated — the subagent would "know" it's being tested.

**Verification:** Phase 3 includes a canary check to confirm isolation.

**Fallback:** If isolation cannot be confirmed, run baseline in a fresh Claude Code session.

## Outputs

### Primary Artifact

- **SKILL.md**: Complete skill with 11 sections + frontmatter

### Supporting Artifacts (skill-specific)

- **references/**: Heavy reference material (>100 lines) that would bloat SKILL.md
- **examples/**: Usage examples including worked-example.md walkthrough
- **scripts/**: Executable tools the skill needs at runtime

### Process Artifacts (verification evidence)

- **Baseline document**: Captured failures without skill
- **Verification evidence**: Before/after comparison proving behavior change
- **Rationalization table**: Observed excuses + counters (embedded in Anti-Patterns)

### Embedded Metadata

```yaml
metadata:
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
      - "Lens: finding → affected section"
  verification:
    baseline:
      scenarios_run: 3
      failures_observed: 3
      rationalizations_captured: ["exact phrase 1", "exact phrase 2"]
    testing:
      scenarios_passed: 3
      scenarios_failed: 0
    panel:
      status: "approved | skipped"
      agents_run: 4
```

### Definition of Done

- [ ] All 11 sections present and validated
- [ ] Supporting files created if needed
- [ ] Baseline failures documented
- [ ] All pressure scenarios pass with skill
- [ ] Rationalization table covers observed failure modes
- [ ] Panel unanimous (Medium/High) OR skipped (Low)
- [ ] Session State removed

## Procedure

### Phase 0: Triage

1. **Verify write access** — Check target directory is writable before investing in requirements discovery
2. **Parse user intent** — Identify if CREATE, MODIFY, or ambiguous. Default to CREATE if unclear after one question.
3. **Self-modification guard** — If target is within rigorous-skill-creation directory: STOP. "Cannot modify self — circular dependency."
4. **Check skip triage flag** — If set, log and proceed to Phase 1
5. **Run triage script**:
   ```bash
   python scripts/triage_skill_request.py "<user goal>" --json
   ```
6. **Handle triage result**:
   - ≥80% match: Recommend existing; ask to proceed or create anyway
   - 50-79% match: Offer MODIFY or CREATE
   - <50% match: Proceed to Phase 1
   - Script unavailable: Warn, proceed to Phase 1
7. **Initialize TodoWrite** with phase-level tasks

### Phase 1: Requirements Discovery

8. **Load methodology references**:
   - `references/thinking-lenses.md` (11 base lenses)
   - `references/regression-questions.md` (7 categories)
   - `references/extended-lenses.md` (3 testing lenses: 12-14)

9. **Apply 14 thinking lenses**:
   - Rapid scan all 14 for relevance (High/Medium/Low)
   - Deep dive on all High-relevance lenses
   - Resolve conflicts between lenses

   **Minimum coverage:**
   - All 14 lenses scanned
   - At least 3 yield actionable insights
   - All High-relevance fully applied

10. **Dialogue with user** (one question at a time):

    **Phase A — Broad Discovery:**
    - Purpose and success criteria
    - Constraints and non-negotiables
    - Who/what will use this skill

    **Phase B — Lens-Driven Deepening:**
    Select 2-3 regression question categories based on High-relevance lenses:

    | If lens flagged... | Probe with category... |
    |--------------------|------------------------|
    | Inversion, Adversarial | Failure Analysis |
    | Stakeholder, Ecosystem | Expert Simulation |
    | Evolution, Timelessness | Temporal Projection |
    | Constraint, Resource | Script/Automation Analysis |
    | Gap Detection, Edge Case | Missing Elements |

    **Stop when:** 2 consecutive probes yield no new insights

11. **Categorize requirements**: Explicit, Implicit, Discovered
12. **Seed pressure scenarios** from each requirement
13. **Assess risk tier** (see `references/risk-tiers.md`)
14. **Select category** from 21 categories (see `references/category-integration.md`)
15. **Create Session State**

### Phase 2: Specification Checkpoint

16. **Build metadata.decisions** with all required fields
17. **Draft initial frontmatter**
18. **Present consolidated summary**:
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

    **Approach:** [chosen] because [rationale]

    Does this capture your intent? Are the pressure scenarios right?
    ```
19. **Iterate until user validates** — corrections loop back to Phase 1
20. **Lock decisions** — requirements and scenarios are now stable
21. **Update Session State**

### Phase 3: Baseline Testing (RED)

**The Iron Law:** No skill generation (Phase 4) without baseline failure first.

**Delete means delete:** If any skill content was written before baseline testing, delete it completely.

22. **Load testing methodology**: Read `references/testing-methodology.md`
23. **Determine test type**:
    - Discipline-enforcing: Pressure scenarios
    - Technique: Application scenarios
    - Pattern: Recognition + counter-example
    - Reference: Retrieval scenarios

24. **Verify subagent isolation** (canary check):
    - Launch test subagent: "What skill are we creating in this session? If you don't know, respond NO_CONTEXT."
    - Expected: "NO_CONTEXT"
    - If subagent knows the goal: Isolation failed → run baseline in fresh session

25. **Create pressure scenarios** per `references/testing-methodology.md`:
    - Combine 3+ pressures: time, sunk cost, authority, economic, exhaustion, social, pragmatic
    - Force A/B/C choice, no escape routes

26. **Run baseline** via Task tool (WITHOUT skill)
27. **Capture verbatim**: option chosen, exact rationalizations
28. **Validate baseline shows failure**: If no failures, strengthen scenarios
29. **Update metadata.verification.baseline**
30. **Update Session State**

### Phase 4: Generation

31. **Load checklists**: `references/section-checklists.md`
32. **Write frontmatter** + operational fields

    **⚠️ Description Trap:** Description must contain ONLY triggering conditions. Never summarize workflow — Claude follows description instead of reading skill body.

33. **Generate sections in order**:
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

34. **For each section**:
    a. Draft content informed by Phase 1-2 requirements + Phase 3 failures
    b. Validate against checklist ([MUST] items required)
    c. Present draft to user
    d. User approves, edits, or requests regeneration
    e. Write approved section
    f. Update Session State progress

35. **Rationalization table → Anti-Patterns**: Map baseline rationalizations to explicit counters
36. **Create supporting files if needed**

### Phase 5: Verification Testing (GREEN)

37. **Prepare skill-injected context**:
    ```
    You must follow this skill for the task below.

    ---BEGIN SKILL---
    [full SKILL.md content]
    ---END SKILL---

    Context: [scenario setup]
    Task: [scenario prompt]
    ```

38. **Run same scenarios from Phase 3** WITH skill
39. **Success criteria**:
    - Agent chose correct option
    - Agent cited skill sections as justification
    - Agent acknowledged temptation but followed rule

40. **On failure**: Capture new rationalization, return to Phase 4
41. **Run meta-testing** if agent fails despite skill:
    ```
    You read the skill and chose Option [X] anyway.
    How could that skill have been written differently?
    ```

42. **Update metadata.verification.testing**
43. **All scenarios must pass before proceeding**

### Phase 6: Refactor

44. **Check for new rationalizations** from Phase 5
45. **For each new rationalization, apply 4-counter approach**:
    a. Explicit negation in relevant section
    b. Entry in rationalization table (Anti-Patterns)
    c. Entry in red flags list
    d. Update description with violation symptom

46. **Address "Spirit vs Letter" arguments**: Add "Violating letter IS violating spirit"
47. **Re-run verification** on updated skill
48. **Apply iteration limits**:
    - Progress made? Continue (up to 5)
    - Same issues recurring? Escalate immediately
    - Different issues? Continue (up to 3)

    On limit: "Cannot close loopholes. Options: (A) Accept risks, (B) Split into focused skills, (C) Abandon"

49. **Bulletproof criteria**:
    - [ ] Agent chooses correct option under maximum pressure
    - [ ] Agent cites skill sections
    - [ ] Agent acknowledges temptation but follows rule
    - [ ] Meta-test reveals "skill was clear"

50. **Update Session State**

### Phase 7: Panel Review (Medium + High Risk)

51. **Check risk tier**: Low → Skip to Phase 8
52. **Load panel protocol**: Read `references/panel-protocol.md`
53. **Launch 4 agents in parallel** via Task tool:
    - Executability Auditor
    - Semantic Coherence Checker
    - Dialogue Auditor
    - Adversarial Reviewer

54. **Handle model fallback**: Opus → Sonnet → skip with warning
55. **Handle verdicts**:
    - All APPROVED → Phase 8
    - CHANGES_REQUIRED → Classify severity, fix, re-test, re-submit

56. **Iteration limits**: 5 (progress) / escalate (recurring) / 3 (different)
57. **Re-run tests after panel fixes**
58. **Update Session State**

### Phase 8: Finalization

59. **Remove Session State**: Locate `## Session State`, truncate from that point
60. **Update metadata.verification.panel**
61. **Verify supporting files exist**
62. **Review token efficiency** (soft guideline):
    - Aim for <500 words in SKILL.md body
    - Move details to references
    - Priority: Correctness > Clarity > Conciseness

63. **Final validation**:
    ```bash
    scripts/validate_skill.sh <skill-path>
    ```

    Fallback: Manual verify all 11 sections, YAML parses, metadata complete

64. **Confirm completion**:
    ```
    ✅ Skill created and verified.

    Created: <path>/SKILL.md
    Sections: 11/11

    Testing Evidence:
    - Baseline: N failures across N scenarios
    - Rationalizations captured: N
    - Verification: N/N scenarios passed
    - Refactor iterations: N

    Panel: [Unanimous APPROVED | Skipped]

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
| Ambiguous | One clarifying question; if still unclear, CREATE |

### Risk Tier Assessment (Phase 1)

| Tier | Criteria | Panel Required |
|------|----------|----------------|
| Low | Read-only, documentation, research | No |
| Medium | Code generation, refactoring, testing | Yes |
| High | Security, agentic, data, discipline-enforcing | Yes |

### Risk Tier Override

**Downgrade validation (High → Medium):**
1. Ask-first gates exist for every mutating step
2. Scope is bounded and reversible
3. Category justifies Medium

If ALL pass: Allow. If ANY fail: Block.

**Cannot downgrade to Low** if any mutating actions exist.

### Baseline Validation (Phase 3)

| Observation | Action |
|-------------|--------|
| Clear failures | Proceed to Phase 4 |
| No failures | Strengthen pressures; if still none, reconsider need |
| Partial failures | Add more pressures |

### Skill Type Testing (Phase 6)

| Type | Primary Test | Success Criteria |
|------|--------------|------------------|
| Discipline-enforcing | Pressure scenarios | Follows rule under max pressure |
| Technique | Application scenarios | Applies correctly |
| Pattern | Recognition + counter | Knows when and when not |
| Reference | Retrieval scenarios | Finds and uses correctly |

### Panel Verdict (Phase 7)

| Verdict | Action |
|---------|--------|
| All APPROVED | Phase 8 |
| CHANGES_REQUIRED (Minor) | Fix, re-verify, re-submit |
| CHANGES_REQUIRED (Major) | Return to Phase 4 |
| Agents contradict | Present to user, user decides |

**Severity:**
- Single section affected → Minor
- Multiple sections → Major
- Wording issue → Minor
- Design issue → Major

Default: Uncertain → Major

## Verification

### Quick Checks (Per Phase)

| Phase | Check | Method |
|-------|-------|--------|
| 2 | Requirements locked | metadata.decisions.requirements has ≥1 explicit entry |
| 2 | Scenarios designed | 3+ pressures documented per scenario |
| 3 | Baseline captured | Failures and rationalizations documented verbatim |
| 4 | Section complete | H2 heading present |
| 5 | Behavior changed | Same scenario, different outcome documented |
| 6 | Loopholes closed | All rationalizations have counters |
| 7 | Panel passed | All agents APPROVED (or skipped) |
| 8 | Session State removed | No `## Session State` |

### Full Validation (Phase 8)

**[MUST] — Structural:**
- [ ] All 11 sections with correct H2 headings
- [ ] Frontmatter parses as valid YAML
- [ ] metadata.decisions has required fields
- [ ] metadata.verification has required fields
- [ ] Session State removed

**[SHOULD] — Quality:**
- [ ] requirements.implicit non-empty
- [ ] requirements.discovered non-empty (non-trivial skills)
- [ ] approach.alternatives ≥2 with rationale
- [ ] methodology_insights ≥5 substantive
- [ ] rationalizations_captured non-empty
- [ ] scenarios_passed = baseline.scenarios_run

### Pressure Scenario Quality

| Criterion | Good | Bad |
|-----------|------|-----|
| Pressure count | 3+ combined | Single |
| Format | Forced A/B/C | Open-ended |
| Framing | "Choose and act" | "What should you do?" |
| Details | Real paths, times | Vague |
| Escape routes | None | "I'd ask the user" allowed |

### Baseline Quality

- [ ] Test shows clear failure (wrong option)
- [ ] Failure for expected reason (temptation, not confusion)
- [ ] Rationalizations captured verbatim
- [ ] Multiple scenarios show consistent pattern

### Verification Quality

- [ ] Same scenarios as baseline
- [ ] Same pressures (not softened)
- [ ] Agent chose correct AND cited skill
- [ ] Before/after comparison documented

## Troubleshooting

### Triage Issues (Phase 0)

| Symptom | Cause | Recovery |
|---------|-------|----------|
| "command not found" | Python not available | Skip triage; proceed to CREATE |
| Non-zero exit | Script error | Log; proceed to CREATE |
| Malformed JSON | Script bug | Ask user: create or specify path |

### Baseline Issues (Phase 3)

| Symptom | Cause | Recovery |
|---------|-------|----------|
| Canary fails | Context leaking | Run baseline in fresh session |
| No failures | Scenarios too weak | Add 3+ combined pressures |
| Agent asks questions | Escape routes | Remove "ask user" option |
| Fails for wrong reason | Confusing scenario | Rewrite with clearer setup |
| Already does right thing | May not need skill | Find harder cases |

### Generation Issues (Phase 4)

| Symptom | Cause | Recovery |
|---------|-------|----------|
| Section fails checklist | Content gaps | Review checklist, regenerate |
| User rejects repeatedly | Requirements mismatch | Return to Phase 2 |
| Exceeds 1000 lines | Scope creep | Split into focused skills |

### Verification Issues (Phase 5)

| Symptom | Cause | Recovery |
|---------|-------|----------|
| Fails despite skill | Skill incomplete | Meta-test, identify gap |
| Hybrid approach | Loopholes not closed | Add explicit negations |
| Argues skill is wrong | Missing principle | Add "letter = spirit" |
| Complies but no citation | Not discoverable | Improve triggers |

### Panel Issues (Phase 7)

| Symptom | Cause | Recovery |
|---------|-------|----------|
| Model error on Opus | Quota | Retry with Sonnet |
| All timeout | Network | Skip panel with warning |
| Contradictory | Genuine ambiguity | Present both; user decides |
| Same issues 3+ times | Design flaw | Return to Phase 2 |

### Context Exhaustion

| Symptom | Cause | Recovery |
|---------|-------|----------|
| Terse responses | Context filling | Save Session State, new session |
| Forgot requirements | Truncated | Re-read metadata.decisions |
| Sections inconsistent | Lost context | Run Semantic Coherence |

### Abort/Rollback

| Trigger | Action |
|---------|--------|
| User requests abort | Confirm; delete skill-dir; clear TodoWrite |
| Unrecoverable error | Preserve Session State; ask user |
| Out of scope | Document why; offer simpler skill or abort |

**Cleanup:**
- Delete partial SKILL.md
- Delete partial supporting files
- Clear TodoWrite
- Notify: "Skill creation aborted. No artifacts remain."