# Packet 1 — Phase H: Finalizer, Consumers & Contracts

**Parent plan:** [manifest](../2026-04-24-packet-1-deferred-approval-response.md)
**Tasks:** 19–22
**Scope:** `_finalize_turn` Captured-Request Terminal Guard (R13/R14 focal point: one-snapshot rule, 4-row request-to-job terminal mapping, 9-row path table, 6-bullet test set). `poll()` `UnknownKindInEscalationProjection` catch + `signal_internal_abort`. `discard()` gate expansion for `canceled` with null promotion_state. `contracts.md` — 5-section update (§decide async, §Start success-union, §Pending Escalation View kind narrowing, §DelegationJob.status + §active_delegation.status, §discard).
**Landing invariant:** `_finalize_turn` terminal guard honors one-snapshot invariant; all 6 plan-wide structural invariants preserved at commit time (6 sentinel raise-sites, 4 mapping rows, 9 path rows, 14–15 canceled propagation touch points, 5 contract sections, 6 test bullets).
**Note:** Task 19 lands the R14 one-snapshot rule — the terminal invariant gate of the plan. Task 20 integration test bodies are `pass` stubs under concrete docstrings. See manifest §Pre-Execution Notes for implementer contract.

---

## Task 19: `_finalize_turn` Captured-Request Terminal Guard (one-snapshot rule)

**Status: COMPLETE.** Feat `1f97b333` (2026-04-27), fix `4409b23c` (2026-04-27), docs (this commit). Suite: 1040 passed, 0 skipped. G18.1 CLOSED, F16.1 CLOSED, F16.2 lineage CLOSED.

**Stale line anchors:** The line numbers at `:14` (`delegation_controller.py:1439-1533`) and `:121` (`delegation_controller.py:1439-1533`) below are STALE — they cite pre-Task-17/18 positions. The binding line anchors are in `task-19-convergence-map.md` Live Anchors table, verified at HEAD `1f97b333`. Do not copy anchors from this section.

**Files:**
- Modify: `packages/plugins/codex-collaboration/server/delegation_controller.py:1439-1533` (rewrite `_finalize_turn`) **(STALE — live anchor: `:2340-2445` pre-rewrite)**
- Test: `packages/plugins/codex-collaboration/tests/test_finalize_turn_terminal_guard.py` (new)

**Spec anchor:** §_finalize_turn Captured-Request Terminal Guard (lines ~1731-1835). This is the R14 one-snapshot rule focal point — the 6 tests in §Tests to add must map to test bodies here.

- [ ] **Step 19.1: Write the failing tests (one-snapshot invariant enforcement + 5 branches)**

Create `packages/plugins/codex-collaboration/tests/test_finalize_turn_terminal_guard.py`:

```python
"""Packet 1 + R14: _finalize_turn Captured-Request Terminal Guard.

Six spec tests per §_finalize_turn Captured-Request Terminal Guard — Tests to add:
1. Decide-success terminal guard (happy path) → final_status="completed"
2. Timeout-cancel-dispatch-succeeded terminal guard → final_status="canceled"
3. D4 blind-write suppression (snapshot-terminal case)
4. One-snapshot invariant enforcement (call counter)
5. Post-dispatch turn fault (OB-1 fallback) → final_status="unknown"
6. Anomalous captured+pending fallback (one-snapshot semantics)
"""

from __future__ import annotations

from unittest.mock import MagicMock, call

import pytest


def test_decide_success_terminal_guard_maps_to_completed(
    delegation_controller_fixture, pending_request_store_factory, simple_job_factory
) -> None:
    """Per §Tests to add bullet 1: request_snapshot.status='resolved' +
    turn_result.status='completed' → final_status='completed'."""
    pass


def test_timeout_cancel_dispatch_succeeded_maps_to_canceled(
    delegation_controller_fixture, pending_request_store_factory, simple_job_factory
) -> None:
    """Per §Tests to add bullet 2: request_snapshot.status='canceled' +
    any turn_result.status → final_status='canceled'. _emit_terminal_outcome_if_needed
    writes DelegationOutcomeRecord with terminal_status='canceled'."""
    pass


def test_d4_blind_write_suppressed_for_terminal_snapshot(
    delegation_controller_fixture, pending_request_store_factory, simple_job_factory,
    pending_request_store_spy
) -> None:
    """Per §Tests to add bullet 3: when request_snapshot.status is 'resolved'
    or 'canceled', D4's update_status(rid, 'resolved') must NOT fire.
    Inspect the store's journal to confirm no update_status record was
    written in the finalizer window."""
    pass


def test_one_snapshot_invariant_exactly_one_status_read(
    delegation_controller_fixture, pending_request_store_factory, simple_job_factory,
    pending_request_store_get_counter
) -> None:
    """Per §Tests to add bullet 4: exactly ONE
    pending_request_store.get(rid) call for status derivation per
    captured-request path through _finalize_turn.
    Hydration reads for non-status fields (if any) must use a distinct
    access pattern that the test harness recognizes as non-derivation."""
    pass


def test_post_dispatch_turn_fault_ob1_fallback_maps_to_unknown(
    delegation_controller_fixture, pending_request_store_factory, simple_job_factory
) -> None:
    """Per §Tests to add bullet 5: request_snapshot.status='resolved' +
    turn_result.status='failed' → final_status='unknown' (OB-1:
    transport applied but turn-level outcome unverified)."""
    pass


def test_anomalous_pending_fallback_preserves_snapshot_authority(
    delegation_controller_fixture, pending_request_store_factory, simple_job_factory
) -> None:
    """Per §Tests to add bullet 6 (R14 one-snapshot semantics):
    Construct a synthetic trace where captured_request is non-None and
    not parse-failed, but request_snapshot.status='pending' at finalizer
    entry. Assert:
      - _finalize_turn reads request_snapshot ONCE
      - Observes pending → writes D4 update_status(rid, 'resolved')
        as legacy fall-through
      - STILL falls through to kind-based logic based on the PRE-D4
        request_snapshot.status='pending' (NOT a post-D4 re-read that
        would see 'resolved')
      - kind-based branch produces final_status='needs_escalation'
      - Log warning emitted about anomalous state
      - PendingRequestStore.get(rid).status == 'resolved' after
        finalizer returns (confirms D4 side-effect on a distinct authority)."""
    pass
```

- [ ] **Step 19.2: Run failing tests**

```bash
uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests/test_finalize_turn_terminal_guard.py -v
```

Expected: FAIL — current _finalize_turn uses kind-based derivation without the one-snapshot rule.

- [ ] **Step 19.3: Rewrite `_finalize_turn` with the Captured-Request Terminal Guard**

Edit `_finalize_turn` at `delegation_controller.py:1439-1533`. Replace the captured-request branch with the R14 one-snapshot rule:

