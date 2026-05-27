# CLAUDE.md

## Project Overview

Monorepo for developing Claude Code extensions: skills, commands, agents, hooks, plugins, and MCP servers.

## How This Repo Works

- Develop skills, commands, and agents in `extensions/` (NOT auto-loaded into Claude's context)
- Develop hooks and packages in `.claude/hooks/` and `packages/`
- Promote to `~/.claude/` when ready

`extensions/` lives outside `.claude/` deliberately. Anything under `.claude/skills/`, `.claude/agents/`, or `.claude/commands/` would auto-load into every session in this repo, duplicating the user-level versions and crowding the skill-listing budget. Keeping dev-staged extensions at `extensions/` makes them ordinary editable files until `scripts/promote` deploys them to `~/.claude/`.

## Development Tenet

This repo builds Claude-facing systems (plugins, skills, hooks, agents,
commands, MCP servers, prompts Claude reads at runtime). For these systems,
prefer giving Claude judgment-supporting context over encoding behavior in
rule machinery. Before adding a structured field, status enum, workflow
stage, validation rule, or imperative decision logic to a Claude-facing
system, run four tests:

**Test 1 — Whose failure is it?** If Claude populates this wrong, does the
**work product** (the artifact a non-plugin reader consumes) suffer, or
does **only the plugin's own machinery** (validators, internal pipelines,
audit trails, derived caches) break? A field counts as ontology if Claude
has to know about it *anywhere* — schema, contract, pipeline stage, audit
log, engine interface. "Derive at runtime" only removes a field from the
ontology when the value is computed on demand AND discarded; it does not
help when the value is computed once and passed forward between stages.
"Move to audit logs" does not help when Claude must populate the logs
correctly. Fields whose only consumer is the plugin's pipeline (internal
state classifications, confidence scores between stages, derived hashes
that couple pipeline steps, override flags, version stamps for contract
checking) are over-fit ontology — remove them, demote them to truly
transient runtime values, or acknowledge that they are over-fit and count
them in Test 2.

**Test 2 — Tooling or thinking?** Separate fields that help Claude reason
(small, bounded, content-shaped — the things a human reader of the output
would also reference) from fields that exist for tooling (queries, audits,
downstream automation). Thinking fields stay roughly proportionate to the
concept's complexity; tooling fields multiply without limit if unchecked.
When tooling fields outnumber thinking fields, the artifact has inverted
its purpose: the plugin is the customer, not the work. Apply per-addition
AND on the full set at Test 4's cadence.

**Test 3 — Could Claude do this work inline?** Before writing a script
that classifies, triages, validates with semantic judgment, scores,
decides, or routes within plugin/skill/agent workflows, ask: given the
same context the script will consume, could a thinking Claude produce the
same decision in prose? If yes, the script is replacing judgment with
code. Move the decision back to Claude; keep only the deterministic
mechanics in code (file I/O, schema parsing, persistence, idempotent state
mutations).

*Exempt from Test 3: infrastructure code.* (a) Hooks running synchronously
on every Claude tool invocation; (b) security/policy guards (credential
scanners, destructive-action blockers, branch protection); (c)
deterministic computational machinery (search ranking, indexing, parsing,
encoding, hashing) where the algorithm itself is the value, not the
decision the algorithm produces. The "unacceptable latency / token cost /
fail-open risk" argument applies only *within* (a), (b), or (c) — it is
not a freestanding exemption, and it does not exempt semantic decisions
(classifying, triaging, scoring) even when called at high frequency.
Infrastructure code is justified by stakes and operational constraints
rather than by its decision shape.

Within workflow contexts, imperative code that pre-decides for Claude is
the form of rule machinery that hides best — it passes Tests 1 and 2
because it isn't a field — but it produces exactly the harm the tenet
exists to prevent.

**Test 4 — Re-test the whole artifact, not just additions.** Tests 1-3
fire per-addition. Re-run all three on the full Claude-facing surface
(every field, every script, every line of prose) at any of these triggers,
whichever first:

- **Deterministic floor:** after every ~25 commits touching the artifact's
  directory, or whenever its Claude-facing surface has grown by ~50% since
  last review (numbers are calibration, not a contract).
- **Subjective signal:** when adding the next item makes you hesitate.

