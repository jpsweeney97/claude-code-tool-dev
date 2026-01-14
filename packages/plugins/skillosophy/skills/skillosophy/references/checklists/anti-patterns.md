# Anti-Patterns Section Checklist

## [MUST] — Structural Requirements

- [ ] Section exists with `## Anti-Patterns` heading
- [ ] Contains ≥1 anti-pattern entry
- [ ] Each entry has pattern description
- [ ] Each entry has consequence (why it's problematic)
- [ ] Not duplicates of "When NOT to use" entries

## [SHOULD] — Quality Requirements

- [ ] Minimum entries matches risk tier: Low ≥1, Medium ≥2, High ≥2
- [ ] Each explains *why* the pattern is problematic (not just "don't do this")
- [ ] Entries are distinct from "When NOT to use" (anti-patterns = bad practices during use; when-not-to-use = wrong context for skill)
- [ ] Patterns are specific enough to recognize
- [ ] Consequences describe observable negative outcomes

## [SEMANTIC] — Anti-Pattern Detection

| Pattern | Issue |
|---------|-------|
| Entry without consequence | No motivation to avoid |
| Vague pattern ("don't do bad things") | Not actionable |
| Duplicates When NOT to use | Wrong section |
| Only 1 entry for High risk skill | Insufficient coverage |
