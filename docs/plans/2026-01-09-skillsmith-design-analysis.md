# Rigorous Analysis: skillsmith Design Document

> Analysis of `/docs/plans/2026-01-09-skillsmith-design.md` against authoritative extension specifications.

**Date:** 2026-01-11
**Status:** Complete
**Analyzed Against:**
- `.claude/rules/skills.md`
- `docs/extension-reference/skills/*.md`
- `docs/extension-reference/plugins/*.md`
- `docs/extension-reference/commands/*.md`
- `docs/extension-reference/hooks/*.md`
- `docs/extension-reference/agents/*.md`

---

## Executive Assessment

The skillsmith design is ambitious and well-structured, merging two existing projects into a unified plugin. However, this analysis identifies **4 critical issues**, **19 important issues**, and **11 minor issues** that need resolution before implementation.

---

## Issue Summary by Severity

| Category | Critical | Important | Minor |
|----------|----------|-----------|-------|
| Skill spec alignment | 2 | 2 | 1 |
| Plugin spec alignment | 0 | 4 | 2 |
| Command spec alignment | 0 | 3 | 2 |
| Hook spec alignment | 0 | 4 | 4 |
| Agent spec alignment | 1 | 4 | 2 |
| Design clarity | 1 | 2 | 0 |
| **Totals** | **4** | **19** | **11** |

---

## Part 1: Skill Specification Analysis

### Issue 1: Section Count Mismatch (Critical)

**Design document claims:** 11-section hybrid structure (Section 3)

**Authoritative specification (`skills.md`):** 8 required content areas

| Design Doc (11 sections) | Official Spec (8 sections) |
|--------------------------|----------------------------|
| 1. Triggers | — (Not in spec) |
| 2. When to use | 1. When to use |
| 3. When NOT to use | 2. When NOT to use |
| 4. Inputs | 3. Inputs |
| 5. Outputs | 4. Outputs |
| 6. Procedure | 5. Procedure |
| 7. Verification | 6. Verification (maps to "Quick check") |
| 8. Troubleshooting | 7. Troubleshooting |
| 9. Anti-Patterns | — (Not in spec) |
| 10. Extension Points | — (Not in spec) |
| 11. References | — (Optional, not required) |
| — | 8. Decision points (REQUIRED) |

**Problem:** The design document treats "Decision points" as embedded in Procedure (line 506), but the official spec treats it as a **distinct required section**. The validator check `FAIL.too-few-decision-points` (line 833) enforces this.

**Resolution:** Either:
- Update the spec to require 11 sections
- OR make Triggers/Anti-Patterns/Extension Points optional (warning, not FAIL)

---

### Issue 2: FAIL Code Extension Not Acknowledged (Important)

**Design claims (Section 10):** 11 FAIL codes total (8 structural + 3 hybrid)

**Problem:** The official spec has 8 FAIL codes. The design proposes *changing* the FAIL code set without explicitly stating this is a **spec extension**.

**Resolution:** Explicitly state this is a spec extension, not alignment with existing spec.

---

### Issue 3: Timelessness as New Requirement (Critical)

**Design document (Section 11b):** Requires `timelessness_score ≥7` for all skills

**Official spec:** No mention of `timelessness_score` as a requirement.

**Resolution:** Acknowledge timelessness scoring as an **innovation** introduced by skillsmith, not claim alignment with existing spec.

---

### Issue 4: Risk Tier Default Gap (Minor)

**Design document (line 404-405):** "Default to higher tier when uncertain"

**Official spec (`skills.md:316-323`):** "If skill has any mutating step, treat as High until procedure explicitly gates those steps."

**Resolution:** Explicitly incorporate the mutation → High default from the spec.

---

### Issue 5: Semantic Quality Dimensions (Verified OK)

**Design document:** Lists 9 semantic quality dimensions
**Official reference:** Also lists 9 dimensions (A through I)

All 9 dimensions align correctly.

---

## Part 2: Plugin Specification Analysis

### Issue 14: Plugin Compliance Checklist Gaps (Important)