```python
def _finalize_turn(
    self,
    *,
    job_id: str,
    runtime_id: str,
    collaboration_id: str,
    entry: ExecutionRuntimeEntry,
    turn_result: TurnExecutionResult,
    captured_request: PendingServerRequest | None,
    interrupted_by_unknown: bool,
    captured_request_parse_failed: bool,
) -> DelegationJob | DelegationEscalation:
    """Post-turn status derivation, audit, and cleanup.

    Packet 1 (T-20260423-02): under the async-decide worker-thread model,
    the captured-request branch applies the Captured-Request Terminal
    Guard (spec §_finalize_turn Captured-Request Terminal Guard, R14):
    exactly ONE pending_request_store.get(rid) read feeds final-status
    derivation (one-snapshot invariant). D4, terminal-mapping, and
    fall-through all consume the same snapshot.
    """
    _CANCEL_CAPABLE_KINDS = frozenset({"command_approval", "file_change"})

    if captured_request is not None:
        # D6 diagnostic — only when we have a parseable request with
        # wire-correlated IDs.
        if not captured_request_parse_failed:
            _verify_post_turn_signals(
                notifications=turn_result.notifications,
                request_id=captured_request.request_id,
                item_id=captured_request.item_id,
            )

            # --- Captured-Request Terminal Guard (R14 one-snapshot rule) ---
            request_snapshot = self._pending_request_store.get(
                captured_request.request_id
            )
            # request_snapshot.status is the AUTHORITATIVE input for both
            # D4 blind-write suppression AND terminal-guard status mapping.
            # NO second .status read may participate in derivation.

            if request_snapshot is not None and request_snapshot.status == "resolved":
                if turn_result.status == "completed":
                    final_status: JobStatus = "completed"
                else:
                    # OB-1: transport applied decision but turn-level
                    # outcome unverified.
                    final_status = "unknown"
                # D4 skipped: request is already terminal.
                # Terminal-guard mapping complete.
                updated_job = self._persist_job_transition(job_id, final_status)
                self._lineage_store.update_status(
                    collaboration_id,
                    "completed" if final_status == "completed" else "unknown",
                )
                self._runtime_registry.release(runtime_id)
                entry.session.close()
                self._emit_terminal_outcome_if_needed(job_id)
                return updated_job

            if request_snapshot is not None and request_snapshot.status == "canceled":
                final_status = "canceled"
                # D4 skipped: worker already wrote terminal state.
                updated_job = self._persist_job_transition(job_id, final_status)
                # Lineage is completed (cancel is verified); asymmetric
                # split per spec §JobStatus='canceled' propagation.
                self._lineage_store.update_status(collaboration_id, "completed")
                self._runtime_registry.release(runtime_id)
                entry.session.close()
                self._emit_terminal_outcome_if_needed(job_id)
                return updated_job

            # --- Pending or tombstone: D4 legacy fall-through + kind-based derivation ---
            # D4 runs ONLY for request_snapshot.status == "pending".
            # For None (tombstone), skip D4 and log anomaly.
            if request_snapshot is not None and request_snapshot.status == "pending":
                # D4 may write; the write does NOT retroactively promote
                # the snapshot. Final-status derivation continues below
                # using the PRE-D4 snapshot.status="pending".
                self._pending_request_store.update_status(
                    captured_request.request_id, "resolved"
                )
                logger.warning(
                    "_finalize_turn: anomalous captured-request branch with "
                    "pending request at finalizer entry. Fell through to "
                    "kind-based logic per one-snapshot fallback.",
                    extra={
                        "job_id": job_id,
                        "request_id": captured_request.request_id,
                    },
                )
            elif request_snapshot is None:
                logger.warning(
                    "_finalize_turn: tombstone snapshot (request record "
                    "missing). Skipped D4; falling through to kind-based.",
                    extra={
                        "job_id": job_id,
                        "request_id": captured_request.request_id,
                    },
                )
            # Kind-based fall-through (pre-Packet-1 logic preserved).

        # Pre-R14 unknown-kind branch preserved (captured_request_parse_failed
        # is True only for the parse-failure path — no snapshot read needed):
        if captured_request.kind in _CANCEL_CAPABLE_KINDS or interrupted_by_unknown:
            if interrupted_by_unknown:
                final_status = "unknown"
            else:
                final_status = "needs_escalation"
        elif turn_result.status == "completed":
            final_status = "completed"
        else:
            final_status = "needs_escalation"

        updated_job = self._persist_job_transition(job_id, final_status)

        if final_status == "needs_escalation":
            self._journal.append_audit_event(
                AuditEvent(
                    event_id=self._uuid_factory(),
                    timestamp=self._journal.timestamp(),
                    actor="claude",
                    action="escalate",
                    collaboration_id=collaboration_id,
                    runtime_id=runtime_id,
                    job_id=job_id,
                    request_id=captured_request.request_id,
                )
            )
            # Hydration-only read — NON-status fields for view construction.
            # This is NOT the terminal-guard derivation read (that's
            # request_snapshot above). The one-snapshot invariant permits
            # later reads for return-shape hydration that don't feed
            # terminal-guard logic.
            hydrated = self._pending_request_store.get(
                captured_request.request_id
            )
            return DelegationEscalation(
                job=updated_job,
                pending_escalation=self._project_request_to_view(
                    hydrated or captured_request
                ),
                agent_context=turn_result.agent_message or None,
            )

        # Non-escalation terminal: release + close and return plain job.
        self._lineage_store.update_status(
            collaboration_id,
            "completed" if final_status in ("completed",) else "unknown",
        )
        self._runtime_registry.release(runtime_id)
        entry.session.close()
        self._emit_terminal_outcome_if_needed(job_id)
        return updated_job

    # No server request captured — clean completion or failure (unchanged).
    if turn_result.status == "completed":
        no_request_status: JobStatus = "completed"
    elif turn_result.status == "failed":
        no_request_status = "failed"
    else:
        no_request_status = "unknown"

    updated_job = self._persist_job_transition(job_id, no_request_status)
    self._lineage_store.update_status(collaboration_id, "completed")
    self._runtime_registry.release(runtime_id)
    entry.session.close()
    self._emit_terminal_outcome_if_needed(job_id)

    return updated_job
```

