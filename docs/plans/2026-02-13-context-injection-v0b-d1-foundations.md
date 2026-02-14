# Context Injection v0b D1: Foundations + Basic Redaction Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement the foundation layer for Call 2 (execute_scout): ScoutOptionRecord with atomic consume_scout(), FileKind classification, and env/ini format redactors.

**Architecture:** Six tasks across four deliverables: (1) nullable excerpt_range for suppression scenarios (types.py), (2) ScoutOptionRecord + consume_scout for Call 2 authentication (state.py + templates.py), (3) FileKind enum + classify_path for extension-based file classification (new classify.py), (4) FormatRedactOutcome types + env/ini redactors (new redact_formats.py). All production code at `packages/context-injection/context_injection/`. All tests at `packages/context-injection/tests/`.

**Tech Stack:** Python 3.14, Pydantic v2 (frozen ProtocolModel), pytest, dataclasses (frozen for internal types), os.path for path operations

**Master plan reference:** `docs/plans/2026-02-13-context-injection-v0b-master-plan.md` (authoritative for all API contracts)

**Branch:** Create `feature/context-injection-v0b-d1` from `main`.

**Test command:** `cd packages/context-injection && uv run pytest` (all) or `uv run pytest tests/test_<module>.py::TestClass::test_name -v` (specific)

**Dependencies between tasks:**
- Tasks 1, 2, 4, 5: independent (any order)
- Task 3: depends on Task 2 (consume_scout returns ScoutOptionRecord)
- Task 6: depends on Task 5 (extends redact_formats.py)

---

### Task 1: Make ReadResult.excerpt_range nullable

**Files:**
- Modify: `context_injection/types.py:326`
- Test: `tests/test_types.py`

**Step 1: Write the failing test**

Add to `tests/test_types.py`:

```python
class TestReadResultExcerptRangeNullable:
    def test_nullable_excerpt_range_accepts_none(self) -> None:
        """PEM suppression and zero-content scenarios need excerpt_range=None."""
        result = ReadResult(
            path_display="src/app.py",
            excerpt="[REDACTED:key_block]",
            excerpt_range=None,
            total_lines=100,
        )
        assert result.excerpt_range is None

    def test_non_null_excerpt_range_still_validates(self) -> None:
        result = ReadResult(
            path_display="src/app.py",
            excerpt="content here",
            excerpt_range=[1, 40],
            total_lines=100,
        )
        assert result.excerpt_range == [1, 40]

    def test_excerpt_range_rejects_wrong_length_when_not_none(self) -> None:
        with pytest.raises(Exception):
            ReadResult(
                path_display="src/app.py",
                excerpt="content",
                excerpt_range=[1],
                total_lines=100,
            )

    def test_excerpt_range_rejects_too_long(self) -> None:
        with pytest.raises(Exception):
            ReadResult(
                path_display="src/app.py",
                excerpt="content",
                excerpt_range=[1, 40, 80],
                total_lines=100,
            )

    def test_excerpt_range_rejects_wrong_item_type(self) -> None:
        """Strict mode rejects string items in list[int] field."""
        with pytest.raises(Exception):
            ReadResult(
                path_display="src/app.py",
                excerpt="content",
                excerpt_range=["1", "40"],
                total_lines=100,
            )
```

**Step 2: Run test to verify it fails**

Run: `cd packages/context-injection && uv run pytest tests/test_types.py::TestReadResultExcerptRangeNullable -v`
Expected: FAIL — `test_nullable_excerpt_range_accepts_none` fails (None not accepted by current type)

**Step 3: Write minimal implementation**

In `context_injection/types.py`, change line 326:

```python
# Before:
    excerpt_range: Annotated[list[int], Field(min_length=2, max_length=2)]

# After:
    excerpt_range: Annotated[list[int], Field(min_length=2, max_length=2)] | None
```

**Step 4: Run tests to verify pass**

Run: `cd packages/context-injection && uv run pytest tests/test_types.py::TestReadResultExcerptRangeNullable -v`
Expected: PASS (all 5 tests)

**Step 5: Run full suite**

Run: `cd packages/context-injection && uv run pytest`
Expected: All 288+ tests pass (no existing tests construct ReadResult with excerpt_range=None)

**Step 6: Commit**

```bash
git add context_injection/types.py tests/test_types.py
git commit -m "feat(context-injection): make ReadResult.excerpt_range nullable

Supports PEM suppression and zero-content scenarios where no line range
applies. Existing [start, end] validation preserved when non-null."
```

---

### Task 2: Add ScoutOptionRecord + update ScoutOptionRegistry

Coordinated refactor: adds the frozen dataclass, changes the type alias, updates templates.py to populate it, and fixes all test files that use the old tuple format.

**Files:**
- Modify: `context_injection/state.py:31-33`
- Modify: `context_injection/templates.py` (imports, `_make_read_option`, `_make_grep_option`, `match_templates` call sites)
- Modify: `tests/test_state.py:134,138` (old tuple format)
- Modify: `tests/test_pipeline.py:514` (old tuple destructuring)
- Test: `tests/test_state.py` (new ScoutOptionRecord tests)

**Step 1: Write the failing test**

Add to `tests/test_state.py` imports:

```python
from context_injection.state import ScoutOptionRecord
```

Add test class:

```python
class TestScoutOptionRecord:
    def test_construction_and_fields(self) -> None:
        spec = _make_read_spec()
        record = ScoutOptionRecord(
            spec=spec,
            token="tok_abc",
            template_id="probe.file_repo_fact",
            entity_id="e_001",
            entity_key="file_path:src/app.py",
            risk_signal=False,
            path_display="src/app.py",
            action="read",
        )
        assert record.spec is spec
        assert record.token == "tok_abc"
        assert record.template_id == "probe.file_repo_fact"
        assert record.entity_id == "e_001"
        assert record.entity_key == "file_path:src/app.py"
        assert record.risk_signal is False
        assert record.path_display == "src/app.py"
        assert record.action == "read"

    def test_frozen(self) -> None:
        record = ScoutOptionRecord(
            spec=_make_read_spec(),
            token="tok_abc",
            template_id="probe.file_repo_fact",
            entity_id="e_001",
            entity_key="file_path:src/app.py",
            risk_signal=False,
            path_display="src/app.py",
            action="read",
        )
        with pytest.raises(AttributeError):
            record.token = "different"

    def test_grep_action(self) -> None:
        from context_injection.types import GrepSpec
        spec = GrepSpec(
            action="grep",
            pattern="MyClass",
            strategy="match_context",
            max_lines=40,
            max_chars=2000,
            context_lines=2,
            max_ranges=5,
        )
        record = ScoutOptionRecord(
            spec=spec,
            token="tok_xyz",
            template_id="probe.symbol_repo_fact",
            entity_id="e_002",
            entity_key="symbol:MyClass",
            risk_signal=False,
            path_display="MyClass",
            action="grep",
        )
        assert record.action == "grep"
        assert record.entity_key == "symbol:MyClass"
```

