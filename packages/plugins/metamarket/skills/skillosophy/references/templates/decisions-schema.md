# Decisions Schema

Template for `metadata.decisions` in SKILL.md frontmatter.

```yaml
metadata:
  version: "1.0.0"
  decisions:
    requirements:
      explicit:
        - "What user literally asked for"
      implicit:
        - "What user expects but didn't state"
      discovered:
        - "What analysis revealed as necessary"
    approach:
      chosen: "Selected approach in one sentence"
      alternatives:
        - "Alternative 1 — rejected because: reason"
        - "Alternative 2 — rejected because: reason"
    risk_tier: "Low | Medium | High — rationale"
    key_tradeoffs:
      - "Tradeoff 1: chose X over Y because Z"
    category: "one-of-21-categories"
    methodology_insights:
      - "Lens: finding → affected section"
```

## Field Descriptions

| Field | Required | Description |
|-------|----------|-------------|
| `requirements.explicit` | Yes | Direct quotes or paraphrases of user's stated needs |
| `requirements.implicit` | No | Unstated expectations inferred from context |
| `requirements.discovered` | No | Needs revealed through analysis |
| `approach.chosen` | Yes | The selected design approach |
| `approach.alternatives` | Should | Rejected alternatives with rationale |
| `risk_tier` | Yes | Low/Medium/High with justification |
| `key_tradeoffs` | Should | Significant trade-offs documented |
| `category` | Should | One of 21 skill categories |
| `methodology_insights` | Should | >=5 substantive lens insights |

## Quality Guidelines

**[SHOULD] Requirements:**
- `alternatives` should include ≥2 rejected approaches with rationale
- `discovered` requirements should be non-empty for non-trivial skills
- `methodology_insights` should trace findings to specific sections (not just "applied X lens")

**[SEMANTIC] Anti-Patterns:**
- Empty `alternatives` → alternatives weren't explored
- `risk_tier` without rationale → classification not justified
- `methodology_insights` with <5 entries → methodology likely superficial
- All insights say "no findings" → analysis wasn't rigorous
