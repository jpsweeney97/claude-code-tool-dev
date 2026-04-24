# Packet 1 — Phase B: Stores

**Parent plan:** [manifest](../2026-04-24-packet-1-deferred-approval-response.md)
**Tasks:** 6–9
**Scope:** `PendingServerRequest` 11 new fields, 3 success-path mutators (`mark_resolved`, `record_response_dispatch`, `record_protocol_echo`), 3 atomic failure-path mutators (`record_timeout`, `record_dispatch_failure`, `record_internal_abort`), `DelegationJob.parked_request_id` + `DelegationJobStore.update_parked_request`.
**Landing invariant:** PendingServerRequest/DelegationJob have new fields + mutators; JSONL round-trips pass.

---

## Task 6: PendingServerRequest field additions (11 new fields)

**Files:**
- Modify: `packages/plugins/codex-collaboration/server/models.py:270-288` (extend `PendingServerRequest` dataclass)
- Modify: `packages/plugins/codex-collaboration/server/pending_request_store.py` (adjust `_replay` to hydrate new fields with safe defaults)
- Test: `packages/plugins/codex-collaboration/tests/test_pending_server_request_fields.py` (new)

**Spec anchor:** §PendingServerRequest (additions) (spec lines ~1414-1432). Field semantics at spec §Store mutators (spec lines ~1477-1535).

- [ ] **Step 6.1: Write the failing test**

Create `packages/plugins/codex-collaboration/tests/test_pending_server_request_fields.py`:

```python
"""Packet 1: PendingServerRequest gains 11 new fields, all nullable / safe-default."""

from __future__ import annotations

from dataclasses import fields

from server.models import PendingServerRequest


def test_has_resolution_action_field() -> None:
    req = PendingServerRequest(
        request_id="r", runtime_id="rt", collaboration_id="c",
        codex_thread_id="t", codex_turn_id="tu", item_id="i",
        kind="command_approval", requested_scope={},
    )
    assert req.resolution_action is None


def test_has_all_new_fields_with_safe_defaults() -> None:
    field_names = {f.name for f in fields(PendingServerRequest)}
    new_fields = {
        "resolution_action",
        "response_payload",
        "response_dispatch_at",
        "dispatch_result",
        "dispatch_error",
        "interrupt_error",
        "resolved_at",
        "protocol_echo_signals",
        "protocol_echo_observed_at",
        "timed_out",
        "internal_abort_reason",
    }
    missing = new_fields - field_names
    assert not missing, f"missing fields: {missing}"


def test_default_values_are_safe() -> None:
    req = PendingServerRequest(
        request_id="r", runtime_id="rt", collaboration_id="c",
        codex_thread_id="t", codex_turn_id="tu", item_id="i",
        kind="command_approval", requested_scope={},
    )
    assert req.resolution_action is None
    assert req.response_payload is None
    assert req.response_dispatch_at is None
    assert req.dispatch_result is None
    assert req.dispatch_error is None
    assert req.interrupt_error is None
    assert req.resolved_at is None
    assert req.protocol_echo_signals == ()
    assert req.protocol_echo_observed_at is None
    assert req.timed_out is False
    assert req.internal_abort_reason is None


def test_existing_records_replay_cleanly_with_none_defaults(tmp_path) -> None:
    """Legacy records (pre-Packet 1) must replay without KeyError on the
    new fields. Simulate by writing a record with ONLY the old-shape keys
    and verifying replay materializes a PendingServerRequest with new
    fields at their defaults."""
    from server.pending_request_store import PendingRequestStore

    store = PendingRequestStore(plugin_data_path=tmp_path, session_id="s1")
    # Hand-craft a legacy record without the new fields and append it.
    import json
    legacy_record = {
        "op": "create",
        "request_id": "legacy-r1",
        "runtime_id": "rt1",
        "collaboration_id": "c1",
        "codex_thread_id": "t1",
        "codex_turn_id": "tu1",
        "item_id": "i1",
        "kind": "command_approval",
        "requested_scope": {"path": "/x"},
        "available_decisions": ["approve", "deny"],
        "status": "pending",
        # NO new fields — simulates pre-Packet-1 data
    }
    store._store_path.write_text(
        json.dumps(legacy_record, sort_keys=True) + "\n", encoding="utf-8"
    )
    replayed = store.get("legacy-r1")
    assert replayed is not None
    assert replayed.resolution_action is None
    assert replayed.protocol_echo_signals == ()
    assert replayed.timed_out is False
```

- [ ] **Step 6.2: Run test to verify it fails**

```bash
uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests/test_pending_server_request_fields.py -v
```

Expected: FAIL — new fields do not exist.

- [ ] **Step 6.3: Extend `PendingServerRequest` with the 11 new fields**

Edit `packages/plugins/codex-collaboration/server/models.py:270-288`:

```python
@dataclass(frozen=True)
class PendingServerRequest:
    """Plugin-owned record for an execution or advisory server request.

    The execution approval-routing layer preserves request-relevant payloads
    opaquely in ``requested_scope``. Normalized request-scope comparison is a
    later T-05 concern and is intentionally not implemented here.

    Packet 1 (T-20260423-02) adds 11 nullable/safe-default fields for the
    deferred-approval lifecycle. All new fields are back-compatible: legacy
    records replay with None / empty defaults.
    """

    request_id: str
    runtime_id: str
    collaboration_id: str
    codex_thread_id: str
    codex_turn_id: str
    item_id: str
    kind: PendingRequestKind
    requested_scope: dict[str, Any]
    available_decisions: tuple[str, ...] = ()
    status: PendingRequestStatus = "pending"
    # Packet 1: deferred-resolution lifecycle
    resolution_action: Literal["approve", "deny"] | None = None
    response_payload: dict[str, Any] | None = None
    response_dispatch_at: str | None = None
    dispatch_result: Literal["succeeded", "failed"] | None = None
    dispatch_error: str | None = None
    interrupt_error: str | None = None
    resolved_at: str | None = None
    protocol_echo_signals: tuple[str, ...] = ()
    protocol_echo_observed_at: str | None = None
    timed_out: bool = False
    internal_abort_reason: str | None = None
```

- [ ] **Step 6.4: Update `PendingRequestStore._replay` to hydrate new fields with defaults**

Edit `packages/plugins/codex-collaboration/server/pending_request_store.py` around line 94 (the `op == "create"` branch). Change the `PendingServerRequest(...)` constructor call to use `.get(key, <default>)` for every new field:

```python
if op == "create":
    try:
        req = PendingServerRequest(
            request_id=record["request_id"],
            runtime_id=record["runtime_id"],
            collaboration_id=record["collaboration_id"],
            codex_thread_id=record["codex_thread_id"],
            codex_turn_id=record["codex_turn_id"],
            item_id=record["item_id"],
            kind=record["kind"],
            requested_scope=record["requested_scope"],
            available_decisions=tuple(record.get("available_decisions", [])),
            status=record.get("status", "pending"),
            resolution_action=record.get("resolution_action"),
            response_payload=record.get("response_payload"),
            response_dispatch_at=record.get("response_dispatch_at"),
            dispatch_result=record.get("dispatch_result"),
            dispatch_error=record.get("dispatch_error"),
            interrupt_error=record.get("interrupt_error"),
            resolved_at=record.get("resolved_at"),
            protocol_echo_signals=tuple(record.get("protocol_echo_signals", ())),
            protocol_echo_observed_at=record.get("protocol_echo_observed_at"),
            timed_out=record.get("timed_out", False),
            internal_abort_reason=record.get("internal_abort_reason"),
        )
        requests[req.request_id] = req
    except (KeyError, TypeError, ValueError):
        continue
```

Read the current store code to confirm the exact indentation and surrounding structure — if the existing `op == "create"` block uses a different structure, preserve it while adding the new `.get(...)` parameters.

- [ ] **Step 6.5: Run test to verify it passes**

```bash
uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests/test_pending_server_request_fields.py -v
```

Expected: 4 PASS.

- [ ] **Step 6.6: Verify existing tests still pass (no regression)**

```bash
uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests/test_pending_request_store.py -v
```

Expected: all existing PendingRequestStore tests PASS. If any fail, the cause is almost certainly a missed field default in `_replay` — fix and re-run.

- [ ] **Step 6.7: Commit**

```bash
git add packages/plugins/codex-collaboration/server/models.py packages/plugins/codex-collaboration/server/pending_request_store.py packages/plugins/codex-collaboration/tests/test_pending_server_request_fields.py
git commit -m "$(cat <<'EOF'
feat(delegate): extend PendingServerRequest with 11 new deferred-approval fields (T-20260423-02 Task 6)

Adds resolution_action, response_payload, response_dispatch_at,
dispatch_result, dispatch_error, interrupt_error, resolved_at,
protocol_echo_signals, protocol_echo_observed_at, timed_out, and
internal_abort_reason. All nullable / safe-default — legacy records
replay cleanly with None / empty-tuple / False defaults.

Store mutators for these fields land in Tasks 7-8.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 7: PendingRequestStore mutators — success-path group

**Files:**
- Modify: `packages/plugins/codex-collaboration/server/pending_request_store.py` (add `mark_resolved`, `record_response_dispatch`, `record_protocol_echo` + replay ops)
- Test: `packages/plugins/codex-collaboration/tests/test_pending_request_store_mutators.py` (new)

**Spec anchor:** §Store mutators — PendingRequestStore additions (spec lines ~1479-1513).

- [ ] **Step 7.1: Write the failing test**

Create `packages/plugins/codex-collaboration/tests/test_pending_request_store_mutators.py`:

```python
"""Packet 1: PendingRequestStore mutators for the success-path lifecycle."""

from __future__ import annotations

import pytest

from server.models import PendingServerRequest
from server.pending_request_store import PendingRequestStore


def _make_pending(rid: str = "r1") -> PendingServerRequest:
    return PendingServerRequest(
        request_id=rid,
        runtime_id="rt1",
        collaboration_id="c1",
        codex_thread_id="th1",
        codex_turn_id="tu1",
        item_id="it1",
        kind="command_approval",
        requested_scope={"path": "/x"},
        available_decisions=("approve", "deny"),
    )


