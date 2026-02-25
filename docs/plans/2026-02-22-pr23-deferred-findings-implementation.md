# PR #23 Deferred Findings — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Address 7 deferred PR #23 review findings across 2 parallel streams with zero file overlap.

**Architecture:** Stream A adds `mode_source` observability field to analytics and clarifies epilogue extraction in SKILL.md. Stream B widens exception handling in the validator, adds scope-breach conformance testing, and fills 4 test coverage gaps. Streams are file-isolated and can run in parallel.

**Tech Stack:** Python 3.11+, pytest, ruff

**Reference:** `docs/plans/2026-02-21-pr23-deferred-findings-design.md`

**Branch:** Create `fix/pr23-deferred-findings` from `main`.

**Test commands:**
- Stream A: `uv run pytest tests/test_emit_analytics.py -x -q`
- Stream B: `uv run pytest tests/test_consultation_contract_sync.py -x -q`
- Full: `uv run pytest tests/ -x -q`
- Lint: `uv run ruff check packages/plugins/cross-model/scripts/emit_analytics.py scripts/validate_consultation_contract.py tests/test_emit_analytics.py tests/test_consultation_contract_sync.py`

**Dependencies between tasks:**
- Task 1 (Stream B: widen read_file to OSError): independent
- Task 2 (Stream B: scope-breach conformance test): independent (imports from emit_analytics but doesn't modify it)
- Task 3 (Stream B: 4 test coverage gaps): depends on Task 1 (PermissionError test needs OSError widening)
- Task 4 (Stream A: mode_source field): independent
- Task 5 (Stream A: SKILL.md extraction clarification): depends on Task 4 (references mode_source)
- Task 6: Final verification + commit

---

## Stream B: Validator + Tests

### Task 1: Widen `read_file` and downstream catches to `OSError` (S4)

**Files:**
- Modify: `scripts/validate_consultation_contract.py:44-48` (read_file), `:109` (check_agent_governance_count), `:206-224` (4 blocks in validate)
- Test: `tests/test_consultation_contract_sync.py`

**Step 1: Write the failing test**

Add to `tests/test_consultation_contract_sync.py` at the end of the file:

```python
# ---------------------------------------------------------------------------
# OSError handling (S4)
# ---------------------------------------------------------------------------


def test_read_file_permission_error(tmp_path: Path, monkeypatch: "pytest.MonkeyPatch") -> None:
    """read_file catches PermissionError (via OSError widening), not just FileNotFoundError."""
    target = tmp_path / "unreadable.md"
    target.write_text("content")

    # Monkeypatch Path.read_text to raise PermissionError
    original_read_text = Path.read_text

    def patched_read_text(self: Path, *args: object, **kwargs: object) -> str:
        if self == target:
            raise PermissionError(f"Permission denied: {self}")
        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", patched_read_text)

    # Before S4 fix: this raises uncaught PermissionError
    # After S4 fix: this returns a descriptive error string
    errors = MODULE.check_agent_governance_count(target, 7)
    assert len(errors) == 1
    assert "PermissionError" in errors[0]
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_consultation_contract_sync.py::test_read_file_permission_error -v`
Expected: FAIL — `PermissionError` propagates unhandled because `check_agent_governance_count` catches only `FileNotFoundError`.

**Step 3: Implement — rewrite `read_file`**

In `scripts/validate_consultation_contract.py`, replace lines 44-48:

```python
def read_file(path: Path) -> str:
    """Read a file. Raises FileNotFoundError with descriptive message on failure."""
    if not path.exists():
        raise FileNotFoundError(f"file not found: {path}")
    return path.read_text()
```

With:

```python
def read_file(path: Path) -> str:
    """Read a file. Raises OSError with descriptive message on failure."""
    try:
        return path.read_text()
    except OSError as e:
        raise type(e)(f"cannot read {path} ({type(e).__name__}): {e}") from e
```

**Step 4: Widen `check_agent_governance_count` catch**

In `scripts/validate_consultation_contract.py` line 109, replace:

```python
    except FileNotFoundError as e:
```

With:

```python
    except OSError as e:
```

**Step 5: Widen all 4 `validate()` catch blocks**

In `scripts/validate_consultation_contract.py`, replace each of the 4 `except FileNotFoundError as e:` blocks (lines 206, 211, 216, 221) with `except OSError as e:`. There are exactly 4 occurrences within the `validate()` function.

**Step 6: Run test to verify it passes**

Run: `uv run pytest tests/test_consultation_contract_sync.py::test_read_file_permission_error -v`
Expected: PASS

**Step 7: Run full Stream B test suite**

Run: `uv run pytest tests/test_consultation_contract_sync.py -x -q`
Expected: All existing tests pass (23 tests) + 1 new test = 24 passed

**Step 8: Run conformance validator**

Run: `uv run scripts/validate_consultation_contract.py`
Expected: PASS

**Step 9: Commit**

```bash
git add scripts/validate_consultation_contract.py tests/test_consultation_contract_sync.py
git commit -m "fix(validator): widen read_file and downstream catches to OSError (S4)

Replaces path.exists() + FileNotFoundError pattern with try/except OSError
on path.read_text(). Widens all 5 downstream catch sites to prevent
uncaught PermissionError from breaking error accumulation."
```

---

### Task 2: Add scope-breach conformance test (I7)

**Files:**
- Test: `tests/test_consultation_contract_sync.py` (2 new tests)
- No source modifications

**Step 1: Write the scope-breach conformance test**

Add to `tests/test_consultation_contract_sync.py`:

```python
# ---------------------------------------------------------------------------
# Scope-breach conformance (I7)
# ---------------------------------------------------------------------------


def test_termination_reasons_match_contract() -> None:
    """§13's Valid termination reasons must match emit_analytics._VALID_TERMINATION_REASONS."""
    import re as re_mod
    import importlib.util as ilu

    # Import _VALID_TERMINATION_REASONS from emit_analytics
    emit_path = (
        REPO_ROOT
        / "packages/plugins/cross-model/scripts/emit_analytics.py"
    )
    spec = ilu.spec_from_file_location("emit_analytics", emit_path)
    assert spec is not None and spec.loader is not None
    emit_mod = ilu.module_from_spec(spec)
    spec.loader.exec_module(emit_mod)
    code_reasons = emit_mod._VALID_TERMINATION_REASONS

    # Parse §13's "### Valid termination reasons" subsection
    contract_text = CONTRACT_PATH.read_text()
    section_13 = MODULE.extract_section_text(contract_text, "## 13.")
    assert section_13 is not None, "§13 not found in contract"

    # Find the subsection body after "### Valid termination reasons"
    sub_start = section_13.find("### Valid termination reasons")
    assert sub_start != -1, "§13 missing '### Valid termination reasons' subsection"

    # Extract text until next ### or end
    sub_text = section_13[sub_start:]
    next_sub = sub_text.find("\n### ", len("### Valid termination reasons"))
    if next_sub != -1:
        sub_text = sub_text[:next_sub]

    # Extract backtick-delimited values
    contract_reasons = set(re_mod.findall(r"`([^`]+)`", sub_text))

    assert contract_reasons == code_reasons, (
        f"termination reason mismatch: contract has {sorted(contract_reasons)}, "
        f"code has {sorted(code_reasons)}"
    )


def test_scope_breach_referenced_in_section_6() -> None:
    """§6 must reference termination_reason: scope_breach for scope enforcement."""
    contract_text = CONTRACT_PATH.read_text()
    section_6 = MODULE.extract_section_text(contract_text, "## 6.")
    assert section_6 is not None, "§6 not found in contract"
    assert "scope_breach" in section_6, (
        "§6 must reference 'scope_breach' as a termination reason"
    )
```

**Step 2: Run tests to verify they pass**

Run: `uv run pytest tests/test_consultation_contract_sync.py::test_termination_reasons_match_contract tests/test_consultation_contract_sync.py::test_scope_breach_referenced_in_section_6 -v`
Expected: PASS — these are conformance tests against existing content. If they fail, it means the contract and code have already drifted, which is a real finding.

**Step 3: Verify the conformance invariant works by checking what would break it**

Mental verification: if someone adds a new termination reason to `_VALID_TERMINATION_REASONS` without updating §13 (or vice versa), `test_termination_reasons_match_contract` fails with a clear set-difference message.

**Step 4: Run full Stream B test suite**

Run: `uv run pytest tests/test_consultation_contract_sync.py -x -q`
Expected: 24 (from Task 1) + 2 new = 26 passed

**Step 5: Commit**

```bash
git add tests/test_consultation_contract_sync.py
git commit -m "test(validator): add scope-breach conformance tests (I7)

Cross-component invariant: parses §13's Valid termination reasons subsection
and compares against emit_analytics._VALID_TERMINATION_REASONS as sets.
Also verifies §6 references scope_breach."
```

---

### Task 3: Fill 4 test coverage gaps

**Files:**
- Test: `tests/test_consultation_contract_sync.py` (4 new tests)
- Depends on Task 1 (OSError widening must be in place)

**Step 1: Write test for missing agent file (FileNotFoundError branch)**

Add to `tests/test_consultation_contract_sync.py`:

```python
# ---------------------------------------------------------------------------
# Test coverage gaps (round 2)
# ---------------------------------------------------------------------------


def test_agent_governance_missing_file(tmp_path: Path) -> None:
    """check_agent_governance_count returns error for non-existent agent file."""
    missing_path = tmp_path / "nonexistent-agent.md"
    errors = MODULE.check_agent_governance_count(missing_path, 7)
    assert len(errors) == 1
    assert "cannot read" in errors[0] or "check_agent_governance failed" in errors[0]
```

**Step 2: Run test to verify it passes**

Run: `uv run pytest tests/test_consultation_contract_sync.py::test_agent_governance_missing_file -v`
Expected: PASS — after Task 1's OSError widening, `read_file` raises `FileNotFoundError` (an `OSError` subclass) and `check_agent_governance_count` catches it.

**Step 3: Write test for §13 missing section**

```python
def test_event_types_missing_section() -> None:
    """check_event_types_in_contract returns error when §13 is absent."""
    contract_without_13 = "\n".join(
        [
            "## 12. Previous Section",
            "",
            "Some content.",
            "",
            "## 14. Next Section",
            "",
            "More content.",
        ]
    )
    errors = MODULE.check_event_types_in_contract(contract_without_13)
    assert len(errors) == 1
    assert "§13" in errors[0]
    assert "not found" in errors[0]
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_consultation_contract_sync.py::test_event_types_missing_section -v`
Expected: PASS — `extract_section_text` returns `None`, function returns "§13 Event Contract section not found".

**Step 5: Write test for multiple simultaneous errors**

```python
def test_multiple_simultaneous_errors() -> None:
    """validate() accumulates errors from multiple failing checks."""
    # Use a repo root that doesn't exist — all file reads will fail
    fake_root = Path("/nonexistent/repo/root")
    errors = MODULE.validate(repo_root=fake_root)
    # 4 file-read errors + 3 unconditional agent governance checks = 7 minimum
    assert len(errors) >= 7, (
        f"expected at least 7 accumulated errors from missing files, got {len(errors)}:\n"
        + "\n".join(f"  - {e}" for e in errors)
    )
    # Verify errors are accumulated, not just the first one
    error_text = "\n".join(errors)
    assert "contract" in error_text.lower()
    assert "skill" in error_text.lower()
```

**Step 6: Run test to verify it passes**

Run: `uv run pytest tests/test_consultation_contract_sync.py::test_multiple_simultaneous_errors -v`
Expected: PASS — `validate()` accumulates errors from all failed reads.

**Step 7: Write test for PermissionError at validate() level**

This directly tests the widened `except OSError` catches in `validate()`, not just the proxy through `check_agent_governance_count`.

```python
def test_validate_catches_permission_error(tmp_path: Path, monkeypatch: "pytest.MonkeyPatch") -> None:
    """validate() catches PermissionError (OSError subclass) during file reads."""
    original_read_file = MODULE.read_file

    def patched_read_file(path: Path) -> str:
        if "consultation-contract" in path.name:
            raise PermissionError(f"Permission denied: {path}")
        return original_read_file(path)

    monkeypatch.setattr(MODULE, "read_file", patched_read_file)
    errors = MODULE.validate(repo_root=tmp_path)
    permission_errors = [e for e in errors if "PermissionError" in e or "Permission denied" in e]
    assert len(permission_errors) >= 1, (
        f"expected PermissionError in accumulated errors, got:\n"
        + "\n".join(f"  - {e}" for e in errors)
    )
```

**Step 8: Run test to verify it passes**

Run: `uv run pytest tests/test_consultation_contract_sync.py::test_validate_catches_permission_error -v`
Expected: PASS — `validate()`'s `except OSError` catches the `PermissionError` raised by `read_file`.

**Step 9: Run full Stream B test suite**

Run: `uv run pytest tests/test_consultation_contract_sync.py -x -q`
Expected: 26 (from Tasks 1-2) + 4 new = 30 passed

**Step 10: Commit**

```bash
git add tests/test_consultation_contract_sync.py
git commit -m "test(validator): fill 4 test coverage gaps

- test_agent_governance_missing_file: FileNotFoundError branch
- test_event_types_missing_section: §13 absent branch
- test_multiple_simultaneous_errors: error accumulation (>= 7 errors)
- test_validate_catches_permission_error: OSError widening at validate() level"
```

---

## Stream A: Analytics + Docs

### Task 4: Add `mode_source` observability field (I3)

**Files:**
- Modify: `packages/plugins/cross-model/scripts/emit_analytics.py`
- Test: `tests/test_emit_analytics.py`

**Step 1: Write the failing tests**

Add to `tests/test_emit_analytics.py`. Find the `TestBuildDialogueOutcome` class and add after the existing methods.

**Important:** `_dialogue_input()` returns a dict sharing the module-level `SAMPLE_PIPELINE` reference. Tests that set keys on `inp["pipeline"]` mutate the shared dict, polluting subsequent tests. Use `{**SAMPLE_PIPELINE, key: value}` to create a fresh pipeline dict for each test that modifies pipeline fields.

```python
    def test_mode_source_epilogue_propagated(self) -> None:
        """mode_source='epilogue' is propagated from pipeline input."""
        pipeline = {**SAMPLE_PIPELINE, "mode_source": "epilogue"}
        inp = _dialogue_input(pipeline=pipeline)
        event = MODULE.build_dialogue_outcome(inp)
        assert event["mode_source"] == "epilogue"

    def test_mode_source_fallback_propagated(self) -> None:
        """mode_source='fallback' is propagated from pipeline input."""
        pipeline = {**SAMPLE_PIPELINE, "mode_source": "fallback"}
        inp = _dialogue_input(pipeline=pipeline)
        event = MODULE.build_dialogue_outcome(inp)
        assert event["mode_source"] == "fallback"

    def test_mode_source_none_when_omitted(self) -> None:
        """mode_source defaults to None when not in pipeline input."""
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        assert event["mode_source"] is None

    def test_mode_source_absent_from_consultation_outcome(self) -> None:
        """mode_source must not be present in consultation_outcome events (D1: absent, not None)."""
        event = MODULE.build_consultation_outcome(_consultation_input())
        assert "mode_source" not in event
```

Also find `TestValidate` class (note: the class is named `TestValidate`, not `TestValidation`) and add:

```python
    def test_mode_source_invalid_value_rejected(self) -> None:
        """Invalid mode_source enum value is rejected."""
        pipeline = {**SAMPLE_PIPELINE, "mode_source": "invented"}
        inp = _dialogue_input(pipeline=pipeline)
        event = MODULE.build_dialogue_outcome(inp)
        with pytest.raises(ValueError, match="invalid mode_source"):
            MODULE.validate(event, "dialogue_outcome")

    def test_mode_source_rejected_on_consultation(self) -> None:
        """Non-None mode_source on consultation_outcome is rejected."""
        inp = _consultation_input()
        event = MODULE.build_consultation_outcome(inp)
        event["mode_source"] = "epilogue"  # manually inject
        with pytest.raises(ValueError, match="mode_source"):
            MODULE.validate(event, "consultation_outcome")

    def test_mode_source_valid_values_pass_validation(self) -> None:
        """Valid mode_source values ('epilogue', 'fallback') pass validation without error."""
        for ms in ("epilogue", "fallback"):
            pipeline = {**SAMPLE_PIPELINE, "mode_source": ms}
            inp = _dialogue_input(pipeline=pipeline)
            event = MODULE.build_dialogue_outcome(inp)
            MODULE.validate(event, "dialogue_outcome")  # should not raise
```

**Step 2: Update `test_all_fields_present` expected key set**

In `tests/test_emit_analytics.py` at line 424, add `"mode_source"` to the `expected_fields` set. Insert after `"mode",` (line 435):

```python
            "mode_source",
```

**Step 3: Run tests to verify they fail**

Run: `uv run pytest tests/test_emit_analytics.py::TestBuildDialogueOutcome::test_mode_source_epilogue_propagated tests/test_emit_analytics.py::TestBuildDialogueOutcome::test_all_fields_present -v`
Expected: FAIL — `mode_source` key doesn't exist in event dict yet.

**Step 4: Implement — add `_VALID_MODE_SOURCES` constant**

In `packages/plugins/cross-model/scripts/emit_analytics.py`, after `_VALID_MODES` (line 50), add:

```python
_VALID_MODE_SOURCES = {"epilogue", "fallback"}
```

**Step 5: Implement — add `mode_source` to `build_dialogue_outcome`**

In `packages/plugins/cross-model/scripts/emit_analytics.py`, in the `build_dialogue_outcome` function's event dict, after the `"mode"` line (line 368), add:

```python
        "mode_source": pipeline.get("mode_source"),
```

**Step 6: Implement — add `mode_source` validation**

In `packages/plugins/cross-model/scripts/emit_analytics.py`, in the `validate` function, after the `mode` validation block (after line 510), add:

```python
    # mode_source enum (dialogue_outcome only, nullable)
    ms = event.get("mode_source")
    if event_type == "dialogue_outcome":
        if ms is not None and ms not in _VALID_MODE_SOURCES:
            raise ValueError(f"invalid mode_source: {ms!r}")
    elif ms is not None:
        raise ValueError(
            f"mode_source must be absent or None on {event_type}, got {ms!r}"
        )
```

**Step 7: Run tests to verify they pass**

Run: `uv run pytest tests/test_emit_analytics.py::TestBuildDialogueOutcome::test_mode_source_epilogue_propagated tests/test_emit_analytics.py::TestBuildDialogueOutcome::test_mode_source_fallback_propagated tests/test_emit_analytics.py::TestBuildDialogueOutcome::test_mode_source_none_when_omitted tests/test_emit_analytics.py::TestBuildDialogueOutcome::test_all_fields_present -v`
Expected: PASS

**Step 8: Run validation tests**

Run: `uv run pytest tests/test_emit_analytics.py::TestValidate::test_mode_source_invalid_value_rejected tests/test_emit_analytics.py::TestValidate::test_mode_source_rejected_on_consultation tests/test_emit_analytics.py::TestValidate::test_mode_source_valid_values_pass_validation -v`
Expected: PASS

**Step 9: Run full Stream A test suite**

Run: `uv run pytest tests/test_emit_analytics.py -x -q`
Expected: All existing tests pass + 8 new tests (4 builder + 3 validation + 1 updated). Fixture replay tests (TestReplayConformance) must still pass — fixtures don't include `mode_source` and the field defaults to `None`.

**Step 10: Commit**

```bash
git add packages/plugins/cross-model/scripts/emit_analytics.py tests/test_emit_analytics.py
git commit -m "feat(analytics): add mode_source observability field (I3)

Reserved nullable enum ('epilogue' | 'fallback') on dialogue_outcome events.
Makes silent mode fallback visible without changing the default behavior.
Follows the episode_id reserved-nullable pattern. Includes enum validation,
positive round-trip validation, absent-key builder test, and rejection of
mode_source on consultation_outcome events."
```

---

### Task 5: Clarify epilogue extraction in SKILL.md (S5-lite)

**Files:**
- Modify: `packages/plugins/cross-model/skills/dialogue/SKILL.md:397` (mode row in pipeline field table)

**Step 1: Update the `mode` row in the Step 7a pipeline field table**

In `packages/plugins/cross-model/skills/dialogue/SKILL.md`, find the `mode` row at line 397 and replace:

```
| `mode` | Step 5 agent return | `"server_assisted"` or `"manual_legacy"`. Parse from the agent's `<!-- pipeline-data -->` JSON epilogue block. Extract the JSON object from the fenced block following the sentinel. If the epilogue is missing, fall back to `"server_assisted"` and log a warning. |
```

With:

```
| `mode` | Step 5 agent return | `"server_assisted"` or `"manual_legacy"`. Parse from the agent's `<!-- pipeline-data -->` JSON epilogue block: extract the JSON object from the fenced code block immediately after the sentinel, stopping at the first closing code fence (`` ``` ``). If the epilogue is missing, unparseable, missing the `mode` key, or has an invalid mode value, fall back to `"server_assisted"` and set `mode_source` to `"fallback"`. |
| `mode_source` | Step 5 agent return | `"epilogue"`, `"fallback"`, or `null`. Set to `"epilogue"` when `mode` was successfully parsed from the agent's pipeline-data epilogue. Set to `"fallback"` when the epilogue was missing, unparseable, or contained an invalid mode value — signals that `mode` is a default, not an observed value. Reserved nullable: not in `_DIALOGUE_REQUIRED`. |
```

**Step 2: Verify no other references need updating**

Grep the SKILL.md for other `mode` references that should mention `mode_source`:
- The Step 7a Write input file section already references the pipeline field table — no additional changes needed.

**Step 3: Commit**

```bash
git add packages/plugins/cross-model/skills/dialogue/SKILL.md
git commit -m "docs(dialogue): clarify epilogue extraction and add mode_source field (S5-lite)

Updates SKILL.md pipeline table: mode row now specifies 'stop at first
closing code fence' extraction rule. Adds mode_source row documenting
the epilogue/fallback/null semantics. Defers closing sentinel."
```

---

## Task 6: Final Verification

**Step 1: Run full test suite**

Run: `uv run pytest tests/ -x -q`
Expected: All existing tests + 14 new tests pass (7 Stream B + 8 Stream A, exact count depends on existing count)

**Step 2: Run lint**

Run: `uv run ruff check packages/plugins/cross-model/scripts/emit_analytics.py scripts/validate_consultation_contract.py tests/test_emit_analytics.py tests/test_consultation_contract_sync.py`
Expected: No errors

**Step 3: Run conformance validator**

Run: `uv run scripts/validate_consultation_contract.py`
Expected: PASS (17 sections, 7 governance rules, stubs resolved)

**Step 4: Verify ruff format**

Run: `uv run ruff format --check packages/plugins/cross-model/scripts/emit_analytics.py scripts/validate_consultation_contract.py tests/test_emit_analytics.py tests/test_consultation_contract_sync.py`
Expected: All files already formatted (or format them if not)

---

## Final Verification

Run: `uv run pytest tests/ -x -q`
Expected: All tests pass

Run: `uv run ruff check packages/plugins/cross-model/scripts/emit_analytics.py scripts/validate_consultation_contract.py tests/test_emit_analytics.py tests/test_consultation_contract_sync.py`
Expected: No errors

Run: `uv run scripts/validate_consultation_contract.py`
Expected: PASS

## Summary of Deliverables

| Module | New/Modified | What This Plan Adds |
|--------|-------------|---------------------|
| `scripts/validate_consultation_contract.py` | Modified | OSError widening in `read_file` + 5 downstream catches |
| `tests/test_consultation_contract_sync.py` | Modified | 7 new tests: PermissionError (1), scope-breach conformance (2), missing file (1), missing §13 (1), error accumulation (1), validate-level PermissionError (1) |
| `packages/plugins/cross-model/scripts/emit_analytics.py` | Modified | `_VALID_MODE_SOURCES` constant, `mode_source` field in builder, enum validation |
| `tests/test_emit_analytics.py` | Modified | 8 new tests + 1 updated: mode_source propagation (3), absent-key builder (1), enum validation (1), consultation rejection (1), positive validation round-trip (1), field set update (1) |
| `packages/plugins/cross-model/skills/dialogue/SKILL.md` | Modified | Clarified `mode` extraction rule, added `mode_source` pipeline field row |
