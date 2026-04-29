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

1. Land the `T-20260416-01` extraction fix and run one post-patch verification.
2. Implement `T-20260429-01` Phase 1 sandbox carve-outs (Options B + E) and
   validate via a comparable `/delegate` smoke with ≤2 escalations.
3. Sweep residual typing and minor Packet 1 carry-forward debt (`TT.1`,
   `RT.1`, `P1-MINOR-SWEEP`).
4. Convert `BMARK-L1-L3` into explicit follow-up tickets or deliberately
   decline those L1/L2/L3 items as non-goals.
5. Specify or explicitly defer `AUDIT-CONSUMER-INTERFACE`.

## Ticket-Owned Active Work

| ID | State | Owning artifact | Current truth | Exit condition |
|---|---|---|---|---|
| `T-20260416-01` | `open` | `docs/tickets/2026-04-16-codex-collaboration-dialogue-reply-extraction-mismatch.md` plus `docs/tickets/closed-tickets/2026-03-30-codex-collaboration-dialogue-parity-and-scouting-retirement.md` | The reply-path extraction mismatch remains a live product defect. Ticket body revised with protocol analysis against vendored schema: the `turn/completed.turn.items[]` fallback was withdrawn (`Turn.items` is always empty per `TurnCompletedNotification.json:1285`). Recommended fix is advisory-only `thread/read` fallback (mechanism A) with turn-ID lookup, best-effort failure semantics, and 9 implementation tests. Mechanism C (notification-stream investigation) is optional diagnostic work, not a gate. | Land the extraction fix with tests (#1-#9 including fallback failure cases and execution-turn isolation) and one post-patch verification, then close the ticket. |
| `T-20260429-01` | `open` | `docs/tickets/2026-04-29-codex-collaboration-delegation-friction-reduction.md` | T-01's closing live `/delegate` smoke required 24 operator escalations to produce a 1-line edit, surfacing three plugin friction sources: `~/.codex/` reads (Codex consulting its own memory + skill cache), worktree `.git` cross-pointer reads (in-worktree `rg`/`git` traversing the gitdir target outside the worktree), and opaque `file_change` escalation payloads (empty `requested_scope` denies operator visibility). Phase 1 (Options B + E) is mechanical sandbox-policy carve-outs in `runtime.py`; Phase 2 (Option F) is investigation-first because the empty `requested_scope` may be a plugin gap or an App Server limitation. | Land the sandbox carve-outs and either resolve the file_change payload opacity or document it as an upstream limitation, then validate via a comparable smoke run with <=2 escalations. |

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
| `CONTRACTS-T02-TEMPORAL-MARKER` | `drift` | `docs/superpowers/specs/codex-collaboration/contracts.md` | `contracts.md:327` uses `T-20260423-02` as a temporal marker ("Post-Packet 1 (T-20260423-02)") in normative contract text. Now that T-02 is closed, the reference is stale attribution in a normative document. | Rewrite to a non-ticket-specific temporal marker or add a "(closed)" annotation. |
| `T02-CLOSED-TICKET-PATH` | `drift` | `docs/tickets/2026-04-23-deferred-same-turn-approval-response.md` | T-20260423-02 was closed in place at `docs/tickets/` rather than moved to `docs/tickets/closed-tickets/` to avoid rename-detection noise in the 7-file reconciliation commit. | `git mv` to `closed-tickets/` in a subsequent housekeeping commit. |

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
