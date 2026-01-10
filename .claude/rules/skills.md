---
paths: .claude/skills/**
---

# Skill Development

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

## Hot-Reload

Skills auto-reload when modified. Changes to files in `~/.claude/skills/` or `.claude/skills/` are immediately available without restarting the session.

## SKILL.md Format

### Frontmatter

```yaml
---
name: skill-name                    # Required: lowercase, hyphens, max 64 chars
description: One-line description   # Required: max 1024 chars
allowed-tools: Tool1, Tool2         # Optional: comma or YAML list
model: claude-sonnet-4-20250514     # Optional: specific model
context: fork                       # Optional: run in isolated subagent
agent: general-purpose              # Optional: agent type when context: fork
hooks:                              # Optional: component-scoped hooks
  PreToolUse:
    - matcher: Bash
      hooks:
        - type: command
          command: ./validate.sh
user-invocable: true                # Optional: controls slash menu visibility
disable-model-invocation: false     # Optional: blocks Skill tool invocation
---
```

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

### Body (Required Content Areas)

The body MUST contain all 8 content areas. Equivalent headings are allowed, but the information MUST exist and be findable quickly:

| Section | Purpose | Required Content |
|---------|---------|------------------|
| **When to use** | Activation boundaries | Clear triggers for when this skill applies |
| **When NOT to use** | Anti-goals, STOP conditions | ≥3 explicit non-goals; boundaries that trigger STOP |
| **Inputs** | What's needed to start | Required inputs, optional inputs, constraints/assumptions |
| **Outputs** | What's produced | Artifacts + Definition of Done (objective checks) |
| **Procedure** | How to execute | Numbered steps; inspect→decide→act→verify order |
| **Decision points** | Branching logic | ≥2 explicit "If...then...otherwise" with observable triggers |
| **Verification** | How to confirm success | Quick check with expected result shape |
| **Troubleshooting** | Recovery paths | ≥1 failure mode with symptoms/causes/next steps |

### Complete Example

```markdown
---
name: code-reviewer
description: Reviews code for bugs, security issues, and style violations. Use when you need systematic code review with actionable findings.
allowed-tools: ["Read", "Grep", "Glob"]
---

# Code Reviewer

## When to Use

- User asks for code review or feedback on implementation
- Before merging a feature branch
- After significant refactoring

## When NOT to Use

- Simple typo fixes (overkill)
- Documentation-only changes (different skill)
- Performance optimization (use profiling skill instead)

## Inputs

**Required:**
- File path(s) or directory to review

**Optional:**
- Focus areas (security, performance, style)
- Severity threshold (report only high/medium issues)

**Constraints:**
- Assumes code is syntactically valid
- Does not execute code

## Outputs

**Artifacts:**
- Review report with issues categorized by severity

**Definition of Done:**
- [ ] All specified files have been read
- [ ] Report contains at least one of: issues found OR explicit "no issues" statement
- [ ] Each issue includes: location (file:line), description, suggested fix

## Procedure

1. Read the specified files using Read tool
2. For each file, analyze for:
   - Logic errors and bugs
   - Security vulnerabilities
   - Style violations
3. Categorize findings by severity (High/Medium/Low)
4. Generate report with actionable recommendations
5. Run verification check

## Decision Points

- If file doesn't exist, STOP and ask user to verify path
- If file is >1000 lines, ask user whether to review in sections or full file
- If security issue found, prioritize it regardless of other findings

## Verification

Quick check: Report contains "## Issues" or "## No Issues Found" heading.
If missing, regenerate report.

## Troubleshooting

**Symptom:** "File not found" error
**Cause:** Path is incorrect or file was moved
**Next steps:** Ask user to verify path; use Glob to search for similar filenames
```

## Output Contract

Outputs MUST distinguish:

- **Artifacts**: files, patches, reports, commands the agent produces
- **Definition of Done**: objective checks that verify success without reading the agent's mind

### What counts as objective DoD

- Artifact existence/shape (file exists, contains required keys)
- Deterministic query/invariant (grep finds/doesn't find X)
- Executable check with expected output (command exits 0, output contains pattern)
- Deterministic logical condition (all X remain unchanged except Y)

### What does NOT count

- "Verify it works"
- "Ensure quality"
- "Make sure tests pass" (without specifying which tests)
- "Check for errors" (without specifying where/how)

## STOP/Ask Behavior

Skills MUST include explicit STOP/ask steps:

**STOP (missing inputs/ambiguity)**:
```
STOP. Ask the user for: <missing required input>. Do not proceed until provided.
STOP. The request is ambiguous. Ask: <clarifying question>. Proceed only after user confirms.
```

**Ask-first (risky/breaking actions)**:
```
Ask first: This step may be breaking/destructive (<risk>). Do not do it without explicit user approval.
If the user does not explicitly approve <action>, skip it and provide a safe alternative.
```

## Decision Points

Skills MUST contain ≥2 explicit decision points (or justify why fewer apply):

```
If <observable signal> is present, then <action>. Otherwise, <alternative>.
If <constraint is violated>, then STOP and ask. Otherwise, continue.
```

**Observable signals** (not subjective judgment):
- File/path exists or doesn't
- Command output matches pattern
- Test passes/fails
- Grep finds/doesn't find pattern
- Config contains/missing key

## Verification Requirements

Skills MUST include verification that measures the primary success property:

```
Quick check: Run <command>. Expected: <exit code/output pattern>.
If the quick check fails, do not continue; go to Troubleshooting first.
```

**Command mention rule**: Any command in the skill MUST specify:
1. Expected result shape (exit code and/or output pattern)
2. Preconditions (tools, env vars, working directory, permissions)
3. Fallback when command cannot run (missing tool, no network, restricted permissions)

## Assumptions and Constraints

Skills MUST declare non-universal assumptions:

| Category | Examples |
|----------|----------|
| Tools | `pytest`, `ruff`, `node`, specific CLI versions |
| Network | API access, package downloads, external services |
| Permissions | File write, env vars, secrets access |
| Repo layout | Specific paths, config files, conventions |

When assumptions aren't met, provide:
- Offline/manual fallback, OR
- "Paste outputs" alternative, OR
- Explicit STOP with what's needed

## Risk Tiering

Risk determines minimum strictness:

| Tier | Characteristics | Minimum Requirements |
|------|-----------------|---------------------|
| **Low** | Info/docs; trivial/reversible changes | All 8 sections; 1 quick check; 1 troubleshooting entry; 1 STOP/ask for missing inputs |
| **Medium** | Code/config changes; bounded/reversible | Low + STOP/ask for ambiguity; explicit non-goals; SHOULD have 2nd verification mode |
| **High** | Security/ops/data/deps/public contracts; costly to reverse | Medium + ask-first gate; ≥2 STOP/ask gates; ≥2 verification modes; rollback/escape guidance |

**Default routing**: If skill has any mutating step (writes/deletes/deploys), treat as High until procedure explicitly gates those steps.

## Semantic Quality

Beyond structure, skills need semantic precision:

### Intent fidelity
- Primary goal in 1-2 sentences
- ≥3 non-goals (explicit out-of-scope items)
- No proxy goals ("improve quality") without measurable acceptance signal

### Constraint completeness
- Declare constraints likely to be guessed wrong (no new deps, no breaking changes, no secrets)
- If constraints are unknown, STOP to ask

### Calibration
- Label claims as: Verified (evidence) / Inferred (derived) / Assumed (not verified)
- Report skipped checks as: `Not run (reason): ... Run: <command> to verify`

## Compliance Checklist

Before promoting a skill, verify:

- [ ] All 8 required content areas exist and are findable quickly
- [ ] Outputs include artifacts + ≥1 objective DoD check
- [ ] Procedure is numbered and includes ≥1 STOP/ask step
- [ ] ≥2 explicit decision points with observable triggers (or justified exception)
- [ ] Verification includes concrete quick check with expected result
- [ ] Troubleshooting includes ≥1 failure mode (symptoms/causes/next steps)
- [ ] Assumptions declared (tools/network/permissions/repo) with fallback
- [ ] Default procedure is safe (ask-first for breaking/destructive actions)
- [ ] Primary goal stated; ≥3 non-goals listed
- [ ] Commands specify expected results and fallbacks

## Workflow

1. Create `.claude/skills/<name>/SKILL.md`
2. Test with `/<name>` in this project
3. Validate against compliance checklist
4. Promote: `uv run scripts/promote skill <name>`

## Precedence

Personal (`~/.claude/skills/`) overrides project (`.claude/skills/`).

To test changes to an existing skill:
1. Use a dev name: `.claude/skills/<name>-dev/`
2. Test with `/<name>-dev`
3. When ready, promote overwrites production

## See Also

- **commands.md** — Simple prompt templates (use when skill complexity isn't needed)
- **agents.md** — Autonomous subagents (use when multi-turn isolation is needed)
- **plugins.md** — Bundle skills for distribution via marketplaces
- **settings.md** — Configure permissions and hooks in settings.json

## References

Authoritative specifications (read when needed for detailed guidance):
- `skill-documentation/skills-as-prompts-strict-spec.md` — Normative structural requirements, reviewer checklist, fail codes
- `skill-documentation/skills-semantic-quality-addendum.md` — Semantic quality requirements, templates
- `skill-documentation/skills-categories-guide.md` — Category definitions, DoD patterns, decision point libraries
