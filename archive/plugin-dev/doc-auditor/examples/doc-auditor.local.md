---
# doc-auditor configuration example
# Copy this to your project: .claude/doc-auditor.local.md

# Which files to scan
include_patterns:
  - "docs/**/*.md"
  - "*.md"

exclude_patterns:
  - "node_modules/**"
  - "vendor/**"

# Detection settings
detection:
  min_severity: LOW           # LOW | MEDIUM | HIGH | CRITICAL
  confidence_threshold: LOW   # LOW | MEDIUM | HIGH
  staleness_days: 180

  # Enable/disable categories (all true by default)
  categories:
    contradictions: true
    dangling-references: true
    undefined-terms: true
    orphaned-content: true
    scope-creep: false        # Often noisy, disabled
    coverage-gaps: true
    stale-content: true
    structural: true
    ambiguity: true
    code-doc-drift: true
    security: true
    readability: false        # Often noisy, disabled
    duplication: false        # Often noisy, disabled
    navigation: true
    template-compliance: true

# Entry points for orphan detection
entry_points:
  - "README.md"
  - "docs/index.md"

# Source files for code-doc-drift detection
code_paths:
  - "src/**/*.py"
  - "src/**/*.ts"

# Template compliance
templates:
  enforce: true
  strictness: strict          # strict | moderate | lenient
---

Configuration notes:
- Adjust include_patterns for your project structure
- Disable noisy categories initially, enable as you fix issues
- Set code_paths to match your source file locations