def test_mark_resolved_sets_status_and_timestamp(tmp_path) -> None:
    store = PendingRequestStore(plugin_data_path=tmp_path, session_id="s1")
    store.create(_make_pending())
    store.mark_resolved("r1", resolved_at="2026-04-24T12:00:00Z")
    result = store.get("r1")
    assert result is not None
    assert result.status == "resolved"
    assert result.resolved_at == "2026-04-24T12:00:00Z"


def test_record_response_dispatch_sets_four_fields(tmp_path) -> None:
    store = PendingRequestStore(plugin_data_path=tmp_path, session_id="s1")
    store.create(_make_pending())
    store.record_response_dispatch(
        "r1",
        action="approve",
        payload={"decision": "accept"},
        dispatch_at="2026-04-24T12:00:00Z",
    )
    result = store.get("r1")
    assert result is not None
    assert result.resolution_action == "approve"
    assert result.response_payload == {"decision": "accept"}
    assert result.response_dispatch_at == "2026-04-24T12:00:00Z"
    assert result.dispatch_result == "succeeded"  # hardcoded by the mutator


def test_record_response_dispatch_does_not_change_status(tmp_path) -> None:
    # Status transitions via mark_resolved; record_response_dispatch is
    # the transport-write stamp only.
    store = PendingRequestStore(plugin_data_path=tmp_path, session_id="s1")
    store.create(_make_pending())
    store.record_response_dispatch(
        "r1", action="approve", payload={}, dispatch_at="2026-04-24T12:00:00Z"
    )
    result = store.get("r1")
    assert result is not None
    assert result.status == "pending"


def test_record_protocol_echo_sets_signals_and_timestamp(tmp_path) -> None:
    store = PendingRequestStore(plugin_data_path=tmp_path, session_id="s1")
    store.create(_make_pending())
    store.record_protocol_echo(
        "r1",
        signals=("serverRequest/resolved", "item/completed"),
        observed_at="2026-04-24T12:00:01Z",
    )
    result = store.get("r1")
    assert result is not None
    assert result.protocol_echo_signals == (
        "serverRequest/resolved",
        "item/completed",
    )
    assert result.protocol_echo_observed_at == "2026-04-24T12:00:01Z"


def test_mutators_round_trip_across_replay(tmp_path) -> None:
    """Force a fresh store instance (new replay) and confirm each mutator's
    effect persists."""
    store = PendingRequestStore(plugin_data_path=tmp_path, session_id="s1")
    store.create(_make_pending())
    store.record_response_dispatch(
        "r1", action="approve", payload={"k": "v"}, dispatch_at="t1"
    )
    store.mark_resolved("r1", resolved_at="t2")
    store.record_protocol_echo("r1", signals=("x",), observed_at="t3")

    reopened = PendingRequestStore(plugin_data_path=tmp_path, session_id="s1")
    result = reopened.get("r1")
    assert result is not None
    assert result.status == "resolved"
    assert result.resolved_at == "t2"
    assert result.resolution_action == "approve"
    assert result.response_payload == {"k": "v"}
    assert result.response_dispatch_at == "t1"
    assert result.dispatch_result == "succeeded"
    assert result.protocol_echo_signals == ("x",)
    assert result.protocol_echo_observed_at == "t3"
```

- [ ] **Step 7.2: Run test to verify it fails**

```bash
uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests/test_pending_request_store_mutators.py -v
```

Expected: FAIL — the three mutators do not exist.

- [ ] **Step 7.3: Implement the three mutators + replay ops**

Edit `packages/plugins/codex-collaboration/server/pending_request_store.py`. Add these mutator methods on `PendingRequestStore` (anywhere after `update_status`):

```python
def mark_resolved(self, request_id: str, resolved_at: str) -> None:
    """Atomic transition to status="resolved" with resolved_at timestamp.

    Success-path mutator only. Not used on timeout or dispatch-failure
    paths — those use record_timeout / record_dispatch_failure which set
    status="canceled" atomically.
    """
    self._append(
        {
            "op": "mark_resolved",
            "request_id": request_id,
            "resolved_at": resolved_at,
        }
    )


def record_response_dispatch(
    self,
    request_id: str,
    *,
    action: Literal["approve", "deny"],
    payload: dict[str, Any],
    dispatch_at: str,
) -> None:
    """Record the successful transport write for an operator decision.

    dispatch_result is hardcoded to "succeeded" inside this mutator — no
    caller kwarg. The failure state is represented structurally by the
    separate record_dispatch_failure mutator (Task 8).
    """
    self._append(
        {
            "op": "record_response_dispatch",
            "request_id": request_id,
            "resolution_action": action,
            "response_payload": payload,
            "response_dispatch_at": dispatch_at,
            "dispatch_result": "succeeded",
        }
    )


def record_protocol_echo(
    self,
    request_id: str,
    *,
    signals: tuple[str, ...],
    observed_at: str,
) -> None:
    """Record post-turn protocol echo signals observed for this request."""
    self._append(
        {
            "op": "record_protocol_echo",
            "request_id": request_id,
            "protocol_echo_signals": list(signals),
            "protocol_echo_observed_at": observed_at,
        }
    )
