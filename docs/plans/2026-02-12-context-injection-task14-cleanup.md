# Context Injection Task 14: Cleanup Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Address all 32 deferred quality items from S2-S7 reviews across 4 sessions, then mark S7 complete.

**Architecture:** No behavioral changes in Sessions 1-2. Sessions 3-4 refine edge-case logic in entity extraction and cross-cutting types. All work is on branch `docs/cross-model-learning-system`. Each session ends with a commit and green tests (215+ passing).

**Tech Stack:** Python 3.14, Pydantic 2.12, MCP SDK 1.26.0, ruff, pytest

**Branch:** `docs/cross-model-learning-system`

**Baseline:** 215 tests passing, 6 ruff errors (all F401), 4 files need reformatting.

---

## Session Map

| Session | Scope | Items | Commits |
|---------|-------|-------|---------|
| 1 | Mechanical cleanup + comments/docs | 17 | 1 |
| 2 | Test improvements | 5 | 1 |
| 3 | Entity extraction refinements | 5 | 1 |
| 4 | Cross-cutting fixes + close S7 | 5 | 1-2 |

Sessions are independent — each starts from the prior session's commit. No cross-session dependencies beyond sequential application.

---

## Session 1: Mechanical Cleanup + Comments

**Goal:** Fix all ruff errors, reformat files, remove dead code, add documentation comments. Zero behavioral changes.

**Commit message:** `chore(context-injection): lint cleanup and documentation comments`

### Task 1.1: Run ruff autofix and format

**Files:**
- Modify: `context_injection/types.py:15`
- Modify: `context_injection/canonical.py:17`
- Modify: `context_injection/entities.py:69-83`
- Modify: `tests/test_canonical.py:5`
- Modify: `tests/test_enums.py:3`
- Format: `tests/test_canonical.py`, `tests/test_integration.py`, `tests/test_server.py`, `tests/test_state.py`

**Step 1: Run ruff autofix**

Run: `cd packages/context-injection && uv run ruff check --fix .`
Expected: 6 errors fixed (all F401 unused imports)

This removes:
- `types.py:15` — `ClaimStatus, Posture, TemplateId` imports (entire import line removed)
- `canonical.py:17` — `ScoutSpec` from the import (keep `ProtocolModel, ReadSpec, GrepSpec`)
- `tests/test_canonical.py:5` — `import pytest`
- `tests/test_enums.py:3` — `import pytest`

**Step 2: Run ruff format**

Run: `cd packages/context-injection && uv run ruff format .`
Expected: 4 files reformatted

**Step 3: Remove dead `EntityTypeLiteral` type alias**

Ruff won't catch this — it's defined but never referenced. Delete `entities.py:69-83`:

```python
# DELETE this entire block:
EntityTypeLiteral = Literal[
    "file_loc",
    "file_path",
    "file_name",
    "symbol",
    "dir_path",
    "env_var",
    "config_key",
    "cli_flag",
    "command",
    "package_name",
    "file_hint",
    "symbol_hint",
    "config_hint",
]
```

After deletion, also remove the `Literal` import from `entities.py:19` if it becomes unused. Check: `Literal` is used in `_confidence()` return type annotation (line 220) — so keep it.

**Step 4: Verify ruff is clean**

Run: `cd packages/context-injection && uv run ruff check . && uv run ruff format --check .`
Expected: 0 errors, 0 files to reformat

**Step 5: Run tests**

Run: `cd packages/context-injection && uv run pytest tests/ -q`
Expected: 215 passed

### Task 1.2: Fix `field(default=None)` inconsistency in paths.py

**Files:**
- Modify: `context_injection/paths.py:91`

**Step 1: Replace `field(default=None)` with `= None`**

Change line 91 from:
```python
    candidates: list[str] | None = field(default=None)
```
to:
```python
    candidates: list[str] | None = None
```

`None` is immutable — `field()` is only needed for mutable defaults like `list()`.

**Step 2: Check if `field` import is still used**

Search `paths.py` for other `field(` usages. If none remain, remove `field` from the `from dataclasses import dataclass, field` line (line 14).

Run: `cd packages/context-injection && uv run ruff check context_injection/paths.py`
Expected: 0 errors

### Task 1.3: Fix redundant case-handling in paths.py

**Files:**
- Modify: `context_injection/paths.py:64-68, 271-272`

**Step 1: Remove `re.IGNORECASE` from risk signal patterns**

The call site already does `path_lower = path.lower()`. The `re.IGNORECASE` flag is redundant.

Change lines 64-68 from:
```python
_RISK_SIGNAL_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"secret", re.IGNORECASE),
    re.compile(r"token", re.IGNORECASE),
    re.compile(r"credential", re.IGNORECASE),
)
```
to:
```python
_RISK_SIGNAL_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"secret"),
    re.compile(r"token"),
    re.compile(r"credential"),
)
```

The `.lower()` call at line 271 handles case-insensitivity.

