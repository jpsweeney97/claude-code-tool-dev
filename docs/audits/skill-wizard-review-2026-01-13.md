# Skill-Wizard Review Report

**Date:** 2026-01-13
**Target:** `.claude/skills/skill-wizard/`
**Type:** Meta-skill (skill creation wizard)
**Reviewer:** Claude Opus 4.5

---

## Executive Summary

`skill-wizard` is a well-structured meta-skill for guided, interactive skill creation. It provides a systematic walkthrough of the skills-as-prompts specification, generating spec-compliant SKILL.md files through collaborative dialogue. While it excels in structural compliance and progressive disclosure, it has opportunities for enhancement in validation depth, integration with the existing extension ecosystem, and recovery handling.

---

## Strengths

### 1. Rigorous Spec Compliance Architecture

The skill embeds the full skills-as-prompts specification through decomposed reference files:

| Reference File | Purpose |
|----------------|---------|
| `spec-requirements.md` | MUST/SHOULD/SEMANTIC anti-pattern definitions |
| `risk-tier-guide.md` | Tier selection and downgrade validation |
| `category-integration.md` | 21 categories with DoD additions |
| 8 `checklist-*.md` files | Per-section structural and semantic checks |

This separation of concerns means spec changes propagate cleanly — update the reference, and validation improves.

### 2. Session Recovery via Artifact Checkpointing

The skill uses the SKILL.md file itself as the checkpoint mechanism:

```markdown
When user says "continue wizard" or "resume skill-wizard":
1. Read existing SKILL.md at target path
2. Parse wizard metadata from frontmatter
3. Validate each existing section against checklists
4. Present summary and resume from first missing/invalid section
```

This is elegant — no external state management, and external edits between sessions are automatically validated.

### 3. Progressive Disclosure Through References

Main SKILL.md stays under 500 lines by deferring detailed guidance to `references/` and `templates/`. This matches the skill's own advice about keeping skills focused.

### 4. Observable Decision Points

Decision points use concrete signals, not subjective judgment:

- "If output path has SKILL.md with `metadata.wizard.status: draft`" — file existence check
- "If skill has mutating actions but user selected Low risk" — deterministic rule
- "If cross-section check fails" — validation result, not intuition

### 5. Category-Aware DoD Generation

`category-integration.md` provides 21 skill categories with specialized Definition of Done additions. When a user selects "security-changes", the wizard knows to add:

- Threat model boundaries stated
- Deny-path verification included
- Rollback plan specified

This prevents generic, underspecified outputs.

---

## Weaknesses

### 1. No Automated Validation Scripts

**The gap:** Skill-wizard describes validation checks but relies entirely on Claude's in-context analysis. There are no executable scripts to verify compliance objectively.

**Evidence:** The skill references commands like `grep -c "^## " <path>/SKILL.md` in verification, but doesn't include actual scripts in a `scripts/` directory.

**Compare to:** `skillforge` includes `validate-skill.py`, `quick_validate.py`, and `package_skill.py` for objective verification.

**Impact:** Without scripts, validation depends on Claude's attention and interpretation. Edge cases may slip through.

### 2. Missing Frontmatter Validation for `allowed-tools`

**The gap:** The frontmatter checklist (`checklist-frontmatter.md`) says:

> `[MUST] allowed-tools lists all tools actually used by skill (if skill uses tools)`

But the wizard doesn't verify this cross-reference during drafting. The procedure collects tools during discovery (question g) but doesn't re-validate against the Procedure section's actual tool usage.

**Impact:** Skills could have `allowed-tools: Read, Write` but then reference `Bash` in the procedure without the wizard catching it.

### 3. Heavy Context Load

**The gap:** The skill system includes 17 reference/template files totaling ~1,200 lines. When all are loaded for comprehensive validation, this consumes significant context.

**Evidence:** Phase 3, step 9d says:

