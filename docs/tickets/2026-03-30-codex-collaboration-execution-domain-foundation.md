# T-20260330-05: Codex-collaboration execution-domain foundation

```yaml
id: T-20260330-05
date: 2026-03-30
status: open
priority: high
tags: [codex-collaboration, delegation, execution-runtime, worktree, supersession]
blocked_by: [T-20260330-03]
blocks: [T-20260330-06]
effort: large
```

## Context

Dialogue is the adoption gate. The execution domain is the completion gate.
Full spec completion and full cross-model supersession both depend on building
the execution-side infrastructure that the current package still lacks:

- isolated worktrees
- execution runtime lifecycle
- delegation job state
- approval routing
- job busy enforcement

This ticket isolates that infrastructure from the later product-facing
promotion and `/delegate` UX work.

## Problem

The normative contracts already define `DelegationJob`, `PendingServerRequest`,
and the delegate tool surface, but the current server still exposes only the
advisory tools. If execution-domain infrastructure is mixed directly into the
final `/delegate` product packet, the hard state-management problems stay
hidden until too late.

## Scope

**In scope:**

- Add execution runtime bootstrap and lifecycle supervision
- Add isolated git worktree creation and cleanup
- Add delegation job persistence and runtime/job identity mapping
- Add approval or escalation routing for execution-domain server requests
- Add `codex.delegate.start`
- Add max-1 concurrent delegation enforcement with the typed `Job Busy`
  response shape
- Add any artifact-store primitives needed to support later promotion work
- Add tests for worktree isolation, job creation, restart boundaries, and busy
  rejection

**Explicitly out of scope:**

- `codex.delegate.poll`
- `codex.delegate.decide`
- `codex.delegate.promote`
- Artifact hash verification
- Rollback
- `/delegate` skill UX
- Cross-model cutover

## Acceptance Criteria

- [ ] The codex-collaboration server can start an isolated execution runtime for
      a delegation job
- [ ] Each delegation job owns exactly one worktree and one execution runtime
- [ ] Job state is persisted strongly enough for the later promotion flow to
      inspect it
- [ ] The control plane rejects a second concurrent delegation with the typed
      `Job Busy` response
- [ ] Execution-domain server requests are surfaced through an approval-routing
      layer rather than being silently auto-approved
- [ ] Tests cover worktree creation, busy rejection, and execution runtime
      lifecycle boundaries

## Verification

- Start a delegation job and confirm it creates an isolated worktree from the
  expected base commit
- Attempt a second concurrent delegation and confirm the typed busy response
- Inspect persisted job state and runtime mapping after job creation
- Run the execution-domain unit and integration tests added in this packet

## Dependencies

This ticket depends on the shared substrate from `T-20260330-03`. It can run in
parallel with `T-20260330-04` once that substrate is stable. It must land
before `T-20260330-06`.

## References

| Resource | Location | Purpose |
|----------|----------|---------|
| Delegation data model | `docs/superpowers/specs/codex-collaboration/contracts.md` | Normative state shape |
| Promotion protocol | `docs/superpowers/specs/codex-collaboration/promotion-protocol.md` | Follow-on dependency |
| Recovery and journal | `docs/superpowers/specs/codex-collaboration/recovery-and-journal.md` | Concurrency and pending-request semantics |
| Delivery step 6 | `docs/superpowers/specs/codex-collaboration/delivery.md` | Normative staging target |
