# Triggers Section Checklist

## [MUST] — Structural Requirements

- [ ] Section exists with `## Triggers` heading
- [ ] Contains ≥3 trigger phrases
- [ ] Each phrase ≤50 characters
- [ ] No duplicate phrases
- [ ] No overlap with "When to use" content (triggers are literal phrases, not conditions)

## [SHOULD] — Quality Requirements

- [ ] Includes both verb phrases ("create a", "build a") and noun phrases ("new skill", "skill for")
- [ ] Covers common synonyms (create/build/make, skill/workflow/automation)
- [ ] Avoids overly generic triggers that match unrelated intents
- [ ] Phrases represent how users actually speak

## [SEMANTIC] — Anti-Pattern Detection

| Pattern | Issue |
|---------|-------|
| Trigger >30 chars | Too specific — won't match variations |
| Single-word trigger | Too broad — false positives |
| Trigger matches common Claude commands | Conflict with built-in functionality |
| All triggers start same way | Limited discoverability |
