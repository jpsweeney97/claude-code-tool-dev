# CLAUDE.md

Monorepo for developing Claude Code extensions: skills, commands, agents, hooks, plugins, and MCP servers.

## How This Repo Works

Extensions are developed in `.claude/` and `packages/`, tested locally, then promoted to `~/.claude/` for production use. Important specific guidance lives in `.claude/rules/`.

## Directory Structure

```
.claude/
├── skills/       # Skill definitions (SKILL.md required)
├── hooks/        # Python event hooks
├── commands/     # Slash command definitions
├── agents/       # Subagent definitions
├── rules/        # Methodology and design guidance — READ BEFORE CREATING
├── handoffs/     # Session continuity documents
└── references/   # Framework documentation

packages/
├── plugins/      # Plugin packages (marketplace: tool-dev)
└── mcp-servers/  # TypeScript MCP servers

scripts/          # Utility scripts (inventory, migrate, promote, sync-settings)
docs/             # Reference documentation and plans
```

## Workflow

```
CREATE in .claude/ or packages/  →  TEST locally  →  PROMOTE to ~/.claude/
```

### Creating Extensions

| Extension  | Create in                        | Test with           |
| ---------- | -------------------------------- | ------------------- |
| Skill      | `.claude/skills/<name>/SKILL.md` | `/<name>`           |
| Command    | `.claude/commands/<name>.md`     | `/<name>`           |
| Hook       | `.claude/hooks/<name>.py`        | After sync-settings |
| Agent      | `.claude/agents/<name>.md`       | Task tool           |
| Plugin     | `packages/plugins/<name>/`       | Marketplace install |
| MCP Server | `packages/mcp-servers/<name>/`   | After build         |

### Promoting to Production

```bash
uv run scripts/promote <type> <name>   # Validate and deploy to ~/.claude/
```

### Plugin Development

Plugins use the `tool-dev` marketplace instead of the promote script:

```bash
claude plugin marketplace update tool-dev
claude plugin install <name>@tool-dev
```

## Rules

### Methodology

Quality standards to adhere to across all work lives in `.claude/rules/methodology/`. **Read the relevant rule before starting ANY work**:

- Users/jp/Projects/active/claude-code-tool-dev/.claude/rules/methodology/rigor.md
- Users/jp/Projects/active/claude-code-tool-dev/.claude/rules/methodology/tenets.md
- Users/jp/Projects/active/claude-code-tool-dev/.claude/rules/methodology/frameworks.md

Full frameworks (templates, worked examples, detailed guidance) live in `docs/frameworks/` — the rules file above tells you when to consult them.

#### Thoroughness Framework (Quick Reference)

**Principle:** Thoroughness is iterative, not linear. You discover dimensions as you go.

**The Loop:**
```
DISCOVER → EXPLORE → VERIFY → REFINE → (loop if new dimensions) → EXIT
```

| Stage | Question | Output |
|-------|----------|--------|
| DISCOVER | What should I look for? | Dimensions with P0/P1/P2 priority |
| EXPLORE | Cover each dimension | Filled coverage matrix with evidence |
| VERIFY | Check findings | Verified findings with confidence |
| REFINE | Loop or exit? | Continue if new dimensions or revisions; exit if converged |

**DISCOVER Techniques** — apply ≥3 to find unknown unknowns:

| Technique | Method |
|-----------|--------|
| External taxonomy | Find established framework for domain (STRIDE, OWASP, "-ilities") |
| Perspective multiplication | List 3-5 stakeholders: "What would they notice?" |
| Pre-mortem | "This analysis would be worthless if ___" (5+ completions) |
| Historical mining | Search postmortems/lessons-learned in this domain |
| Boundary perturbation | Key parameters: 10x larger? smaller? zero? sudden change? |
| Temporal expansion | What changes at T+1 week, 3 months, 1 year? |

**Yield%** — convergence signal measuring new/revisionary information per pass:

- *Counts:* New entity, reopened item, revised conclusion, escalated priority
- *Does not count:* Routine completion, adding detail without changing conclusions

| Level | Yield Threshold | Stability Requirement |
|-------|-----------------|----------------------|
| Adequate | <20% | Dimensions stable 1 pass |
| Rigorous | <10% | Dimensions + findings stable 1 pass |
| Exhaustive | <5% | Stable 2 passes + disconfirmation empty |

**Disconfirmation Menu** — apply 1+ (adequate), 2+ (rigorous), 3+ (exhaustive) per P0:

| Technique | Method |
|-----------|--------|
| Counterexample search | Find a case that breaks the current claim |
| Alternative hypothesis | Write strongest competing explanation; test it |
| Adversarial read | Look for reasons evidence could be misleading |
| Negative test | Run check expected to fail if model is wrong |
| Cross-check | Verify via independent method |

### Branch Protection

A hook blocks Edit/Write on `main`, `master`, `develop`. Create a working branch first.

**Exceptions (edits allowed on protected branches):**
- `docs/plans/*.md`, `docs/audits/*.md`
- `CHANGELOG.md`, `README.md`, `settings.json`
- `*/.claude/handoffs/*`, `*/.claude/notes/*`
- Gitignored paths (no commit anyway)

Full details: Users/jp/Projects/active/claude-code-tool-dev/.claude/rules/workflow/git.md

### Extensions

Detailed guidance for each extension type lives in `.claude/rules/extensions/`. **Read the relevant rule before starting work on a new extension**:

| Working on... | Read first                                                                             |
| ------------- | --------------------------------------------------------------------------------------|
| Skills        | Users/jp/Projects/active/claude-code-tool-dev/.claude/rules/extensions/skills.md      |
| Hooks         | Users/jp/Projects/active/claude-code-tool-dev/.claude/rules/extensions/hooks.md       |
| Commands      | Users/jp/Projects/active/claude-code-tool-dev/.claude/rules/extensions/commands.md    |
| Agents        | Users/jp/Projects/active/claude-code-tool-dev/.claude/rules/extensions/agents.md      |
| Plugins       | Users/jp/Projects/active/claude-code-tool-dev/.claude/rules/extensions/plugins.md     |
| MCP Servers   | Users/jp/Projects/active/claude-code-tool-dev/.claude/rules/extensions/mcp-servers.md |
| Settings      | Users/jp/Projects/active/claude-code-tool-dev/.claude/rules/extensions/settings.md    |

### Scripts

Run with `uv run scripts/<name>`: `inventory`, `migrate`, `promote`, `sync-settings`