**Step 2: Run test to verify it fails**

Run: `cd packages/context-injection && uv run pytest tests/test_state.py::TestScoutOptionRecord -v`
Expected: FAIL — `ScoutOptionRecord` not importable

**Step 3: Add ScoutOptionRecord and update type alias in state.py**

In `context_injection/state.py`, replace lines 31-32:

```python
# Before:
ScoutOptionRegistry = dict[str, tuple[ReadSpec | GrepSpec, str]]
"""scout_option_id -> (frozen ScoutSpec, HMAC token). Atomic pairs for Call 2."""

# After:
@dataclass(frozen=True)
class ScoutOptionRecord:
    """Stored metadata for a single scout option.

    Bundles everything needed to produce a protocol-compliant ScoutResult
    at execution time. Created during Call 1 (template synthesis).
    Consumed during Call 2 via consume_scout().
    """

    spec: ReadSpec | GrepSpec
    token: str
    template_id: str
    entity_id: str
    entity_key: str
    risk_signal: bool
    path_display: str
    action: str


ScoutOptionRegistry = dict[str, ScoutOptionRecord]
"""scout_option_id -> ScoutOptionRecord. Full metadata for Call 2."""
```

**Step 4: Run new tests to verify pass**

Run: `cd packages/context-injection && uv run pytest tests/test_state.py::TestScoutOptionRecord -v`
Expected: PASS

**Step 5: Update templates.py to populate ScoutOptionRecord**

In `context_injection/templates.py`:

1. Update import (line 26):

```python
# Before:
from context_injection.state import AppContext, ScoutOptionRegistry, generate_token

# After:
from context_injection.state import AppContext, ScoutOptionRecord, ScoutOptionRegistry, generate_token
```

2. In `_make_read_option` — add `template_id: str` parameter and replace tuple registration:

Add parameter to signature:
```python
def _make_read_option(
    entity: Entity,
    pd: PathDecision,
    turn_request: TurnRequest,
    ctx: AppContext,
    entities_by_id: dict[str, Entity],
    so_counter: list[int],
    spec_registry: ScoutOptionRegistry,
    template_id: str,  # NEW
) -> ReadOption:
```

Replace `spec_registry[so_id] = (spec, token)` (approx line 286) with:
```python
    entity_key = _compute_effective_key(entity, entities_by_id)
    spec_registry[so_id] = ScoutOptionRecord(
        spec=spec,
        token=token,
        template_id=template_id,
        entity_id=entity.id,
        entity_key=entity_key,
        risk_signal=risk,
        path_display=target_display,
        action="read",
    )
```

3. In `_make_grep_option` — add `template_id: str` and `entities_by_id` parameters:

```python
def _make_grep_option(
    entity: Entity,
    turn_request: TurnRequest,
    ctx: AppContext,
    so_counter: list[int],
    spec_registry: ScoutOptionRegistry,
    template_id: str,  # NEW
    entities_by_id: dict[str, Entity],  # NEW
) -> GrepOption:
```

Replace `spec_registry[so_id] = (spec, token)` (approx line 333) with:
```python
    entity_key = _compute_effective_key(entity, entities_by_id)
    spec_registry[so_id] = ScoutOptionRecord(
        spec=spec,
        token=token,
        template_id=template_id,
        entity_id=entity.id,
        entity_key=entity_key,
        risk_signal=False,
        path_display=entity.canonical,
        action="grep",
    )
```

4. Update call sites in `match_templates` (approx lines 529-544):

```python
# Grep call — add template_id and entities_by_id:
scout_option = _make_grep_option(
    entity, turn_request, ctx, so_counter, spec_registry,
    template_id=template_id, entities_by_id=entities_by_id,
)

# Read call — add template_id:
scout_option = _make_read_option(
    entity, pd, turn_request, ctx, entities_by_id, so_counter, spec_registry,
    template_id=template_id,
)
```

**Step 6: Exhaustive search for old tuple format**

Before updating known sites, verify there are no other tuple-unpacking patterns:

Run: `cd packages/context-injection && rg "(spec, token)" --type py`

Expected sites (all must be updated in this step):
- `tests/test_state.py`: `scout_options={"so_001": (spec, token)}` and `== (spec, token)`
- `tests/test_pipeline.py`: `for so_id, (spec, token) in record.scout_options.items()`

If any additional sites are found, update them following the same pattern below.

**Step 7: Update existing tests for new ScoutOptionRecord format**

In `tests/test_state.py`, update `TestTurnRequestStore.test_store_and_retrieve` (lines 126-138):

```python
# Before:
record = TurnRequestRecord(
    turn_request=req,
    scout_options={"so_001": (spec, token)},
)
ctx.store_record(ref, record)
assert ref in ctx.store
assert ctx.store[ref].scout_options["so_001"] == (spec, token)

# After:
option = ScoutOptionRecord(
    spec=spec,
    token=token,
    template_id="probe.file_repo_fact",
    entity_id="e_001",
    entity_key="file_path:src/app.py",
    risk_signal=False,
    path_display="src/app.py",
    action="read",
)
record = TurnRequestRecord(
    turn_request=req,
    scout_options={"so_001": option},
)
ctx.store_record(ref, record)
assert ref in ctx.store
assert ctx.store[ref].scout_options["so_001"] is option
```

In `tests/test_pipeline.py`, update `test_spec_registry_stored` (line 514):

```python
# Before:
for so_id, (spec, token) in record.scout_options.items():
    assert so_id.startswith("so_")
    assert isinstance(token, str)
    assert len(token) > 0

# After:
for so_id, option in record.scout_options.items():
    assert so_id.startswith("so_")
    assert isinstance(option, ScoutOptionRecord)
    assert isinstance(option.token, str)
    assert len(option.token) > 0
```

Add import at top of `tests/test_pipeline.py`:
```python
from context_injection.state import ScoutOptionRecord
```

**Step 8: Run full suite**

Run: `cd packages/context-injection && uv run pytest -v`
Expected: All tests pass

**Step 9: Commit**

```bash
git add context_injection/state.py context_injection/templates.py tests/
git commit -m "feat(context-injection): add ScoutOptionRecord, update ScoutOptionRegistry

ScoutOptionRecord bundles spec + token + metadata (template_id, entity_id,
entity_key, risk_signal, path_display, action) for Call 2 execution.
Replaces prior tuple[spec, token] in ScoutOptionRegistry."
```

