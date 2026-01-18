# Phase Procedures

Detailed step-by-step procedures for each phase of rigorous skill creation.

## Phase 0: Triage

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

## Phase 1: Requirements Discovery

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
    - User's Skill idea

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
12. **Identify skill type** (see `type-specific-testing.md`):
    - Process/workflow: Enforces step sequence
    - Quality enhancement: Makes output "better"
    - Capability: Enables new abilities
    - Solution development: Problem → optimal solution
    - Meta-cognitive: Recognizes own state (uncertainty, errors, limits)
    - Recovery/Resilience: Handles failures gracefully
13. **Seed test scenarios** from each requirement, using type-appropriate templates
14. **Assess risk tier** (see `risk-tiers.md`)
15. **Select category** from 21 categories (see `category-integration.md`)
16. **Create Session State**

## Phase 2: Specification Checkpoint

17. **Build metadata.decisions** with all required fields
18. **Draft initial frontmatter**
19. **Present consolidated summary**:
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
20. **Iterate until user validates** — corrections loop back to Phase 1
21. **Lock decisions** — requirements and scenarios are now stable
22. **Update Session State**

## Phase 3: Baseline Testing (RED)

**The Iron Law:** No skill generation (Phase 4) without baseline failure first.

**Delete means delete:** If any skill content was written before baseline testing, delete it completely.

23. **Load testing methodology**: Read `testing-methodology.md` and `type-specific-testing.md`
24. **Select test approach based on skill type** (from Phase 1):
    - Process/workflow: Step completion under pressure, step order violation, early exit scenarios
    - Quality enhancement: Before/after comparison, rubric application, adversarial challenge
    - Capability: Can/can't tasks, edge case handling, novel application
    - Solution development: Process completeness + criteria coverage + adversarial challenge
    - Meta-cognitive: Recognition scenarios, calibration testing, false positive/negative checks
    - Recovery/Resilience: Failure injection, recovery strategy testing, cascading failure scenarios

25. **Verify subagent isolation** (canary check):
    - Launch test subagent: "What skill are we creating in this session? If you don't know, respond NO_CONTEXT."
    - Expected: "NO_CONTEXT"
    - If subagent knows the goal: Isolation failed → run baseline in fresh session

26. **Create test scenarios** using type-appropriate templates from `type-specific-testing.md`:
    - Process/workflow: Combine 3+ pressures, force A/B/C choice
    - Quality enhancement: Prepare baseline output for comparison
    - Capability: Identify tasks requiring the capability
    - Solution development: Prepare problems with known good solutions

27. **Run baseline** via Task tool (WITHOUT skill)
28. **Capture verbatim**: choices made, exact rationalizations, quality scores (if applicable)
29. **Validate baseline shows failure**: If no failures, strengthen scenarios or reconsider skill need
30. **Update metadata.verification.baseline**
31. **Update Session State**

## Phase 4: Generation

32. **Load checklists**: `section-checklists.md`
33. **Write frontmatter** + operational fields

    **Description Trap:** Description must contain ONLY triggering conditions. Never summarize workflow — Claude follows description instead of reading skill body.

34. **Generate sections in order**:
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

35. **For each section**:
    a. Draft content informed by Phase 1-2 requirements + Phase 3 failures
    b. Validate against checklist ([MUST] items required)
    c. Present draft to user
    d. User approves, edits, or requests regeneration
    e. Write approved section
    f. Update Session State progress

36. **Rationalization table → Anti-Patterns**: Map baseline rationalizations to explicit counters
37. **Create supporting files if needed**

## Phase 5: Verification Testing (GREEN)

38. **Prepare skill-injected context**:
    ```
    You must follow this skill for the task below.

    ---BEGIN SKILL---
    [full SKILL.md content]
    ---END SKILL---

    Context: [scenario setup]
    Task: [scenario prompt]
    ```

39. **Run same scenarios from Phase 3** WITH skill
40. **Success criteria** (type-specific):
    - Process/workflow: Agent chose correct option, cited skill sections
    - Quality enhancement: Rubric scores improved, criteria addressed, survives adversarial challenge
    - Capability: Task completed successfully
    - Solution development: Process complete, criteria covered, survives adversarial challenge
    - Meta-cognitive: Situation recognized, appropriate response, well-calibrated confidence
    - Recovery/Resilience: Failure recognized, appropriate recovery, no damage escalation

41. **On failure**: Capture new rationalization or gap, return to Phase 4
42. **Run meta-testing** if agent fails despite skill:
    ```
    You read the skill and chose Option [X] anyway.
    How could that skill have been written differently?
    ```

43. **Update metadata.verification.testing**
44. **All scenarios must pass before proceeding**

## Phase 6: Refactor

