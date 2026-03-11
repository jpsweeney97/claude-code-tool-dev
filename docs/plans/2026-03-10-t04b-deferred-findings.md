# T-04b Deferred Findings Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Address three deferred PR #70 findings: error-path tests (A4), three-bucket exception split (A2), and producer defaults (A3).

**Architecture:** Split `emit_envelope` into `_prepare_envelope` (validate + build + serialize) and `_write_envelope_payload` (exclusive file create), keeping `emit_envelope` as public wrapper. `main()` calls the internal functions directly with three-bucket exception handling: validation errors (continue), collision exhaustion (continue), operational I/O failure (abort batch). Producer defaults for `priority`/`effort` ship separately.

**Tech Stack:** Python 3.12+, pytest, no new dependencies

**Source:** Codex dialogue `019cdaea-d124-77c0-94e7-b8223002f509` (5-turn collaborative, all resolved)

**Delivery:** Two PRs, sequential. PR 1 (A2+A4) merges first, PR 2 (A3) builds on it.

---

## File Structure

| File | Role | PR |
|------|------|----|
| `packages/plugins/handoff/scripts/defer.py` | Production: refactor internals, update `main()`, add defaults | 1, 2 |
| `packages/plugins/handoff/tests/test_defer.py` | Tests: helper extraction, 12 CLI contract tests, 2 default tests | 1, 2 |

**No new files.** All changes are modifications to existing files.

**Post-plan test counts:**

| Class | Before | After PR 1 | After PR 2 |
|-------|--------|------------|------------|
| `TestEmitEnvelope` | 8 | 8 | 10 |
| `TestMainEmitsEnvelopes` | 2 | 14 | 14 |
| **Total** | **10** | **22** | **24** |

---

## Chunk 1: PR 1 — Exception Refactor + CLI Contract Tests (A2+A4)

**Branch:** `feature/t04b-a2-a4-exception-refactor-tests`

**Why A2+A4 ship together:** Tests should pin intended (post-refactor) behavior, not current broad-catch behavior. Writing tests for current behavior then updating them in A2 creates churn. The one test that distinguishes old vs new behavior (`test_write_oserror_aborts_batch`) starts red and goes green after the refactor — standard TDD.

### Task 1: Extract `_run_main` test helper

**Files:**
- Modify: `packages/plugins/handoff/tests/test_defer.py:1-10` (add helper after imports)
- Modify: `packages/plugins/handoff/tests/test_defer.py:214-283` (refactor 2 existing tests)

- [ ] **Step 1: Add `_run_main` helper at module level**

Insert after the imports (line 9), before `class TestEmitEnvelope`:

```python
def _run_main(input_json: str, tickets_dir: Path) -> tuple[int, dict]:
    """Run main() with given stdin JSON, return (exit_code, parsed_output)."""
    import io

    from scripts.defer import main

    original_stdin, original_stdout = sys.stdin, sys.stdout
    sys.stdin = io.StringIO(input_json)
    buf = io.StringIO()
    sys.stdout = buf
    try:
        code = main(["--tickets-dir", str(tickets_dir)])
    finally:
        sys.stdin, sys.stdout = original_stdin, original_stdout
    return code, json.loads(buf.getvalue())
```

- [ ] **Step 2: Refactor `test_main_output_format` to use helper**

Replace the body of `test_main_output_format` (lines 215-250):

```python
    def test_main_output_format(self, tmp_path: Path) -> None:
        """CLI writes envelopes and outputs JSON with 'envelopes' key."""
        candidate = {
            "summary": "CLI test", "problem": "Test problem.",
            "source_text": "Quote.", "proposed_approach": "Fix.",
            "acceptance_criteria": ["Done"], "priority": "medium",
            "source_type": "ad-hoc", "source_ref": "", "session_id": "sess-cli",
        }
        code, output = _run_main(json.dumps([candidate]), tmp_path)
        assert code == 0
        assert output["status"] == "ok"
        assert len(output["envelopes"]) == 1
        assert output["envelopes"][0]["path"].endswith(".json")
```

- [ ] **Step 3: Refactor `test_envelopes_written_to_dir` to use helper**

Replace the body of `test_envelopes_written_to_dir` (lines 252-283):

