# Changelog

All notable changes to doc-auditor will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-12-28

### Added

- **Coherence Report** (`/doc-auditor:report`) — Synthesize what documentation actually describes as a unified design
- **Issue Scanner** (`/doc-auditor:scan`) — Detect 15 categories of documentation problems with severity levels
- **Interactive Repair** (`/doc-auditor:repair`) — Walk through issues with accept/skip/suppress workflow
- **Pre-commit Hook** — Optional hook to block commits when documentation has issues
- **Template Compliance** — Enforce required sections for 14 document types

#### Issue Categories

Detection across 15 categories with 74 subcategories:

1. `contradictions` — Same thing described differently
2. `dangling-references` — Links to nonexistent targets
3. `undefined-terms` — Jargon never explained
4. `orphaned-content` — Docs nothing links to
5. `scope-creep` — Over-engineering, speculation
6. `coverage-gaps` — Missing error handling, rationale
7. `stale-content` — Outdated information
8. `structural` — Formatting, heading issues
9. `ambiguity` — Vague language, unclear referents
10. `code-doc-drift` — Docs don't match code
11. `security` — Credentials, insecure patterns
12. `readability` — Complex sentences, jargon density
13. `duplication` — Copy-pasted content
14. `navigation` — Missing TOCs, poor discoverability
15. `template-compliance` — Missing required sections

#### Agents

- `coherence-analyzer` — Synthesizes documentation into unified design view
- `issue-detector` — Scans for issues across all 15 categories

#### Configuration

- YAML frontmatter configuration in `.claude/doc-auditor.local.md`
- Include/exclude patterns for file selection
- Per-category enable/disable
- Severity thresholds and confidence levels
- Entry point specification for navigation analysis
- Code paths for drift detection

#### Inline Suppressions

- `<!-- doc-auditor:ignore CATEGORY -->` block suppressions
- `<!-- doc-auditor:ignore-line CATEGORY -->` single-line suppressions

#### Templates

- 14 document type templates with required/optional sections
- Strictness levels: strict, moderate, lenient

[1.0.0]: https://github.com/jp/doc-auditor/releases/tag/v1.0.0
