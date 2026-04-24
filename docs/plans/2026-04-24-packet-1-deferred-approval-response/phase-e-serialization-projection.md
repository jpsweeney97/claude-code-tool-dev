# Packet 1 — Phase E: Serialization & Projection

**Parent plan:** [manifest](../2026-04-24-packet-1-deferred-approval-response.md)
**Tasks:** 13–14
**Scope:** `DelegationDecisionResult` new 3-field shape (`decision_accepted`, `job_id`, `request_id`) + MCP serializer fix (remove custom branch at `mcp_server.py:505-516`). Projection helpers rewrite: `_project_request_to_view` unknown-kind guard raising `UnknownKindInEscalationProjection`, `_project_pending_escalation` job-anchored lookup, tombstone-projection for purged rows.
**Landing invariant:** `DelegationDecisionResult` round-trips to JSON via `asdict`; projection surfaces `UnknownKindInEscalationProjection` explicitly instead of silently coercing. This is a breaking contract change to `codex.delegate.decide` — flagged in Phase H contracts update.

---

## Task 13: DelegationDecisionResult new 3-field shape + MCP serializer fix

**Files:**
- Modify: `packages/plugins/codex-collaboration/server/models.py:418-426` (rewrite `DelegationDecisionResult`)
- Modify: `packages/plugins/codex-collaboration/server/mcp_server.py:505-516` (replace custom serializer branch)
- Test: `packages/plugins/codex-collaboration/tests/test_delegation_decision_result_shape.py` (new)
- Test: `packages/plugins/codex-collaboration/tests/test_mcp_decide_response_shape_integration.py` (new)

**Spec anchor:** §DelegationDecisionResult — new shape (spec mentions at lines ~964, ~2052-2087).

This is a **breaking contract change**. Callers that read `pending_escalation` or `agent_context` from `decide`'s response must switch to `poll()`.

- [ ] **Step 13.1: Write the failing test**

Create `packages/plugins/codex-collaboration/tests/test_delegation_decision_result_shape.py`:

```python
"""Packet 1: DelegationDecisionResult new 3-field shape."""

from __future__ import annotations

from dataclasses import fields

from codex_collaboration.server.models import DelegationDecisionResult


def test_has_exactly_three_fields() -> None:
    names = {f.name for f in fields(DelegationDecisionResult)}
    assert names == {"decision_accepted", "job_id", "request_id"}


def test_decision_accepted_is_bool() -> None:
    r = DelegationDecisionResult(
        decision_accepted=True, job_id="j1", request_id="r1"
    )
    assert r.decision_accepted is True


def test_no_pending_escalation_or_agent_context() -> None:
    # These fields must not exist post-Packet-1.
    r = DelegationDecisionResult(
        decision_accepted=True, job_id="j1", request_id="r1"
    )
    assert not hasattr(r, "pending_escalation")
    assert not hasattr(r, "agent_context")
    assert not hasattr(r, "job")
    assert not hasattr(r, "decision")
    assert not hasattr(r, "resumed")
```

Create `packages/plugins/codex-collaboration/tests/test_mcp_decide_response_shape_integration.py`:

```python
"""Packet 1: MCP serializer emits the 3-field DelegationDecisionResult shape."""

from __future__ import annotations

from dataclasses import asdict

from codex_collaboration.server.models import DelegationDecisionResult


def test_asdict_produces_three_keys() -> None:
    r = DelegationDecisionResult(
        decision_accepted=True, job_id="j1", request_id="r1"
    )
    payload = asdict(r)
    assert set(payload.keys()) == {"decision_accepted", "job_id", "request_id"}
    assert payload["decision_accepted"] is True
    assert payload["job_id"] == "j1"
    assert payload["request_id"] == "r1"
```

- [ ] **Step 13.2: Run tests to verify they fail**

```bash
uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests/test_delegation_decision_result_shape.py packages/plugins/codex-collaboration/tests/test_mcp_decide_response_shape_integration.py -v
```

Expected: FAIL — current shape has 5 fields.

- [ ] **Step 13.3: Rewrite `DelegationDecisionResult`**

Edit `packages/plugins/codex-collaboration/server/models.py:418-426`:

