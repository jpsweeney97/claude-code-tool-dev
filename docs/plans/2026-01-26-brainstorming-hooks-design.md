# Design Context: brainstorming-hooks

**Type:** Solution Development
**Risk:** Low (design and implementation, no destructive operations)

## Problem Statement

People underuse hooks — they default to the obvious PreToolUse+Bash+block pattern without exploring the rich design space. Common mistakes include:
- Wrong event type selection
- Underusing JSON output capabilities (updatedInput, permissionDecision, additionalContext)
- Matcher scope issues (too broad or too narrow)
- Wrong hook type (command when prompt would be simpler)
- Exit code confusion (exit 1 doesn't block)

The hooks rule file covers implementation details but doesn't guide design exploration.

## Success Criteria

After using this skill:
1. User has seen 2-4 candidate approaches with trade-offs
2. User understands why one approach was recommended over others
3. Hook is fully specified (event, hook type, matcher, output mechanism, exit codes, format)
4. Hook is implemented in the appropriate location
5. Checkpoint verified all dimensions (event fit, hook type fit, matcher, output, performance, independence, format)

## Compliance Risks

| Risk | Mitigation |
|------|------------|
| Claude shortcuts to obvious pattern | Explicit "provoke creative options" step; require 2-3 approaches |
| User pushes to skip exploration | "Before I implement, are you open to a quick alternative?" |
| Claude rationalizes past checkpoint | Checkpoint is mandatory, not optional preparation |
| Implementation drifts from design | Checkpoint at end verifies all dimensions match |

## Entry Points

The skill handles four distinct starting points:
1. **Specific behavior wanted** — "I want to X" → clarify and explore alternatives
2. **Vague sense hooks could help** — "Something feels automatable" → explore what's repetitive
3. **Improving existing hook** — "I have this hook" → understand what it does and what's missing
4. **Proactive exploration** — "What can hooks do?" → patterns catalog as menu

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| Skill implements hooks, not just designs | User feedback: stopping at design is incomplete |
| Self-contained reference material | Skill should work without needing to read hooks.md |
| Comprehensive patterns catalog | Key differentiator from just reading docs |
| Hybrid process (explore then checklist) | Matches brainstorming-skills pattern |
| Weighted toward surfacing alternatives | Core value is expanding design space |

## Rejected Approaches

| Approach | Why Rejected |
|----------|--------------|
| Redirect to hook vs. other mechanism | Scope creep; skill assumes hooks are the answer |
| Include hook testing | Separate concern; keeps skill focused |
| Linear checklist-first process | Doesn't encourage creative exploration |
| Minimal patterns (just underexplored ones) | Comprehensive catalog is the main value-add |

## Reference Files Created

1. **hook-design-space.md** — Technical reference: event types, hook types, matchers, output mechanisms, input schemas
2. **creative-patterns-catalog.md** — Patterns organized by goal (enforce, capture, inject, integrate) plus underexplored patterns
3. **hook-implementation-checklist.md** — Quick reference for implementation: templates, exit codes, JSON schemas, testing

## Testing Notes

To validate the skill works:
1. Give it a goal like "notify me when Claude is idle"
2. Verify it surfaces multiple approaches (Notification hook, prompt hook, different matchers)
3. Verify it presents trade-offs before converging
4. Verify implemented hook matches the selected design
