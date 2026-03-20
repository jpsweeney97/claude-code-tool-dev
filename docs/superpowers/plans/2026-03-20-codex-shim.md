# Codex MCP Shim — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a thin FastMCP shim (`codex_shim.py`) that exposes `codex` and `codex-reply` tools backed by the `codex_consult.py` adapter, returning `structuredContent.threadId` for backward compatibility with existing skills/agents.

**Architecture:** D-prime Phase 1 — adapter owns the real transport (`codex exec` subprocess), shim provides MCP backward compatibility. The shim is translation-only: no safety logic (handled by `codex_guard.py` PreToolUse hook), no analytics (owned by skills), no continuity logic (owned by agents). The shim translates MCP tool parameters to adapter inputs and adapter results to MCP `CallToolResult` with `structuredContent`.

**Tech Stack:** Python 3.11+, FastMCP (`mcp>=1.9.0`), pytest

**Ticket:** `docs/tickets/2026-03-19-codex-mcp-to-exec-migration.md` (T-20260319-01)

**Codex dialogue thread:** `019d097e-7350-7171-ab28-2d0220ae6dea` (converged architecture: D-prime)

**Predecessor plan:** `docs/superpowers/plans/2026-03-20-codex-consult-adapter.md` (T1/T2)

---

## File Structure

### New Files

| File | Responsibility |
|------|---------------|
| `scripts/codex_shim.py` | FastMCP stdio server exposing `codex` and `codex-reply` tools, translation-only |
| `tests/test_codex_shim.py` | Shim unit tests: schema verification, response builder, server creation, round-trip |

### Modified Files

| File | Change |
|------|--------|
| `pyproject.toml:6` | Add `mcp>=1.9.0` to dependencies |
| `scripts/codex_consult.py:317-421` | Extract `consult()` programmatic API from `run()`, add `_result()` helper, add `reasoning_effort` validation |
| `scripts/consultation_safety.py:46` | Add `"approval_policy"` to `START_POLICY.expected_fields` (shim uses underscore variant) |

### Unchanged (reference only)

| File | Why referenced |
|------|---------------|
| `scripts/codex_guard.py:157-167` | PostToolUse reads `tool_response["structuredContent"]["threadId"]` — shim must produce this |
| `context-injection/context_injection/server.py` | FastMCP server pattern reference |
| `scripts/consultation_safety.py` | `check_tool_input`, `START_POLICY` — called by `consult()` |

---

## Key Design Decisions

**`structuredContent` for threadId:** The upstream `codex mcp-server` returns `{ structuredContent: { threadId, content }, content: [{type: "text", text}] }`. The shim must replicate this exact shape. Verified: the `mcp` Python SDK's `CallToolResult` has a `structuredContent: dict | None` field (confirmed in installed package).

**Flat parameters instead of Pydantic models:** FastMCP wraps Pydantic model parameters in a nested `{"params": {...}}` schema, breaking backward compatibility. Verified empirically: `def codex_tool(params: CodexParams)` produces `{"properties": {"params": {"$ref": "#/$defs/CodexParams"}}}`. Flat Python parameters produce the correct flat schema. The upstream `approval-policy` (hyphen) becomes `approval_policy` (underscore) because hyphens are invalid Python identifiers. This requires adding `"approval_policy"` to `consultation_safety.py:START_POLICY.expected_fields` to prevent spurious shadow telemetry. `threadId` (camelCase) is a valid Python identifier and works directly.

**`consult()` programmatic API:** The adapter's `run()` function uses file I/O (reads JSON file, prints to stdout). The shim needs a direct call interface. `consult()` is a new function that takes typed parameters, runs the full pipeline (credential scan → version check → build command → subprocess → parse JSONL), and returns a result dict. `run()` is refactored to call `consult()`. This API is transport-agnostic — usable by both file-based CLI and MCP shim.

**No lifespan context:** Unlike the context-injection server (which needs POSIX checks, git file lists, HMAC keys), the codex shim has no per-process state. Tool handlers call `consult()` directly. No lifespan needed.