> - **Cross-reference with other sections:**
>   - If Procedure mentions tools, verify they're in `allowed-tools`
>   - If Procedure mentions writing files, verify fallback exists
>   - If Verification has commands, verify they use literal paths

This requires reading multiple sections simultaneously while holding checklists in context.

**Impact:** In long sessions, earlier content may be summarized, potentially losing checklist details.

### 4. Discovery Phase Ordering Issue

**The gap:** The discovery phase asks for output path (step 4) *before* completing the conceptual exploration. But step 3 says:

> "Explore approaches (when design choices exist)"

If the approach exploration leads to a different skill structure (e.g., "this should be a command, not a skill"), the path question was premature.

**Impact:** Minor — the wizard can recover by navigating back, but the flow creates slight friction.

### 5. No Integration with Existing Extension Infrastructure

**The gap:** The wizard creates SKILL.md files but doesn't:

- Check if a similar skill already exists (unlike skillforge's Phase 0 triage)
- Offer to run `audit-design` afterward for feasibility review
- Suggest `design-reviewer` for design validation before implementation

**Evidence:** The "When NOT to Use" section mentions routing to other tools but doesn't integrate with them:

> Route to: `skill-reviewer` agent or manual review against compliance checklist.

But there's no `skill-reviewer` agent in the repo — this appears to be aspirational.

### 6. Limited Error Recovery in Cross-Section Validation

**The gap:** Phase 4 says:

> If issues found: Identify which sections need revision → Navigate user to those sections → Re-run section validation after edits → Loop until all checks pass

But there's no guidance on handling dependency chains. If editing the Inputs section invalidates the Procedure (which references those inputs), and editing the Procedure invalidates Verification (which checks Procedure outputs), the user could be in a loop.

**Impact:** Could lead to frustration in complex revisions.

---

## Enhancement Opportunities

### 1. Add Validation Scripts

Create a `scripts/` directory with:

```
scripts/
├── validate-structure.py    # Check 8 sections exist
├── validate-frontmatter.py  # Check name, description constraints
├── validate-crossref.py     # Check allowed-tools vs Procedure
└── validate-semantic.py     # Detect anti-pattern language
```

This would enable:
- Objective verification independent of Claude's attention
- Pre-commit hooks for skill quality gates
- CI integration for skill repos

**Implementation note:** Use Python stdlib only per project conventions. The skill already has `Bash` in allowed-tools.

### 2. Pre-Flight Duplicate Check

Before Phase 1 discovery, scan existing skills:

```python
# Pseudo-code for discovery
existing_skills = glob("~/.claude/skills/**/SKILL.md") + glob(".claude/skills/**/SKILL.md")
for skill in existing_skills:
    if similarity(new_purpose, skill.description) > 0.7:
        warn(f"Similar skill exists: {skill.name}")
```

This mirrors skillforge's Phase 0 triage but in a lighter-weight form.

### 3. Explicit Dependency Graph for Revisions

Add a revision tracking mode in Phase 4:

```markdown
## Revision Impact Graph

When editing a section, these sections may become invalid:

| If you edit... | Re-validate... |
|----------------|----------------|
| When to use | When NOT to use |
| Inputs | Procedure, Verification |
| Outputs | Procedure, Verification |
| Procedure | Decision points, Verification, Troubleshooting |
```

The `section-order.md` reference already has this information — surface it during revision.

### 4. Post-Creation Workflow Suggestions

After completion, offer next steps:

```markdown
## Next Steps

1. Test: Run `/<skill-name>` in this project
2. Audit: Run `/audit-design .claude/skills/<name>/SKILL.md` for feasibility review
3. Promote: Run `uv run scripts/promote skill <name>` to deploy to ~/.claude/
```

This integrates with the existing extension ecosystem.

### 5. Checklist Aggregation for Context Efficiency

Instead of loading 8 separate checklist files, maintain a compiled single-file version:

```bash
# Build script
cat references/checklist-*.md > references/checklist-compiled.md
```

Load the compiled version during validation to reduce file read operations and keep related content together.

---

## Merger Opportunities

### 1. skill-wizard + audit-design Integration

**Current state:** Both skills produce quality assessments of skill designs, but at different stages:

- `skill-wizard`: Creates skills with inline validation during drafting
- `audit-design`: Reviews existing designs for feasibility/risk

**Merger opportunity:** Add audit-design's feasibility checks as an optional Phase 4.5:

```markdown
### Phase 4.5: Feasibility Audit (Optional)

After cross-section validation passes:

1. Ask user: "Run feasibility audit? This checks for Claude capability assumptions."
2. If yes, apply audit-design's checks:
   - State assumptions (persistent memory, learning)
   - Reasoning complexity (multi-step without verification)
   - Tool behavior assumptions
3. Add findings to compliance summary
```

This catches issues like "assumes Claude remembers previous runs" that structural validation misses.

### 2. skill-wizard + skillforge Relationship Clarification

**Current state:** Both skills create skills, but with very different approaches:

| Aspect | skill-wizard | skillforge |
|--------|--------------|------------|
| Model | Interactive dialogue | Autonomous with panel review |
| Complexity | Moderate (~426 lines) | High (~872 lines) |
| Validation | Inline during drafting | Post-hoc with scripts |
| Duplicate detection | None | Phase 0 triage |
| Target user | Learning the spec | Power users wanting automation |

**Recommendation:** Don't merge — they serve different needs. But improve routing:

```markdown
## skill-wizard's "When NOT to Use"

- **STOP** if user says "skillforge", "ultimate skill", or wants autonomous creation.
  Route to: `skillforge` for autonomous multi-agent skill creation.
```

And update skillforge's Phase 0 triage to recognize "skill-wizard" as an explicit create intent that wants interactive mode.

### 3. Create a Shared Validation Library

Both skill-wizard and skillforge need to validate against the skills spec. Currently:

- skill-wizard has 11 checklist reference files
- skillforge has `validate-skill.py` and spec templates

**Merger opportunity:** Create a shared `references/skill-validation/` library:

```
.claude/references/skill-validation/
├── spec-requirements.md      # Shared spec source of truth
├── checklists/              # Section checklists (from skill-wizard)
├── scripts/                 # Validation scripts (from skillforge)
└── templates/               # Wording patterns, semantic templates
```

Both skills reference this shared location. Updates propagate to both.

---

## Priority Recommendations

| Priority | Enhancement | Effort | Impact |
|----------|-------------|--------|--------|
| **P1** | Add validation scripts | Medium | Objective verification, CI integration |
| **P1** | Add duplicate check before Phase 1 | Low | Prevents redundant skill creation |
| **P2** | Integrate audit-design feasibility checks | Medium | Catches capability assumptions |
| **P2** | Surface revision dependency graph | Low | Reduces revision loop frustration |
| **P3** | Create shared validation library | High | Consolidates spec enforcement |
| **P3** | Compile checklists for context efficiency | Low | Reduces context pressure |

---

## Conclusion

skill-wizard is a well-designed meta-skill that successfully balances comprehensiveness with usability. Its modular checklist architecture and artifact-based session recovery are particularly strong. The primary gaps are:

1. **Lack of executable validation** — relying on Claude's attention rather than scripts
2. **Missing duplicate detection** — could create redundant skills
3. **Limited integration** with the broader extension ecosystem (audit-design, skillforge)

The skill doesn't need major restructuring — targeted enhancements (validation scripts, duplicate check, audit integration) would significantly improve its reliability without changing its interactive, educational character.

**Meta-observation:** skill-wizard is itself a skill that should be audited by audit-design. Running `/audit-design .claude/skills/skill-wizard/SKILL.md` would catch any feasibility issues in its own design — a nice dogfooding opportunity.