```python
@dataclass(frozen=True)
class DelegationDecisionResult:
    """Returned by codex.delegate.decide under the Packet 1 async contract.

    Post-Packet 1 (T-20260423-02): decide() returns once the operator's
    decision has been accepted for dispatch (journal intent durable,
    reservation committed), NOT once the dispatch has completed. The
    caller observes post-dispatch state through poll().

    Breaking change from the pre-Packet-1 shape — callers that read
    `pending_escalation` or `agent_context` from decide's response must
    switch to poll().
    """

    decision_accepted: bool
    job_id: str
    request_id: str
```

- [ ] **Step 13.4: Fix the MCP serializer branch**

Edit `packages/plugins/codex-collaboration/server/mcp_server.py:505-516`. Replace the custom branch with the fallthrough:

```python
# Before (at mcp_server.py:505-516):
# if isinstance(result, DelegationDecisionResult):
#     payload = {
#         "job": asdict(result.job),
#         "decision": result.decision,
#         "resumed": result.resumed,
#     }
#     if result.pending_escalation is not None:
#         payload["pending_escalation"] = asdict(result.pending_escalation)
#     if result.agent_context is not None:
#         payload["agent_context"] = result.agent_context
#     return payload
# return asdict(result)

# After:
if isinstance(result, DelegationDecisionResult):
    return asdict(result)
# Existing branch for other tools continues below.
```

Note: if the existing code has the generic fallthrough `return asdict(result)` further below, removing the `DelegationDecisionResult`-specific branch entirely is equivalent. Pick whichever is cleanest; verify by reading the surrounding context.

- [ ] **Step 13.5: Run tests to verify they pass**

```bash
uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests/test_delegation_decision_result_shape.py packages/plugins/codex-collaboration/tests/test_mcp_decide_response_shape_integration.py -v
```

Expected: PASS.

- [ ] **Step 13.6: Update broken existing tests**

Run the full test suite:

```bash
uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests -x 2>&1 | head -100
```

Tests that assert on `result.decision`, `result.resumed`, `result.pending_escalation`, `result.agent_context` — notably `test_mcp_server.py:1202` per spec — must be rewritten to the new shape. For each failing test:

- If the test asserts "decide succeeded": assert on `result.decision_accepted is True`, `result.job_id == expected`, `result.request_id == expected`.
- If the test asserts "decide returned pending_escalation": DELETE that assertion and add a follow-up `poll()` call that asserts the escalation is observable via poll (this reflects the new async contract).
- If the test asserts on `decision="approve"` inside the result: DELETE — the decision literal is passed IN (arg to decide), not echoed OUT.

Apply the rewrites file-by-file until the suite goes green.

- [ ] **Step 13.7: Commit**

```bash
git add packages/plugins/codex-collaboration/server/models.py packages/plugins/codex-collaboration/server/mcp_server.py packages/plugins/codex-collaboration/tests/
git commit -m "$(cat <<'EOF'
feat(delegate): rewrite DelegationDecisionResult to 3-field shape + fix MCP serializer (T-20260423-02 Task 13)

BREAKING CONTRACT CHANGE: decide() returns {decision_accepted, job_id,
request_id} — no longer carries job / pending_escalation / agent_context.
Post-dispatch observations now come from poll(). Caller migration forcing
is intentional per spec §Testing and Migration.

mcp_server.py's custom DelegationDecisionResult serializer branch
(previously at :505-516 reading the removed fields) collapses to the
generic asdict() fallthrough. Existing tests that inspected the pre-Packet-1
shape are rewritten to assert on the 3 new fields.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 14: Projection helpers rewrite (`_project_request_to_view` guard + `_project_pending_escalation` job-anchored + tombstone)

**Files:**
- Modify: `packages/plugins/codex-collaboration/server/delegation_controller.py:849-868` (rewrite both helpers)
- Test: `packages/plugins/codex-collaboration/tests/test_projection_helpers.py` (new)

**Spec anchor:** §Projection helper rewrites (spec lines ~1888-2021).

- [ ] **Step 14.1: Write the failing test**

Create `packages/plugins/codex-collaboration/tests/test_projection_helpers.py`:

```python
"""Packet 1: _project_request_to_view guards + _project_pending_escalation rewrite."""

from __future__ import annotations

from typing import cast

import pytest

from codex_collaboration.server.delegation_controller import (
    DelegationController,
    UnknownKindInEscalationProjection,
    _ESCALATABLE_REQUEST_KINDS,
)
from codex_collaboration.server.models import (
    DelegationJob,
    PendingServerRequest,
)


def test_escalatable_set_has_three_literals() -> None:
    assert _ESCALATABLE_REQUEST_KINDS == frozenset(
        {"command_approval", "file_change", "request_user_input"}
    )