**Plugin specification requirements (`plugins-distribution.md:86-101`):**

| Requirement | Design Status |
|-------------|--------------|
| `name` in plugin.json | Implied (skillsmith) |
| `version` in plugin.json | Implied |
| README.md | Listed (line 165) |
| CHANGELOG.md | Listed (line 167) |
| LICENSE | Listed (line 166) |
| Scripts executable | Not specified |
| `${CLAUDE_PLUGIN_ROOT}` usage | Not addressed |

**Resolution:** Specify how scripts will use `${CLAUDE_PLUGIN_ROOT}` for runtime path resolution.

---

### Issue 15: Missing plugin.json Definition (Important)

**Design document:** Shows directory but doesn't define `plugin.json` contents.

**Resolution:** Include a concrete `plugin.json` specification:

```json
{
  "name": "skillsmith",
  "version": "1.0.0",
  "description": "Unified plugin for creating, validating, and reviewing skills",
  "author": {
    "name": "Human + Claude"
  },
  "license": "MIT",
  "keywords": ["skill", "creation", "validation", "review"],

  "skills": "./skills/",
  "commands": "./commands/",
  "agents": [
    "./agents/design-agent.md",
    "./agents/audience-agent.md",
    "./agents/evolution-agent.md",
    "./agents/script-agent.md"
  ]
}
```

---

### Issue 16: Nested References Violate Progressive Disclosure (Important)

**Design proposes (lines 122-145):**
```
skills/skillsmith/
├── SKILL.md
└── references/
    ├── spec/                    ← Level 1
    │   ├── skills-as-prompts-strict-spec.md
    │   └── ...
    ├── workflow/                ← Level 1
    └── analysis/                ← Level 1
```

**Official skill guidelines (`skills.md:25-26`):**
> "Keep references one level deep — link from SKILL.md to reference files, not reference → reference (deeply nested files may be partially read)"

**Resolution:** Flatten to `references/*.md` instead of `references/*/`:

```
skills/skillsmith/
├── SKILL.md
├── references/
│   ├── strict-spec.md           ← Flattened
│   ├── categories-guide.md      ← Flattened
│   ├── semantic-quality.md      ← Flattened
│   └── INDEX.md                 ← Navigation file
└── templates/
```

---

### Issue 17: Agent-Type Hooks Not Documented (Important)

**Plugin components spec (`plugins-components.md:139-140`):**
> Hook types: `command`, `prompt`, `agent` (agent is plugin-only)

The design describes 4 panel agents but doesn't specify how they're invoked.

**Resolution:** Clarify agent invocation mechanism:
- Via Task tool with `subagent_type`?
- Via hook type `agent`?
- Inline in the skill procedure?

---

### Issue 18: Scripts Location Ambiguity (Minor)

**Design document shows two script locations:**
1. Plugin-level scripts (line 155-157)
2. Skill-level templates (line 150)

**Resolution:** Clarify script discoverability and registration.

---

### Issue 19: Command Naming Convention (Minor)

**Design commands:** `create-skill`, `review-skill`, `lint-skill`

These don't conflict with built-ins, but `/review-skill` is close to `/review` (built-in).

**Resolution:** Consider `/skillsmith:review` for clarity.

---

## Part 3: Command Specification Analysis

### Issue 20: Commands Contain Complex Workflow Logic (Important)

**Design document proposes:**
- `/create-skill` → Full 5-phase workflow
- `/review-skill` → Phase 3 + Phase 4

**Commands spec (`commands-overview.md:19`):** "No logic, just injection"

**Resolution:** Commands should be simple aliases that invoke the skill with arguments:

```markdown
# commands/create-skill.md
---
description: Create a new skill with full analysis and review
argument-hint: <what-the-skill-does>
disable-model-invocation: true
---

You are about to create a new skill using skillsmith.

**Goal:** $ARGUMENTS

**Next step:** Invoke the `skillsmith` skill to begin the 5-phase creation workflow.
```

---

