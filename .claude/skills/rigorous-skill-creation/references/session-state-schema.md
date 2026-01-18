# Session State Schema

Template for `## Session State` section (transient, removed after Phase 8 approval).

```markdown
## Session State
<!-- Removed automatically after Phase 8 finalization -->

**Phase:** 0-8
**Progress:** N/11 sections approved
**Last action:** What happened before interruption

### Dialogue Context
- User preference discovered
- Alternative considered and outcome
- Key insight from methodology
- Constraint or assumption validated

### Next Steps
- Specific next action (not "continue")
- What section/phase comes next
```

## Field Descriptions

| Field | Required | Description |
|-------|----------|-------------|
| `Phase` | Yes | Current phase (0=Triage, 1=Requirements, 2=Checkpoint, 3=Baseline, 4=Generation, 5=Verification, 6=Refactor, 7=Panel, 8=Finalization) |
| `Progress` | Yes | Sections approved out of 11 |
| `Last action` | Yes | What happened immediately before (for context on resume) |
| `Dialogue Context` | Should | Key exchanges, preferences, insights not yet in sections |
| `Next Steps` | Yes | Specific upcoming action |

## Extended Fields

These fields track rigorous-skill-creation workflow state beyond the base skillosophy schema.

### baseline (Phase 3)

Captures failures observed without the skill.

```yaml
baseline:
  scenarios:
    - name: "Time pressure + sunk cost"
      option_chosen: "B"
      rationalization: "exact quote from agent"
    - name: "Authority pressure"
      option_chosen: "C"
      rationalization: "exact quote from agent"
  total_failures: 2
```

| Field | Required | Description |
|-------|----------|-------------|
| `scenarios` | Yes | List of baseline test scenarios |
| `scenarios[].name` | Yes | Descriptive name for the scenario |
| `scenarios[].option_chosen` | Yes | The option the agent chose (A/B/C) |
| `scenarios[].rationalization` | Yes | Verbatim quote of agent's justification |
| `total_failures` | Yes | Count of scenarios where agent chose wrong option |

### verification (Phase 5)

Tracks verification testing results with skill injected.

```yaml
verification:
  scenarios_passed: 1
  scenarios_failed: 1
  new_rationalizations:
    - "new excuse discovered during verification"
```

| Field | Required | Description |
|-------|----------|-------------|
| `scenarios_passed` | Yes | Count of scenarios where agent chose correct option with skill |
| `scenarios_failed` | Yes | Count of scenarios where agent still failed despite skill |
| `new_rationalizations` | Should | Verbatim quotes of new excuses discovered during verification |

### refactor (Phase 6)

Tracks loophole-closing iterations.

```yaml
refactor:
  iteration: 2
  loopholes_closed: 3
```

| Field | Required | Description |
|-------|----------|-------------|
| `iteration` | Yes | Current refactor iteration (1-5 typical, escalate if same issues) |
| `loopholes_closed` | Yes | Count of rationalizations addressed with counters |

### panel (Phase 7)

Tracks multi-agent panel review status.

```yaml
panel:
  status: "pending"                   # pending | in_progress | approved | skipped
  agents_completed: 0
  issues_found: []
```

| Field | Required | Description |
|-------|----------|-------------|
| `status` | Yes | Current panel status: pending, in_progress, approved, skipped |
| `agents_completed` | Yes | Count of agents that have returned verdicts (0-4) |
| `issues_found` | Should | List of issues from agents requiring CHANGES_REQUIRED |

### degraded_mode

Tracks when reference files are unavailable and inline fallbacks are used.

```yaml
degraded_mode:
  - "testing-methodology.md not found; using inline methodology"
  - "persuasion-principles.md not found; skipping persuasion optimization"
```

| Field | Required | Description |
|-------|----------|-------------|
| `degraded_mode` | No | List of unavailable references and fallback actions taken |

## Lifecycle

| Phase | Session State Action |
|-------|---------------------|
| 0 | Not created yet |
| 1 | Create with initial values; set `requirements_locked: false` |
| 2 | Set `requirements_locked: true` after user validates |
| 3 | Populate `baseline` with failures and rationalizations |
| 4 | Update `progress` as sections complete (e.g., "3/11") |
| 5 | Update `verification` with pass/fail counts |
| 6 | Update `refactor` with iteration count and loopholes closed |
| 7 | Update `panel` status and issues |
| 8 | Remove entirely (truncate from `## Session State` to EOF) |

## Complete Example

```yaml
## Session State

phase: 5
progress: 8/11
requirements_locked: true
last_action: "Verification scenario 2 failed with new rationalization"

baseline:
  scenarios:
    - name: "Time pressure + sunk cost"
      option_chosen: "C"
      rationalization: "Tests after achieve the same goal. Being pragmatic."
    - name: "Works already + reference temptation"
      option_chosen: "B"
      rationalization: "Keep as reference, write tests, then adapt."
  total_failures: 2

verification:
  scenarios_passed: 1
  scenarios_failed: 1
  new_rationalizations:
    - "I'll write tests for the core path, the edge cases can wait"

refactor:
  iteration: 1
  loopholes_closed: 2

panel:
  status: "pending"
  agents_completed: 0
  issues_found: []

degraded_mode:
  - "persuasion-principles.md not found; skipping persuasion optimization"

### Dialogue Context
- User prefers explicit error handling over silent failures
- Considered single-pressure scenarios; rejected (too easy to resist)
- Inversion lens revealed "keep as reference" loophole

### Next Steps
- Address new rationalization in Anti-Patterns
- Re-run verification scenario 2
```

## Quality Guidelines

**next_steps -- specific vs. generic:**
- Good: "Generate Decision Points section, starting with user preference for fail-fast behavior"
- Poor: "Continue"
- Poor: "Proceed with remaining sections"

**dialogue_context -- capture decisions:**
- Good: "User prefers explicit error handling over silent failures"
- Poor: "Discussed error handling"

**baseline.rationalization -- verbatim quotes:**
- Good: "Tests after achieve the same goal. Being pragmatic."
- Poor: "Agent rationalized tests after"

**degraded_mode -- actionable notes:**
- Good: "testing-methodology.md not found; using inline methodology"
- Poor: "File missing"

## Recovery from Context Exhaustion

If context is exhausted mid-session:

1. Export current Session State (copy from SKILL.md)
2. Start new Claude Code session
3. Load the partial SKILL.md
4. Read `metadata.decisions` to restore requirements context
5. Read Session State to restore phase/progress
6. Continue from `last_action` and `Next Steps`

Session State is designed to contain everything needed to resume without re-doing earlier phases.