**Defense in depth on credential scanning:** The shim is translation-only (no safety logic). But `consult()` still runs `check_tool_input()` internally. Combined with `codex_guard.py` PreToolUse hook, prompts are scanned twice: once at the hook layer (MCP tool call), once at the adapter layer (subprocess dispatch). This is intentional — if either layer is bypassed, the other catches credentials.

---

## Task 1: Add `mcp>=1.9.0` to cross-model plugin dependencies

**Files:**
- Modify: `pyproject.toml:6`

- [ ] **Step 1: Add the dependency**

```toml
dependencies = ["pyyaml>=6.0", "mcp>=1.9.0"]
```

At `pyproject.toml:6`, change:
```
dependencies = ["pyyaml>=6.0"]
```
to:
```
dependencies = ["pyyaml>=6.0", "mcp>=1.9.0"]
```

- [ ] **Step 2: Sync and verify import**

Run: `cd packages/plugins/cross-model && uv sync && uv run python -c "from mcp.types import CallToolResult; print('structuredContent' in CallToolResult.model_fields)"`
Expected: `True`

- [ ] **Step 3: Commit**

```bash
git add packages/plugins/cross-model/pyproject.toml
git commit -m "feat(cross-model): add mcp dependency for codex shim"
```

---

## Task 2: Extract `consult()` programmatic API from `codex_consult.py`

**Files:**
- Modify: `scripts/codex_consult.py:317-421`
- Test: `tests/test_codex_consult.py` (add `TestConsult` class)

The `consult()` function runs the full pipeline without file I/O. It never raises — all errors are captured in the return dict (same field set as `_output()`). This gives the shim a clean programmatic interface.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_codex_consult.py`:

```python
class TestConsult:
    """Programmatic API: consult() — same pipeline as run() without file I/O."""

    @patch("scripts.codex_consult._run_subprocess")
    @patch("scripts.codex_consult._check_codex_version")
    @patch("scripts.codex_consult.check_tool_input")
    def test_success(self, mock_safety: MagicMock, mock_version: MagicMock, mock_run: MagicMock) -> None:
        from scripts.codex_consult import consult, SafetyVerdict
        mock_safety.return_value = SafetyVerdict(action="allow")
        mock_run.return_value = (
            '{"type":"thread.started","thread_id":"thr_api"}\n'
            '{"type":"item.completed","item":{"type":"agent_message","text":"Response via API."}}\n'
            '{"type":"turn.completed","usage":{"input_tokens":10,"output_tokens":5}}\n',
            0,
        )
        result = consult(prompt="test prompt")
        assert result["status"] == "ok"
        assert result["dispatched"] is True
        assert result["continuation_id"] == "thr_api"
        assert result["response_text"] == "Response via API."
        assert result["token_usage"] == {"input_tokens": 10, "output_tokens": 5}
        assert result["dispatch_state"] == "complete"
        assert result["error"] is None

    @patch("scripts.codex_consult.check_tool_input")
    def test_credential_block(self, mock_safety: MagicMock) -> None:
        from scripts.codex_consult import consult, SafetyVerdict
        mock_safety.return_value = SafetyVerdict(action="block", reason="AWS key", tier="strict")
        result = consult(prompt="AKIAIOSFODNN7EXAMPLE")
        assert result["status"] == "blocked"
        assert result["dispatched"] is False
        assert "AWS key" in result["error"]
        assert result["dispatch_state"] == "no_dispatch"

    @patch("scripts.codex_consult._run_subprocess")
    @patch("scripts.codex_consult._check_codex_version")
    @patch("scripts.codex_consult.check_tool_input")
    def test_timeout_with_partial_token(self, mock_safety: MagicMock, mock_version: MagicMock, mock_run: MagicMock) -> None:
        from scripts.codex_consult import consult, SubprocessTimeout, SafetyVerdict
        mock_safety.return_value = SafetyVerdict(action="allow")
        mock_run.side_effect = SubprocessTimeout('{"type":"thread.started","thread_id":"thr_partial"}\n')
        result = consult(prompt="test")
        assert result["status"] == "timeout_uncertain"
        assert result["continuation_id"] == "thr_partial"
        assert result["dispatch_state"] == "dispatched_with_token_uncertain"

    @patch("scripts.codex_consult._run_subprocess")
    @patch("scripts.codex_consult._check_codex_version")
    @patch("scripts.codex_consult.check_tool_input")
    def test_passes_thread_id_to_build_command(self, mock_safety: MagicMock, mock_version: MagicMock, mock_run: MagicMock) -> None:
        from scripts.codex_consult import consult, SafetyVerdict
        mock_safety.return_value = SafetyVerdict(action="allow")
        mock_run.return_value = (
            '{"type":"thread.started","thread_id":"thr_resumed"}\n'
            '{"type":"item.completed","item":{"type":"agent_message","text":"Continued."}}\n'
            '{"type":"turn.completed","usage":{}}\n',
            0,
        )
        result = consult(prompt="continue", thread_id="thr_original")
        assert result["status"] == "ok"
        cmd = mock_run.call_args[0][0]
        assert "resume" in cmd
        assert "thr_original" in cmd

    def test_invalid_reasoning_effort(self) -> None:
        from scripts.codex_consult import consult
        result = consult(prompt="test", reasoning_effort="ultra")
        assert result["status"] == "error"
        assert "reasoning_effort" in result["error"]
        assert result["dispatched"] is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_codex_consult.py::TestConsult -v`
Expected: FAIL with `ImportError` (consult not defined yet)

- [ ] **Step 3: Implement `consult()` and refactor `run()`**

In `scripts/codex_consult.py`, make these changes:

**3a. Replace `_output()` with `_result()` + `_output()` wrapper:**

Replace the existing `_output` function at line 323-329:
```python
def _output(status: str, **kwargs: object) -> str:
    """Format adapter output as JSON. Validates all required fields present."""
    result: dict = {"status": status}
    result.update(kwargs)
    missing = _OUTPUT_REQUIRED - set(result.keys())
    assert not missing, f"_output missing fields: {missing}"
    return json.dumps(result)