45. **Check for new rationalizations or gaps** from Phase 5
46. **For each new rationalization, apply 4-counter approach**:
    a. Explicit negation in relevant section
    b. Entry in rationalization table (Anti-Patterns)
    c. Entry in red flags list
    d. Update description with violation symptom

47. **Address "Spirit vs Letter" arguments**: Add "Violating letter IS violating spirit"
48. **Re-run verification** on updated skill
49. **Apply iteration limits**:
    - Progress made? Continue (up to 5)
    - Same issues recurring? Escalate immediately
    - Different issues? Continue (up to 3)

    On limit: "Cannot close loopholes. Options: (A) Accept risks, (B) Split into focused skills, (C) Abandon"

50. **Bulletproof criteria** (type-specific):
    - Process/workflow: Agent follows steps under maximum pressure, cites skill
    - Quality enhancement: Consistent rubric improvement, survives adversarial challenge
    - Capability: High success rate on target tasks
    - Solution development: Process complete, criteria covered, survives adversarial challenge
    - Meta-cognitive: High recognition rate, well-calibrated, low false positive/negative rates
    - Recovery/Resilience: High recovery rate, no damage escalation, clear communication

51. **Update Session State**

## Phase 7: Panel Review (Medium + High Risk)

52. **Check risk tier**: Low → Skip to Phase 8
53. **Load panel protocol**: Read `panel-protocol.md`
54. **Launch 4 agents in parallel** via Task tool:
    - Executability Auditor
    - Semantic Coherence Checker
    - Dialogue Auditor
    - Adversarial Reviewer

55. **Handle model fallback**: Opus → Sonnet → skip with warning
56. **Handle verdicts**:
    - All APPROVED → Phase 8
    - CHANGES_REQUIRED → Classify severity, fix, re-test, re-submit

57. **Iteration limits**: 5 (progress) / escalate (recurring) / 3 (different)
58. **Re-run tests after panel fixes**
59. **Update Session State**

## Phase 8: Finalization

60. **Remove Session State**: Locate `## Session State`, truncate from that point
61. **Update metadata.verification.panel**
62. **Verify supporting files exist**
63. **Review token efficiency** (soft guideline):
    - Aim for <500 words in SKILL.md body
    - Move details to references
    - Priority: Correctness > Clarity > Conciseness

64. **Final validation**:
    ```bash
    scripts/validate_skill.sh <skill-path>
    ```

    Fallback: Manual verify all 11 sections, YAML parses, metadata complete

65. **Confirm completion**:
    ```
    Skill created and verified.

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

## Verification Checklists

### Quick Checks (Per Phase)

| Phase | Check | Method |
|-------|-------|--------|
| 1 | Skill type identified | One of: Process, Quality, Capability, Solution Development |
| 2 | Requirements locked | metadata.decisions.requirements has ≥1 explicit entry |
| 2 | Scenarios designed | Type-appropriate templates used |
| 3 | Baseline captured | Failures documented (rationalizations, quality scores, or task failures) |
| 4 | Section complete | H2 heading present |
| 5 | Behavior changed | Type-specific success criteria met |
| 6 | Loopholes closed | All gaps addressed |
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

## Anti-Patterns

### Process Anti-Patterns

| Pattern | Consequence | Instead |
|---------|-------------|---------|
| Skipping baseline | Don't know what to prevent | Always run WITHOUT skill first |
| Weak pressure (single) | False confidence | Combine 3+ pressures |
| Paraphrasing rationalizations | Counters miss wording | Quote verbatim |
| Softening verification | Tests don't prove | Same pressure as baseline |
| Testing after writing skill | Violated Iron Law | Delete, start with baseline |

### Dialogue Anti-Patterns

| Pattern | Consequence | Instead |
|---------|-------------|---------|
| Multiple questions | User overwhelmed | One at a time |
| Open-ended when options exist | Slower | Multiple choice |
| Not seeding scenarios | Disconnect | Each requirement → scenario |

### Testing Anti-Patterns

| Pattern | Consequence | Instead |
|---------|-------------|---------|
| Single pressure | Easy resistance | 3+ pressures |
| Open-ended scenarios | Theorizing | Force A/B/C |
| "What should you do?" | No action | "What do you do?" |
| Escape routes | Agent defers | Remove "ask user" |
| No meta-testing | Don't know why | Ask how skill could be clearer |

### Content Anti-Patterns

| Pattern | Consequence | Instead |
|---------|-------------|---------|
| Vague triggers | False positives | Specific verb+noun |
| "as appropriate" | Unexecutable | Exact action + condition |
| Description summarizes workflow | Claude skips body | Triggers only |
| Rationalization without quotes | Miss nuance | Exact phrases |

### Red Flags — STOP and Reassess

- Baseline shows no failures
- Agent passes without citing skill
- Same rationalization 3+ iterations
- Panel finds issues tests didn't catch
- Skill exceeds 1000 lines
- User repeatedly rejects sections
- Verification softer than baseline