---

### Task 3: Add consume_scout() to AppContext

**Files:**
- Modify: `context_injection/state.py`
- Test: `tests/test_state.py`

**Step 1: Write the failing tests**

Add helper function to `tests/test_state.py`:

```python
def _setup_consume_test(
    ctx: AppContext | None = None,
) -> tuple[AppContext, str, str, str, ScoutOptionRecord]:
    """Set up a valid consume_scout scenario.

    Returns (ctx, turn_request_ref, scout_option_id, token, expected_record).
    """
    if ctx is None:
        ctx = AppContext.create(repo_root="/tmp/repo")
    req = _make_turn_request()
    ref = make_turn_request_ref(req)

    spec = _make_read_spec()
    so_id = "so_001"
    payload = ScoutTokenPayload(
        v=1,
        conversation_id=req.conversation_id,
        turn_number=req.turn_number,
        scout_option_id=so_id,
        spec=spec,
    )
    token = generate_token(ctx.hmac_key, payload)

    option = ScoutOptionRecord(
        spec=spec,
        token=token,
        template_id="probe.file_repo_fact",
        entity_id="e_001",
        entity_key="file_path:src/app.py",
        risk_signal=False,
        path_display="src/app.py",
        action="read",
    )
    record = TurnRequestRecord(
        turn_request=req,
        scout_options={so_id: option},
    )
    ctx.store_record(ref, record)

    return ctx, ref, so_id, token, option
```

Add test class:

```python
class TestConsumeScout:
    def test_valid_consume_returns_record(self) -> None:
        ctx, ref, so_id, token, expected = _setup_consume_test()
        result = ctx.consume_scout(ref, so_id, token)
        assert result is expected

    def test_marks_record_used(self) -> None:
        ctx, ref, so_id, token, _ = _setup_consume_test()
        assert ctx.store[ref].used is False
        ctx.consume_scout(ref, so_id, token)
        assert ctx.store[ref].used is True

    def test_returns_all_metadata_fields(self) -> None:
        ctx, ref, so_id, token, _ = _setup_consume_test()
        result = ctx.consume_scout(ref, so_id, token)
        assert result.template_id == "probe.file_repo_fact"
        assert result.entity_id == "e_001"
        assert result.entity_key == "file_path:src/app.py"
        assert result.risk_signal is False
        assert result.path_display == "src/app.py"
        assert result.action == "read"

    def test_unknown_ref_raises(self) -> None:
        ctx, _, so_id, token, _ = _setup_consume_test()
        with pytest.raises(ValueError, match="turn_request_ref not found"):
            ctx.consume_scout("nonexistent:1", so_id, token)

    def test_unknown_option_id_raises(self) -> None:
        ctx, ref, _, token, _ = _setup_consume_test()
        with pytest.raises(ValueError, match="scout_option_id not found"):
            ctx.consume_scout(ref, "so_999", token)

    def test_bad_token_raises(self) -> None:
        ctx, ref, so_id, _, _ = _setup_consume_test()
        with pytest.raises(ValueError, match="token verification failed"):
            ctx.consume_scout(ref, so_id, "AAAAAAAAAAAAAAAAAAAAAA==")

    def test_replay_raises(self) -> None:
        ctx, ref, so_id, token, _ = _setup_consume_test()
        ctx.consume_scout(ref, so_id, token)  # First use
        with pytest.raises(ValueError, match="already used"):
            ctx.consume_scout(ref, so_id, token)

    def test_bad_token_does_not_set_used(self) -> None:
        """Used-bit not set on verification failure (D10 design decision)."""
        ctx, ref, so_id, _, _ = _setup_consume_test()
        with pytest.raises(ValueError, match="token verification failed"):
            ctx.consume_scout(ref, so_id, "AAAAAAAAAAAAAAAAAAAAAA==")
        assert ctx.store[ref].used is False

    def test_different_option_after_used_raises(self) -> None:
        """One scout per turn: consuming any option after used=True fails.

        Protocol guarantees scout_available=false after one consumption.
        The used bit is per-record, not per-option.
        """
        ctx = AppContext.create(repo_root="/tmp/repo")
        req = _make_turn_request()
        ref = make_turn_request_ref(req)
        spec1 = _make_read_spec()
        spec2 = _make_read_spec(resolved_path="src/other.py")
        payload1 = ScoutTokenPayload(
            v=1,
            conversation_id=req.conversation_id,
            turn_number=req.turn_number,
            scout_option_id="so_001",
            spec=spec1,
        )
        payload2 = ScoutTokenPayload(
            v=1,
            conversation_id=req.conversation_id,
            turn_number=req.turn_number,
            scout_option_id="so_002",
            spec=spec2,
        )
        token1 = generate_token(ctx.hmac_key, payload1)
        token2 = generate_token(ctx.hmac_key, payload2)
        option1 = ScoutOptionRecord(
            spec=spec1, token=token1,
            template_id="probe.file_repo_fact", entity_id="e_001",
            entity_key="file_path:src/app.py", risk_signal=False,
            path_display="src/app.py", action="read",
        )
        option2 = ScoutOptionRecord(
            spec=spec2, token=token2,
            template_id="probe.file_repo_fact", entity_id="e_002",
            entity_key="file_path:src/other.py", risk_signal=False,
            path_display="src/other.py", action="read",
        )
        record = TurnRequestRecord(
            turn_request=req,
            scout_options={"so_001": option1, "so_002": option2},
        )
        ctx.store_record(ref, record)
        ctx.consume_scout(ref, "so_001", token1)
        with pytest.raises(ValueError, match="already used"):
            ctx.consume_scout(ref, "so_002", token2)
```

**Step 2: Run tests to verify they fail**

Run: `cd packages/context-injection && uv run pytest tests/test_state.py::TestConsumeScout -v`
Expected: FAIL — `consume_scout` not defined on `AppContext`

**Step 3: Implement consume_scout**

Add method to `AppContext` class in `context_injection/state.py`:

```python
    def consume_scout(
        self,
        turn_request_ref: str,
        scout_option_id: str,
        scout_token: str,
    ) -> ScoutOptionRecord:
        """Atomic verify-and-consume for Call 2.

        Validates HMAC token, checks replay, marks used, returns record.
        All failures raise ValueError -> maps to ScoutResultInvalid.

        Check order: ref lookup -> option lookup -> HMAC verify -> replay check -> mark used.
        Used-bit NOT set on verification failure (D10 design decision).

        INVARIANT: One scout per turn. The used bit is per-record (not
        per-option). After ANY option is consumed, ALL other options on
        the same turn are blocked. This enforces the Budget Computation
        Rule: "scout_available = false, 1 scout per turn, just consumed."
        See test_different_option_after_used_raises for verification.
        """
        # 1. Look up turn request record
        record = self.store.get(turn_request_ref)
        if record is None:
            raise ValueError(
                f"consume_scout failed: turn_request_ref not found. "
                f"Got: {turn_request_ref!r:.100}"
            )

        # 2. Look up scout option
        option = record.scout_options.get(scout_option_id)
        if option is None:
            raise ValueError(
                f"consume_scout failed: scout_option_id not found. "
                f"Got: {scout_option_id!r:.100}"
            )

        # 3. Verify HMAC token
        payload = ScoutTokenPayload(
            v=1,
            conversation_id=record.turn_request.conversation_id,
            turn_number=record.turn_request.turn_number,
            scout_option_id=scout_option_id,
            spec=option.spec,
        )
        if not verify_token(self.hmac_key, payload, scout_token):
            raise ValueError(
                f"consume_scout failed: token verification failed "
                f"for {scout_option_id!r}"
            )

        # 4. Replay check (AFTER token verification — don't leak used state)
        if record.used:
            raise ValueError(
                f"consume_scout failed: record already used "
                f"for {turn_request_ref!r}"
            )

        # 5. Mark used
        record.used = True

        return option
```

**Step 4: Run tests to verify pass**

Run: `cd packages/context-injection && uv run pytest tests/test_state.py::TestConsumeScout -v`
Expected: PASS (all 9 tests)

**Step 5: Run full suite**

Run: `cd packages/context-injection && uv run pytest`
Expected: All tests pass

**Step 6: Commit**

```bash
git add context_injection/state.py tests/test_state.py
git commit -m "feat(context-injection): add consume_scout() atomic helper

Atomic verify-and-consume for Call 2: HMAC verification, replay prevention,
returns ScoutOptionRecord with all metadata. All auth failures raise
ValueError -> ScoutResultInvalid."
```

---

### Task 4: Create classify.py with FileKind enum

**Files:**
- Create: `context_injection/classify.py`
- Create: `tests/test_classify.py`

**Step 1: Write the failing tests**

Create `tests/test_classify.py`:

```python
"""Tests for file type classification."""

import pytest

from context_injection.classify import FileKind, classify_path


class TestFileKind:
    def test_is_config_true_for_all_config_variants(self) -> None:
        for kind in FileKind:
            if kind.value.startswith("config_"):
                assert kind.is_config is True, f"{kind} should be config"

    def test_is_config_false_for_non_config(self) -> None:
        assert FileKind.CODE.is_config is False
        assert FileKind.UNKNOWN.is_config is False

    def test_all_values_are_lowercase(self) -> None:
        for kind in FileKind:
            assert kind.value == kind.value.lower()


class TestClassifyPath:
    # --- Dotenv files (basename-based detection) ---

    @pytest.mark.parametrize(
        "path",
        [".env", ".env.local", ".env.production", "src/.env", "/repo/.env.staging"],
    )
    def test_dotenv_by_basename(self, path: str) -> None:
        assert classify_path(path) == FileKind.CONFIG_ENV

    def test_dotenv_by_extension(self) -> None:
        """Files like config.env use extension-based detection."""
        assert classify_path("config.env") == FileKind.CONFIG_ENV

    # --- Config formats (extension-based) ---

    @pytest.mark.parametrize(
        "path, expected",
        [
            ("settings.json", FileKind.CONFIG_JSON),
            ("tsconfig.jsonc", FileKind.CONFIG_JSON),
            ("config.yaml", FileKind.CONFIG_YAML),
            ("docker-compose.yml", FileKind.CONFIG_YAML),
            ("pyproject.toml", FileKind.CONFIG_TOML),
            ("config.ini", FileKind.CONFIG_INI),
            ("setup.cfg", FileKind.CONFIG_INI),
            ("app.properties", FileKind.CONFIG_INI),
        ],
    )
    def test_config_by_extension(self, path: str, expected: FileKind) -> None:
        assert classify_path(path) == expected

    # --- Code files ---

    @pytest.mark.parametrize(
        "path",
        ["app.py", "index.ts", "main.go", "lib.rs", "App.java", "script.sh"],
    )
    def test_code_classification(self, path: str) -> None:
        assert classify_path(path) == FileKind.CODE

    # --- Unknown ---

    @pytest.mark.parametrize(
        "path",
        ["Makefile", "Dockerfile", "LICENSE", "file.xyz", ".gitignore"],
    )
    def test_unknown_classification(self, path: str) -> None:
        assert classify_path(path) == FileKind.UNKNOWN

    # --- Case insensitivity ---

    def test_case_insensitive_extension(self) -> None:
        assert classify_path("Config.JSON") == FileKind.CONFIG_JSON
        assert classify_path("APP.PY") == FileKind.CODE

    # --- Full paths ---

    def test_full_path_uses_basename_extension(self) -> None:
        assert classify_path("/repo/src/config/settings.yaml") == FileKind.CONFIG_YAML
        assert classify_path("/repo/.env") == FileKind.CONFIG_ENV
        assert classify_path("/repo/src/main.py") == FileKind.CODE

    # --- is_config routing ---

    def test_all_config_kinds_are_config(self) -> None:
        """Every CONFIG_* member returns is_config=True."""
        config_kinds = {FileKind.CONFIG_ENV, FileKind.CONFIG_INI, FileKind.CONFIG_JSON,
                        FileKind.CONFIG_YAML, FileKind.CONFIG_TOML}
        for kind in config_kinds:
            assert kind.is_config is True
```

**Step 2: Run tests to verify they fail**

Run: `cd packages/context-injection && uv run pytest tests/test_classify.py -v`
Expected: FAIL — module not found

**Step 3: Implement classify.py**

Create `context_injection/classify.py`:

```python
"""File type classification by extension.

Maps file paths to FileKind for redaction routing. Config files get
format-specific redaction; code and unknown files get generic token
redaction only.

Extension mapping from v0b master plan.
"""

from __future__ import annotations

import os
from enum import StrEnum


class FileKind(StrEnum):
    """File type classification for redaction routing."""

    CODE = "code"
    CONFIG_ENV = "config_env"
    CONFIG_INI = "config_ini"
    CONFIG_JSON = "config_json"
    CONFIG_YAML = "config_yaml"
    CONFIG_TOML = "config_toml"
    UNKNOWN = "unknown"

    @property
    def is_config(self) -> bool:
        """True for all CONFIG_* variants."""
        return self.value.startswith("config_")


_CONFIG_MAP: dict[str, FileKind] = {
    ".env": FileKind.CONFIG_ENV,
    ".json": FileKind.CONFIG_JSON,
    ".jsonc": FileKind.CONFIG_JSON,
    ".yaml": FileKind.CONFIG_YAML,
    ".yml": FileKind.CONFIG_YAML,
    ".toml": FileKind.CONFIG_TOML,
    ".ini": FileKind.CONFIG_INI,
    ".cfg": FileKind.CONFIG_INI,
    ".properties": FileKind.CONFIG_INI,
}

_CODE_EXTENSIONS: frozenset[str] = frozenset({
    ".py", ".pyi", ".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs",
    ".go", ".rs", ".rb", ".java", ".kt", ".scala",
    ".c", ".cpp", ".cc", ".h", ".hpp", ".cs",
    ".swift", ".sh", ".bash", ".zsh",
    ".pl", ".php", ".lua", ".r",
    ".ex", ".exs", ".erl", ".hs",
    ".sql", ".html", ".htm", ".css", ".scss",
    ".vue", ".svelte", ".md", ".rst", ".txt", ".xml",
})


def classify_path(path: str) -> FileKind:
    """Classify file by extension. Returns UNKNOWN for unrecognized extensions.

    Handles dotenv files (.env, .env.local) by basename check since
    os.path.splitext(".env") returns no extension.
    """
    name = os.path.basename(path).lower()
    _, ext = os.path.splitext(name)

    # Dotenv files: .env, .env.local, .env.production, etc.
    if name == ".env" or name.startswith(".env."):
        return FileKind.CONFIG_ENV

    # Extension-based config classification
    if ext in _CONFIG_MAP:
        return _CONFIG_MAP[ext]

    # Known code extensions
    if ext in _CODE_EXTENSIONS:
        return FileKind.CODE

    return FileKind.UNKNOWN
```

**Step 4: Run tests to verify pass**

Run: `cd packages/context-injection && uv run pytest tests/test_classify.py -v`
Expected: PASS (all tests)

**Step 5: Run full suite**

Run: `cd packages/context-injection && uv run pytest`
Expected: All tests pass

**Step 6: Commit**

```bash
git add context_injection/classify.py tests/test_classify.py
git commit -m "feat(context-injection): add FileKind enum and classify_path()

Extension-based file classification for redaction routing. Config files
(env, json, yaml, toml, ini) get format-specific redaction; code and
unknown files get generic token pass only."
```

---

### Task 5: Create redact_formats.py with types and redact_env()

**Files:**
- Create: `context_injection/redact_formats.py`
- Create: `tests/redaction_harness.py` (shared test harness for D3 reuse)
- Create: `tests/test_redact_formats.py`

**Step 1a: Create shared redaction test harness**

Create `tests/redaction_harness.py` (shared by D1 test_redact_formats.py and D3 format redactor tests):

```python
"""Shared test harness for format redactor tests.

Provides assertion helpers and common case definitions. Used by D1
(test_redact_formats.py) and D3 (test_redact_json.py, test_redact_yaml.py,
test_redact_toml.py) to ensure consistent output contract verification.
"""

from __future__ import annotations

from context_injection.redact_formats import (
    FormatRedactOutcome,
    FormatRedactResult,
    FormatSuppressed,
)


def assert_redact_result(
    outcome: FormatRedactOutcome,
    *,
    expected_text: str | None = None,
    expected_count: int | None = None,
) -> FormatRedactResult:
    """Assert outcome is FormatRedactResult, optionally check text and count."""
    assert isinstance(outcome, FormatRedactResult), (
        f"Expected FormatRedactResult, got {type(outcome).__name__}"
    )
    if expected_text is not None:
        assert outcome.text == expected_text, (
            f"Text mismatch:\n  expected: {expected_text!r}\n  got:      {outcome.text!r}"
        )
    if expected_count is not None:
        assert outcome.redactions_applied == expected_count, (
            f"Count mismatch: expected {expected_count}, got {outcome.redactions_applied}"
        )
    return outcome


def assert_suppressed(
    outcome: FormatRedactOutcome,
    *,
    reason_contains: str | None = None,
) -> FormatSuppressed:
    """Assert outcome is FormatSuppressed, optionally check reason."""
    assert isinstance(outcome, FormatSuppressed), (
        f"Expected FormatSuppressed, got {type(outcome).__name__}"
    )
    if reason_contains is not None:
        assert reason_contains in outcome.reason, (
            f"Reason mismatch: expected substring {reason_contains!r} in {outcome.reason!r}"
        )
    return outcome


# Common test cases for output contract verification across all format redactors.
# Each tuple: (description, input_text, expected_redactions).
# Format-specific tests extend these with their own cases.
COMMON_REDACTION_CASES: list[tuple[str, str, int]] = [
    ("empty input", "", 0),
    ("whitespace only", "  \n  \n", 0),
]
```

**Step 1b: Write the failing tests**

Create `tests/test_redact_formats.py`:

