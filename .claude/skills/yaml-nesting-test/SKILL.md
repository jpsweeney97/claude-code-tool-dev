---
name: yaml-nesting-test
description: Test skill to validate deep YAML nesting in frontmatter. Use when testing frontmatter parsing.
license: MIT
metadata:
  version: "1.0.0"
  decisions:
    requirements:
      explicit:
        - "Review code for logic bugs before PR merge"
        - "Generate summary report of findings"
      implicit:
        - "Should work on typical PR size (< 500 lines)"
        - "Supports common programming languages"
      discovered:
        - "Needs chunking strategy for large diffs"
        - "Must handle missing file context gracefully"
    approach:
      chosen: "Multi-phase: gather context, analyze, report"
      alternatives:
        - "Single-pass streaming — rejected: loses cross-file context"
        - "Checklist-only — rejected: bugs require reasoning"
    risk_tier: "medium"
    category: "code-quality"
    key_tradeoffs:
      - "Thoroughness vs. speed — chose thoroughness"
      - "Contextual analysis vs. file-by-file — chose contextual"
    methodology_insights:
      - "Inversion lens revealed: fails without surrounding code context"
      - "Pre-mortem revealed: reviewer fatigue on large diffs"
---

# YAML Nesting Test Skill

This skill exists solely to test whether Claude Code correctly parses deeply nested YAML in frontmatter.

## When to Use

- Testing frontmatter parsing
- Validating the skillosophy design proposal

## Verification

If this skill loads without errors and you can read this text, the nested YAML structure is valid.

## Expected Structure

The frontmatter contains:
- `metadata.decisions.requirements.explicit` — array (2 items)
- `metadata.decisions.requirements.implicit` — array (2 items)
- `metadata.decisions.requirements.discovered` — array (2 items)
- `metadata.decisions.approach.chosen` — string
- `metadata.decisions.approach.alternatives` — array (2 items)
- `metadata.decisions.risk_tier` — string
- `metadata.decisions.category` — string
- `metadata.decisions.key_tradeoffs` — array (2 items)
- `metadata.decisions.methodology_insights` — array (2 items)

This represents 4 levels of nesting with arrays containing multi-part strings.
