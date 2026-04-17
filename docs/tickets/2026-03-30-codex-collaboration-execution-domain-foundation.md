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

## Pre-Design Reconciliation: Inherited Scope-Transport Question

This packet inherits an unresolved design question from `T-20260330-04`'s v1
plan (`docs/plans/2026-04-13-t04-v1-production-dialogue-scoping-plan.md:80-107`,
specifically item §2.2.3 "Multi-agent scope-transport design"). The dialogue
path resolved its instance of the question by an architecture choice — keeping
gatherers OUTSIDE containment because they are read-only scouts (see
`packages/plugins/codex-collaboration/hooks/hooks.json` matcher and the
"gatherers are not containment subjects" pattern documented in the
2026-04-14 PR-107 merge handoff).

That escape hatch does not generalize to delegation. A delegation job is a
contained execution subject by definition — its own worktree, its own runtime,
its own persisted state, its own approval path. T-05 must therefore answer the
scope-transport question for the delegation case before locking the acceptance
criteria below. The question is narrower than "general multi-agent scope
transport"; delegation handoff is a one-shot parent→child handoff at job
creation, not a coexistence problem among co-resident agents.

### Existing material to reconcile against (read first)

- `docs/superpowers/specs/codex-collaboration/contracts.md:59-73` —
  `DelegationJob` definition. **Note:** no scope field exists on the job
  today. `requested_scope` on `PendingServerRequest` (`:88`) is the shape of
  a mid-job approval ASK, not the initial allowed scope.
- `docs/superpowers/specs/codex-collaboration/promotion-protocol.md` —
  promotion-state contracts that interact with scope mutation post-creation.
- `docs/superpowers/specs/codex-collaboration/recovery-and-journal.md` —
  pending-request semantics and concurrency model.
- `docs/benchmarks/dialogue-supersession/v1/manifest.json:36-43` — the
  dialogue-side `scope_envelope` shape, as a reference point for whether
  delegation should adopt, adapt, or reject it.

### Five questions to answer before locking ACs

**0. Reference reconciliation.** Is the dialogue-side `scope_envelope` shape
adopted as the delegation job's scope descriptor, or is a different shape
required? If different, document why (likely: the envelope is prompt-time
guidance for read-only scouts; jobs need durable state-modeled scope that
survives runtime restarts and feeds approval routing). Decide this BEFORE
answering 1-4, because all four depend on the descriptor's shape.

**1. Scope authority.** What object defines a delegation job's allowed scope?
Candidates:

- Repo-root + path set on `DelegationJob` (requires adding a field to
  `contracts.md:59-73`)
- Explicit envelope passed at `codex.delegate.start`, persisted as job state
- Derivative of the parent collaboration's containment seed (couples job
  scope to caller scope)
- Some other shape

The choice determines whether `contracts.md` needs a spec update as part of
T-05. If `DelegationJob` needs an initial scope field, `contracts.md` and the
persisted job model must change together — they are not independently
revisable.

**2. Scope materialization.** How is the chosen descriptor injected into the
isolated runtime/worktree at job start? This is the core transport step.
Candidates: startup config file in the worktree, runtime-init parameter,
environment variable, hooks-side enforcement, or a combination. Must work
given that the job runs in a separate worktree and must not depend on the
parent session's containment state.

**3. Scope mutation.** Is scope immutable for the lifetime of a job, or can
it widen/narrow through approval-routing decisions? If mutable, what state
transition records the change (a new `DelegationJob` field? audit-log
entries? promotion-state interaction?). If immutable, what happens when a
`PendingServerRequest` with `requested_scope` outside the job's initial
scope arrives — block, escalate, or fail?

**4. Enforcement surface.** What actually enforces the job's scope inside the
execution runtime? Candidates: startup-config restricting allowed paths,
rewritten allowed_roots in the codex CLI invocation, guard hooks inside the
runtime, or another mechanism. Must be enforceable in the isolated worktree
without depending on the parent session's containment substrate.

### What this note is NOT

- Not a re-opening of T-04. T-04's AC-7-direct closeout stands. The
  inherited question is a forward design need, not a retroactive defect.
- Not a contract change in itself. If contracts.md needs an update for
  question 1, that update lands inside T-05's implementation — the note
  only flags that the spec gap exists.
- Not a general multi-agent scope-transport solution. Coexisting-agent
  scope coordination remains out of scope; T-05 only solves the
  parent→child handoff at job creation.

### Gating effect on Acceptance Criteria

The current AC list assumes scope is a solved problem. Once questions 0-4
are answered, the existing ACs may need:

- An additional AC ("delegation jobs receive their allowed scope via
  [chosen mechanism]")
- A modification to the existing approval-routing AC to specify
  scope-mutation handling
- A spec-update note if `contracts.md` needs the new `DelegationJob` field

Do not lock ACs until the design pass closes the five questions above.

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
