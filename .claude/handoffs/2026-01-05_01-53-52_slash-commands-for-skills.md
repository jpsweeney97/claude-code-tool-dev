---
date: 2026-01-05T01:53:52.131174
version: 1
git_commit: 9c8d4be
branch: main
repository: claude-code-tool-dev
tags: ["commands", "skills", "plugin-architecture"]
---

# Handoff: Slash commands for skills

## Goal
Add slash commands to skills that would benefit from explicit user invocation

## Key Decisions
- Skills and commands are complementary: skills for auto-discovery, commands for explicit invocation
- Thin wrapper pattern: command handles invocation, skill handles implementation
- Skip commands for implicit guidance skills (writing-clearly-and-concisely, writing-for-claude)
- Commands go in .claude/commands/ for project-level auto-discovery

## Recent Changes
- .claude/commands/retro.md - Wrapper for deep-retrospective skill
- .claude/commands/explore.md - Wrapper for deep-exploration skill
- .claude/commands/audit.md - Wrapper for three-lens-audit skill
- .claude/commands/security.md - Wrapper for deep-security-audit skill
- .claude/commands/adr.md - Wrapper for architecture-decisions skill
- .claude/commands/cli.md - Wrapper for cli-script-generator skill
- .claude/commands/subagent.md - Wrapper for creating-subagents skill
- .claude/commands/skillforge.md - Wrapper for skillforge skill

## Learnings
- Progressive disclosure: Skills use 3-level hierarchy (metadata → core → supporting files)
- Description field is critical for skill triggering - vague descriptions = skill never activates
- Commands created mid-session require restart to be discovered
- Official docs confirm .claude/commands/ is auto-discovered for project commands

## Next Steps
1. TEST: Start new Claude Code session and verify /retro, /explore, /audit etc. appear in autocomplete
2. TEST: Run /help to confirm commands are listed
3. INVESTIGATE: If commands do not appear, run claude --debug and check for loading errors
4. INVESTIGATE: Verify .claude/commands/ auto-discovery behavior matches official docs
5. CONSIDER: Add /format command for markdown-formatter skill (lower priority)
6. CONSIDER: Add /synthesize command for deep-synthesis skill (niche use case)

## Uncommitted Files
```
LAUDE.md
docs/plans/2026-01-04-promote-script-test-plan.md
packages/plugins/docs-kb/.claude-plugin/plugin.json
packages/plugins/docs-kb/skills/verify/SKILL.md
packages/plugins/persistent-tasks/.claude-plugin/plugin.json
.claude-plugin/
.claude/CLAUDE.md
.claude/commands/adr.md
.claude/commands/audit.md
.claude/commands/cli.md
... and 6 more
```