The deterministic floor exists because momentum-driven development
suppresses the hesitation signal exactly when re-evaluation is most
needed. Balanced incrementalism — adding one thinking field per tooling
field — passes per-addition checks indefinitely while accumulating into a
heavy ontology; only periodic full-surface re-evaluation catches it.

If the artifact's Claude-facing surface feels disproportionate to the work
it does — compared to lighter plugins in this repo like `handoff` or
`context-metrics` — that is the redesign signal. Responsibility for Test 4
falls on whoever next adds to the artifact; if you can't tell when it last
ran, run it now.

### Illustrative shapes

| Shape | Verdict | Why |
|---|---|---|
| A document artifact with `title`, `body`, `priority`, `tags` | Keep | A non-plugin reader uses each field; passes Test 1 and Test 2 |
| The same artifact also carrying internal pipeline fields (process-stage enum, derived hash persisted across stages, classification-confidence float, contract version stamp, hook-origin marker) | Over-fit | Only the plugin's machinery cares; "derived at runtime" does not save it because the value crosses stages; "in audit logs" does not save it because Claude must populate them |
| A script that classifies user intent into N categories then routes to one of N handlers within a plugin workflow | Over-fit (Test 3) | A thinking Claude given the same input could pick a category in prose; the script is making Claude's decision for it |
| A hook that scans files for credentials and blocks egress | Hard rule, Test 3 exempt | Runs synchronously on every tool call; latency-sensitive; security-critical. Semantically a "classifier" but exempt because infrastructure |
| A hook that blocks edits to protected branches (multi-state state machine + env-var configuration) | Hard rule, justified | Wrong = real branch/data damage; failure lands in the work. Claude's role here is one decision (edit/don't), not navigating a taxonomy |
| A skill that lays out a fixed N-stage workflow Claude must walk in order regardless of situation | Over-fit | Cases needing 1 stage and cases needing N are both forced through N |
| A skill that exposes a checklist Claude consults but isn't forced to walk | Keep | Structure offered as context, not imposed as workflow; Claude decides which items apply |
| A session-state plugin with `session_id`, `timestamp`, `branch`, `summary` persisted to disk | Keep | Fields are content-shaped (a non-plugin reader uses them); the plugin's existence is justified by an otherwise-unsolvable problem (cross-session memory); Test 1 passes because a wrong field = wrong handoff = wrong work |

### Supporting frame

Claude-facing systems support judgment; they do not replace it with rule
machinery. The four tests above are how that stance becomes a filter at
design time. Hard rules remain appropriate where a mistake degrades the
work itself — safety, destructive actions, data integrity, recovery
guarantees, stale state. Everywhere else, prefer giving Claude durable
context, clear boundaries, recoverable state, and structured evidence,
then trust the judgment that follows.

This tenet sits alongside `.claude/rules/methodology/tenets.md` and does
not override it. The methodology tenets are broader: they cover code
design (Deterministic over Heuristic, Explicit over Silent), problem-
solving approach (counteract capability-first thinking), and risk
awareness for irreversible actions. This tenet is narrower: it covers the
design of Claude-facing artifacts in this repo specifically. The two are
mostly compatible — code-design tenets apply to the runtime behavior under
a Claude-facing artifact while this tenet applies to the surface above.
Where they directly conflict, the more specific tenet (this one, for the
Claude-facing surface) governs.

A good implementation makes Claude more capable without making normal work
feel heavy. The tests bind themselves by that constraint: apply them to
the design as a whole, not as a per-keystroke ritual. If running them
takes longer than the artifact deserves, the artifact is probably too
small to need any of them — but Test 4's periodic full-surface check is
the floor, not a ceiling.

## Directory Structure

```
extensions/       # Dev-staging for skills/commands/agents (NOT auto-loaded)
├── skills/       # Skills under development (SKILL.md required)
├── commands/     # Slash commands under development
└── agents/       # Subagents under development

.claude/
├── hooks/        # Hooks (Python scripts, synced to settings.json) — auto-loaded
├── rules/        # Auto-loaded session rules (keep minimal)
├── handoffs/     # Session handoff documents (gitignored)
├── sessions/     # Session notes (gitignored)
└── worktrees/    # Git worktree state (gitignored)

scripts/          # Utility scripts (run with uv run scripts/<name>)

docs/
├── frameworks/   # Methodology frameworks (thoroughness, decision-making, verification)
├── references/   # Skill patterns, guides, style references
├── plans/        # Implementation plans and design documents
├── decisions/    # Architecture Decision Records
├── learnings/    # Codex consultation insights
├── tickets/      # Work tickets
└── audits/       # Quality audits

.claude-plugin/   # Plugin marketplace config (turbo-mode bundle)
```