### Issue 21: Missing Command Content Specification (Important)

**Design document:** Lists command files but provides no content specification.

**Resolution:** Include concrete command markdown content in the design.

---

### Issue 22: `/review-skill` Close to Built-in (Minor)

**Built-in command:** `/review`
**Proposed command:** `/review-skill`

**Resolution:** Consider namespacing: `/skillsmith:review`

---

### Issue 23: Model Invocation Behavior Undefined (Minor)

**Resolution:** Add `disable-model-invocation: true` to prevent accidental skill creation.

---

### Issue 24: Character Budget Consideration (Minor)

**Skill tool spec:** 15,000 character budget default.

**Resolution:** Note in design that verbose command descriptions consume context budget.

---

### Issue 25: Command → Skill Delegation Unclear (Important)

**Resolution:** Document the delegation pattern:
- Commands set context and mode
- Commands ask Claude to invoke skillsmith skill
- Skill does all workflow logic

---

## Part 4: Hook Specification Analysis

### Issue 26: Missing Hook Strategy (Important)

**Design document:** Does not specify any hooks for the skillsmith plugin.

**Resolution:** At minimum, document the decision (even if "no hooks needed"):

```json
{
  "description": "skillsmith validation and review hooks",
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/check-skill-write.sh",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

---

### Issue 27: Agent Hook Type Underutilized (Important)

**Hooks spec (`hooks-types.md:95-112`):** Agent hooks are plugin-only and provide full tool access.

**Resolution:** Clarify whether panel agents use hook type `agent` or Task tool invocation.

---

### Issue 28: Prompt Hooks Opportunity Unused (Minor)

**Resolution:** Consider `Stop` prompt hook for iteration cap enforcement.

---

### Issue 29: Component-Scoped Hooks Limitations (Minor)

**Hooks spec:** Skills can only define PreToolUse, PostToolUse, Stop hooks in frontmatter.

**Resolution:** If skillsmith needs SubagentStop hooks, define at plugin level.

---

### Issue 30: Exit Code Semantic Mismatch (Minor)

**Validator exit codes:**
- `0` — All checks pass
- `1` — Validation failed

**Hook exit codes:**
- `1` — Error but proceed (non-blocking)
- `2` — Block

**Resolution:** If validator is used as hook, use exit code 2 for failures.

---

### Issue 31: Script Path Resolution Incomplete (Important)

**Resolution:** All script invocations should use `${CLAUDE_PLUGIN_ROOT}`:

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/skill_lint.py" path/to/skill
```

---

### Issue 32: Hook Performance Not Addressed (Minor)

**Resolution:** Document that hooks should target <1s execution and use specific matchers.

---

## Part 5: Agent Specification Analysis

### Issue 33: Panel Agent Specification Missing (Important)

**Design document:** Lists 4 panel agents but provides no concrete definitions.

**Resolution:** Include complete agent markdown files (see recommendations below).

---

### Issue 34: Proposed Agent Definitions (Important)

**Resolution:** Add concrete definitions for all 4 agents:

**`agents/design-agent.md`:**
```yaml
---
name: design-agent
description: Reviews skills for structural correctness, pattern compliance, and logical consistency.
tools: Read, Glob, Grep
model: opus
permissionMode: plan
---

You are a skill design reviewer focused on structure and correctness.
[... full system prompt ...]
```

Similar definitions needed for `audience-agent`, `evolution-agent`, `script-agent`.

---

### Issue 35: Agents Cannot Spawn Other Agents (Critical)

**Agent spec (`agents-overview.md:61`):**
> "Cannot spawn other agents — use skills or chain from main conversation"

**Resolution:** Use parallel invocation from main skill:

```markdown
## Phase 4 Procedure

1. Launch review panel in parallel:
   - Task(subagent_type: "design-agent", prompt: "Review {skill-path}")
   - Task(subagent_type: "audience-agent", prompt: "Review {skill-path}")
   - Task(subagent_type: "evolution-agent", prompt: "Review {skill-path}")
   - If scripts exist: Task(subagent_type: "script-agent", prompt: "Review {skill-path}")

2. Await all agent completions

3. Synthesize results in main skill
```

