# Plugin Optimization: plugin-dev

Generated: 2025-12-29

## Summary

The plugin-dev plugin is a mature, comprehensive toolkit with 10 skills, 4 commands, and 3 agents. Its strengths include progressive disclosure patterns, well-designed command workflows, and appropriate degrees of freedom for fragile operations. The main opportunities lie in skill descriptions (verbose preambles, missing trigger phrases), token efficiency (two skills exceed 3,000 words), and documentation completeness (README omits two skills).

**Key insight established:** SKILL.md must be complete and self-sufficient. References provide depth on elemental concepts—not essential workflow steps hidden away. This prevents the "fragmented skill" anti-pattern.

---

## Quick Wins

### 1. Fix Script References in `plugin-validator` Agent

**File:** `agents/plugin-validator.md`
**Effort:** ~10 min

The agent references four scripts that do not exist:
- `validate-json.sh` (missing)
- `validate-yaml-frontmatter.sh` (missing)
- `check-paths.sh` (missing)
- `check-file-references.sh` (missing)

Only `check-syntax.sh` and `check-structure.sh` exist.

**Fix:** Replace lines 129-134 with:

```markdown
## Using Validation Scripts

Run deterministic validation:
```bash
# Layer 1: Syntax validation (JSON/YAML)
bash ${CLAUDE_PLUGIN_ROOT}/skills/plugin-audit/scripts/check-syntax.sh <plugin-path>

# Layer 2: Structure validation (manifest, naming, required fields)
bash ${CLAUDE_PLUGIN_ROOT}/skills/plugin-audit/scripts/check-structure.sh <plugin-path>
```

For path and reference checks, analyze files directly using Read/Grep tools.
```

---

### 2. Rename `optimize` Command to `optimize-plugin`

**File:** `commands/optimize.md` → `commands/optimize-plugin.md`
**Effort:** ~5 min

Current commands follow the pattern `verb-plugin`: `audit-plugin`, `create-plugin`, `fix-plugin`. The `optimize` command breaks this pattern.

**Fix:** Rename file and update any references in README.

---

### 3. Update Skill Descriptions (8 skills)

**Files:** All skills except `writing-skills` and `optimizing-plugins`
**Effort:** ~5 min per skill

Apply two changes to each description:

1. **Implementation-intention format:** Replace "This skill should be used when the user asks to" with "Use when"
2. **Quote trigger phrases:** Wrap specific triggers in quotes

**Before:**
```yaml
description: This skill should be used when the user asks to "create a hook", "add a PreToolUse hook"...
```

**After:**
```yaml
description: Use when "creating a hook", "adding a PreToolUse hook", "validating tool use", or "implementing prompt-based hooks". Also when working with hook events (PreToolUse, PostToolUse, Stop, SubagentStop, SessionStart, SessionEnd, UserPromptSubmit, PreCompact, Notification).
```

---

## High Value

### 4. Establish Complementary Peer Relationship

**Files:** `writing-skills/SKILL.md`, `skill-development/SKILL.md`
**Effort:** ~15 min

These skills serve different domains and should cross-reference each other as peers:

| Skill | Domain | Core question |
|-------|--------|---------------|
| `writing-skills` | Process | HOW do I create and test a skill? |
| `skill-development` | Structure | WHAT goes in a skill? |

**Fix descriptions:**

```yaml
# writing-skills
description: Use when "creating skills", "testing skills", or applying TDD to documentation. For structure and file organization, see skill-development.

# skill-development
description: Use for "skill file structure", "SKILL.md format", "progressive disclosure" patterns, or organizing skill directories. For creation process and testing, see writing-skills.
```

**Add cross-reference in each skill's body:**

```markdown
## Related
For [process/structure], see the `[other-skill]` skill.
```

---

### 5. Tighten `writing-skills` Through Concision

**File:** `skills/writing-skills/SKILL.md`
**Effort:** ~45 min
**Target:** 3,202 → ~2,200 words

The skill contains redundancy and verbose sections. Tighten without fragmenting:

| Section | Action |
|---------|--------|
| CSO section (~600 words) | Condense to ~300 words using tables |
| Multiple "Bottom Line" summaries | Consolidate to one |
| Redundant explanations | Remove repetition of "third person", "imperative form" |
| Structural content | Remove (defer to `skill-development`) |

**Do not move essential workflow content to references.** The skill must remain self-sufficient.

---

### 6. Restructure `skill-development` as Structural Reference

