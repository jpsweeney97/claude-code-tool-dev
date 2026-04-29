# T-20260423-02: Deferred same-turn approval response in delegation runtime

```yaml
id: T-20260423-02
date: 2026-04-23
status: closed
closed_date: 2026-04-29
resolution: completed
resolution_ref: >
  Packet 1 merged via PR #126 (merge commit 36ef13e8).
  Candidate A sandbox policy promotion at ce0579f6.
  Live /delegate smoke artifact at a7a4e9c9.
  T-20260423-01 closed at 6580d86e.
  Carry-forward verification at docs/plans/2026-04-24-packet-1-deferred-approval-response/carry-forward.md.
priority: high
tags: [codex-collaboration, delegation, runtime, control-plane, approval]
blocked_by: []
effort: large
```

## Summary

This ticket tracked the control-plane mechanism that lets
`codex.delegate.decide(...)` respond to an in-flight App Server request
after operator delay. The work shipped as "Packet 1" of the deferred
approval response design.

**Packet 1 implementation landed through Phase H and merged via PR #126
(`36ef13e8`).** The implementation covered all 8 in-scope items from the
original ticket: `start()` lifecycle redesign, background turn
ownership, capture cardinality (park-based single-capture model),
blocking resolution registry, persisted request/job mutation, public
contract updates, timeout alignment, and recovery semantics.

**T-20260423-01 (parent ticket) was subsequently closed** after live
`/delegate` smoke validation produced a real artifact (commit
`a7a4e9c9`) and promotion succeeded end-to-end. The `blocks`
relationship from this ticket to T-01 is fully resolved.

The carry-forward closeout (`carry-forward.md`) records `1040 passed /
0 skipped / 0 failed` with residual debt items (`TT.1`, `RT.1`, minor
polish) tracked separately in the reconciliation register.

## Amendment admission status

The original ticket framing assumed an amendment-admission follow-up
layer (allowlist, classifier, `approve_amendment` verb) would stack on
this ticket's primitives. The diagnostic run record
(`docs/diagnostics/2026-04-28-delegate-execution-diagnostic.md`) later
found that amendment admission is not currently required for the observed
canonical delegation flow: `acceptWithExecpolicyAmendment` was offered
as one of 6 available decisions across all observed approval cycles, but
plain `accept` (mapped from operator `approve`) sufficed throughout.
S7b (response-required) did not fire.

This finding does not preclude future amendment-admission work if
upstream capability triggers change, but it removes the premise that
such work was a required next step after this ticket.

## Provenance

- Parent acceptance-gap ticket: **T-20260423-01**
  (`docs/tickets/closed-tickets/2026-04-23-codex-collaboration-delegate-execution-remediation.md`).
- Design spec: `docs/superpowers/specs/2026-04-23-deferred-approval-response-design.md`.
- Implementation plan: `docs/plans/2026-04-24-packet-1-deferred-approval-response/`.
- Carry-forward: `docs/plans/2026-04-24-packet-1-deferred-approval-response/carry-forward.md`.
- Rejected earlier design spec: commit `edff9c07` on
  `feature/delegate-exec-policy-amendment`. Decisions D1-D6, D9, D11,
  D12 from that spec survive and would apply to any future
  amendment-admission work.
- Scrutiny record: delivered 2026-04-23 against `edff9c07`, verdict
  `Reject`. Seven Required Changes became the brainstorm questions that
  shaped this ticket's scope.
- Split decision: **B-prime** — narrow Packet 1 to deferred same-turn
  approval response; amendment admission deferred (later judged not
  currently required).
