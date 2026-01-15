# doc-auditor

Documentation audit and repair for Claude Code. Analyzes documentation sets for coherence, detects 15 categories of issues, and provides interactive fixes.

## Features

- **Coherence Report** — Synthesize what docs actually describe ("forest view")
- **Issue Scan** — Detect 15 categories of documentation problems
- **Interactive Fix** — Walk through issues with accept/skip/suppress options
- **Pre-commit Hook** — Block commits when documentation has issues (optional)
- **Template Compliance** — Enforce required sections for 14 document types

## Commands

| Command | Description |
|---------|-------------|
| `/doc-auditor:report [path]` | Generate coherence report |
| `/doc-auditor:scan [path]` | Scan for issues, save results |
| `/doc-auditor:repair [options]` | Interactive repair session |

### Repair Options

```
/doc-auditor:repair                    # All issues
/doc-auditor:repair --critical         # CRITICAL and HIGH only
/doc-auditor:repair --category=X       # Single category
/doc-auditor:repair ISSUE-ID           # Single issue by ID
```

## Issue Categories

| # | Category | What It Catches |
|---|----------|-----------------|
| 1 | `contradictions` | Same thing described differently |
| 2 | `dangling-references` | Links to nonexistent targets |
| 3 | `undefined-terms` | Jargon never explained |
| 4 | `orphaned-content` | Docs nothing links to |
| 5 | `scope-creep` | Over-engineering, speculation |
| 6 | `coverage-gaps` | Missing error handling, rationale |
| 7 | `stale-content` | Outdated information |
| 8 | `structural` | Formatting, heading issues |
| 9 | `ambiguity` | Vague language, unclear referents |
| 10 | `code-doc-drift` | Docs don't match code |
| 11 | `security` | Credentials, insecure patterns |
| 12 | `readability` | Complex sentences, jargon density |
| 13 | `duplication` | Copy-pasted content |
| 14 | `navigation` | Missing TOCs, poor discoverability |
| 15 | `template-compliance` | Missing required sections |

## Configuration

Create `.claude/doc-auditor.local.md` in your project with YAML frontmatter.

**Full guide:** See `references/configuration-guide.md` for complete options and examples by project type.

**Minimal example:**

```yaml
---
include_patterns:
  - "docs/**/*.md"
  - "*.md"
exclude_patterns:
  - "docs/archive/**"

detection:
  min_severity: LOW           # LOW | MEDIUM | HIGH | CRITICAL
  categories:
    contradictions: true
    dangling-references: true
    # ... (all 15 categories enabled by default)
  confidence_threshold: LOW   # Report uncertain findings
  staleness_days: 180

entry_points:
  - "README.md"
  - "docs/index.md"

code_paths:                   # For code-doc-drift detection
  - "src/**/*.py"

templates:
  enforce: true
  strictness: strict          # strict | moderate | lenient
---
```

## Inline Suppressions

Suppress specific issues in documentation:

```markdown
<!-- doc-auditor:ignore undefined-terms -->
The frobnicator handles all edge cases.
<!-- doc-auditor:end-ignore -->

<!-- doc-auditor:ignore-line ambiguity -->
This is handled automatically.
```

## Pre-commit Hook

The pre-commit hook is **disabled by default**. To enable:

1. Edit `hooks/hooks.json`
2. Remove `"disabled": true` from the hook configuration

When enabled, the hook:
- Blocks commits when ANY documentation issues exist
- Requires scan results to be <1 hour old
- Only activates when markdown files are being committed

## Output Files

| File | Purpose |
|------|---------|
| `.claude/doc-auditor.local.md` | Configuration (you create) |
| `.claude/doc-auditor/scan-results.json` | Last scan results (gitignore) |

## Workflow

1. **Scan:** `/doc-auditor:scan` to detect issues
2. **Review:** Check summary for issue counts
3. **Repair:** `/doc-auditor:repair` to walk through issues interactively
4. **Repeat:** Re-scan to verify fixes

## Severity Levels

| Severity | Meaning |
|----------|---------|
| **CRITICAL** | Core design contradictions; would cause implementation errors |
| **HIGH** | Behavioral contradictions; missing critical information |
| **MEDIUM** | Inconsistencies that cause confusion; incomplete sections |
| **LOW** | Style issues; minor gaps; cosmetic problems |

## Requirements

- Claude Code
- `jq` (for pre-commit hook only)

## Design Document

This plugin was built from a comprehensive design document that specifies:
- All 15 issue categories with 74 subcategories
- Detection patterns and severity guidelines
- Output schemas and persistence formats
- Edge case handling and error recovery

See the original design: `~/.claude/docs/plans/2025-12-28-doc-auditor-design-v2.3.md`
