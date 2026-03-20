# A-002: Typed Stage Handoffs Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the untyped `.get()`-driven payload extraction in `_dispatch()` with frozen dataclass models that validate shape and presence at the dispatch boundary.

**Architecture:** Create `ticket_stage_models.py` with 4 frozen dataclasses (one per pipeline stage) and a `PayloadError` exception. Each model has a `from_payload()` classmethod that extracts, validates, and defaults fields. The entrypoint `_dispatch()` constructs the model, catches `PayloadError`, and unpacks into existing engine kwargs. Engine signatures are unchanged.

**Tech Stack:** Python 3, dataclasses (frozen), pytest

**Design doc:** `docs/plans/2026-03-08-a002-typed-stage-handoffs-design.md`

---

## Reference: Current `_dispatch()` Defaults

These defaults MUST be preserved exactly — this is a typing refactor, not a behavior change.

| Field | Classify | Plan | Preflight | Execute |
|-------|----------|------|-----------|---------|
| `action` | `""` | — | `""` | `""` |
| `args` | `{}` | — | — | — |
| `session_id` | `""` | `""` | `""` | `""` |
| `intent` | — | `payload["intent"]` or `payload["action"]` or `""` | — | — |
| `fields` | — | `{}` | `None` | `{}` |
| `ticket_id` | — | — | `None` | `None` |
| `classify_confidence` | — | — | `0.0` | `None` |
| `classify_intent` | — | — | `""` | `None` |
| `dedup_fingerprint` | — | — | `None` | `None` |
| `target_fingerprint` | — | — | `None` | `None` |
| `duplicate_of` | — | — | `None` | — |
| `dedup_override` | — | — | `False` | `False` |
| `dependency_override` | — | — | `False` | `False` |
| `hook_injected` | — | — | `False` | `False` |
| `hook_request_origin` | — | — | — | `None` |
| `autonomy_config_data` | — | — | — | `None` (raw dict before `AutonomyConfig.from_dict`) |

---

## Task 1: Create `ticket_stage_models.py` with PayloadError, helpers, and ClassifyInput + PlanInput

**Files:**
- Create: `packages/plugins/ticket/scripts/ticket_stage_models.py`
- Create: `packages/plugins/ticket/tests/test_stage_models.py`

**Step 1: Write failing tests for PayloadError and ClassifyInput**

Create `packages/plugins/ticket/tests/test_stage_models.py`:

```python
"""Tests for ticket_stage_models.py — stage boundary input models."""
from __future__ import annotations

import pytest

from scripts.ticket_stage_models import (
    ClassifyInput,
    PayloadError,
    PlanInput,
)


class TestPayloadError:
    def test_carries_code_and_state(self):
        exc = PayloadError("missing field: action", code="need_fields", state="need_fields")
        assert str(exc) == "missing field: action"
        assert exc.code == "need_fields"
        assert exc.state == "need_fields"

    def test_parse_error_variant(self):
        exc = PayloadError("args must be a dict", code="parse_error", state="escalate")
        assert exc.code == "parse_error"
        assert exc.state == "escalate"


class TestClassifyInput:
    def test_valid_payload(self):
        inp = ClassifyInput.from_payload({
            "action": "create",
            "args": {"ticket_id": "T-001"},
            "session_id": "sess-1",
        })
        assert inp.action == "create"
        assert inp.args == {"ticket_id": "T-001"}
        assert inp.session_id == "sess-1"

    def test_defaults(self):
        inp = ClassifyInput.from_payload({
            "action": "create",
            "session_id": "sess-1",
        })
        assert inp.args == {}

    def test_empty_defaults_for_missing_strings(self):
        """Preserves current _dispatch() behavior: missing action/session_id default to ''."""
        inp = ClassifyInput.from_payload({})
        assert inp.action == ""
        assert inp.session_id == ""
        assert inp.args == {}

    def test_args_wrong_type_raises_parse_error(self):
        with pytest.raises(PayloadError) as exc_info:
            ClassifyInput.from_payload({
                "action": "create",
                "args": "not a dict",
                "session_id": "sess-1",
            })
        assert exc_info.value.code == "parse_error"
        assert exc_info.value.state == "escalate"

    def test_extra_keys_ignored(self):
        inp = ClassifyInput.from_payload({
            "action": "create",
            "args": {},
            "session_id": "sess-1",
            "extra_field": "ignored",
            "hook_injected": True,
        })
        assert inp.action == "create"

    def test_frozen(self):
        inp = ClassifyInput.from_payload({"action": "create", "session_id": "s"})
        with pytest.raises(AttributeError):
            inp.action = "update"


class TestPlanInput:
    def test_valid_payload(self):
        inp = PlanInput.from_payload({
            "intent": "create",
            "fields": {"title": "Test"},
            "session_id": "sess-1",
        })
        assert inp.intent == "create"
        assert inp.fields == {"title": "Test"}
        assert inp.session_id == "sess-1"

    def test_intent_falls_back_to_action(self):
        inp = PlanInput.from_payload({
            "action": "update",
            "session_id": "sess-1",
        })
        assert inp.intent == "update"

    def test_intent_prefers_intent_over_action(self):
        inp = PlanInput.from_payload({
            "intent": "create",
            "action": "update",
            "session_id": "sess-1",
        })
        assert inp.intent == "create"

    def test_defaults(self):
        inp = PlanInput.from_payload({})
        assert inp.intent == ""
        assert inp.fields == {}
        assert inp.session_id == ""

    def test_fields_wrong_type_raises_parse_error(self):
        with pytest.raises(PayloadError) as exc_info:
            PlanInput.from_payload({
                "intent": "create",
                "fields": ["not", "a", "dict"],
                "session_id": "sess-1",
            })
        assert exc_info.value.code == "parse_error"

    def test_frozen(self):
        inp = PlanInput.from_payload({"session_id": "s"})
        with pytest.raises(AttributeError):
            inp.intent = "update"
```

