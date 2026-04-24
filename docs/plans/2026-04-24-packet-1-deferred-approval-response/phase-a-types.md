# Packet 1 — Phase A: Types

**Parent plan:** [manifest](../2026-04-24-packet-1-deferred-approval-response.md)
**Tasks:** 1–5
**Scope:** Canceled-status type expansion, escalatable-request-kind narrowing, sanitization helper, exception types (`DelegationStartError`, `UnknownKindInEscalationProjection`), worker sentinel `_WorkerTerminalBranchSignal`.
**Landing invariant:** All new types, literals, and exception classes compile and round-trip.

---

## Task 1: JobStatus and DelegationTerminalStatus expansion (add `"canceled"`)

**Files:**
- Modify: `packages/plugins/codex-collaboration/server/models.py:21-23, 36`
- Modify: `packages/plugins/codex-collaboration/server/delegation_controller.py:104-108`
- Test: `packages/plugins/codex-collaboration/tests/test_models_canceled_status.py` (new file, created by Step 1.1)

**Spec anchor:** §JobStatus='canceled' propagation (spec lines ~1334-1412). C1-A row 1 (`JobStatus`) and row 2 (`DelegationTerminalStatus`) land here; remaining rows land in later tasks.

- [ ] **Step 1.1: Write the failing test**

Create `packages/plugins/codex-collaboration/tests/test_models_canceled_status.py`:

```python
"""Packet 1: JobStatus + DelegationTerminalStatus + _TERMINAL_STATUS_MAP admit canceled."""

from __future__ import annotations

from typing import get_args

from codex_collaboration.server.delegation_controller import _TERMINAL_STATUS_MAP
from codex_collaboration.server.models import DelegationTerminalStatus, JobStatus


def test_job_status_admits_canceled() -> None:
    assert "canceled" in get_args(JobStatus)


def test_delegation_terminal_status_admits_canceled() -> None:
    assert "canceled" in get_args(DelegationTerminalStatus)


def test_terminal_status_map_maps_canceled_to_canceled() -> None:
    assert _TERMINAL_STATUS_MAP.get("canceled") == "canceled"


def test_terminal_status_map_has_four_entries_post_packet_1() -> None:
    assert set(_TERMINAL_STATUS_MAP.keys()) == {"completed", "failed", "canceled", "unknown"}
```

- [ ] **Step 1.2: Run test to verify it fails**

```bash
uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests/test_models_canceled_status.py -v
```

Expected: 4 FAILs with `AssertionError` — the literals and map entry are absent pre-Packet-1.

- [ ] **Step 1.3: Expand `JobStatus` literal**

Edit `packages/plugins/codex-collaboration/server/models.py:21-23`:

```python
# Before:
JobStatus = Literal[
    "queued", "running", "needs_escalation", "completed", "failed", "unknown"
]

# After:
JobStatus = Literal[
    "queued",
    "running",
    "needs_escalation",
    "completed",
    "failed",
    "canceled",
    "unknown",
]
```

- [ ] **Step 1.4: Expand `DelegationTerminalStatus` literal**

Edit `packages/plugins/codex-collaboration/server/models.py:36`:

```python
# Before:
DelegationTerminalStatus = Literal["completed", "failed", "unknown"]

# After:
DelegationTerminalStatus = Literal["completed", "failed", "canceled", "unknown"]
```

- [ ] **Step 1.5: Add `"canceled": "canceled"` to `_TERMINAL_STATUS_MAP`**

Edit `packages/plugins/codex-collaboration/server/delegation_controller.py:104-108`:

```python
# Before:
_TERMINAL_STATUS_MAP: dict[str, DelegationTerminalStatus] = {
    "completed": "completed",
    "failed": "failed",
    "unknown": "unknown",
}

# After:
_TERMINAL_STATUS_MAP: dict[str, DelegationTerminalStatus] = {
    "completed": "completed",
    "failed": "failed",
    "canceled": "canceled",
    "unknown": "unknown",
}
```

- [ ] **Step 1.6: Run test to verify it passes**

```bash
uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests/test_models_canceled_status.py -v
```

Expected: 4 PASS.