def test_project_request_to_view_raises_for_unknown_kind(
    delegation_controller: DelegationController,
) -> None:
    req = PendingServerRequest(
        request_id="r1",
        runtime_id="rt1",
        collaboration_id="c1",
        codex_thread_id="t1",
        codex_turn_id="tu1",
        item_id="i1",
        kind="unknown",
        requested_scope={},
    )
    with pytest.raises(UnknownKindInEscalationProjection):
        delegation_controller._project_request_to_view(req)


def test_project_request_to_view_admits_escalatable_kinds(
    delegation_controller: DelegationController,
) -> None:
    for kind in ("command_approval", "file_change", "request_user_input"):
        req = PendingServerRequest(
            request_id=f"r-{kind}",
            runtime_id="rt1",
            collaboration_id="c1",
            codex_thread_id="t1",
            codex_turn_id="tu1",
            item_id="i1",
            kind=kind,
            requested_scope={},
        )
        view = delegation_controller._project_request_to_view(req)
        assert view.kind == kind


def test_project_pending_escalation_returns_none_for_terminal_job(
    delegation_controller: DelegationController, simple_job_factory
) -> None:
    for terminal in ("completed", "failed", "canceled", "unknown"):
        job = simple_job_factory(status=terminal)
        assert delegation_controller._project_pending_escalation(job) is None


def test_project_pending_escalation_returns_none_when_unparked(
    delegation_controller: DelegationController, simple_job_factory
) -> None:
    job = simple_job_factory(status="needs_escalation", parked_request_id=None)
    assert delegation_controller._project_pending_escalation(job) is None


def test_project_pending_escalation_returns_none_on_tombstone(
    delegation_controller: DelegationController,
    simple_job_factory,
    pending_request_store_factory,
) -> None:
    # Worker's mark_resolved landed but update_parked_request(None) hasn't —
    # the request is `resolved` but the job still shows parked_request_id.
    request = PendingServerRequest(
        request_id="r-tombstone",
        runtime_id="rt1",
        collaboration_id="c1",
        codex_thread_id="t1",
        codex_turn_id="tu1",
        item_id="i1",
        kind="command_approval",
        requested_scope={},
        status="resolved",
    )
    pending_request_store_factory.insert(request)
    job = simple_job_factory(
        status="needs_escalation", parked_request_id="r-tombstone"
    )
    assert delegation_controller._project_pending_escalation(job) is None


def test_project_pending_escalation_raises_for_unknown_kind_request(
    delegation_controller: DelegationController,
    simple_job_factory,
    pending_request_store_factory,
) -> None:
    request = PendingServerRequest(
        request_id="r-unknown",
        runtime_id="rt1",
        collaboration_id="c1",
        codex_thread_id="t1",
        codex_turn_id="tu1",
        item_id="i1",
        kind="unknown",
        requested_scope={},
        status="pending",
    )
    pending_request_store_factory.insert(request)
    job = simple_job_factory(
        status="needs_escalation", parked_request_id="r-unknown"
    )
    with pytest.raises(UnknownKindInEscalationProjection):
        delegation_controller._project_pending_escalation(job)


def test_project_pending_escalation_returns_view_on_happy_path(
    delegation_controller: DelegationController,
    simple_job_factory,
    pending_request_store_factory,
) -> None:
    request = PendingServerRequest(
        request_id="r-happy",
        runtime_id="rt1",
        collaboration_id="c1",
        codex_thread_id="t1",
        codex_turn_id="tu1",
        item_id="i1",
        kind="command_approval",
        requested_scope={"cmd": "ls"},
        status="pending",
    )
    pending_request_store_factory.insert(request)
    job = simple_job_factory(
        status="needs_escalation", parked_request_id="r-happy"
    )
    view = delegation_controller._project_pending_escalation(job)
    assert view is not None
    assert view.request_id == "r-happy"
    assert view.kind == "command_approval"
    assert view.requested_scope == {"cmd": "ls"}
```

Assume `delegation_controller`, `simple_job_factory`, and `pending_request_store_factory` fixtures exist in `conftest.py`. If not, add them following existing fixture patterns.

- [ ] **Step 14.2: Run test to verify it fails**

```bash
uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests/test_projection_helpers.py -v
```

Expected: FAIL — `_ESCALATABLE_REQUEST_KINDS` doesn't exist; `_project_request_to_view` doesn't raise; `_project_pending_escalation` takes `collaboration_id`, not `job`.

- [ ] **Step 14.3: Rewrite `_project_request_to_view` with guard**

Edit `packages/plugins/codex-collaboration/server/delegation_controller.py:849-858`:

```python
# Add near the top of the module (after _TERMINAL_STATUS_MAP or similar):
_ESCALATABLE_REQUEST_KINDS: frozenset[str] = frozenset(
    {"command_approval", "file_change", "request_user_input"}
)