```python
    def test_envelopes_written_to_dir(self, tmp_path: Path) -> None:
        """Envelopes are written to .envelopes/ subdirectory."""
        candidate = {
            "summary": "Dir test", "problem": "Problem.",
            "source_text": "Quote.", "proposed_approach": "Fix.",
            "acceptance_criteria": ["Done"], "priority": "low",
            "source_type": "ad-hoc", "source_ref": "", "session_id": "sess-dir",
        }
        _run_main(json.dumps([candidate]), tmp_path)
        envelopes = list((tmp_path / ".envelopes").glob("*.json"))
        assert len(envelopes) == 1
```

- [ ] **Step 4: Run tests to verify no regression**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_defer.py -v`
Expected: All 10 tests pass.

- [ ] **Step 5: Commit**

```bash
git add packages/plugins/handoff/tests/test_defer.py
git commit -m "refactor(test): extract _run_main helper in test_defer.py"
```

### Task 2: Write 12 CLI error-path and normalization tests

**Files:**
- Modify: `packages/plugins/handoff/tests/test_defer.py` (add 12 tests to `TestMainEmitsEnvelopes`)

**Context:** These tests target post-refactor behavior. 11 pass with current code. `test_write_oserror_aborts_batch` fails (current code continues batch, target behavior aborts). This is expected — it goes green after the refactor in Task 4.

- [ ] **Step 1: Write 6 validation error tests**

Add to `TestMainEmitsEnvelopes`:

```python
    def test_invalid_json_stdin(self, tmp_path: Path) -> None:
        """Invalid JSON input produces error status."""
        code, output = _run_main("not json{{{", tmp_path)
        assert code == 1
        assert output["status"] == "error"
        assert output["envelopes"] == []
        assert "Invalid JSON input" in output["errors"][0]["error"]

    def test_non_dict_candidate_error(self, tmp_path: Path) -> None:
        """Non-dict items in candidate list produce per-item errors."""
        code, output = _run_main(json.dumps([42, "string"]), tmp_path)
        assert code == 1
        assert output["status"] == "error"
        assert len(output["errors"]) == 2
        assert "Candidate must be a dict" in output["errors"][0]["error"]

    def test_missing_summary_key_error(self, tmp_path: Path) -> None:
        """Candidate missing 'summary' produces KeyError."""
        code, output = _run_main(json.dumps([{"problem": "P"}]), tmp_path)
        assert code == 1
        assert "KeyError" in output["errors"][0]["error"]

    def test_missing_problem_key_error(self, tmp_path: Path) -> None:
        """Candidate missing 'problem' produces KeyError."""
        code, output = _run_main(json.dumps([{"summary": "S"}]), tmp_path)
        assert code == 1
        assert "KeyError" in output["errors"][0]["error"]

    def test_non_string_summary_cli_error(self, tmp_path: Path) -> None:
        """Non-string summary produces TypeError at CLI level."""
        code, output = _run_main(json.dumps([{"summary": 42, "problem": "P"}]), tmp_path)
        assert code == 1
        assert "TypeError" in output["errors"][0]["error"]

    def test_empty_summary_cli_error(self, tmp_path: Path) -> None:
        """Whitespace-only summary produces ValueError at CLI level."""
        code, output = _run_main(json.dumps([{"summary": "   ", "problem": "P"}]), tmp_path)
        assert code == 1
        assert "ValueError" in output["errors"][0]["error"]
```

- [ ] **Step 2: Write 4 batch behavior tests**

```python
    def test_all_errors_batch(self, tmp_path: Path) -> None:
        """All-error batch produces 'error' status."""
        candidates = [{"summary": "A"}, {"summary": "B"}]  # Both missing problem
        code, output = _run_main(json.dumps(candidates), tmp_path)
        assert code == 1
        assert output["status"] == "error"
        assert len(output["errors"]) == 2
        assert output["envelopes"] == []

    def test_partial_success_mixed_batch(self, tmp_path: Path) -> None:
        """Mixed batch (one valid, one bad) produces 'partial_success'."""
        candidates = [
            {"summary": "Good", "problem": "Valid."},
            {"summary": "Bad"},  # Missing problem
        ]
        code, output = _run_main(json.dumps(candidates), tmp_path)
        assert code == 1
        assert output["status"] == "partial_success"
        assert len(output["envelopes"]) == 1
        assert len(output["errors"]) == 1

    def test_single_object_normalization(self, tmp_path: Path) -> None:
        """Bare dict (not list) is normalized to single-item list."""
        candidate = {"summary": "Solo", "problem": "Valid."}
        code, output = _run_main(json.dumps(candidate), tmp_path)
        assert code == 0
        assert output["status"] == "ok"
        assert len(output["envelopes"]) == 1

    def test_single_object_with_error(self, tmp_path: Path) -> None:
        """Bare dict with error produces error status."""
        code, output = _run_main(json.dumps({"summary": "No problem"}), tmp_path)
        assert code == 1
        assert output["status"] == "error"
