# T-20260511-01: Widen discard() admission to recover from anomalous needs_escalation

```yaml
id: T-20260511-01
date: 2026-05-11
status: open
priority: low
tags: [codex-collaboration, delegation, discard, defense-in-depth, operational-recovery]
blocked_by: []
blocks: []
effort: small
```

## Context

Surfaced during PR #125 disposition investigation (2026-05-11). PR #125 (`fix(delegate): harden escalation state machine and sandbox support roots`) was closed without merging — all three of its scope areas were superseded by Packet 1 (PR #126) and the sandbox carve-outs PR (#127). The spot-check that grounded the close decision identified one residual operational-recovery gap that Packet 1 did not capture.

The gap is small in probability and narrow in scope, but the recovery cost when it fires is high (manual store mutation; no operator action).

## Defect

The discard gate on main (`delegation_controller.py`, `discard()` method) admits a job for discard when:

```python
_discardable = job.promotion_state in ("pending", "prechecks_failed") or (
    job.status in ("failed", "unknown", "canceled")
    and job.promotion_state is None
)
```

It does **not** admit `(status=needs_escalation, promotion_state=None)`.

In normal operation, that exclusion is correct: a `needs_escalation` job is awaiting operator response via `codex.delegate.decide`, and discard would short-circuit the escalation flow.

But under one specific anomalous path, `_finalize_turn` produces `(status=needs_escalation, promotion_state=None)` for cancel-capable kinds (`command_approval`, `file_change`) — and that state has no operational recovery.

## The anomalous path

`_finalize_turn` (`delegation_controller.py:2431`) Step 3 reads the captured request's status snapshot. If the snapshot is `pending` (not `resolved`/`canceled`), Step 3 logs an `"anomalous pending"` warning and defensively writes the store entry to `resolved`. But the local `request_snapshot` variable still holds the old `pending` value, so Step 4's resolved/canceled branches do not match, and Step 5b's kind-based fall-through fires:

```python
elif captured_request.kind in _CANCEL_CAPABLE_KINDS:
    final_status = "needs_escalation"
```

Result: `(status=needs_escalation, promotion_state=None)`. The discard gate rejects this. The job is stuck.

The path is explicitly tested at `test_finalize_turn_terminal_guard.py:599` (`test_l9_anomalous_pending_warning`), confirming Packet 1's authors knew about it and chose to log+recover rather than hard-fix.

## When the anomalous path can fire

Packet 1's architectural invariant is that every non-parse-failed capture path writes a terminal request status before `_finalize_turn` runs. Audit of the current code confirms this invariant holds for all known paths:

| Path | Writes terminal request status before finalize? |
|---|---|
| Happy path (operator `decide(accept/deny)`) | Yes (`mark_resolved`) |
| Operator no-show (timeout cancel-success) | Yes (`record_timeout` writes `status=canceled` atomically) |
| Timeout cancel-dispatch-failed | Yes (writes canceled), then raises sentinel → finalize bypassed |
| Timeout interrupt-failed/succeeded | Yes (writes canceled), then raises sentinel → finalize bypassed |
| Decide-dispatch-failed | Sentinel raised → finalize bypassed |
| Worker generic `Exception` | `_mark_execution_unknown_and_cleanup` marks JOB as `unknown` (discardable); request store untouched but irrelevant since finalize is not called |

So the anomalous path can fire **only** under one of:

1. A code defect in the terminal-status-write paths above (e.g., `mark_resolved` succeeds but write doesn't commit; a future code path forgets the write)
2. A race between operator `decide()` and turn completion that leaves the store mid-flight
3. A future code change introducing a new capture path that forgets to write terminal status

All three are low-probability under current code, but the recovery cost is asymmetric: the stuck job requires manual `pending_request_store` mutation or job-store surgery to clear.

## Proposed fix

Add `needs_escalation` to the discard admission set when `promotion_state` is `None`:

```python
_discardable = job.promotion_state in ("pending", "prechecks_failed") or (
    job.status in ("failed", "unknown", "canceled", "needs_escalation")
    and job.promotion_state is None
)
```

Existing rejection logic for `(needs_escalation, promotion_state != None)` (in-flight escalation work) remains intact via the `promotion_state is None` clause.

## Acceptance criteria

- [ ] AC1: `discard(job)` succeeds for a job with `(status=needs_escalation, promotion_state=None)` and performs the full discard cleanup chain: atomic `failed + discarded` transition, runtime release, lineage completion, terminal-outcome emission, audit event.
- [ ] AC2: New unit test exercising the recovery path end-to-end: construct a job at `(needs_escalation, None)` via the anomalous-pending fall-through, call `discard()`, assert success + cleanup invariants.
- [ ] AC3: Existing discard tests pass without modification. Rejection of `(needs_escalation, promotion_state != None)` (in-flight escalations) remains intact.
- [ ] AC4: `docs/superpowers/specs/codex-collaboration/promotion-protocol.md` updated to document the widened admission set and the recovery use case.

## Out of scope

- **PR #125's Option B** (auto-finalize empty `available_decisions` → `failed` in `_finalize_turn` Step 5): architecturally incompatible with Packet 1's "trust terminal-status invariant" design. The architecture deliberately keeps the fall-through producing `needs_escalation` so that defects are visible (anomalous-pending warning) rather than auto-recovered into a different status. Adding recovery via `discard` preserves that visibility.
- **Approval router projection changes**: already covered on main via `_PLUGIN_DECISIONS = ("approve", "deny")`.
- **Hardening the terminal-status-write paths** (root-cause defense): separate concern. If a specific defect is identified, file a targeted ticket; this ticket is the operational backstop.
- **Worker-thread restructuring**: out of scope.

## Provenance

- Surfaced during PR #125 disposition investigation, 2026-05-11.
- PR #125 (closed-without-merge): the original Option A change was bundled with the architecturally-superseded Option B; closing as a whole made sense but Option A's value was identified as standalone.
- T-20260423-01 (closed 2026-04-29 via successful live `/delegate` smoke on Packet 1) — the original ticket PR #125 was meant to address.
- Spot-check evidence: `test_finalize_turn_terminal_guard.py:599` confirms the anomalous-pending path is reachable and intentionally allowed.

## References

- `_finalize_turn` Captured-Request Terminal Guard: `delegation_controller.py:2431-2570`
- Discard gate: `delegation_controller.py` (search `def discard`)
- `record_timeout` atomic terminal status write: `pending_request_store.py` (search `def record_timeout`)
- Test for anomalous-pending path: `tests/test_finalize_turn_terminal_guard.py:599`
- Contract source: `docs/superpowers/specs/codex-collaboration/promotion-protocol.md`
- Closed predecessor ticket: `docs/tickets/closed-tickets/2026-04-23-codex-collaboration-delegate-execution-remediation.md`
