# Extension Points Section Checklist

## [MUST] — Structural Requirements

- [ ] Section exists with `## Extension Points` heading
- [ ] Contains ≥2 extension point entries
- [ ] Each entry is actionable (verb + object)
- [ ] No vague entries ("improve", "enhance" without specifics)

## [SHOULD] — Quality Requirements

- [ ] Entries span different extension types (scope expansion, integration, optimization)
- [ ] Each entry is independently actionable
- [ ] Entries don't require major redesign (natural evolution paths)
- [ ] At least one entry addresses integration with other tools/skills
- [ ] Entries are forward-looking but realistic

## [SEMANTIC] — Anti-Pattern Detection

| Pattern | Issue |
|---------|-------|
| Entry starts with "improve", "enhance", "optimize" without specifics | Not actionable direction |
| Entry requires fundamental redesign | Not an extension, it's a rewrite |
| All entries are scope expansion | Missing integration/optimization paths |
| Entry duplicates existing functionality | Not actually an extension |
