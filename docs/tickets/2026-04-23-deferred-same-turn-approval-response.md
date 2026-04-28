# T-20260423-02: Deferred same-turn approval response in delegation runtime

```yaml
id: T-20260423-02
date: 2026-04-23
status: open
priority: high
tags: [codex-collaboration, delegation, runtime, control-plane, approval]
blocked_by: []
blocks: [T-20260423-01]
effort: large
```

## Context

This ticket carves off a control-plane rewrite from T-20260423-01's AC1.
The parent ticket's end-to-end delegation AC is blocked by the plugin's
current inability to send an approval response back through an in-flight
App Server request after operator delay. The existing call path is
synchronous: `_execute_live_turn` returns only after the turn ends, and
`DelegationEscalation` is constructed only inside `_finalize_turn`. Any
operator decision flow that requires the App Server turn to stay live
while `codex.delegate.decide(...)` is awaited does not compose with this
shape.

An earlier attempt to solve this bundled a control-plane rewrite with
amendment-admission logic (allowlist, classifier, `approve_amendment`
verb, audit record) into a single spec on
`feature/delegate-exec-policy-amendment` at commit `edff9c07`. Design
review rejected that spec: the "transport prerequisite" named in the
document was in fact the bulk of the work, not a precondition, and the
spec never owned its design. The rejected artifact remains on that
branch as record.

This ticket separates concerns cleanly:

- **T-20260423-02 (this ticket):** control-plane mechanism that lets
  `codex.delegate.decide(...)` respond to an in-flight App Server
  request after operator delay. Narrow to the specific lifecycle
  required.
- **Amendment admission layer (follow-up ticket):** allowlist +
  classifier + `approve_amendment` verb + amendment-specific audit.
  Stacks on top of T-20260423-02's primitives.

T-20260423-02 does not resolve T-20260423-01 on its own; it unblocks the
amendment-admission follow-up that does.

## Scope

**In scope:**

1. `codex.delegate.start` lifecycle — return semantics while the
   original turn is live.
2. Background / live-turn ownership — who drives the App Server JSON-RPC
   loop after `start()` returns.
3. Capture cardinality model — single-capture-per-turn vs multi-capture,
   and what the stored request identity means when the turn resumes.
4. Blocking resolution registry — how `decide()` signals the handler
   that is parked inside the turn loop.
5. Persisted request / job mutation model — new fields, mutation API,
   cold-start reconciliation for blocked paths.
6. Public contract updates — MCP tool schema, `contracts.md`, model
   enums for any new decision verbs or rejection surfaces introduced.
7. Timeout alignment — operator window ≤ transport budget ≤ runtime
   notification timeout, with explicit coordination.
8. Recovery semantics for blocked approval paths.

**Out of scope:**

- Exec-policy amendment admission (separate follow-up ticket).
- Allowlist / eligibility logic.
- Generic "deferred-decision framework." Amendments are the only
  consumer for v1; reusability is incidental, not a design driver.

## Design-phase brainstorm questions

The fresh-session brainstorm starts with these seven questions. Each
exposes a call-path or data-model gap that the current codebase does
not cover. Line-number evidence is included so the brainstorm is
grounded in verified repo state.

1. **How does `start()` return an operator-visible escalation while the
   original App Server turn stays live?**
   Current behavior: `_execute_live_turn` returns only after the turn
   ends, via `_finalize_turn` — which is the single construction site
   for `DelegationEscalation`.
   Evidence: `delegation_controller.py:618-624` (synchronous return);
   `delegation_controller.py:1504-1510` (`DelegationEscalation`
   construction post-turn).

2. **What replaces the single `captured_request` model?**
   Current behavior: `captured_request` is singular, set only when
   `None`. An amended turn that resumes and emits a second approval
   would overwrite or drop the second capture.
   Evidence: `delegation_controller.py:639` (declaration);
   `delegation_controller.py:685-687, 702-704, 714-716` (three
   is-None-guarded set-sites).

3. **What persisted state records blocked-request disposition, and how
   is that state mutated after capture?**
   Current `PendingRequestStore` API supports `create / get / list_* /
   update_status` only — no generic `update`. Any new fields
   (handler_disposition, resolution_result, etc.) need a designed
   mutation path.
   Evidence: `pending_request_store.py:29-69`.

