# Configuration Guide

This guide explains how to configure doc-auditor for your project using `.claude/doc-auditor.local.md`.

## File Location

Create the configuration file at:
```
your-project/.claude/doc-auditor.local.md
```

The file uses YAML frontmatter. Any markdown content below the frontmatter is ignored.

## Complete Configuration Example

```yaml
---
# =============================================================================
# SCOPE: Which files to analyze
# =============================================================================

include_patterns:
  - "docs/**/*.md"           # All markdown in docs/
  - "*.md"                   # Root-level markdown (README, CHANGELOG, etc.)
  - "src/**/*.md"            # Inline documentation

exclude_patterns:
  - "node_modules/**"        # Dependencies (default)
  - ".git/**"                # Git internals (default)
  - "vendor/**"              # Vendored code (default)
  - "docs/archive/**"        # Archived docs
  - "docs/generated/**"      # Auto-generated docs
  - "**/CHANGELOG.md"        # Skip changelogs if too noisy

# =============================================================================
# DETECTION: What to look for and how strict
# =============================================================================

detection:
  # Minimum severity to report
  # Options: LOW | MEDIUM | HIGH | CRITICAL
  # Default: LOW (report everything)
  min_severity: LOW

  # Minimum confidence to report
  # Options: LOW | MEDIUM | HIGH
  # Default: LOW (report uncertain findings too)
  # Set to HIGH if you want only definite issues
  confidence_threshold: LOW

  # Days before content is considered potentially stale
  # Default: 180
  staleness_days: 180

  # Enable/disable specific categories
  # All true by default
  categories:
    # Core quality issues (usually keep enabled)
    contradictions: true        # Same thing described differently
    dangling-references: true   # Broken links
    undefined-terms: true       # Jargon without definitions
    coverage-gaps: true         # Missing expected content
    structural: true            # Formatting problems

    # Context-dependent (may want to tune)
    orphaned-content: true      # Requires entry_points to work well
    stale-content: true         # May be noisy for stable projects
    ambiguity: true             # Can be subjective

    # Often noisy - consider disabling initially
    scope-creep: false          # Over-engineering detection
    readability: false          # Sentence complexity
    duplication: false          # Copy-paste detection

    # Requires additional config
    code-doc-drift: true        # Needs code_paths
    template-compliance: true   # Uses built-in or custom templates

    # Security-focused
    security: true              # Credentials, insecure patterns

    # Navigation
    navigation: true            # TOCs, discoverability

# =============================================================================
# ENTRY POINTS: For orphan detection
# =============================================================================

# Documents that serve as navigation roots
# Orphan detection traces links from these files
# If not specified, auto-detects: README.md, docs/index.md, index.md
entry_points:
  - "README.md"
  - "docs/index.md"
  - "docs/README.md"

# =============================================================================
# CODE CROSS-REFERENCE: For code-doc-drift detection
# =============================================================================

# Source files to cross-reference against documentation
# Used to detect when docs don't match actual implementation
code_paths:
  - "src/**/*.py"
  - "src/**/*.ts"
  - "src/**/*.js"
  - "lib/**/*.go"

# =============================================================================
# TEMPLATE COMPLIANCE
# =============================================================================

templates:
  # Enable template compliance checking
  # Default: true
  enforce: true

  # How strict to be about template requirements
  # Options: strict | moderate | lenient
  # - strict: All required sections must exist with correct order
  # - moderate: Required sections must exist, order flexible
  # - lenient: Only check for critical sections
  # Default: strict
  strictness: strict

  # Paths to custom template definitions
  # Templates in these dirs override built-in templates
  custom_templates:
    - ".claude/doc-templates/"

# =============================================================================
# DOCUMENT TYPE MAPPINGS
# =============================================================================

# Override automatic document type detection
# Maps glob patterns to document types
document_types:
  "docs/adr/*.md": adr
  "docs/api/**/*.md": api-reference
  "docs/runbooks/**/*.md": runbook
  "docs/guides/**/*.md": how-to-guide
  "docs/tutorials/**/*.md": tutorial
  "CHANGELOG.md": changelog
  "CONTRIBUTING.md": contributing
  "SECURITY.md": security-policy

# =============================================================================
# INLINE SUPPRESSION
# =============================================================================

# Prefix for inline suppression comments
# Default: "doc-auditor"
# Change if it conflicts with other tools
suppression_prefix: "doc-auditor"
---

Any markdown content below the frontmatter is ignored.
You can use this space for notes about your configuration choices.
```

## Minimal Configuration

For most projects, start with this minimal config:

```yaml
---
include_patterns:
  - "docs/**/*.md"
  - "*.md"

entry_points:
  - "README.md"
---
```

Then add more settings as needed based on scan results.

## Configuration by Project Type

### Library/Package

```yaml
---
include_patterns:
  - "docs/**/*.md"
  - "*.md"

detection:
  categories:
    code-doc-drift: true      # API docs should match code
    template-compliance: true  # Enforce README structure

code_paths:
  - "src/**/*.py"             # Adjust for your language

entry_points:
  - "README.md"
  - "docs/index.md"
---
```

### Internal Documentation

```yaml
---
include_patterns:
  - "docs/**/*.md"

detection:
  min_severity: MEDIUM        # Less strict for internal docs
  categories:
    scope-creep: false        # Internal docs can be speculative
    readability: false        # Team knows the jargon

entry_points:
  - "docs/index.md"
---
```

### API Documentation

```yaml
---
include_patterns:
  - "docs/api/**/*.md"

detection:
  categories:
    code-doc-drift: true
    coverage-gaps: true       # All endpoints documented
    template-compliance: true

code_paths:
  - "src/routes/**/*.ts"
  - "src/controllers/**/*.ts"

document_types:
  "docs/api/**/*.md": api-reference
---
```

### Monorepo

```yaml
---
include_patterns:
  - "packages/*/README.md"
  - "packages/*/docs/**/*.md"
  - "docs/**/*.md"

exclude_patterns:
  - "packages/deprecated-*/**"

entry_points:
  - "README.md"
  - "docs/index.md"
---
```

## Tuning for Noise

If scans produce too many issues:

1. **Raise severity threshold:**
   ```yaml
   detection:
     min_severity: MEDIUM  # or HIGH
   ```

2. **Raise confidence threshold:**
   ```yaml
   detection:
     confidence_threshold: HIGH
   ```

3. **Disable noisy categories:**
   ```yaml
   detection:
     categories:
       ambiguity: false
       readability: false
       scope-creep: false
   ```

4. **Use inline suppressions** for specific exceptions:
   ```markdown
   <!-- doc-auditor:ignore-line undefined-terms -->
   The frobnicator handles edge cases.
   ```

## Gitignore Recommendations

Add to your `.gitignore`:
```
# doc-auditor scan results (regenerated on each scan)
.claude/doc-auditor/
```

The config file (`.claude/doc-auditor.local.md`) is safe to commit — it contains no sensitive data and helps maintain consistent documentation standards across your team.
