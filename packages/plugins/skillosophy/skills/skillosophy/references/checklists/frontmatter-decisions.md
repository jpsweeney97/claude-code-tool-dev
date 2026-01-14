# Frontmatter Decisions Checklist

## [MUST] — Structural Requirements

- [ ] `metadata.decisions` field present and parses as valid YAML
- [ ] Contains `requirements` object with at least one `explicit` entry
- [ ] Contains `approach.chosen` describing selected approach
- [ ] Contains `risk_tier` with value (Low/Medium/High)

## [SHOULD] — Quality Requirements

- [ ] `requirements.implicit` non-empty (user expectations not stated)
- [ ] `requirements.discovered` non-empty for non-trivial skills
- [ ] `approach.alternatives` includes ≥2 rejected approaches with rationale
- [ ] `risk_tier` includes rationale (not just "Medium")
- [ ] `key_tradeoffs` documents significant trade-offs made
- [ ] `methodology_insights` traces lens findings to sections
- [ ] `category` matches one of 21 defined categories

## [SEMANTIC] — Anti-Pattern Detection

| Pattern | Issue |
|---------|-------|
| Empty `alternatives` | Alternatives weren't explored |
| `risk_tier` without rationale | Classification not justified |
| `methodology_insights` with <5 entries | Methodology likely superficial |
| All insights say "no findings" | Analysis wasn't rigorous |
| `discovered` empty for complex skill | Analysis incomplete |