```python
"""Tests for format-specific config redactors."""

import pytest

from context_injection.redact_formats import (
    FormatRedactOutcome,
    FormatRedactResult,
    FormatSuppressed,
    redact_env,
)
from tests.redaction_harness import assert_redact_result, assert_suppressed


# --- Type tests ---

class TestFormatRedactTypes:
    def test_result_is_frozen(self) -> None:
        r = FormatRedactResult(text="a", redactions_applied=1)
        with pytest.raises(AttributeError):
            r.text = "b"

    def test_suppressed_is_frozen(self) -> None:
        s = FormatSuppressed(reason="test_desync")
        with pytest.raises(AttributeError):
            s.reason = "other"

    def test_union_type_discriminates(self) -> None:
        r: FormatRedactOutcome = FormatRedactResult(text="a", redactions_applied=0)
        s: FormatRedactOutcome = FormatSuppressed(reason="x")
        assert isinstance(r, FormatRedactResult)
        assert isinstance(s, FormatSuppressed)


# --- Env redactor ---

class TestRedactEnv:
    def test_basic_key_value(self) -> None:
        r = assert_redact_result(redact_env("DB_HOST=localhost\n"))
        assert r.text == "DB_HOST=[REDACTED:value]\n"
        assert r.redactions_applied == 1

    def test_multiple_keys(self) -> None:
        r = assert_redact_result(redact_env("A=1\nB=2\nC=3\n"))
        assert r.redactions_applied == 3
        assert "A=[REDACTED:value]" in r.text
        assert "B=[REDACTED:value]" in r.text
        assert "C=[REDACTED:value]" in r.text

    def test_export_prefix(self) -> None:
        r = assert_redact_result(redact_env("export SECRET=hunter2\n"))
        assert r.text == "export SECRET=[REDACTED:value]\n"
        assert r.redactions_applied == 1

    def test_quoted_double(self) -> None:
        r = assert_redact_result(redact_env('KEY="value with spaces"\n'))
        assert r.text == "KEY=[REDACTED:value]\n"
        assert r.redactions_applied == 1

    def test_quoted_single(self) -> None:
        r = assert_redact_result(redact_env("KEY='value'\n"))
        assert r.text == "KEY=[REDACTED:value]\n"
        assert r.redactions_applied == 1

    def test_comments_preserved(self) -> None:
        text = "# Database config\nDB_HOST=localhost\n# End\n"
        r = assert_redact_result(redact_env(text))
        assert "# Database config" in r.text
        assert "# End" in r.text
        assert r.redactions_applied == 1

    def test_empty_value(self) -> None:
        r = assert_redact_result(redact_env("EMPTY=\n"))
        assert "EMPTY=[REDACTED:value]" in r.text
        assert r.redactions_applied == 1

    def test_value_with_equals_sign(self) -> None:
        r = assert_redact_result(redact_env("URL=https://host?key=val\n"))
        assert r.text == "URL=[REDACTED:value]\n"
        assert r.redactions_applied == 1

    def test_backslash_continuation(self) -> None:
        # Each \\ in source -> one \ in content. Each \n -> newline.
        # Content: KEY=line1\ + newline + line2 + newline
        text = "KEY=line1\\\nline2\n"
        r = assert_redact_result(redact_env(text))
        assert r.text == "KEY=[REDACTED:value]\n"
        assert r.redactions_applied == 1
        assert "line2" not in r.text  # Continuation consumed

    def test_empty_input(self) -> None:
        r = assert_redact_result(redact_env(""))
        assert r.text == ""
        assert r.redactions_applied == 0

    def test_whitespace_only(self) -> None:
        r = assert_redact_result(redact_env("  \n  \n"))
        assert r.redactions_applied == 0

    def test_no_trailing_newline_preserved(self) -> None:
        r = assert_redact_result(redact_env("KEY=val"))
        assert not r.text.endswith("\n")

    def test_trailing_newline_preserved(self) -> None:
        r = assert_redact_result(redact_env("KEY=val\n"))
        assert r.text.endswith("\n")

    def test_bare_export_preserved(self) -> None:
        """'export KEY' without = is preserved as-is."""
        r = assert_redact_result(redact_env("export PATH\n"))
        assert r.text == "export PATH\n"
        assert r.redactions_applied == 0

    def test_multi_continuation_lines(self) -> None:
        """Multiple continuation lines all consumed into one redaction."""
        text = "KEY=val\\\nmore\\\nlast\nNEXT=zzz\n"
        r = assert_redact_result(redact_env(text))
        assert "KEY=[REDACTED:value]" in r.text
        assert "NEXT=[REDACTED:value]" in r.text
        assert r.redactions_applied == 2
        assert "more" not in r.text
        assert "last" not in r.text

    def test_continuation_eats_assignment_line(self) -> None:
        """Continuation consumes next line even if it looks like key=value.

        Security posture: don't leak continuation payloads as separate keys.
        """
        text = "KEY=val\\\nEVIL=secret\nNEXT=yyy\n"
        r = assert_redact_result(redact_env(text))
        assert "KEY=[REDACTED:value]" in r.text
        assert "NEXT=[REDACTED:value]" in r.text
        assert r.redactions_applied == 2
        assert "EVIL" not in r.text
        assert "secret" not in r.text
```

**Step 2: Run tests to verify they fail**

Run: `cd packages/context-injection && uv run pytest tests/test_redact_formats.py -v`
Expected: FAIL — module not found

**Step 3: Implement redact_formats.py**

Create `context_injection/redact_formats.py`:

```python
"""Per-format config redactors.

Each redactor returns FormatRedactOutcome:
- FormatRedactResult: successfully redacted text + count
- FormatSuppressed: scanner desync or unparseable input

All redactors replace config values with [REDACTED:value] markers.
One marker = one redaction in the count.

D1 delivers: redact_env, redact_ini
D3 delivers: redact_json, redact_yaml, redact_toml
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class FormatRedactResult:
    """Successfully redacted text with count."""

    text: str
    redactions_applied: int


@dataclass(frozen=True)
class FormatSuppressed:
    """Scanner desync or unparseable input.

    reason is debug-only (e.g., "json_scanner_desync").
    Orchestration layer (redact_text) maps ALL FormatSuppressed
    to SuppressedText(reason=FORMAT_DESYNC).
    """

    reason: str


FormatRedactOutcome = FormatRedactResult | FormatSuppressed

_REDACTED_VALUE = "[REDACTED:value]"


# --- Shared helpers ---


def _has_line_continuation(line: str) -> bool:
    """Check if line ends with unescaped backslash (odd trailing count)."""
    stripped = line.rstrip()
    if not stripped.endswith("\\"):
        return False
    count = len(stripped) - len(stripped.rstrip("\\"))
    return count % 2 == 1


# --- Env redactor ---


_EXPORT_RE = re.compile(r"^export\s+")


def redact_env(text: str) -> FormatRedactOutcome:
    """Redact values in .env format.

    Handles: KEY=VALUE, export KEY=VALUE, KEY="quoted", KEY='quoted',
    backslash continuation, # comments. Empty values are redacted
    (defense in depth).
    """
    if not text.strip():
        return FormatRedactResult(text=text, redactions_applied=0)

    lines = text.splitlines()
    result: list[str] = []
    redactions = 0
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Empty or comment
        if not stripped or stripped.startswith("#"):
            result.append(line)
            i += 1
            continue

        # Strip optional export prefix
        has_export = bool(_EXPORT_RE.match(stripped))
        content = _EXPORT_RE.sub("", stripped) if has_export else stripped

        # Key=value pair
        if "=" in content:
            key, _, _ = content.partition("=")
            prefix = "export " if has_export else ""
            result.append(f"{prefix}{key}={_REDACTED_VALUE}")
            redactions += 1

            # Skip continuation lines (value ends with unescaped \)
            while _has_line_continuation(lines[i]) and i + 1 < len(lines):
                i += 1
        else:
            # Not a key=value line (e.g., bare 'export KEY')
            result.append(line)

        i += 1

    redacted = "\n".join(result)
    if text.endswith("\n"):
        redacted += "\n"

    return FormatRedactResult(text=redacted, redactions_applied=redactions)
```

**Step 4: Run tests to verify pass**

Run: `cd packages/context-injection && uv run pytest tests/test_redact_formats.py -v`
Expected: PASS (all tests)

**Step 5: Run full suite**

Run: `cd packages/context-injection && uv run pytest`
Expected: All tests pass