**Step 2: Run tests to verify they fail**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_stage_models.py -v`

Expected: ImportError (module doesn't exist yet)

**Step 3: Implement PayloadError, helpers, ClassifyInput, and PlanInput**

Create `packages/plugins/ticket/scripts/ticket_stage_models.py`:

```python
"""Stage-boundary input models for the ticket engine pipeline.

Frozen dataclasses with from_payload() constructors that validate shape and
presence at the dispatch boundary. Business rule validation (allowed field
values, status transitions, etc.) remains in the engine and ticket_validate.py.

Import direction: this module imports only stdlib. Entrypoints and engine
import from it. It must not import EngineResponse, AutonomyConfig, or any
ticket module.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class PayloadError(Exception):
    """Raised when payload validation fails during stage-input construction.

    code: "need_fields" (missing required data) or "parse_error" (wrong type/shape)
    state: recommended EngineResponse state — "need_fields" or "escalate"
    """

    def __init__(self, message: str, *, code: str, state: str) -> None:
        super().__init__(message)
        self.code = code
        self.state = state


# --- Extraction helpers ---


def _get_str(payload: dict[str, Any], key: str, *, default: str) -> str:
    """Get a string field with a default. Raises PayloadError if present but wrong type."""
    value = payload.get(key, default)
    if not isinstance(value, str):
        raise PayloadError(
            f"{key} must be a string, got {type(value).__name__}",
            code="parse_error",
            state="escalate",
        )
    return value


def _get_dict(payload: dict[str, Any], key: str, *, default: dict[str, Any] | None) -> dict[str, Any]:
    """Get a dict field with a default. Raises PayloadError if present but wrong type."""
    if key not in payload:
        if default is not None:
            return dict(default)  # Defensive copy.
        raise PayloadError(
            f"missing required field: {key}",
            code="need_fields",
            state="need_fields",
        )
    value = payload[key]
    if not isinstance(value, dict):
        raise PayloadError(
            f"{key} must be a dict, got {type(value).__name__}",
            code="parse_error",
            state="escalate",
        )
    return value


def _get_bool(payload: dict[str, Any], key: str, *, default: bool) -> bool:
    """Get a bool field with a default. Raises PayloadError if present but wrong type."""
    value = payload.get(key, default)
    if not isinstance(value, bool):
        raise PayloadError(
            f"{key} must be a bool, got {type(value).__name__}",
            code="parse_error",
            state="escalate",
        )
    return value


def _get_float(payload: dict[str, Any], key: str, *, default: float) -> float:
    """Get a numeric field with a default. Accepts int or float."""
    value = payload.get(key, default)
    if not isinstance(value, (int, float)):
        raise PayloadError(
            f"{key} must be a number, got {type(value).__name__}",
            code="parse_error",
            state="escalate",
        )
    return float(value)


def _get_optional_str(payload: dict[str, Any], key: str) -> str | None:
    """Get an optional string field. Returns None if absent."""
    value = payload.get(key)
    if value is not None and not isinstance(value, str):
        raise PayloadError(
            f"{key} must be a string or null, got {type(value).__name__}",
            code="parse_error",
            state="escalate",
        )
    return value


def _get_optional_float(payload: dict[str, Any], key: str) -> float | None:
    """Get an optional numeric field. Returns None if absent."""
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, (int, float)):
        raise PayloadError(
            f"{key} must be a number or null, got {type(value).__name__}",
            code="parse_error",
            state="escalate",
        )
    return float(value)


def _get_optional_dict(payload: dict[str, Any], key: str) -> dict[str, Any] | None:
    """Get an optional dict field. Returns None if absent."""
    value = payload.get(key)
    if value is not None and not isinstance(value, dict):
        raise PayloadError(
            f"{key} must be a dict or null, got {type(value).__name__}",
            code="parse_error",
            state="escalate",
        )
    return value


# --- Stage input models ---


@dataclass(frozen=True)
class ClassifyInput:
    """Input model for the classify stage."""

    action: str
    args: dict[str, Any]
    session_id: str

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> ClassifyInput:
        return cls(
            action=_get_str(payload, "action", default=""),
            args=_get_dict(payload, "args", default={}),
            session_id=_get_str(payload, "session_id", default=""),
        )


@dataclass(frozen=True)
class PlanInput:
    """Input model for the plan stage."""

    intent: str
    fields: dict[str, Any]
    session_id: str

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> PlanInput:
        return cls(
            intent=_get_str(payload, "intent", default=_get_str(payload, "action", default="")),
            fields=_get_dict(payload, "fields", default={}),
            session_id=_get_str(payload, "session_id", default=""),
        )
```

**Step 4: Run tests to verify they pass**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_stage_models.py -v`

Expected: All PASSED

**Step 5: Commit**

```bash
git add scripts/ticket_stage_models.py tests/test_stage_models.py
git commit -m "feat(ticket): add PayloadError, ClassifyInput, PlanInput stage models (A-002)"
```

---

## Task 2: Add PreflightInput and ExecuteInput

**Files:**
- Modify: `packages/plugins/ticket/scripts/ticket_stage_models.py`
- Modify: `packages/plugins/ticket/tests/test_stage_models.py`

**Step 1: Write failing tests for PreflightInput and ExecuteInput**

Add to `test_stage_models.py` imports:

```python
from scripts.ticket_stage_models import (
    ClassifyInput,
    ExecuteInput,
    PayloadError,
    PlanInput,
    PreflightInput,
)
```

Add test classes:

```python
class TestPreflightInput:
    def test_valid_payload(self):
        inp = PreflightInput.from_payload({
            "action": "create",
            "ticket_id": "T-20260302-01",
            "session_id": "sess-1",
            "classify_confidence": 0.95,
            "classify_intent": "create",
            "dedup_fingerprint": "abc123",
            "target_fingerprint": "def456",
            "fields": {"title": "Test"},
            "duplicate_of": "T-20260301-01",
            "dedup_override": True,
            "dependency_override": True,
            "hook_injected": True,
        })
        assert inp.action == "create"
        assert inp.ticket_id == "T-20260302-01"
        assert inp.classify_confidence == 0.95
        assert inp.classify_intent == "create"
        assert inp.dedup_fingerprint == "abc123"
        assert inp.target_fingerprint == "def456"
        assert inp.fields == {"title": "Test"}
        assert inp.duplicate_of == "T-20260301-01"
        assert inp.dedup_override is True
        assert inp.dependency_override is True
        assert inp.hook_injected is True

    def test_defaults(self):
        inp = PreflightInput.from_payload({})
        assert inp.action == ""
        assert inp.ticket_id is None
        assert inp.session_id == ""
        assert inp.classify_confidence == 0.0
        assert inp.classify_intent == ""
        assert inp.dedup_fingerprint is None
        assert inp.target_fingerprint is None
        assert inp.fields is None
        assert inp.duplicate_of is None
        assert inp.dedup_override is False
        assert inp.dependency_override is False
        assert inp.hook_injected is False

    def test_classify_confidence_accepts_int(self):
        inp = PreflightInput.from_payload({"classify_confidence": 1})
        assert inp.classify_confidence == 1.0
        assert isinstance(inp.classify_confidence, float)

    def test_classify_confidence_wrong_type_raises(self):
        with pytest.raises(PayloadError) as exc_info:
            PreflightInput.from_payload({"classify_confidence": "high"})
        assert exc_info.value.code == "parse_error"

    def test_fields_wrong_type_raises(self):
        with pytest.raises(PayloadError) as exc_info:
            PreflightInput.from_payload({"fields": "not a dict"})
        assert exc_info.value.code == "parse_error"

    def test_frozen(self):
        inp = PreflightInput.from_payload({})
        with pytest.raises(AttributeError):
            inp.action = "update"


class TestExecuteInput:
    def test_valid_payload(self):
        inp = ExecuteInput.from_payload({
            "action": "update",
            "ticket_id": "T-20260302-01",
            "fields": {"priority": "high"},
            "session_id": "sess-1",
            "dedup_override": True,
            "dependency_override": True,
            "target_fingerprint": "abc123",
            "autonomy_config": {"mode": "auto_audit", "max_creates": 5},
            "hook_injected": True,
            "hook_request_origin": "user",
            "classify_intent": "update",
            "classify_confidence": 0.95,
            "dedup_fingerprint": "def456",
        })
        assert inp.action == "update"
        assert inp.ticket_id == "T-20260302-01"
        assert inp.fields == {"priority": "high"}
        assert inp.session_id == "sess-1"
        assert inp.dedup_override is True
        assert inp.dependency_override is True
        assert inp.target_fingerprint == "abc123"
        assert inp.autonomy_config_data == {"mode": "auto_audit", "max_creates": 5}
        assert inp.hook_injected is True
        assert inp.hook_request_origin == "user"
        assert inp.classify_intent == "update"
        assert inp.classify_confidence == 0.95
        assert inp.dedup_fingerprint == "def456"

    def test_defaults(self):
        inp = ExecuteInput.from_payload({})
        assert inp.action == ""
        assert inp.ticket_id is None
        assert inp.fields == {}
        assert inp.session_id == ""
        assert inp.dedup_override is False
        assert inp.dependency_override is False
        assert inp.target_fingerprint is None
        assert inp.autonomy_config_data is None
        assert inp.hook_injected is False
        assert inp.hook_request_origin is None
        assert inp.classify_intent is None
        assert inp.classify_confidence is None
        assert inp.dedup_fingerprint is None

    def test_classify_confidence_none_when_absent(self):
        """Execute uses None (not 0.0) for missing classify_confidence."""
        inp = ExecuteInput.from_payload({})
        assert inp.classify_confidence is None

    def test_classify_confidence_accepts_float(self):
        inp = ExecuteInput.from_payload({"classify_confidence": 0.95})
        assert inp.classify_confidence == 0.95

    def test_autonomy_config_wrong_type_raises(self):
        with pytest.raises(PayloadError) as exc_info:
            ExecuteInput.from_payload({"autonomy_config": "not a dict"})
        assert exc_info.value.code == "parse_error"

    def test_fields_wrong_type_raises(self):
        with pytest.raises(PayloadError) as exc_info:
            ExecuteInput.from_payload({"fields": 42})
        assert exc_info.value.code == "parse_error"

    def test_frozen(self):
        inp = ExecuteInput.from_payload({})
        with pytest.raises(AttributeError):
            inp.action = "close"
```

**Step 2: Run tests to verify they fail**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_stage_models.py::TestPreflightInput tests/test_stage_models.py::TestExecuteInput -v`

Expected: ImportError (PreflightInput and ExecuteInput not defined yet)

**Step 3: Implement PreflightInput and ExecuteInput**

Add to `ticket_stage_models.py` after `PlanInput`:

```python
@dataclass(frozen=True)
class PreflightInput:
    """Input model for the preflight stage."""

    action: str
    ticket_id: str | None
    session_id: str
    classify_confidence: float
    classify_intent: str
    dedup_fingerprint: str | None
    target_fingerprint: str | None
    fields: dict[str, Any] | None
    duplicate_of: str | None
    dedup_override: bool
    dependency_override: bool
    hook_injected: bool

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> PreflightInput:
        return cls(
            action=_get_str(payload, "action", default=""),
            ticket_id=_get_optional_str(payload, "ticket_id"),
            session_id=_get_str(payload, "session_id", default=""),
            classify_confidence=_get_float(payload, "classify_confidence", default=0.0),
            classify_intent=_get_str(payload, "classify_intent", default=""),
            dedup_fingerprint=_get_optional_str(payload, "dedup_fingerprint"),
            target_fingerprint=_get_optional_str(payload, "target_fingerprint"),
            fields=_get_optional_dict(payload, "fields"),
            duplicate_of=_get_optional_str(payload, "duplicate_of"),
            dedup_override=_get_bool(payload, "dedup_override", default=False),
            dependency_override=_get_bool(payload, "dependency_override", default=False),
            hook_injected=_get_bool(payload, "hook_injected", default=False),
        )


@dataclass(frozen=True)
class ExecuteInput:
    """Input model for the execute stage."""

    action: str
    ticket_id: str | None
    fields: dict[str, Any]
    session_id: str
    dedup_override: bool
    dependency_override: bool
    target_fingerprint: str | None
    autonomy_config_data: dict[str, Any] | None
    hook_injected: bool
    hook_request_origin: str | None
    classify_intent: str | None
    classify_confidence: float | None
    dedup_fingerprint: str | None

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> ExecuteInput:
        return cls(
            action=_get_str(payload, "action", default=""),
            ticket_id=_get_optional_str(payload, "ticket_id"),
            fields=_get_dict(payload, "fields", default={}),
            session_id=_get_str(payload, "session_id", default=""),
            dedup_override=_get_bool(payload, "dedup_override", default=False),
            dependency_override=_get_bool(payload, "dependency_override", default=False),
            target_fingerprint=_get_optional_str(payload, "target_fingerprint"),
            autonomy_config_data=_get_optional_dict(payload, "autonomy_config"),
            hook_injected=_get_bool(payload, "hook_injected", default=False),
            hook_request_origin=_get_optional_str(payload, "hook_request_origin"),
            classify_intent=_get_optional_str(payload, "classify_intent"),
            classify_confidence=_get_optional_float(payload, "classify_confidence"),
            dedup_fingerprint=_get_optional_str(payload, "dedup_fingerprint"),
        )
```

**Step 4: Run tests to verify they pass**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_stage_models.py -v`

Expected: All PASSED

**Step 5: Run full suite to verify no regressions**

Run: `cd packages/plugins/ticket && uv run pytest -q`

Expected: 510 passed (baseline — models aren't wired in yet)

**Step 6: Commit**

```bash
git add scripts/ticket_stage_models.py tests/test_stage_models.py
git commit -m "feat(ticket): add PreflightInput, ExecuteInput stage models (A-002)"
```

---

## Task 3: Wire models into `_dispatch()` in both entrypoints

**Files:**
- Modify: `packages/plugins/ticket/scripts/ticket_engine_user.py:106-161`
- Modify: `packages/plugins/ticket/scripts/ticket_engine_agent.py:106-161`

**Step 1: Add integration tests for PayloadError handling at the dispatch level**

Add to the end of `packages/plugins/ticket/tests/test_entrypoints.py`:

```python
class TestPayloadValidation:
    """Entrypoints translate PayloadError into structured EngineResponse."""

    def test_classify_bad_args_type_returns_parse_error(self, tmp_path):
        output = run_entrypoint(
            "ticket_engine_user.py",
            "classify",
            {
                "action": "create",
                "args": "not a dict",
                "session_id": "test",
            },
            tmp_path,
        )
        assert output["state"] == "escalate"
        assert output["error_code"] == "parse_error"
        assert "classify" in output["message"].lower()

    def test_execute_bad_fields_type_returns_parse_error(self, tmp_path):
        output = run_entrypoint(
            "ticket_engine_user.py",
            "execute",
            {
                "action": "create",
                "fields": "not a dict",
                "session_id": "test",
                "hook_injected": True,
                "hook_request_origin": "user",
            },
            tmp_path,
        )
        assert output["state"] == "escalate"
        assert output["error_code"] == "parse_error"
        assert "execute" in output["message"].lower()

    def test_agent_entrypoint_also_validates(self, tmp_path):
        output = run_entrypoint(
            "ticket_engine_agent.py",
            "classify",
            {
                "action": "create",
                "args": 42,
                "session_id": "test",
            },
            tmp_path,
        )
        assert output["state"] == "escalate"
        assert output["error_code"] == "parse_error"
```

**Step 2: Run integration tests to verify they fail**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_entrypoints.py::TestPayloadValidation -v`

Expected: FAIL — current `_dispatch()` doesn't validate types, so `args=42` passes through to the engine which may handle it differently.

**Step 3: Update `_dispatch()` in `ticket_engine_user.py`**

Replace the entire `_dispatch()` function (lines 106-161) with:

```python
def _dispatch(subcommand: str, payload: dict, tickets_dir: Path) -> EngineResponse:
    try:
        if subcommand == "classify":
            inp = ClassifyInput.from_payload(payload)
            return engine_classify(
                action=inp.action,
                args=inp.args,
                session_id=inp.session_id,
                request_origin=REQUEST_ORIGIN,
            )
        elif subcommand == "plan":
            inp = PlanInput.from_payload(payload)
            return engine_plan(
                intent=inp.intent,
                fields=inp.fields,
                session_id=inp.session_id,
                request_origin=REQUEST_ORIGIN,
                tickets_dir=tickets_dir,
            )
        elif subcommand == "preflight":
            inp = PreflightInput.from_payload(payload)
            return engine_preflight(
                ticket_id=inp.ticket_id,
                action=inp.action,
                session_id=inp.session_id,
                request_origin=REQUEST_ORIGIN,
                classify_confidence=inp.classify_confidence,
                classify_intent=inp.classify_intent,
                dedup_fingerprint=inp.dedup_fingerprint,
                target_fingerprint=inp.target_fingerprint,
                fields=inp.fields,
                duplicate_of=inp.duplicate_of,
                dedup_override=inp.dedup_override,
                dependency_override=inp.dependency_override,
                hook_injected=inp.hook_injected,
                tickets_dir=tickets_dir,
            )
        elif subcommand == "execute":
            inp = ExecuteInput.from_payload(payload)
            autonomy_config = (
                AutonomyConfig.from_dict(inp.autonomy_config_data)
                if isinstance(inp.autonomy_config_data, dict)
                else None
            )
            return engine_execute(
                action=inp.action,
                ticket_id=inp.ticket_id,
                fields=inp.fields,
                session_id=inp.session_id,
                request_origin=REQUEST_ORIGIN,
                dedup_override=inp.dedup_override,
                dependency_override=inp.dependency_override,
                tickets_dir=tickets_dir,
                target_fingerprint=inp.target_fingerprint,
                autonomy_config=autonomy_config,
                hook_injected=inp.hook_injected,
                hook_request_origin=inp.hook_request_origin,
                classify_intent=inp.classify_intent,
                classify_confidence=inp.classify_confidence,
                dedup_fingerprint=inp.dedup_fingerprint,
            )
        else:
            return EngineResponse(
                state="escalate",
                message=f"Unknown subcommand: {subcommand!r}",
                error_code="intent_mismatch",
            )
    except PayloadError as exc:
        return EngineResponse(
            state=exc.state,
            message=f"{subcommand} payload validation failed: {exc}",
            error_code=exc.code,
        )
```

Also add the import at the top of `ticket_engine_user.py` (after the existing imports):

```python
from scripts.ticket_stage_models import (
    ClassifyInput,
    ExecuteInput,
    PayloadError,
    PlanInput,
    PreflightInput,
)
```

**Step 4: Apply the IDENTICAL changes to `ticket_engine_agent.py`**

The `_dispatch()` function and imports are the same in both files. Apply the same replacement.

**Step 5: Run integration tests**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_entrypoints.py -v`

Expected: All PASSED (including old tests + new TestPayloadValidation)

**Step 6: Run full test suite**

Run: `cd packages/plugins/ticket && uv run pytest -q`

Expected: All tests pass. The exact count depends on how many new tests were added across tasks 1-3. Baseline is 510 + new model tests + new entrypoint tests.

**Step 7: Commit**

```bash
git add scripts/ticket_engine_user.py scripts/ticket_engine_agent.py tests/test_entrypoints.py
git commit -m "refactor(ticket): wire stage models into _dispatch() boundary (A-002)"
```

---

## Task 4: Final Verification

**Step 1: Run full test suite from clean state**

Run: `cd packages/plugins/ticket && uv run pytest -v`

Expected: All tests pass.

**Step 2: Verify no behavioral change on happy paths**

Run a quick smoke test through the entrypoint:

```bash
cd packages/plugins/ticket && uv run pytest tests/test_entrypoints.py -v
```

Verify all existing entrypoint tests still pass — this confirms the dispatch refactor preserves behavior.

**Step 3: Verify import direction**

Run: `cd packages/plugins/ticket && grep -r "from scripts.ticket_engine_core" scripts/ticket_stage_models.py`

Expected: No output (stage models must not import engine core).

Run: `cd packages/plugins/ticket && grep -r "from scripts.ticket_stage_models" scripts/ticket_engine_user.py scripts/ticket_engine_agent.py`

Expected: Both files import from stage models.

**Step 4: Check commit history**

The 3 commits from this plan:
1. `feat(ticket): add PayloadError, ClassifyInput, PlanInput stage models (A-002)` — new module + tests
2. `feat(ticket): add PreflightInput, ExecuteInput stage models (A-002)` — remaining models + tests
3. `refactor(ticket): wire stage models into _dispatch() boundary (A-002)` — entrypoint changes
