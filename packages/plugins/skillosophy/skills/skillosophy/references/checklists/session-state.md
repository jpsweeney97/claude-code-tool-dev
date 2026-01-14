# Session State Checklist

## [MUST] — Structural Requirements

- [ ] Section exists with `## Session State` heading (during creation)
- [ ] Contains `phase` field with value 0-4
- [ ] Contains `progress` field in format "N/11" (body sections completed, not phases)
- [ ] Removed after Phase 4 approval (not present in final skill)

## [SHOULD] — Quality Requirements

- [ ] `dialogue_context` captures user preferences discovered during session
- [ ] `next_steps` is specific (not just "continue" or "proceed")
- [ ] Updated after each section approval in Phase 3
- [ ] `last_action` describes what happened before any interruption

## [SEMANTIC] — Anti-Pattern Detection

| Pattern | Issue |
|---------|-------|
| `next_steps` contains only "continue" or "proceed" | Not specific enough for recovery |
| `progress` doesn't match actual sections present | State out of sync |
| `phase` value doesn't match progress | Inconsistent state |
| Session State present in "final" skill | Not cleaned up after approval |

## Lifecycle

| Phase | Session State |
|-------|---------------|
| Phase 0 (Triage) | Not yet created |
| Phase 1 (Analysis) | Created at end with initial state |
| Phase 2 (Checkpoint) | Updated with validated decisions |
| Phase 3 (Generation) | Updated after each section approval |
| Phase 4 (Panel) | Present during review |
| After approval | **Removed** |
