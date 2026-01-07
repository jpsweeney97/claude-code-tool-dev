# Changelog

All notable changes to three-lens-audit.

## [1.15.0] - 2026-01-06

### Changed
- Condensed SKILL.md from 387 to 131 lines
- Extracted Cost Estimation, Incremental Mode, Execution to workflow-details.md
- Extracted Implementation Spec format to implementation-spec.md
- Moved lens philosophy to variants-and-custom-lenses.md

### Fixed
- Added semantic convergence guidance to synthesis template (addresses keyword-only detection limitation)
- Strengthened synthesize.py warning when no 3-lens convergence found

## [1.13.0] - 2026-01-04

### Fixed

- Added missing `--claude-code` preset to run_audit.py
- Replaced deprecated `subagent_type` with `name` in Task templates
- Fixed `--threshold` parameter not being passed to synthesis

### Added

- Basic Python tests for validate_output.py and synthesize.py
- CHANGELOG.md
- Fallback validation for custom lenses

### Changed

- Reduced SKILL.md size by moving details to references/
- De-duplicated prompts (run_audit.py now reads from agent-prompts.md)

### Documentation

- Added three-lens-audit to repository CLAUDE.md

## [1.12.0] - 2026-01-04

### Added

- Verified Claude Code capabilities reference (`references/claude-code-capabilities.md`)
- Artifact-specific checklists for Skills, Hooks, Plugins, MCP Servers, Commands, Subagents
- Claude Code feasibility audit preset (`--claude-code` flag)
- Basic tests for `validate_output.py` and `synthesize.py`

### Changed

- Refactored SKILL.md to move detailed sections to `references/` subdirectory
- Prompts now loaded from `references/agent-prompts.md` instead of inline

### Fixed

- Pass `--threshold` parameter through to synthesis
- Use `name` instead of deprecated `subagent_type` in Task tool calls

## [1.11.0] - 2026-01-02

### Added

- Pricing last-updated date in cost documentation
- Convergence algorithm limitation documentation

### Fixed

- Warning when no convergent findings detected

## [1.10.0] - 2026-01-02

### Added

- Action tracking template for re-audit workflow

## [1.9.0] - 2026-01-02

### Added

- Lens rationale documentation ("Why These Lenses?")

## [1.8.0] - 2026-01-02

### Added

- Inline example output in SKILL.md

## [1.7.0] - 2026-01-02

### Added

- Progressive disclosure with collapsible sections

## [1.6.0] - 2026-01-02

### Changed

- Improved workflow documentation

## [1.5.0] - 2026-01-02

### Added

- Pipeline orchestration with `run_audit.py prepare/finalize/status`

## [1.4.0] - 2026-01-02

### Added

- Automation scripts (`run_audit.py`, `synthesize.py`, `validate_output.py`)

## [1.3.0] - 2026-01-02

### Changed

- General improvements

## [1.2.0] - 2026-01-02

### Changed

- General improvements

## [1.0.0] - 2026-01-02

### Added

- Initial release
- Three default lenses: Adversarial, Pragmatic, Cost/Benefit
- Design preset with Robustness, Minimalist, Capability, Arbiter lenses
- Custom lens template
- Worked examples
