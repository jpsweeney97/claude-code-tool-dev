# When NOT to Use Checklist

## Structural
- [MUST] Section exists with clear heading or equivalent
- [MUST] Contains at least 3 explicit non-goals or out-of-scope items

## Semantic
- [MUST] Non-goals prevent common scope failures
- [MUST] Includes STOP conditions (explicit triggers to halt and route elsewhere)
- [SHOULD] Default non-goals stated if applicable:
  - No dependency upgrades (unless skill's purpose)
  - No public API changes (unless skill's purpose)
  - No destructive actions (unless skill's purpose)
  - No schema/data migrations (unless skill's purpose)

## Anti-patterns
- [SEMANTIC] Non-goals are just routing suggestions without STOP language
- [SEMANTIC] Missing boundaries that would surprise reviewers