**Step 2: Run tests**

Run: `cd packages/context-injection && uv run pytest tests/test_paths.py -q`
Expected: 22 passed

### Task 1.4: Fix `object` type in test helper

**Files:**
- Modify: `tests/test_pipeline.py:33`

**Step 1: Replace `object` with `Any`**

Change line 33 from:
```python
def _make_turn_request(**overrides: object) -> TurnRequest:
```
to:
```python
def _make_turn_request(**overrides: Any) -> TurnRequest:
```

Add `Any` to the existing imports at the top of the file. Check what's already imported — line 14 has `from unittest.mock import patch`. Add:
```python
from typing import Any
```

This also removes the `# type: ignore[arg-type]` on line 45 (the `TurnRequest(**defaults)` call) if the type checker is satisfied. If not, keep the ignore comment — the `Any` type is still more accurate than `object`.

### Task 1.5: Remove unused `repo_root` parameter from `create_server()`

**Files:**
- Modify: `context_injection/server.py:47`

**Step 1: Remove the parameter**

Change line 47 from:
```python
def create_server(repo_root: str | None = None) -> FastMCP:
```
to:
```python
def create_server() -> FastMCP:
```

**Step 2: Update docstring**

Change line 48 from:
```python
    """Create the FastMCP instance (useful for testing without running)."""
```
to:
```python
    """Create the FastMCP instance. Useful for testing without starting stdio."""
```

**Step 3: Check callers**

Search for `create_server(` in tests. `test_server.py` calls `create_server()` with no arguments (lines 9, 14) — no changes needed.

### Task 1.6: Add documentation comments

**Files:**
- Modify: `context_injection/state.py:64-67`
- Modify: `context_injection/paths.py:75-84, 21-34, 213-231`
- Modify: `context_injection/server.py:57-62`
- Modify: `context_injection/pipeline.py:167-168`
- Modify: `tests/test_server.py:15`
- Modify: `docs/plans/2026-02-12-context-injection-v0a-progress.md:100`

**Step 1: Add `next_entity_id()` docstring** (`state.py:64`)

Change:
```python
    def next_entity_id(self) -> str:
        """Generate the next entity ID (e_NNN format)."""
```
to:
```python
    def next_entity_id(self) -> str:
        """Generate the next entity ID (e_NNN format, monotonic per process)."""
```

**Step 2: Add CompileTimeResult cross-reference** (`paths.py:76-84`)

Add a cross-reference line to the docstring. Change:
```python
class CompileTimeResult:
    """Result of check_path_compile_time().

    status values align with PathStatus enum:
    - "allowed": safe to scout
    - "denied": blocked by denylist
    - "not_tracked": not in git ls-files
    - "unresolved": could not resolve path
    """
```
to:
```python
class CompileTimeResult:
    """Result of check_path_compile_time().

    Maps to PathDecision (types.py) in the pipeline via field-by-field copy
    in pipeline.py:145-156. Both types use the same status values.

    status values align with PathStatus enum:
    - "allowed": safe to scout
    - "denied": blocked by denylist
    - "not_tracked": not in git ls-files
    - "unresolved": could not resolve path
    """
```

**Step 3: Add `_is_denied_dir` clarity comment** (`paths.py:213-231`)

Add a comment before the function. Change:
```python
def _is_denied_dir(path: str) -> str | None:
    """Check if any path component matches a denied directory pattern.

    Returns deny reason or None.
    """
```
to:
```python
def _is_denied_dir(path: str) -> str | None:
    """Check if any path component matches a denied directory pattern.

    For simple patterns (no /): fnmatch against individual components.
    For patterns with / (e.g., ".git/*"): fnmatch against accumulated path prefix.

    Returns deny reason or None.
    """
```

**Step 4: Add denylist dual-pattern comment** (`paths.py:21-34`)

Add a comment after the tuple. Change line 35:
```python
"""Glob patterns for denied directory prefixes. Matched against path components."""
```
to:
```python
"""Glob patterns for denied directory prefixes.

Each directory has two entries: bare name (denies the directory itself) and
name/* (denies any file within it). Both are needed because fnmatch matches
against individual path components, not the full path.
"""
```

**Step 5: Add `model_dump` rationale comment** (`server.py:62`)

Change:
```python
        result = process_turn(request, app_ctx)
        return result.model_dump(mode="json")
```
to:
```python
        result = process_turn(request, app_ctx)
        # Return dict to avoid FastMCP double-serialization of discriminated unions.
        # TurnPacket uses Annotated[Union[...], Discriminator(...)] which the SDK's
        # serializer may not handle correctly.
        return result.model_dump(mode="json")
```

**Step 6: Add `_tool_manager` comment** (`test_server.py:15`)

Change:
```python
    tools = server._tool_manager.list_tools()
```
to:
```python
    # _tool_manager is private API; no public tool listing method in FastMCP v1.26.0.
    tools = server._tool_manager.list_tools()
```