**Step 6: Commit**

```bash
git add context_injection/redact_formats.py tests/redaction_harness.py tests/test_redact_formats.py
git commit -m "feat(context-injection): add FormatRedactOutcome types, redact_env(), shared test harness

Env redactor: line-split on first =, redact RHS, preserve comments,
handle export prefix, quoted values, backslash continuation.
Shared redaction_harness.py for D3 format redactor test reuse."
```

---

### Task 6: Add redact_ini() with .properties dialect

**Files:**
- Modify: `context_injection/redact_formats.py`
- Modify: `tests/test_redact_formats.py`

**Step 1: Write the failing tests**

Add import to `tests/test_redact_formats.py`:

```python
from context_injection.redact_formats import (
    FormatRedactOutcome,
    FormatRedactResult,
    FormatSuppressed,
    redact_env,
    redact_ini,  # NEW
)
```

Add test classes:

```python
class TestRedactIni:
    def test_equals_separator(self) -> None:
        r = assert_redact_result(redact_ini("key = value\n"))
        assert r.text == "key = [REDACTED:value]\n"
        assert r.redactions_applied == 1

    def test_no_space_equals(self) -> None:
        r = assert_redact_result(redact_ini("key=value\n"))
        assert r.text == "key=[REDACTED:value]\n"

    def test_colon_separator(self) -> None:
        r = assert_redact_result(redact_ini("host: localhost\n"))
        assert r.text == "host: [REDACTED:value]\n"
        assert r.redactions_applied == 1

    def test_first_separator_wins(self) -> None:
        """When both = and : present, first one is the separator."""
        r = assert_redact_result(redact_ini("url = https://host:8080\n"))
        assert r.text == "url = [REDACTED:value]\n"
        assert r.redactions_applied == 1

    def test_colon_before_equals(self) -> None:
        r = assert_redact_result(redact_ini("host: name=value\n"))
        assert r.text == "host: [REDACTED:value]\n"

    def test_section_headers_preserved(self) -> None:
        text = "[database]\nhost = localhost\nport = 5432\n"
        r = assert_redact_result(redact_ini(text))
        assert "[database]" in r.text
        assert r.redactions_applied == 2

    def test_semicolon_comment(self) -> None:
        text = "; comment\nkey = value\n"
        r = assert_redact_result(redact_ini(text))
        assert "; comment" in r.text
        assert r.redactions_applied == 1

    def test_hash_comment(self) -> None:
        text = "# comment\nkey = value\n"
        r = assert_redact_result(redact_ini(text))
        assert "# comment" in r.text
        assert r.redactions_applied == 1

    def test_no_value_key_preserved(self) -> None:
        """Key without separator is preserved as-is."""
        r = assert_redact_result(redact_ini("bare_key\n"))
        assert r.text == "bare_key\n"
        assert r.redactions_applied == 0

    def test_empty_value(self) -> None:
        r = assert_redact_result(redact_ini("key =\n"))
        assert "[REDACTED:value]" in r.text
        assert r.redactions_applied == 1

    def test_empty_input(self) -> None:
        r = assert_redact_result(redact_ini(""))
        assert r.redactions_applied == 0

    def test_trailing_newline_preserved(self) -> None:
        r = assert_redact_result(redact_ini("key=val\n"))
        assert r.text.endswith("\n")

    def test_no_trailing_newline_preserved(self) -> None:
        r = assert_redact_result(redact_ini("key=val"))
        assert not r.text.endswith("\n")

    def test_multiple_sections(self) -> None:
        text = "[s1]\na = 1\n[s2]\nb = 2\n"
        r = assert_redact_result(redact_ini(text))
        assert "[s1]" in r.text
        assert "[s2]" in r.text
        assert r.redactions_applied == 2

    def test_whitespace_after_separator_preserved(self) -> None:
        """Multi-space between separator and value is preserved exactly."""
        r = assert_redact_result(redact_ini("key =  value\n"))
        assert r.text == "key =  [REDACTED:value]\n"


class TestRedactIniPropertiesMode:
    def test_exclamation_comment(self) -> None:
        text = "! comment\nkey = value\n"
        r = assert_redact_result(redact_ini(text, properties_mode=True))
        assert "! comment" in r.text
        assert r.redactions_applied == 1

    def test_exclamation_not_comment_in_standard_mode(self) -> None:
        """! is NOT a comment prefix in standard INI mode."""
        text = "!key = value\n"
        r = assert_redact_result(redact_ini(text, properties_mode=False))
        # ! is part of the key, line still has = so it's redacted
        assert "[REDACTED:value]" in r.text

    def test_backslash_continuation(self) -> None:
        # Content: key=line1\ + newline + (spaces)line2\ + newline + (spaces)line3 + newline
        text = "key=line1\\\n  line2\\\n  line3\n"
        r = assert_redact_result(redact_ini(text, properties_mode=True))
        assert r.text == "key=[REDACTED:value]\n"
        assert r.redactions_applied == 1
        assert "line2" not in r.text
        assert "line3" not in r.text

    def test_escaped_backslash_not_continuation(self) -> None:
        # Content: key=value\\ (two backslashes) + newline + other=val + newline
        # Two trailing backslashes = even count = NOT continuation
        text = "key=value\\\\\nother=val\n"
        r = assert_redact_result(redact_ini(text, properties_mode=True))
        assert r.redactions_applied == 2

    def test_no_continuation_in_standard_mode(self) -> None:
        """Standard INI mode does NOT handle backslash continuation."""
        text = "key=line1\\\nline2\n"
        r = assert_redact_result(redact_ini(text, properties_mode=False))
        # Both lines processed independently
        assert r.redactions_applied == 1  # Only key=line1\ has =, line2 has no =

    def test_mid_continuation_passthrough(self) -> None:
        """Mid-continuation excerpt: no key= visible, line passed through.

        Generic token layer (D2a) catches secrets in passthrough lines.
        This test documents the accepted limitation.
        """
        text = "  continued_secret_value\nnormal_key=normal_value\n"
        r = assert_redact_result(redact_ini(text, properties_mode=True))
        assert "continued_secret_value" in r.text  # Passed through (no key=)
        assert "normal_key=[REDACTED:value]" in r.text
        assert r.redactions_applied == 1

    def test_properties_continuation_and_backstop_ordering(self) -> None:
        """Continuation + ordering: format redactor handles known patterns,
        generic token layer (D2a) is the backstop for missed patterns.

        This test verifies the format redactor correctly collapses continuations.
        The ordering guarantee (format-specific then generic) is tested in D2a.
        """
        text = "db.password=supersecret\\\n  continued\n"
        r = assert_redact_result(redact_ini(text, properties_mode=True))
        assert r.text == "db.password=[REDACTED:value]\n"
        assert r.redactions_applied == 1
        assert "supersecret" not in r.text
        assert "continued" not in r.text

    def test_mid_continuation_secret_survives_format_redaction(self) -> None:
        """Accepted limitation: a secret on a mid-continuation passthrough
        line survives format-specific redaction. D2a's generic token backstop
        is responsible for catching it.

        This is an executable reminder — if this test ever fails (secret
        gets redacted), the D2a backstop test may need updating.
        """
        # Simulates an excerpt starting mid-continuation: the first line
        # has no key= prefix, so the format redactor passes it through.
        text = "  secret_api_key_12345\nnormal_key = safe_value\n"
        r = assert_redact_result(redact_ini(text, properties_mode=True))
        # Secret survives format-specific redaction (no key= to trigger it)
        assert "secret_api_key_12345" in r.text
        # Normal key IS redacted
        assert "normal_key = [REDACTED:value]" in r.text
        assert r.redactions_applied == 1
```

