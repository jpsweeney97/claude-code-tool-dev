---
paths:
  - ".claude/skills/**"
  - "~/.claude/skills/**"
  - "**/SKILL.MD"
---

# Skill Development

## Storage Locations & Priority

| Location | Path | Scope |
|----------|------|-------|
| Enterprise | Managed settings | Organization-wide |
| Personal | `~/.claude/skills/<skill-name>/SKILL.md` | All user's projects |
| Project | `.claude/skills/<skill-name>/SKILL.md` | Project only |
| Plugin | `<plugin>/skills/<skill-name>/SKILL.md` | Where plugin enabled |

**Priority:** enterprise > personal > project

**Nested discovery:** Claude Code automatically discovers skills from nested `.claude/skills/` directories (e.g., `packages/frontend/.claude/skills/`) for monorepo support.

**Plugin namespacing:** Plugin skills use `plugin-name:skill-name` to avoid conflicts.

## Backward Compatibility

Custom slash commands have been merged into skills:
- `.claude/commands/review.md` and `.claude/skills/review/SKILL.md` both create `/review`
- When skill and command share the same name, **skill takes precedence**
- Commands support same frontmatter but lack supporting file features
- Existing `.claude/commands/` files continue working

## Structure

Skills are directories containing `SKILL.md`:

```
.claude/skills/<name>/
├── SKILL.md          # Main skill file (required)
├── references/       # Deep documentation (optional)
├── scripts/          # Automation - stdlib only (optional)
├── templates/        # Output templates (optional)
└── assets/           # Images, prompts (optional)
```

## Progressive Disclosure

Skills share Claude's context window with conversation history, other skills, and your request. Keep skills focused:

- **Keep SKILL.md under 500 lines** — larger skills degrade performance
- **Keep references one level deep** — link from SKILL.md to reference files, not reference → reference (deeply nested files may be partially read)
- **Use scripts for zero-context execution** — scripts run without loading contents into context; only output consumes tokens

### When to Split

| Signal                    | Action                                                     |
| ------------------------- | ---------------------------------------------------------- |
| SKILL.md > 500 lines      | Move detailed reference to `references/` directory         |
| Repeated validation logic | Extract to `scripts/` and tell Claude to run (not read) it |
| Large examples/templates  | Move to `templates/` directory                             |

In SKILL.md, point to supporting files:

```markdown
For detailed API reference, see [REFERENCE.md](REFERENCE.md).
Run the validation script: `python scripts/validate.py input.pdf`
```

## Hot-Reload

Skills auto-reload when modified. Changes to files in `~/.claude/skills/` or `.claude/skills/` are immediately available without restarting the session.

## Skill Lifecycle

When you send a request, Claude follows these steps:

1. **Discovery**: At startup, loads only name + description of each skill (keeps startup fast)
2. **Activation**: When request matches a skill's description, Claude asks to use it. Full SKILL.md loads after user confirms.
3. **Execution**: Claude follows the skill's instructions, loading referenced files or running bundled scripts as needed.

## SKILL.md Format

### Frontmatter

```yaml
---
name: skill-name # Required: kebab-case, gerund form (verb-ing), max 64 chars
description: Trigger conditions only # Required: max 1024 chars, never summarize workflow
argument-hint: "<query>" # Optional: hint shown during autocomplete (e.g., "[pr-number]", "<filename>")
license: MIT # Optional: license type
metadata: # Optional: version and quality info
  version: '1.0.0'
  timelessness_score: 8
  model: claude-opus-4-5-20251101 # Recommended model (informational only)
allowed-tools: Tool1, Tool2 # Optional: comma or YAML list; patterns like Bash(python:*)
model: claude-sonnet-4-20250514 # Optional: specific model
context: fork # Optional: run in isolated subagent
agent: general-purpose # Optional: agent type when context: fork
hooks: # Optional: component-scoped hooks
  PreToolUse:
    - matcher: Bash
      hooks:
        - type: command
          command: ./validate.sh
          once: true # Optional: run only once per session
user-invocable: true # Optional: controls slash menu visibility
disable-model-invocation: false # Optional: blocks Skill tool invocation
---
```

### String Substitutions

Skills support dynamic value substitution in the body:

| Variable | Description |
|----------|-------------|
| `$ARGUMENTS` | All arguments passed when invoking the skill. If not present in body, appended as `ARGUMENTS: <value>` |
| `${CLAUDE_SESSION_ID}` | Current session ID for logging, session-specific files, or correlating output |

### Context Fork Behavior

When `context: fork` is set, the skill runs in a separate subagent. However:

- **Built-in agents** (Explore, Plan, general-purpose) cannot access your skills
- **Custom subagents** need an explicit `skills` field to load skills

To give a custom subagent access to skills, define it in `.claude/agents/`:

```yaml
# .claude/agents/code-reviewer.md
---
name: code-reviewer
description: Review code for quality and best practices
skills: pr-review, security-check
---
```

If `skills` is omitted, no skills are preloaded into the subagent context.

#### Skills vs Subagents Integration

| Approach | System prompt | Task | Also loads |
|----------|--------------|------|-----------|
| Skill with `context: fork` | From agent type (Explore, Plan, etc.) | SKILL.md content | CLAUDE.md |
| Subagent with `skills` field | Subagent's markdown body | Claude's delegation message | Preloaded skills + CLAUDE.md |

### Dynamic Context Injection

The `` !`command` `` syntax runs shell commands as **preprocessing** — before skill content is sent to Claude. Output replaces the placeholder, so Claude receives actual data, not commands.

```markdown
---
name: pr-summary
description: Summarize changes in a pull request
context: fork
agent: Explore
---

## Pull request context
- PR diff: !`gh pr diff`
- PR comments: !`gh pr view --comments`
```

This is preprocessing, not Claude execution — the commands run when the skill loads.

### Extended Thinking

To enable extended thinking in a skill, include the word **"ultrathink"** anywhere in your skill content.

### Context Budget

- **Default limit:** 15,000 characters for skill descriptions
- If exceeded, some skills may be excluded from context
- Check current usage with `/context` command
- Increase limit via `SLASH_COMMAND_TOOL_CHAR_BUDGET` environment variable

### Agent Types

| Agent             | Model  | Best For                       |
| ----------------- | ------ | ------------------------------ |
| `Explore`         | haiku  | Read-only codebase exploration |
| `Plan`            | sonnet | Architecture and planning      |
| `general-purpose` | sonnet | Multi-step modifications        |

## Permission Control

Three ways to restrict Claude's skill access:

1. **Disable all skills:** Deny the Skill tool in `/permissions`
2. **Allow/deny specific skills:** Use permission rules with patterns:
   - **Exact match:** `Skill(commit)`
   - **Prefix match:** `Skill(deploy:*)`
3. **Hide individual skills:** Add `disable-model-invocation: true` to frontmatter

**Note:** The `user-invocable` field only controls menu visibility, not Skill tool access. Use `disable-model-invocation: true` to block programmatic invocation.

Built-in commands like `/compact` and `/init` are not available through the Skill tool.

## Persuasion Principles

Use deliberately for discipline-enforcing skills. See [skill-writing-guide.md](skills/brainstorming-skills/references/skill-writing-guide.md) for full details.

| Technique | Use | Example |
|-----------|-----|---------|
| **Authority** | Critical requirements | "YOU MUST", "Never", "No exceptions" |
| **Commitment** | Tracking compliance | "Announce skill usage", TodoWrite checklists |
| **Scarcity** | Preventing procrastination | "Before proceeding", "Immediately after X" |
| **Social Proof** | Establishing norms | "Every time", "X without Y = failure" |
| **Unity** | Collaborative skills | "our codebase", "we both want quality" |

**By skill type:**

| Type | Use | Avoid |
|------|-----|-------|
| Discipline-enforcing | Authority + Commitment + Social Proof | Liking |
| Guidance/technique | Moderate Authority + Unity | Heavy authority |
| Collaborative | Unity + Commitment | Authority |

**Key insight:** Bright-line rules reduce rationalization. "When X, do Y" beats "generally do Y."

## Quality Dimensions

Quick reference for skill review. See [skill-writing-guide.md](skills/brainstorming-skills/references/skill-writing-guide.md) for full details.

| Dimension | Check |
|-----------|-------|
| **Intent fidelity** | Primary goal explicit; non-goals listed |
| **Constraint completeness** | Allowed vs forbidden explicit; conflicts trigger STOP |
| **Terminology clarity** | Terms defined once, reused consistently |
| **Evidence anchoring** | "Confirm X exists before acting" |
| **Decision sufficiency** | Every decision: condition → action → alternative |
| **Verification validity** | Quick check measures actual success property |
| **Artifact usefulness** | Output format, required fields, tailored to consumer |
| **Minimality** | "Prefer smallest correct change" |
| **Calibration** | Claims labeled: Verified / Inferred / Assumed |

## Output Conventions

Skills that produce files (reports, decision records, exploration findings, etc.) must separate **artifact output** from **chat output**.

### The Principle

**Artifact is the work product. Chat is the summary.**

