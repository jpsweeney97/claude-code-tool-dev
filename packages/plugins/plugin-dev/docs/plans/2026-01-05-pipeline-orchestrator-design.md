# Pipeline Orchestrator Design

**Status:** Draft
**Created:** 2026-01-05
**Last Updated:** 2026-01-05
**ADR Reference:** [ADR-001: Plugin Development Pipeline Architecture](../ADR-001-plugin-development-pipeline.md)

## Problem Statement

The plugin-dev plugin has a staged pipeline architecture (ADR-001) with specialized skills for each phase:

- **Triage:** `brainstorming-plugins`
- **Design:** `brainstorming-{skills,hooks,agents,commands}`
- **Implementation:** `implementing-{skills,hooks,agents,commands}`
- **Optimization:** `optimizing-plugins`
- **Deployment:** `deploying-plugins`

However, the current `/create-plugin` command predates these skills and doesn't orchestrate them. Users must manually invoke the right skill at each stage, track their own progress, and manage handoffs between stages.

### Problems Identified (Three-Lens Audit)

| Problem | Source |
|---------|--------|
| No session resume mechanism | All 3 lenses |
| Validation is advisory, not enforced | All 3 lenses |
| Pipeline overhead kills simple cases | All 3 lenses |
| Multi-component integration untested | Adversarial + Implementation |
| Reference skills duplicate implementing-X | Adversarial + Cost/Benefit |
| Design artifacts not validated for quality | Adversarial + Implementation |

### Goal

Design a **smart router orchestrator** that:
1. Analyzes complexity and recommends appropriate paths
2. Manages state across sessions
3. Invokes the right skills at the right time via custom subagents
4. Supports path graduation (quick → standard → full)
5. Tracks learnings for future reference

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        ORCHESTRATOR                                  │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │  Complexity  │  │    Path      │  │    State     │              │
│  │  Analyzer    │  │   Router     │  │   Manager    │              │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │
│         │                 │                 │                       │
│         └─────────────────┼─────────────────┘                       │
│                           │                                         │
│                           ▼                                         │
│                  ┌─────────────────┐                               │
│                  │ Subagent        │                               │
│                  │ Dispatcher      │                               │
│                  └────────┬────────┘                               │
└───────────────────────────┼─────────────────────────────────────────┘
                            │
          ┌─────────────────┼─────────────────┐
          │                 │                 │
          ▼                 ▼                 ▼
   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
   │  pipeline-  │  │  pipeline-  │  │  pipeline-  │
   │  designer   │  │ implementer │  │  optimizer  │
   │             │  │             │  │             │
   │  skills:    │  │  skills:    │  │  skills:    │
   │  brainstorm-│  │  implement- │  │  optimizing-│
   │  ing-*      │  │  ing-*      │  │  plugins    │
   └─────────────┘  └─────────────┘  └─────────────┘
```

### Key Principles

1. **Evidence-backed recommendations** — Orchestrator analyzes, recommends, user decides
2. **Explicit state** — State file tracks progress; artifact inference for re-entry
3. **Skill isolation** — Custom subagents have explicit skill access; orchestrator routes
4. **Path flexibility** — Enter at any stage, graduate between paths, resume across sessions

---

## Complexity Analysis

The orchestrator performs complexity analysis at entry to recommend an appropriate path.

### Signals (Priority Order)

| Signal | Detection Method | Impact |
|--------|------------------|--------|
| **Component count** | Parse request for: skill, hook, agent, command, MCP mentions | 1 = simple; 2+ = coordination needed |
| **Target audience** | Ask: "Personal use or wider distribution?" | Personal = lower bar; Marketplace = full rigor |
| **External dependencies** | Keywords: "database", "API", "MCP", "external", service names | External deps = integration risk |

### Mid-Flow Escalation Trigger

| Signal | When Detected | Action |
|--------|---------------|--------|
| **Cross-component contracts** | During implementation, when one component assumes behavior of another | Surface to user, suggest adding integration test stage |

### Analysis Output

The orchestrator presents analysis with evidence:

```
## Complexity Analysis

**Component count:** 2 (skill + hook)
**Target audience:** Marketplace
**External dependencies:** MCP postgres server

**Recommendation:** Standard path
**Reasoning:** Multiple components + external MCP = coordination complexity.
              Marketplace target = quality bar requires design + validation.