- [ ] **Step 1.7: Verify `_VALID_STATUSES` derivation auto-picks up the new literal**

```bash
uv run --package codex-collaboration python -c "from codex_collaboration.server.delegation_job_store import _VALID_STATUSES; assert 'canceled' in _VALID_STATUSES, _VALID_STATUSES; print('OK')"
```

Expected: `OK`. The `get_args(JobStatus)` call at `delegation_job_store.py:17` derives `_VALID_STATUSES` from the Literal, so adding to the Literal auto-widens the validator without a separate edit.

- [ ] **Step 1.8: Commit**

```bash
git add packages/plugins/codex-collaboration/server/models.py packages/plugins/codex-collaboration/server/delegation_controller.py packages/plugins/codex-collaboration/tests/test_models_canceled_status.py
git commit -m "$(cat <<'EOF'
feat(delegate): expand JobStatus/DelegationTerminalStatus with canceled (T-20260423-02 Task 1)

Adds "canceled" to JobStatus (6 → 7 literals), DelegationTerminalStatus
(3 → 4 literals), and _TERMINAL_STATUS_MAP (3 → 4 entries). Downstream
propagation (discard gate, list_user_attention_required, contracts.md
enums, projection terminal guards) lands in subsequent tasks per the
JobStatus='canceled' propagation table in the spec.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: EscalatableRequestKind + PendingEscalationView.kind narrowing

**Files:**
- Modify: `packages/plugins/codex-collaboration/server/models.py` (add literal, narrow field, after existing `PendingRequestKind` at `:16-18`)
- Test: `packages/plugins/codex-collaboration/tests/test_models_escalatable_kind.py` (new)

**Spec anchor:** §EscalatableRequestKind (new literal) + `PendingEscalationView.kind` narrowing (spec lines ~1451-1475).

- [ ] **Step 2.1: Write the failing test**

Create `packages/plugins/codex-collaboration/tests/test_models_escalatable_kind.py`:

```python
"""Packet 1: EscalatableRequestKind narrows PendingEscalationView.kind to 3 literals."""

from __future__ import annotations

from typing import get_args, get_type_hints

from codex_collaboration.server.models import (
    EscalatableRequestKind,
    PendingEscalationView,
    PendingRequestKind,
)


def test_escalatable_kind_has_three_literals() -> None:
    assert set(get_args(EscalatableRequestKind)) == {
        "command_approval",
        "file_change",
        "request_user_input",
    }


def test_escalatable_kind_excludes_unknown() -> None:
    assert "unknown" not in get_args(EscalatableRequestKind)


def test_pending_request_kind_unchanged() -> None:
    # PendingRequestKind is still the 4-literal persisted kind; unknown is a
    # valid persisted kind (parse-failure audit record) but NOT escalatable.
    assert set(get_args(PendingRequestKind)) == {
        "command_approval",
        "file_change",
        "request_user_input",
        "unknown",
    }


def test_pending_escalation_view_kind_narrowed() -> None:
    hints = get_type_hints(PendingEscalationView)
    assert hints["kind"] is EscalatableRequestKind
```

- [ ] **Step 2.2: Run test to verify it fails**

```bash
uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests/test_models_escalatable_kind.py -v
```

Expected: FAIL — `EscalatableRequestKind` does not exist.

- [ ] **Step 2.3: Add `EscalatableRequestKind` literal**

Edit `packages/plugins/codex-collaboration/server/models.py`. After the `PendingRequestKind` definition at `:16-18`, add:

```python
# PendingRequestKind stays 4 literals — "unknown" is still a valid PERSISTED kind
# (parse-failure audit record). EscalatableRequestKind is the narrower subset
# that may appear in PendingEscalationView. Under Packet 1, kind="unknown"
# terminalizes the job before reaching any escalation projection.
EscalatableRequestKind = Literal[
    "command_approval",
    "file_change",
    "request_user_input",
]
```

- [ ] **Step 2.4: Narrow `PendingEscalationView.kind`**

Edit `packages/plugins/codex-collaboration/server/models.py:441-452`:

```python
@dataclass(frozen=True)
class PendingEscalationView:
    """Projected view of a pending escalation for poll results.

    Minimal subset of PendingServerRequest fields needed by the caller
    to render an escalation prompt. Does not carry internal correlation
    ids (codex_thread_id, codex_turn_id, item_id).
    """

    request_id: str
    kind: EscalatableRequestKind
    requested_scope: dict[str, Any]
    available_decisions: tuple[str, ...] = ()
