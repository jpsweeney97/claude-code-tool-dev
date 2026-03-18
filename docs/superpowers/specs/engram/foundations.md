---
module: foundations
status: active
normative: true
authority: foundation
---

# Foundations

## System Identity

**Engram** is a federated persistence and observability layer for Claude Code. It provides shared identity, indexing, and cross-subsystem coordination for three concerns:

| Subsystem | Concern | Unit | Formerly |
|---|---|---|---|
| **Context** | Session state at boundaries | Snapshot | Handoff plugin |
| **Work** | Task lifecycle and project tracking | Ticket | Ticket plugin |
| **Knowledge** | Durable insights and patterns | Lesson | Learning pipeline |

## Core Invariant

**Engram indexes but does not mutate.** All writes flow through subsystem engines. Engram reads the results.

Each subsystem (Context, Work, Knowledge) remains authoritative for its own records. Engram provides shared identity, indexing, and cross-subsystem coordination — but it never owns domain data.

### Permitted Exceptions

CLAUDE.md is an external sink, not an Engram-managed record. Two operations are permitted on CLAUDE.md:

1. **Content write:** The [/promote](operations.md#promote-knowledge-to-claudemd) Step 2 writes transformed text wrapped in [paired markers](types.md#promotion-markers-in-claudemd). The Knowledge engine owns promotion *state* (via [promote-meta](types.md#promote-meta-promotion-state-record)); the CLAUDE.md edit is a skill-level operation that bypasses the engine write path.

2. **Marker management:** Markers (`<!-- engram:lesson:start/end:<lesson_id> -->`) are locator hints embedded in CLAUDE.md for re-promotion and relocation. They broaden the ownership posture (Engram places content in CLAUDE.md) without shifting authority (promote-meta remains the source of truth). Marker deletion by the user degrades automation (manual reconcile), not system state.

No other skill-level write to a protected or externally-owned path is permitted without an explicit clause in this section.

### Shadow Authority Anti-Pattern

Any feature that makes Engram a second source of truth for data that a subsystem already owns is a design violation.

**Test:** Could a user get a different answer by querying the subsystem directly vs. querying Engram? If yes, the feature violates the core invariant.

## Package Structure

```
packages/plugins/engram/
├── .claude-plugin/
│   └── plugin.json          # Marketplace manifest
├── engram_core/              # Shared library (identity, types, indexing)
│   ├── identity.py           # repo_id, worktree_id resolution
│   ├── types.py              # RecordRef, RecordMeta, contracts
│   ├── reader_protocol.py    # NativeReader protocol definition only
│   └── query.py              # Discovery + query engine
├── skills/                   # User-facing skills (13 total, including engram init)
├── hooks/                    # PreToolUse/PostToolUse/SessionStart hooks
├── scripts/                  # Subsystem engines
│   ├── context/              # Context engine + context_reader.py
│   ├── work/                 # Work engine + work_reader.py
│   └── knowledge/            # Knowledge engine + knowledge_reader.py
└── pyproject.toml
```

`engram_core/` lives inside the plugin, not as a separate package. One plugin install gets everything. Extract later if external consumers emerge.

## Design Principles

Three cross-cutting principles guide implementation decisions across subsystems. These are not invariants (they have no enforcement mechanism) but inform trade-offs.

### Auxiliary State Authority

Recovery manifests (`save_recovery.json`, `migration_report.json`) are operational aids only. Primary records — snapshots, tickets, learnings, chain state files — remain authoritative. Reconciliation metadata ([`promote-meta`](types.md#promote-meta-promotion-state-record)) is authoritative promotion-lifecycle state: its presence/absence gates the [promote state machine](operations.md#promote-knowledge-to-claudemd) (Branch A/B/C).

Manifest failure degrades convenience (retry requires manual `snapshot_ref` lookup) but does not break standalone operations. Use distinct naming for each manifest to prevent shadow-authority confusion.

### Pre/Post-Write Validation Layering

Pre-write or pre-dispatch validation for hard invariants (trust triples, idempotency keys, promotion state machine). Post-write validation for advisory quality checks only ([`engram_quality`](enforcement.md#quality-validation)).

Design rationale for the write/warn layering: see [enforcement boundary constraint](enforcement.md#enforcement-boundary-constraint).

### Chain Integrity at Migration Boundaries

When migrating state from an old system (chain files, staging candidates), classify each artifact's health before copying. Only migrate valid, fresh state. Do not reimport known defects (stale chain files, poisoned references) from the predecessor system. See [chain state migration](delivery.md#step-4-context-cutover) for the classification scheme.
