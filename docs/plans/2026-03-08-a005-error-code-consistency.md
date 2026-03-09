# A-005: Error-Code Consistency Implementation Plan

**Goal:** Ensure every non-success `EngineResponse` in the ticket engine includes a machine-readable `error_code`, closing the 7 gaps identified in architectural review finding A-005.

**Architecture:** Add one new error code (`io_error`) to the contract for infrastructure failures, fix the 7 `escalate` paths that omit `error_code`, enforce the invariant via `__post_init__` on `EngineResponse`, and add a sweep test proving all non-ok paths carry an error_code. No state changes, no exit code changes.

**Tech Stack:** Python 3, pytest, dataclasses

---

## Background

The ticket engine defines 15 machine states and 11 error codes. Success states (`ok`, `ok_create`, `ok_update`, `ok_close`, `ok_close_archived`, `ok_reopen`) omit `error_code`; all other states should include one. Seven `escalate` paths currently omit `error_code`:

| # | File:Line | Context | New `error_code` |
|---|-----------|---------|-------------------|
| 1 | `ticket_engine_core.py:157` | classify: unknown action | `intent_mismatch` |
| 2 | `ticket_engine_core.py:1385` | create: write OSError | `io_error` (new) |
| 3 | `ticket_engine_core.py:1396` | create: retry budget exhausted | `io_error` (new) |
| 4 | `ticket_engine_core.py:1473` | update: `fields.ticket_id` mismatch | `intent_mismatch` |
| 5 | `ticket_engine_core.py:1487` | update: section/unknown fields | `intent_mismatch` |
| 6 | `ticket_engine_core.py:1643` | archive: collision suffix exhausted | `io_error` (new) |
| 7 | `ticket_engine_core.py:1651` | archive: rename OSError | `io_error` (new) |

**Error-code rationale:**
- `intent_mismatch` for #1, #4, #5: the caller's request doesn't match what the action supports (unknown action, wrong ticket_id in fields, unsupported field names). Consistent with the existing `intent_mismatch` usage in preflight (line 460) and execute dispatch (line 1254).
- `io_error` (new) for #2, #3, #6, #7: infrastructure write failures where the operation itself is valid but the filesystem rejected it. No existing code covers this — `parse_error` is for format/parse issues, not write failures.

**Exit-code impact:** None. The entrypoint maps `error_code == "need_fields"` to exit 2; all other non-ok states exit 1. Neither `intent_mismatch` nor `io_error` triggers the exit-2 path.

**Key files:**
- Engine: `packages/plugins/ticket/scripts/ticket_engine_core.py`
- Contract: `packages/plugins/ticket/references/ticket-contract.md`
- Tests: `packages/plugins/ticket/tests/test_engine.py`

**Existing tests that need updating** (9 tests assert state/message but not error_code, or explicitly assert `error_code is None`):

| Test | Line | Current assertion | New assertion |
|------|------|-------------------|---------------|
| `test_unknown_action` | 99 | state only | + `error_code == "intent_mismatch"` |
| `test_execute_create_fails_after_retry_budget_exhausted` | 1125 | state + message | + `error_code == "io_error"` |
| `test_update_rejects_section_fields` | 1224 | state + message | + `error_code == "intent_mismatch"` |
| `test_update_rejects_mixed_frontmatter_and_section_fields_atomically` | 1243 | state + message | + `error_code == "intent_mismatch"` |
| `test_update_rejects_unknown_field_and_leaves_file_unchanged` | 1269 | state + message | + `error_code == "intent_mismatch"` |
| `test_update_rejects_mismatched_fields_ticket_id` | 1317 | state + message | + `error_code == "intent_mismatch"` |
| `test_close_archive_rename_failure_returns_escalate` | 1860 | state + message | + `error_code == "io_error"` |
| `test_close_archive_collision_suffix_exhausted_returns_escalate` | 1884 | state + message | + `error_code == "io_error"` |
| `test_update_rejects_unknown_fields_before_serialization` | 2173 | `error_code is None` | `error_code == "intent_mismatch"` |

---

## Task 1: Update the contract

**Files:**
- Modify: `packages/plugins/ticket/references/ticket-contract.md:86-88`

**Step 1: Add `io_error` to the error codes list**

Change line 86-88 from:

```markdown
### Error Codes (11)

need_fields, invalid_transition, policy_blocked, preflight_failed, stale_plan, duplicate_candidate, parse_error, not_found, dependency_blocked, intent_mismatch, origin_mismatch
```

To:

```markdown
### Error Codes (12)

need_fields, invalid_transition, policy_blocked, preflight_failed, stale_plan, duplicate_candidate, parse_error, io_error, not_found, dependency_blocked, intent_mismatch, origin_mismatch
```

**Step 2: Update the `EngineResponse` docstring count**

In `packages/plugins/ticket/scripts/ticket_engine_core.py:40`, change:

```python
    error_code: machine-readable error code (10 defined codes, or None on success)
```

To:

```python
    error_code: machine-readable error code (12 defined codes, or None on success)
```

Note: the docstring already said "10" when the contract has 11. Fix to the correct count of 12.

**Step 3: Commit**

```bash
cd packages/plugins/ticket
git add references/ticket-contract.md scripts/ticket_engine_core.py
git commit -m "docs(ticket): add io_error to contract error codes (A-005)"
```

---

## Task 2: Write failing tests for the 7 error-code gaps

**Files:**
- Modify: `packages/plugins/ticket/tests/test_engine.py`

**Step 1: Update 9 existing tests to assert error_code**

In `TestEngineClassify.test_unknown_action` (around line 106), add after `assert resp.state == "escalate"`:

```python
        assert resp.error_code == "intent_mismatch"
```

In `TestEngineExecute.test_execute_create_fails_after_retry_budget_exhausted` (around line 1156), add after `assert resp.state == "escalate"`:

```python
        assert resp.error_code == "io_error"
```

In `TestEngineExecute.test_update_rejects_section_fields` (around line 1239), add after `assert resp.state == "escalate"`:

```python
        assert resp.error_code == "intent_mismatch"
```

In `TestEngineExecute.test_update_rejects_mixed_frontmatter_and_section_fields_atomically` (around line 1263), add after `assert resp.state == "escalate"`:

```python
        assert resp.error_code == "intent_mismatch"
```

In `TestEngineExecute.test_update_rejects_unknown_field_and_leaves_file_unchanged` (around line 1289), add after `assert resp.state == "escalate"`:

```python
        assert resp.error_code == "intent_mismatch"
```

In `TestEngineExecute.test_update_rejects_mismatched_fields_ticket_id` (around line 1337), add after `assert resp.state == "escalate"`:

```python
        assert resp.error_code == "intent_mismatch"
```

In `TestEngineExecute.test_close_archive_rename_failure_returns_escalate` (around line 1881), add after `assert resp.state == "escalate"`:

```python
        assert resp.error_code == "io_error"
```

In `TestEngineExecute.test_close_archive_collision_suffix_exhausted_returns_escalate` (around line 1921), add after `assert resp.state == "escalate"`:

```python
        assert resp.error_code == "io_error"
```

In `TestEngineExecuteIntegration.test_update_rejects_unknown_fields_before_serialization` (around line 2194), change:

```python
        assert resp.error_code is None
```

To:

```python
        assert resp.error_code == "intent_mismatch"
```