```

- [ ] **Step 2.5: Run test to verify it passes**

```bash
uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests/test_models_escalatable_kind.py -v
```

Expected: 4 PASS.

- [ ] **Step 2.6: Commit**

```bash
git add packages/plugins/codex-collaboration/server/models.py packages/plugins/codex-collaboration/tests/test_models_escalatable_kind.py
git commit -m "$(cat <<'EOF'
feat(delegate): narrow PendingEscalationView.kind via EscalatableRequestKind (T-20260423-02 Task 2)

Introduces EscalatableRequestKind = Literal["command_approval",
"file_change", "request_user_input"] and retypes
PendingEscalationView.kind to exclude "unknown". PendingRequestKind stays
unchanged at 4 literals — unknown-kind requests remain valid persisted
audit records but can no longer surface through escalation projection.
The runtime guard enforcing this narrowing lands in Task 14
(_project_request_to_view rewrite).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Sanitization helper for forensic error-string fields

**Files:**
- Modify: `packages/plugins/codex-collaboration/server/delegation_controller.py` (add module-private helper near the top, after `_TERMINAL_STATUS_MAP`)
- Test: `packages/plugins/codex-collaboration/tests/test_delegation_sanitization.py` (new)

**Spec anchor:** §Sanitization rules for error-string fields (spec lines ~2118-2137).

- [ ] **Step 3.1: Write the failing test**

Create `packages/plugins/codex-collaboration/tests/test_delegation_sanitization.py`:

```python
"""Packet 1: _sanitize_error_string bounds & class-prefix format for forensic fields."""

from __future__ import annotations

import pytest

from codex_collaboration.server.delegation_controller import _sanitize_error_string


def test_sanitize_class_prefix_and_message() -> None:
    exc = RuntimeError("boom")
    assert _sanitize_error_string(exc) == "RuntimeError: boom"


def test_sanitize_truncates_message_at_200_chars_with_ellipsis() -> None:
    exc = RuntimeError("x" * 400)
    out = _sanitize_error_string(exc)
    # Message portion is truncated to 200 chars + "..." suffix
    assert out.startswith("RuntimeError: ")
    message_portion = out[len("RuntimeError: ") :]
    assert message_portion.endswith("...")
    assert len(message_portion) == 203  # 200 chars + "..."


def test_sanitize_strips_newlines_and_control_chars() -> None:
    exc = RuntimeError("line1\nline2\tcolumn")
    out = _sanitize_error_string(exc)
    assert "\n" not in out
    assert "\t" not in out
    assert "\\n" in out
    assert "\\t" in out


def test_sanitize_caps_total_at_256_chars() -> None:
    # Over-long class name triggers the combined cap.
    class ExceptionClassWithAVeryVeryVeryVeryLongName(RuntimeError):
        pass

    exc = ExceptionClassWithAVeryVeryVeryVeryLongName("x" * 400)
    out = _sanitize_error_string(exc)
    assert len(out) <= 256


def test_sanitize_handles_short_message_without_truncation() -> None:
    exc = BrokenPipeError("broken")
    assert _sanitize_error_string(exc) == "BrokenPipeError: broken"
```

- [ ] **Step 3.2: Run test to verify it fails**

```bash
uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests/test_delegation_sanitization.py -v
```

Expected: FAIL — `_sanitize_error_string` does not exist.

- [ ] **Step 3.3: Implement `_sanitize_error_string`**

Edit `packages/plugins/codex-collaboration/server/delegation_controller.py`. Add after `_TERMINAL_STATUS_MAP` at `:108`:

```python
_SANITIZE_MESSAGE_CAP = 200
_SANITIZE_TOTAL_CAP = 256


def _sanitize_error_string(exc: BaseException) -> str:
    """Produce a bounded, JSONL-safe forensic string for persistence.

    Format: "<ExceptionClassName>: <bounded, escaped message>". Used by the
    three PendingServerRequest forensic fields (dispatch_error,
    interrupt_error, internal_abort_reason). Per spec §Sanitization rules:
    message truncated at 200 chars with "..." elision, newlines/tabs escaped,
    total length bounded at 256 chars. A too-long class name triggers a
    further truncation and a warning log.
    """
    class_name = type(exc).__name__
    raw = str(exc)
    if len(raw) > _SANITIZE_MESSAGE_CAP:
        message = raw[:_SANITIZE_MESSAGE_CAP] + "..."
    else:
        message = raw
    # Escape newlines, tabs, and other control characters so the final string
    # is a single JSONL-safe line. encode/decode(unicode_escape) preserves
    # regular content while quoting control characters as \n, \t, etc.
    message = message.encode("unicode_escape").decode("ascii")
    combined = f"{class_name}: {message}"
    if len(combined) > _SANITIZE_TOTAL_CAP:
        logger.warning(
            "Forensic string exceeded total cap; truncating. class=%r len=%d",
            class_name,
            len(combined),
        )
        combined = combined[:_SANITIZE_TOTAL_CAP]
    return combined
```

- [ ] **Step 3.4: Run test to verify it passes**

```bash
uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests/test_delegation_sanitization.py -v
```

Expected: 5 PASS.

- [ ] **Step 3.5: Commit**

```bash
git add packages/plugins/codex-collaboration/server/delegation_controller.py packages/plugins/codex-collaboration/tests/test_delegation_sanitization.py
git commit -m "$(cat <<'EOF'
feat(delegate): add _sanitize_error_string helper for forensic fields (T-20260423-02 Task 3)

Module-private helper that produces bounded, JSONL-safe forensic strings
for dispatch_error, interrupt_error, and internal_abort_reason fields.
Class-prefix format, 200-char message cap with ellipsis, newline escape,
256-char combined cap. Per spec §Sanitization rules.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: Exception types (DelegationStartError + UnknownKindInEscalationProjection)

**Files:**
- Modify: `packages/plugins/codex-collaboration/server/delegation_controller.py` (add exception classes after `_sanitize_error_string`)
- Test: `packages/plugins/codex-collaboration/tests/test_delegation_exceptions.py` (new)

**Spec anchor:** §Exception classes introduced by Packet 1 (spec lines ~568-620).

- [ ] **Step 4.1: Write the failing test**

Create `packages/plugins/codex-collaboration/tests/test_delegation_exceptions.py`:

```python
"""Packet 1: DelegationStartError + UnknownKindInEscalationProjection exception types."""

from __future__ import annotations

import pytest

from codex_collaboration.server.delegation_controller import (
    DelegationStartError,
    UnknownKindInEscalationProjection,
)


def test_delegation_start_error_is_runtime_error_subclass() -> None:
    exc = DelegationStartError(reason="worker_failed_before_capture")
    assert isinstance(exc, RuntimeError)


def test_delegation_start_error_str_is_reason_alone_when_no_message() -> None:
    assert str(DelegationStartError(reason="foo")) == "foo"


def test_delegation_start_error_str_is_reason_colon_message_when_set() -> None:
    assert str(DelegationStartError(reason="foo", message="bar")) == "foo: bar"


def test_delegation_start_error_preserves_cause_and_dunder_cause() -> None:
    original = ValueError("original")
    try:
        raise DelegationStartError(reason="foo", cause=original) from original
    except DelegationStartError as exc:
        assert exc.cause is original
        assert exc.__cause__ is original


def test_delegation_start_error_reason_is_attribute() -> None:
    exc = DelegationStartError(reason="parked_projection_invariant_violation")
    assert exc.reason == "parked_projection_invariant_violation"


def test_unknown_kind_in_escalation_projection_is_exception_not_runtime_error() -> None:
    # Must NOT be RuntimeError subclass so narrower except clauses don't
    # swallow it through the RuntimeError branch.
    exc = UnknownKindInEscalationProjection("msg")
    assert isinstance(exc, Exception)
    assert not isinstance(exc, RuntimeError)