Without explicit separation, Claude defaults to showing its full work in chat — iteration logs, scoring tables, complete findings — overwhelming users who want actionable next steps.

### When This Applies

| Skill Type | Applies? | Example |
|------------|----------|---------|
| Produces files (reports, records, documents) | **Yes** | Exploration, evaluation, handoffs |
| Modifies existing code | No | Refactoring, bug fixes |
| Pure conversation (Q&A, explanation) | No | Clarification, guidance |

### Required in SKILL.md

For skills that produce files, the **Outputs** section must explicitly specify:

**1. What goes in the artifact:**
```markdown
**Artifact:** Report at `docs/reports/YYYY-MM-DD-<name>.md`

Includes: [full list of sections — iteration logs, scoring tables,
complete findings, evidence, etc.]
```

**2. What goes in chat:**
```markdown
**Chat summary (brief — not the full report):**

[Template showing the exact format — typically 5-8 lines max]
```

**3. What NOT to show in chat:**
```markdown
Do NOT include in chat: [explicit list — scoring tables, iteration logs,
full findings, pressure-testing Q&A, etc.]
```

### Example Pattern

```markdown
## Outputs

**IMPORTANT:** Full report goes in artifact ONLY. Chat receives brief summary.

**Artifact:** `docs/decisions/YYYY-MM-DD-<name>.md`
- [Full list of sections]

**Chat summary:**
```
**Decision:** [outcome]
**Why:** [1-2 sentences]
**Trade-offs:** [brief]
**Full report:** `path/to/artifact.md`
```

Do NOT include in chat: scoring tables, iteration logs, full analysis.
```

### Verification

Skills producing files should include in their verification checklist:

```markdown
Output:
- [ ] Full report written to artifact location
- [ ] Chat contains brief summary only
- [ ] Chat does NOT contain: [skill-specific list]
```

## Framework for Thoroughness

Some skills need rigor — iterative analysis, evidence tracking, principled stopping criteria. The [Framework for Thoroughness](../../references/framework-for-thoroughness_v1.0.0.md) provides reusable patterns.

### When to Use the Framework

| Situation | Integration Level |
|-----------|-------------------|
| Open-ended analysis (unknown iteration count) | **Full protocol** — adopt Entry Gate, loop, Yield%, Exit Gate |
| Structured workflow that needs rigor vocabulary | **Vocabulary only** — use Evidence/Confidence levels, Stakes calibration |
| Linear workflow with fixed steps | **Don't use** — framework adds overhead without benefit |

**Use full protocol when:**
- You don't know upfront how many passes are needed
- Findings in one pass may invalidate earlier findings
- "Done" is defined by convergence, not checklist completion
- Examples: codebase exploration, security audits, research synthesis

**Use vocabulary only when:**
- Workflow has defined phases/passes (not iterative until convergence)
- Want consistent rigor language without restructuring the skill
- Examples: design validation (11 dimensions), gap analysis (7 passes)

### Canonical Vocabulary

When skills need rigor concepts, use these definitions for consistency across the ecosystem.

#### Evidence Levels

| Level | Meaning | Example |
|-------|---------|---------|
| **E0** | Assertion only | "I believe X" |
| **E1** | Single source / single method | Read file, saw X |
| **E2** | Two independent methods | Read + grep confirmed; inspect + run |
| **E3** | Triangulated + disconfirmation | Multiple sources + actively tried to disprove |

#### Confidence Levels

| Level | Meaning |
|-------|---------|
| **High** | Replicated / strongly supported; disconfirmation attempts failed |
| **Medium** | Supported but incomplete; some assumptions untested |
| **Low** | Plausible hypothesis; major gaps or contradictory signals |

**Rule:** Confidence cannot exceed evidence. E0/E1 evidence caps confidence at Medium.

#### Stakes Calibration

| Level | When to Use | Yield Threshold | Evidence Required |
|-------|-------------|-----------------|-------------------|
| **Adequate** | Low stakes, reversible | <20% | E1 for P0 |
| **Rigorous** | Medium stakes, moderate cost of error | <10% | E2 for P0, E1 for P1 |
| **Exhaustive** | High stakes, costly/irreversible | <5% | E2 all, E3 for P0 |

### Declaring Framework Use

If a skill adopts the full framework, declare it in the skill header:

```markdown
# My Analysis Skill

Systematic analysis using the Framework for Thoroughness.

**Protocol:** [thoroughness.framework@1.0.0](references/framework-for-thoroughness.md)
**Default thoroughness:** Rigorous
```

If adopting vocabulary only, no declaration needed — just use the canonical terms consistently.