**Step 7: Add redundant `compute_budget` comment** (`pipeline.py:167-168`)

Change:
```python
    # --- Step 5: Budget computation ---
    budget = compute_budget(request.evidence_history)
```
to:
```python
    # --- Step 5: Budget computation ---
    # Note: match_templates() also calls compute_budget() internally for ranking.
    # This second call is intentional — the pipeline needs the budget object for
    # the TurnPacket response, and compute_budget() is a pure function (<1µs).
    budget = compute_budget(request.evidence_history)
```

**Step 8: Fix tracker stale text** (`progress.md:100`)

Change:
```
- Task 5: `types.py` part 3 — `ScoutSpec` union (Read/Grep/Ls/Stat), `ScoutOption`, `TurnPacket`, `ScoutResult` union (with callable discriminator). Uncomment `DedupRecord.model_validator`. Add 4 invariant tests for DedupRecord.
```
to:
```
- Task 5: `types.py` part 3 — `ScoutSpec` union (Read/Grep), `ScoutOption`, `TurnPacket`, `ScoutResult` union (with callable discriminator). Uncomment `DedupRecord.model_validator`. Add 4 invariant tests for DedupRecord.
```

**Step 9: Run full test suite and ruff**

Run: `cd packages/context-injection && uv run ruff check . && uv run ruff format --check . && uv run pytest tests/ -q`
Expected: 0 errors, 0 reformats, 215 passed

### Task 1.7: Commit

**Step 1: Stage and commit**

```bash
cd /Users/jp/Projects/active/claude-code-tool-dev
git add packages/context-injection/ docs/plans/2026-02-12-context-injection-v0a-progress.md
git commit -m "chore(context-injection): lint cleanup and documentation comments"
```

---

## Session 2: Test Improvements

**Goal:** Fill test coverage gaps, fix misleading test name, add missing assertions. No production code changes.

**Commit message:** `test(context-injection): fill coverage gaps and fix test naming`

### Task 2.1: Rename misleading test

**Files:**
- Modify: `tests/test_pipeline.py:62`

**Step 1: Rename the test**

Change:
```python
    def test_wrong_schema_version_returns_error(self) -> None:
        """Mismatched schema version → TurnPacketError with invalid_schema_version."""
```
to:
```python
    def test_correct_schema_version_succeeds(self) -> None:
        """Correct schema version → TurnPacketSuccess (guard against future version bumps)."""
```

The test actually passes `"0.1.0"` (the current valid version) and asserts `TurnPacketSuccess`. The name was inherited from intent (test wrong version) but the implementation tests the happy path because Pydantic's `Literal` validation prevents constructing a request with a wrong version.

**Step 2: Run the renamed test**

Run: `cd packages/context-injection && uv run pytest tests/test_pipeline.py::TestSchemaVersionValidation::test_correct_schema_version_succeeds -v`
Expected: PASSED

### Task 2.2: Add `test_schema_version_mismatch_via_model_construct`

**Files:**
- Modify: `tests/test_pipeline.py` (add after the renamed test)

**Step 1: Write the test**

Add after the renamed test:

```python
    def test_schema_version_mismatch_returns_error(self) -> None:
        """Bypassed Pydantic validation with wrong version → TurnPacketError."""
        ctx = _make_ctx()
        # Use model_construct to bypass Pydantic's Literal validation
        req = TurnRequest.model_construct(
            schema_version="99.0.0",
            turn_number=1,
            conversation_id="conv_test",
            focus=Focus(text="test", claims=[], unresolved=[]),
            context_claims=[],
            evidence_history=[],
            posture="exploratory",
        )
        result = process_turn(req, ctx)
        assert isinstance(result, TurnPacketError)
        assert result.error.code == "invalid_schema_version"
```

**Step 2: Run it**

Run: `cd packages/context-injection && uv run pytest tests/test_pipeline.py::TestSchemaVersionValidation -v`
Expected: 2 passed (renamed + new)

### Task 2.3: Add HMAC token length test

**Files:**
- Modify: `tests/test_state.py` (add to `TestTokenGeneration` class)

**Step 1: Write the test**

Add after `test_modified_payload_fails`:

```python
    def test_token_is_base64url_encoded(self) -> None:
        """Token is base64url-encoded, length matches TAG_LEN."""
        import base64
        from context_injection.state import TAG_LEN
        ctx = AppContext.create(repo_root="/tmp/repo")
        spec = _make_read_spec()
        payload = ScoutTokenPayload(
            v=1, conversation_id="conv_1", turn_number=1,
            scout_option_id="so_001", spec=spec,
        )
        token = generate_token(ctx.hmac_key, payload)
        # Decode should succeed (valid base64url)
        decoded = base64.urlsafe_b64decode(token)
        assert len(decoded) == TAG_LEN
```

**Step 2: Run it**

