# T-05 Pending-Request Capture Slice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close AC 6 — execution-domain server requests are surfaced through an approval-routing layer rather than being silently auto-approved.

**Architecture:** Extend `codex.delegate.start` to accept an execution objective, dispatch the first execution turn with a non-`"never"` approval policy, and intercept App Server server requests during the notification loop. Three response strategies by request kind: (a) cancel-capable requests (command/file approvals) get `{"decision": "cancel"}`; (b) known no-cancel requests (user-input) get minimal denial; (c) unknown/unparseable requests trigger `turn/interrupt` (fail closed per `recovery-and-journal.md:134`). Captured requests are persisted via a new `PendingRequestStore` and the start call returns a typed `DelegationEscalation` with the causal record, job state, and optional agent context.

**Tech Stack:** Python 3.12+, pytest, JSONL persistence (append-only replay pattern), JSON-RPC 2.0 over stdio.

**Baseline:** 666 tests passing on `main` at `5ee7afb4`.

---

## Key Design Decisions (Frozen)

These decisions were reached through collaborative analysis and are NOT open for re-evaluation during implementation.

| # | Decision | Rationale |
|---|---|---|
| D1 | `approvalPolicy` is probe-gated | Use `untrusted` for first proof if needed. Narrow to `on-request` only after live probe confirms prompt behavior. Vendored schema proves allowed values, not operational semantics. |
| D2 | First execution turn is intentionally unjournaled | Explicit deferral. `job_creation.completed` means "all durable start writes landed." Turn dispatch happens after journal is terminal. A crash during the first-turn window leaves the job persisted as `running` with no replay anchor — `recover_startup()` reconciles this via orphaned-running-job detection (see Task 6). Turn-dispatch journaling (with its own idempotency key) lands with T-06. |
| D3 | Three capture strategies by request kind | (a) Cancel-capable (command/file): `{"decision": "cancel"}` — turn interrupts. (b) Known no-cancel (user-input): minimal denial — turn continues. (c) Unknown/unparseable (permissions, unrecognized methods, parse failures): `turn/interrupt` — fail closed per `recovery-and-journal.md:134`. Universal `cancel` is NOT available across all request kinds. |
| D4 | `PendingServerRequest.status` is wire lifecycle for parsed requests | Per spec at `recovery-and-journal.md:125-127`. For normally-parsed requests, status is `"resolved"` after capture (wire request responded to and confirmed by `serverRequest/resolved`). Parse-failure causal records (D9) are created with `status="pending"` and are NOT updated to `"resolved"` — they have no wire request that can be confirmed. Plugin escalation tracked by `DelegationJob.status`. |
| D5 | No structured output schema for execution turns | The "output" is worktree state + server requests, not a JSON blob. `_run_turn()` must make `outputSchema` optional. |
| D6 | Three-signal diagnostic after cancel | `serverRequest/resolved` + `item/completed` (target itemId) + `turn/completed` are all authoritative protocol boundaries. State derivation uses `turn/completed` status as the terminal signal. After the loop exits, `_verify_post_turn_signals()` checks `turn_result.notifications` for matching `serverRequest/resolved` and target `item/completed` and logs warnings if missing. This is **diagnostic-only observability**, not a state-derivation gate — missing signals do not block terminal state transitions. |
| D7 | Agent context is best-effort from authoritative completed items only | Nullable `agent_context` field on `DelegationEscalation`. Only `item/completed` with `type: "agentMessage"`, no delta scraping. |
| D8 | `DelegationEscalation` is a third typed start result | Not bolted onto `DelegationJob`. Separates persisted lifecycle state from transient escalation state. |
| D9 | `request_id` is the normalized wire id, not plugin-generated | The App Server wire `RequestId` (string or integer) is normalized to string at the parse boundary and used directly as `PendingServerRequest.request_id`. This preserves wire correlation for `serverRequest/resolved` matching and D6 diagnostics. The contract at `contracts.md:81` currently says "plugin-assigned unique identifier" — this slice amends that to "wire request id, normalized to string by the plugin." Parse-failure causal records may use a plugin-generated fallback id when the raw message has no usable `id`; these are NOT wire-correlated and D4 does not apply to them. |

---

## File Structure

### New Files

| File | Responsibility |
|---|---|
| `server/pending_request_store.py` | JSONL persistence for `PendingServerRequest` records. Mirrors `DelegationJobStore` pattern. |
| `server/execution_prompt_builder.py` | Execution-turn prompt construction. Minimal — conveys objective + worktree scope. |
| `tests/test_pending_request_store.py` | Store CRUD + replay validation tests. |
| `tests/test_execution_prompt_builder.py` | Prompt construction tests. |
| `tests/test_jsonrpc_respond.py` | JSON-RPC `respond()` and server-request discrimination tests. |

### Modified Files

| File | Changes |
|---|---|
| `server/jsonrpc_client.py` | Add `respond(request_id, result)` method. |
| `server/models.py` | Add `TurnStatus` type alias. Add `status` field to `TurnExecutionResult`. Add `DelegationEscalation` dataclass. |
| `server/runtime.py` | Make `output_schema` optional. Add `approval_policy` parameter. Add `server_request_handler` callback. Accept `interrupted`/`failed` terminal states. |
| `server/delegation_controller.py` | Add `objective` parameter. Implement capture loop. Job status transitions. Audit emission. Terminal runtime cleanup. Startup orphan reconciliation for `running` jobs. |
| `server/approval_router.py` | Accept `str | int` wire request IDs and normalize to `str` at parse boundary (contract: `request_id` is `string`). |
| `server/delegation_job_store.py` | No changes — `update_status()` already supports any `JobStatus` including `"needs_escalation"`. |
| `server/mcp_server.py` | Update tool definition. Handle three return types. |
| `server/__init__.py` | Export `DelegationEscalation`, `PendingRequestStore`. |
| `tests/test_delegation_controller.py` | Capture loop unit tests. |
| `tests/test_mcp_server.py` | Updated tool dispatch tests. |
| `tests/test_delegate_start_integration.py` | E2E integration tests. |
| `tests/test_runtime.py` | Turn-widening tests. |

---

## Task 1: JSON-RPC Server-Request Response Primitive

**Files:**
- Modify: `server/jsonrpc_client.py`
- Create: `tests/test_jsonrpc_respond.py`

This task adds the ability to respond to server-initiated requests. Currently `JsonRpcClient` can only send client-initiated requests — it has no API for replying to messages that have both `id` and `method` (server requests).

---

- [ ] **Step 1.1: Write test for `respond()` method**

Create `tests/test_jsonrpc_respond.py`:

```python
"""Tests for JsonRpcClient server-request response support."""

from __future__ import annotations

import json
import subprocess
import threading
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from server.jsonrpc_client import JsonRpcClient


class TestRespond:
    """Tests for JsonRpcClient.respond()."""

    def test_respond_writes_jsonrpc_response_to_stdin(self) -> None:
        """respond() sends a JSON-RPC 2.0 response with the given request_id and result."""
        client = JsonRpcClient(["echo"], cwd=Path("/tmp"))
        mock_process = MagicMock()
        mock_stdin = MagicMock()
        mock_process.stdin = mock_stdin
        client._process = mock_process

        client.respond("req-42", {"decision": "cancel"})

        written = mock_stdin.write.call_args[0][0]
        payload = json.loads(written.strip())
        assert payload == {
            "jsonrpc": "2.0",
            "id": "req-42",
            "result": {"decision": "cancel"},
        }
        mock_stdin.flush.assert_called_once()

    def test_respond_with_integer_request_id(self) -> None:
        """respond() preserves integer request IDs (JSON-RPC allows string or int)."""
        client = JsonRpcClient(["echo"], cwd=Path("/tmp"))
        mock_process = MagicMock()
        mock_stdin = MagicMock()
        mock_process.stdin = mock_stdin
        client._process = mock_process

        client.respond(7, {"permissions": {}})

        written = mock_stdin.write.call_args[0][0]
        payload = json.loads(written.strip())
        assert payload["id"] == 7

    def test_respond_raises_if_not_started(self) -> None:
        """respond() raises RuntimeError if called before start()."""
        client = JsonRpcClient(["echo"], cwd=Path("/tmp"))

        with pytest.raises(RuntimeError, match="not started"):
            client.respond("req-1", {})

    def test_respond_raises_on_broken_pipe(self) -> None:
        """respond() wraps BrokenPipeError with context."""
        client = JsonRpcClient(["echo"], cwd=Path("/tmp"))
        mock_process = MagicMock()
        mock_stdin = MagicMock()
        mock_stdin.write.side_effect = BrokenPipeError()
        mock_process.stdin = mock_stdin
        client._process = mock_process

        with pytest.raises(RuntimeError, match="broken stdin pipe"):
            client.respond("req-1", {})
```

- [ ] **Step 1.2: Run test to verify it fails**

Run:
```bash
cd packages/plugins/codex-collaboration && uv run pytest tests/test_jsonrpc_respond.py -v
```
Expected: FAIL — `JsonRpcClient` has no `respond` method.

- [ ] **Step 1.3: Implement `respond()` method**

In `server/jsonrpc_client.py`, add after the `request()` method (after line 104):

```python
def respond(self, request_id: str | int, result: dict[str, Any]) -> None:
    """Send a JSON-RPC 2.0 response to a server-initiated request.

    Server requests arrive as messages with both ``id`` and ``method``
    fields. This method sends the response back to the subprocess so
    the App Server can continue processing.
    """
    if self._process is None:
        raise RuntimeError(
            "JSON-RPC respond failed: client not started"
        )
    assert self._process.stdin is not None
    payload = {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": result,
    }
    try:
        self._process.stdin.write(json.dumps(payload) + "\n")
        self._process.stdin.flush()
    except BrokenPipeError as exc:
        raise RuntimeError(
            "JSON-RPC respond failed: broken stdin pipe. "
            f"Got: request_id={request_id!r:.100}"
        ) from exc
```

- [ ] **Step 1.4: Run test to verify it passes**

Run:
```bash
cd packages/plugins/codex-collaboration && uv run pytest tests/test_jsonrpc_respond.py -v
```
Expected: 4 passed.

- [ ] **Step 1.5: Fix `_require_string` in `approval_router.py` to accept integer request IDs**