## Packages

| Package | Path | Language | Purpose |
|---------|------|----------|---------|
| handoff | `packages/plugins/handoff/` | Python | Session state persistence (save/load/search) |
| ticket | `packages/plugins/ticket/` | Python | Repo-local ticket lifecycle management |
| context-metrics | `packages/plugins/context-metrics/` | Python | Context window usage analysis |
| superspec | `packages/plugins/superspec/` | Shell/Markdown | Spec writing system — write, review, modularize specs with shared contract |
| claude-code-docs | `packages/mcp-servers/claude-code-docs/` | TypeScript | BM25-indexed Claude Code doc search |

> **codex-collaboration** was extracted to its own repo at `/Users/jp/Projects/active/codex-collaboration/` on 2026-05-11. The standalone repo is the sole authority. See `packages/plugins/codex-collaboration/MIGRATED.md` for the redirect.

Plugins deploy via `turbo-mode` marketplace. MCP servers and extensions deploy via `uv run scripts/promote`.

## Gotchas

- **Dev vs production**: Edit skills/commands/agents in `extensions/` (this repo), not `~/.claude/` (production). Hooks live in `.claude/hooks/`. Promote when ready via `scripts/promote`.
- **Sync after hook changes**: Run `uv run scripts/sync-settings` after modifying hooks — Claude Code reads from `settings.json`, not hook files directly.
- **Package-local testing**: A uv workspace (`pyproject.toml` at repo root) links all packages. Run tests from anywhere: `uv run --package <name> pytest`, or from the package directory: `cd packages/<path> && uv run pytest`.
- **Rules file size**: `.claude/rules/` files auto-load into every session. Keep them minimal — move reference material to `docs/` and link to it.
- **Hook failure polarity**: PreToolUse hooks are fail-open — unhandled exceptions don't produce exit code 2, so the tool call proceeds. For critical enforcement, catch all errors and return a block decision.
- **MCP tool naming**: Plugin tools use `mcp__plugin_<plugin>_<server>__<tool>`. Must match across hook matchers, skill `allowed-tools`, and agent `tools` frontmatter. `tools` is a hard allowlist (wrong name = unavailable); `allowed-tools` is auto-approval only (wrong name = permission prompts).
- **Hook payload fields**: PostToolUse uses `tool_response` (not `tool_result`); PreToolUse uses `tool_input`. Plugin `.mcp.json` `env` merges with parent environment. `${VAR:-default}` does NOT expand; safest to inherit rather than set.

## Writing Extensions

Applies to instruction documents: skills (`extensions/skills/*/SKILL.md`) and subagents (`extensions/agents/*.md`).

Audience is Claude. Optimize for machine parsing.

Full guidance: `docs/references/writing-principles.md`

- **Prohibit, don't omit**: When Claude should avoid an action, use active prohibitions ("Do NOT set X", "Never use Y") rather than passive language ("omit X for default", "leave X empty"). Passive instructions don't reliably prevent Claude from filling gaps with training knowledge. The stronger the training prior, the more explicit the prohibition must be.
- **Standalone layers**: When instruction documents layer (skill → agent → contract), each layer must be fully operational standalone. Never use "if available, use X; otherwise fall back" — inline the minimal self-contained version. Other sources are additive, not alternative.

## Workflow

### Promoting Extensions

```bash
uv run scripts/promote <type> <name>   # Validate and deploy to ~/.claude/
```

Types: `skill`, `command`, `agent`, `hook`. Plugins use the marketplace instead (see Packages table).

### Scripts

Run with `uv run scripts/<name>`:

| Script | Purpose |
|--------|---------|
| `sync-settings` | Sync hook config to `settings.json` (run after hook changes) |
| `inventory` | List all extensions and packages |
| `migrate` | Extension schema migrations |
| `validate_episode.py` | Validate learning episode format |
