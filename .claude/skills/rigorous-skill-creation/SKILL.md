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