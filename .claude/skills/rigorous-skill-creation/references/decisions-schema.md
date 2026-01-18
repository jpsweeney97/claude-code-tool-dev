# Decisions Schema

Template for `metadata.decisions` and `metadata.verification` in SKILL.md frontmatter.

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
  verification:
    baseline:
      scenarios_run: 3
      failures_observed: 3
      rationalizations_captured: ["exact phrase 1", "exact phrase 2"]
    testing:
      scenarios_passed: 3
      scenarios_failed: 0
    panel:
      status: "approved | skipped"
      agents_run: 4
```

## Field Descriptions

### decisions

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

### verification

| Field | Required | Description |
|-------|----------|-------------|
| `baseline.scenarios_run` | Yes | Number of baseline scenarios executed |
| `baseline.failures_observed` | Yes | Number of failures observed without skill |
| `baseline.rationalizations_captured` | Should | Exact phrases from rationalization attempts |
| `testing.scenarios_passed` | Yes | Number of scenarios passing with skill |
| `testing.scenarios_failed` | Yes | Number of scenarios failing with skill |
| `panel.status` | Should | "approved" or "skipped" (with rationale) |
| `panel.agents_run` | Should | Number of review agents deployed |

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

## Verification Anti-Patterns

- `baseline.failures_observed: 0` → baseline didn't demonstrate the problem
- `rationalizations_captured: []` → didn't capture actual failure modes
- `testing.scenarios_passed < baseline.scenarios_run` → skill doesn't address all baseline failures
- `panel.status: "skipped"` without rationale → review obligation dodged