The JSON-RPC `RequestId` schema is `anyOf [string, integer]` (`ServerRequest.json:1475`). The parser's `_require_string(message, "id")` rejects integer IDs. Add a dedicated extractor for request IDs.

In `server/approval_router.py`, add after `_require_string` (after line 80):

```python
def _require_request_id(payload: dict[str, Any], key: str) -> str:
    """Extract a JSON-RPC request ID, normalizing to string.

    The wire ``RequestId`` is ``anyOf [string, integer]`` per the App
    Server schema (``ServerRequest.json:1475``). The plugin normalizes
    to string at the parse boundary (D9). The stored ``request_id`` is
    the wire request id in string form — used for ``serverRequest/resolved``
    correlation and D6 diagnostics. The ``respond()`` transport layer
    preserves the original wire type for the response.
    """
    value = payload.get(key)
    if not isinstance(value, (str, int)):
        raise RuntimeError(
            f"Server request parse failed: missing {key}. Got: {value!r:.100}"
        )
    return str(value)
```

Then update `parse_pending_server_request` to use it:

```python
    request_id = _require_request_id(message, "id")
```

`PendingServerRequest.request_id` stays `str` — the normalization happens at parse time. The `respond()` method on `JsonRpcClient` still accepts `str | int` because it writes to the wire, where the original type matters.

Add a test in `tests/test_approval_router.py`:

```python
def test_parse_integer_request_id_normalized_to_string() -> None:
    """Integer request IDs are accepted and normalized to string."""
    message = {
        "id": 42,
        "method": "item/commandExecution/requestApproval",
        "params": {
            "itemId": "item-1",
            "threadId": "thr-1",
            "turnId": "turn-1",
            "command": "echo hello",
            "cwd": "/repo",
        },
    }
    result = parse_pending_server_request(
        message, runtime_id="rt-1", collaboration_id="collab-1"
    )
    assert result.request_id == "42"  # Normalized to string
    assert result.kind == "command_approval"
```

- [ ] **Step 1.6: Run full suite to verify no regressions**

Run:
```bash
cd packages/plugins/codex-collaboration && uv run pytest -x -q
```
Expected: 671+ passed (666 existing + new).

- [ ] **Step 1.7: Commit**

```bash
git add packages/plugins/codex-collaboration/server/jsonrpc_client.py packages/plugins/codex-collaboration/server/approval_router.py packages/plugins/codex-collaboration/server/models.py packages/plugins/codex-collaboration/tests/test_jsonrpc_respond.py packages/plugins/codex-collaboration/tests/test_approval_router.py
git commit -m "feat(t20260330-05): add JsonRpcClient.respond() + accept integer request IDs"
```

---

## Task 2: Turn Status/Result Widening

**Files:**
- Modify: `server/models.py`
- Modify: `server/runtime.py`
- Modify: `tests/test_runtime.py`

Currently `_run_turn()` raises unless `turn.status == "completed"`, and `TurnExecutionResult` has no status field. This task makes `interrupted` and `failed` first-class terminal outcomes.

---

- [ ] **Step 2.1: Add `TurnStatus` type and `status` field to `TurnExecutionResult`**

In `server/models.py`, add after line 11 (after existing type aliases):

```python
TurnStatus = Literal["completed", "interrupted", "failed"]
```

Modify the `TurnExecutionResult` dataclass at line 122 to include the status field:

```python
@dataclass(frozen=True)
class TurnExecutionResult:
    """Projected result of a single `turn/start` execution."""

    turn_id: str
    status: TurnStatus
    agent_message: str
    notifications: tuple[dict[str, Any], ...] = ()
```

- [ ] **Step 2.2: Write test for `_run_turn()` with interrupted status**

Add to `tests/test_runtime.py`:

```python
def test_run_turn_accepts_interrupted_status_when_allowed(
    fake_server_process: FakeServerProcess,
) -> None:
    """Execution turns accept interrupted as a valid terminal status."""
    fake_server_process.queue_response(
        "turn/start",
        {"turn": {"id": "t1", "status": "inProgress", "items": []}},
    )
    fake_server_process.queue_notification(
        "turn/completed",
        {
            "threadId": "thr-1",
            "turn": {"id": "t1", "status": "interrupted", "items": []},
        },
    )
    session = AppServerRuntimeSession(repo_root=Path("/repo"))
    session._client = fake_server_process.client

    result = session.run_execution_turn(
        thread_id="thr-1",
        prompt_text="do work",
        sandbox_policy={"type": "workspaceWrite"},
        approval_policy="on-request",
    )

    assert result.status == "interrupted"
    assert result.turn_id == "t1"
```

```python
def test_run_turn_accepts_failed_status_when_allowed(
    fake_server_process: FakeServerProcess,
) -> None:
    """Execution turns accept failed as a valid terminal status."""
    fake_server_process.queue_response(
        "turn/start",
        {"turn": {"id": "t1", "status": "inProgress", "items": []}},
    )
    fake_server_process.queue_notification(
        "turn/completed",
        {
            "threadId": "thr-1",
            "turn": {"id": "t1", "status": "failed", "items": [], "error": {"message": "boom"}},
        },
    )
    session = AppServerRuntimeSession(repo_root=Path("/repo"))
    session._client = fake_server_process.client

    result = session.run_execution_turn(
        thread_id="thr-1",
        prompt_text="do work",
        sandbox_policy={"type": "workspaceWrite"},
        approval_policy="on-request",
    )

    assert result.status == "failed"
```

```python
def test_run_advisory_turn_rejects_interrupted_status() -> None:
    """Advisory turns still reject non-completed status."""
    # Advisory turns use run_advisory_turn(), which should continue to raise
    # on interrupted/failed status. Test verifies the per-caller policy.
    pass  # Covered by existing tests — advisory path unchanged.
```

- [ ] **Step 2.3: Run tests to verify they fail**

Run:
```bash
cd packages/plugins/codex-collaboration && uv run pytest tests/test_runtime.py::test_run_turn_accepts_interrupted_status_when_allowed -v
```
Expected: FAIL — `run_execution_turn()` does not accept `approval_policy` parameter, `TurnExecutionResult` has no `status` field.

- [ ] **Step 2.4: Modify `run_execution_turn()` and `_run_turn()` in `server/runtime.py`**

Update `run_execution_turn()` at line 158 to accept `approval_policy` and pass `allowed_terminal_statuses`:

```python
def run_execution_turn(
    self,
    *,
    thread_id: str,
    prompt_text: str,
    sandbox_policy: dict[str, Any],
    approval_policy: str = "on-request",
    output_schema: dict[str, Any] | None = None,
    effort: str | None = None,
    server_request_handler: Callable[[dict[str, Any]], dict[str, Any] | None] | None = None,
) -> TurnExecutionResult:
    """Start an execution turn with an explicit execution sandbox."""

    return self._run_turn(
        thread_id=thread_id,
        prompt_text=prompt_text,
        output_schema=output_schema,
        effort=effort,
        sandbox_policy=sandbox_policy,
        approval_policy=approval_policy,
        allowed_terminal_statuses=("completed", "interrupted", "failed"),
        server_request_handler=server_request_handler,
    )
```

Update `_run_turn()` at line 177 to accept the new parameters:

```python
def _run_turn(
    self,
    *,
    thread_id: str,
    prompt_text: str,
    output_schema: dict[str, Any] | None,
    effort: str | None,
    sandbox_policy: dict[str, Any],
    approval_policy: str = "never",
    allowed_terminal_statuses: tuple[str, ...] = ("completed",),
    server_request_handler: Callable[[dict[str, Any]], dict[str, Any] | None] | None = None,
) -> TurnExecutionResult:
    """Start a turn and collect notifications until completion."""

    params: dict[str, Any] = {
        "threadId": thread_id,
        "input": [{"type": "text", "text": prompt_text}],
        "cwd": str(self._repo_root),
        "approvalPolicy": approval_policy,
        "sandboxPolicy": sandbox_policy,
        "summary": "concise",
        "personality": "pragmatic",
    }
    if output_schema is not None:
        params["outputSchema"] = output_schema
    if effort is not None:
        params["effort"] = effort

    result = self._client.request("turn/start", params)
    turn = result.get("turn")
    if not isinstance(turn, dict) or not isinstance(turn.get("id"), str):
        raise RuntimeError(
            f"Turn start failed: malformed turn response. Got: {turn!r:.100}"
        )
    turn_id = str(turn["id"])
    agent_message = ""
    notifications: list[dict[str, Any]] = []
    while True:
        notification = self._client.next_notification(timeout=1200.0)
        if notification.get("method") is None:
            continue
        notifications.append(notification)
        method = str(notification["method"])
        params_n = notification.get("params", {})
        if not isinstance(params_n, dict):
            continue
        if params_n.get("turnId") not in (None, turn_id):
            continue
        # Server-request handling: messages with both 'id' and 'method'
        # are server-initiated requests, not passive notifications.
        if "id" in notification and server_request_handler is not None:
            response_payload = server_request_handler(notification)
            if response_payload is not None:
                self._client.respond(notification["id"], response_payload)
        if method == "item/completed":
            item = params_n.get("item")
            if isinstance(item, dict) and item.get("type") == "agentMessage":
                text = item.get("text")
                if isinstance(text, str):
                    agent_message = text
        if method == "turn/completed":
            turn_payload = params_n.get("turn")
            if not isinstance(turn_payload, dict):
                raise RuntimeError(
                    "Turn completion failed: missing turn payload. "
                    f"Got: {params_n!r:.100}"
                )
            status = turn_payload.get("status")
            if status not in allowed_terminal_statuses:
                raise RuntimeError(
                    "Turn completion failed: turn status not in allowed set. "
                    f"Got: {status!r:.100}, allowed: {allowed_terminal_statuses!r}"
                )
            return TurnExecutionResult(
                turn_id=turn_id,
                status=str(status),
                agent_message=agent_message,
                notifications=tuple(notifications),
            )
```

Update `run_advisory_turn()` at line 140 to pass `output_schema` and `approval_policy` explicitly:

```python
def run_advisory_turn(
    self,
    *,
    thread_id: str,
    prompt_text: str,
    output_schema: dict[str, Any],
    effort: str | None = None,
) -> TurnExecutionResult:
    """Start an advisory turn in the read-only runtime."""

    return self._run_turn(
        thread_id=thread_id,
        prompt_text=prompt_text,
        output_schema=output_schema,
        effort=effort,
        sandbox_policy=_build_read_only_sandbox_policy(),
        approval_policy="never",
        allowed_terminal_statuses=("completed",),
    )
```