```

With:
```python
def _result(status: str, **kwargs: object) -> dict:
    """Build result dict with field validation."""
    result: dict = {"status": status}
    result.update(kwargs)
    missing = _OUTPUT_REQUIRED - set(result.keys())
    assert not missing, f"_result missing fields: {missing}"
    return result


def _output(status: str, **kwargs: object) -> str:
    """Format adapter output as JSON string. Validates all required fields."""
    return json.dumps(_result(status, **kwargs))
```

**3b. Add the `consult()` function** between `_output()` and `run()`:

```python
def consult(
    prompt: str,
    thread_id: str | None = None,
    model: str | None = None,
    reasoning_effort: str = "xhigh",
) -> dict:
    """Run the consultation pipeline programmatically.

    Returns a dict with all required output fields. Never raises.
    Status is one of: ok, blocked, timeout_uncertain, error.
    """
    dispatch = DispatchState.NO_DISPATCH

    try:
        if reasoning_effort not in _VALID_EFFORTS:
            raise ConsultationError(
                f"invalid reasoning_effort: must be one of {sorted(_VALID_EFFORTS)}"
            )

        verdict = check_tool_input({"prompt": prompt}, START_POLICY)
        if verdict.action == "block":
            raise CredentialBlockError(verdict.reason or "credential detected")

        _check_codex_version()

        cmd = _build_command(
            prompt=prompt,
            thread_id=thread_id,
            sandbox="read-only",
            model=model,
            reasoning_effort=reasoning_effort,
        )

        dispatch = DispatchState.DISPATCHED_NO_TOKEN
        stdout_text, returncode = _run_subprocess(cmd)

        parsed = _parse_jsonl(stdout_text)

        if parsed["continuation_id"]:
            dispatch = DispatchState.COMPLETE

        return _result(
            "ok", dispatched=True,
            continuation_id=parsed["continuation_id"],
            response_text=parsed["response_text"],
            token_usage=parsed["token_usage"],
            runtime_failures=parsed["runtime_failures"],
            error=None, dispatch_state=dispatch.value,
        )

    except CredentialBlockError as exc:
        return _result(
            "blocked", dispatched=False, error=str(exc),
            continuation_id=None, response_text=None,
            token_usage=None, runtime_failures=[],
            dispatch_state=DispatchState.NO_DISPATCH.value,
        )

    except SubprocessTimeout as exc:
        partial_token = None
        try:
            partial = _parse_jsonl(exc.partial_stdout)
            partial_token = partial.get("continuation_id")
        except ConsultationError:
            pass

        if partial_token:
            dispatch = DispatchState.DISPATCHED_WITH_TOKEN_UNCERTAIN

        return _result(
            "timeout_uncertain", dispatched=True, error=str(exc),
            continuation_id=partial_token, response_text=None,
            token_usage=None, runtime_failures=[],
            dispatch_state=dispatch.value,
        )

    except ConsultationError as exc:
        return _result(
            "error", dispatched=(dispatch != DispatchState.NO_DISPATCH),
            error=str(exc), continuation_id=None,
            response_text=None, token_usage=None, runtime_failures=[],
            dispatch_state=dispatch.value,
        )

    except Exception as exc:
        return _result(
            "error", dispatched=(dispatch != DispatchState.NO_DISPATCH),
            error=f"internal error: {exc}", continuation_id=None,
            response_text=None, token_usage=None, runtime_failures=[],
            dispatch_state=dispatch.value,
        )