# Replace _project_request_to_view at :849-858:
def _project_request_to_view(
    self, request: PendingServerRequest
) -> PendingEscalationView:
    """Project a PendingServerRequest to the caller-visible PendingEscalationView.

    Raises UnknownKindInEscalationProjection if request.kind is not in the
    escalatable set. Under Packet 1, caller control flow should prevent
    this (unknown-kind requests terminalize the job before reaching any
    projection callsite). The runtime guard is a belt-and-suspenders check
    against dynamic construction paths (JSONL replay of pre-Packet-1 records,
    future callsites that bypass the type system).
    """
    if request.kind not in _ESCALATABLE_REQUEST_KINDS:
        raise UnknownKindInEscalationProjection(
            f"EscalatableRequestKind violation: request_id={request.request_id!r} "
            f"kind={request.kind!r:.100}. Under Packet 1, kind='unknown' "
            f"must never reach escalation projection; such jobs are "
            f"terminalized via the Unknown-kind contract."
        )
    return PendingEscalationView(
        request_id=request.request_id,
        kind=request.kind,
        requested_scope=request.requested_scope,
        available_decisions=self._PLUGIN_DECISIONS,
    )
```

- [ ] **Step 14.4: Rewrite `_project_pending_escalation` (job-anchored + tombstone + terminal guard)**

Replace `_project_pending_escalation` at `delegation_controller.py:860-868`:

```python
def _project_pending_escalation(
    self, job: DelegationJob
) -> PendingEscalationView | None:
    """Project a job's parked request into a view. PURE — no side effects.

    Returns None for legitimate no-view states (terminal, unparked,
    tombstone). Re-raises UnknownKindInEscalationProjection for invariant
    violations so each callsite owns its own abort-signaling and rejection
    semantics. The helper never calls signal_internal_abort and never logs
    critical errors; those concerns live at callsites (poll(), start()'s
    escalation-return branch) because the appropriate reason and
    caller-facing response differ between them.
    """
    if job.status in ("completed", "failed", "canceled", "unknown"):
        return None
    if job.parked_request_id is None:
        return None
    request = self._pending_request_store.get(job.parked_request_id)
    if request is None or request.status != "pending":
        return None
    return self._project_request_to_view(request)
```

- [ ] **Step 14.5: Update all callers of `_project_pending_escalation` to pass the `job` object (not `collaboration_id`)**

Current callers in `delegation_controller.py`:
- `poll()` at ~`:925`: `pending_escalation = self._project_pending_escalation(refreshed.collaboration_id)` → `pending_escalation = self._project_pending_escalation(refreshed)`
- `_finalize_turn` (doesn't currently call this helper; the new call lands in Task 19).

Update poll() accordingly (full poll rewrite lands in Task 20 — for now, just change the argument to preserve compile correctness):

```python
if refreshed.status == "needs_escalation":
    pending_escalation = self._project_pending_escalation(refreshed)
```

- [ ] **Step 14.6: Run test to verify it passes**

```bash
uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests/test_projection_helpers.py -v
```

Expected: PASS.

- [ ] **Step 14.7: Commit**

```bash
git add packages/plugins/codex-collaboration/server/delegation_controller.py packages/plugins/codex-collaboration/tests/test_projection_helpers.py
git commit -m "$(cat <<'EOF'
feat(delegate): rewrite projection helpers with guard + job-anchored + tombstone (T-20260423-02 Task 14)

_project_request_to_view now raises UnknownKindInEscalationProjection for
non-escalatable kinds. _project_pending_escalation now takes DelegationJob
(job-anchored, not collaboration-anchored), returns None for terminal jobs
/ unparked jobs / tombstone races (request is pending=False but
parked_request_id not yet cleared), and re-raises unknown-kind from the
inner projector. Callsite-ownership pattern: helpers stay pure; poll() and
start()-escalation branch do their own signal_internal_abort on catch.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

**Phase E complete.** Serialization and projection surfaces are ready. Phase F begins the worker execution model — the largest phase.

---