Run: `cd packages/context-injection && uv run pytest tests/test_state.py::TestTokenGeneration -v`
Expected: 4 passed

### Task 2.4: Add `normalize_input_path` default mode test

**Files:**
- Modify: `tests/test_paths.py` (add to `TestNormalizeInputPath` class)

**Step 1: Write the test**

Add after the existing `test_splits_github_anchor` test:

```python
    def test_default_mode_preserves_anchor_in_path(self) -> None:
        """Without split_anchor, colon anchor stays in the path string."""
        result = normalize_input_path("src/app.py:42")
        assert result == "src/app.py:42"
        assert isinstance(result, str)  # not a tuple

    def test_default_mode_preserves_github_anchor(self) -> None:
        """Without split_anchor, #L anchor stays in the path string."""
        result = normalize_input_path("src/app.py#L42")
        assert result == "src/app.py#L42"
        assert isinstance(result, str)
```

**Step 2: Run it**

Run: `cd packages/context-injection && uv run pytest tests/test_paths.py::TestNormalizeInputPath -v`
Expected: 6 passed (4 existing + 2 new)

### Task 2.5: Add `check_path_runtime` tests

**Files:**
- Modify: `tests/test_paths.py` (add new test class at end)

**Step 1: Add import**

Add `check_path_runtime` and `RuntimeResult` to the import at lines 5-9:

```python
from context_injection.paths import (
    CompileTimeResult,
    RuntimeResult,
    check_path_compile_time,
    check_path_runtime,
    is_risk_signal_path,
    normalize_input_path,
)
```

**Step 2: Write the test class**

Add at the end of `test_paths.py`:

```python
class TestCheckPathRuntime:
    """Tests for check_path_runtime() — Call 2 lightweight re-check."""

    def test_existing_file_allowed(self, tmp_path) -> None:
        """A regular file under repo_root is allowed."""
        f = tmp_path / "src" / "app.py"
        f.parent.mkdir(parents=True)
        f.write_text("print('hello')")
        result = check_path_runtime(str(f), repo_root=str(tmp_path))
        assert result.status == "allowed"
        assert result.resolved_abs is not None

    def test_nonexistent_file_not_found(self, tmp_path) -> None:
        """A non-existent path returns not_found."""
        result = check_path_runtime(
            str(tmp_path / "missing.py"), repo_root=str(tmp_path)
        )
        assert result.status == "not_found"

    def test_directory_not_found(self, tmp_path) -> None:
        """A directory (not a regular file) returns not_found."""
        d = tmp_path / "subdir"
        d.mkdir()
        result = check_path_runtime(str(d), repo_root=str(tmp_path))
        assert result.status == "not_found"

    def test_path_escaping_repo_root_denied(self, tmp_path) -> None:
        """A path outside repo_root is denied."""
        import os
        outside = tmp_path / ".." / "outside.py"
        # Create the file so it exists
        real_outside = tmp_path.parent / "outside.py"
        real_outside.write_text("secret")
        result = check_path_runtime(str(outside), repo_root=str(tmp_path))
        assert result.status == "denied"
        assert result.deny_reason is not None
        # Cleanup
        real_outside.unlink()

    def test_symlink_to_outside_denied(self, tmp_path) -> None:
        """A symlink pointing outside repo_root is denied."""
        import os
        outside = tmp_path.parent / "secret.txt"
        outside.write_text("secret")
        link = tmp_path / "link.txt"
        link.symlink_to(outside)
        result = check_path_runtime(str(link), repo_root=str(tmp_path))
        assert result.status == "denied"
        # Cleanup
        outside.unlink()
```

**Step 3: Run the new tests**

Run: `cd packages/context-injection && uv run pytest tests/test_paths.py::TestCheckPathRuntime -v`
Expected: 5 passed

### Task 2.6: Add golden vector independence test

**Files:**
- Modify: `tests/test_canonical.py` (add to `TestCanonicalJsonBytes`)

**Step 1: Write the test**

Add after `test_deterministic_output`:

```python
    def test_different_inputs_produce_different_bytes(self) -> None:
        """Different payloads produce different canonical bytes (independence)."""
        spec = ReadSpec(
            action="read", resolved_path="a.py", strategy="first_n",
            max_lines=40, max_chars=2000,
        )
        payload_a = ScoutTokenPayload(
            v=1, conversation_id="conv_a", turn_number=1,
            scout_option_id="so_001", spec=spec,
        )
        payload_b = ScoutTokenPayload(
            v=1, conversation_id="conv_b", turn_number=1,
            scout_option_id="so_001", spec=spec,
        )
        assert canonical_json_bytes(payload_a) != canonical_json_bytes(payload_b)
```

**Step 2: Run it**

Run: `cd packages/context-injection && uv run pytest tests/test_canonical.py::TestCanonicalJsonBytes -v`
Expected: 5 passed

### Task 2.7: Run full suite, ruff, commit

**Step 1: Verify**