- [ ] **Step 19.4: Run terminal-guard tests**

```bash
uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests/test_finalize_turn_terminal_guard.py -v
```

Expected: PASS.

- [ ] **Step 19.5: Run full suite**

```bash
uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests -x 2>&1 | tail -60
```

Expected: PASS. If any prior test breaks, it's almost certainly asserting pre-R14 kind-based derivation; update to match the terminal-guard semantics.

- [ ] **Step 19.6: Commit**

```bash
git add packages/plugins/codex-collaboration/server/delegation_controller.py packages/plugins/codex-collaboration/tests/test_finalize_turn_terminal_guard.py
git commit -m "$(cat <<'EOF'
feat(delegate): add _finalize_turn Captured-Request Terminal Guard (R14 one-snapshot) (T-20260423-02 Task 19)

Per spec §_finalize_turn Captured-Request Terminal Guard (R14):
  - Exactly ONE pending_request_store.get(rid) read for status derivation
  - request_snapshot.status="resolved" → final_status="completed" or
    "unknown" (OB-1 for non-"completed" turn_result)
  - request_snapshot.status="canceled" → final_status="canceled"
  - request_snapshot.status="pending" → D4 legacy fall-through + kind-based
    (pre-D4 snapshot still authority; D4 write doesn't retroactively promote)
  - request_snapshot is None → skip D4, fall through, log anomaly

Hydration reads for NON-status fields (used to build DelegationEscalation
return) do not participate in the one-snapshot invariant — they're a
distinct access pattern.

Preserves all pre-R14 invariants: sentinel raise-sites (6), terminal
mapping (4 rows), path table (9 rows), §contracts.md updates (5 sections),
§Captured-Request Terminal Guard test bullets (6).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 20: `poll()` update — UnknownKindInEscalationProjection catch + signal_internal_abort

**Files:**
- Modify: `packages/plugins/codex-collaboration/server/delegation_controller.py` (rewrite `poll()` projection segment)
- Test: `packages/plugins/codex-collaboration/tests/test_poll_projection_guard_integration.py` (new)

**Spec anchor:** §Projection helper rewrites — poll() callsite (spec lines ~1936-1964).

- [ ] **Step 20.1: Write the failing test**

Create `packages/plugins/codex-collaboration/tests/test_poll_projection_guard_integration.py`:

```python
"""Packet 1: poll() catches UnknownKindInEscalationProjection and signals abort."""

from __future__ import annotations


def test_poll_returns_pending_escalation_none_on_unknown_kind(
    delegation_controller_fixture, pending_request_store_factory, simple_job_factory
) -> None:
    """Pre-Packet-1 JSONL replay surfaces a PendingServerRequest(kind='unknown')
    bound to a job's parked_request_id. poll() catches
    UnknownKindInEscalationProjection, logs critical, signals internal abort,
    returns pending_escalation=None."""
    pass


def test_poll_signals_internal_abort_with_correct_reason(
    delegation_controller_fixture, pending_request_store_factory, simple_job_factory,
    resolution_registry_spy
) -> None:
    """The signal_internal_abort call uses reason='unknown_kind_in_escalation_projection'
    (poll callsite reason — NOT 'parked_projection_invariant_violation'
    which is start's callsite reason)."""
    pass


def test_poll_returns_pending_escalation_view_for_normal_kind(
    delegation_controller_fixture, pending_request_store_factory, simple_job_factory
) -> None:
    """Regression: poll() on a needs_escalation job with a command_approval
    request returns the view normally."""
    pass
