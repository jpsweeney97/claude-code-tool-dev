# Persistence Replay Hardening and Type Narrowing

Design for fixing three deferred persistence replay findings (I2, I3, I4) from the T-03 second review and two type improvements (F4, F6). All changes target the `codex-collaboration` plugin at `packages/plugins/codex-collaboration/`.

## Origin

Findings from the T-03 safety substrate second review (PR #90, squash-merged at `43fa3ba5`):

| Finding | File | Bug |
|---------|------|-----|
| I2 | `turn_store.py:70` | One malformed JSONL record crashes entire TurnStore replay via `KeyError` |
| I3 | `turn_store.py`, `lineage_store.py`, `journal.py` | Corrupt mid-file records silently discarded — no distinction from expected trailing truncation |
| I4 | `lineage_store.py:110-127` | Unknown operation types silently dropped during lineage replay |
| F4 | `profiles.py:22-29` | `ResolvedProfile` fields accept arbitrary strings — typos propagate silently |
| F6 | `models.py:123` | `AdvisoryRuntimeState.session` typed as `Any` instead of concrete `AppServerRuntimeSession` |

## Branches

Two branches with different risk profiles:

| Branch | Scope | Classification |
|--------|-------|----------------|
| `fix/persistence-replay-hardening` | I2, I3, I4 — shared replay helper, store migrations, corruption diagnostics | Correctness debt on delivered R2 infrastructure |
| `chore/type-narrowing` | F4, F6 — literal types, concrete session type, runtime validation | Behavior-preserving cleanup |

Execution order: fix branch first, chore branch second. Within the fix branch, incremental migration: helper first, then turn_store (simplest), lineage_store (adds unknown-op), journal (adds dataclass construction).

## Branch 1: Persistence Replay Hardening

### Shared Replay Helper (`server/replay.py`)

A new module with two layers:

**Layer 1 (line decoding):** Owned by the helper. Iterates all lines with physical line numbers (`enumerate(f, start=1)`), skips blank lines, attempts `json.loads`, classifies parse failures as trailing truncation or mid-file corruption using deferred single-pass classification, and rejects non-dict JSON as schema violations before reaching the callback.

**Layer 2 (record application):** Owned by per-store callbacks. Each store provides a callback that validates record schema (field presence, field types) and applies the record. The callback raises `SchemaViolation` or `UnknownOperation` for diagnosed failures. All other exceptions propagate as programmer bugs.

#### Diagnostic Model

```python
@dataclass(frozen=True)
class ReplayDiagnostic:
    line_number: int  # Physical file line number (1-based)
    label: Literal[
        "trailing_truncation",
        "mid_file_corruption",
        "schema_violation",
        "unknown_operation",
    ]
    detail: str


@dataclass(frozen=True)
class ReplayDiagnostics:
    diagnostics: tuple[ReplayDiagnostic, ...]

    @property
    def has_warnings(self) -> bool:
        """True if any non-trailing diagnostics exist."""
        return any(
            d.label != "trailing_truncation" for d in self.diagnostics
        )
```

#### Exception Types

```python
class SchemaViolation(Exception):
    """Raised by store callback when a parsed record has wrong/missing fields."""


class UnknownOperation(Exception):
    """Raised by store callback when a parsed record has an unrecognized op."""

    def __init__(self, op: str | None) -> None:
        self.op = op
        super().__init__(f"unknown operation: {op!r}")
```

`UnknownOperation` carries the `op` string as an attribute for consistent detail construction.

#### Helper Signature

```python
def replay_jsonl(
    path: Path,
    apply: Callable[[dict[str, Any]], T | None],
) -> tuple[tuple[T, ...], ReplayDiagnostics]:
```

#### Replay Algorithm

Single-pass with deferred trailing-truncation classification:

1. If `path` does not exist, return `((), ReplayDiagnostics(()))`.
2. Iterate all lines with `enumerate(f, start=1)`.
3. Skip blank/whitespace-only lines.
4. For each non-empty line, attempt `json.loads(line)`:
   - **`JSONDecodeError`**: Record `line_number` as a pending parse failure. Classification deferred to step 5.
   - **Success, but `type(parsed) is not dict`**: Emit `schema_violation` diagnostic (`"expected JSON object, got {type}"`) immediately. Record this line as a successful-JSON line for trailing classification purposes.
   - **Success, `dict`**: Call `apply(parsed)`:
     - Returns `T` → collect in results.
     - Returns `None` → skip result collection.
     - Raises `SchemaViolation` → emit `schema_violation` diagnostic. Record as successful-JSON line.
     - Raises `UnknownOperation` → emit `unknown_operation` diagnostic. Record as successful-JSON line.
     - Raises anything else → **propagate unhandled** (programmer bug in callback).
5. After the loop, classify pending parse failures:
   - Determine the last line number that produced successful JSON (including lines that yielded schema/unknown diagnostics — JSON parsing itself succeeded).
   - Parse failures **after** that last-valid-JSON line → `trailing_truncation`.
   - Parse failures **at or before** that last-valid-JSON line → `mid_file_corruption`.
   - If no line produced successful JSON → all parse failures are `trailing_truncation` (entire file is one crash tail).
6. Merge all diagnostics, sort by `line_number`, return `(tuple(results), ReplayDiagnostics(tuple(sorted_diagnostics)))`.

#### Replay Contract Table

| Input condition | Classification | Behavior |
|----------------|---------------|----------|
| Empty/whitespace line | — | Skip |
| `JSONDecodeError` at EOF tail | `trailing_truncation` | Skip, count |
| `JSONDecodeError` mid-file | `mid_file_corruption` | Skip, warn |
| Valid JSON, not a dict | `schema_violation` | Skip, warn (before callback) |
| Valid dict, callback raises `SchemaViolation` | `schema_violation` | Skip, warn |
| Valid dict, callback raises `UnknownOperation` | `unknown_operation` | Skip, warn |
| Valid dict, callback raises other exception | Programmer bug | **Propagate** |
| Valid dict, callback returns `None` | No-op | Skip result collection |
| Valid dict, callback returns `T` | Success | Collect result |

### Per-Store Callbacks

#### TurnStore (`server/turn_store.py`)

Fixes I2. Replace `_replay()` with `replay_jsonl()` plus typed callback.

Callback validates:
- `collaboration_id` present and `isinstance(x, str)`
- `turn_sequence` present and `type(x) is int`
- `context_size` present and `type(x) is int`

Returns `tuple[str, int]` — composite key and context_size. `_replay()` collects into a `dict` (last-write-wins from tuple ordering).

#### LineageStore (`server/lineage_store.py`)

Fixes I4. Replace `_replay()` with `replay_jsonl()` plus closure-captured accumulator callback.

Callback validates:
- `op` present, `isinstance(x, str)` — missing or non-string `op` is `SchemaViolation`, not `UnknownOperation`
- `collaboration_id` present and `isinstance(x, str)`
- Known ops (`create`, `update_status`, `update_runtime`): validate required fields per operation. Extra fields on known ops are **silently ignored** (forward-compatible).
- Unknown ops: raise `UnknownOperation(op)`.

Callback mutates a closure-captured `dict[str, CollaborationHandle]`, returns `None` always. The `results` tuple from `replay_jsonl` is empty; the real output is the closure-captured dict.

#### Journal (`server/journal.py`)

Replace `_terminal_phases()` with `replay_jsonl()` plus typed callback.

Callback validates all `OperationJournalEntry` field types before dataclass construction:
- `idempotency_key`: `isinstance(x, str)`
- `operation`: `isinstance(x, str)`, value in `("thread_creation", "turn_dispatch")` — unknown values are `SchemaViolation` (not `UnknownOperation`, which is lineage-specific)
- `phase`: `isinstance(x, str)`, value in `("intent", "dispatched", "completed")` — unknown values are `SchemaViolation`
- `collaboration_id`: `isinstance(x, str)`
- `created_at`: `isinstance(x, str)`
- `repo_root`: `isinstance(x, str)`
- Optional integer fields (`turn_sequence`, `context_size`): `type(x) is int` when present
- Optional string fields (`codex_thread_id`, `runtime_id`): `isinstance(x, str)` when present

Returns `tuple[str, OperationJournalEntry]` — idempotency key and entry. `_terminal_phases()` collects into a dict (last-write-wins).

### Store Health API

Each store exposes:

```python
def check_health(self) -> ReplayDiagnostics:
    """Replay and return diagnostics. For explicit diagnostic access."""
```

Internal `_replay()` methods discard diagnostics (performance path — called on every `get()`/`list()`). `check_health()` calls `replay_jsonl()` and returns the diagnostics object.

No production caller is wired in this branch. Tests are the primary consumer. Surfacing diagnostics through `codex.status` or audit events requires a spec amendment to `contracts.md` and is out of scope.

### Integer Validation Rule

All integer field checks use `type(x) is int`, not `isinstance(x, int)`. Python's `bool` subclasses `int`, so `isinstance(True, int)` returns `True`. JSON `true`/`false` must not pass integer validation in replay records.

### Extra-Field Policy

Extra fields on known operation types are **silently ignored**. This is intentional forward-compatibility: a record written by a newer version with additional fields is still interpretable for its known operation. No diagnostic is emitted.

This matches the existing behavior at `lineage_store.py:117` where `CollaborationHandle.__dataclass_fields__` is used as a key filter.

### Test Plan

| Test file | New tests |
|-----------|-----------|
| `tests/test_replay.py` (NEW) | Trailing truncation classification, mid-file corruption classification, schema violation (missing field, wrong type, non-dict JSON, bool-as-int), unknown operation, mixed valid/corrupt, all-corrupt file, empty file, missing file, diagnostics ordering, programmer-bug propagation |
| `tests/test_turn_store.py` | Malformed record doesn't crash replay (I2 regression), schema violation on wrong types, check_health returns diagnostics |
| `tests/test_lineage_store.py` | Unknown op diagnosed (I4 regression), schema violation on missing fields, check_health returns diagnostics |
| `tests/test_journal.py` | Schema violation on wrong types, check_health returns diagnostics |

## Branch 2: Type Narrowing

### F4: Literal Types for ResolvedProfile (`server/profiles.py`)

Define literal types:

```python
Posture = Literal["collaborative", "adversarial", "exploratory", "evaluative", "comparative"]
Effort = Literal["minimal", "low", "medium", "high", "xhigh"]
SandboxPolicy = Literal["read-only"]
ApprovalPolicy = Literal["never"]
```

`SandboxPolicy` and `ApprovalPolicy` are single-value literals reflecting the R1 validation gate at `profiles.py:119-128`. When freeze-and-rotate lands, these literals expand intentionally.

Narrow `ResolvedProfile`:

```python
@dataclass(frozen=True)
class ResolvedProfile:
    posture: Posture
    turn_budget: int
    effort: Effort | None
    sandbox: SandboxPolicy
    approval_policy: ApprovalPolicy
```

Narrow `resolve_profile()` public API:

```python
def resolve_profile(
    *,
    profile_name: str | None = None,
    explicit_posture: Posture | None = None,
    explicit_turn_budget: int | None = None,
    explicit_effort: Effort | None = None,
    explicit_sandbox: SandboxPolicy | None = None,
    explicit_approval_policy: ApprovalPolicy | None = None,
) -> ResolvedProfile:
```

Typed parameters for code callers. Runtime validation for YAML-loaded values only:

```python
_VALID_POSTURES: frozenset[str] = frozenset(get_args(Posture))
_VALID_EFFORTS: frozenset[str] = frozenset(get_args(Effort))

# After YAML resolution, before construction:
if posture not in _VALID_POSTURES:
    raise ProfileValidationError(
        f"Profile resolution failed: unknown posture. "
        f"Got: posture={posture!r:.100}"
    )
if effort is not None and effort not in _VALID_EFFORTS:
    raise ProfileValidationError(
        f"Profile resolution failed: unknown effort. "
        f"Got: effort={effort!r:.100}"
    )
if not (type(turn_budget) is int and turn_budget > 0):
    raise ProfileValidationError(
        f"Profile resolution failed: turn_budget must be a positive integer. "
        f"Got: turn_budget={turn_budget!r:.100}"
    )
```

### F6: Concrete Session Type (`server/models.py`)

Replace `session: Any` with `session: AppServerRuntimeSession`:

```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .runtime import AppServerRuntimeSession
```

`from __future__ import annotations` is already present in `models.py`. The `TYPE_CHECKING` guard prevents the circular import (`models.py` → `runtime.py` → `models.py`). The annotation resolves as a string at runtime; type checkers resolve it normally.

No runtime code introspects `AdvisoryRuntimeState` annotations — verified by searching for `get_type_hints`, `__annotations__`, and `__dataclass_fields__` usage across the package.

### Test Plan

| Test file | Changes |
|-----------|---------|
| `tests/test_profiles.py` | Add tests for unknown posture rejection, unknown effort rejection, non-positive turn_budget rejection, string turn_budget rejection, bool turn_budget rejection |
| `tests/test_models_r2.py` | Verify `AdvisoryRuntimeState` accepts `AppServerRuntimeSession` instance (existing construction tests may already cover this) |

## Design Decisions

### Trailing truncation applies only to JSONDecodeError

Schema violations and unknown operations at EOF are NOT trailing truncation, because JSON parsing itself succeeded. Only lines where `json.loads` fails qualify for trailing classification. A structurally invalid but JSON-parseable line at EOF indicates version skew, bad migration, or a writer bug — not a partial append from a crash.

### Diagnostics are return-only, not retained on store instances

These stores replay on every `get()`/`list()`/`get_all()` call — there is no in-memory cache. Retaining `self.diagnostics` would be overwritten on every read operation, creating misleading stale state. Return-only ties diagnostics to the specific replay that produced them.

### Extra fields on known ops are forward-compatible

A record written by a newer version with additional fields is still interpretable for its known operation. Rejecting extra fields would make replay fragile across version upgrades. No diagnostic is emitted for extra fields.

### Unexpected callback exceptions propagate

The helper catches exactly `SchemaViolation` and `UnknownOperation`. All other callback exceptions propagate as programmer bugs. The "no hard failures" contract applies to persisted data, not code defects.

### Store health surfacing is out of scope

Wiring `check_health()` to `codex.status` or the audit log requires spec amendments to `contracts.md` and `delivery.md`. This branch delivers the diagnostic substrate; a future branch wires the consumer.

## References

| What | Where |
|------|-------|
| T-03 second review handoff | `docs/handoffs/archive/2026-03-31_13-56_t03-safety-substrate-second-review-and-merge.md` |
| Lineage store spec | `docs/superpowers/specs/codex-collaboration/contracts.md` §Lineage Store |
| Recovery and journal spec | `docs/superpowers/specs/codex-collaboration/recovery-and-journal.md` |
| Delivery roadmap | `docs/superpowers/specs/codex-collaboration/delivery.md` |
| `codex.consult` resolution | `docs/superpowers/specs/codex-collaboration/decisions.md:115-141` |
