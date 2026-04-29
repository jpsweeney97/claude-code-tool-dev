# Codex-Collaboration Reconciliation Register

Last reconciled: 2026-04-29

## Authority

This register is the working index of still-open, still-deferred, or
still-unreconciled `codex-collaboration` work in this repo.

Authority boundary:

- This file summarizes current-state classification, priority, and next-action
  labeling for work that already has source evidence elsewhere in the repo.
- Linked tickets, plans, diagnostics, and specs remain authoritative for
  acceptance criteria, evidence, and behavioral design.
- If a linked artifact's status language drifts from newer repo evidence, this
  register may record that drift only when the row makes the newer source of
  truth explicit. If the register and source artifacts disagree without that
  evidence trail, treat the row as needing reconciliation rather than as a
  tie-breaker.

Scope included here:

- Open ticket-owned work
- Residual carry-forward debt
- Benchmark closeout follow-on work that remains intentionally unresolved
- Spec and documentation reconciliation debt
- Intentional future-scope deferrals that are still active design surfaces
- Active supporting artifacts whose open/closed design state no longer matches
  current decisions

## State Vocabulary

| State | Meaning |
|---|---|
| `blocking` | Blocks the next important operational gate |
| `open` | Real work item remains unresolved |
| `drift` | The underlying implementation or closure state changed, but the owning artifact still says the old thing |
| `missing-artifact` | Work exists conceptually, but the durable tracker is missing |
| `deferred` | Intentionally out of the current slice, but still a live future-scope surface |

## Current Priority Order

1. Reconcile stale authority artifacts created by the landed Candidate A and
   Packet 1 work.
2. Rewrite `T-20260423-02` to current truth and remove the superseded
   amendment-admission follow-up premise unless new evidence reopens it.
3. Sweep residual typing and minor Packet 1 carry-forward debt.

## Ticket-Owned Active Work

| ID | State | Owning artifact | Current truth | Exit condition |
|---|---|---|---|---|
| `T-20260423-02` | `drift` | `docs/tickets/2026-04-23-deferred-same-turn-approval-response.md`, `docs/plans/2026-04-24-packet-1-deferred-approval-response/carry-forward.md`, and `docs/diagnostics/2026-04-28-delegate-execution-diagnostic.md` | Packet 1 implementation landed through Phase H. The carry-forward closeout records `1040 passed / 0 skipped / 0 failed` and leaves residual debt such as `TT.1`, `RT.1`, and minor polish items. The later live diagnostic also records that amendment admission is not currently required for the observed canonical flow, so the ticket's follow-up-ticket premise is no longer current truth. | Rewrite the ticket to current truth, then either close it or retarget it explicitly to residual debt that still survives the post-diagnostic evidence. |
| `T-20260416-01` | `open` | `docs/tickets/2026-04-16-codex-collaboration-dialogue-reply-extraction-mismatch.md` plus `docs/tickets/closed-tickets/2026-03-30-codex-collaboration-dialogue-parity-and-scouting-retirement.md` | The reply-path extraction mismatch remains a live product defect. The parent benchmark closeout no longer blocks the fix, but the ticket body still says to wait until the benchmark track completes. | Land the extraction fix with tests and one-run verification, then update the ticket body and close it. |

## Residual Carry-Forward Debt

| ID | State | Owning artifact | Current truth | Exit condition |
|---|---|---|---|---|
| `TT.1` | `open` | `docs/plans/2026-04-24-packet-1-deferred-approval-response/carry-forward.md` | Pre-existing Pyright issues around `_FakeControlPlane` typing remain open after Packet 1 closeout. | Resolve the test-fake typing mismatches or explicitly accept them in a narrower typing policy. |
| `RT.1` | `open` | `docs/plans/2026-04-24-packet-1-deferred-approval-response/carry-forward.md` | Pre-existing Pyright `TurnStatus` literal narrowing issue in `runtime.py` remains open after Packet 1 closeout. | Fix the narrowing issue or explicitly document a durable rationale for leaving it unresolved. |
| `P1-MINOR-SWEEP` | `open` | `docs/plans/2026-04-24-packet-1-deferred-approval-response/carry-forward.md` | Fourteen non-blocking carry-forward items remain open: `A4`, `A5`, `B6.1`, `B6.2`, `B7.1`, `B7.2`, `B8.1`, `B8.2`, `C10.2`, `C10.3`, `E13.1`, `E13.2`, `E13.3`, `E14.1`. These are test-parity, style, docstring, and declarative-cleanup items rather than correctness blockers. | Sweep or disposition the items individually in the carry-forward tracker. |