Add the `Callable` import at the top of `runtime.py`:

```python
from typing import Any, Callable
```

Add `interrupt_turn()` and `close()` methods to `AppServerRuntimeSession` (after `run_execution_turn`):

```python
def interrupt_turn(
    self, *, thread_id: str, turn_id: str | None
) -> None:
    """Request cancellation of an in-flight turn via turn/interrupt.

    The App Server responds with ``{}`` and finishes the turn with
    ``status: "interrupted"`` in the ``turn/completed`` notification.
    ``turn_id`` is optional — if None, the most recent turn for the
    thread is interrupted.
    """
    params: dict[str, Any] = {"threadId": thread_id}
    if turn_id is not None:
        params["turnId"] = turn_id
    self._client.request("turn/interrupt", params)

def close(self) -> None:
    """Terminate the runtime subprocess and release resources."""
    self._client.close()
```

- [ ] **Step 2.5: Run tests to verify they pass**

Run:
```bash
cd packages/plugins/codex-collaboration && uv run pytest tests/test_runtime.py -v -x
```
Expected: all runtime tests pass (existing + 2 new).

- [ ] **Step 2.6: Run full suite**

Run:
```bash
cd packages/plugins/codex-collaboration && uv run pytest -x -q
```
Expected: 672+ passed.

- [ ] **Step 2.7: Commit**

```bash
git add packages/plugins/codex-collaboration/server/models.py packages/plugins/codex-collaboration/server/runtime.py packages/plugins/codex-collaboration/tests/test_runtime.py
git commit -m "feat(t20260330-05): widen TurnExecutionResult with status field, accept interrupted/failed"
```

---

## Task 3: `codex.delegate.start` Input Contract

**Files:**
- Modify: `server/delegation_controller.py`
- Modify: `server/mcp_server.py`
- Modify: `tests/test_delegation_controller.py`
- Modify: `tests/test_mcp_server.py`

This task expands the tool surface with `objective`, updates the idempotency hash, and wires the approval-policy parameter through the tool dispatch. It does NOT yet add turn dispatch — that comes in Task 7.

---

- [ ] **Step 3.1: Write test for `objective` parameter in `start()`**

Add to `tests/test_delegation_controller.py`:

```python
def test_start_accepts_objective_parameter(tmp_path: Path) -> None:
    """start() accepts an objective parameter without error."""
    controller, _, _, _, _, _, _ = _build_controller(tmp_path)

    result = controller.start(
        repo_root=tmp_path / "repo",
        objective="Fix the login bug",
    )

    # Verifies objective is accepted. Specific status depends on
    # whether turn dispatch is wired (Task 7). Pre-Task-7: queued.
    # Post-Task-7: completed/needs_escalation/etc.
    assert not isinstance(result, JobBusyResponse)
```

```python
def test_delegation_request_hash_includes_objective(
    tmp_path: Path,
) -> None:
    """Objective is a component of the idempotency hash."""
    from server.delegation_controller import _delegation_request_hash

    repo_root = (tmp_path / "repo").resolve()
    hash_a = _delegation_request_hash(repo_root, "head-abc", "Fix bug A")
    hash_b = _delegation_request_hash(repo_root, "head-abc", "Fix bug B")
    hash_no_obj = _delegation_request_hash(repo_root, "head-abc", "")

    assert hash_a != hash_b, "Different objectives must produce different hashes"
    assert hash_a != hash_no_obj, "Objective vs no-objective must differ"
```

- [ ] **Step 3.2: Run tests to verify they fail**

Run:
```bash
cd packages/plugins/codex-collaboration && uv run pytest tests/test_delegation_controller.py::test_start_accepts_objective_parameter -v
```
Expected: FAIL — `start()` does not accept `objective` parameter.

- [ ] **Step 3.3: Add `objective` parameter to `DelegationController.start()`**

In `server/delegation_controller.py`, modify the `start()` signature at line 159:

```python
def start(
    self,
    *,
    repo_root: Path,
    base_commit: str | None = None,
    objective: str = "",
) -> DelegationJob | JobBusyResponse:
```

- [ ] **Step 3.4: Update `_delegation_request_hash()` to include objective**

At line 90 in `server/delegation_controller.py`:

```python
def _delegation_request_hash(repo_root: Path, base_commit: str, objective: str) -> str:
    """Recovery-contract idempotency component — hash of the delegation request.

    Per recovery-and-journal.md:47, the ``job_creation`` idempotency key is
    ``claude_session_id + delegation_request_hash``. The request is fully
    characterized by the resolved repo_root + base_commit + objective in v1.

    When the MCP surface later accepts additional inputs (e.g., a delegation
    brief or profile override), they must be included in the hash so replay
    recognizes the full request shape.
    """

    payload = f"{repo_root}:{base_commit}:{objective}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
```

Update the call site (around line 304):

```python
request_hash = _delegation_request_hash(resolved_root, resolved_base, objective)
```

- [ ] **Step 3.5: Update MCP tool definition and dispatch**

In `server/mcp_server.py`, update the `codex.delegate.start` tool definition at line 100:

```python
{
    "name": "codex.delegate.start",
    "description": "Start an isolated execution job. Creates a worktree, bootstraps an ephemeral execution runtime, and accepts an execution objective. Turn dispatch is wired in Task 7.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "repo_root": {
                "type": "string",
                "description": "Repository root path",
            },
            "objective": {
                "type": "string",
                "description": "What the execution agent should accomplish in the worktree.",
            },
            "base_commit": {
                "type": "string",
                "description": "Optional — the commit SHA to base the worktree on. Defaults to current HEAD of repo_root.",
            },
        },
        "required": ["repo_root", "objective"],
    },
},
```

Update the dispatch at line 326:

```python
if name == "codex.delegate.start":
    controller = self._ensure_delegation_controller()
    result = controller.start(
        repo_root=Path(arguments["repo_root"]),
        base_commit=arguments.get("base_commit"),
        objective=arguments["objective"],
    )
    return asdict(result)
```

- [ ] **Step 3.6: Run tests to verify they pass**

Run:
```bash
cd packages/plugins/codex-collaboration && uv run pytest tests/test_delegation_controller.py tests/test_mcp_server.py -v -x
```
Expected: all pass. Existing tests may need `objective=""` added to calls.

- [ ] **Step 3.7: Fix existing tests that call `start()` without `objective`**

Add `objective=""` (or any string) to all existing `controller.start()` calls in `tests/test_delegation_controller.py` and `tests/test_delegate_start_integration.py`. The parameter has a default of `""`, so existing tests should pass without changes, but verify.

- [ ] **Step 3.8: Run full suite**

Run:
```bash
cd packages/plugins/codex-collaboration && uv run pytest -x -q
```
Expected: 674+ passed.

- [ ] **Step 3.9: Commit**

```bash
git add packages/plugins/codex-collaboration/server/delegation_controller.py packages/plugins/codex-collaboration/server/mcp_server.py packages/plugins/codex-collaboration/tests/test_delegation_controller.py packages/plugins/codex-collaboration/tests/test_mcp_server.py packages/plugins/codex-collaboration/tests/test_delegate_start_integration.py
git commit -m "feat(t20260330-05): add objective to codex.delegate.start, update idempotency hash"
```

---

## Task 4: Execution Prompt Builder

**Files:**
- Create: `server/execution_prompt_builder.py`
- Create: `tests/test_execution_prompt_builder.py`

Minimal execution prompt builder. Deliberate decision: NO structured output schema for execution turns (D5).

---

- [ ] **Step 4.1: Write test for `build_execution_turn_text()`**

Create `tests/test_execution_prompt_builder.py`:

```python
"""Tests for execution-turn prompt construction."""

from __future__ import annotations

from server.execution_prompt_builder import build_execution_turn_text


def test_build_execution_turn_text_includes_objective() -> None:
    result = build_execution_turn_text(
        objective="Fix the login timeout bug",
        worktree_path="/data/runtimes/delegation/job-1/worktree",
    )
    assert "Fix the login timeout bug" in result


def test_build_execution_turn_text_includes_worktree_scope() -> None:
    result = build_execution_turn_text(
        objective="Refactor auth",
        worktree_path="/data/runtimes/delegation/job-1/worktree",
    )
    assert "/data/runtimes/delegation/job-1/worktree" in result


def test_build_execution_turn_text_conveys_execution_context() -> None:
    """The prompt should tell the agent it is operating in an isolated worktree."""
    result = build_execution_turn_text(
        objective="Add tests",
        worktree_path="/wt/abc",
    )
    assert "worktree" in result.lower() or "isolated" in result.lower()
```

- [ ] **Step 4.2: Run test to verify it fails**

Run:
```bash
cd packages/plugins/codex-collaboration && uv run pytest tests/test_execution_prompt_builder.py -v
```
Expected: FAIL — module does not exist.

- [ ] **Step 4.3: Implement `build_execution_turn_text()`**

Create `server/execution_prompt_builder.py`:

```python
"""Execution-turn prompt construction.

Execution turns dispatch real work in an isolated worktree. The prompt conveys
the objective and scope. Unlike advisory turns, execution turns do NOT use a
structured output schema — the "result" is the worktree state plus any server
requests captured during the turn.
"""

from __future__ import annotations


def build_execution_turn_text(
    *,
    objective: str,
    worktree_path: str,
) -> str:
    """Build the text input for an execution turn's ``turn/start``.

    The prompt instructs the execution agent to work within the isolated
    worktree boundary. No structured output schema is enforced — the agent
    operates freely within the sandbox constraints.
    """
    return (
        "You are working in an isolated worktree. Your workspace is:\n"
        f"  {worktree_path}\n\n"
        "Objective:\n"
        f"  {objective}\n\n"
        "Work within the worktree boundary. Commands that require approval "
        "will be escalated to the caller for review."
    )
```

- [ ] **Step 4.4: Run test to verify it passes**

Run:
```bash
cd packages/plugins/codex-collaboration && uv run pytest tests/test_execution_prompt_builder.py -v
```
Expected: 3 passed.

- [ ] **Step 4.5: Run full suite**

Run:
```bash
cd packages/plugins/codex-collaboration && uv run pytest -x -q
```
Expected: 677+ passed.

- [ ] **Step 4.6: Commit**