4. **How do `poll()` and `decide()` synchronize with background turn
   execution?**
   Current `McpServer` is synchronous / serialized; stores and journal
   are lockless appenders. Background turn execution plus live
   `decide()` introduces multi-threaded store mutation into components
   never designed for it.
   Evidence: `mcp_server.py:191` (serial dispatch);
   `pending_request_store.py:71-75`, `delegation_job_store.py:133-140`,
   `journal.py:301-307` (lockless appenders).

5. **What exact MCP tool schema / `contracts.md` / model enum changes
   are required?**
   Any new decision verb, rejection reason, or caller-visible
   `available_decisions` shape needs to own its contract update. The
   rejected spec claimed "no external shape changes" while introducing
   new verbs — that inconsistency must not recur.
   Evidence: `models.py:34-47, 420-437` (`DecisionAction`, rejection
   enum); `contracts.md:297-310` (current decide contract).

6. **What outcome can the runtime honestly observe after sending a
   deferred response?**
   Current `JsonRpcClient.respond()` is fire-and-forget stdin write
   with no ack channel. The runtime notification loop does not
   distinguish "App Server accepted our response" from "App Server
   ignored it." The audit / observability design must be honest about
   what is observable.
   Evidence: `jsonrpc_client.py:106-130` (respond implementation);
   `runtime.py:243-249` (loop continues after respond with no ack).

7. **What timeout budget matches the real transport limits?**
   Current transport `request_timeout` and notification-loop timeout
   are both 1200s. Any operator-response budget must be ≤ the transport
   budget or the transport will time out before the operator window
   closes.
   Evidence: `runtime.py:49` (session request_timeout default 1200s);
   `runtime.py:233` (notification loop timeout 1200s);
   `jsonrpc_client.py:163-170` (client default resolution).

## Acceptance criteria

- [ ] Design spec produced on `feature/delegate-deferred-approval-response`
      covering all 8 in-scope items.
- [ ] Spec explicitly owns the `start()` call-path redesign, not just
      names it as a prerequisite.
- [ ] Spec specifies the capture cardinality invariant (either preserves
      single-capture with hard proof that amended turns cannot emit a
      second approval, or replaces the model).
- [ ] Spec specifies the exact `PendingRequestStore` and
      `DelegationJobStore` API extensions required for new state.
- [ ] Spec names every public contract change (MCP tool schema,
      `contracts.md`, model literals) and owns the update set.
- [ ] Spec aligns timeouts so operator window ≤ transport budget, and
      names the transition atomicity rules for
      `needs_escalation → running` under operator approval.
- [ ] Spec defines recovery semantics for jobs caught in blocked
      approval paths at cold start (either reuses existing `unknown`
      mapping with explicit rationale, or defines a new recovery
      contract).
- [ ] Spec defines the runtime-observable outcome taxonomy for deferred
      responses — what the plugin can honestly record vs what it cannot.
- [ ] Implementation plan follows in a separate phase; this ticket
      closes on spec approval.

## Non-goals for this ticket

- Implementation. Plan + code land under a separate phase / ticket
  after spec approval.
- Amendment-specific logic. Admission layer lives in the follow-up
  ticket.
- Revisiting decisions D1–D6, D9, D11, D12 from the rejected spec.
  Those survive the split and apply to the admission-layer ticket,
  not here.

## Provenance

- Parent acceptance-gap ticket: **T-20260423-01**
  (`docs/tickets/2026-04-23-codex-collaboration-delegate-execution-remediation.md`).
- Rejected design spec: commit `edff9c07` on
  `feature/delegate-exec-policy-amendment`. Do not resurrect; cite only
  for decisions D1–D6, D9, D11, D12 that survive the split.
- Scrutiny record: delivered 2026-04-23 against `edff9c07`, verdict
  `Reject`. Seven Required Changes became the seven brainstorm
  questions above.
- Split decision: **B-prime** — narrow Packet 1 to deferred same-turn
  approval response; follow-up ticket covers amendment admission.
