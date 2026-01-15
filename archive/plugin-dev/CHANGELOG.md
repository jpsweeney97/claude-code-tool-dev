# Changelog

All notable changes to plugin-dev will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **`brainstorming-commands` skill** - 6-step collaborative workflow for command design
- **`implementing-commands` skill** - TDD-focused command implementation with iron law

## [1.4.0] - 2025-12-31

### Changed
- **BREAKING**: Renamed `skillcreator` to `skillforge` (upstream repo renamed)
- **SkillForge v4.0**: Now includes Phase 0 Triage before analysis
  - Routes requests to USE_EXISTING / IMPROVE_EXISTING / CREATE_NEW / COMPOSE / CLARIFY
  - Prevents ecosystem bloat with domain-based matching
  - New scripts: `triage_skill_request.py`, `discover_skills.py`
- Updated sync workflow to use `tripleyak/SkillForge` repository
- Updated all cross-references from skillcreator to skillforge

### Migration
- See `docs/migrations/skillcreator-to-skillforge.md` for migration guide
- Update any custom scripts referencing `skillcreator` to use `skillforge`

## [1.3.0] - 2025-12-30

### Added
- **SkillCreator skill** (now SkillForge) - Rigorous 4-phase skill creation methodology with:
  - 11 thinking lenses framework for deep analysis
  - Evolution/timelessness scoring (minimum 7/10 required)
  - Multi-agent synthesis panel (3 Opus agents, unanimous approval)
  - XML specification template
  - 3 validation/packaging scripts
- **`/plugin-dev:create-skill` command** - Entry point for SkillCreator workflow
- **Validation scripts** at plugin root (`scripts/`) for convenient access
- **Skill Creation Workflow** section in README with decision tree

### Changed
- **skill-reviewer agent** - Enhanced with evolution/timelessness scoring criteria
- **skill-development skill** - Added cross-reference to skillcreator
- **writing-skills skill** - Added cross-reference to skillcreator

## [1.2.0] - 2025-12-29

### Added
- **brainstorming-plugins skill** - Plugin design exploration workflow
- **`/plugin-dev:brainstorm` command** - Entry point for brainstorming

## [1.1.0] - 2025-12-28

### Added
- Initial plugin-dev toolkit release
- 11 specialized skills for plugin development
- 3 agents (agent-creator, plugin-validator, skill-reviewer)
- 5 commands (create-plugin, audit-plugin, fix-plugin, optimize-plugin, brainstorm)
- 50+ validation rules