```bash
git add packages/plugins/codex-collaboration/server/execution_prompt_builder.py packages/plugins/codex-collaboration/tests/test_execution_prompt_builder.py
git commit -m "feat(t20260330-05): add execution prompt builder (no output schema)"
```

---

## Task 5: Pending-Request Store + `DelegationEscalation` Response Type

**Files:**
- Create: `server/pending_request_store.py`
- Create: `tests/test_pending_request_store.py`
- Modify: `server/models.py`
- Modify: `server/__init__.py`

---

- [ ] **Step 5.1a: Add `request_id` to `AuditEvent` in `server/models.py`**

The normative contract at `contracts.md:196` defines `request_id` as a top-level `string?` field on `AuditEvent`. The current dataclass at `models.py:159` is missing it. Add the field:

```python
@dataclass(frozen=True)
class AuditEvent:
    """Audit event record. See contracts.md §AuditEvent."""

    event_id: str
    timestamp: str
    actor: Literal["claude", "codex", "user", "system"]
    action: str
    collaboration_id: str
    runtime_id: str
    context_size: int | None = None
    policy_fingerprint: str | None = None
    turn_id: str | None = None
    job_id: str | None = None
    request_id: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)
```

- [ ] **Step 5.1b: Add `DelegationEscalation` to `server/models.py`**

Add after the `JobBusyResponse` class (after line 340):

```python
@dataclass(frozen=True)
class DelegationEscalation:
    """Returned when codex.delegate.start dispatched a turn that needs escalation.

    Separates persisted job lifecycle state from transient escalation state.
    The ``pending_request`` is a causal record — the wire request was already
    resolved at capture time (``PendingServerRequest.status == "resolved"``).
    Plugin escalation lifecycle is tracked by ``DelegationJob.status``.

    For parse failures, ``pending_request`` is a minimal causal record
    with ``kind="unknown"`` and whatever envelope fields could be
    extracted from the raw message (at minimum ``request_id`` and
    ``requested_scope.raw_method``). This gives ``codex.delegate.decide``
    enough context to operate on the escalation.
    """

    job: DelegationJob
    pending_request: PendingServerRequest
    agent_context: str | None = None
```

- [ ] **Step 5.2: Write test for `PendingRequestStore`**

Create `tests/test_pending_request_store.py`:

```python
"""Tests for PendingRequestStore — JSONL persistence for server request records."""

from __future__ import annotations

from pathlib import Path

import pytest

from server.models import PendingServerRequest
from server.pending_request_store import PendingRequestStore


def _make_request(
    *,
    request_id: str = "req-1",
    runtime_id: str = "rt-1",
    collaboration_id: str = "collab-1",
    kind: str = "command_approval",
    status: str = "pending",
) -> PendingServerRequest:
    return PendingServerRequest(
        request_id=request_id,
        runtime_id=runtime_id,
        collaboration_id=collaboration_id,
        codex_thread_id="thr-1",
        codex_turn_id="turn-1",
        item_id="item-1",
        kind=kind,
        requested_scope={"command": "pytest", "cwd": "/repo"},
        available_decisions=("accept", "decline", "cancel"),
        status=status,
    )


class TestPendingRequestStoreCreate:
    def test_create_persists_request(self, tmp_path: Path) -> None:
        store = PendingRequestStore(tmp_path, "sess-1")
        request = _make_request()
        store.create(request)

        retrieved = store.get("req-1")
        assert retrieved is not None
        assert retrieved.request_id == "req-1"
        assert retrieved.kind == "command_approval"

    def test_create_survives_replay(self, tmp_path: Path) -> None:
        store = PendingRequestStore(tmp_path, "sess-1")
        store.create(_make_request())

        # New store instance replays from disk
        store2 = PendingRequestStore(tmp_path, "sess-1")
        assert store2.get("req-1") is not None


class TestPendingRequestStoreUpdateStatus:
    def test_update_status_changes_status(self, tmp_path: Path) -> None:
        store = PendingRequestStore(tmp_path, "sess-1")
        store.create(_make_request(status="pending"))
        store.update_status("req-1", "resolved")

        retrieved = store.get("req-1")
        assert retrieved is not None
        assert retrieved.status == "resolved"

    def test_update_status_rejects_invalid_status(self, tmp_path: Path) -> None:
        store = PendingRequestStore(tmp_path, "sess-1")
        store.create(_make_request())

        with pytest.raises(ValueError, match="unknown status"):
            store.update_status("req-1", "bogus")


class TestPendingRequestStoreList:
    def test_list_pending_returns_only_pending(self, tmp_path: Path) -> None:
        store = PendingRequestStore(tmp_path, "sess-1")
        store.create(_make_request(request_id="req-1", status="pending"))
        store.create(_make_request(request_id="req-2", status="resolved"))

        pending = store.list_pending()
        assert len(pending) == 1
        assert pending[0].request_id == "req-1"

    def test_list_by_collaboration_id(self, tmp_path: Path) -> None:
        store = PendingRequestStore(tmp_path, "sess-1")
        store.create(_make_request(request_id="req-1", collaboration_id="c1"))
        store.create(_make_request(request_id="req-2", collaboration_id="c2"))

        result = store.list_by_collaboration_id("c1")
        assert len(result) == 1
        assert result[0].request_id == "req-1"


class TestPendingRequestStoreReplay:
    def test_replay_skips_invalid_status(self, tmp_path: Path) -> None:
        """Records with invalid status are silently skipped on replay."""
        store = PendingRequestStore(tmp_path, "sess-1")
        store.create(_make_request(status="pending"))

        # Manually write a corrupt update
        store_path = tmp_path / "pending_requests" / "sess-1" / "requests.jsonl"
        with store_path.open("a") as f:
            f.write('{"op":"update_status","request_id":"req-1","status":"bogus"}\n')

        store2 = PendingRequestStore(tmp_path, "sess-1")
        retrieved = store2.get("req-1")
        assert retrieved is not None
        assert retrieved.status == "pending"  # corrupt update skipped
```

- [ ] **Step 5.3: Run test to verify it fails**

Run:
```bash
cd packages/plugins/codex-collaboration && uv run pytest tests/test_pending_request_store.py -v
```
Expected: FAIL — module does not exist.

- [ ] **Step 5.4: Implement `PendingRequestStore`**

Create `server/pending_request_store.py`:

```python
"""Session-scoped JSONL store for PendingServerRequest records.

Mirrors DelegationJobStore pattern. Append-only; replay on read; last record
for each request_id wins. PendingServerRequest.status tracks the wire lifecycle
per recovery-and-journal.md:125-127, NOT the plugin escalation lifecycle.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import Any, get_args

from .models import PendingRequestStatus, PendingServerRequest

_VALID_STATUSES: frozenset[str] = frozenset(get_args(PendingRequestStatus))


class PendingRequestStore:
    """Append-only JSONL store for PendingServerRequest records."""

    def __init__(self, plugin_data_path: Path, session_id: str) -> None:
        self._store_dir = plugin_data_path / "pending_requests" / session_id
        self._store_dir.mkdir(parents=True, exist_ok=True)
        self._store_path = self._store_dir / "requests.jsonl"

    def create(self, request: PendingServerRequest) -> None:
        """Persist a new request record."""
        if request.status not in _VALID_STATUSES:
            raise ValueError(
                f"PendingRequestStore.create failed: unknown status. "
                f"Got: {request.status!r:.100}"
            )
        record = asdict(request)
        # Convert tuple fields to lists for JSON serialization
        record["available_decisions"] = list(record["available_decisions"])
        self._append({"op": "create", **record})

    def get(self, request_id: str) -> PendingServerRequest | None:
        """Retrieve a request by id, or None if not found."""
        return self._replay().get(request_id)

    def list_pending(self) -> list[PendingServerRequest]:
        """Return requests whose wire status is still pending."""
        return [r for r in self._replay().values() if r.status == "pending"]

    def list_by_collaboration_id(
        self, collaboration_id: str
    ) -> list[PendingServerRequest]:
        """Return all requests for a given collaboration."""
        return [
            r
            for r in self._replay().values()
            if r.collaboration_id == collaboration_id
        ]

    def update_status(
        self, request_id: str, status: PendingRequestStatus
    ) -> None:
        """Append a status update record to the log."""
        if status not in _VALID_STATUSES:
            raise ValueError(
                f"PendingRequestStore.update_status failed: unknown status. "
                f"Got: {status!r:.100}"
            )
        self._append(
            {"op": "update_status", "request_id": request_id, "status": status}
        )

    def _append(self, record: dict[str, Any]) -> None:
        with self._store_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())

    def _replay(self) -> dict[str, PendingServerRequest]:
        """Replay the JSONL log and return the current state per request_id."""
        requests: dict[str, PendingServerRequest] = {}
        if not self._store_path.exists():
            return requests
        with self._store_path.open(encoding="utf-8") as handle:
            for line in handle:
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    record = json.loads(stripped)
                except json.JSONDecodeError:
                    continue
                if not isinstance(record, dict):
                    continue
                op = record.get("op")
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
                            requested_scope=record.get("requested_scope", {}),
                            available_decisions=tuple(
                                record.get("available_decisions", ())
                            ),
                            status=record.get("status", "pending"),
                        )
                    except (KeyError, TypeError):
                        continue
                    if req.status not in _VALID_STATUSES:
                        continue
                    requests[req.request_id] = req
                elif op == "update_status":
                    req_id = record.get("request_id")
                    status = record.get("status")
                    if not isinstance(req_id, str) or not isinstance(status, str):
                        continue
                    if status not in _VALID_STATUSES:
                        continue
                    if req_id not in requests:
                        continue
                    existing = requests[req_id]
                    requests[req_id] = PendingServerRequest(
                        request_id=existing.request_id,
                        runtime_id=existing.runtime_id,
                        collaboration_id=existing.collaboration_id,
                        codex_thread_id=existing.codex_thread_id,
                        codex_turn_id=existing.codex_turn_id,
                        item_id=existing.item_id,
                        kind=existing.kind,
                        requested_scope=existing.requested_scope,
                        available_decisions=existing.available_decisions,
                        status=status,
                    )
        return requests
```

- [ ] **Step 5.5: Run tests to verify they pass**

Run:
```bash
cd packages/plugins/codex-collaboration && uv run pytest tests/test_pending_request_store.py -v
```
Expected: 7 passed.

- [ ] **Step 5.6: Update `server/__init__.py` exports**

