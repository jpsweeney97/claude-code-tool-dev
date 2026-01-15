# Audit Response Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Simplify the pipeline orchestrator design document based on three-lens audit findings via 6 incremental commits.

**Architecture:** Documentation-only changes to `2026-01-05-pipeline-orchestrator-design.md` and `ADR-001-plugin-development-pipeline.md`. Each commit addresses one audit finding, allowing validation between changes.

**Tech Stack:** Markdown editing, git

---

## Task 1: Remove Checkpoint System

**Files:**
- Modify: `packages/plugins/plugin-dev/docs/plans/2026-01-05-pipeline-orchestrator-design.md`

**Step 1: Read the checkpoint-related sections**

Identify all checkpoint references:
- Lines 427-445: Error handling architecture (references Checkpoint System)
- Lines 448-466: Checkpoint System section
- Lines 552-557: Error Handling Files section (mentions `.checkpoint-*.jsonl`)

**Step 2: Remove Checkpoint System section**

Delete lines 448-466 (the entire "### Checkpoint System" section including table and bullet points).

**Step 3: Update Error Handling Architecture diagram**

Replace the architecture diagram (lines 423-444) with simplified version:

```
┌─────────────────────────────────────────────────────────────────┐
│                     ERROR HANDLING LAYERS                        │
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐                    │
│  │  Reconciliation  │  │    Session       │                    │
│  │     Engine       │  │    Manager       │                    │
│  │                  │  │                  │                    │
│  │  • State/artifact│  │  • Resume UX     │                    │
│  │    merge         │  │  • Context       │                    │
│  │  • Conflict      │  │    restore       │                    │
│  │    resolution    │  │  • Learning      │                    │
│  │  • Backup        │  │    capture       │                    │
│  └────────┬─────────┘  └────────┬─────────┘                    │
│           │                     │                               │
│           └──────────┬──────────┘                               │
│                      │                                          │
│                      ▼                                          │
│         ┌────────────────────────┐                              │
│         │    State File          │                              │
│         │  plugin-state.json     │                              │
│         └────────────────────────┘                              │
└─────────────────────────────────────────────────────────────────┘
```

**Step 4: Update Failure Classification table**

Remove checkpoint-related recovery actions. Change "Resume from checkpoint" option to "Resume from state file".

Current (lines 467-477):
```markdown
| Classification | Detection Signals | Recovery Action |
|----------------|-------------------|-----------------|
| **Transient** | Network timeout, MCP connection failed, rate limit | Auto-retry (max 2, backoff 5s/15s) |
| **Deterministic** | Context limit, permission error, validation failed | User prompt with options |
| **Ambiguous** | User abort, no checkpoint + failure | User prompt |
```

Replace with:
```markdown
| Classification | Detection Signals | Recovery Action |
|----------------|-------------------|-----------------|
| **Transient** | Network timeout, MCP connection failed, rate limit | Auto-retry (max 2, backoff 5s/15s) |
| **Deterministic** | Context limit, permission error, validation failed | User prompt with options |
| **Ambiguous** | User abort, state/artifact mismatch | User prompt |
```

**Step 5: Update User Prompt Options**

Current (lines 479-482):
```markdown
**User Prompt Options:**
- Retry stage (fresh start)
- Resume from checkpoint (skip completed work)
- Skip stage (mark as manual)
- Abort pipeline
```

Replace with:
```markdown
**User Prompt Options:**
- Retry stage (fresh start)
- Skip stage (mark as manual)
- Abort pipeline
```

**Step 6: Remove Resume Context section**

Delete lines 484-490 (Resume Context for Subagent) since checkpoint context no longer exists.

**Step 7: Update State Reconciliation triggers**

Current (lines 495-500):
```markdown
**Triggers:**
- Orchestrator entry (every invocation)
- Stage transition
- Resume from checkpoint
- User request
```

Replace with:
```markdown
**Triggers:**
- Orchestrator entry (every invocation)
- Stage transition
- User request
```

**Step 8: Update merge strategy table**

