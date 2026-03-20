# A-002: Typed Stage Handoffs — Design

## Problem

Pipeline stage inputs are untyped JSON dicts. The entrypoint `_dispatch()` function pulls 13+ fields per stage via `.get()` with implicit defaults. Field-name drift between what the skill writes and what the engine expects is caught late (at runtime, heuristically) rather than early (at construction, structurally).

Evidence: `_dispatch()` in `ticket_engine_user.py:106` and `ticket_engine_agent.py:106`.

## Solution

Frozen dataclasses with explicit `from_payload()` constructors at the dispatch boundary. One model per pipeline stage. A dedicated module (`ticket_stage_models.py`) that both entrypoints and the engine can import.

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Mechanism | Frozen dataclasses | Matches codebase patterns (`EngineResponse`, `AutonomyConfig`). Construction-time enforcement. No new dependencies. |
| Location | `scripts/ticket_stage_models.py` | Clean seam. One-way import direction. Supports future A-001 decomposition. |
| Phase 1 scope | Stage input models only, at `_dispatch()` | Delivers boundary typing with minimal blast radius. |
| Engine signatures | Unchanged | Models unpack into existing kwargs. Avoids touching 500+ tests. |
| `request_origin` | Passed separately to engine, not in models | Trusted routing state established by entrypoint, not payload data. |
| `tickets_dir` | Passed separately to engine, not in models | Resolved infrastructure, validated before dispatch. |
| `autonomy_config` | `dict[str, Any] \| None` in phase 1 | Avoids circular import with `ticket_engine_core.py`. |
| Unknown payload keys | Ignored | Payload accumulates fields across stages (classify output merged for plan, etc.). |
| Error type | `PayloadError(code, state)` in `ticket_stage_models.py` | Models don't import `EngineResponse`. Caller translates. |
| Error mapping | `need_fields` → `state="need_fields"` (exit 2), `parse_error` → `state="escalate"` (exit 1) | Preserves recoverable vs unrecoverable distinction. |

## Constraints

1. **Shape validation only, not business rules.** `from_payload()` validates that `fields` is a dict and `classify_confidence` is a float. It does NOT validate that `priority` is one of the allowed values — that stays in `ticket_validate.py` and the engine.

2. **Contract-preserving defaults.** The model layer must reproduce the exact defaults currently in `_dispatch()`:
   - `classify_confidence`: `0.0` (preflight), `None` (execute)
   - `fields`: `{}` (classify, plan, execute), `None` (preflight)
   - `hook_injected`: `False`
   - `dedup_override`: `False`
   - `dependency_override`: `False`
   - `dedup_fingerprint`: `None`
   - `target_fingerprint`: `None`
   - `duplicate_of`: `None`

3. **Import direction is one-way.** `ticket_stage_models.py` imports only stdlib. Entrypoints and engine import from it. It must not import `EngineResponse`, `AutonomyConfig`, or any ticket module.

## Module: `ticket_stage_models.py`

### `PayloadError`

```python
class PayloadError(Exception):
    """Raised when payload validation fails during stage-input construction."""
    def __init__(self, message: str, *, code: str, state: str) -> None:
        super().__init__(message)
        self.code = code    # "need_fields" or "parse_error"
        self.state = state  # "need_fields" or "escalate"
```

### `ClassifyInput`

```python
@dataclass(frozen=True)
class ClassifyInput:
    action: str
    args: dict[str, Any]
    session_id: str

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> ClassifyInput:
        # Require: action, session_id
        # Default: args={}
        # Validate: args must be dict
        ...
```

### `PlanInput`

```python
@dataclass(frozen=True)
class PlanInput:
    intent: str
    fields: dict[str, Any]
    session_id: str

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> PlanInput:
        # Require: session_id
        # Default: intent from payload["intent"] or payload["action"], fields={}
        # Validate: fields must be dict
        ...
```

Note: `intent` falls back to `payload["action"]` to preserve existing `_dispatch()` behavior.

### `PreflightInput`

```python
@dataclass(frozen=True)
class PreflightInput:
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
        # Require: action, session_id
        # Default: classify_confidence=0.0, classify_intent="",
        #          dedup_override=False, dependency_override=False,
        #          hook_injected=False, others=None
        # Validate: classify_confidence is numeric, fields is dict|None
        ...
```

### `ExecuteInput`

```python
@dataclass(frozen=True)
class ExecuteInput:
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
        # Require: action, session_id
        # Default: fields={}, dedup_override=False, dependency_override=False,
        #          hook_injected=False, others=None
        # Validate: fields must be dict, autonomy_config_data must be dict|None
        ...
```

## Entrypoint Changes

`_dispatch()` in both `ticket_engine_user.py` and `ticket_engine_agent.py` changes from:

```python
def _dispatch(subcommand: str, payload: dict, tickets_dir: Path) -> EngineResponse:
    if subcommand == "classify":
        return engine_classify(
            action=payload.get("action", ""),
            args=payload.get("args", {}),
            session_id=payload.get("session_id", ""),
            request_origin=REQUEST_ORIGIN,
        )
    # ... 40+ lines of .get() calls
```

To:

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
        # ... same pattern for plan, preflight, execute
    except PayloadError as exc:
        return EngineResponse(
            state=exc.state,
            message=f"{subcommand} payload validation failed: {exc}",
            error_code=exc.code,
        )
```

## Phase 2 (Deferred)

Phase 2 types the internal boundary — `EngineResponse.data`. Stage-specific response-data models:

- `ClassifyData` — `intent`, `confidence`, `classify_intent`, `classify_confidence`, `resolved_ticket_id`
- `PlanData` — `dedup_fingerprint`, `target_fingerprint`, `duplicate_of`, `missing_fields`, `action_plan`
- `PreflightData` — `checks_passed`, `checks_failed`, plus autonomy/notification fields
- `ExecuteData` — `ticket_path`, `changes`

These would also live in `ticket_stage_models.py`. Engine functions construct them instead of raw dicts. `EngineResponse.data` accepts either the model or its `.to_dict()` output. The skill still receives JSON — models serialize transparently.

Phase 2 is a separate plan and PR.

## Files Changed (Phase 1)

| Action | File | What changes |
|--------|------|--------------|
| Create | `scripts/ticket_stage_models.py` | 4 input models + `PayloadError` |
| Modify | `scripts/ticket_engine_user.py` | `_dispatch()` uses models |
| Modify | `scripts/ticket_engine_agent.py` | `_dispatch()` uses models |
| Create | `tests/test_stage_models.py` | Unit tests for `from_payload()` |
| Modify | `tests/test_entrypoints.py` | If dispatch error paths change |

## Testing Strategy

- **`test_stage_models.py`**: Unit tests for each model's `from_payload()`. Cover: valid payloads, missing required fields (→ `PayloadError` with `need_fields`), wrong types (→ `PayloadError` with `parse_error`), extra keys ignored, default values preserved.
- **`test_entrypoints.py`**: Integration tests that malformed payloads produce structured error responses (not tracebacks).
- **Existing `test_engine.py`**: Must continue passing unchanged — engine signatures don't change.
