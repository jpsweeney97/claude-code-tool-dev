# Cross-Model Plugin Migration Design

**Status:** Design discussion. Not yet planned or scoped.

**Origin:** PR #13 review session (2026-02-18). During discussion of remaining Codex-related files in the repo, decided the target is a single `cross-model` plugin bundling all three systems.

**Decision:** Single cross-model plugin is the target architecture. Confirmed by user during step 3 of the PR #13 review.

---

## Current State

Three systems, packaged differently:

| System | Location | Package Type | Status |
|--------|----------|-------------|--------|
| Codex Integration | `packages/plugins/codex/` | Plugin (v0.1, merged) | Deployed |
| Context Injection | `packages/context-injection/` | Standalone Python MCP server | Deployed (repo-level only) |
| Cross-Model Learning | `docs/plans/2026-02-10-cross-model-learning-system.md` | Spec only | Not started |

### Dependency Chain

```
Cross-Model Learning (not yet built)
        ↓ depends on
Context Injection (repo-level MCP, 969 tests)
        ↓ depends on
Codex Integration (plugin MCP)
```

### Current File Duplication

After PR #13, these files exist in both project and plugin locations:

| Project-level | Plugin-bundled | Relationship |
|---------------|----------------|-------------|
| `.claude/agents/codex-dialogue.md` | `packages/plugins/codex/agents/codex-dialogue.md` | Divergent (contract paths, Setup section) |
| `.claude/agents/codex-reviewer.md` | (none) | Project-only, no plugin counterpart |
| `docs/references/consultation-contract.md` | `packages/plugins/codex/references/consultation-contract.md` | Nearly identical (1 path diff) |
| `docs/references/consultation-profiles.yaml` | `packages/plugins/codex/references/consultation-profiles.yaml` | Nearly identical (1 path diff) |
| `.claude/hooks/nudge-codex-consultation.py` | (none) | Project-only, needs Q2 guardrails |

The project-level codex skill was removed in PR #13 (plugin skill is canonical).

### The Problem

The codex-dialogue agent straddles two systems:
- **Codex tools:** `mcp__plugin_codex_codex__codex` (plugin-provided)
- **Context injection tools:** `mcp__context-injection__process_turn`, `mcp__context-injection__execute_scout` (repo-level)

External users who install `codex@cross-model` get the agent but NOT context injection. The agent falls back to `manual_legacy` mode (no scouting, no server-side convergence detection, no evidence gathering). This is a degraded experience.

Project-level agents have priority 2 (higher than plugin priority 4), so within this repo the project copies shadow the plugin copies. The project copies use repo-relative contract paths and repo-level context-injection tool names — both correct for this repo's context.

---

## Target Architecture

A single `cross-model` plugin that bundles all three systems.

### Directory Structure

```
packages/plugins/cross-model/
├── .claude-plugin/plugin.json       # name: cross-model
├── .mcp.json                        # codex + context-injection servers
├── skills/
│   └── codex/SKILL.md               # consultation skill
├── agents/
│   ├── codex-dialogue.md            # multi-turn dialogue
│   └── codex-reviewer.md            # single-turn code review
├── hooks/hooks.json                 # credential guard + nudge (opt-in gated)
├── scripts/
│   └── codex_guard.py               # enforcement hook
├── references/
│   ├── consultation-contract.md
│   └── consultation-profiles.yaml
├── context-injection/               # bundled MCP server (Python package)
│   ├── context_injection/           # the actual Python package
│   ├── pyproject.toml
│   └── ...
├── learnings/                       # future: cross-model learning
├── README.md
└── CHANGELOG.md
```

### What Changes

| Aspect | Current (`codex` plugin) | Target (`cross-model` plugin) |
|--------|-------------------------|-------------------------------|
| Plugin name | `codex` | `cross-model` |
| MCP servers | codex only | codex + context-injection |
| Context injection tools | repo-level (`mcp__context-injection__*`) | plugin-namespaced (`mcp__plugin_cross-model_context-injection__*`) |
| Agents | codex-dialogue only | codex-dialogue + codex-reviewer |
| Hooks | credential guard only | credential guard + nudge (opt-in gated) |
| Manual legacy fallback | needed for external users | not needed (context injection bundled) |
| Install command | `claude plugin install codex@cross-model` | `claude plugin install cross-model@cross-model` |

### After Migration: Project-Level Cleanup

Once the single plugin bundles everything, project-level copies can be removed:

| File | Action |
|------|--------|
| `.claude/agents/codex-dialogue.md` | Remove (plugin agent is canonical, context injection is now plugin-provided) |
| `.claude/agents/codex-reviewer.md` | Remove (bundled in plugin) |
| `.claude/hooks/nudge-codex-consultation.py` | Remove (bundled in plugin with opt-in gate) |
| `docs/references/consultation-contract.md` | Keep as canonical source (plugin bundles derivative copy) |
| `docs/references/consultation-profiles.yaml` | Keep as canonical source |
| `scripts/validate_consultation_contract.py` | Keep (validates canonical source) |
| `tests/test_consultation_contract_sync.py` | Keep (13 tests, validates contract integrity) |

