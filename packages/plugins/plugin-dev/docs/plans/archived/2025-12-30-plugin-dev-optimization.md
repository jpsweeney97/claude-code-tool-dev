# Plugin Optimization: plugin-dev

> **⚠️ PARTIALLY SUPERSEDED (2025-12-31):** This optimization report references `skillcreator` which has been renamed to `skillforge` following an upstream repository rename. The plugin is now at v1.4.0.
>
> - Migration documentation: [`docs/migrations/skillcreator-to-skillforge.md`](../migrations/skillcreator-to-skillforge.md)
>
> *The optimization recommendations remain valid; substitute `skillforge` for `skillcreator`.*

---

Generated: 2025-12-30

## Summary

plugin-dev is a comprehensive, well-architected toolkit at v1.3.0 containing 12 skills, 3 agents, 6 commands, and extensive reference materials (~34,000 words total). The quality level is high — skills follow progressive disclosure, have working utility scripts, and demonstrate consistent patterns. Structural consistency is excellent (every skill follows the same pattern). The primary optimization opportunities are in **trigger fidelity** (descriptions could be more discoverable with third-person format and clearer cross-references) and **plugin coherence** (naming relationships between commands, skills, and directories need clarification).

---

## Quick Wins

Low effort, do first.

### [QW-1] Convert Skill Descriptions to Third-Person Format

**Lens:** Trigger Fidelity
**Files:** 8+ skill SKILL.md files
**Effort:** ~20 min | **Impact:** Medium

**Issue:** Most skill descriptions use "Use when..." (imperative) instead of "This skill..." (declarative).

**Change Pattern:**
```yaml
# Before
description: Use when "auditing a plugin", "validating plugin structure"...

# After
description: This skill validates Claude Code plugins with 50+ rules. Use when "auditing a plugin", "validating plugin structure"...
```

**Files to update:**
- `skills/plugin-audit/SKILL.md`
- `skills/hook-development/SKILL.md`
- `skills/skill-development/SKILL.md`
- `skills/mcp-integration/SKILL.md`
- `skills/plugin-settings/SKILL.md`
- `skills/command-development/SKILL.md`
- `skills/agent-development/SKILL.md`
- `skills/writing-skills/SKILL.md`
- `skills/optimizing-plugins/SKILL.md`
- `skills/brainstorming-plugins/SKILL.md`

---

### [QW-2] Fix Quoted Triggers in skill-development

**Lens:** Trigger Fidelity
**File:** `skills/skill-development/SKILL.md`
**Effort:** ~5 min | **Impact:** Medium

**Before:**
```yaml
description: Use for "skill file structure", "SKILL.md format", "progressive disclosure" patterns, or organizing skill directories.
```

**After:**
```yaml
description: This skill provides structural reference for building skills in Claude Code plugins. Use for "skill file structure", "SKILL.md format", "progressive disclosure patterns", "organizing skill directories", or "skill anatomy". For creation process and TDD testing, see writing-skills. For rigorous creation with analysis, see skillcreator.
```

---

### [QW-3] Improve optimizing-plugins Triggers

**Lens:** Trigger Fidelity
**File:** `skills/optimizing-plugins/SKILL.md`
**Effort:** ~5 min | **Impact:** Low

**Before:**
```yaml
description: Systematically improves Claude Code plugins through 6 analytical lenses. Use after audit confirms no broken issues, when asked to optimize, improve, or enhance a plugin, or when refining trigger phrases, token efficiency, or structural clarity.
```

**After:**
```yaml
description: "This skill guides systematic plugin improvement from 'good' to 'great' using 6 analytical lenses. Use after 'audit passes', when plugin 'works but feels rough', 'triggers aren't firing reliably', 'skills overlap confusingly', or when asked to 'optimize plugin', 'improve plugin quality', 'refine descriptions'. Distinct from audit (which fixes broken → working)."
```

---

### [QW-4] Add Fallback Instructions to plugin-audit

**Lens:** Degrees of Freedom
**File:** `skills/plugin-audit/SKILL.md`
**Effort:** ~5 min | **Impact:** Medium

**Add after Quick Start section:**
```markdown
**If scripts unavailable:** Perform manual checks — verify JSON syntax with `jq`, check required fields exist, scan for hardcoded paths using Grep.
```

---

### [QW-5] Fix Skill Name References in skill-reviewer Agent

