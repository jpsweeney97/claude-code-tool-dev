# Codex-Collaboration Reconciliation Register

Use this file for open or unreconciled work.

Start at [codex-collaboration Current State](./codex-collaboration-current-state.md)
for project orientation, implemented-now surface, authority ownership, and
reader routing.

Last reconciled: 2026-04-30

## Authority

This register is the working index of still-open, still-deferred, or
still-unreconciled `codex-collaboration` work in this repo.

Authority boundary:

- This file summarizes current-state classification, priority, and next-action
  labeling for work that already has source evidence elsewhere in the repo.
- This file is **not** the canonical long-form current-state synthesis. It is the
  bounded index of open, deferred, or still-unreconciled work.
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

1. Resolve `T-20260416-01` closure standard: accept test coverage plus
   App Server version drift as sufficient, or wait for natural live
   fallback proof (implementation and non-regression evidence landed;
   fallback recovery path unproven by live run).
2. Implement `T-20260429-01` Phase 1 sandbox carve-outs (Options B + E) and
   validate via a comparable `/delegate` smoke with avoidable sandbox-friction
   escalations <=2. Count legitimate operator-gated approvals separately.
3. Classify or intentionally safe-terminalize the currently unsupported App
   Server request kinds tracked by `T-20260429-02`.
4. Sweep residual typing and minor Packet 1 carry-forward debt (`TT.1`,
   `RT.1`, `P1-MINOR-SWEEP`).
5. Convert `BMARK-L1-L3` into explicit follow-up tickets or deliberately
   decline those L1/L2/L3 items as non-goals.
6. Specify or explicitly defer `AUDIT-CONSUMER-INTERFACE`.

## Ticket-Owned Active Work

| ID | State | Owning artifact | Current truth | Exit condition |
|---|---|---|---|---|
| `T-20260416-01` | `open` | `docs/tickets/2026-04-16-codex-collaboration-dialogue-reply-extraction-mismatch.md` plus `docs/tickets/closed-tickets/2026-03-30-codex-collaboration-dialogue-parity-and-scouting-retirement.md` | Implementation landed (`00ec0054`): advisory-only `thread/read` fallback (mechanism A) with turn-ID lookup, best-effort failure semantics, shared `turn_extraction.py` helper, and 12 tests (5 extraction + 7 runtime). Live post-patch verification (`c5807d84`): 5 adversarial turns on Codex `0.125.0`, all completed without error, fallback did not fire. Non-regression established; fallback recovery path unproven by live evidence (original failure class did not reproduce). | Accept test coverage plus App Server version drift (`0.117.0` → `0.125.0`) as sufficient closure evidence and close the ticket, or wait for a natural live fallback recovery proof. |
| `T-20260429-01` | `open` | `docs/tickets/2026-04-29-codex-collaboration-delegation-friction-reduction.md` | T-01's closing live `/delegate` smoke required 24 operator escalations to produce a 1-line edit, surfacing three plugin friction sources: `~/.codex/` reads (Codex consulting its own memory + skill cache), worktree `.git` cross-pointer reads (in-worktree `rg`/`git` traversing the gitdir target outside the worktree), and opaque `file_change` escalation payloads. Phase 1 (Options B + E) is mechanical sandbox-policy carve-outs in `runtime.py`; Phase 2 Option F investigation is complete — `file_change` payload opacity is confirmed as an upstream schema limitation (`FileChangeRequestApprovalParams` carries only `grantRoot` and `reason`), `/delegate` SKILL.md rendering narrowed accordingly (D-06). `file_change` opacity is counted separately from avoidable sandbox friction. | Land the Phase 1 sandbox carve-outs and validate via a comparable smoke run with avoidable sandbox-friction escalations <=2. Count legitimate operator-gated approvals separately. |
| `T-20260429-02` | `open` | `docs/tickets/2026-04-29-codex-collaboration-unsupported-server-request-reachability.md` | The current delegation runtime parks only three server-request kinds (`command_approval`, `file_change`, `request_user_input`). Other App Server request methods that the current parser cannot fully support can still create minimal `unknown` records and terminalize jobs as `unknown`. The open work is to classify each unsupported method by reachability and then provide one of: supported handling, a regression test proving intentional safe terminal behavior, or a documented non-reachability proof. | Classify each unsupported `ServerRequest` method and land either support, regression coverage for intentional safe terminal behavior, or a recorded non-reachability proof for current advisory/delegation flows. |

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

## Open Spec Questions

| ID | State | Owning artifact | Current truth | Exit condition |
|---|---|---|---|---|
| `AUDIT-CONSUMER-INTERFACE` | `open` | `docs/superpowers/specs/codex-collaboration/decisions.md` | The audit record shape and write behavior are specified, but the query / aggregation / export interface for consuming audit records is still not specified. | Specify the consumer interface or deliberately defer it behind a narrower rollout boundary. |

## Intentional Future-Scope Deferrals

| ID | State | Owning artifact | Current truth | Exit condition |
|---|---|---|---|---|
| `DIALOGUE-FORK` | `deferred` | `docs/superpowers/specs/codex-collaboration/decisions.md` and `docs/superpowers/specs/codex-collaboration/contracts.md` | Dialogue branchability is preserved as an architectural property, but the intended surface is `seed_from` on `codex.dialogue.start` (copy-and-diverge via current-head `thread/fork`), not a standalone `codex.dialogue.fork` tool. Tree-structured dialogue and prefix seeding are explicitly deferred. See [decisions.md §Dialogue Fork Scope](../superpowers/specs/codex-collaboration/decisions.md#dialogue-fork-scope). | A concrete seeded-dialogue use case justifies implementation. Constraints: admissibility, fresh control resolution, dialogue-thread `thread/fork` verification, and D-07 ordering dependency. |
| `MCP-STRUCTURED-ERROR-REASON` | `deferred` | `docs/superpowers/specs/codex-collaboration/contracts.md` | MCP clients still rely on text-prefix recoverability for certain delegation errors because a structured wire-level `reason` field is explicitly deferred to a future packet. | Define and land the structured wire field in a follow-up packet. |
| `ADVISORY-WIDENING-ROTATION` | `deferred` | `docs/superpowers/specs/codex-collaboration/advisory-runtime-policy.md` plus `packages/plugins/codex-collaboration/server/control_plane.py` and `packages/plugins/codex-collaboration/server/profiles.py` | Advisory widening, narrowing, freeze-and-rotate, and reap behavior are specified as future-scope design, clearly separated from current Packet 1 fixed-posture behavior. The spec text (`advisory-runtime-policy.md`) has been restructured into current behavior and future-scope sections (D-03). The current implementation rejects widened advisory requests and rejects widened profile settings until rotate support exists. | Implement advisory widening/rotation with matching recovery and profile behavior. |
| `PHASED-CONSULTATION-PROFILES` | `deferred` | `packages/plugins/codex-collaboration/references/consultation-profiles.yaml` plus `packages/plugins/codex-collaboration/server/profiles.py` | The profile catalog includes phased profiles such as `debugging`, but the resolver currently rejects any profile with `phases` until phase-progression support exists. This is an intentional future-scope surface, not an accidental runtime bug. | Implement phase-progression support for phased profiles, or narrow the shipped profile catalog/documentation so only currently resolvable profiles are advertised. |

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