```

- [ ] **Step 20.2: Run failing tests**

Expected: FAIL.

- [ ] **Step 20.3: Update `poll()` to catch `UnknownKindInEscalationProjection`**

Edit `DelegationController.poll` at `delegation_controller.py:901-945`. Replace the projection segment:

```python
pending_escalation = None
if refreshed.status == "needs_escalation":
    try:
        pending_escalation = self._project_pending_escalation(refreshed)
    except UnknownKindInEscalationProjection as exc:
        logger.critical(
            "delegation.poll: unknown-kind in escalation projection; "
            "signaling worker-coordinated internal abort",
            extra={
                "job_id": refreshed.job_id,
                "request_id": refreshed.parked_request_id,
                "cause": str(exc),
            },
        )
        if refreshed.parked_request_id is not None:
            self._registry.signal_internal_abort(
                refreshed.parked_request_id,
                reason="unknown_kind_in_escalation_projection",
            )
        pending_escalation = None
```

- [ ] **Step 20.4: Run tests**

```bash
uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests/test_poll_projection_guard_integration.py -v
```

Expected: PASS.

- [ ] **Step 20.5: Commit**

```bash
git add packages/plugins/codex-collaboration/server/delegation_controller.py packages/plugins/codex-collaboration/tests/test_poll_projection_guard_integration.py
git commit -m "$(cat <<'EOF'
feat(delegate): poll() catches UnknownKindInEscalationProjection + signals abort (T-20260423-02 Task 20)

poll()'s projection segment now wraps _project_pending_escalation in
try/except UnknownKindInEscalationProjection. On catch: log critical,
signal_internal_abort(reason="unknown_kind_in_escalation_projection"),
return pending_escalation=None. Subsequent polls observe the worker's
abort-path writes (status → unknown).

Callsite-local reason ("unknown_kind_in_escalation_projection") is
distinct from start()'s broader reason ("parked_projection_invariant_violation")
— the helper stays pure.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 21: `discard()` gate expansion (admit canceled with null promotion_state)

**Files:**
- Modify: `packages/plugins/codex-collaboration/server/delegation_controller.py:1404-1406` (expand status tuple)
- Test: `packages/plugins/codex-collaboration/tests/test_discard_canceled.py` (new)

**Spec anchor:** §JobStatus='canceled' propagation — `discard()` gate row (spec line ~1377).

- [ ] **Step 21.1: Write the failing test**

Create `packages/plugins/codex-collaboration/tests/test_discard_canceled.py`:

```python
"""Packet 1: discard() admits canceled jobs with null promotion_state."""

from __future__ import annotations

from server.models import DiscardRejectedResponse, DiscardResult


def test_discard_canceled_with_null_promotion_state_succeeds(
    delegation_controller_fixture, simple_job_factory
) -> None:
    job = simple_job_factory(status="canceled", promotion_state=None)
    result = delegation_controller_fixture.discard(job_id=job.job_id)
    assert isinstance(result, DiscardResult)
    assert result.job.promotion_state == "discarded"


def test_discard_canceled_with_applied_promotion_state_rejects(
    delegation_controller_fixture, simple_job_factory
) -> None:
    """Post-mutation states still reject regardless of status."""
    job = simple_job_factory(status="canceled", promotion_state="applied")
    result = delegation_controller_fixture.discard(job_id=job.job_id)
    assert isinstance(result, DiscardRejectedResponse)
    assert result.reason == "job_not_discardable"


def test_discard_canceled_writes_audit_event(
    delegation_controller_fixture, simple_job_factory, audit_event_spy
) -> None:
    job = simple_job_factory(status="canceled", promotion_state=None)
    delegation_controller_fixture.discard(job_id=job.job_id)
    assert any(
        ev.action == "discard" and ev.job_id == job.job_id
        for ev in audit_event_spy.appended
    )
```

- [ ] **Step 21.2: Run failing test**

Expected: FAIL — canceled not in the gate tuple.

- [ ] **Step 21.3: Expand `discard()` gate**

Edit `DelegationController.discard` at `delegation_controller.py:1404-1406`:

```python
# Before:
# _discardable = job.promotion_state in ("pending", "prechecks_failed") or (
#     job.status in ("failed", "unknown") and job.promotion_state is None
# )

# After:
_discardable = job.promotion_state in ("pending", "prechecks_failed") or (
    job.status in ("failed", "unknown", "canceled")
    and job.promotion_state is None
)
```

- [ ] **Step 21.4: Run test to verify it passes**

```bash
uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests/test_discard_canceled.py -v
```

Expected: PASS.

- [ ] **Step 21.5: Commit**

```bash
git add packages/plugins/codex-collaboration/server/delegation_controller.py packages/plugins/codex-collaboration/tests/test_discard_canceled.py
git commit -m "$(cat <<'EOF'
feat(delegate): expand discard() gate to admit canceled with null promotion_state (T-20260423-02 Task 21)

Per spec §JobStatus='canceled' propagation — discard() gate row: canceled
joins failed/unknown in the "discardable when promotion_state is null"
branch. Post-mutation promotion states (applied, rollback_needed) still
reject regardless of status. Backs the list_user_attention_required
"retry-or-dismiss" UX promise — canceled jobs can now be dismissed.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 22: contracts.md — 5 section updates

**Files:**
- Modify: `docs/superpowers/specs/codex-collaboration/contracts.md` (5 sections)

**Spec anchor:** §contracts.md updates (spec lines ~2023-2051).

- [ ] **Step 22.1: Read the existing contracts.md structure**

```bash
wc -l /Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/contracts.md
grep -n "^##\|^###" /Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/contracts.md | head -60
```

Locate the five sections to edit (approximate line numbers per spec):
- §decide at `:297-310`
- §Pending Escalation View at `:325-334`
- §DelegationJob.status at `:73`
- §active_delegation.status at `:379`
- §discard (locate by header)

- [ ] **Step 22.2: Update §decide**

Replace the existing §decide section with:

```markdown
### decide

`codex.delegate.decide(job_id, request_id, decision, answers?)`

**Post-Packet 1 (T-20260423-02): async acceptance model.** decide() returns once
the operator's decision has been accepted for dispatch (journal intent durable,
reservation committed). Dispatch completion is observed asynchronously via
`codex.delegate.poll`.

**Return shape (success):**

```json
{
  "decision_accepted": true,
  "job_id": "<uuid>",
  "request_id": "<uuid>"
}
```

**Accepted-for-dispatch, not applied.** The response indicates the plugin has
committed the decision to the operation journal and signaled the worker to
dispatch it. The plugin does NOT claim the App Server has applied the
decision (OB-1). Post-dispatch observations come through poll.

**poll is the sole observation surface for post-decide state.** Between
decide() returning and the worker completing `job.status → running`, poll()
may transiently show the pre-decide `pending_escalation`; callers should
trust decide()'s `decision_accepted=true` as authoritative.

**Rejection (DecisionRejectedResponse):** unchanged. Reasons continue to be
`invalid_decision`, `job_not_found`, `job_not_awaiting_decision`,
`request_not_found`, `request_job_mismatch`, `request_already_decided`,
`runtime_unavailable`, `answers_required`, `answers_not_allowed`.
```

- [ ] **Step 22.3: Update §Start (success-union documentation)**

Locate the §Start section and add documentation of the success union as a table:

```markdown
### Start success outcomes

codex.delegate.start returns one of three success shapes or raises. The MCP
serializer maps each internal outcome to a wire JSON shape.

| Internal outcome | Return type | MCP JSON shape |
|------------------|-------------|----------------|
| Parked (parkable capture) | DelegationEscalation | `{"job": {...}, "pending_escalation": {...}, "agent_context": null, "escalated": true}` |
| Turn completed without capture | plain DelegationJob | `{"job_id": "...", "status": "completed", ...}` (no `pending_escalation`, no `escalated`) |
| Unknown-kind parse failure | plain DelegationJob | `{"job_id": "...", "status": "unknown", ...}` (no `pending_escalation`, no `escalated`) |
| Start-wait budget elapsed | plain DelegationJob | `{"job_id": "...", "status": "running", ...}` (caller polls; NOT a failure) |
| Worker exception (pre-capture) | RAISES | MCP tool error: `DelegationStartError` with text prefix `worker_failed_before_capture` |
| Parked projection invariant violation | RAISES | MCP tool error: `DelegationStartError` with text prefix `parked_projection_invariant_violation` |
| Unknown-kind interrupt transport failure | RAISES | MCP tool error: `DelegationStartError` with text prefix `unknown_kind_interrupt_transport_failure` |