Current (lines 504-510):
```markdown
| Situation | Resolution |
|-----------|------------|
| Artifact exists + state agrees | ✓ Consistent |
| Artifact exists + state silent | Add as "discovered" |
| Artifact exists + state says "pending" | Update to "complete" |
| Artifact missing + state says exists | **Ask user** |
| Checkpoint exists + state not updated | Apply checkpoint |
```

Remove the last row about checkpoints.

**Step 9: Update Error Handling Files section**

Current (lines 549-557):
```markdown
### Error Handling Files

\`\`\`
docs/plans/
├── plugin-state.json        # Source of truth (decisions, learnings, progress)
├── plugin-state.json.bak    # Backup before conflict resolution
├── .checkpoint-design.jsonl # Active checkpoint (gitignored)
└── 2026-01-05-*-design.md   # Design documents
\`\`\`
```

Replace with:
```markdown
### Error Handling Files

\`\`\`
docs/plans/
├── plugin-state.json        # Source of truth (decisions, learnings, progress)
├── plugin-state.json.bak    # Backup before conflict resolution
└── 2026-01-05-*-design.md   # Design documents
\`\`\`
```

**Step 10: Add note about checkpoint deferral**

In the "Deferred Topics" section (line 747), add:

```markdown
### Checkpoint System

Checkpointing deferred to v2 — all three audit lenses questioned whether checkpoint complexity is warranted for workflows that typically complete in one session. Claude Code already provides `/save-handoff` for session continuity. Revisit if users report lost progress in multi-session workflows.
```

**Step 11: Commit**

```bash
git add packages/plugins/plugin-dev/docs/plans/2026-01-05-pipeline-orchestrator-design.md
git commit -m "$(cat <<'EOF'
refactor(plugin-dev): remove checkpoint system from orchestrator design

All three audit lenses questioned checkpoint complexity for 30-min
workflows. Claude Code provides /save-handoff for session continuity.
Deferred to v2 pending user feedback about lost progress.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Consolidate Paths to Minimal/Rigorous

**Files:**
- Modify: `packages/plugins/plugin-dev/docs/plans/2026-01-05-pipeline-orchestrator-design.md`

**Step 1: Update Paths section header**

Current section starts at line 127. Replace entire Paths section (lines 127-178) with:

```markdown
## Paths

### Minimal Path

**When:** Personal tool, quick iteration

```
Implement → Done
```

- No formal design document
- Implementing skill handles clarification inline
- No integration testing stage
- Exit: Working component for personal use

### Rigorous Path

**When:** Marketplace quality, shared use

```
Design (per component) → Implement (per component) → Integration Test → Done
```

- Design document per component
- Full TDD implementation
- Integration testing for cross-component contracts
- Exit: Done or continue to Optimization/Deployment on request

### Path Comparison

| Aspect | Minimal | Rigorous |
|--------|---------|----------|
| Design docs | No | Yes, per component |
| Integration test | No | Yes, required before "done" |
| Optimization | On request | On request |
| Deployment | On request | On request |
| Best for | Personal tools | Team plugins, marketplace |

### Path Selection

Single question to user: **"Is this plugin for personal use, or will others use it?"**

- Personal use → Minimal path
- Others will use it → Rigorous path
```

**Step 2: Update Complexity Analysis output example**

Find the analysis output example (around line 106-122) and replace with:

```markdown
### Analysis Output

The orchestrator presents analysis with evidence:

\`\`\`
## Complexity Analysis

**Component count:** 2 (skill + hook)
**Target audience:** Marketplace (others will use it)

**Recommendation:** Rigorous path
**Reasoning:** Marketplace target requires design docs and integration testing.

Paths available:
- Minimal: Implement directly (for personal use only)
- Rigorous: Design → Implement → Integration test (recommended for shared use)
\`\`\`

User chooses; orchestrator records choice in state.
```

**Step 3: Update Path Graduation section**

Find Path Graduation section (around line 182) and update graduation options to reference new path names:

```markdown
### Graduation Options

\`\`\`
Minimal path completed
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
│ A) Retrofit design doc (upgrade to    │
│    Rigorous path documentation)       │
│ B) Run optimization (6 lenses)        │
│ C) Prepare for marketplace            │
│ D) Add more components                │
└───────────────────────────────────────┘
\`\`\`
```

**Step 4: Update state schema path values**

In the state schema example (around line 243), change:
- `"chosen_path": "standard"` → `"chosen_path": "rigorous"`
- `"recommended_path": "standard"` → `"recommended_path": "rigorous"`

**Step 5: Update Path Behavior table in Integration Testing**

Find the table (around line 737) and replace:

```markdown
### Path Behavior

| Path | Integration Testing |
|------|---------------------|
| Minimal | Skipped (typically single component, no contracts) |
| Rigorous | Required before "done" |
```

**Step 6: Commit**

```bash
git add packages/plugins/plugin-dev/docs/plans/2026-01-05-pipeline-orchestrator-design.md
git commit -m "$(cat <<'EOF'
refactor(plugin-dev): consolidate paths to Minimal/Rigorous

Replace Quick/Standard/Full with two clear paths:
- Minimal: personal tools, no design docs
- Rigorous: shared use, full documentation

Path selection via single question: "Personal use or shared?"

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Define Subagent Output Contract Schema

**Files:**
- Modify: `packages/plugins/plugin-dev/docs/plans/2026-01-05-pipeline-orchestrator-design.md`

**Step 1: Add new section after Skill Invocation**

After the "### Invocation Pattern" section (around line 377), add a new section:

```markdown
### Subagent Output Contract

All custom subagents return structured YAML at the end of their response.

**Subagent instruction:**
> End your response with a fenced YAML block (using `---` delimiters) containing: artifacts, decisions, contracts, errors.

**Schema:**

\`\`\`yaml
---
artifacts:
  - path: skills/my-skill/SKILL.md
    type: skill          # skill | hook | agent | command
    action: created      # created | modified | deleted

decisions:
  - key: trigger_strategy
    value: explicit_command_only
    rationale: "Skill is complex; avoid accidental invocation"

contracts:  # Only for pipeline-implementer
  - description: "Assumes hook:block-etc blocks /etc writes"
    source: skill:path-validator
    target: hook:block-etc

errors:  # Empty array if none
  - stage: implementation
    message: "MCP server not responding"
    recoverable: true
---
\`\`\`

**Field definitions:**

| Field | Required | Description |
|-------|----------|-------------|
| `artifacts` | Yes | Files created/modified/deleted during execution |
| `decisions` | Yes | Key decisions made (for state tracking and resume) |
| `contracts` | pipeline-implementer only | Cross-component assumptions |
| `errors` | Yes | Errors encountered (empty array if none) |

**Orchestrator parsing:**

1. Extract YAML block from subagent response (regex: `---\n.*?\n---`)
2. Parse YAML
3. Update state file with artifacts, decisions, contracts
4. If errors non-empty and `recoverable: false`, trigger failure handling
```

**Step 2: Commit**

```bash
git add packages/plugins/plugin-dev/docs/plans/2026-01-05-pipeline-orchestrator-design.md
git commit -m "$(cat <<'EOF'
feat(plugin-dev): define subagent output contract schema

Subagents return structured YAML: artifacts, decisions, contracts, errors.
YAML format chosen for forgiving syntax and easy extraction.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: Simplify State Schema to 9 Fields

**Files:**
- Modify: `packages/plugins/plugin-dev/docs/plans/2026-01-05-pipeline-orchestrator-design.md`

**Step 1: Replace state schema**

Find the state schema section (around line 240-305). Replace the entire schema example with:

```markdown
### Schema