```

**3c. Refactor `run()` to use `consult()`:**

Replace the existing `run()` function (line 337-421) with:

```python
def run(input_path: Path) -> int:
    """Execute the consultation pipeline from file. Returns exit code."""
    try:
        phase_a = _parse_input(input_path)
    except ConsultationError as exc:
        print(_output(
            "error", dispatched=False, error=str(exc),
            continuation_id=None, response_text=None,
            token_usage=None, runtime_failures=[],
            dispatch_state=DispatchState.NO_DISPATCH.value,
        ))
        return 1

    result = consult(
        prompt=phase_a["prompt"],
        thread_id=phase_a["thread_id"],
        model=phase_a["model"],
        reasoning_effort=phase_a["reasoning_effort"],
    )
    print(json.dumps(result))
    return 0 if result["status"] in ("ok", "blocked") else 1
```

- [ ] **Step 4: Run all tests to verify**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_codex_consult.py -v`
Expected: ALL PASS (existing `TestRun` tests + new `TestConsult` tests)

The refactor preserves `run()` semantics:
- `_parse_input` errors → `_output()` + exit 1 (same as before)
- `consult()` result dict → `json.dumps()` + exit code based on status (same JSON output)

- [ ] **Step 5: Commit**

```bash
git add scripts/codex_consult.py tests/test_codex_consult.py
git commit -m "feat(cross-model): extract consult() programmatic API from codex_consult.py"
```

---

## Task 3: Write `codex_shim.py` — translation layer and safety policy update

**Files:**
- Create: `scripts/codex_shim.py`
- Create: `tests/test_codex_shim.py`
- Modify: `scripts/consultation_safety.py:46`

**FastMCP schema constraint:** FastMCP wraps Pydantic model parameters in a nested `{"params": {...}}` schema (verified empirically). Using flat Python function parameters produces the correct flat schema. The upstream `approval-policy` (hyphen) becomes `approval_policy` (underscore) because hyphens are invalid Python identifiers. `threadId` (camelCase) works directly as a Python identifier.

**Safety policy update:** `consultation_safety.py:START_POLICY.expected_fields` has `"approval-policy"`. Claude will send `"approval_policy"` (underscore) based on the shim's schema. Adding the underscore variant prevents spurious shadow telemetry.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_codex_shim.py`:

```python
"""Tests for codex_shim MCP compatibility server."""

from __future__ import annotations


class TestExtractReasoningEffort:
    """Extract model_reasoning_effort from MCP config object."""

    def test_extracts_from_config(self) -> None:
        from scripts.codex_shim import _extract_reasoning_effort
        assert _extract_reasoning_effort({"model_reasoning_effort": "high"}) == "high"

    def test_defaults_to_xhigh(self) -> None:
        from scripts.codex_shim import _extract_reasoning_effort
        assert _extract_reasoning_effort(None) == "xhigh"

    def test_defaults_on_missing_key(self) -> None:
        from scripts.codex_shim import _extract_reasoning_effort
        assert _extract_reasoning_effort({"other_key": "value"}) == "xhigh"

    def test_defaults_on_non_string_value(self) -> None:
        from scripts.codex_shim import _extract_reasoning_effort
        assert _extract_reasoning_effort({"model_reasoning_effort": 42}) == "xhigh"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_codex_shim.py::TestExtractReasoningEffort -v`
Expected: FAIL with `ImportError` (codex_shim not defined yet)

- [ ] **Step 3: Create `codex_shim.py` with translation function**

Create `scripts/codex_shim.py`:

```python
"""Thin MCP compatibility shim for codex consultation.

Exposes two FastMCP tools (``codex`` and ``codex-reply``) that translate
MCP tool parameters to the codex_consult adapter and format responses
as structuredContent with threadId.

Translation-only: no safety, analytics, or continuity logic.
Safety is enforced by codex_guard.py PreToolUse hook (fires on MCP tool
name prefix ``mcp__plugin_cross-model_codex__``). Analytics are owned
by skills.

Design: D-prime architecture — adapter owns transport, shim provides
backward-compatible MCP interface.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import CallToolResult, TextContent

if __package__:
    from scripts.codex_consult import consult
else:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from codex_consult import consult  # type: ignore[import-not-found,no-redef]


# ---------------------------------------------------------------------------
# Translation
# ---------------------------------------------------------------------------


def _extract_reasoning_effort(config: dict[str, Any] | None) -> str:
    """Extract model_reasoning_effort from MCP config object."""
    if config and isinstance(config.get("model_reasoning_effort"), str):
        return config["model_reasoning_effort"]
    return "xhigh"
```

- [ ] **Step 4: Update `consultation_safety.py` expected_fields**

In `scripts/consultation_safety.py:46`, change:
```python
    expected_fields={"sandbox", "approval-policy", "model", "profile"},
```
to:
```python
    expected_fields={"sandbox", "approval-policy", "approval_policy", "model", "profile"},
```

This prevents spurious shadow telemetry when the shim's schema causes Claude to send `approval_policy` (underscore) instead of `approval-policy` (hyphen).

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_codex_shim.py::TestExtractReasoningEffort tests/test_consultation_safety.py -v`
Expected: ALL PASS

- [ ] **Step 6: Commit**

```bash
git add scripts/codex_shim.py tests/test_codex_shim.py scripts/consultation_safety.py
git commit -m "feat(cross-model): codex shim translation layer and safety policy update"
```

---

## Task 4: Write `codex_shim.py` — MCP response builder

**Files:**
- Modify: `scripts/codex_shim.py`
- Modify: `tests/test_codex_shim.py`

The response builder translates the adapter's result dict into a `CallToolResult` with `structuredContent.threadId`. This is the critical integration point — the `codex-dialogue` agent reads `structuredContent.threadId`, and `codex_guard.py` PostToolUse reads it for telemetry.

**Response shape (must match upstream `codex mcp-server`):**
```json
{
  "content": [{"type": "text", "text": "<response text>"}],
  "structuredContent": {"threadId": "<continuation_id>", "content": "<response text>"},
  "isError": false
}
```

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_codex_shim.py`:

```python
from mcp.types import CallToolResult, TextContent


class TestBuildResponse:
    """Translate adapter result dict to MCP CallToolResult."""

    def test_success_has_structured_content(self) -> None:
        from scripts.codex_shim import _build_response
        result = _build_response({
            "status": "ok",
            "continuation_id": "thr_123",
            "response_text": "Here is the analysis.",
            "token_usage": {"input_tokens": 10, "output_tokens": 5},
            "runtime_failures": [],
            "error": None,
        })
        assert isinstance(result, CallToolResult)
        assert result.isError is False
        assert result.structuredContent == {
            "threadId": "thr_123",
            "content": "Here is the analysis.",
        }
        assert len(result.content) == 1
        assert result.content[0].text == "Here is the analysis."

    def test_blocked_is_error(self) -> None:
        from scripts.codex_shim import _build_response
        result = _build_response({
            "status": "blocked",
            "error": "AWS key detected",
        })
        assert result.isError is True
        assert "Blocked" in result.content[0].text

    def test_error_is_error(self) -> None:
        from scripts.codex_shim import _build_response
        result = _build_response({
            "status": "error",
            "error": "codex not found on PATH",
        })
        assert result.isError is True
        assert "codex not found" in result.content[0].text

    def test_timeout_preserves_partial_token(self) -> None:
        from scripts.codex_shim import _build_response
        result = _build_response({
            "status": "timeout_uncertain",
            "error": "exec failed: process timeout",
            "continuation_id": "thr_partial",
        })
        assert result.isError is True
        assert "Timeout" in result.content[0].text
        assert result.structuredContent == {"threadId": "thr_partial", "content": ""}

    def test_timeout_without_token(self) -> None:
        from scripts.codex_shim import _build_response
        result = _build_response({
            "status": "timeout_uncertain",
            "error": "exec failed: process timeout",
            "continuation_id": None,
        })
        assert result.isError is True
        assert result.structuredContent == {"threadId": None, "content": ""}

    def test_null_response_text_uses_empty_string(self) -> None:
        from scripts.codex_shim import _build_response
        result = _build_response({
            "status": "ok",
            "continuation_id": "thr_456",
            "response_text": None,
        })
        assert result.isError is False
        assert result.structuredContent["content"] == ""
        assert result.content[0].text == ""

    def test_null_continuation_id_preserved(self) -> None:
        from scripts.codex_shim import _build_response
        result = _build_response({
            "status": "ok",
            "continuation_id": None,
            "response_text": "Some response",
        })
        assert result.structuredContent["threadId"] is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_codex_shim.py::TestBuildResponse -v`
Expected: FAIL with `ImportError` (_build_response not defined yet)

- [ ] **Step 3: Implement `_build_response`**

Append to `scripts/codex_shim.py` after the `_extract_reasoning_effort` function:

```python
def _build_response(result: dict) -> CallToolResult:
    """Translate adapter result to MCP CallToolResult with structuredContent.

    Success responses include structuredContent.threadId for consumers.
    Timeout responses include structuredContent with partial continuation_id
    (agents may use it for recovery). Block/error responses omit structuredContent.
    """
    status = result.get("status", "error")
    response_text = result.get("response_text") or ""
    continuation_id = result.get("continuation_id")

    if status == "timeout_uncertain":
        error_msg = result.get("error", "unknown error")
        return CallToolResult(
            content=[TextContent(type="text", text=f"Timeout: {error_msg}")],
            structuredContent={"threadId": continuation_id, "content": ""},
            isError=True,
        )

    if status in ("blocked", "error"):
        error_label = "Blocked" if status == "blocked" else "Error"
        error_msg = result.get("error", "unknown error")
        return CallToolResult(
            content=[TextContent(type="text", text=f"{error_label}: {error_msg}")],
            isError=True,
        )

    return CallToolResult(
        content=[TextContent(type="text", text=response_text)],
        structuredContent={
            "threadId": continuation_id,
            "content": response_text,
        },
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_codex_shim.py::TestBuildResponse -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/codex_shim.py tests/test_codex_shim.py
git commit -m "feat(cross-model): codex shim MCP response builder"
```

---

## Task 5: Write `codex_shim.py` — FastMCP server and tool handlers

**Files:**
- Modify: `scripts/codex_shim.py`
- Modify: `tests/test_codex_shim.py`

The server exposes two tools matching the upstream `codex mcp-server`:
- `codex` → new conversation (calls `consult()` without `thread_id`)
- `codex-reply` → continue conversation (calls `consult()` with `thread_id`)

The server name is `"codex"` — Claude Code constructs MCP tool names as `mcp__plugin_<plugin>_<server>__<tool>`. With server name `codex` in plugin `cross-model`, the tools become:
- `mcp__plugin_cross-model_codex__codex`
- `mcp__plugin_cross-model_codex__codex-reply`