Run: `cd packages/context-injection && uv run ruff check . && uv run ruff format --check . && uv run pytest tests/ -q`
Expected: 0 errors, 0 reformats, 224 passed (215 + 1 pipeline + 1 state + 2 paths + 5 runtime + 1 canonical = ~225)

**Step 2: Commit**

```bash
cd /Users/jp/Projects/active/claude-code-tool-dev
git add packages/context-injection/tests/
git commit -m "test(context-injection): fill coverage gaps and fix test naming"
```

---

## Session 3: Entity Extraction Refinements

**Goal:** Refine edge-case handling in `entities.py` — confidence, traversal, URL schemes, Unicode. Document `_overlaps` algorithm choice.

**Commit message:** `fix(context-injection): entity extraction edge-case refinements`

### Task 3.1: Recognize double-backtick as high confidence

**Files:**
- Modify: `context_injection/entities.py:258-280`
- Modify: `tests/test_entities.py` (add test)

**Step 1: Write the failing test**

Add to the appropriate test class in `test_entities.py`:

```python
def test_double_backtick_entity_gets_high_confidence(self) -> None:
    """Entity within double backticks gets high confidence."""
    ctx = AppContext.create(repo_root="/tmp/repo", git_files=set())
    entities = extract_entities(
        "Check ``src/config.yaml`` for settings",
        source_type="claim",
        in_focus=True,
        ctx=ctx,
    )
    file_entities = [e for e in entities if e.canonical == "src/config.yaml"]
    assert len(file_entities) == 1
    assert file_entities[0].confidence == "high"
```

**Step 2: Run test to verify it fails**

Run: `cd packages/context-injection && uv run pytest tests/test_entities.py -k "double_backtick" -v`
Expected: FAIL — double backtick not recognized, entity gets "medium"

**Step 3: Fix `_find_backtick_spans` to handle double backticks**

The current implementation at line 268 checks `text[i] == "`"` and finds the next single backtick. For double backticks (` `` `), it would match `` ` `` to `` ` `` getting an empty string, which is skipped.

Change `_find_backtick_spans` (lines 258-280) to:

```python
def _find_backtick_spans(text: str) -> list[tuple[int, int, str]]:
    """Find all backtick-delimited spans in text.

    Supports both single (`) and double (``) backtick delimiters.
    Returns list of (content_start, content_end, content) tuples.
    content_start/end are indices into the original text of the content
    (not including the backticks themselves).
    """
    spans: list[tuple[int, int, str]] = []
    i = 0
    while i < len(text):
        if text[i] == "`":
            # Count consecutive backticks to determine delimiter width
            width = 1
            while i + width < len(text) and text[i + width] == "`":
                width += 1
            delimiter = "`" * width
            # Find matching closing delimiter
            content_start = i + width
            close_idx = text.find(delimiter, content_start)
            if close_idx != -1:
                content = text[content_start:close_idx]
                if content.strip():  # Skip empty/whitespace-only
                    spans.append((content_start, close_idx, content.strip()))
                i = close_idx + width
            else:
                i += width  # No closing delimiter found, skip
        else:
            i += 1
    return spans
```

**Step 4: Run test to verify it passes**

Run: `cd packages/context-injection && uv run pytest tests/test_entities.py -k "double_backtick" -v`
Expected: PASSED

**Step 5: Run full entity tests to check for regressions**

Run: `cd packages/context-injection && uv run pytest tests/test_entities.py -q`
Expected: 60 passed (59 + 1 new)

### Task 3.2: More precise traversal detection

**Files:**
- Modify: `context_injection/entities.py:351-355`
- Modify: `tests/test_entities.py` (add test)

The current check `if ".." in raw` is overly broad — it matches `..` anywhere in the string, including filenames like `something..else`. The intent is to reject directory traversal patterns like `../` or `/..`.

**Step 1: Write the failing test**

```python
def test_filename_with_double_dots_not_rejected(self) -> None:
    """A file like 'utils..helpers.py' should not be rejected as traversal."""
    ctx = AppContext.create(repo_root="/tmp/repo", git_files=set())
    entities = extract_entities(
        "Check `src/utils..helpers.py` for the fix",
        source_type="claim",
        in_focus=True,
        ctx=ctx,
    )
    file_entities = [e for e in entities if "utils..helpers" in e.raw]
    assert len(file_entities) == 1
```

**Step 2: Run test to verify it fails**

Run: `cd packages/context-injection && uv run pytest tests/test_entities.py -k "double_dots_not_rejected" -v`
Expected: FAIL — current `".." in raw` rejects it

**Step 3: Fix the traversal check**

Change `_extract_file_paths` lines 351-355 from:
```python
        # Skip traversal paths — they always fail downstream path checking.
        # Claim the span so downstream extractors don't match substrings.
        if ".." in raw:
            spans.append((start, end))
            continue
```
to:
```python
        # Skip traversal paths (../ or /.. segments) — they always fail
        # downstream path checking. Claim the span so downstream extractors
        # don't match substrings. Uses path-segment check, not substring
        # match, to avoid rejecting filenames with consecutive dots.
        parts = raw.split("/")
        if ".." in parts:
            spans.append((start, end))
            continue
```

This matches `normalize_input_path`'s own traversal check (paths.py:171-175) which also uses `parts = path.split("/"); if ".." in parts`.

**Step 4: Run test**

Run: `cd packages/context-injection && uv run pytest tests/test_entities.py -k "double_dots" -v`
Expected: PASSED

**Step 5: Verify existing traversal tests still pass**

Run: `cd packages/context-injection && uv run pytest tests/test_entities.py -q`
Expected: All pass (existing traversal rejection tests use `../../etc/passwd` which has `..` as a path segment)

### Task 3.3: Document `ftp://` URL scheme exclusion

**Files:**
- Modify: `context_injection/entities.py:124-127`

This is a **document, don't fix** item. FTP URLs are rare in claim text, and adding `ftp://` extraction would need path-checking decisions (FTP paths aren't local files). Document the intentional exclusion.

**Step 1: Add comment**

Change:
```python
# URL: starts with http:// or https://
_URL_RE = re.compile(
    r"https?://[^\s`\"\')>\]]+",
)
```
to:
```python
# URL: HTTP/HTTPS only. FTP, SSH, and other schemes are intentionally excluded —
# they aren't local file references and would need scheme-specific path handling.
_URL_RE = re.compile(
    r"https?://[^\s`\"\')>\]]+",
)
```

### Task 3.4: Document Unicode NFC timing

**Files:**
- Modify: `context_injection/entities.py:449-454`

This is a **document, don't fix** item. Pre-normalizing text before regex matching would change span indices and break backtick detection. The risk (NFD combining characters spanning regex boundaries) is theoretical — NFC is the dominant encoding in source code. Document the accepted risk.

**Step 1: Add comment**

Change:
```python
    # Cap input length to bound worst-case regex execution (ReDoS mitigation)
    if len(text) > MAX_TEXT_LEN:
        text = text[:MAX_TEXT_LEN]

    # Pre-compute backtick spans for confidence detection
    bt_spans = _find_backtick_spans(text)
```
to:
```python
    # Cap input length to bound worst-case regex execution (ReDoS mitigation)
    if len(text) > MAX_TEXT_LEN:
        text = text[:MAX_TEXT_LEN]

    # Note: text is NOT NFC-normalized before regex matching. Normalizing here
    # would shift character positions and break span tracking. Instead, canon()
    # normalizes per-entity after extraction. NFD combining characters spanning
    # regex boundaries are theoretically possible but not observed in practice.

    # Pre-compute backtick spans for confidence detection
    bt_spans = _find_backtick_spans(text)
```

### Task 3.5: Document `_overlaps` algorithm choice

**Files:**
- Modify: `context_injection/entities.py:247-252`

**Step 1: Add comment**

Change:
```python
def _overlaps(spans: list[tuple[int, int]], start: int, end: int) -> bool:
    """Check if (start, end) overlaps with any existing span."""
```
to:
```python
def _overlaps(spans: list[tuple[int, int]], start: int, end: int) -> bool:
    """Check if (start, end) overlaps with any existing span.

    O(n) scan per call, O(n²) total for n entities. Acceptable for MVP —
    MAX_TEXT_LEN=2000 bounds entity count to ~20 in practice.
    """
```

### Task 3.6: Run full suite, ruff, commit

**Step 1: Verify**

Run: `cd packages/context-injection && uv run ruff check . && uv run ruff format --check . && uv run pytest tests/ -q`
Expected: 0 errors, ~227 passed

**Step 2: Commit**

```bash
cd /Users/jp/Projects/active/claude-code-tool-dev
git add packages/context-injection/
git commit -m "fix(context-injection): entity extraction edge-case refinements"
```

---

## Session 4: Cross-Cutting Fixes + Close S7

**Goal:** Address remaining items across canonical, types, server, and paths. Update progress tracker. Mark S7 complete.

**Commit message:** `chore(context-injection): cross-cutting type fixes and S7 completion`

### Task 4.1: Add `parse_entity_key` input validation

**Files:**
- Modify: `context_injection/canonical.py:69-75`
- Modify: `tests/test_canonical.py` (add test)

**Step 1: Write the failing test**

Add to `TestEntityKey` class:

```python
    def test_parse_empty_string_raises(self) -> None:
        """Empty string input raises ValueError."""
        with pytest.raises(ValueError, match="empty"):
            parse_entity_key("")

    def test_parse_no_colon_raises(self) -> None:
        """String without colon raises ValueError."""
        with pytest.raises(ValueError, match="no colon"):
            parse_entity_key("file_path_only")
```

Note: `pytest` was removed by ruff autofix in Session 1. Re-add the import:
```python
import pytest
```

**Step 2: Run tests to verify they fail**

Run: `cd packages/context-injection && uv run pytest tests/test_canonical.py::TestEntityKey -v`
Expected: 2 new tests FAIL

**Step 3: Add validation**

Change `parse_entity_key` from:
```python
def parse_entity_key(key: str) -> tuple[str, str]:
    """Parse entity key back to (entity_type, canonical_form).

    Handles values containing colons (e.g., file_loc:config.py:42).
    """
    entity_type, _, canonical_form = key.partition(":")
    return entity_type, canonical_form
```
to:
```python
def parse_entity_key(key: str) -> tuple[str, str]:
    """Parse entity key back to (entity_type, canonical_form).

    Handles values containing colons (e.g., file_loc:config.py:42).

    Raises:
        ValueError: If key is empty or contains no colon separator.
    """
    if not key:
        raise ValueError("parse_entity_key failed: empty key")
    entity_type, sep, canonical_form = key.partition(":")
    if not sep:
        raise ValueError(
            f"parse_entity_key failed: no colon separator. Got: {key!r:.100}"
        )
    return entity_type, canonical_form
```

**Step 4: Run tests**

Run: `cd packages/context-injection && uv run pytest tests/test_canonical.py -v`
Expected: All pass

### Task 4.2: Add `Context[AppContext]` type parameter

**Files:**
- Modify: `context_injection/server.py:57`

**Step 1: Change the type annotation**

Change:
```python
    @mcp.tool()
    def process_turn_tool(
        request: TurnRequest,
        ctx: Context,
    ) -> dict:
```
to:
```python
    @mcp.tool()
    def process_turn_tool(
        request: TurnRequest,
        ctx: Context[AppContext],
    ) -> dict:
```

This gives IDE type-checking for `ctx.request_context.lifespan_context`.

**Step 2: Run tests**

Run: `cd packages/context-injection && uv run pytest tests/test_server.py -v`
Expected: 4 passed

### Task 4.3: Extract `scout_options` type alias

**Files:**
- Modify: `context_injection/state.py:37`
- Modify: `context_injection/templates.py` (if it references the same type)

**Step 1: Check current usages**

The type `dict[str, tuple[ReadSpec | GrepSpec, str]]` appears in:
- `state.py:37` — `TurnRequestRecord.scout_options`
- `templates.py` — as the return type in `match_templates`

Search for the pattern to confirm all locations before creating the alias.

**Step 2: Add type alias to `state.py`**

Add after the `TAG_LEN` definition (line 29):

```python
ScoutOptionRegistry = dict[str, tuple[ReadSpec | GrepSpec, str]]
"""scout_option_id -> (frozen ScoutSpec, HMAC token). Atomic pairs for Call 2."""
```

**Step 3: Update `TurnRequestRecord`**

Change:
```python
    scout_options: dict[str, tuple[ReadSpec | GrepSpec, str]]
    """scout_option_id -> (frozen ScoutSpec, HMAC token) -- atomic pairs."""
```
to:
```python
    scout_options: ScoutOptionRegistry
```

**Step 4: Update `templates.py` if it uses the same type**

Search `templates.py` for the matching type signature. If found, import and use `ScoutOptionRegistry`.

**Step 5: Run tests**

Run: `cd packages/context-injection && uv run pytest tests/ -q`
Expected: All pass

### Task 4.4: Document architectural observations

**Files:**
- Modify: `context_injection/paths.py:76-84` (CompileTimeResult ↔ PathDecision)
- Add comment to `context_injection/paths.py:365-407` (TOCTOU)

**Step 1: Add CompileTimeResult → PathDecision alignment note**

This was partially done in Session 1 (cross-reference comment). Verify the comment from Task 1.6 Step 2 is present. If so, this item is complete.

**Step 2: Add TOCTOU accepted-risk comment to `check_path_runtime`**

Change:
```python
def check_path_runtime(
    resolved_path: str,
    *,
    repo_root: str,
) -> RuntimeResult:
    """Lightweight runtime path check for Call 2 (ScoutResult execution).

    Checks:
    1. Realpath resolution (follows symlinks)
    2. Containment under repo_root
    3. Regular file existence

    This re-validates at execution time. The compile-time check already
    verified denylist and git tracking; runtime re-checks containment
    and file existence (which may have changed between Call 1 and Call 2).
    """
```
to:
```python
def check_path_runtime(
    resolved_path: str,
    *,
    repo_root: str,
) -> RuntimeResult:
    """Lightweight runtime path check for Call 2 (ScoutResult execution).

    Checks:
    1. Realpath resolution (follows symlinks)
    2. Containment under repo_root
    3. Regular file existence

    This re-validates at execution time. The compile-time check already
    verified denylist and git tracking; runtime re-checks containment
    and file existence (which may have changed between Call 1 and Call 2).

    TOCTOU note: A symlink could be swapped between this check and the
    subsequent file read. Accepted for v0a — the agent is the consumer,
    and the denylist re-check at Call 2 time provides defense in depth.
    """
```

### Task 4.5: Update progress tracker and close S7

**Files:**
- Modify: `docs/plans/2026-02-12-context-injection-v0a-progress.md`

**Step 1: Update Task 14 status**

Change:
```
| 14 | Cleanup | Pending | — | Lint, type-check, final polish |
```
to:
```
| 14 | Cleanup | Complete | 225+ pass | 4-session split: lint, tests, entities, cross-cutting |
```

**Step 2: Update S7 session status**

Change the S7 row from "In Progress" to "Complete" in the Session Schedule section.

**Step 3: Verify all S7 exit criteria**

Run through the checklist at lines 293-301:
- [x] SDK smoke test passes
- [x] Server starts and accepts MCP tool calls
- [x] Integration test: realistic TurnRequest → valid TurnPacket
- [x] `ruff check` and `ruff format` pass with zero issues
- [x] `uv run pytest tests/ -v` — all pass
- [x] No `TODO` or `FIXME` in production code
- [x] All Open Issues reviewed
- [x] One commit per task (Tasks 12, 13, 14 each have commits)

### Task 4.6: Run full suite, ruff, commit

**Step 1: Verify clean state**

Run: `cd packages/context-injection && uv run ruff check . && uv run ruff format --check . && uv run pytest tests/ -v`
Expected: 0 errors, 0 reformats, ~227+ passed

**Step 2: Check no TODO/FIXME in production code**

Run: `cd packages/context-injection && grep -rn "TODO\|FIXME" context_injection/ || echo "Clean"`
Expected: "Clean"

**Step 3: Commit**

```bash
cd /Users/jp/Projects/active/claude-code-tool-dev
git add packages/context-injection/ docs/plans/
git commit -m "chore(context-injection): cross-cutting type fixes and S7 completion"
```

---

## Verification Checklist (After All 4 Sessions)

| Check | Expected |
|-------|----------|
| `ruff check .` | 0 errors |
| `ruff format --check .` | 0 files to reformat |
| `pytest tests/ -v` | 225+ passed, 0 failed |
| `grep -rn "TODO\|FIXME" context_injection/` | No matches |
| Progress tracker S7 status | Complete |
| Progress tracker Task 14 status | Complete |

## Item Cross-Reference

Every deferred item mapped to its session and task:

| # | Item | Session.Task |
|---|------|-------------|
| 1 | Unused enum imports (types.py) | 1.1 |
| 2 | Unused ScoutSpec import (canonical.py) | 1.1 |
| 3 | Unused pytest import (test_canonical.py) | 1.1 |
| 4 | Unused pytest import (test_enums.py) | 1.1 |
| 5 | Dead EntityTypeLiteral alias (entities.py) | 1.1 |
| 6 | field(default=None) inconsistency (paths.py) | 1.2 |
| 7 | Redundant case-handling (paths.py) | 1.3 |
| 8 | object type in test helper (test_pipeline.py) | 1.4 |
| 9 | Unused repo_root parameter (server.py) | 1.5 |
| 10 | next_entity_id() docstring (state.py) | 1.6 |
| 11 | CompileTimeResult cross-reference (paths.py) | 1.6 |
| 12 | _is_denied_dir algorithm comment (paths.py) | 1.6 |
| 13 | Denylist dual-pattern comment (paths.py) | 1.6 |
| 14 | model_dump rationale comment (server.py) | 1.6 |
| 15 | _tool_manager private API comment (test_server.py) | 1.6 |
| 16 | Redundant compute_budget comment (pipeline.py) | 1.6 |
| 17 | Tracker stale text (progress.md) | 1.6 |
| 18 | Rename misleading test (test_pipeline.py) | 2.1 |
| 19 | Add schema mismatch test via model_construct | 2.2 |
| 20 | Token length test (test_state.py) | 2.3 |
| 21 | normalize_input_path default mode test | 2.4 |
| 22 | check_path_runtime tests | 2.5 |
| 23 | Golden vector independence test | 2.6 |
| 24 | Double-backtick confidence (entities.py) | 3.1 |
| 25 | Traversal detection precision (entities.py) | 3.2 |
| 26 | ftp:// URL scheme documentation (entities.py) | 3.3 |
| 27 | Unicode NFC timing documentation (entities.py) | 3.4 |
| 28 | _overlaps algorithm documentation (entities.py) | 3.5 |
| 29 | parse_entity_key validation (canonical.py) | 4.1 |
| 30 | Context[AppContext] type parameter (server.py) | 4.2 |
| 31 | scout_options type alias (state.py) | 4.3 |
| 32 | CompileTimeResult ↔ PathDecision alignment | 4.4 |
| 33 | TOCTOU symlink documentation (paths.py) | 4.4 |
| 34 | Update progress tracker, close S7 | 4.5 |