Paths available:
- Quick: Skip design, implement directly (not recommended for this case)
- Standard: Design → Implement → Integration test (recommended)
- Full: Design → Implement → Optimize → Deploy
```

User chooses; orchestrator records choice in state.

---

## Paths

### Quick Path

**When:** Single component, personal use, no external deps

```
Triage → Implement → Done
```

- Skips formal design document
- Implementing skill asks clarifying questions inline
- No optimization stage
- Exit: Working component for personal use

### Standard Path

**When:** Multiple components OR external deps OR marketplace target

```
Triage → Design (per component) → Implement (per component) → Integration Test → Done/Publish-prep
```

- Design document per component
- Full TDD implementation
- Integration testing for cross-component contracts
- Exit: Done (personal) or continue to Publish-prep

### Full Path

**When:** Complex + marketplace quality required

```
Triage → Design → Implement → Optimize → Deploy → Published
```

- All standard path stages
- Six-lens optimization
- Deployment to marketplace
- Exit: Published plugin

### Path Comparison

| Aspect | Quick | Standard | Full |
|--------|-------|----------|------|
| Design docs | No | Yes | Yes |
| Integration test | No | Yes | Yes |
| Optimization | No | Optional | Yes |
| Deployment | Manual | Manual | Guided |
| Estimated overhead | +5 min | +30 min | +60 min |
| Best for | Personal tools | Team/quality plugins | Marketplace |

---

## Path Graduation

Plugins can graduate from one path to another as needs evolve.

### Detection

When user returns to an existing plugin:

1. **State file exists** → Resume from recorded state
2. **No state file, artifacts exist** → Infer state from artifacts
3. **No state file, no artifacts** → Fresh start

### Graduation Options

```
Quick path completed
        │
        ▼
