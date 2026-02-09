> **Status: PARKED** — Codex repo not created. Revisit if Codex extension development begins.

# Codex Tool Dev Repo — Skeleton File List (v1)

This document enumerates the concrete files to create in the new repo `codex-tool-dev` to implement the spec in `docs/plans/codex-tool-dev-repo-spec.md`.

## Root

- `README.md`
- `CHANGELOG.md`
- `package.json` (workspaces for `packages/*`)
- `tsconfig.base.json` (if TypeScript packages exist)
- `.gitignore`

## `.codex/`

- `.codex/rules/skills.md`
- `.codex/rules/agents.md`
- `.codex/rules/automations.md`
- `.codex/rules/mcp-servers.md`
- `.codex/rules/settings.md`
- `.codex/rules/workflow/git.md`
- `.codex/rules/methodology/frameworks.md`
- `.codex/skills/example-skill/SKILL.md`
- `.codex/agents/example-agent.md`
- `.codex/automations/templates/example-automation.toml.tmpl`

## `scripts/` (Python via uv)

- `scripts/validate` (entrypoint)
- `scripts/promote` (entrypoint)
- `scripts/lib/codex_home.py` (resolves `/Users/jp/.codex`, supports override)
- `scripts/lib/manifest.py` (read/write install manifest)
- `scripts/lib/mdlint.py` (skill/agent structure checks)
- `scripts/lib/automation.py` (template rendering + TOML validation)

## `packages/mcp-servers/` (optional in v1)

- `packages/mcp-servers/hello-codex-tools/` (a minimal MCP server)

## `docs/`

- `docs/references/writing-principles.md`
- `docs/frameworks/verification.md`
- `docs/frameworks/debugging.md`
- `docs/frameworks/decision-making.md`

## `tests/`

- `tests/scenarios/skills/example-skill.yaml`
- `tests/scenarios/agents/example-agent.yaml`

