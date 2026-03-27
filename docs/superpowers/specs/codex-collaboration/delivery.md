---
module: delivery
status: active
normative: true
authority: delivery
---

# Delivery

Implementation plan, compatibility policy, build sequence, and test strategy.

## Implementation Language

**Python** for the Claude-side control plane.

Rationale:

- Matches the repo's existing plugin and test conventions.
- The existing hook ecosystem is Python-heavy.
- stdio JSON-RPC, process supervision, and worktree orchestration are straightforward in `asyncio`.
- The external Codex runtime remains the supported Rust implementation from the Codex CLI.

## Plugin Component Structure

Plugin ID: `codex-collaboration`

```text
packages/plugins/codex-collaboration/
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   ├── consult-codex/
│   │   └── SKILL.md
│   ├── dialogue-codex/
│   │   └── SKILL.md
│   ├── delegate-codex/
│   │   └── SKILL.md
│   └── codex-status/
│       └── SKILL.md
├── hooks/
│   └── hooks.json
├── .mcp.json
├── scripts/
│   ├── codex_guard.py
│   └── codex_runtime_bootstrap.py
├── server/
│   ├── __init__.py
│   ├── mcp_server.py
│   ├── control_plane.py
│   ├── runtime_supervisor.py
│   ├── jsonrpc_client.py
│   ├── approval_router.py
│   ├── worktree_manager.py
│   ├── lineage_store.py
│   ├── prompt_builder.py
│   └── artifact_store.py
├── references/
│   ├── sources.md
│   └── prompts/
│       ├── consult.md
│       ├── dialogue.md
│       ├── delegation.md
│       └── review.md
└── tests/
```

## Compatibility Policy

### Version Pinning

Pin a minimum Codex CLI / App Server version. Vendor the generated schema for that version into tests.

### Startup Checks

All checks must pass before the plugin accepts requests. Failure is fail-closed.

| Check | Failure Behavior |
|---|---|
| `codex` binary present | Plugin refuses to start |
| Auth available | Plugin refuses to start |
| App Server initialize handshake succeeds | Plugin refuses to start |
| Required stable methods present | Plugin refuses to start |

### Excluded Dependencies

The following are not used for core functionality in v1:

| Feature | Reason |
|---|---|
| WebSocket transport | Experimental |
| Dynamic tools | Experimental |
| `plugin/list`, `plugin/read`, `plugin/install`, `plugin/uninstall` | Not needed for core flows |
| Other experimental APIs | Stability not guaranteed |

## Recommended Build Sequence

Build the smallest slice that proves the architecture without recreating the old plugin.

| Step | Component | Dependencies |
|---|---|---|
| 1 | `codex.status` | App Server connection, auth, version check |
| 2 | `codex.consult` | Advisory runtime, prompt builder, thread lifecycle |
| 3 | Lineage store | Persistent collaboration handle tracking |
| 4 | `codex.dialogue.start` + `.reply` + `.read` | Advisory runtime, lineage store, thread management |
| 5 | Hook guard | Secret scanning, path validation, policy checks |
| 6 | `codex.delegate.start` | Execution runtime, worktree manager, isolation |
| 7 | `codex.delegate.poll` + `.decide` + `.promote` | [Promotion protocol](promotion-protocol.md), [operation journal](recovery-and-journal.md#operation-journal) |

### Not in First Slice

- Analytics
- Codex-side plugin discovery
- Generalized policy editing
- Multi-job concurrency (beyond max-1)
- Three-way merge in promotion

## Test Strategy

### Unit Tests

- Control plane routing logic
- Policy fingerprint computation and comparison
- Idempotency key generation and deduplication
- Promotion precondition checks
- Promotion state machine transitions
- Typed response shape construction

### Integration Tests

- Full consultation flow through advisory runtime
- Dialogue with fork and read
- Delegation with worktree isolation
- Promotion with all preconditions verified
- Crash recovery from journal replay
- Advisory runtime rotation on privilege widening

### Contract Tests

- Vendor the pinned App Server schema
- Verify startup handshake against the pinned version
- Test behavior with unknown/unsupported server request kinds
- Verify typed rejection responses match [contracts.md](contracts.md#typed-response-shapes) shapes