Add `DelegationEscalation` and `PendingRequestStore` to `server/__init__.py`:

```python
from .models import (
    CollaborationHandle,
    ConsultRequest,
    ConsultResult,
    DelegationEscalation,
    DelegationJob,
    DialogueReadResult,
    DialogueReplyResult,
    DialogueStartResult,
    JobBusyResponse,
)
from .pending_request_store import PendingRequestStore
```

And add both to `__all__`.

- [ ] **Step 5.7: Run full suite**

Run:
```bash
cd packages/plugins/codex-collaboration && uv run pytest -x -q
```
Expected: 684+ passed.

- [ ] **Step 5.8: Commit**

```bash
git add packages/plugins/codex-collaboration/server/models.py packages/plugins/codex-collaboration/server/pending_request_store.py packages/plugins/codex-collaboration/server/__init__.py packages/plugins/codex-collaboration/tests/test_pending_request_store.py
git commit -m "feat(t20260330-05): add PendingRequestStore + DelegationEscalation result type"
```

---

## Task 6: Explicit Journaling Deferral + Orphaned-Running-Job Recovery

**Files:**
- Modify: `server/delegation_controller.py`
- Modify: `tests/test_delegation_controller.py`

This task documents the explicit deferral of execution-turn journaling. No functional code changes — only a docstring annotation in the controller (D2).

---

- [ ] **Step 6.1: Add deferral docstring to `DelegationController`**

In `server/delegation_controller.py`, add a class-level docstring section or update the existing module docstring (after line 24):

```python
# Execution-turn journaling deferral (T-05 pending-request capture slice):
#
# The first execution turn dispatched inside start() is intentionally
# unjournaled. job_creation.completed means "all durable start writes
# landed," not "turn finished." Turn dispatch happens AFTER the journal
# is terminal.
#
# Crash recovery for the first-turn window:
#
# After job_creation.completed, the journal entry IS resolved —
# list_unresolved() will NOT return it. If the process crashes after
# update_status(job_id, "running") but before post-turn terminal writes,
# the job is persisted as "running" with no live runtime and no journal
# replay anchor. recover_startup() handles this via orphaned-running-job
# detection (see Step 6.2): any job persisted as "running" after a cold
# restart has no live runtime (the registry is fresh) and is marked
# "unknown".
#
# Turn-dispatch journaling (with its own ``turn_dispatch`` operation and
# idempotency key per recovery-and-journal.md:49) lands with T-06
# (codex.delegate.poll), where multi-turn dispatch and replay become
# real requirements.
```

- [ ] **Step 6.2: Add orphaned-running-job recovery to `recover_startup()`**

After a cold restart, the execution runtime registry is fresh — no live runtimes exist. Any delegation job persisted as `"running"` is orphaned: the turn was in progress when the process died, and there is no replay anchor (D2). Mark these jobs `"unknown"` so poll/discard/promote can operate on terminal durable state.

In `server/delegation_controller.py`, add to `recover_startup()` after the existing `job_creation` reconciliation loop (after the `for entry in by_key.values():` block ends):

```python
        # --- Orphaned-running-job reconciliation ---
        # After a cold restart, the runtime registry is fresh: no live
        # runtimes exist. Any job persisted as "running" is orphaned —
        # the first-turn window crashed after update_status(job_id,
        # "running") but before post-turn terminal writes. There is no
        # journal replay anchor (D2: first turn is intentionally
        # unjournaled), so the only safe terminal state is "unknown".
        #
        # This is separate from the journal-based reconciliation above
        # because the journal entry is already "completed" at this point
        # (job_creation.completed fired before turn dispatch).
        for job in self._job_store.list_active():
            if job.status == "running":
                self._job_store.update_status(job.job_id, "unknown")
```

- [ ] **Step 6.3: Write test for orphaned-running-job recovery**

Add to `tests/test_delegation_controller.py`:

```python
def test_recover_startup_marks_orphaned_running_jobs_unknown(
    tmp_path: Path,
) -> None:
    """After a cold restart, running jobs with no live runtime are marked unknown."""
    controller, _, _, job_store, _, _, _ = _build_controller(tmp_path)

    # Simulate a crash: job persisted as "running" but no runtime in registry
    # (registry is fresh after restart).
    result = controller.start(repo_root=tmp_path / "repo")
    assert isinstance(result, DelegationJob)
    job_id = result.job_id

    # Manually set job to "running" to simulate the post-journal,
    # pre-turn-completion crash window.
    job_store.update_status(job_id, "running")

    # Cold restart: build a fresh controller (fresh registry, no live runtimes).
    controller2, _, _, _, _, _, _ = _build_controller(tmp_path, session_id="sess-1")
    controller2.recover_startup()

    recovered = job_store.get(job_id)
    assert recovered is not None
    assert recovered.status == "unknown"
```

- [ ] **Step 6.4: Run tests**

Run:
```bash
cd packages/plugins/codex-collaboration && uv run pytest tests/test_delegation_controller.py -v -x -k "orphaned_running"
```
Expected: 1 passed.

- [ ] **Step 6.5: Run full suite to verify no regressions**

Run:
```bash
cd packages/plugins/codex-collaboration && uv run pytest -x -q
```
Expected: same count + 1.

- [ ] **Step 6.6: Commit**

```bash
git add packages/plugins/codex-collaboration/server/delegation_controller.py packages/plugins/codex-collaboration/tests/test_delegation_controller.py
git commit -m "fix(t20260330-05): orphaned-running-job recovery + explicit journaling deferral"
```

- [ ] **Step 6.7: Amend `contracts.md` — `request_id` semantics (D9)**

Update the `PendingServerRequest` field description at `contracts.md:81`:

```
| `request_id` | string | Wire request id from the App Server, normalized to string. Used for `serverRequest/resolved` correlation. Parse-failure causal records may use a plugin-generated fallback id (not wire-correlated). |
```

This replaces "Plugin-assigned unique identifier" which is inaccurate — the existing `approval_router.py` already extracts the wire id directly, and the D6 diagnostic depends on wire correlation for `serverRequest/resolved` matching.

- [ ] **Step 6.8: Commit contract amendment**

```bash
git add docs/superpowers/specs/codex-collaboration/contracts.md
git commit -m "docs(t20260330-05): amend request_id semantics — wire id, not plugin-assigned (D9)"
```

---

## Task 7: Capture Loop + Job Transitions

**Files:**
- Modify: `server/delegation_controller.py`
- Modify: `tests/test_delegation_controller.py`

This is the heaviest task. It wires turn dispatch into `start()`, implements the three-strategy capture loop (cancel-capable, known no-cancel, fail-closed `turn/interrupt` for unknown/parse-failures per D3), job status transitions, agent context capture, D6 diagnostic post-loop signal verification, and terminal runtime cleanup (release + close for completed/failed, keep live for `needs_escalation`).

---

- [ ] **Step 7.1: Add `PendingRequestStore` and prompt builder to `DelegationController.__init__()`**

In `server/delegation_controller.py`, add imports at top:

```python
from .approval_router import parse_pending_server_request
from .execution_prompt_builder import build_execution_turn_text
from .pending_request_store import PendingRequestStore
from .models import (
    AuditEvent,
    CollaborationHandle,
    DelegationEscalation,
    DelegationJob,
    JobBusyResponse,
    OperationJournalEntry,
    PendingServerRequest,
)
from .runtime import AppServerRuntimeSession, build_workspace_write_sandbox_policy
```

Add `pending_request_store` to `__init__()`:

```python
def __init__(
    self,
    *,
    control_plane: _ControlPlaneLike,
    worktree_manager: _WorktreeManagerLike,
    job_store: DelegationJobStore,
    lineage_store: LineageStore,
    runtime_registry: ExecutionRuntimeRegistry,
    journal: OperationJournal,
    pending_request_store: PendingRequestStore,
    session_id: str,
    plugin_data_path: Path,
    head_commit_resolver: Callable[[Path], str] | None = None,
    uuid_factory: Callable[[], str] | None = None,
    approval_policy: str = "on-request",
) -> None:
    # ... existing assignments ...
    self._pending_request_store = pending_request_store
    self._approval_policy = approval_policy
```

- [ ] **Step 7.2: Update `start()` return type and add turn dispatch**

Change the `start()` return type:

```python
def start(
    self,
    *,
    repo_root: Path,
    base_commit: str | None = None,
    objective: str = "",
) -> DelegationJob | DelegationEscalation | JobBusyResponse:
```

After the committed-start block (after `return job` at line 494), replace the final `return job` with turn dispatch logic:

```python
        # --- Turn dispatch (post-journal-completed) ---
        # The job_creation journal is terminal. Turn dispatch is intentionally
        # unjournaled in this slice (see Task 6 deferral comment above).
        self._job_store.update_status(job_id, "running")

        sandbox_policy = build_workspace_write_sandbox_policy(worktree_path)
        prompt_text = build_execution_turn_text(
            objective=objective,
            worktree_path=str(worktree_path),
        )

        # Server-request capture state
        captured_request: PendingServerRequest | None = None
        interrupted_by_unknown: bool = False
        parse_failed: bool = False  # Distinguishes parse failure from parseable-unknown

        _CANCEL_CAPABLE_KINDS = frozenset({"command_approval", "file_change"})
        _KNOWN_DENIAL_KINDS: dict[str, dict[str, Any]] = {
            "request_user_input": {"answers": {}},
        }

        def _server_request_handler(message: dict[str, Any]) -> dict[str, Any] | None:
            """Handle a server-initiated request during the notification loop.

            Three cases, in priority order:

            1. **Parse failure or unknown kind** — fail closed. The request
               cannot be safely auto-responded, so interrupt the turn via
               ``turn/interrupt``. Return ``None`` to skip responding to
               this specific request (the turn interrupt handles cleanup).
            2. **First parseable request** — persist and respond:
               - Cancel-capable (command/file): ``{"decision": "cancel"}``
               - Known no-cancel (user-input): minimal denial
            3. **Subsequent parseable requests** — always respond (to avoid
               deadlocking the App Server) but do NOT persist a second
               capture. Use the same response strategy as case 2.
            """
            nonlocal captured_request, interrupted_by_unknown, parse_failed

            # Parse the server request.
            try:
                request = parse_pending_server_request(
                    message,
                    runtime_id=runtime_id,
                    collaboration_id=collaboration_id,
                )
            except Exception:
                # Parse failure: fail closed. Preserve a minimal causal
                # record from whatever the raw message provides, then
                # interrupt the turn. The stored record gives
                # delegate.decide something to operate on.
                #
                # D4 does not apply: no wire response was sent, so the
                # stored status stays "pending" (not "resolved").
                # D6 does not apply: no wire request id or item id to
                # correlate against serverRequest/resolved.
                # D9: request_id uses raw wire id if available, else
                # a plugin-generated fallback (not wire-correlated).
                raw_id = message.get("id")
                raw_method = str(message.get("method", "unknown"))
                minimal = PendingServerRequest(
                    request_id=str(raw_id) if raw_id is not None else self._uuid_factory(),
                    runtime_id=runtime_id,
                    collaboration_id=collaboration_id,
                    codex_thread_id="",
                    codex_turn_id="",
                    item_id="",
                    kind="unknown",
                    requested_scope={"raw_method": raw_method},
                    available_decisions=(),
                )
                if captured_request is None:
                    self._pending_request_store.create(minimal)
                    captured_request = minimal
                interrupted_by_unknown = True
                parse_failed = True
                entry.session.interrupt_turn(thread_id=thread_id, turn_id=None)
                return None

            # Unknown kind: fail closed. Persist the request (it IS
            # parseable — we have the envelope fields), then interrupt.
            # Unknown requests are never auto-approved per
            # recovery-and-journal.md:134.
            if request.kind == "unknown":
                if captured_request is None:
                    self._pending_request_store.create(request)
                    captured_request = request
                interrupted_by_unknown = True
                entry.session.interrupt_turn(thread_id=thread_id, turn_id=None)
                return None

            # First parseable, known-kind request: persist and respond.
            if captured_request is None:
                self._pending_request_store.create(request)
                captured_request = request

            # Respond (both first and subsequent requests get a response
            # to avoid deadlocking the App Server).
            if request.kind in _CANCEL_CAPABLE_KINDS:
                return {"decision": "cancel"}
            elif request.kind in _KNOWN_DENIAL_KINDS:
                return _KNOWN_DENIAL_KINDS[request.kind]
            else:
                # Defensive: kind is in PendingRequestKind but not in
                # either set above. Interrupt rather than fabricate.
                interrupted_by_unknown = True
                entry.session.interrupt_turn(thread_id=thread_id, turn_id=None)
                return None

        entry = self._runtime_registry.lookup(runtime_id)
        if entry is None:
            raise RuntimeError(
                "Delegation turn dispatch failed: runtime not registered. "
                f"Got: runtime_id={runtime_id!r:.100}"
            )

        turn_result = entry.session.run_execution_turn(
            thread_id=thread_id,
            prompt_text=prompt_text,
            sandbox_policy=sandbox_policy,
            approval_policy=self._approval_policy,
            server_request_handler=_server_request_handler,
        )

        captured_agent_context = turn_result.agent_message or None

        # --- D6 diagnostic: three-signal verification ---
        # Only for requests with wire-correlated ids (not parse
        # failures). Parse-failure causal records have empty item_id
        # and may have a synthetic request_id, so D6 signals are not
        # expected. Parseable unknown-kind requests DO have wire ids,
        # and the App Server emits serverRequest/resolved on interrupt
        # as part of lifecycle cleanup.
        if captured_request is not None and not parse_failed:
            _verify_post_turn_signals(
                notifications=turn_result.notifications,
                request_id=captured_request.request_id,
                item_id=captured_request.item_id,
            )

        # --- Derive job status from turn outcome + cleanup ---
        if captured_request is not None:
            # D4: mark wire request as resolved — but only for
            # wire-correlated requests. Parse-failure causal records
            # stay "pending": no wire response was sent, no
            # serverRequest/resolved can confirm closure.
            if not parse_failed:
                self._pending_request_store.update_status(
                    captured_request.request_id, "resolved"
                )

            if captured_request.kind in _CANCEL_CAPABLE_KINDS:
                # Cancel-capable: turn was interrupted → needs_escalation
                self._job_store.update_status(job_id, "needs_escalation")
            elif interrupted_by_unknown:
                # Unknown kind: turn was interrupted → needs_escalation
                self._job_store.update_status(job_id, "needs_escalation")
            elif turn_result.status != "completed":
                # No-cancel request and turn didn't complete → needs_escalation
                self._job_store.update_status(job_id, "needs_escalation")
            else:
                # No-cancel request but turn completed → job completed
                self._job_store.update_status(job_id, "completed")

            # Emit audit event (contract action name: "escalate").
            # Per recovery-and-journal.md:88 and contracts.md:196,
            # escalate events carry request_id as a top-level field.
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

            updated_job = self._job_store.get(job_id)
            assert updated_job is not None

            # Terminal cleanup: completed/failed jobs release the runtime
            # and close the session. needs_escalation keeps the runtime
            # live for T-06 codex.delegate.decide to resume.
            if updated_job.status not in ("needs_escalation", "running"):
                self._runtime_registry.release(runtime_id)
                entry.session.close()

            return DelegationEscalation(
                job=updated_job,
                pending_request=captured_request,
                agent_context=captured_agent_context,
            )
        else:
            # No server request captured — turn completed normally
            if turn_result.status == "completed":
                self._job_store.update_status(job_id, "completed")
            elif turn_result.status == "failed":
                self._job_store.update_status(job_id, "failed")
            else:
                self._job_store.update_status(job_id, "unknown")

            updated_job = self._job_store.get(job_id)
            assert updated_job is not None

            # Terminal cleanup: release runtime + close session.
            self._runtime_registry.release(runtime_id)
            entry.session.close()

            return updated_job
```

Add the D6 signal verification helper as a module-level function:

```python
def _verify_post_turn_signals(
    *,
    notifications: tuple[dict[str, Any], ...],
    request_id: str,
    item_id: str,
) -> None:
    """D6 diagnostic: check serverRequest/resolved + item/completed.

    Called after the turn loop exits on turn/completed. Checks that the
    expected protocol signals are present in the notification stream.
    Missing signals are logged as warnings for observability but do NOT
    affect state derivation — turn result status is the terminal signal.
    """
    import logging

    logger = logging.getLogger(__name__)
    seen_resolved = False
    seen_item_completed = False
    for notification in notifications:
        method = notification.get("method")
        params = notification.get("params", {})
        if not isinstance(params, dict):
            continue
        if method == "serverRequest/resolved" and params.get("requestId") == request_id:
            seen_resolved = True
        if method == "item/completed" and isinstance(params.get("item"), dict):
            if params["item"].get("id") == item_id:
                seen_item_completed = True
    if not seen_resolved:
        logger.warning(
            "D6 signal missing: serverRequest/resolved not seen for "
            "request_id=%r after turn/completed",
            request_id,
        )
    if not seen_item_completed:
        logger.warning(
            "D6 signal missing: item/completed not seen for "
            "item_id=%r after turn/completed",
            item_id,
        )
```

- [ ] **Step 7.3: Write unit tests for capture loop — cancel-capable path**

Add to `tests/test_delegation_controller.py`:

First, update `_FakeSession` to support `run_execution_turn()`:

```python
class _FakeSession:
    def __init__(self, thread_id: str = "thr-1") -> None:
        self._thread_id = thread_id
        self.closed = False
        self._interrupted = False
        self._turn_result: TurnExecutionResult | None = None
        self._server_requests: list[dict[str, Any]] = []

    # ... existing methods ...

    def run_execution_turn(
        self,
        *,
        thread_id: str,
        prompt_text: str,
        sandbox_policy: dict[str, Any],
        approval_policy: str = "on-request",
        output_schema: dict[str, Any] | None = None,
        effort: str | None = None,
        server_request_handler=None,
    ) -> TurnExecutionResult:
        """Fake execution turn that invokes server_request_handler for queued requests."""
        handler_responses: list[dict[str, Any] | None] = []
        for req in self._server_requests:
            if server_request_handler is not None:
                resp = server_request_handler(req)
                handler_responses.append(resp)

        # If the turn was interrupted (via interrupt_turn), override
        # the configured result status.
        if self._interrupted and self._turn_result is not None:
            return TurnExecutionResult(
                turn_id=self._turn_result.turn_id,
                status="interrupted",
                agent_message=self._turn_result.agent_message,
                notifications=self._turn_result.notifications,
            )
        if self._interrupted:
            return TurnExecutionResult(
                turn_id="turn-1",
                status="interrupted",
                agent_message="",
            )

        if self._turn_result is not None:
            return self._turn_result
        return TurnExecutionResult(
            turn_id="turn-1",
            status="completed",
            agent_message="",
        )

    def interrupt_turn(
        self, *, thread_id: str, turn_id: str | None
    ) -> None:
        """Fake turn interrupt — marks the session so run_execution_turn
        returns 'interrupted' status."""
        self._interrupted = True

    def close(self) -> None:
        """Mark the session as closed."""
        self.closed = True
```

Then add the test:

```python
def test_start_with_command_approval_returns_escalation(tmp_path: Path) -> None:
    """When a command approval request fires, start() returns DelegationEscalation."""
    controller, cp, _, job_store, _, _, _ = _build_controller(tmp_path)

    # Configure the fake session to emit a server request
    session = cp._sessions[0] if cp._sessions else None
    # We need to pre-configure — the session is created inside start().
    # Override _FakeControlPlane to produce a session with a server request.
    server_request_msg = {
        "id": "req-1",
        "method": "item/commandExecution/requestApproval",
        "params": {
            "itemId": "item-1",
            "threadId": "thr-1",
            "turnId": "turn-1",
            "command": "pytest tests/",
            "cwd": "/repo",
        },
    }
    cp._next_session_requests = [server_request_msg]
    cp._next_turn_result = TurnExecutionResult(
        turn_id="turn-1",
        status="interrupted",
        agent_message="I was about to run tests",
    )

    result = controller.start(
        repo_root=tmp_path / "repo",
        objective="Run the tests",
    )

    assert isinstance(result, DelegationEscalation)
    assert result.job.status == "needs_escalation"
    assert result.pending_request.kind == "command_approval"
    assert result.pending_request.status == "resolved"
    assert result.agent_context == "I was about to run tests"
```

- [ ] **Step 7.4: Write unit test for unknown-kind request (fail-closed interrupt)**