```

At the top of `pending_request_store.py`, ensure the `Literal` import is present (`from typing import Any, Literal, get_args`).

Then extend `_replay` to handle the three new ops. Read the existing `_replay` method to find its existing `op` dispatch (after `op == "create"` and `op == "update_status"`). Add:

```python
elif op == "mark_resolved":
    rid = record.get("request_id")
    if rid in requests:
        existing = requests[rid]
        requests[rid] = PendingServerRequest(
            **{**asdict_for_replay(existing),
               "status": "resolved",
               "resolved_at": record.get("resolved_at"),
               "available_decisions": existing.available_decisions,
               "protocol_echo_signals": existing.protocol_echo_signals,
               "requested_scope": existing.requested_scope,
            }
        )
elif op == "record_response_dispatch":
    rid = record.get("request_id")
    if rid in requests:
        existing = requests[rid]
        requests[rid] = PendingServerRequest(
            **{**asdict_for_replay(existing),
               "resolution_action": record.get("resolution_action"),
               "response_payload": record.get("response_payload"),
               "response_dispatch_at": record.get("response_dispatch_at"),
               "dispatch_result": record.get("dispatch_result"),
               "available_decisions": existing.available_decisions,
               "protocol_echo_signals": existing.protocol_echo_signals,
               "requested_scope": existing.requested_scope,
            }
        )
elif op == "record_protocol_echo":
    rid = record.get("request_id")
    if rid in requests:
        existing = requests[rid]
        requests[rid] = PendingServerRequest(
            **{**asdict_for_replay(existing),
               "protocol_echo_signals": tuple(record.get("protocol_echo_signals", ())),
               "protocol_echo_observed_at": record.get("protocol_echo_observed_at"),
               "available_decisions": existing.available_decisions,
               "requested_scope": existing.requested_scope,
            }
        )
```

Add a module-private helper `asdict_for_replay` near the top of the file (since `dataclasses.asdict` would conflict with the custom tuple/dict types if we use it naively, a focused shallow-copy helper is cleaner):

```python
def asdict_for_replay(req: PendingServerRequest) -> dict[str, Any]:
    """Shallow copy of a PendingServerRequest as a dict, for use in replay
    mutation branches. Preserves tuples and dicts by reference — the
    replacing caller overwrites only the mutated fields."""
    from dataclasses import fields

    return {f.name: getattr(req, f.name) for f in fields(req)}
```

- [ ] **Step 7.4: Run test to verify it passes**

```bash
uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests/test_pending_request_store_mutators.py -v
```

Expected: 5 PASS. If any fail, the most likely cause is a typo in `_replay`'s dict-merge logic; inspect and fix.

- [ ] **Step 7.5: Verify existing store tests still pass**

```bash
uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests/test_pending_request_store.py -v
```

Expected: all PASS. Fix any regressions before committing.

- [ ] **Step 7.6: Commit**

```bash
git add packages/plugins/codex-collaboration/server/pending_request_store.py packages/plugins/codex-collaboration/tests/test_pending_request_store_mutators.py
git commit -m "$(cat <<'EOF'
feat(delegate): add PendingRequestStore success-path mutators (T-20260423-02 Task 7)

Adds mark_resolved (status → resolved + resolved_at), record_response_dispatch
(resolution_action + response_payload + response_dispatch_at + dispatch_result
hardcoded to "succeeded"), and record_protocol_echo (post-turn signal capture).
Each mutator appends a discrete op record; replay hydrates the new fields with
safe defaults for legacy records. Failure-path mutators land in Task 8.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 8: PendingRequestStore mutators — atomic failure-path group

**Files:**
- Modify: `packages/plugins/codex-collaboration/server/pending_request_store.py` (add `record_timeout`, `record_dispatch_failure`, `record_internal_abort` + replay ops)
- Test: `packages/plugins/codex-collaboration/tests/test_pending_request_store_atomic_mutators.py` (new)

**Spec anchor:** §Store mutators — PendingRequestStore atomic mutators (spec lines ~1514-1535). §Dispatch failure path (§Timeout path cancel-dispatch try/except). §Internal abort coordination step 3 (`record_internal_abort`).

These three mutators are **atomic**: each sets multiple fields in a single JSONL append. Partial-write replay MUST NEVER yield an inconsistent state (e.g., `dispatch_result="failed"` with `status="pending"`).

- [ ] **Step 8.1: Write the failing test**

Create `packages/plugins/codex-collaboration/tests/test_pending_request_store_atomic_mutators.py`:

```python
"""Packet 1: PendingRequestStore atomic mutators for timeout / dispatch-failure / internal-abort."""

from __future__ import annotations

from server.models import PendingServerRequest
from server.pending_request_store import PendingRequestStore


def _make_pending(rid: str = "r1") -> PendingServerRequest:
    return PendingServerRequest(
        request_id=rid,
        runtime_id="rt1",
        collaboration_id="c1",
        codex_thread_id="th1",
        codex_turn_id="tu1",
        item_id="it1",
        kind="command_approval",
        requested_scope={},
    )


def test_record_timeout_succeeded_cancel_dispatch(tmp_path) -> None:
    store = PendingRequestStore(plugin_data_path=tmp_path, session_id="s1")
    store.create(_make_pending())
    store.record_timeout(
        "r1",
        response_payload={"decision": "cancel"},
        response_dispatch_at="2026-04-24T12:00:00Z",
        dispatch_result="succeeded",
        dispatch_error=None,
    )
    r = store.get("r1")
    assert r is not None
    assert r.timed_out is True
    assert r.status == "canceled"
    assert r.response_payload == {"decision": "cancel"}
    assert r.response_dispatch_at == "2026-04-24T12:00:00Z"
    assert r.dispatch_result == "succeeded"
    assert r.dispatch_error is None
    assert r.resolution_action is None
    assert r.interrupt_error is None
    assert r.resolved_at is None


def test_record_timeout_failed_cancel_dispatch_carries_error(tmp_path) -> None:
    store = PendingRequestStore(plugin_data_path=tmp_path, session_id="s1")
    store.create(_make_pending())
    store.record_timeout(
        "r1",
        response_payload={"decision": "cancel"},
        response_dispatch_at="2026-04-24T12:00:00Z",
        dispatch_result="failed",
        dispatch_error="BrokenPipeError: stdin closed",
    )
    r = store.get("r1")
    assert r is not None
    assert r.timed_out is True
    assert r.status == "canceled"
    assert r.dispatch_result == "failed"
    assert r.dispatch_error == "BrokenPipeError: stdin closed"


def test_record_timeout_non_cancel_capable_interrupt_path(tmp_path) -> None:
    store = PendingRequestStore(plugin_data_path=tmp_path, session_id="s1")
    store.create(_make_pending())
    store.record_timeout(
        "r1",
        response_payload=None,
        response_dispatch_at=None,
        dispatch_result=None,
        dispatch_error=None,
    )
    r = store.get("r1")
    assert r is not None
    assert r.timed_out is True
    assert r.status == "canceled"
    assert r.response_payload is None
    assert r.dispatch_result is None


def test_record_timeout_non_cancel_capable_interrupt_failed_carries_interrupt_error(tmp_path) -> None:
    store = PendingRequestStore(plugin_data_path=tmp_path, session_id="s1")
    store.create(_make_pending())
    store.record_timeout(
        "r1",
        response_payload=None,
        response_dispatch_at=None,
        dispatch_result=None,
        dispatch_error=None,
        interrupt_error="RuntimeError: session interrupt failed",
    )
    r = store.get("r1")
    assert r is not None
    assert r.timed_out is True
    assert r.status == "canceled"
    assert r.interrupt_error == "RuntimeError: session interrupt failed"
    assert r.dispatch_error is None


def test_record_dispatch_failure_atomic_fields(tmp_path) -> None:
    store = PendingRequestStore(plugin_data_path=tmp_path, session_id="s1")
    store.create(_make_pending())
    store.record_dispatch_failure(
        "r1",
        action="approve",
        payload={"decision": "accept"},
        dispatch_at="2026-04-24T12:00:00Z",
        dispatch_error="BrokenPipeError: pipe closed",
    )
    r = store.get("r1")
    assert r is not None
    assert r.status == "canceled"
    assert r.dispatch_result == "failed"
    assert r.dispatch_error == "BrokenPipeError: pipe closed"
    assert r.resolution_action == "approve"
    assert r.response_payload == {"decision": "accept"}
    assert r.response_dispatch_at == "2026-04-24T12:00:00Z"
    assert r.resolved_at is None


def test_record_dispatch_failure_atomicity_no_partial(tmp_path) -> None:
    """Partial-write replay safety: the single-append JSONL record either
    materializes all fields or none. We verify this indirectly by
    inspecting the store's raw JSONL for a single line per mutation."""
    store = PendingRequestStore(plugin_data_path=tmp_path, session_id="s1")
    store.create(_make_pending())
    before_lines = store._store_path.read_text(encoding="utf-8").splitlines()
    store.record_dispatch_failure(
        "r1",
        action="approve",
        payload={},
        dispatch_at="t",
        dispatch_error="X: y",
    )
    after_lines = store._store_path.read_text(encoding="utf-8").splitlines()
    # Exactly ONE new line appended — atomicity is encoded in the single-write.
    assert len(after_lines) == len(before_lines) + 1


def test_record_internal_abort_sets_canceled_and_reason(tmp_path) -> None:
    store = PendingRequestStore(plugin_data_path=tmp_path, session_id="s1")
    store.create(_make_pending())
    store.record_internal_abort(
        "r1", reason="parked_projection_invariant_violation"
    )
    r = store.get("r1")
    assert r is not None
    assert r.status == "canceled"
    assert r.internal_abort_reason == "parked_projection_invariant_violation"
    assert r.resolution_action is None
    assert r.response_payload is None
    assert r.response_dispatch_at is None
    assert r.dispatch_result is None
    assert r.resolved_at is None


def test_record_internal_abort_round_trip_via_replay(tmp_path) -> None:
    store = PendingRequestStore(plugin_data_path=tmp_path, session_id="s1")
    store.create(_make_pending())
    store.record_internal_abort("r1", reason="unknown_kind_in_escalation_projection")
    reopened = PendingRequestStore(plugin_data_path=tmp_path, session_id="s1")
    r = reopened.get("r1")
    assert r is not None
    assert r.internal_abort_reason == "unknown_kind_in_escalation_projection"
    assert r.status == "canceled"
```