def test_unknown_kind_exception_carries_message() -> None:
    exc = UnknownKindInEscalationProjection("kind=unknown request_id=abc")
    assert str(exc) == "kind=unknown request_id=abc"
```

- [ ] **Step 4.2: Run test to verify it fails**

```bash
uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests/test_delegation_exceptions.py -v
```

Expected: FAIL — exception types don't exist.

- [ ] **Step 4.3: Implement exception types**

Edit `packages/plugins/codex-collaboration/server/delegation_controller.py`. Add after `_sanitize_error_string`:

```python
class DelegationStartError(RuntimeError):
    """Raised by start() when the delegation-start sequence cannot produce
    a successful return value. The reason literal is part of the public
    plugin contract — see §DelegationStartError reasons in the spec.

    __str__ contract: "{reason}: {message}" when message is non-empty,
    else "{reason}". This guarantees MCP text-prefix recoverability
    without requiring a boundary change.

    Raise idiom for cases with a chained cause:
        raise DelegationStartError(reason=..., cause=exc) from exc
    so Python's __cause__ chain is preserved alongside the explicit .cause
    field. Duplication is intentional: __cause__ participates in
    tracebacks; .cause is the typed attribute callers can read without
    walking __cause__.
    """

    reason: str
    cause: Exception | None

    def __init__(
        self,
        *,
        reason: str,
        cause: Exception | None = None,
        message: str = "",
    ) -> None:
        if message:
            super().__init__(f"{reason}: {message}")
        else:
            super().__init__(reason)
        self.reason = reason
        self.cause = cause


class UnknownKindInEscalationProjection(Exception):
    """Raised by _project_request_to_view when request.kind is not in
    EscalatableRequestKind. Internal assertion signal — MUST NOT escape the
    controller boundary.

    Subclass of Exception (NOT RuntimeError) so narrower except clauses
    catch it before a generic `except RuntimeError`. Carries only a
    message; the callsite determines the abort reason.
    """

    pass
```

- [ ] **Step 4.4: Run test to verify it passes**

```bash
uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests/test_delegation_exceptions.py -v
```

Expected: 7 PASS.

- [ ] **Step 4.5: Commit**

```bash
git add packages/plugins/codex-collaboration/server/delegation_controller.py packages/plugins/codex-collaboration/tests/test_delegation_exceptions.py
git commit -m "$(cat <<'EOF'
feat(delegate): add DelegationStartError + UnknownKindInEscalationProjection (T-20260423-02 Task 4)

DelegationStartError is the public terminal-failure boundary for start(),
with a text-prefix recoverable serialization ("reason: message"). Carries
typed .reason and .cause attributes.

UnknownKindInEscalationProjection is an internal assertion signal raised
by the projection helper; NOT a RuntimeError subclass so narrower except
clauses handle it before generic RuntimeError catches.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: `_WorkerTerminalBranchSignal` private sentinel exception

**Files:**
- Modify: `packages/plugins/codex-collaboration/server/delegation_controller.py` (add after exception types from Task 4)
- Test: `packages/plugins/codex-collaboration/tests/test_worker_terminal_branch_signal.py` (new)

**Spec anchor:** §Worker terminal-branch signaling primitive (spec lines ~441-567). Six call sites with distinct `reason` literals; implementation of raise sites lands in Task 16, catch site in Task 15.

- [ ] **Step 5.1: Write the failing test**

Create `packages/plugins/codex-collaboration/tests/test_worker_terminal_branch_signal.py`:

```python
"""Packet 1: _WorkerTerminalBranchSignal frozen-dataclass exception carrying reason."""

from __future__ import annotations

import pytest

from codex_collaboration.server.delegation_controller import (
    _WorkerTerminalBranchSignal,
)


def test_is_exception_subclass() -> None:
    assert issubclass(_WorkerTerminalBranchSignal, Exception)


def test_carries_reason_field() -> None:
    signal = _WorkerTerminalBranchSignal(reason="internal_abort")
    assert signal.reason == "internal_abort"


def test_accepts_all_six_spec_reasons() -> None:
    for reason in (
        "internal_abort",
        "dispatch_failed",
        "timeout_interrupt_failed",
        "timeout_interrupt_succeeded",
        "timeout_cancel_dispatch_failed",
        "unknown_kind_interrupt_transport_failure",
    ):
        signal = _WorkerTerminalBranchSignal(reason=reason)
        assert signal.reason == reason


def test_is_raisable_and_catchable() -> None:
    with pytest.raises(_WorkerTerminalBranchSignal) as exc_info:
        raise _WorkerTerminalBranchSignal(reason="dispatch_failed")
    assert exc_info.value.reason == "dispatch_failed"


def test_does_not_propagate_through_runtime_error_except() -> None:
    # _WorkerTerminalBranchSignal is not RuntimeError — a narrower except
    # clause above `except Exception` must be placed to catch it before
    # the generic _mark_execution_unknown_and_cleanup handler fires.
    with pytest.raises(_WorkerTerminalBranchSignal):
        try:
            raise _WorkerTerminalBranchSignal(reason="internal_abort")
        except RuntimeError:  # would incorrectly swallow if it were RuntimeError
            pytest.fail("sentinel must not be caught by RuntimeError handler")
```

- [ ] **Step 5.2: Run test to verify it fails**

```bash
uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests/test_worker_terminal_branch_signal.py -v
```

Expected: FAIL — `_WorkerTerminalBranchSignal` does not exist.

- [ ] **Step 5.3: Implement `_WorkerTerminalBranchSignal`**

Edit `packages/plugins/codex-collaboration/server/delegation_controller.py`. Add after `UnknownKindInEscalationProjection`:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class _WorkerTerminalBranchSignal(Exception):
    """Private sentinel raised by the server-request handler to terminalize
    the worker turn after the branch's own cleanup has already run.

    The handler raises this AFTER performing its branch's own cleanup:
      - writing any final approval_resolution.completed record
      - calling update_parked_request(job_id, None)
      - discarding the per-request registry entry
      - calling _mark_execution_unknown_and_cleanup (closes session, marks job)
      (or the timeout-success analog: _persist_job_transition(..., "canceled"))

    Caught in _execute_live_turn's new except clause BEFORE the generic
    except Exception; MUST NOT escape _execute_live_turn as a raw exception
    or be caught by the worker runner — doing so would produce
    announce_worker_failed for a handler-terminalized branch.

    Six call sites with distinct reason literals per spec §Worker
    terminal-branch signaling primitive — see the table at "Where it is
    raised."
    """

    reason: str
```

Note: the `from dataclasses import dataclass` import is already present at the top of delegation_controller.py (line 11 imports `from typing import Any, Callable, Protocol` — add `dataclass` to existing imports if not imported from `dataclasses` yet). If it is NOT already imported, add `from dataclasses import dataclass` near the top-of-file imports.

Before committing, verify the dataclass import is clean:

```bash
uv run --package codex-collaboration python -c "from codex_collaboration.server.delegation_controller import _WorkerTerminalBranchSignal; print(_WorkerTerminalBranchSignal(reason='ok').reason)"
```

Expected: `ok`.

- [ ] **Step 5.4: Run test to verify it passes**

```bash
uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests/test_worker_terminal_branch_signal.py -v
```

Expected: 5 PASS.

- [ ] **Step 5.5: Commit**

```bash
git add packages/plugins/codex-collaboration/server/delegation_controller.py packages/plugins/codex-collaboration/tests/test_worker_terminal_branch_signal.py
git commit -m "$(cat <<'EOF'
feat(delegate): add _WorkerTerminalBranchSignal sentinel exception (T-20260423-02 Task 5)

Private frozen-dataclass exception carrying a reason literal. The
handler raises this after performing branch-specific cleanup to
terminalize the worker turn without propagating through the generic
except Exception branch (which would double-clean + mask the
handler-owned terminalization via announce_worker_failed).

Catch site in _execute_live_turn + six raise sites inside the handler
land in subsequent tasks. Six spec-defined reasons round-trip cleanly.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

**Phase A complete.** All new types, literals, and exception classes are in place. At this point the tree compiles, prior tests still pass (`uv run --package codex-collaboration pytest` should be green), and no behavior has changed. Phase B begins with the store-layer field additions and mutators.

---