┌───────────────────────────────────────┐
│ "I want to improve this plugin"       │
│                                       │
│ Orchestrator detects:                 │
│ • Existing component(s) at [path]     │
│ • No design doc exists                │
│ • Not optimized                       │
│ • Not deployed                        │
└───────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────┐
│ Options:                              │
│ A) Retrofit design doc                │
│ B) Run optimization (6 lenses)        │
│ C) Prepare for marketplace (full)     │
│ D) Add more components (extend)       │
└───────────────────────────────────────┘
```

### Behaviors

| Action | What happens |
|--------|--------------|
| **Retrofit design doc** | Generate design doc from existing implementation (document rationale) |
| **Run optimization** | Enter optimization stage; existing components treated as input |
| **Prepare for marketplace** | Optimization → Deployment stages |
| **Add components** | Return to triage with existing components acknowledged |

---

## State Management

### State File

**Location:** `docs/plans/plugin-state.json` (in plugin directory)

**When created:** On first orchestrator invocation for a plugin

**When updated:** After each stage transition, decision, or learning

### Schema

```json
{
  "schema_version": "1.0",
  "plugin": "my-plugin",
  "path": "/path/to/plugin",
  "created": "2026-01-05T12:00:00Z",
  "updated": "2026-01-05T14:30:00Z",

  "analysis": {
    "component_count": 2,
    "target_audience": "marketplace",
    "external_deps": ["mcp:postgres", "api:github"],
    "recommended_path": "standard",
    "reasoning": "2 components + external MCP = standard path"
  },

  "chosen_path": "standard",

  "decisions": {
    "skill:my-skill": {
      "design_approach": "light",
      "trigger_strategy": "explicit command only"
    }
  },

  "components": [
    {
      "type": "skill",
      "name": "my-skill",
      "stage": "implementing",
      "design_doc": "docs/plans/2026-01-05-my-skill-design.md",
      "artifacts": ["skills/my-skill/SKILL.md"],
      "validation": { "passed": true, "last_run": "2026-01-05T14:00:00Z" }
    },
    {
      "type": "hook",
      "name": "validate-writes",
      "stage": "pending",
      "design_doc": null,
      "artifacts": []
    }
  ],

  "integration": {
    "status": "pending",
    "contracts": ["skill:my-skill assumes hook:validate-writes blocks invalid paths"],
    "test_results": null
  },

  "learnings": [
    {
      "stage": "implementing",
      "component": "hook:validate-writes",
      "type": "gotcha",
      "description": "Exit code 2 shows stderr to Claude, not user",
      "resolution": "Made error messages instructional for Claude",
      "timestamp": "2026-01-05T13:45:00Z"
    }
  ],

  "escalation_triggers": [],
  "blockers": []
}
```

### Learning Types

| Type | Meaning |
|------|---------|
| `gotcha` | Unexpected behavior / easy mistake |
| `lesson` | General insight worth remembering |
| `workaround` | Limitation that required creative solution |
| `assumption_violated` | Something we thought was true but wasn't |

### Artifact Inference (for re-entry)

When no state file exists but artifacts are present:

| Artifact Found | Inferred State |
|----------------|----------------|
| `plugin.json` | Plugin exists |
| `skills/*/SKILL.md` | Skill implemented |
| `hooks/*.py` | Hook implemented |
| `docs/plans/*-design.md` | Design completed |
| Design doc but no implementation | Design stage complete, implementation pending |

---

## Skill Invocation

### Constraint

From official Claude Code docs:
> "Built-in agents (Explore, Plan, Verify) and the Task tool do **not** have access to your Skills"

Only custom subagents defined in `.claude/agents/` with explicit `skills` field can access skills.

### Custom Subagents

The orchestrator uses three custom subagents:

#### pipeline-designer

**Purpose:** Execute design phases
**Skills:** `brainstorming-skills`, `brainstorming-hooks`, `brainstorming-agents`, `brainstorming-commands`, `brainstorming-plugins`

#### pipeline-implementer

**Purpose:** Execute implementation phases
**Skills:** `implementing-skills`, `implementing-hooks`, `implementing-agents`, `implementing-commands`

#### pipeline-optimizer

**Purpose:** Execute optimization phase
**Skills:** `optimizing-plugins`

### Invocation Pattern

```
Orchestrator (main thread)
    │
    ├─ Complexity analysis (inline)
    ├─ Path recommendation (inline)
    ├─ State management (inline)
    │
    └─ Stage execution (delegated)
           │
           ▼
       Task tool → custom subagent with skills
           │
           ▼
       Subagent returns: artifacts created, decisions made, learnings
           │
           ▼
       Orchestrator updates state file
```

---

## Entry Points

### Command Entry

**File:** `commands/create-plugin.md` (replaces legacy)

```yaml
---
description: Guided plugin creation with complexity analysis and state management
argument-hint: [plugin description or path to existing plugin]
allowed-tools: Read, Write, Bash, Task, Glob, Grep, TodoWrite, AskUserQuestion
---
```

**Invocation:**
- `/create-plugin` — Start new plugin
- `/create-plugin A plugin for managing database migrations` — Start with description
- `/create-plugin ./my-existing-plugin` — Resume or graduate existing plugin

### Skill Entry

**File:** `skills/pipeline-orchestrator/SKILL.md`

**Description:** Triggers on natural language requests to build, create, or improve plugins.

**Trigger phrases:**
- "build a plugin for X"
- "create a plugin that does Y"
- "help me improve my plugin"
- "I want to publish this plugin"

### Relationship

Both entry points invoke the same orchestrator logic. The command is explicit; the skill is discoverable via natural language.

---

## Error Handling & Recovery

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     ERROR HANDLING LAYERS                        │
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐ │
│  │   Checkpoint     │  │  Reconciliation  │  │    Session    │ │
│  │   System         │  │     Engine       │  │    Manager    │ │
│  │                  │  │                  │  │               │ │
│  │  • Progress      │  │  • State/artifact│  │  • Resume UX  │ │
│  │    tracking      │  │    merge         │  │  • Context    │ │
│  │  • Retry logic   │  │  • Conflict      │  │    restore    │ │
│  │  • Resume ctx    │  │    resolution    │  │  • Learning   │ │
│  │                  │  │  • Backup        │  │    capture    │ │
│  └────────┬─────────┘  └────────┬─────────┘  └───────┬───────┘ │
│           │                     │                    │          │
│           └─────────────────────┼────────────────────┘          │
│                                 │                               │
│                                 ▼                               │
│                    ┌────────────────────────┐                   │
│                    │    State File          │                   │
│                    │  plugin-state.json     │                   │
│                    └────────────────────────┘                   │
└─────────────────────────────────────────────────────────────────┘
```

### Checkpoint System

**Purpose:** Track subagent progress to enable recovery from execution failures.

| Aspect | Design |
|--------|--------|
| **Location** | `docs/plans/.checkpoint-{stage}.jsonl` |
| **Format** | JSON Lines (append-only) |
| **Granularity** | Adaptive: coarse default, fine for high-risk stages |
| **Events tracked** | `stage_start`, `artifact_created`, `decision`, `validation_*`, `learning`, `error`, `stage_complete` |

**High-risk triggers (fine granularity):**
- External dependencies (MCP, APIs)
- Multi-file operations
- Long-running stages (>2 min)
- Validation phases

### Failure Classification & Recovery

| Classification | Detection Signals | Recovery Action |
|----------------|-------------------|-----------------|
| **Transient** | Network timeout, MCP connection failed, rate limit | Auto-retry (max 2, backoff 5s/15s) |
| **Deterministic** | Context limit, permission error, validation failed | User prompt with options |
| **Ambiguous** | User abort, no checkpoint + failure | User prompt |

**User Prompt Options:**
- Retry stage (fresh start)
- Resume from checkpoint (skip completed work)
- Skip stage (mark as manual)
- Abort pipeline

**Resume Context for Subagent:**
- Original task description
- Progress summary from checkpoint
- Decisions made so far
- Artifacts already created
- Explicit "continue from" instruction

### State Reconciliation

**Purpose:** Maintain consistency between state file and actual artifacts.

**Triggers:**
- Orchestrator entry (every invocation)
- Stage transition
- Resume from checkpoint
- User request

**Merge Strategy (Conservative):**

| Situation | Resolution |
|-----------|------------|
| Artifact exists + state agrees | ✓ Consistent |
| Artifact exists + state silent | Add as "discovered" |
| Artifact exists + state says "pending" | Update to "complete" |
| Artifact missing + state says exists | **Ask user** |
| Checkpoint exists + state not updated | Apply checkpoint |

**Backup Policy:**
- Create `plugin-state.json.bak` before conflict resolution or corruption recovery
- Single backup file, overwritten each time
- Normal additive reconciliation: no backup

### Session Management

**Resume UX (on return):**

```
## Resuming: my-plugin

Last active: [date]
Path: [Standard/Quick/Full]
Current stage: [stage] → [component]

### Progress
[Table of components and their status]

### Key Decisions Made
[List of important decisions]

### What's Next
[Numbered list of upcoming steps]

Options: Resume | Review decisions | Start fresh | Switch component
```

- Summary length: Same always (user can skim)
- Always show full context restore + options

**Pause Mechanisms:**

| Type | Trigger | Behavior |
|------|---------|----------|
| Implicit | User leaves | Checkpoint preserves state |
| Explicit | `/pause` or "let's stop" | Full handoff with learning prompt |

**Learning Capture:**
- Always prompt at stage completion
- Prompt on explicit pause
- Prompt when errors occur and user stops
- Stored in checkpoint + state file

### Error Handling Files

```
docs/plans/
├── plugin-state.json        # Source of truth (decisions, learnings, progress)
├── plugin-state.json.bak    # Backup before conflict resolution
├── .checkpoint-design.jsonl # Active checkpoint (gitignored)
└── 2026-01-05-*-design.md   # Design documents
```

---

## Integration Testing

### Scope

Integration tests verify **observable, external behavior** — not Claude's internal logic.

| Testable | Not Testable |
|----------|--------------|
| Hook blocking behavior | Skill decision logic |
| State transitions (files created/modified) | Claude's reasoning |
| Audit log entries | Prompt interpretation |
| Exit codes and stderr | Skill-to-skill interaction |

**Primary value:** Verifying hooks work as contracts specify. This catches the most likely integration failures — a skill assuming a hook protects it, but the hook doesn't.

### Test Categories

| Category | Purpose | Example |
|----------|---------|---------|
| **Contract** | Verify component assumes correct behavior from another | Hook blocks writes skill relies on |
| **End-to-end** | Verify user-facing flows produce expected state | Command creates expected files |
| **Failure propagation** | Verify failures surface correctly | Hook block produces correct error |

### File Structure

```
docs/plans/
├── integration-tests.md     # Scenario definitions (static)
├── plugin-state.json        # Results in integration.results[] (dynamic)
└── .hook-audit.log          # Test artifact (gitignored)
```

### Scenario Format

```markdown
# Integration Tests

## Environment Setup
\`\`\`bash
export CLAUDE_HOOK_AUDIT_ENABLED=1
export CLAUDE_HOOK_AUDIT_LOG=.hook-audit.log
\`\`\`

## Scenarios

### hook-blocks-etc-writes

**Category:** contract
**Contract:** hook:block-etc blocks writes to /etc/*
**Components:** hook:block-etc

#### Setup
\`\`\`bash
rm -f .hook-audit.log
\`\`\`

#### Action
\`\`\`bash
# Attempt write that hook should block
echo "test" > /etc/test-file
\`\`\`

#### Verify
\`\`\`bash
test ! -f /etc/test-file && echo "PASS:file-blocked" || echo "FAIL:file-created"
grep -q '"decision":"block"' .hook-audit.log && echo "PASS:logged" || echo "FAIL:no-log"
\`\`\`
```

### Hook Testability Requirements

Hooks referenced in integration test contracts must include audit logging:

```python
#!/usr/bin/env python3
import os, json, sys
from datetime import datetime

hook_input = json.loads(sys.stdin.read())

# Audit logging (enable with CLAUDE_HOOK_AUDIT_ENABLED=1)
if os.getenv("CLAUDE_HOOK_AUDIT_ENABLED"):
    log_path = os.getenv("CLAUDE_HOOK_AUDIT_LOG", ".hook-audit.log")
    with open(log_path, "a") as f:
        f.write(json.dumps({
            "timestamp": datetime.now().isoformat(),
            "tool": hook_input.get("tool_name"),
            "decision": "block",
            "reason": "..."
        }) + "\n")

print("Blocked: reason", file=sys.stderr)
sys.exit(2)
```

**Policy:**

| Scenario | Audit logging |
|----------|---------------|
| Hook with no cross-component contract | Recommended (template provided) |
| Hook referenced in integration test contract | Required |
| Quick path hooks | Not required |

### Contract Surfacing

Contracts are explicitly surfaced by the implementation subagent, not auto-detected.

**Pipeline-implementer instruction:**

> When your implementation assumes behavior from another component:
> 1. Add a comment: `# CONTRACT: assumes hook:X blocks Y`
> 2. Include in return output: `contracts: [{description, source, target}]`

**Orchestrator response:**

1. Add to `plugin-state.json` → `integration.contracts[]`
2. Create skeleton scenario in `integration-tests.md`
3. Flag component as "has untested contracts"

### State Schema (integration section)

```json
"integration": {
  "status": "pending",
  "contracts": [
    {
      "id": "skill-hook-block-etc",
      "description": "skill:path-validator assumes hook:block-etc blocks /etc writes",
      "source_component": "skill:path-validator",
      "target_component": "hook:block-etc",
      "test_scenario": "hook-blocks-etc-writes",
      "status": "untested"
    }
  ],
  "results": [
    {
      "scenario": "hook-blocks-etc-writes",
      "timestamp": "2026-01-05T15:00:00Z",
      "status": "passed",
      "checks": [
        {"name": "file-blocked", "passed": true},
        {"name": "logged", "passed": true}
      ],
      "output": "PASS:file-blocked\nPASS:logged"
    }
  ]
}
```

### Trigger Points

| Trigger | Condition | Behavior |
|---------|-----------|----------|
| **Auto (stage transition)** | All components reach "implemented" | Orchestrator prompts: "Ready to run integration tests?" |
| **Manual** | User requests "run integration tests" | Execute all scenarios |
| **Pre-deployment gate** | Before optimization or deployment stage | Required pass for Standard/Full paths |

### Execution Flow

```
Orchestrator sets environment (CLAUDE_HOOK_AUDIT_ENABLED=1)
        │
        ▼
For each scenario:
   ├─ Run Setup bash commands
   ├─ Run Action bash commands
   ├─ Run Verify bash commands
   ├─ Parse PASS/FAIL from output
   └─ Record to plugin-state.json
        │
        ▼
Report summary to user
   ├─ All pass → proceed to next stage
   └─ Any fail → show failures, offer retry/skip/fix
```

### Path Behavior

| Path | Integration Testing |
|------|---------------------|
| Quick | Skipped (typically single component, no contracts) |
| Standard | Required before "done" |
| Full | Required before optimization |

---

## Deferred Topics

The following topics will be addressed in a future session:

### Subagent Design

- Full agent definitions for pipeline-designer, pipeline-implementer, pipeline-optimizer
- System prompts
- Output format contracts
- Context handoff mechanisms

---

## Open Questions

1. **State file location:** `docs/plans/plugin-state.json` vs root-level `plugin-state.json`?
2. **Learnings export:** Should learnings auto-export to README at publish time?
3. **Parallel component work:** Can multiple components be designed/implemented in parallel?
4. **Validation enforcement:** Should stage transitions be gated by validation, or advisory?

---

## Appendix: Three-Lens Audit Summary

This design was informed by a three-lens audit (`--claude-code` preset) of ADR-001.

### Convergent Findings Addressed

| Finding | How Addressed |
|---------|---------------|
| No session resume | State file with explicit tracking + session management |
| Validation advisory | Checkpoint system + failure classification enables gating |
| Pipeline overhead for simple cases | Quick path with minimal stages |
| Iron Law enforcement | Deterministic failures require user decision; no silent skips |
| Multi-component integration | Integration testing phase with contract surfacing and hook testability |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-05 | Initial design draft |
| 2026-01-05 | Added error handling & recovery section (checkpoint system, failure classification, state reconciliation, session management) |
| 2026-01-05 | Added integration testing section (scope, scenario format, hook testability, contract surfacing, execution flow) |