**Step 2: Run tests to verify they fail**

Run: `cd packages/context-injection && uv run pytest tests/test_redact_formats.py::TestRedactIni tests/test_redact_formats.py::TestRedactIniPropertiesMode -v`
Expected: FAIL — `redact_ini` not importable

**Step 3: Implement redact_ini**

Add to `context_injection/redact_formats.py`:

```python
# --- INI redactor ---


def redact_ini(text: str, *, properties_mode: bool = False) -> FormatRedactOutcome:
    """Redact values in INI/.properties format.

    Handles: key=value, key:value, key = value, [section] headers,
    comments (; and # for INI, # and ! for .properties).

    Properties mode: backslash continuation (strict: line must end with
    unescaped backslash). Excerpt-start-mid-continuation is an accepted
    limitation mitigated by generic token pass (D2a).
    """
    if not text.strip():
        return FormatRedactResult(text=text, redactions_applied=0)

    lines = text.splitlines()
    result: list[str] = []
    redactions = 0
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Empty line
        if not stripped:
            result.append(line)
            i += 1
            continue

        # Comment detection
        if _is_ini_comment(stripped, properties_mode=properties_mode):
            result.append(line)
            i += 1
            continue

        # Section header [section]
        if stripped.startswith("[") and stripped.endswith("]"):
            result.append(line)
            i += 1
            continue

        # Key-value pair
        kv = _split_ini_kv(stripped)
        if kv is not None:
            prefix, _ = kv
            result.append(f"{prefix}{_REDACTED_VALUE}")
            redactions += 1

            # Properties mode: skip continuation lines
            if properties_mode:
                while _has_line_continuation(lines[i]) and i + 1 < len(lines):
                    i += 1
        else:
            # No separator found — preserve line as-is
            result.append(line)

        i += 1

    redacted = "\n".join(result)
    if text.endswith("\n"):
        redacted += "\n"

    return FormatRedactResult(text=redacted, redactions_applied=redactions)


def _is_ini_comment(stripped: str, *, properties_mode: bool) -> bool:
    """Check if a stripped line is a comment."""
    if stripped.startswith("#") or stripped.startswith(";"):
        return True
    if properties_mode and stripped.startswith("!"):
        return True
    return False


def _split_ini_kv(line: str) -> tuple[str, str] | None:
    """Split INI key-value line into (prefix, value).

    prefix includes key, separator, and all original whitespace:
    'key = value' -> ('key = ', 'value')
    'key:value' -> ('key:', 'value')
    'key =  value' -> ('key =  ', 'value')

    Uses first separator found (min position of = and :).
    """
    eq_idx = line.find("=")
    colon_idx = line.find(":")

    if eq_idx < 0 and colon_idx < 0:
        return None

    if eq_idx < 0:
        idx = colon_idx
    elif colon_idx < 0:
        idx = eq_idx
    else:
        idx = min(eq_idx, colon_idx)

    prefix = line[:idx + 1]
    rest = line[idx + 1:]
    # Preserve all whitespace between separator and value start
    stripped_rest = rest.lstrip()
    whitespace = rest[:len(rest) - len(stripped_rest)]
    prefix += whitespace
    rest = stripped_rest

    return prefix, rest
```

**Step 4: Run tests to verify pass**

Run: `cd packages/context-injection && uv run pytest tests/test_redact_formats.py -v`
Expected: PASS (all tests including env + ini + properties)

**Step 5: Run full suite**

Run: `cd packages/context-injection && uv run pytest`
Expected: All tests pass

**Step 6: Commit**

```bash
git add context_injection/redact_formats.py tests/test_redact_formats.py
git commit -m "feat(context-injection): add redact_ini() with .properties dialect

INI redactor: key=value and key:value with section/comment preservation.
Properties mode adds ! comments and backslash continuation (strict).
Mid-continuation passthrough is accepted limitation — D2a generic token
pass is the backstop."
```

---

## Final Verification

After all 6 tasks:

Run: `cd packages/context-injection && uv run pytest -v`
Expected: All tests pass (288 existing + ~65-75 new tests)

Run: `cd packages/context-injection && uv run ruff check`
Expected: No lint errors

## Summary of Deliverables

| Module | New/Modified | What D1 Adds |
|--------|-------------|-------------|
| `types.py` | Modified | `ReadResult.excerpt_range` nullable |
| `state.py` | Modified | `ScoutOptionRecord` dataclass, `ScoutOptionRegistry` type update, `consume_scout()` method |
| `templates.py` | Modified | Populates `ScoutOptionRecord` with metadata in `_make_read_option` / `_make_grep_option` |
| `classify.py` | **New** | `FileKind` enum with `is_config`, `classify_path()` |
| `redact_formats.py` | **New** | `FormatRedactOutcome` types, `redact_env()`, `redact_ini()` with `.properties` dialect |
| `test_types.py` | Modified | 5 new tests (nullable excerpt_range + strict mode + too-long) |
| `test_state.py` | Modified | ~15 new tests (ScoutOptionRecord + consume_scout incl. one-scout-per-turn invariant), updated existing tests for new format |
| `test_pipeline.py` | Modified | Updated tuple destructuring to ScoutOptionRecord attribute access |
| `test_classify.py` | **New** | ~15 tests (extension mapping, is_config, edge cases) |
| `redaction_harness.py` | **New** | Shared assertion helpers (`assert_redact_result`, `assert_suppressed`) + common cases for D3 reuse |
| `test_redact_formats.py` | **New** | ~35 tests (types, env redactor incl. multi-continuation, ini redactor incl. whitespace preservation, properties mode incl. limitation tests) |
