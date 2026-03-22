---
module: foundations
status: active
normative: true
authority: foundation
---

# CCDI Foundations

## Problem

Codex has no training knowledge about Claude Code's extension ecosystem — hooks, skills, plugins, agents, MCP servers, slash commands, frontmatter schemas, event types. When consultations involve reviewing or designing Claude Code extensions, Codex gives generic advice because it doesn't understand the APIs or conventions.

## Approach

Automatically detect when a consultation involves Claude Code extensions and inject relevant documentation from the `claude-code-docs` MCP server into the Codex conversation.

Two injection phases:

- **Initial:** A dedicated subagent runs in parallel with existing `/dialogue` context-gatherers, queries `claude-code-docs`, and produces a compact reference injected into the Codex briefing.
- **Mid-dialogue:** The `codex-dialogue` agent detects new extension topics emerging in Codex's responses and injects targeted fact packets before the next turn.

Two modes:

| Mode | Entry point | Classifier | Registry | Mid-turn injection |
|------|------------|------------|----------|--------------------|
| **CCDI-lite** | `/codex` skill | One-shot | No | No |
| **Full CCDI** | `/dialogue` skill → `codex-dialogue` agent | Per-turn | Yes | Yes |

Detection is automatic (no manual flags). Injection is source-separated from repo evidence (`[ccdocs:...]` citations vs `@ path:line`). CCDI is an optional capability layer — consultations proceed without it if `claude-code-docs` is unavailable.

## Design Principles

| Principle | Meaning |
|-----------|---------|
| Detect aggressively, inject conservatively | High-recall classifier, precision-gated packet builder |
| Search wide, inject narrow | Initial subagent retrieves broadly, delivers 2–3 families |
| Auto-generated scaffold, curated overlay | Topic inventory stays current without full manual maintenance |
| Persist semantics, derive performance | Compiled inventory stores meaning; runtime matcher is separate |
| CCDI is premise enrichment, not retargeting | CCDI adds context to the follow-up prompt; it never changes what the agent asks Codex about. Packet content should provide background, not prescriptive directives — repo evidence is always the primary signal for Codex's assessment |
| Scout evidence beats CCDI evidence | When context-injection has a scout candidate at the same boundary, CCDI yields |

Schema evolution constraint (additive-only): the architectural principle is stated here under `architecture_rule` authority; the persistence-schema elaboration (field-level invariants and load-time behavior) lives in [data-model.md#schema-evolution-constraint](data-model.md#schema-evolution-constraint) under `persistence_schema` authority.

## CLI/Agent Separation

All deterministic logic lives in Python (`topic_inventory.py`), exposed as coarse-grained workflow commands. Agents invoke via Bash with file-oriented I/O. Agents provide semantic judgment (e.g., semantic hints) and orchestrate deterministic CLI calls (e.g., target-match invocation); the CLI provides deterministic computation (classification, registry state transitions, packet building). This separation ensures reproducibility — the CLI produces identical output for identical inputs regardless of which agent invokes it.

**Boundary rule:** Agents do NOT hold CCDI state. State lives in the registry file on disk. Agents read CLI stdout and write CLI input files. The prepare/commit protocol ([integration.md#mid-dialogue-phase-per-turn-in-codex-dialogue](integration.md#mid-dialogue-phase-per-turn-in-codex-dialogue)) exists because of this separation — ensuring injection is only registered after delivery. See the protocol's [specification](integration.md#mid-dialogue-phase-per-turn-in-codex-dialogue) for the full prepare/commit sequence.

## Resilience Principle

CCDI failures never block consultations. Every failure path degrades to "consultation proceeds without extension docs" — the current behavior. The system adds value when it works; it is invisible when it doesn't.

**Registry reinit exception:** When the topic registry is corrupted mid-dialogue, CCDI reinitializes an empty registry and continues. This may re-inject topics already sent — an acceptable degradation because premise enrichment is idempotent (duplicate context is low-harm, unlike missing context).

Per-component failure modes are specified in each contract file: [classifier.md](classifier.md#failure-modes), [registry.md](registry.md#failure-modes), [packets.md](packets.md#failure-modes), [integration.md](integration.md#failure-modes), and [data-model.md](data-model.md#failure-modes).

## Topic Hierarchy

Approximate scope of Claude Code extension topics covered by the [compiled topic inventory](data-model.md):

```
hooks                          skills                    plugins
├── hooks.pre_tool_use         ├── skills.skill_md       ├── plugins.manifest
├── hooks.post_tool_use        ├── skills.frontmatter    ├── plugins.structure
├── hooks.stop                 ├── skills.allowed_tools  └── plugins.mcp_integration
├── hooks.subagent_stop        └── skills.context_fork
├── hooks.session_start        agents                    mcp
├── hooks.session_end          ├── agents.subagents      ├── mcp.server_config
├── hooks.permission_request   └── agents.frontmatter    └── mcp.tools
├── hooks.notification         commands                  memory
└── hooks.pre_compact          └── commands.slash        └── memory.claude_md
```

## Scope Boundary

The following components are untouched by CCDI:

| Component | Reason |
|-----------|--------|
| `codex_consult.py` | Transport layer — CCDI operates above transport |
| `codex_shim.py` | MCP interface — not affected |
| Context-injection pipeline (`process_turn`/`execute_scout`) | Repo evidence — separate concern; CCDI yields to scout |
| `codex_guard.py` | Safety hooks — orthogonal |
| `retrieve_learnings.py` | Learning injection — separate concern |
