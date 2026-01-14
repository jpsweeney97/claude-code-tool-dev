# Session State Schema

Template for `## Session State` section (transient, removed after approval).

```markdown
## Session State
<!-- Removed automatically after Phase 4 approval -->

**Phase:** 0-4
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
| `Phase` | Yes | Current phase (0=Triage, 1=Analysis, 2=Checkpoint, 3=Generation, 4=Panel) |
| `Progress` | Yes | Sections approved out of 11 |
| `Last action` | Yes | What happened immediately before (for context on resume) |
| `Dialogue Context` | Should | Key exchanges, preferences, insights not yet in sections |
| `Next Steps` | Yes | Specific upcoming action |

## Lifecycle

- Created: End of Phase 1
- Updated: After each section approval in Phase 3
- Removed: After Phase 4 unanimous approval

## Quality Guidelines

**next_steps — specific vs. generic:**
- ✅ Good: "Generate Decision Points section, starting with user preference for fail-fast behavior"
- ❌ Poor: "Continue"
- ❌ Poor: "Proceed with remaining sections"

**dialogue_context — capture decisions:**
- ✅ Good: "User prefers explicit error handling over silent failures"
- ❌ Poor: "Discussed error handling"