\`\`\`json
{
  "schema_version": "1.0",
  "plugin": "my-plugin",
  "created": "2026-01-05T12:00:00Z",
  "updated": "2026-01-05T14:30:00Z",
  "path": "rigorous",
  "stage": "implementing",
  "components": [
    {
      "type": "skill",
      "name": "my-skill",
      "status": "implemented",
      "design_doc": "docs/plans/2026-01-05-my-skill-design.md"
    }
  ],
  "contracts": [
    "skill:path-validator assumes hook:block-etc blocks /etc writes"
  ],
  "notes": "Exit code 2 shows stderr to Claude, not user."
}
\`\`\`

**Field definitions:**

| Field | Type | Description |
|-------|------|-------------|
| `schema_version` | string | Schema version for migrations |
| `plugin` | string | Plugin name |
| `created` | ISO 8601 | Creation timestamp |
| `updated` | ISO 8601 | Last modification timestamp |
| `path` | enum | `minimal` or `rigorous` |
| `stage` | enum | `designing`, `implementing`, `testing`, `done` |
| `components` | array | Component tracking (type, name, status, design_doc) |
| `contracts` | array | Cross-component assumptions as strings |
| `notes` | string | Free-form notes/learnings |
```

**Step 2: Remove Learning Types section**

Delete the "### Learning Types" section (around lines 307-315) since learnings are now captured in the simple `notes` field.

**Step 3: Update Integration Testing state schema**

Find the integration section schema example (around line 682) and replace with simplified version:

```markdown
### State Schema (integration section)

Integration status is tracked via component status and contracts array. No separate integration section needed — contracts are top-level in simplified schema.
```

**Step 4: Commit**

```bash
git add packages/plugins/plugin-dev/docs/plans/2026-01-05-pipeline-orchestrator-design.md
git commit -m "$(cat <<'EOF'
refactor(plugin-dev): simplify state schema to 9 fields

Replaces 83-line schema with 9 focused fields.
Removes: analysis block, per-component decisions, learnings taxonomy,
integration.results, escalation_triggers, blockers.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: Change Contract Surfacing to Post-hoc Grep

**Files:**
- Modify: `packages/plugins/plugin-dev/docs/plans/2026-01-05-pipeline-orchestrator-design.md`

**Step 1: Update Contract Surfacing section**

Find the "### Contract Surfacing" section (around line 664) and replace with:

```markdown
### Contract Surfacing

Contracts are surfaced via post-hoc grep, not subagent self-reporting.

**Comment convention:**

\`\`\`python
# CONTRACT: assumes hook:block-etc blocks /etc/* writes
\`\`\`

**Subagent instruction:**
> When your implementation assumes behavior from another component, add a comment: `# CONTRACT: assumes {component}:{name} {behavior}`. You do NOT need to report contracts in your YAML output.

**Extraction:**

\`\`\`bash
grep -rh "# CONTRACT:" skills/ hooks/ agents/ commands/ | \
  sed 's/.*# CONTRACT: //' | sort -u
\`\`\`

**Rationale:** Post-hoc grep is deterministic. Expecting Claude to self-report assumptions produces unreliable results — Claude doesn't notice assumptions it made implicitly.
```

**Step 2: Update subagent output contract**

In the subagent output contract section (added in Task 3), update the contracts field description:

Change:
```markdown
| `contracts` | pipeline-implementer only | Cross-component assumptions |
```

To:
```markdown
| `contracts` | No | Deprecated — use `# CONTRACT:` comments instead |
```

**Step 3: Commit**

```bash
git add packages/plugins/plugin-dev/docs/plans/2026-01-05-pipeline-orchestrator-design.md
git commit -m "$(cat <<'EOF'
refactor(plugin-dev): change contract surfacing to post-hoc grep

Replace self-reporting with deterministic extraction:
  grep -rh "# CONTRACT:" | sed | sort -u

Claude doesn't reliably notice implicit assumptions.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: Add Plugin.json Creation to Pipeline

**Files:**
- Modify: `packages/plugins/plugin-dev/docs/plans/2026-01-05-pipeline-orchestrator-design.md`

**Step 1: Add new section after Entry Points**

After the "### Relationship" section (around line 414), add:

```markdown
---

## Plugin Manifest Creation

The orchestrator creates `.claude-plugin/plugin.json` automatically.

### Trigger

After the first component reaches "implemented" status.

### Template

\`\`\`json
{
  "name": "my-plugin",
  "version": "0.1.0",
  "description": "Created by pipeline orchestrator",
  "author": {
    "name": "User"
  },
  "components": {
    "skills": "./skills/"
  }
}
\`\`\`

### User Prompt

After creating the manifest:

> Created `.claude-plugin/plugin.json`. Update `description` and `author.name` before publishing.

### Component Discovery

The orchestrator adds component directories as they're created:

| Component Type | Manifest Entry |
|----------------|----------------|
| Skill | `"skills": "./skills/"` |
| Hook | `"hooks": "./hooks/"` |
| Agent | `"agents": "./agents/"` |
| Command | `"commands": "./commands/"` |

**Example** (plugin with skill and hook):

\`\`\`json
{
  "name": "my-plugin",
  "version": "0.1.0",
  "description": "A plugin for X",
  "author": {
    "name": "Your Name"
  },
  "components": {
    "skills": "./skills/",
    "hooks": "./hooks/"
  }
}
\`\`\`
```

**Step 2: Update artifact inference table**

Find the artifact inference table (around line 319) and add plugin.json:

```markdown
### Artifact Inference (for re-entry)

When no state file exists but artifacts are present:

| Artifact Found | Inferred State |
|----------------|----------------|
| `.claude-plugin/plugin.json` | Plugin initialized |
| `skills/*/SKILL.md` | Skill implemented |
| `hooks/*.py` | Hook implemented |
| `docs/plans/*-design.md` | Design completed |
| Design doc but no implementation | Design stage complete, implementation pending |
```

**Step 3: Commit**

```bash
git add packages/plugins/plugin-dev/docs/plans/2026-01-05-pipeline-orchestrator-design.md
git commit -m "$(cat <<'EOF'
feat(plugin-dev): add plugin.json creation to pipeline

Orchestrator creates .claude-plugin/plugin.json after first component
is implemented. Two-lens audit finding: pipeline must produce
installable output.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 7: Update ADR-001

**Files:**
- Modify: `packages/plugins/plugin-dev/docs/ADR-001-plugin-development-pipeline.md`

**Step 1: Update Pipeline Stages diagram**

Find the pipeline diagram (around line 32-92) and add note about paths:

After the diagram, add:

```markdown
**Note:** The pipeline orchestrator offers two paths:
- **Minimal:** Implement → Done (personal use)
- **Rigorous:** Design → Implement → Test → Done (shared use)

Path selection via single question: "Is this plugin for personal use, or will others use it?"
```

**Step 2: Update Key Design Decisions table**

Find the table (around line 155) and add row:

```markdown
| Two paths (Minimal/Rigorous) | Clear intent: personal vs. shared use |
```

**Step 3: Add Updates entry**

Find the Updates section (around line 189) and add:

```markdown
- **2026-01-05**: Audit response applied — paths simplified to Minimal/Rigorous, checkpoint system deferred to v2, state schema reduced to 9 fields. See [Audit Response Strategy](plans/2026-01-05-audit-response-strategy.md).
```

**Step 4: Commit**

```bash
git add packages/plugins/plugin-dev/docs/ADR-001-plugin-development-pipeline.md
git commit -m "$(cat <<'EOF'
docs(plugin-dev): update ADR-001 for Minimal/Rigorous paths

Reflect audit response changes: two clear paths based on
personal vs. shared use intent.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Verification Checklist

After all commits:

- [ ] Design document internally consistent (no references to Quick/Standard/Full)
- [ ] State schema matches subagent output contract
- [ ] Paths map to available skills (implementing-X for Minimal, brainstorming-X + implementing-X for Rigorous)
- [ ] ADR updated to reflect changes
- [ ] All 7 commits applied
- [ ] Run `grep -r "Quick\|Standard\|Full" packages/plugins/plugin-dev/docs/` returns no path references
- [ ] Run `grep -r "checkpoint" packages/plugins/plugin-dev/docs/plans/2026-01-05-pipeline-orchestrator-design.md` returns only "Deferred" section