```python
def test_start_with_unknown_request_interrupts_and_escalates(
    tmp_path: Path,
) -> None:
    """Unknown request kind triggers turn/interrupt and needs_escalation."""
    controller, cp, _, job_store, _, _, registry = _build_controller(tmp_path)

    # permissions/requestApproval maps to kind="unknown" in the parser
    server_request_msg = {
        "id": "req-1",
        "method": "item/permissions/requestApproval",
        "params": {
            "itemId": "item-1",
            "threadId": "thr-1",
            "turnId": "turn-1",
            "reason": "Need write access",
            "permissions": {"fileSystem": {"write": ["/extra"]}},
        },
    }
    cp._next_session_requests = [server_request_msg]
    # turn_result is overridden to "interrupted" by the fake session
    # when interrupt_turn is called.
    cp._next_turn_result = TurnExecutionResult(
        turn_id="turn-1",
        status="completed",
        agent_message="Was working on it",
    )

    result = controller.start(
        repo_root=tmp_path / "repo",
        objective="Do the thing",
    )

    # Unknown kind (parseable) → fail closed → interrupt → needs_escalation
    assert isinstance(result, DelegationEscalation)
    assert result.job.status == "needs_escalation"
    assert result.pending_request.kind == "unknown"
    # Parseable unknown-kind: wire-correlated, D4 applies → "resolved"
    assert result.pending_request.status == "resolved"
```

- [ ] **Step 7.4b: Write unit test for second request (no deadlock)**

```python
def test_start_with_two_requests_responds_to_both(tmp_path: Path) -> None:
    """Second request after the first gets a response (no deadlock), but is not persisted."""
    controller, cp, _, job_store, _, _, _ = _build_controller(tmp_path)

    cp._next_session_requests = [
        {
            "id": "req-1",
            "method": "item/commandExecution/requestApproval",
            "params": {
                "itemId": "item-1",
                "threadId": "thr-1",
                "turnId": "turn-1",
                "command": "make build",
                "cwd": "/repo",
            },
        },
        {
            "id": "req-2",
            "method": "item/commandExecution/requestApproval",
            "params": {
                "itemId": "item-2",
                "threadId": "thr-1",
                "turnId": "turn-1",
                "command": "make test",
                "cwd": "/repo",
            },
        },
    ]
    cp._next_turn_result = TurnExecutionResult(
        turn_id="turn-1",
        status="interrupted",
        agent_message="Building",
    )

    result = controller.start(
        repo_root=tmp_path / "repo",
        objective="Build and test",
    )

    assert isinstance(result, DelegationEscalation)
    # Only the first request is persisted
    assert result.pending_request.request_id == "req-1"
```

- [ ] **Step 7.4c: Write unit test for parse-failure escalation (minimal causal record)**

```python
def test_start_with_unparseable_request_creates_minimal_causal_record(
    tmp_path: Path,
) -> None:
    """Unparseable server request → turn/interrupt → needs_escalation with
    a minimal causal record preserving raw id and method."""
    controller, cp, _, job_store, _, _, _ = _build_controller(tmp_path)

    # A message with no params → parse failure in approval_router
    malformed_request = {
        "id": "req-bad",
        "method": "item/commandExecution/requestApproval",
        # Missing "params" entirely
    }
    cp._next_session_requests = [malformed_request]
    cp._next_turn_result = TurnExecutionResult(
        turn_id="turn-1",
        status="completed",
        agent_message="Something went wrong",
    )

    result = controller.start(
        repo_root=tmp_path / "repo",
        objective="Parse failure test",
    )

    assert isinstance(result, DelegationEscalation)
    assert result.job.status == "needs_escalation"
    # Minimal causal record preserved from raw message
    assert result.pending_request is not None
    assert result.pending_request.kind == "unknown"
    assert result.pending_request.request_id == "req-bad"
    assert result.pending_request.requested_scope["raw_method"] == "item/commandExecution/requestApproval"
    # D4 carve-out: parse-failure records stay "pending" — no wire
    # response was sent, no serverRequest/resolved can confirm.
    assert result.pending_request.status == "pending"
    assert result.agent_context == "Something went wrong"

    # Verify persisted store state matches the returned object.
    # This catches bugs where the handler sets parse_failed but the
    # status-derivation block still calls update_status("resolved").
    from server.pending_request_store import PendingRequestStore
    store = PendingRequestStore(tmp_path / "data", "sess-1")
    persisted = store.get("req-bad")
    assert persisted is not None
    assert persisted.status == "pending", (
        "D4 carve-out: parse-failure record must stay 'pending' in store, "
        f"got {persisted.status!r}"
    )
```

- [ ] **Step 7.5: Write unit test for no server request (clean completion)**

```python
def test_start_with_no_server_requests_returns_delegation_job(
    tmp_path: Path,
) -> None:
    """When no server requests fire, start() returns a completed DelegationJob.
    Runtime is released and session is closed."""
    controller, cp, _, _, _, _, registry = _build_controller(tmp_path)

    cp._next_session_requests = []
    cp._next_turn_result = TurnExecutionResult(
        turn_id="turn-1",
        status="completed",
        agent_message="All done",
    )

    result = controller.start(
        repo_root=tmp_path / "repo",
        objective="Clean task",
    )

    assert isinstance(result, DelegationJob)
    assert result.status == "completed"

    # Verify terminal cleanup: runtime released, session closed
    assert len(registry.active_runtime_ids()) == 0
    assert cp._sessions[-1].closed is True
```

- [ ] **Step 7.6: Update `_build_controller()` to include `PendingRequestStore`**

```python
def _build_controller(
    tmp_path: Path,
    *,
    head_sha: str = "head-abc",
    session_id: str = "sess-1",
) -> tuple[
    DelegationController,
    _FakeControlPlane,
    _FakeWorktreeManager,
    DelegationJobStore,
    LineageStore,
    OperationJournal,
    ExecutionRuntimeRegistry,
]:
    plugin_data = tmp_path / "data"
    plugin_data.mkdir(parents=True, exist_ok=True)
    job_store = DelegationJobStore(plugin_data, session_id)
    lineage_store = LineageStore(plugin_data, session_id)
    journal = OperationJournal(plugin_data)
    pending_store = PendingRequestStore(plugin_data, session_id)
    control_plane = _FakeControlPlane()
    worktree_manager = _FakeWorktreeManager()
    registry = ExecutionRuntimeRegistry()
    uuid_counter = iter(
        [f"job-{i}" for i in range(1, 20)]
        + [f"collab-{i}" for i in range(1, 20)]
        + [f"evt-{i}" for i in range(1, 20)]
    )
    controller = DelegationController(
        control_plane=control_plane,
        worktree_manager=worktree_manager,
        job_store=job_store,
        lineage_store=lineage_store,
        runtime_registry=registry,
        journal=journal,
        pending_request_store=pending_store,
        session_id=session_id,
        plugin_data_path=plugin_data,
        head_commit_resolver=lambda repo_root: head_sha,
        uuid_factory=lambda: next(uuid_counter),
    )
    return (
        controller,
        control_plane,
        worktree_manager,
        job_store,
        lineage_store,
        journal,
        registry,
    )
```

- [ ] **Step 7.7: Update `_FakeControlPlane` to support configurable turn results**

```python
class _FakeControlPlane:
    def __init__(self) -> None:
        self.calls: list[Path] = []
        self._next_runtime_id = 0
        self._sessions: list[_FakeSession] = []
        self._next_session_requests: list[dict[str, Any]] = []
        self._next_turn_result: TurnExecutionResult | None = None

    def start_execution_runtime(
        self, worktree_path: Path
    ) -> tuple[str, _FakeSession, str]:
        self.calls.append(worktree_path)
        self._next_runtime_id += 1
        session = _FakeSession(thread_id=f"thr-{self._next_runtime_id}")
        session._server_requests = list(self._next_session_requests)
        session._turn_result = self._next_turn_result
        self._sessions.append(session)
        return f"rt-{self._next_runtime_id}", session, session._thread_id
```

- [ ] **Step 7.8: Run capture loop tests**

Run:
```bash
cd packages/plugins/codex-collaboration && uv run pytest tests/test_delegation_controller.py -v -x -k "capture or escalation or server_request or no_server"
```
Expected: new tests pass.

- [ ] **Step 7.9: Fix all existing tests that build `DelegationController`**

All existing tests that call `_build_controller()` or construct `DelegationController` directly will need `pending_request_store` added. Update `_build_controller()` as shown in Step 7.6, which should fix all callers automatically.

- [ ] **Step 7.10: Update MCP server dispatch for three return types**

In `server/mcp_server.py`, update the delegate dispatch at line 326:

```python
if name == "codex.delegate.start":
    controller = self._ensure_delegation_controller()
    result = controller.start(
        repo_root=Path(arguments["repo_root"]),
        base_commit=arguments.get("base_commit"),
        objective=arguments["objective"],
    )
    if isinstance(result, DelegationEscalation):
        return {
            "job": asdict(result.job),
            "pending_request": asdict(result.pending_request),
            "agent_context": result.agent_context,
            "escalated": True,
        }
    return asdict(result)
```

Add the import:
```python
from .models import DelegationEscalation
```

- [ ] **Step 7.11: Run full suite**

Run:
```bash
cd packages/plugins/codex-collaboration && uv run pytest -x -q
```
Expected: 690+ passed.

- [ ] **Step 7.12: Run ruff**

Run:
```bash
cd packages/plugins/codex-collaboration && uv run ruff check .
```
Expected: All checks passed.

- [ ] **Step 7.13: Commit**

```bash
git add packages/plugins/codex-collaboration/server/delegation_controller.py packages/plugins/codex-collaboration/server/mcp_server.py packages/plugins/codex-collaboration/tests/test_delegation_controller.py
git commit -m "feat(t20260330-05): capture loop with three-strategy response (D3), terminal cleanup, D6 diagnostic"
```

---

## Task 8: Integration Proof + Approval-Policy Probe

**Files:**
- Modify: `tests/test_delegate_start_integration.py`
- Modify: `scripts/codex_runtime_bootstrap.py`

---

- [ ] **Step 8.1: Update production bootstrap to wire `PendingRequestStore`**

In `scripts/codex_runtime_bootstrap.py`, update `_build_delegation_factory()` to include `PendingRequestStore`:

Add the import at the top of `scripts/codex_runtime_bootstrap.py`:

```python
from server.pending_request_store import PendingRequestStore
```

Then update the factory closure inside `_build_delegation_factory()` (after line 112).
The existing pattern reads session_id from disk inside the closure via
`_read_session_id(plugin_data_path)` — preserve that boundary. Only add the
`PendingRequestStore` construction alongside the existing stores:

```python
    def factory() -> DelegationController:
        session_id = _read_session_id(plugin_data_path)
        job_store = DelegationJobStore(plugin_data_path, session_id)
        lineage_store = LineageStore(plugin_data_path, session_id)
        pending_store = PendingRequestStore(plugin_data_path, session_id)
        return DelegationController(
            control_plane=control_plane,
            worktree_manager=WorktreeManager(),
            job_store=job_store,
            lineage_store=lineage_store,
            runtime_registry=runtime_registry,
            journal=journal,
            pending_request_store=pending_store,
            session_id=session_id,
            plugin_data_path=plugin_data_path,
        )
```

- [ ] **Step 8.2: Write E2E integration test — command approval escalation**

Add to `tests/test_delegate_start_integration.py`:

```python
def test_e2e_command_approval_produces_escalation(tmp_path: Path) -> None:
    """Full path: start → turn dispatch → command approval → cancel → DelegationEscalation."""
    # Build controller with all real stores, fake runtime
    controller, cp = _build_integration_controller(tmp_path)

    # Configure fake session: emit command approval, return interrupted
    cp._next_session_requests = [
        {
            "id": "req-1",
            "method": "item/commandExecution/requestApproval",
            "params": {
                "itemId": "item-1",
                "threadId": "thr-1",
                "turnId": "turn-1",
                "command": "make build",
                "cwd": "/repo/worktree",
            },
        }
    ]
    cp._next_turn_result = TurnExecutionResult(
        turn_id="turn-1",
        status="interrupted",
        agent_message="Building the project",
    )

    result = controller.start(
        repo_root=tmp_path / "repo",
        objective="Build and test the project",
    )

    assert isinstance(result, DelegationEscalation)
    assert result.job.status == "needs_escalation"
    assert result.pending_request.kind == "command_approval"
    assert result.pending_request.request_id == "req-1"
    assert result.pending_request.status == "resolved"
    assert result.agent_context == "Building the project"

    # Verify pending request was persisted
    from server.pending_request_store import PendingRequestStore
    store = PendingRequestStore(tmp_path / "data", "sess-1")
    persisted = store.get("req-1")
    assert persisted is not None
    assert persisted.status == "resolved"
```

- [ ] **Step 8.3: Write E2E test — clean completion (no server requests)**

```python
def test_e2e_clean_completion_returns_delegation_job(tmp_path: Path) -> None:
    """Turn completes without server requests → DelegationJob with completed status."""
    controller, cp = _build_integration_controller(tmp_path)

    cp._next_session_requests = []
    cp._next_turn_result = TurnExecutionResult(
        turn_id="turn-1",
        status="completed",
        agent_message="All done",
    )

    result = controller.start(
        repo_root=tmp_path / "repo",
        objective="Simple task",
    )

    assert isinstance(result, DelegationJob)
    assert result.status == "completed"
```

- [ ] **Step 8.4: Write E2E test — unknown request kind triggers fail-closed interrupt**

```python
def test_e2e_unknown_request_kind_interrupts_and_escalates(
    tmp_path: Path,
) -> None:
    """Unknown request kind (permissions) → turn/interrupt → needs_escalation."""
    controller, cp = _build_integration_controller(tmp_path)

    cp._next_session_requests = [
        {
            "id": "req-1",
            "method": "item/permissions/requestApproval",
            "params": {
                "itemId": "item-1",
                "threadId": "thr-1",
                "turnId": "turn-1",
                "permissions": {"fileSystem": {"write": ["/extra"]}},
            },
        }
    ]
    # turn_result status will be overridden to "interrupted" by the
    # fake session when interrupt_turn is called.
    cp._next_turn_result = TurnExecutionResult(
        turn_id="turn-1",
        status="completed",
        agent_message="Worked around permissions",
    )

    result = controller.start(
        repo_root=tmp_path / "repo",
        objective="Task with optional permissions",
    )

    # Unknown kind (parseable) → fail closed → interrupt → needs_escalation
    assert isinstance(result, DelegationEscalation)
    assert result.job.status == "needs_escalation"
    assert result.pending_request.kind == "unknown"
    # Parseable unknown-kind: wire-correlated, D4 applies → "resolved"
    assert result.pending_request.status == "resolved"
```

- [ ] **Step 8.5: Write E2E test — busy gate with needs_escalation job**

```python
def test_e2e_busy_gate_blocks_when_job_needs_escalation(
    tmp_path: Path,
) -> None:
    """A job in needs_escalation is still active → busy gate blocks."""
    controller, cp = _build_integration_controller(tmp_path)

    # First start → escalation
    cp._next_session_requests = [
        {
            "id": "req-1",
            "method": "item/commandExecution/requestApproval",
            "params": {
                "itemId": "item-1",
                "threadId": "thr-1",
                "turnId": "turn-1",
                "command": "rm -rf /",
                "cwd": "/repo",
            },
        }
    ]
    cp._next_turn_result = TurnExecutionResult(
        turn_id="turn-1",
        status="interrupted",
        agent_message="",
    )

    first = controller.start(
        repo_root=tmp_path / "repo",
        objective="Dangerous task",
    )
    assert isinstance(first, DelegationEscalation)
    assert first.job.status == "needs_escalation"

    # Second start → busy
    second = controller.start(
        repo_root=tmp_path / "repo",
        objective="Another task",
    )
    assert isinstance(second, JobBusyResponse)
    assert second.busy is True
```

- [ ] **Step 8.6: Run integration tests**

Run:
```bash
cd packages/plugins/codex-collaboration && uv run pytest tests/test_delegate_start_integration.py -v
```
Expected: all pass.

- [ ] **Step 8.7: Run full suite**

Run:
```bash
cd packages/plugins/codex-collaboration && uv run pytest -x -q
```
Expected: 696+ passed.

- [ ] **Step 8.8: Run ruff**

Run:
```bash
cd packages/plugins/codex-collaboration && uv run ruff check . && uv run ruff format --check .
```
Expected: All checks passed.

- [ ] **Step 8.9: Commit**

```bash
git add packages/plugins/codex-collaboration/scripts/codex_runtime_bootstrap.py packages/plugins/codex-collaboration/tests/test_delegate_start_integration.py
git commit -m "test(t20260330-05): E2E integration tests for pending-request capture + bootstrap wiring"
```

---

## Risks and Known Deferrals

| Risk / Deferral | Why deferred | Trigger that reopens it |
|---|---|---|
| **First execution turn is intentionally unjournaled.** `job_creation.completed` means "all durable start writes landed," not "turn finished." If the process crashes during the first turn, the job is persisted as `running` with no replay anchor. `recover_startup()` detects orphaned running jobs (no live runtime after cold restart) and marks them `unknown` (Task 6). | Turn-dispatch journaling requires its own `turn_dispatch` operation with idempotency key `runtime_id + thread_id + turn_sequence` per `recovery-and-journal.md:49`. Multi-turn dispatch and replay become real requirements only with T-06 `codex.delegate.poll`. | T-06 (codex.delegate.poll), where multi-turn dispatch and replay become real requirements. |
| **`approvalPolicy` is probe-gated.** The vendored schema proves `untrusted \| on-failure \| on-request \| never` are valid values, but operational semantics (which actions trigger prompts under each policy) are not documented in the repo. | Use `untrusted` for the first proof. Narrow to `on-request` only after a live probe confirms it generates server requests for command execution in a `workspaceWrite` sandbox. | Live probe during Task 8. |
| **`cancel` is not universal across request kinds.** Command/file approvals support `cancel` (turn immediately interrupted). Permissions requests only support a granted-permissions response; denial is by omission. User-input requests only accept `{ answers: {...} }`. | Design decision D3. Three strategies: cancel-capable (command/file), known no-cancel minimal denial (user-input), fail-closed `turn/interrupt` (unknown/permissions/parse-failures). Unknown requests are never auto-approved per `recovery-and-journal.md:134`. | If a new request kind appears that needs a fourth strategy, or if permissions gets a stable deny path. |
| **`PendingServerRequest.status` is wire lifecycle, not plugin escalation.** After capture, status is `"resolved"` (wire request was responded to). Plugin escalation tracked by `DelegationJob.status`. | Design decision D4. Keeps spec contract at `recovery-and-journal.md:125-127` intact. Avoids spec amendment. | If `codex.delegate.decide` (T-06) needs to distinguish "pending wire request" from "resolved wire request pending plugin decision" — addressed by `DelegationJob.status` + stored causal record. |
| **No structured output schema for execution turns.** The `outputSchema` parameter is omitted for execution turns. Advisory turns continue to use `CONSULT_OUTPUT_SCHEMA`. | Design decision D5. Execution turn "output" is worktree state + server requests, not a JSON blob. | If a future slice needs structured execution results (e.g., for artifact extraction). |
| **Three-signal diagnostic is observability-only.** D6 is diagnostic, not a state-derivation gate. `turn/completed` status is the terminal signal for state transitions. `_verify_post_turn_signals()` logs warnings if `serverRequest/resolved` or target `item/completed` are missing from `turn_result.notifications`. | State derivation uses turn result status directly. The three-signal check exists to detect protocol anomalies during development; it does not block or alter job/request state transitions. | If protocol guarantees make signal presence load-bearing, upgrade D6 from diagnostic to required. |
| **`context_assembly.py` execution profile still emits advisory output schema.** The execution profile has token budgets and trim order but its `expected_output_shape` is the consult-style schema. | This slice does not use `context_assembly.py` for execution turns. The execution prompt builder (`build_execution_turn_text`) replaces the advisory packet assembly path for execution. | When execution turns need context-trimmed prompt assembly (likely T-06 or later). |

---

## Execution Handoff

**Plan saved to `docs/plans/2026-04-19-t05-pending-request-capture-slice.md`.**

Two execution options:

1. **Subagent-Driven (recommended)** — Dispatch a fresh subagent per task, review between tasks, fast iteration. Uses `superpowers:subagent-driven-development`.

2. **Inline Execution** — Execute tasks in this session using `superpowers:executing-plans`, batch execution with checkpoints for review.

**Which approach?**
