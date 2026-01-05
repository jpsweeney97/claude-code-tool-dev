---
date: 2026-01-05T00:13:50.505569
version: 1
git_commit: 9c8d4be
branch: main
repository: claude-code-tool-dev
tags: ["uv", "sandbox", "debugging"]
---

# Handoff: uv sandbox panic - workaround identified

## Goal
Test promote script workflow for sandbox-to-production deployment

## Key Decisions
- Root cause: Claude Code macOS seatbelt sandbox blocks com.apple.SystemConfiguration.configd mach service → uv panics
- excludedCommands: ["uv"] in settings.json but NOT working (potential Claude Code bug)
- Python urllib works fine (network access OK) - issue is uv Rust code unconditionally calling SystemConfiguration
- Workaround: pyproject.toml + python -m venv + pip install aligns with mise-tool-management standards

## Learnings
- uv commands that work in sandbox: --version, cache dir, pip list (read-only)
- uv commands that panic: python list, pip install, run --script (need network config)
- GitHub issues: astral-sh/uv#16664, astral-sh/uv#16916 - fix is upstream but unreleased
- Codex fixed this in v0.56.0 by updating their sandbox - Claude Code needs similar fix

## Next Steps
1. Try: Start new session with sandbox disabled (/sandbox to toggle off)
2. If still fails: Create pyproject.toml with rich+pyyaml, use python -m venv + pip install workaround
3. Then: Resume test plan execution (Tasks 0-14, 17)
4. Consider: File /bug report about excludedCommands not working

## Uncommitted Files
```
LAUDE.md
docs/plans/2026-01-04-promote-script-test-plan.md
.claude/handoffs/
```