```

- [ ] **Step 3: Write 2 I/O error tests**

```python
    def test_collision_exhaustion_continues_batch(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """FileExistsError from collision exhaustion is candidate-local."""
        import scripts.defer as defer_module

        fixed_now = datetime(2026, 3, 10, 15, 0, 0, tzinfo=timezone.utc)

        class FixedDateTime:
            @classmethod
            def now(cls, tz: timezone | None = None) -> datetime:
                return fixed_now

        monkeypatch.setattr(defer_module, "datetime", FixedDateTime)

        envelopes_dir = tmp_path / ".envelopes"
        envelopes_dir.mkdir(parents=True)
        stem = "2026-03-10T150000Z-collide-me"
        (envelopes_dir / f"{stem}.json").write_text("{}")
        for i in range(1, 100):
            (envelopes_dir / f"{stem}-{i:02d}.json").write_text("{}")

        candidates = [
            {"summary": "Collide me", "problem": "Exhausts collisions."},
            {"summary": "Second item", "problem": "Should succeed."},
        ]
        code, output = _run_main(json.dumps(candidates), tmp_path)
        assert output["status"] == "partial_success"
        assert len(output["errors"]) == 1
        assert "FileExistsError" in output["errors"][0]["error"]
        assert len(output["envelopes"]) == 1
        assert code == 1

    def test_write_oserror_aborts_batch(self, tmp_path: Path) -> None:
        """Non-FileExistsError OSError aborts remaining candidates."""
        envelopes_dir = tmp_path / ".envelopes"
        envelopes_dir.mkdir(parents=True)
        envelopes_dir.chmod(0o444)
        try:
            candidates = [
                {"summary": "First", "problem": "Will fail write."},
                {"summary": "Second", "problem": "Should not be attempted."},
            ]
            code, output = _run_main(json.dumps(candidates), tmp_path)
            assert code == 1
            assert output["status"] == "error"
            assert len(output["errors"]) == 1  # Batch aborted after first
            assert "PermissionError" in output["errors"][0]["error"]
        finally:
            envelopes_dir.chmod(0o755)
```

- [ ] **Step 4: Run tests — expect 11 new pass, 1 new fail**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_defer.py -v`
Expected: `test_write_oserror_aborts_batch` FAILS — current code catches all `OSError` and continues, so `len(errors) == 2` instead of the expected `1`. All other 21 tests pass. This is expected red-green TDD — the test pins the target behavior.

- [ ] **Step 5: Mark the red test as `xfail` for clean CI**

Add `@pytest.mark.xfail(reason="Pre-refactor: OSError continues batch, target: aborts")` above `test_write_oserror_aborts_batch`. This will be removed in Task 4 when the refactor makes it pass.

- [ ] **Step 6: Commit**

```bash
git add packages/plugins/handoff/tests/test_defer.py
git commit -m "test(defer): add 12 CLI contract tests for error paths and normalization (A4)

11 tests pass with current code. test_write_oserror_aborts_batch is
xfail — it pins the post-refactor OSError-aborts-batch behavior
that Task 3-4 will implement."
```

### Task 3: Refactor `emit_envelope` internals

**Files:**
- Modify: `packages/plugins/handoff/scripts/defer.py:27-103`

**Key insight:** Separating `json.dumps` from the write path prevents `TypeError` from serialization being masked as an I/O error (per the 2026-02-20 `emit_analytics.py` prior learning).

- [ ] **Step 1: Replace `_write_envelope_json` and `emit_envelope` with three functions**

Replace lines 27-103 (`_write_envelope_json` + `emit_envelope`) with:

```python
def _prepare_envelope(candidate: dict[str, Any]) -> tuple[str, str]:
    """Validate candidate, build envelope, serialize. Returns (payload_json, stem).

    Raises KeyError for missing required fields, TypeError/ValueError for
    invalid field values. These are candidate-local validation failures.
    """
    for field in ("summary", "problem"):
        value = candidate[field]  # KeyError if missing
        if not isinstance(value, str):
            raise TypeError(f"{field} must be a string, got {type(value).__name__}")
        if not value.strip():
            raise ValueError(f"{field} must be non-empty")

    now = datetime.now(timezone.utc)

    envelope: dict[str, Any] = {
        "envelope_version": "1.0",
        "title": candidate["summary"],
        "problem": candidate["problem"],
        "source": {
            "type": candidate.get("source_type", "ad-hoc"),
            "ref": candidate.get("source_ref", ""),
            "session": candidate.get("session_id", ""),
        },
        "emitted_at": now.isoformat(),
    }

    # Optional fields — only include if present and non-empty.
    if candidate.get("proposed_approach"):
        envelope["approach"] = candidate["proposed_approach"]
    if candidate.get("acceptance_criteria"):
        envelope["acceptance_criteria"] = candidate["acceptance_criteria"]
    if candidate.get("priority"):
        envelope["suggested_priority"] = candidate["priority"]
    if candidate.get("effort"):
        envelope["effort"] = candidate["effort"]
    if candidate.get("files"):
        envelope["key_file_paths"] = candidate["files"]

    # Context composition: branch + source_text folded into context.
    context_parts: list[str] = []
    if candidate.get("branch"):
        context_parts.append(f"Captured on branch `{candidate['branch']}`.")
    if candidate.get("source_text"):
        context_parts.append(f"Evidence anchor:\n> \"{candidate['source_text']}\"")
    if context_parts:
        envelope["context"] = "\n\n".join(context_parts)

    timestamp = now.strftime("%Y-%m-%dT%H%M%SZ")
    stem = f"{timestamp}-{_slug(candidate['summary'])}"
    payload = json.dumps(envelope, indent=2)

    return payload, stem


def _write_envelope_payload(envelopes_dir: Path, stem: str, payload: str) -> Path:
    """Write pre-serialized envelope payload to disk.

    Uses exclusive create mode. Retries with -01 through -99 suffixes.
    Raises FileExistsError after 100 collision attempts (candidate-local).
    Raises OSError on I/O failure (operational — abort batch).
    """
    for attempt in range(100):
        suffix = "" if attempt == 0 else f"-{attempt:02d}"
        path = envelopes_dir / f"{stem}{suffix}.json"
        try:
            with path.open("x", encoding="utf-8") as handle:
                handle.write(payload)
        except FileExistsError:
            continue
        return path

    raise FileExistsError(f"Envelope filename collision after 100 attempts for stem: {stem}")


def emit_envelope(candidate: dict[str, Any], envelopes_dir: Path) -> Path:
    """Write a DeferredWorkEnvelope JSON file. Returns the path.

    Maps /defer candidate fields to envelope schema v1.0. The envelope
    carries no status — the ticket engine consumer synthesizes it.
    """
    envelopes_dir.mkdir(parents=True, exist_ok=True)
    payload, stem = _prepare_envelope(candidate)
    return _write_envelope_payload(envelopes_dir, stem, payload)
```

**Design note:** `emit_envelope` retains `mkdir` for standalone callers (e.g., unit tests, future non-CLI usage). `main()` in Task 4 will bypass this wrapper entirely, calling `_prepare_envelope` + `_write_envelope_payload` directly with its own `mkdir` before the loop. The `mkdir` in `emit_envelope` is idempotent and harmless when `main()` has already created the directory.

- [ ] **Step 2: Run unit tests to verify no regression**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_defer.py::TestEmitEnvelope -v`
Expected: All 8 unit tests pass (public API unchanged).

- [ ] **Step 3: Commit**

```bash
git add packages/plugins/handoff/scripts/defer.py
git commit -m "refactor(defer): split emit_envelope into _prepare_envelope + _write_envelope_payload (A2)"
```

### Task 4: Update `main()` with three-bucket catches

**Files:**
- Modify: `packages/plugins/handoff/scripts/defer.py:106-152` (the `main()` function)

**Key changes:**
1. `main()` bypasses `emit_envelope` — calls `_prepare_envelope` + `_write_envelope_payload` directly for finer-grained error control
2. `mkdir` runs once before the candidate loop (operational failure = immediate abort)
3. Per-candidate: `_prepare_envelope` call with validation catch, then `_write_envelope_payload` with I/O catches
4. `FileExistsError` caught before `OSError` (subclass ordering — Python matches first matching except clause)

- [ ] **Step 1: Rewrite `main()` candidate processing**

Replace lines 126-144 (from `envelopes_dir = args.tickets_dir / ".envelopes"` through the for loop body, up to but not including the status output block):

```python
    envelopes_dir = args.tickets_dir / ".envelopes"
    envelopes_dir.mkdir(parents=True, exist_ok=True)
    created: list[dict[str, str]] = []
    errors: list[dict[str, str]] = []

    for cand in candidates:
        if not isinstance(cand, dict):
            errors.append({
                "summary": "unknown",
                "error": f"Candidate must be a dict, got {type(cand).__name__}",
            })
            continue
        try:
            payload, stem = _prepare_envelope(cand)
        except (KeyError, TypeError, ValueError) as exc:
            errors.append({
                "summary": cand.get("summary", "unknown"),
                "error": f"{type(exc).__name__}: {exc}",
            })
            continue
        try:
            path = _write_envelope_payload(envelopes_dir, stem, payload)
        except FileExistsError as exc:
            errors.append({
                "summary": cand.get("summary", "unknown"),
                "error": f"FileExistsError: {exc}",
            })
            continue
        except OSError as exc:
            errors.append({
                "summary": cand.get("summary", "unknown"),
                "error": f"{type(exc).__name__}: {exc}",
            })
            break
        created.append({"path": str(path)})
```

The status output block (lines 146-152) remains unchanged.

- [ ] **Step 2: Remove `xfail` marker from `test_write_oserror_aborts_batch`**

The test now passes — remove the `@pytest.mark.xfail(...)` decorator added in Task 2.

- [ ] **Step 3: Run all tests — all 22 should pass**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_defer.py -v`
Expected: All 22 tests pass. `test_write_oserror_aborts_batch` now passes (was xfail, now green).

- [ ] **Step 4: Commit**

```bash
git add packages/plugins/handoff/scripts/defer.py
git commit -m "feat(defer): three-bucket exception handling in main() (A2)

Bucket 1: (KeyError, TypeError, ValueError) from _prepare_envelope
  -> continue batch (candidate-local validation failure)
Bucket 2: FileExistsError from _write_envelope_payload
  -> continue batch (collision exhaustion is candidate-local)
Bucket 3: other OSError from _write_envelope_payload
  -> abort batch (operational failure, e.g. read-only filesystem)

mkdir runs once before the loop so FileExistsError in the write
helper always means collision exhaustion, not directory creation."
```

### Task 5: Run full suite and create PR

- [ ] **Step 1: Run full handoff plugin test suite**

Run: `cd packages/plugins/handoff && uv run pytest -v`
Expected: All tests pass (325+ tests).

- [ ] **Step 2: Push and create PR**

```bash
git push -u origin feature/t04b-a2-a4-exception-refactor-tests
```

PR title: `refactor(defer): three-bucket exception split + 12 CLI contract tests (A2+A4)`

PR body should include:
- The three-bucket exception semantics
- Test count changes (10 → 22)
- Link to Codex dialogue thread `019cdaea-d124-77c0-94e7-b8223002f509` `019cdaea-d124-77c0-94e7-b8223002f509`
- Note: A3 (producer defaults) ships as a separate follow-up PR

---

## Chunk 2: PR 2 — Producer Defaults (A3)

**Branch:** `feature/t04b-a3-producer-defaults` (based on `main` after PR 1 merges)

**Decision from dialogue:** Reject cross-plugin import of `validate_envelope`. Reject local enum duplication. Only apply SKILL.md-documented defaults: `priority` defaults to `"medium"`, `effort` defaults to `"S"`.

### Task 6: Write default-behavior tests

**Files:**
- Modify: `packages/plugins/handoff/tests/test_defer.py` (add 2 tests to `TestEmitEnvelope`)

- [ ] **Step 1: Write 2 default-behavior tests**

Add to `TestEmitEnvelope`:

```python
    def test_producer_defaults_applied(self, tmp_path: Path) -> None:
        """Absent priority/effort get SKILL.md-documented defaults."""
        from scripts.defer import emit_envelope

        candidate = {"summary": "Test defaults", "problem": "No priority or effort."}
        path = emit_envelope(candidate, tmp_path / ".envelopes")
        data = json.loads(path.read_text())
        assert data["suggested_priority"] == "medium"
        assert data["effort"] == "S"

    def test_explicit_values_override_defaults(self, tmp_path: Path) -> None:
        """Explicit priority/effort override defaults."""
        from scripts.defer import emit_envelope

        candidate = {
            "summary": "Test override", "problem": "Has values.",
            "priority": "high", "effort": "XL",
        }
        path = emit_envelope(candidate, tmp_path / ".envelopes")
        data = json.loads(path.read_text())
        assert data["suggested_priority"] == "high"
        assert data["effort"] == "XL"
```

- [ ] **Step 2: Run tests — expect 1 fail**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_defer.py::TestEmitEnvelope::test_producer_defaults_applied tests/test_defer.py::TestEmitEnvelope::test_explicit_values_override_defaults -v`
Expected: `test_producer_defaults_applied` FAILS with `KeyError: 'suggested_priority'` — the field is absent in the envelope when `priority` is not provided. `test_explicit_values_override_defaults` passes.

- [ ] **Step 3: Commit**

```bash
git add packages/plugins/handoff/tests/test_defer.py
git commit -m "test(defer): add default-behavior tests for priority and effort (A3)"
```

### Task 7: Apply producer defaults

**Files:**
- Modify: `packages/plugins/handoff/scripts/defer.py` (in `_prepare_envelope`)

- [ ] **Step 1: Replace conditional assignment with defaults**

In `_prepare_envelope`, find:

```python
    if candidate.get("priority"):
        envelope["suggested_priority"] = candidate["priority"]
    if candidate.get("effort"):
        envelope["effort"] = candidate["effort"]
```

Replace with:

```python
    envelope["suggested_priority"] = candidate.get("priority") or "medium"
    envelope["effort"] = candidate.get("effort") or "S"
```

- [ ] **Step 2: Run all tests — all 24 should pass**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_defer.py -v`
Expected: All 24 tests pass. `test_producer_defaults_applied` now passes.

- [ ] **Step 3: Commit**

```bash
git add packages/plugins/handoff/scripts/defer.py
git commit -m "feat(defer): apply SKILL.md-documented defaults for priority and effort (A3)

priority defaults to 'medium', effort defaults to 'S' when not
provided by the LLM extractor. Matches SKILL.md candidate schema
(lines 63, 68). Consumer-side validation in validate_envelope
remains authoritative — no cross-plugin import added."
```

### Task 8: Run full suite and create PR

- [ ] **Step 1: Run full handoff plugin test suite**

Run: `cd packages/plugins/handoff && uv run pytest -v`
Expected: All tests pass.

- [ ] **Step 2: Push and create PR**

```bash
git push -u origin feature/t04b-a3-producer-defaults
```

PR title: `feat(defer): apply SKILL.md-documented defaults for priority and effort (A3)`

PR body should include:
- What was rejected: cross-plugin `validate_envelope` import, local enum duplication
- What was added: defaults for `priority` ("medium") and `effort` ("S")
- Link to Codex dialogue thread `019cdaea-d124-77c0-94e7-b8223002f509`
- Note the emerged finding: SKILL.md "Required" column semantics need doc-only clarification (separate follow-up)

---

## Post-Implementation Follow-Up (Not Part of This Plan)

**SKILL.md "Required" column clarification:** The dialogue surfaced that SKILL.md lines 56-69 use "Required" to mean "extractor should try to supply," not "must be present in candidate JSON." This is a doc-only wording fix. Handle as a separate commit, not a PR.
