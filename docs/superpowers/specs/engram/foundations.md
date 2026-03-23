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

CLAUDE.md is an external sink, not an Engram-managed record. The Knowledge engine owns promotion *state* (via [promote-meta](types.md#promote-meta--promotion-state-record)); the CLAUDE.md edit is a skill-level bypass of the engine write path. Two operations are permitted on CLAUDE.md:

1. **Content write:** The [/promote](operations.md#promote-knowledge-to-claudemd) Step 2 writes to CLAUDE.md. See [operations.md §Promote](operations.md#promote-knowledge-to-claudemd) for the full behavioral specification.

2. **Marker management:** Markers (`<!-- engram:lesson:start/end:<lesson_id> -->`) are locator hints for re-promotion and relocation. They broaden the ownership posture (Engram places content in CLAUDE.md) without shifting authority (promote-meta remains the source of truth). Marker deletion by the user degrades automation (manual reconcile), not system state.

No other skill-level write to a protected or externally-owned path is permitted without an explicit clause in this section.

#### Adding New Exceptions

foundations.md (this file) is the authoritative source for enforcement exceptions. A new exception is effective only when present in this section — the [enforcement.md exceptions table](enforcement.md#enforcement-exceptions) then references it. This sequencing ensures foundation authority governs exception creation — foundation is second in the enforcement_mechanism precedence chain (per spec.yaml claim_precedence: `[enforcement, foundation, operations, decisions]`). enforcement.md owns enforcement mechanisms but cannot unilaterally expand the set of exceptions those mechanisms must accommodate.

### Shadow Authority Anti-Pattern

Any feature that makes Engram a second source of truth for data that a subsystem already owns is a design violation.

**IndexEntry corollary:** IndexEntry is discovery-only — no mutation, policy, or lifecycle decisions from IndexEntry alone. Any operation that changes state must open the native file through the subsystem engine. See [IndexEntry contract](storage-and-indexing.md#indexentry).

**Design test:** Could a user get a different answer by querying the subsystem directly vs. querying Engram? If yes, the feature violates the core invariant.

**Runnable tests:** See [delivery.md §Step 0a Required Verification](delivery.md) (VR-0A-1) for structural assertions: NativeReader has no `write()` method, `query.py` contains no filesystem write calls, and cross-reader queries do not modify subsystem directories.

## Package Structure

```
packages/plugins/engram/
├── .claude-plugin/
│   └── plugin.json          # Marketplace manifest
├── engram_core/              # Shared library (identity, types, indexing)
│   ├── identity.py           # repo_id, worktree_id resolution
│   ├── types.py              # RecordRef, RecordMeta, contracts
│   ├── reader_protocol.py    # NativeReader protocol definition only
│   ├── canonical.py          # Deterministic JSON serialization for idempotency keys
│   ├── trust.py             # collect_trust_triple_errors() + validate_origin_match() — shared trust validators
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

Three cross-cutting principles guide implementation decisions across subsystems. The first two are architectural guidelines without automated enforcement — compliance is verified by design review, not runtime checks. The third — the Enforcement Boundary Constraint — is a hard invariant enforced structurally by hook registration.

### Auxiliary State Authority

Recovery manifests (`save_recovery.json`, `migration_report.json`) and chain state files (`chain/<worktree_id>-<session_id>`) are operational aids only. Primary records — snapshots, tickets, learnings — remain authoritative. Chain state files are ephemeral coordination artifacts with 24-hour TTL; their loss degrades `resumed_from` lineage tracking but does not invalidate any primary record. See [chain protocol](skill-surface.md#chain-protocol-session-lineage-tracking) for TTL and cleanup rules. Reconciliation metadata ([`promote-meta`](types.md#promote-meta--promotion-state-record)) is classified as authoritative promotion-lifecycle state (not auxiliary), because its presence/absence controls the [promote state machine](operations.md#promote-knowledge-to-claudemd).

Manifest failure degrades convenience (retry requires manual `snapshot_ref` lookup) but does not break standalone operations. Use distinct naming for each manifest to prevent shadow-authority confusion.

### Pre/Post-Write Validation Layering

Pre-write or pre-dispatch validation for hard invariants (trust triples, idempotency keys, promotion state machine). Post-write validation for advisory quality checks only ([`engram_quality`](enforcement.md#quality-validation)).

#### Enforcement Boundary Constraint (Invariant)

**Invariant:** PostToolUse hooks **must not** become enforcement boundaries. The race between write completion and validation readback is acceptable for warnings, not for trust authorization. This is why `engram_quality` uses **Warn** (not Block) as its failure mode. This constraint applies to all current and future PostToolUse hooks in the Engram system.

### Chain Integrity at Migration Boundaries

When migrating state from an old system (chain files, staging candidates), classify each artifact's health before copying. Only migrate valid, fresh state. Do not reimport known defects (stale chain files, poisoned references) from the predecessor system. See [chain state migration](delivery.md#step-4-context-cutover) for the classification scheme.