## Benchmark-Carried Follow-On Work

| ID | State | Owning artifact | Current truth | Exit condition |
|---|---|---|---|---|
| `BMARK-L1-L3` | `open` | `docs/tickets/closed-tickets/2026-03-30-codex-collaboration-dialogue-parity-and-scouting-retirement.md` | The benchmark closeout preserved three candidate mechanism losses as future work rather than closure blockers: `L1` scout integrity, `L2` plateau / budget control, and `L3` per-scout redaction of raw host-tool output. These are not yet decomposed into standalone backlog artifacts. | Convert the three caveats into explicit follow-up tickets / packets, or explicitly decline them as non-goals. |

## Spec And Documentation Reconciliation Debt

| ID | State | Owning artifact | Current truth | Exit condition |
|---|---|---|---|---|
| `DELIVERY-ROLLOUT-PROFILE` | `drift` | `docs/superpowers/specs/codex-collaboration/delivery.md` | The `R1/R2 Deployment Profile` block still says the implemented surface ends at `codex.status`, `codex.consult`, and `codex.dialogue.*`, and still assumes no delegation / promotion path. That block no longer matches the implemented repo surface. | Rewrite the rollout-profile block so it reflects the current implemented surfaces and remaining boundaries. |
| `T01-DIAGNOSTIC-HEADER` | `drift` | `docs/diagnostics/2026-04-28-delegate-execution-diagnostic.md` | The run record header still says the engineering action is pending even though Candidate A policy promotion has already landed. The rest of the branch history treats the patch as implemented and pushed. | Reconcile the header language to the landed state or explicitly mark the line as historical context. |
| `T16-BLOCKER-MODEL` | `drift` | `docs/tickets/2026-04-16-codex-collaboration-dialogue-reply-extraction-mismatch.md` | The ticket's post-benchmark section still says to defer work until the benchmark track completes, but the parent benchmark ticket has already closed and explicitly preserves this defect as live follow-up work. | Update the ticket body so the blocker model matches current repo state. |
| `REWRITE-MAP-CONSULT-QUESTION` | `drift` | `docs/superpowers/specs/codex-collaboration/official-plugin-rewrite-map.md` plus `docs/superpowers/specs/codex-collaboration/decisions.md` | The active supporting rewrite map still says to keep an open question about retiring `codex.consult`, but `decisions.md` resolves that surface and narrows re-evaluation to specific upstream capability triggers. | Replace the stale open-question note with a pointer to the resolved decision or mark it as historical context only. |

## Open Spec Questions

| ID | State | Owning artifact | Current truth | Exit condition |
|---|---|---|---|---|
| `AUDIT-CONSUMER-INTERFACE` | `open` | `docs/superpowers/specs/codex-collaboration/decisions.md` | The audit record shape and write behavior are specified, but the query / aggregation / export interface for consuming audit records is still not specified. | Specify the consumer interface or deliberately defer it behind a narrower rollout boundary. |

## Intentional Future-Scope Deferrals

| ID | State | Owning artifact | Current truth | Exit condition |
|---|---|---|---|---|
| `DIALOGUE-FORK` | `deferred` | `docs/superpowers/specs/codex-collaboration/decisions.md` and `docs/superpowers/specs/codex-collaboration/contracts.md` | `codex.dialogue.fork` and fork-specific lineage operations are intentionally deferred from the current dialogue milestone. This is a live future-scope surface, not a forgotten gap. | A concrete branched-dialogue use case enters scope and a follow-up packet is opened. |
| `MCP-STRUCTURED-ERROR-REASON` | `deferred` | `docs/superpowers/specs/codex-collaboration/contracts.md` | MCP clients still rely on text-prefix recoverability for certain delegation errors because a structured wire-level `reason` field is explicitly deferred to a future packet. | Define and land the structured wire field in a follow-up packet. |

## Maintenance Rule

When a new unresolved item appears, add it here immediately if it crosses any
authority boundary:

- a closed ticket leaves real follow-on work behind
- a carry-forward tracker becomes the real home of still-open debt
- a linked ticket/spec/plan no longer matches the implemented state
- a newer diagnostic or closeout explicitly disproves an older planned
  follow-up or blocker model
- a future-scope surface is intentionally deferred but still matters to roadmap
  truth

This register should stay short enough to scan in one sitting. If a row grows
too detailed, move the detail into the owning artifact and keep only the
current-truth summary here.