---

## Known Challenges

### 1. Bundling the Context Injection MCP Server

Context injection is a full Python package (`packages/context-injection/`, 969 tests, own `pyproject.toml` and venv). The plugin `.mcp.json` would register it as a `stdio` server:

```json
{
  "mcpServers": {
    "codex": { ... },
    "context-injection": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "--directory", "${CLAUDE_PLUGIN_ROOT}/context-injection", "python", "-m", "context_injection"],
      "env": {}
    }
  }
}
```

**Open question:** Does `${CLAUDE_PLUGIN_ROOT}` expand in plugin `.mcp.json`? It works in `hooks.json` (confirmed: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/codex_guard.py`). If not, needs a wrapper script or absolute path workaround.

**Open question:** Can `uv run --directory` resolve the package from the plugin cache directory? The installed plugin lives at `~/.claude/plugins/cache/cross-model/cross-model/<version>/`. The `uv run` command needs to find the Python package and its dependencies there.

### 2. Tool Name Cascade

When context injection becomes plugin-provided, every reference to its tools changes:

| Current (repo-level) | Target (plugin-namespaced) |
|---|---|
| `mcp__context-injection__process_turn` | `mcp__plugin_cross-model_context-injection__process_turn` |
| `mcp__context-injection__execute_scout` | `mcp__plugin_cross-model_context-injection__execute_scout` |

Affected files: agent `tools` frontmatter, agent body text (many references), context injection contract (`docs/references/context-injection-contract.md`).

### 3. Nudge Hook Q2 Guardrails

The nudge hook (`nudge-codex-consultation.py`) fires on PostToolUseFailure to suggest Codex consultation after repeated failures. Before bundling in a user-scoped plugin:

1. MCP-availability guard — only nudge if Codex MCP is actually available
2. Explicit opt-in gate — user-scope plugins affect all projects; nudging should be opt-in
3. Clean-machine smoke test — verify behavior when Codex CLI is not installed

These guardrails were scoped out of v0.1 (Q2 consultation finding from the adversarial Codex dialogue).

### 4. Plugin Rename

Renaming from `codex` to `cross-model` means:
- New `plugin.json` with `name: cross-model`
- Marketplace entry updated (`.claude-plugin/marketplace.json`)
- All `mcp__plugin_codex_codex__*` tool names change to `mcp__plugin_cross-model_codex__*`
- Another tool name cascade across all files
- Users need to uninstall old plugin and install new one

### 5. Context Injection Test Infrastructure

The context injection package has 969 tests that run from `packages/context-injection/`. After bundling into the plugin, the test infrastructure needs to work from the new location. Options:
- Keep tests at `packages/context-injection/` and reference the source
- Move tests into the plugin directory
- Symlink or import path configuration

---

## Open Design Questions (For Next Session)

1. **Plugin naming for MCP tools:** When the plugin is named `cross-model`, the codex MCP tools become `mcp__plugin_cross-model_codex__codex`. Is this the right granularity, or should the plugin name be shorter?

2. **Source vs. distribution:** Should `docs/references/` remain the canonical source for contract/profiles, with the plugin bundling derivative copies? Or should the plugin become the single source of truth?

3. **Build step:** Should there be a build/sync script that generates plugin content from canonical sources (similar to `scripts/promote`)? This would automate path transformations and copy management.

4. **Context injection packaging:** Should the Python package be vendored (copy source into plugin), or should the plugin reference it as a dependency? Vendoring is simpler but creates maintenance burden. Dependency reference is cleaner but requires `uv` to resolve packages from the plugin cache.

5. **Phasing:** Should context injection bundling happen before or after cross-model learning Phase 0? Phase 0 is the current top priority (`/learn` command + learnings file).

6. **Backwards compatibility:** When renaming from `codex` to `cross-model`, is there a migration path for existing users? Or is the user base (1 person) small enough that a clean break is fine?

---

## References

| What | Where |
|------|-------|
| Codex plugin (v0.1, merged) | `packages/plugins/codex/` |
| Context injection MCP server | `packages/context-injection/` |
| Context injection design spec | `docs/plans/2026-02-11-conversation-aware-context-injection.md` |
| Context injection contract | `docs/references/context-injection-contract.md` |
| Cross-model learning spec | `docs/plans/2026-02-10-cross-model-learning-system.md` |
| Codex plugin design doc | `docs/plans/2026-02-18-codex-plugin-design.md` |
| PR #13 (codex plugin) | `https://github.com/jpsweeney97/claude-code-tool-dev/pull/13` |
| Modularization proposal | `~/.claude/handoffs/claude-code-tool-dev/2026-02-17_16-44_spec-modularization-proposal-codex-reviewed.md` |