---

### Issue 36: Permission Mode Selection (Verified OK)

**Resolution:** Use `permissionMode: plan` for all review agents (read-only access).

---

### Issue 37: Model Selection for Panel (Minor)

**Resolution:**
- Design, Audience, Evolution: Use `opus` (semantic review)
- Script Agent: Use `sonnet` (code review)

---

### Issue 38: Skills Injection vs Inheritance (Important)

**Agent spec:** Skills are injected, not inherited. Agents don't inherit parent skills.

**Resolution:** If panel agents need spec access, include explicit Read instructions:
```markdown
Before making risk tier decisions, read:
${CLAUDE_PLUGIN_ROOT}/skills/skillsmith/references/strict-spec.md
```

---

### Issue 39: Agent Hooks for Lifecycle Management (Minor)

**Resolution:** Consider SubagentStop hooks for logging panel results:

```json
{
  "hooks": {
    "SubagentStop": [{
      "matcher": "design-agent|audience-agent|evolution-agent|script-agent",
      "hooks": [{
        "type": "command",
        "command": "${CLAUDE_PLUGIN_ROOT}/scripts/record-review-result.sh"
      }]
    }]
  }
}
```

---

### Issue 40: Consensus Protocol Implementation (Important)

**Resolution:** Use parallel invocation with synthesis:
1. Invoke all agents in parallel
2. When all return, synthesize results
3. Determine consensus from combined output

---

### Issue 41: Agent Output Format Enforcement (Verified OK)

**Resolution:** Output format is specified but should be in actual agent definitions.

---

## Part 6: Design Clarity Issues

### Issue 6: Panel Composition Ambiguity (Critical)

**Design document:** Variously describes "3-4 agents" without clear rules.

**Resolution:** Define explicitly:
- 3 agents always (Design, Audience, Evolution)
- Script Agent joins only when skill has scripts
- Consensus rules for 3-agent vs 4-agent panels

---

### Issue 7: Circular Definition Risk (Important)

**Design document (line 1238):** "Should skillsmith create its own skills?"

**Resolution:** Initial skillsmith SKILL.md should be hand-authored and validated manually. Only after v1.0 stable should self-modification be allowed.

---

### Issue 8: Spec Consultation Model Fragility (Important)

**Design document (lines 687-697):** Agents consult spec documents via "explicit triggers"

**Resolution:** Create verified `spec-index.md` with exact anchor names and validation that anchors exist in target files.

---

## Recommendations

### Critical (Must Fix Before Implementation)

1. **Resolve 8 vs 11 section conflict.** Either update the official spec to require 11 sections, OR make Triggers/Anti-Patterns/Extension Points optional (warning, not FAIL).

2. **Clarify timelessness as a NEW requirement.** Explicitly state: "skillsmith introduces timelessness scoring as an additional quality gate beyond the current spec."

3. **Define panel composition rules.** State explicitly: "Panel is always 3 agents (Design, Audience, Evolution). Script Agent joins only when skill includes `scripts/` directory."

4. **Address agent spawning limitation.** Use parallel Task tool invocations from main skill, not agent-to-agent chaining.

### Important (Should Fix)

5. **Define concrete plugin.json.** Include full manifest schema.

6. **Flatten reference hierarchy.** Move from `references/spec/`, `references/workflow/` to flat `references/*.md`.

7. **Include complete agent definitions.** Provide full markdown files for all 4 panel agents.

8. **Specify command content.** Include actual markdown for all 3 commands.

9. **Document hook strategy.** Even if "no hooks needed," explain the decision.

10. **Use `${CLAUDE_PLUGIN_ROOT}` everywhere.** All script paths must use plugin root variable.

### Nice to Have

11. **Add bootstrap instructions.** Document that initial skillsmith is hand-authored.

12. **Consider skill size limits.** Define handling for skills >1000 lines.