**File:** `skills/skill-development/SKILL.md`
**Effort:** ~60 min
**Target:** 3,196 → ~1,200 words

The skill duplicates process content from `writing-skills`. Restructure as a focused structural reference:

**Keep:**
- About Skills (what they are)
- Anatomy of a Skill (directory structure)
- Bundled Resources (scripts/, references/, assets/)
- Progressive Disclosure Design Principle
- Plugin-Specific Considerations
- Quick Reference (structure templates)

**Remove:**
- Skill Creation Process (duplicates `writing-skills`)
- Writing Style Requirements (duplicates `writing-skills`)
- Validation Checklist (duplicates `writing-skills`)
- Common Mistakes to Avoid (partial overlap)
- Best Practices Summary (redundant)
- Implementation Workflow (redundant)
- Three separate "Additional Resources" sections (consolidate)

---

### 7. Restructure `writing-skills` Hierarchy

**File:** `skills/writing-skills/SKILL.md`
**Effort:** ~30 min (combine with #5)

The skill has 29 H2 sections—a flat, hard-to-navigate structure. Reorganize into 7 H2 sections with H3 subsections:

```markdown
# Writing Skills

## Overview
## When to Create a Skill
## The TDD Process
### The Iron Law
### RED: Write Failing Test
### GREEN: Write Minimal Skill
### REFACTOR: Close Loopholes
## Writing the Skill
### Claude Search Optimization (CSO)
### Skill Content Guidelines
## Testing by Skill Type
## Bulletproofing Against Rationalization
## Checklist
## Related
```

---

### 8. Update README to Document All Skills

**File:** `README.md`
**Effort:** ~20 min

The README lists 8 skills; the plugin has 10. Add documentation for:

**9. Writing Skills**
- Trigger phrases: "creating skills", "testing skills", "TDD for documentation"
- Covers: TDD methodology, CSO, bulletproofing, validation
- Related: For structure, see Skill Development

**10. Plugin Optimization**
- Trigger phrases: "optimize plugin", "improve plugin quality"
- Covers: Six-lens analysis, prioritized design documents
- Use after audit confirms no critical issues

Also:
- Fix intro from "nine specialized skills" to "ten specialized skills"
- Add brief agents section describing all three agents
- Explain the `writing-skills` ↔ `skill-development` relationship

---

## Consider

### 9. Add Table of Contents to Large Skills

**Files:** Skills over 500 lines
**Effort:** ~5 min per skill

Six skills exceed 500 lines. Consider adding a brief TOC after frontmatter for navigation. Lower priority—restructuring (#5, #6, #7) may reduce file sizes enough to make this unnecessary.

---

## Cross-Cutting Notes

### Implementation Order

```
Phase 1: Independent Quick Wins
├── #1: Fix plugin-validator script references
└── #2: Rename optimize → optimize-plugin

Phase 2: Content Restructuring
├── #6: Restructure skill-development
├── #5 + #7: Tighten + restructure writing-skills
└── #4: Add cross-references (complementary peers)

Phase 3: Description Updates (batch)
└── #3: Update all 8 skill descriptions

Phase 4: Documentation
└── #8: Update README
```

### Clustered Changes

**`writing-skills` changes (#3, #5, #7):** Implement together. The hierarchy restructure enables concision; description update is separate frontmatter change.

**`skill-development` changes (#3, #4, #6):** Implement together. Restructuring and relationship update are interdependent.

**Description updates (#3):** Batch after content restructuring. Apply consistent pattern across all skills.

### Key Principle to Codify

Add to `writing-skills` skill:

> **Skill Architecture Principle**
>
> SKILL.md = Complete workflow, self-sufficient for using the skill
> References = Deep knowledge on elemental concepts mentioned in the skill
>
> If Claude must read a reference to execute the skill, that content belongs in SKILL.md. References answer "tell me more about X"—not "what's the next step."

---

## Estimated Total Effort

| Priority | Items | Effort |
|----------|-------|--------|
| Quick Wins | #1, #2, #3 | ~55 min |
| High Value | #4, #5, #6, #7, #8 | ~170 min |
| Consider | #9 | ~30 min |
| **Total** | | **~4 hours** |

---

## Next Steps

1. Review this design document
2. Create implementation worktree: `git worktree add ../plugin-dev-optimization`
3. Execute phases in order
4. Run `/plugin-dev:audit-plugin` after each phase to verify
5. Commit and merge when complete