These match the names `codex_guard.py` fires on (line 65: `mcp__plugin_cross-model_codex__codex-reply`).

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_codex_shim.py`:

```python
import asyncio
from unittest.mock import patch, MagicMock


class TestCreateServer:
    """FastMCP server creation and tool registration."""

    def test_server_has_codex_tool(self) -> None:
        from scripts.codex_shim import create_server
        server = create_server()
        tools = server._tool_manager.list_tools()
        tool_names = [t.name for t in tools]
        assert "codex" in tool_names

    def test_server_has_codex_reply_tool(self) -> None:
        from scripts.codex_shim import create_server
        server = create_server()
        tools = server._tool_manager.list_tools()
        tool_names = [t.name for t in tools]
        assert "codex-reply" in tool_names

    def test_server_name_is_codex(self) -> None:
        from scripts.codex_shim import create_server
        server = create_server()
        assert server.name == "codex"

    def test_codex_tool_schema_is_flat(self) -> None:
        from scripts.codex_shim import create_server
        server = create_server()
        tool = server._tool_manager._tools["codex"]
        props = tool.parameters["properties"]
        assert "prompt" in props
        assert "model" in props
        assert "config" in props
        # No nested "params" wrapper
        assert "params" not in props


class TestRoundTrip:
    """Full round-trip: mock consult, dispatch through FastMCP tool, verify response."""

    @patch("scripts.codex_shim.consult")
    def test_codex_new_conversation(self, mock_consult: MagicMock) -> None:
        from scripts.codex_shim import create_server
        from mcp.types import CallToolResult
        mock_consult.return_value = {
            "status": "ok",
            "dispatched": True,
            "continuation_id": "thr_new",
            "response_text": "Analysis complete.",
            "token_usage": {"input_tokens": 100, "output_tokens": 50},
            "runtime_failures": [],
            "error": None,
            "dispatch_state": "complete",
        }
        server = create_server()
        tool = server._tool_manager._tools["codex"]
        result = asyncio.run(tool.run({
            "prompt": "review this code",
            "config": {"model_reasoning_effort": "high"},
            "model": "o3-pro",
        }))
        assert isinstance(result, CallToolResult)
        assert result.structuredContent["threadId"] == "thr_new"
        assert result.content[0].text == "Analysis complete."
        mock_consult.assert_called_once_with(
            prompt="review this code",
            model="o3-pro",
            reasoning_effort="high",
        )

    @patch("scripts.codex_shim.consult")
    def test_codex_reply_passes_thread_id(self, mock_consult: MagicMock) -> None:
        from scripts.codex_shim import create_server
        from mcp.types import CallToolResult
        mock_consult.return_value = {
            "status": "ok",
            "dispatched": True,
            "continuation_id": "thr_continued",
            "response_text": "Follow-up answer.",
            "token_usage": None,
            "runtime_failures": [],
            "error": None,
            "dispatch_state": "complete",
        }
        server = create_server()
        tool = server._tool_manager._tools["codex-reply"]
        result = asyncio.run(tool.run({
            "prompt": "elaborate on point 2",
            "threadId": "thr_original",
        }))
        assert isinstance(result, CallToolResult)
        assert result.structuredContent["threadId"] == "thr_continued"
        mock_consult.assert_called_once_with(
            prompt="elaborate on point 2",
            thread_id="thr_original",
        )

    @patch("scripts.codex_shim.consult")
    def test_codex_blocked_returns_error(self, mock_consult: MagicMock) -> None:
        from scripts.codex_shim import create_server
        mock_consult.return_value = {
            "status": "blocked",
            "dispatched": False,
            "error": "credential detected",
            "continuation_id": None,
            "response_text": None,
            "token_usage": None,
            "runtime_failures": [],
            "dispatch_state": "no_dispatch",
        }
        server = create_server()
        tool = server._tool_manager._tools["codex"]
        result = asyncio.run(tool.run({"prompt": "AKIAIOSFODNN7EXAMPLE"}))
        assert result.isError is True
        assert "Blocked" in result.content[0].text
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_codex_shim.py::TestCreateServer tests/test_codex_shim.py::TestRoundTrip -v`
Expected: FAIL with `ImportError` (create_server not defined yet)

- [ ] **Step 3: Implement `create_server()` and `main()`**

Append to `scripts/codex_shim.py`:

```python
# ---------------------------------------------------------------------------
# FastMCP server
# ---------------------------------------------------------------------------