- [ ] **Step 8.2: Run test to verify it fails**

```bash
uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests/test_pending_request_store_atomic_mutators.py -v
```

Expected: FAIL — the three mutators do not exist.

- [ ] **Step 8.3: Implement the three atomic mutators + replay ops**

Edit `packages/plugins/codex-collaboration/server/pending_request_store.py`. Add these methods:

```python
def record_timeout(
    self,
    request_id: str,
    *,
    response_payload: dict[str, Any] | None,
    response_dispatch_at: str | None,
    dispatch_result: Literal["succeeded", "failed"] | None,
    dispatch_error: str | None,
    interrupt_error: str | None = None,
) -> None:
    """Atomic timeout record: timed_out=True + status=canceled in single append.

    Per spec §Timeout record fields:
      - Cancel-capable kind, dispatch succeeded:
          payload={"decision":"cancel"}, at=<iso>, result="succeeded", error=None, interrupt_error=None
      - Cancel-capable kind, dispatch failed:
          payload={"decision":"cancel"}, at=<iso>, result="failed",
          error=<sanitized>, interrupt_error=None
      - Non-cancel-capable kind, interrupt succeeded:
          payload=None, at=None, result=None, error=None, interrupt_error=None
      - Non-cancel-capable kind, interrupt failed:
          payload=None, at=None, result=None, error=None, interrupt_error=<sanitized>
    """
    self._append(
        {
            "op": "record_timeout",
            "request_id": request_id,
            "timed_out": True,
            "status": "canceled",
            "resolution_action": None,
            "response_payload": response_payload,
            "response_dispatch_at": response_dispatch_at,
            "dispatch_result": dispatch_result,
            "dispatch_error": dispatch_error,
            "interrupt_error": interrupt_error,
        }
    )


def record_dispatch_failure(
    self,
    request_id: str,
    *,
    action: Literal["approve", "deny"],
    payload: dict[str, Any],
    dispatch_at: str,
    dispatch_error: str,
) -> None:
    """Atomic dispatch-failure record: status=canceled + dispatch_result=failed
    + resolution_action + response_payload + response_dispatch_at + dispatch_error
    in a single append. Used when session.respond() raises on the operator-decide
    path. resolved_at stays None (the operator decision was NOT applied).
    """
    self._append(
        {
            "op": "record_dispatch_failure",
            "request_id": request_id,
            "status": "canceled",
            "dispatch_result": "failed",
            "dispatch_error": dispatch_error,
            "resolution_action": action,
            "response_payload": payload,
            "response_dispatch_at": dispatch_at,
            "resolved_at": None,
        }
    )


def record_internal_abort(self, request_id: str, *, reason: str) -> None:
    """Atomic internal-abort record: status=canceled + internal_abort_reason
    + resolution_action=None + payload fields cleared, in a single append.
    Used when the worker wakes on InternalAbort (plugin-invariant violation).
    """
    self._append(
        {
            "op": "record_internal_abort",
            "request_id": request_id,
            "status": "canceled",
            "internal_abort_reason": reason,
            "resolution_action": None,
            "response_payload": None,
            "response_dispatch_at": None,
            "dispatch_result": None,
            "resolved_at": None,
        }
    )
```

Extend `_replay` with the three new op branches:

```python
elif op == "record_timeout":
    rid = record.get("request_id")
    if rid in requests:
        existing = requests[rid]
        requests[rid] = PendingServerRequest(
            **{**asdict_for_replay(existing),
               "timed_out": True,
               "status": "canceled",
               "resolution_action": None,
               "response_payload": record.get("response_payload"),
               "response_dispatch_at": record.get("response_dispatch_at"),
               "dispatch_result": record.get("dispatch_result"),
               "dispatch_error": record.get("dispatch_error"),
               "interrupt_error": record.get("interrupt_error"),
               "available_decisions": existing.available_decisions,
               "protocol_echo_signals": existing.protocol_echo_signals,
               "requested_scope": existing.requested_scope,
            }
        )
elif op == "record_dispatch_failure":
    rid = record.get("request_id")
    if rid in requests:
        existing = requests[rid]
        requests[rid] = PendingServerRequest(
            **{**asdict_for_replay(existing),
               "status": "canceled",
               "dispatch_result": "failed",
               "dispatch_error": record.get("dispatch_error"),
               "resolution_action": record.get("resolution_action"),
               "response_payload": record.get("response_payload"),
               "response_dispatch_at": record.get("response_dispatch_at"),
               "resolved_at": None,
               "available_decisions": existing.available_decisions,
               "protocol_echo_signals": existing.protocol_echo_signals,
               "requested_scope": existing.requested_scope,
            }
        )
elif op == "record_internal_abort":
    rid = record.get("request_id")
    if rid in requests:
        existing = requests[rid]
        requests[rid] = PendingServerRequest(
            **{**asdict_for_replay(existing),
               "status": "canceled",
               "internal_abort_reason": record.get("internal_abort_reason"),
               "resolution_action": None,
               "response_payload": None,
               "response_dispatch_at": None,
               "dispatch_result": None,
               "resolved_at": None,
               "available_decisions": existing.available_decisions,
               "protocol_echo_signals": existing.protocol_echo_signals,
               "requested_scope": existing.requested_scope,
            }
        )
```