**Lens:** Plugin Coherence
**File:** `agents/skill-reviewer.md`
**Effort:** ~10 min | **Impact:** Low

**Changes:**
- Line 44: Change "skill-creator best practices" → "`skillcreator` skill best practices"
- Line 217: Change "plugin-dev's own skills" → "plugin-dev's skills (see `skill-development`, `writing-skills`, `skillcreator`)"

Use backticks for skill directory names throughout.

---

### [QW-6] Convert README Skill List to Table

**Lens:** Plugin Coherence
**File:** `README.md`
**Effort:** ~5 min | **Impact:** Low

**Replace lines 7-20 with:**
```markdown
The plugin-dev toolkit provides **12 specialized skills** to help you build high-quality Claude Code plugins:

| # | Skill | Directory | Purpose |
|---|-------|-----------|---------|
| 1 | Hook Development | `hook-development` | Event-driven automation |
| 2 | MCP Integration | `mcp-integration` | Model Context Protocol servers |
| 3 | Plugin Structure | `plugin-structure` | Organization and manifest |
| 4 | Plugin Settings | `plugin-settings` | Configuration patterns |
| 5 | Command Development | `command-development` | Slash commands |
| 6 | Agent Development | `agent-development` | Autonomous agents |
| 7 | Skill Development | `skill-development` | Skill structure reference |
| 8 | Plugin Audit | `plugin-audit` | 50+ validation rules |
| 9 | Writing Skills | `writing-skills` | TDD methodology |
| 10 | Plugin Optimization | `optimizing-plugins` | Six-lens improvement |
| 11 | Plugin Brainstorming | `brainstorming-plugins` | Design before implementation |
| 12 | SkillCreator | `skillcreator` | Rigorous 4-phase creation |
```

---

### [QW-7] Add Command-Skill Relationship Table to README

**Lens:** Plugin Coherence
**File:** `README.md`
**Effort:** ~5 min | **Impact:** Medium

**Add after skill list:**
```markdown
**Command ↔ Skill Relationships:**

| Command | Invokes Skill | When to Use |
|---------|---------------|-------------|
| `/audit-plugin` | `plugin-audit` | On-demand structured audit |
| `/optimize-plugin` | `optimizing-plugins` | Guided improvement session |
| `/fix-plugin` | `plugin-audit` | Interactive repair |
| `/create-plugin` | Multiple skills | End-to-end creation |
| `/create-skill` | `skillcreator` | Rigorous skill creation |
| `/brainstorm` | `brainstorming-plugins` | Design exploration |
```

---

## High Value

Worth the investment.

### [HV-1] Clarify Skill Overlap: skillcreator vs skill-development vs writing-skills

**Lens:** Trigger Fidelity
**Files:** 3 skill SKILL.md files
**Effort:** ~15 min | **Impact:** High

**Issue:** All three skills address "creating skills" with unclear differentiation.

**skillcreator description:**
```yaml
description: "This skill creates production-grade skills using rigorous 4-phase methodology with 11 thinking lenses and multi-agent synthesis. Use when 'SkillCreator:', 'ultimate skill', 'best possible skill', 'rigorous skill creation', or when creating complex/critical skills. For simple skills, use skill-development (structure) + writing-skills (testing)."
```

**writing-skills description:**
```yaml
description: "This skill applies TDD methodology to skill development. Use when 'testing skills', 'skill TDD', 'pressure testing skills', or 'validating skill effectiveness'. For skill structure, see skill-development. For full creation methodology, see skillcreator."
```

**skill-development description:**
```yaml
description: "This skill provides structural reference for building skills. Use for 'skill file structure', 'SKILL.md format', 'progressive disclosure patterns', 'skill directory layout'. This is the WHERE and WHAT of skills. For HOW to test, see writing-skills. For rigorous creation, see skillcreator."
```

---

### [HV-2] Add Error Handling to Hook Example Scripts

**Lens:** Resilience
**Files:** `examples/validate-write.sh`, `validate-bash.sh`, `load-context.sh`
**Effort:** ~15 min | **Impact:** Medium

**Add to each script after `input=$(cat)`:**
```bash
# Validate JSON input
if ! echo "$input" | jq empty 2>/dev/null; then
  echo '{"continue": true, "systemMessage": "Hook received malformed JSON input, skipping validation"}' >&2
  exit 0  # Don't block on parse errors
fi
```

**Update jq calls with error handling:**
```bash
# Before
file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty')

# After
file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty' 2>/dev/null || echo "")
```