**Step 2: Add new test for create write OSError (gap #2 — no existing test)**

Add to `TestEngineExecute` class, after `test_execute_create_fails_after_retry_budget_exhausted`:

```python
    def test_execute_create_write_oserror_returns_escalate_with_io_error(
        self, tmp_tickets: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def oserror_write(ticket_path: Path, content: str) -> None:
            raise OSError("disk full")

        monkeypatch.setattr(ticket_engine_core, "_write_text_exclusive", oserror_write)

        resp = engine_execute(
            action="create",
            ticket_id=None,
            fields={
                "title": "Write failure",
                "problem": "Create should return io_error on OSError.",
                "priority": "medium",
            },
            session_id="oserror-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
            hook_injected=True,
            hook_request_origin="user",
            classify_intent="create",
            classify_confidence=0.95,
            dedup_fingerprint=compute_dedup_fp("Create should return io_error on OSError.", []),
        )
        assert resp.state == "escalate"
        assert resp.error_code == "io_error"
        assert "create failed" in resp.message.lower()
```

**Step 3: Run tests to verify they fail**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_engine.py -k "test_unknown_action or test_execute_create_fails_after_retry or test_execute_create_write_oserror or test_update_rejects_section_fields or test_update_rejects_mixed_frontmatter or test_update_rejects_unknown_field_and_leaves or test_update_rejects_mismatched_fields or test_close_archive_rename_failure or test_close_archive_collision_suffix or test_update_rejects_unknown_fields_before" -v`

Expected: 10 FAILED (the new error_code assertions fail because the engine doesn't set error_code on these paths yet).

**Step 4: Commit failing tests**

```bash
git add tests/test_engine.py
git commit -m "test(ticket): add error_code assertions for 7 escalate gaps (A-005, red)"
```

---

## Task 3: Fix the 7 error-code gaps in the engine

**Files:**
- Modify: `packages/plugins/ticket/scripts/ticket_engine_core.py`

**Step 1: Fix gap #1 — classify unknown action (line 157)**

Change:

```python
        return EngineResponse(
            state="escalate",
            message=f"Unknown action: {action!r}. Valid: {', '.join(sorted(VALID_ACTIONS))}",
        )
```

To:

```python
        return EngineResponse(
            state="escalate",
            message=f"Unknown action: {action!r}. Valid: {', '.join(sorted(VALID_ACTIONS))}",
            error_code="intent_mismatch",
        )
```

**Step 2: Fix gap #2 — create write OSError (line 1385)**

Change:

```python
            return EngineResponse(
                state="escalate",
                message=f"create failed: {exc}. Got: {str(ticket_path)!r:.100}",
            )
```

To:

```python
            return EngineResponse(
                state="escalate",
                message=f"create failed: {exc}. Got: {str(ticket_path)!r:.100}",
                error_code="io_error",
            )
```

**Step 3: Fix gap #3 — create retry exhaustion (line 1396)**

Change:

```python
    return EngineResponse(
        state="escalate",
        message=(
            "create failed: exclusive write retry budget exhausted after "
            f"{_CREATE_WRITE_RETRY_LIMIT} attempts. Got: {title!r:.100}"
        ),
    )
```

To:

```python
    return EngineResponse(
        state="escalate",
        message=(
            "create failed: exclusive write retry budget exhausted after "
            f"{_CREATE_WRITE_RETRY_LIMIT} attempts. Got: {title!r:.100}"
        ),
        error_code="io_error",
    )
```

**Step 4: Fix gap #4 — update ticket_id mismatch (line 1473)**

Change:

```python
        return EngineResponse(
            state="escalate",
            message=f"Update failed: fields.ticket_id must match top-level ticket_id. Got: {fields.get('ticket_id')!r:.100}",
            ticket_id=ticket_id,
        )
```

To:

```python
        return EngineResponse(
            state="escalate",
            message=f"Update failed: fields.ticket_id must match top-level ticket_id. Got: {fields.get('ticket_id')!r:.100}",
            ticket_id=ticket_id,
            error_code="intent_mismatch",
        )
```

**Step 5: Fix gap #5 — update section/unknown fields (line 1487)**

Change:

```python
        return EngineResponse(
            state="escalate",
            message=f"Update failed: {'; '.join(parts)}",
            ticket_id=ticket_id,
        )
```

To:

```python
        return EngineResponse(
            state="escalate",
            message=f"Update failed: {'; '.join(parts)}",
            ticket_id=ticket_id,
            error_code="intent_mismatch",
        )
```

**Step 6: Fix gap #6 — archive collision exhaustion (line 1643)**

Change:

```python
                return EngineResponse(
                    state="escalate",
                    message=f"archive collision resolution failed: exhausted suffix search. Got: {ticket_path.name!r:.100}",
                    ticket_id=ticket_id,
                )
```

To:

```python
                return EngineResponse(
                    state="escalate",
                    message=f"archive collision resolution failed: exhausted suffix search. Got: {ticket_path.name!r:.100}",
                    ticket_id=ticket_id,
                    error_code="io_error",
                )
```

**Step 7: Fix gap #7 — archive rename failure (line 1651)**

Change:

```python
            return EngineResponse(
                state="escalate",
                message=f"archive rename failed: {exc}. Got: {str(dst)!r:.100}",
                ticket_id=ticket_id,
            )
```

To:

```python
            return EngineResponse(
                state="escalate",
                message=f"archive rename failed: {exc}. Got: {str(dst)!r:.100}",
                ticket_id=ticket_id,
                error_code="io_error",
            )
```

**Step 8: Run the previously-failing tests to verify they pass**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_engine.py -k "test_unknown_action or test_execute_create_fails_after_retry or test_execute_create_write_oserror or test_update_rejects_section_fields or test_update_rejects_mixed_frontmatter or test_update_rejects_unknown_field_and_leaves or test_update_rejects_mismatched_fields or test_close_archive_rename_failure or test_close_archive_collision_suffix or test_update_rejects_unknown_fields_before" -v`

Expected: 10 PASSED

**Step 9: Run full test suite**

Run: `cd packages/plugins/ticket && uv run pytest -q`

Expected: 511 passed (510 + 1 new test)

**Step 10: Commit**

```bash
git add scripts/ticket_engine_core.py
git commit -m "fix(ticket): add missing error_code to 7 escalate paths (A-005)"
```

---

## Task 4: Add `__post_init__` invariant enforcement to `EngineResponse`

**Files:**
- Modify: `packages/plugins/ticket/scripts/ticket_engine_core.py:35-64`
- Modify: `packages/plugins/ticket/tests/test_engine.py` (new test class)

**Step 1: Write failing test for the invariant**

Add a new test class at the end of `test_engine.py`:

```python
class TestEngineResponseInvariant:
    """EngineResponse enforces error_code on non-success states."""

    _OK_STATES = frozenset({
        "ok", "ok_create", "ok_update", "ok_close", "ok_close_archived", "ok_reopen",
    })

    def test_success_state_allows_no_error_code(self):
        for state in self._OK_STATES:
            resp = EngineResponse(state=state, message="ok")
            assert resp.error_code is None

    def test_success_state_rejects_error_code(self):
        with pytest.raises(ValueError, match="error_code must be None"):
            EngineResponse(state="ok", message="ok", error_code="intent_mismatch")

    def test_non_success_state_requires_error_code(self):
        with pytest.raises(ValueError, match="error_code is required"):
            EngineResponse(state="escalate", message="bad")

    def test_non_success_state_accepts_error_code(self):
        resp = EngineResponse(state="escalate", message="bad", error_code="intent_mismatch")
        assert resp.error_code == "intent_mismatch"

    def test_need_fields_state_requires_error_code(self):
        resp = EngineResponse(state="need_fields", message="missing", error_code="need_fields")
        assert resp.error_code == "need_fields"

    def test_duplicate_candidate_state_requires_error_code(self):
        resp = EngineResponse(state="duplicate_candidate", message="dup", error_code="duplicate_candidate")
        assert resp.error_code == "duplicate_candidate"
```

**Step 2: Run to verify failures**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_engine.py::TestEngineResponseInvariant -v`

Expected: `test_success_state_rejects_error_code` and `test_non_success_state_requires_error_code` FAIL (no `__post_init__` yet). Others PASS.

**Step 3: Add `__post_init__` to `EngineResponse`**

In `packages/plugins/ticket/scripts/ticket_engine_core.py`, add after the `data` field (after line 50) and before `def to_dict`:

```python
    _OK_STATES: frozenset[str] = field(
        default=frozenset({
            "ok", "ok_create", "ok_update", "ok_close", "ok_close_archived", "ok_reopen",
        }),
        init=False,
        repr=False,
        compare=False,
    )

    def __post_init__(self) -> None:
        if self.state in self._OK_STATES:
            if self.error_code is not None:
                raise ValueError(
                    f"error_code must be None for success state {self.state!r}, "
                    f"got {self.error_code!r}"
                )
        else:
            if self.error_code is None:
                raise ValueError(
                    f"error_code is required for non-success state {self.state!r}. "
                    f"Message: {self.message!r:.100}"
                )
```

**Step 4: Run invariant tests**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_engine.py::TestEngineResponseInvariant -v`

Expected: 6 PASSED

**Step 5: Run full test suite**

Run: `cd packages/plugins/ticket && uv run pytest -q`

Expected: 517 passed (511 + 6 invariant tests). If any test fails here, it means there's an `EngineResponse` construction we missed — investigate and fix.

**Step 6: Commit**

```bash
git add scripts/ticket_engine_core.py tests/test_engine.py
git commit -m "fix(ticket): enforce error_code invariant on EngineResponse (A-005)"
```

---

## Task 5: Final verification

**Step 1: Run full test suite from clean state**

Run: `cd packages/plugins/ticket && uv run pytest -v`

Expected: All tests pass (approximately 517).

**Step 2: Verify no behavioral change in exit codes**

Run a quick sanity check that the entrypoint exit-code logic still works as before. The key line in both `ticket_engine_user.py:100` and `ticket_engine_agent.py:100`:

```python
elif resp.error_code == "need_fields":
    sys.exit(2)
```

Verify: none of the 7 fixed paths use `error_code="need_fields"`, so exit codes are unchanged.

**Step 3: Commit summary (squash or leave as-is)**

The 4 commits from this plan:
1. `docs(ticket): add io_error to contract error codes (A-005)` — contract + docstring
2. `test(ticket): add error_code assertions for 7 escalate gaps (A-005, red)` — test expectations
3. `fix(ticket): add missing error_code to 7 escalate paths (A-005)` — engine fixes
4. `fix(ticket): enforce error_code invariant on EngineResponse (A-005)` — __post_init__ guard

These can be left as separate commits (they tell the TDD story) or squashed into one.