- [ ] **Step 8.4: Run test to verify it passes**

```bash
uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests/test_pending_request_store_atomic_mutators.py -v
```

Expected: 8 PASS.

- [ ] **Step 8.5: Commit**

```bash
git add packages/plugins/codex-collaboration/server/pending_request_store.py packages/plugins/codex-collaboration/tests/test_pending_request_store_atomic_mutators.py
git commit -m "$(cat <<'EOF'
feat(delegate): add PendingRequestStore atomic failure-path mutators (T-20260423-02 Task 8)

Adds record_timeout (timed_out=True + status=canceled + path-specific
dispatch fields), record_dispatch_failure (single-append atomicity of
status=canceled + dispatch_result=failed + forensic error), and
record_internal_abort (status=canceled + internal_abort_reason +
request-payload fields cleared). Each mutator is a single JSONL append
— partial-write replay cannot observe an inconsistent state.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 9: DelegationJob.parked_request_id + DelegationJobStore.update_parked_request

**Files:**
- Modify: `packages/plugins/codex-collaboration/server/models.py` (add `parked_request_id` to `DelegationJob`)
- Modify: `packages/plugins/codex-collaboration/server/delegation_job_store.py` (add `update_parked_request` + replay op)
- Test: `packages/plugins/codex-collaboration/tests/test_delegation_job_parked_request_id.py` (new)

**Spec anchor:** Spec §parked_request_id (lines ~1320-1332). The job's durable selector answering "which request is this job currently parked on."

- [ ] **Step 9.1: Write the failing test**

Create `packages/plugins/codex-collaboration/tests/test_delegation_job_parked_request_id.py`:

```python
"""Packet 1: DelegationJob.parked_request_id + update_parked_request mutator."""

from __future__ import annotations

from server.delegation_job_store import DelegationJobStore
from server.models import DelegationJob


def _make_job(job_id: str = "j1") -> DelegationJob:
    return DelegationJob(
        job_id=job_id,
        runtime_id="rt1",
        collaboration_id="c1",
        base_commit="abc",
        worktree_path="/tmp/wt",
        promotion_state=None,
        status="running",
    )


def test_parked_request_id_default_is_none(tmp_path) -> None:
    store = DelegationJobStore(plugin_data_path=tmp_path, session_id="s1")
    store.create(_make_job())
    result = store.get("j1")
    assert result is not None
    assert result.parked_request_id is None


def test_update_parked_request_sets_rid(tmp_path) -> None:
    store = DelegationJobStore(plugin_data_path=tmp_path, session_id="s1")
    store.create(_make_job())
    store.update_parked_request("j1", "r1")
    result = store.get("j1")
    assert result is not None
    assert result.parked_request_id == "r1"


def test_update_parked_request_clears_rid(tmp_path) -> None:
    store = DelegationJobStore(plugin_data_path=tmp_path, session_id="s1")
    store.create(_make_job())
    store.update_parked_request("j1", "r1")
    store.update_parked_request("j1", None)
    result = store.get("j1")
    assert result is not None
    assert result.parked_request_id is None


def test_update_parked_request_replay_consistency(tmp_path) -> None:
    store = DelegationJobStore(plugin_data_path=tmp_path, session_id="s1")
    store.create(_make_job())
    store.update_parked_request("j1", "r-set1")
    store.update_parked_request("j1", None)
    store.update_parked_request("j1", "r-set2")
    reopened = DelegationJobStore(plugin_data_path=tmp_path, session_id="s1")
    result = reopened.get("j1")
    assert result is not None
    assert result.parked_request_id == "r-set2"


def test_legacy_records_without_field_replay_as_none(tmp_path) -> None:
    store = DelegationJobStore(plugin_data_path=tmp_path, session_id="s1")
    # Hand-write a legacy record with no parked_request_id field.
    import json
    legacy = {
        "op": "create",
        "job_id": "j-legacy",
        "runtime_id": "rt1",
        "collaboration_id": "c1",
        "base_commit": "abc",
        "worktree_path": "/tmp/wt",
        "promotion_state": None,
        "promotion_attempt": 0,
        "status": "running",
        "artifact_paths": [],
        "artifact_hash": None,
    }
    store._store_path.write_text(
        json.dumps(legacy, sort_keys=True) + "\n", encoding="utf-8"
    )
    result = store.get("j-legacy")
    assert result is not None
    assert result.parked_request_id is None
