---
module: readme
legacy_sections: []
authority: root
normative: false
status: active
---

# Engram Design Specification

Modular design spec for Engram — a persistence and observability layer for Claude Code.

## Reading Order

| # | Document | What it covers |
|---|----------|---------------|
| 1 | [foundations.md](foundations.md) | System overview, architecture, judgment split |
| 2 | [decisions.md](decisions.md) | Locked design decisions with sources |
| 3 | [contracts/tool-surface.md](contracts/tool-surface.md) | MCP tool table, envelopes, bootstrap, action semantics, public types |
| 4 | [contracts/behavioral-semantics.md](contracts/behavioral-semantics.md) | Observable behavior: merge rules, atomicity, ordering, lifecycle |
| 5 | [internal-architecture.md](internal-architecture.md) | Directory layout, architectural rules, deferred items |
| 6 | [schema/ddl.md](schema/ddl.md) | All DDL (11 tables, 1 FTS5, 3 triggers) |
| 7 | [schema/rationale.md](schema/rationale.md) | Storage rationale: ON DELETE, FTS sync, FK coupling |
| 8 | [contracts/skill-orchestration.md](contracts/skill-orchestration.md) | Two-stage guard, confirmation model, shared contracts, lazy bootstrap |
| 9 | [skills/overview.md](skills/overview.md) | Skill roster and visibility model |
| 10 | [skills/catalog.md](skills/catalog.md) | Per-skill designs (6 skills) |
| 11 | [skills/appendix.md](skills/appendix.md) | Directory layout, allowed-tools naming, open questions |
| 12 | `implementation/*.md` | Hook specs, validation, packaging, migration, testing (stubs) |

## Authority Model

The public API contract is defined by the documents in `contracts/`. Schema documents describe storage implementation and must not change public behavior. Implementation documents describe enforcement mechanics. Changes to observable behavior require updating `contracts/` first.

## Document Conventions

- **Frontmatter:** Every document has YAML frontmatter with `module`, `legacy_sections`, `authority`, `normative`, `status`
- **Anchors:** Semantic kebab-case (e.g., `#anchor-hash-merge`). No section numbers.
- **Cross-references:** Relative markdown links (e.g., `[merge rules](contracts/behavioral-semantics.md#anchor-hash-merge)`)
- **Amendment history:** Tracked in [amendments.md](amendments.md), not inline

## Legacy Section Map

See [legacy-map.md](legacy-map.md) for old section numbers → new file/anchor mapping.