---

### [HV-3] Add Partial Failure Handling to plugin-validator Agent

**Lens:** Resilience
**File:** `agents/plugin-validator.md`
**Effort:** ~10 min | **Impact:** Medium

**Add after Comprehensive Mode section:**
```markdown
**Handling Partial Failures:**
- If validation scripts fail to run: Fall back to manual checks using Read/Grep. Note in report: "Script validation unavailable — manual checks performed."
- If a category can't be assessed: Mark as "⚠️ Skipped" with reason, don't silently omit.
- If findings are incomplete: Explicitly state what was NOT checked and why.
- Never report "all clear" unless all categories were actually validated.
```

**Add to Output Format section:**
```markdown
### For Incomplete Checks
## Plugin Audit Summary (Partial)

**Note:** Some checks could not be completed:
- [Category]: [Reason]

| Category | Status |
|----------|--------|
| Structure | ✅ |
| Skills | ⚠️ Skipped |

**Recommendation:** Resolve blockers and re-run.
```

---

### [HV-4] Update Command Descriptions with Skill References

**Lens:** Plugin Coherence
**File:** `commands/audit-plugin.md`
**Effort:** ~5 min | **Impact:** Medium

**Before:**
```yaml
description: Run comprehensive plugin audit with detailed report, severity ratings, and fix suggestions
```

**After:**
```yaml
description: Run comprehensive plugin audit. Invokes the `plugin-audit` skill with structured output, severity ratings, and fix suggestions. Use this command for on-demand audits; the skill loads automatically when discussing audit topics.
```

Apply similar pattern to `optimize-plugin.md`, `fix-plugin.md`.

---

## Consider

May not justify the cost.

### [C-1] Clarify Creative vs Rigid Sections in agent-creator

**Lens:** Degrees of Freedom
**File:** `agents/agent-creator.md`
**Effort:** ~10 min | **Impact:** Low

**Issue:** Steps 1-2 (Extract Intent, Design Persona) are creative; Steps 3-5 are rigid. All presented identically.

**Optional fix:** Add brief annotations like "(use judgment)" vs "(follow exactly)" to distinguish section types.

**Recommendation:** Skip unless agent produces inconsistent results.

---

## Cross-Cutting Notes

### Consolidated Changes

1. **Skill Description Pass** — Update all 10 skill descriptions in single session. Apply: third-person format, quoted triggers, cross-references.

2. **README Enhancement** — Both table changes (skill list + command relationships) in same edit.

3. **Hook Examples** — Same error handling pattern to all 3 scripts.

### Implementation Order

```
1. Skill descriptions (QW-1, QW-2, QW-3, HV-1) — no dependencies
2. README tables (QW-6, QW-7) — references skill directories
3. Hook examples (HV-2) — independent
4. Agent updates (QW-5, HV-3) — independent
5. Command descriptions (HV-4) — references skills
6. plugin-audit fallback (QW-4) — independent
```

### Files Changed

| File | Suggestions |
|------|-------------|
| `README.md` | QW-6, QW-7 |
| `skills/plugin-audit/SKILL.md` | QW-1, QW-4 |
| `skills/skill-development/SKILL.md` | QW-1, QW-2, HV-1 |
| `skills/writing-skills/SKILL.md` | QW-1, HV-1 |
| `skills/skillcreator/SKILL.md` | HV-1 |
| `skills/optimizing-plugins/SKILL.md` | QW-1, QW-3 |
| `skills/hook-development/SKILL.md` | QW-1 |
| `skills/mcp-integration/SKILL.md` | QW-1 |
| `skills/plugin-settings/SKILL.md` | QW-1 |
| `skills/command-development/SKILL.md` | QW-1 |
| `skills/agent-development/SKILL.md` | QW-1 |
| `skills/brainstorming-plugins/SKILL.md` | QW-1 |
| `agents/skill-reviewer.md` | QW-5 |
| `agents/plugin-validator.md` | HV-3 |
| `commands/audit-plugin.md` | HV-4 |
| `examples/validate-write.sh` | HV-2 |
| `examples/validate-bash.sh` | HV-2 |
| `examples/load-context.sh` | HV-2 |

---

## Metrics

| Metric | Value |
|--------|-------|
| Total suggestions | 12 |
| Quick Wins | 7 |
| High Value | 4 |
| Consider | 1 |
| Files affected | 18 |
| Estimated effort | ~90 min |