13. **Align validator exit codes.** Use exit code 2 for failures if used as hook.

---

## Positive Aspects

### Unified Validator Approach
The decision to merge `skill_lint.py` and `validate-skill.py` into a single unified linter eliminates the conflict where "a skill passing `skill_lint.py` might fail `validate-skill.py`."

### Diff + Confirm Pattern
Phase 3's requirement for explicit user confirmation before any writes prevents surprise modifications.

### Human Escalation Fallback
The 5-iteration cap on panel disagreement with human escalation prevents infinite loops.

### Error Handling Documentation
Section 13's error handling summary is comprehensive and actionable.

### Semantic Quality Alignment
The 9 semantic quality dimensions align correctly with the official spec.

---

## Appendix A: Proposed plugin.json

```json
{
  "name": "skillsmith",
  "version": "1.0.0",
  "description": "Unified plugin for creating, validating, and reviewing skills",
  "author": {
    "name": "Human + Claude"
  },
  "license": "MIT",
  "keywords": ["skill", "creation", "validation", "review"],

  "skills": "./skills/",
  "commands": "./commands/",
  "agents": [
    "./agents/design-agent.md",
    "./agents/audience-agent.md",
    "./agents/evolution-agent.md",
    "./agents/script-agent.md"
  ]
}
```

---

## Appendix B: Proposed Flattened Reference Structure

```
skills/skillsmith/
├── SKILL.md
├── references/
│   ├── strict-spec.md
│   ├── categories-guide.md
│   ├── semantic-quality.md
│   ├── domain-annexes.md
│   ├── authoring-pipeline.md
│   ├── one-pager.md
│   ├── regression-questions.md
│   ├── multi-lens.md
│   ├── evolution-scoring.md
│   ├── synthesis-protocol.md
│   ├── script-framework.md
│   ├── script-patterns.md
│   └── INDEX.md
└── templates/
    ├── skill-template.md
    ├── analysis-notes.md
    └── script-template.py
```

---

## Appendix C: Proposed Agent Definition (design-agent.md)

```yaml
---
name: design-agent
description: Reviews skills for structural correctness, pattern compliance, and logical consistency. Use as part of skillsmith review panel.
tools: Read, Glob, Grep
model: opus
permissionMode: plan
---

You are a skill design reviewer focused on structure and correctness.

## Review Criteria

1. **Structural compliance**: All 11 sections present per hybrid spec
2. **Pattern appropriateness**: Risk tier, category, verification mode
3. **Logical consistency**: No contradictions between sections
4. **Decision coverage**: ≥2 decision points with observable triggers
5. **STOP gate placement**: At least 1 STOP gate at appropriate point

## Output Format

```markdown
## Design Agent Review

### Verdict: APPROVED / CHANGES_REQUIRED

### Scores
| Criterion | Score (1-10) | Notes |
|-----------|--------------|-------|

### Issues (if CHANGES_REQUIRED)
| Issue | Severity | Required Change |
|-------|----------|-----------------|

### Spec Citations
- [Decision]: [spec section referenced]
```

Report issues using semantic quality dimensions as vocabulary.
```

---

## Appendix D: Phase 4 Agent Invocation Pattern

```markdown
## Phase 4 Procedure

1. Launch review panel in parallel:
   - Task(subagent_type: "design-agent", prompt: "Review {skill-path}")
   - Task(subagent_type: "audience-agent", prompt: "Review {skill-path}")
   - Task(subagent_type: "evolution-agent", prompt: "Review {skill-path}")
   - If scripts exist: Task(subagent_type: "script-agent", prompt: "Review {skill-path}")

2. Await all agent completions

3. Synthesize results:
   - Count APPROVED vs CHANGES_REQUIRED verdicts
   - If all APPROVED: Extract timelessness score, proceed to finalization
   - If any CHANGES_REQUIRED: Collect issues, return to Phase 1

4. Track iteration count:
   - Iterations 1-4: Retry with feedback
   - Iteration 5: Escalate to human
```

---

*Analysis generated 2026-01-11*