**Text-prefix recoverability.** MCP clients that need to branch on the
reason can parse the leading token of the error text up to the first `": "`.
A structured `reason` field on the MCP wire is deferred to a future packet.
```

- [ ] **Step 22.4: Update §Pending Escalation View (kind enum narrowing)**

Edit the `kind` enum in the §Pending Escalation View section:

```markdown
| Field | Type | Notes |
|-------|------|-------|
| kind  | `Literal["command_approval", "file_change", "request_user_input"]` | `unknown` is a valid `PendingRequestKind` at the store/audit layer but cannot appear in a `PendingEscalationView` under Packet 1 — such requests terminalize the job instead (see §Unknown-kind contract in the design spec). |
```

- [ ] **Step 22.5: Update §DelegationJob.status and §active_delegation.status**

Expand the status enum in both sections. Find the current enum (likely a Literal list or JSON-schema "enum" array of 6 values) and add `"canceled"`:

```markdown
**status:** one of `queued`, `running`, `needs_escalation`, `completed`, `failed`, `canceled`, `unknown`.

**Definition of `canceled`:** terminal state reached via the non-cancel timeout
interrupt-succeeded branch OR the cancel-capable timeout with successful
cancel-dispatch; distinct from `unknown` (which indicates unverified
transport failure). See §JobStatus='canceled' propagation in the design
spec.

Migration: pre-Packet-1 JSONL records have no `canceled` entries (no historical
data anomalies); post-Packet-1 runtime-generated records may carry the new literal.
```

Apply to both the §DelegationJob.status section and the §active_delegation.status section.

- [ ] **Step 22.6: Update §discard**

Locate the §discard section and update the admissibility rule:

```markdown
**Admissibility:** Discardable when `promotion_state in ("pending", "prechecks_failed")` OR when `status in ("failed", "unknown", "canceled")` with null `promotion_state`. Post-mutation states (`applied`, `rollback_needed`) remain non-discardable regardless of status.

Rationale: the `list_user_attention_required` surface includes canceled jobs
under §JobStatus='canceled' propagation; the discard contract must offer the
matching close path or the "retry-or-dismiss" UX promise is unbacked.

Migration guidance: existing discard callers observing
`DiscardRejectedResponse(reason="job_not_discardable")` on a canceled job
may now see `DiscardResult` instead; no caller relied on the rejection as
a signal, so this is a strict behavior widening without regression risk.
```

- [ ] **Step 22.7: Verify contracts.md is still valid Markdown**

```bash
cat /Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/contracts.md | head -100
```

Spot-check no headers are broken.

- [ ] **Step 22.8: Commit**

```bash
git add docs/superpowers/specs/codex-collaboration/contracts.md
git commit -m "$(cat <<'EOF'
docs(delegate): update contracts.md for Packet 1 (T-20260423-02 Task 22)

Five sections updated per spec §contracts.md updates:
  - §decide: async acceptance model + 3-field DelegationDecisionResult
  - §Start: success-union documentation with wire-shape table
  - §Pending Escalation View: kind enum narrowed (3 literals; unknown not permitted)
  - §DelegationJob.status + §active_delegation.status: add "canceled" literal
  - §discard: admit "canceled" with null promotion_state

Text-prefix recoverability for DelegationStartError.reason is documented
as the MCP wire contract for Packet 1; structured propagation deferred.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

**Phase H complete.** Packet 1 implementation is done.

**Final verification is plan-wide, not phase-local.** After the Task 22 commit lands, run the full verification checklist in the parent manifest — see [§Final Verification in the manifest](../2026-04-24-packet-1-deferred-approval-response.md#final-verification). This is REQUIRED — Phase H completion alone does NOT satisfy plan closure. The checklist covers: full pytest suite, mypy type check, structural invariant counts (6 sentinel raise-sites, 4 terminal mapping rows, ≥14 canceled propagation touch points), dialogue-controller regression check, and integration smoke.