```

- [ ] **Step 9.2: Run test to verify it fails**

```bash
uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests/test_delegation_job_parked_request_id.py -v
```

Expected: FAIL — field and mutator don't exist.

- [ ] **Step 9.3: Add `parked_request_id` to `DelegationJob`**

Edit `packages/plugins/codex-collaboration/server/models.py:368-388` (the `DelegationJob` dataclass). Add the field:

```python
@dataclass(frozen=True)
class DelegationJob:
    """Persisted delegation job record. See contracts.md §DelegationJob.

    Status transitions (running, completed, needs_escalation, failed,
    canceled, unknown) are managed by ``DelegationController`` and
    ``recover_startup()``.

    No ``created_at`` field by design — creation timestamp is captured in
    the ``job_creation`` journal entry under the same idempotency key.
    """

    job_id: str
    runtime_id: str
    collaboration_id: str
    base_commit: str
    worktree_path: str
    promotion_state: PromotionState | None
    promotion_attempt: int = 0
    status: JobStatus = "queued"
    artifact_paths: tuple[str, ...] = ()
    artifact_hash: str | None = None
    parked_request_id: str | None = None
```

- [ ] **Step 9.4: Add `update_parked_request` mutator + replay op**

Edit `packages/plugins/codex-collaboration/server/delegation_job_store.py`. Add the mutator (anywhere after `update_status_and_promotion`):

```python
def update_parked_request(
    self, job_id: str, parked_request_id: str | None
) -> None:
    """Set or clear the durable selector for which request this job's
    worker is currently parked on.

    Worker writes on park (rid) and on post-respond cleanup (None).
    Packet 1 §parked_request_id.
    """
    self._append(
        {
            "op": "update_parked_request",
            "job_id": job_id,
            "parked_request_id": parked_request_id,
        }
    )
```

Extend `_replay` to handle the new op. Read the existing `_replay` structure; add the branch near the other update branches:

```python
elif op == "update_parked_request":
    jid = record.get("job_id")
    if jid in jobs:
        existing = jobs[jid]
        jobs[jid] = DelegationJob(
            **{**asdict_for_replay(existing),
               "parked_request_id": record.get("parked_request_id"),
            }
        )
```

Also update the `op == "create"` replay branch in this file to hydrate `parked_request_id=record.get("parked_request_id")` (with None default for legacy). Follow the existing pattern.

Add a local `asdict_for_replay(job)` helper at module scope (same shape as the pending_request_store helper):

```python
def asdict_for_replay(job: DelegationJob) -> dict[str, Any]:
    from dataclasses import fields
    return {f.name: getattr(job, f.name) for f in fields(job)}
```

- [ ] **Step 9.5: Run test to verify it passes**

```bash
uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests/test_delegation_job_parked_request_id.py -v
```

Expected: 5 PASS.

- [ ] **Step 9.6: Verify existing DelegationJobStore tests still pass**

```bash
uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests/test_delegation_job_store.py -v
```

Expected: all PASS.

- [ ] **Step 9.7: Verify `list_user_attention_required` admits canceled jobs with null promotion_state (no code change needed — existing predicate works)**

Add a quick integration assertion inline in the test file:

```python
def test_list_user_attention_required_admits_canceled_jobs(tmp_path) -> None:
    store = DelegationJobStore(plugin_data_path=tmp_path, session_id="s1")
    job = DelegationJob(
        job_id="j-cancel",
        runtime_id="rt1",
        collaboration_id="c1",
        base_commit="abc",
        worktree_path="/tmp/wt",
        promotion_state=None,
        status="canceled",
    )
    store.create(job)
    attention = store.list_user_attention_required()
    assert any(j.job_id == "j-cancel" for j in attention), (
        "list_user_attention_required must admit canceled jobs with null "
        "promotion_state — see spec §JobStatus='canceled' propagation"
    )
```

Run:

```bash
uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests/test_delegation_job_parked_request_id.py::test_list_user_attention_required_admits_canceled_jobs -v
```

Expected: PASS. The existing predicate `promotion_state not in _TERMINAL_PROMOTION_STATES and not (status == "completed" and promotion_state is None)` already admits `status="canceled", promotion_state=None` because canceled is not completed.

- [ ] **Step 9.8: Commit**

```bash
git add packages/plugins/codex-collaboration/server/models.py packages/plugins/codex-collaboration/server/delegation_job_store.py packages/plugins/codex-collaboration/tests/test_delegation_job_parked_request_id.py
git commit -m "$(cat <<'EOF'
feat(delegate): add parked_request_id + update_parked_request mutator (T-20260423-02 Task 9)

Adds parked_request_id: str | None field on DelegationJob (default None —
back-compatible for legacy records) and DelegationJobStore.update_parked_request
mutator. Worker writes rid on park, None on post-respond cleanup.
list_user_attention_required confirmed to admit canceled jobs with null
promotion_state without modification (existing predicate already correct).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

**Phase B complete.** `PendingServerRequest` now carries all 11 new fields; its 3 success-path and 3 atomic failure-path mutators round-trip through the JSONL replay harness. `DelegationJob.parked_request_id` is wired and `DelegationJobStore.update_parked_request` is in place. The store layer can now observe — durably and atomically — every state transition Packet 1 introduces, including the critical atomicity guarantees on the failure-path mutators that the worker will lean on. Phase C follows with the journal validator relaxation for `decision=None`, after which Phase D introduces the cross-thread `ResolutionRegistry`.

---