def create_server() -> FastMCP:
    """Create the codex MCP shim server."""
    mcp = FastMCP("codex")

    @mcp.tool(name="codex")
    def codex_tool(
        prompt: str,
        sandbox: str | None = None,
        model: str | None = None,
        approval_policy: str | None = None,
        config: dict | None = None,
        profile: str | None = None,
    ) -> CallToolResult:
        """Start a new Codex consultation."""
        result = consult(
            prompt=prompt,
            model=model,
            reasoning_effort=_extract_reasoning_effort(config),
        )
        return _build_response(result)

    @mcp.tool(name="codex-reply")
    def codex_reply_tool(prompt: str, threadId: str) -> CallToolResult:
        """Continue an existing Codex conversation."""
        result = consult(prompt=prompt, thread_id=threadId)
        return _build_response(result)

    return mcp


def main() -> None:
    """Entry point for the codex MCP shim server."""
    server = create_server()
    server.run()


if __name__ == "__main__":
    main()
```

**Verified:** FastMCP passes `CallToolResult` return values through without double-wrapping (tested with both `convert_result=False` and `convert_result=True`). `structuredContent` is preserved.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_codex_shim.py -v`
Expected: ALL PASS (all shim tests)

- [ ] **Step 5: Commit**

```bash
git add scripts/codex_shim.py tests/test_codex_shim.py
git commit -m "feat(cross-model): codex shim FastMCP server with tool handlers"
```

---

## Task 6: Full test suite verification

**Files:**
- No changes (verification only)

- [ ] **Step 1: Run full cross-model plugin test suite**

Run: `cd packages/plugins/cross-model && uv run pytest -v`
Expected: 755+ tests pass (733 existing + 5 consult API + 17 shim)

The 1 existing collection error (`test_credential_parity.py` — depends on `context_injection` module) is pre-existing and unrelated.

- [ ] **Step 2: Verify test count**

Run: `cd packages/plugins/cross-model && uv run pytest --co -q 2>&1 | tail -3`
Expected: `755 tests collected` (or more)

- [ ] **Step 3: Run lint check**

Run: `cd packages/plugins/cross-model && uv run ruff check scripts/codex_shim.py tests/test_codex_shim.py`
Expected: No errors

- [ ] **Step 4: Final commit (if lint fixes needed)**

If lint fixes were required:
```bash
git add scripts/codex_shim.py tests/test_codex_shim.py
git commit -m "style(cross-model): lint fixes for codex shim"
```

---

## Post-Implementation Notes

### What this plan does NOT cover (T4 territory)

- **`.mcp.json` update**: Replacing the upstream `codex mcp-server` entry with the local shim. This is T4.
- **End-to-end smoke test**: Calling `/codex` through the full stack. This requires the `.mcp.json` wiring.
- **Skill/agent updates**: None needed — the shim is backward-compatible by design.

### Integration verification checklist (for T4)

After wiring the shim into `.mcp.json`, verify:

| Check | How |
|-------|-----|
| `codex_guard.py` PreToolUse fires on shim tool calls | Tool name prefix `mcp__plugin_cross-model_codex__` matches hook matchers |
| `codex-dialogue` agent reads `structuredContent.threadId` | Response shape: `{ structuredContent: { threadId, content }, content: [...] }` |
| `codex_guard.py` PostToolUse reads `structuredContent.threadId` | Same response shape |
| `CODEX_SANDBOX=seatbelt` propagated | Set in `.mcp.json` env AND in `codex_consult.py:_run_subprocess` |
| Credential scanning still blocks | Double-scan: hook layer + adapter layer |
