# PR #7 Review Findings Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Address the 4 important findings from the multi-agent PR #7 review — fix vestigial docstring, guard anchor-only empty paths, add pipeline integration tests.

**Architecture:** All changes are on existing branch `fix/context-injection-p1-findings`. Two production file edits (docstring + guard), one test file expansion. Each task is a single commit.

**Tech Stack:** Python 3.14, pytest, posixpath, fnmatch

---

### Task 1: Fix vestigial DENYLIST_DIRS docstring and normalize_input_path step 8

**Files:**
- Modify: `packages/context-injection/context_injection/paths.py:42-44` (denylist docstring)
- Modify: `packages/context-injection/context_injection/paths.py:164` (step 8 docstring)

**Why:** The DENYLIST_DIRS warning explains why slash patterns fail using the *old* code's accumulated-prefix matching logic. The new per-component matching never presents a slash to fnmatch — different mechanism, same conclusion. Step 8 omits the post-normpath re-validation sub-steps.

**Step 1: Fix DENYLIST_DIRS docstring**

Replace lines 42-44 in `paths.py`:

```python
# OLD (vestigial — describes accumulated-prefix matching from old code):
Do NOT add slash-containing patterns (e.g., `name/*`). They silently fail for
paths where the denied directory appears at depth > 0, because fnmatch compares
against the full accumulated prefix which includes parent segments.

# NEW (describes current per-component matching):
Do NOT add slash-containing patterns (e.g., `name/*`). Per-component matching
splits on `/` before calling fnmatch, so no component ever contains a slash.
Patterns like `name/*` would never match any individual component.
```

**Step 2: Update step 8 in normalize_input_path docstring**

Replace line 164 in `paths.py`:

```python
# OLD:
    8. Canonicalize: collapse //, remove . segments, strip trailing /

# NEW:
    8. Canonicalize: collapse //, remove . segments, strip trailing /
       Post-normpath re-validation rejects any `..` reintroduced by normpath
       and bare `.` (from inputs like `./` or `.`).
```

**Step 3: Run tests to verify no regressions**

Run: `uv run pytest packages/context-injection/tests/test_paths.py -v`
Expected: All 73 tests PASS (docstring-only changes, no behavioral change)

**Step 4: Commit**

```bash
git add packages/context-injection/context_injection/paths.py
git commit -m "docs(context-injection): fix vestigial denylist docstring and expand step 8"
```

---

### Task 2: Guard anchor-only empty path in normalize_input_path

**Files:**
- Modify: `packages/context-injection/context_injection/paths.py:225-226`
- Test: `packages/context-injection/tests/test_paths.py`

**Why:** `normalize_input_path(":42", split_anchor=True)` returns `("", 42)` — an empty path string. Not reachable from the current pipeline (`check_path_compile_time` uses `split_anchor=False`) but is a latent bug in the public API. `os.path.join(repo_root, "")` produces just `repo_root`, which could cause unexpected behavior.

**Step 1: Write the failing tests**

Add to `test_paths.py` after `TestNormalizeInputPathCanonicalization`:

```python
class TestNormalizeInputPathAnchorOnly:
    """Anchor-only inputs must be rejected when split_anchor=True."""

    def test_rejects_colon_anchor_only(self) -> None:
        """':42' has no path component — should raise, not return ('', 42)."""
        with pytest.raises(ValueError, match="empty path"):
            normalize_input_path(":42", split_anchor=True)

    def test_rejects_github_anchor_only(self) -> None:
        """'#L42' has no path component — should raise, not return ('', 42)."""
        with pytest.raises(ValueError, match="empty path"):
            normalize_input_path("#L42", split_anchor=True)

    def test_rejects_dot_slash_anchor(self) -> None:
        """./:42 normalizes to '.' then anchor splits to '' — should raise."""
        with pytest.raises(ValueError, match="empty"):
            normalize_input_path("./:42", split_anchor=True)
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest packages/context-injection/tests/test_paths.py::TestNormalizeInputPathAnchorOnly -v`
Expected: FAIL — `test_rejects_colon_anchor_only` returns `("", 42)` instead of raising. `test_rejects_dot_slash_anchor` raises for a different reason (bare `.` rejection catches it before anchor split) — that test may pass already.

**Step 3: Write minimal implementation**

In `paths.py`, add empty-path check after anchor splitting. Replace lines 225-229:

```python
    # Split anchor if requested
    line: int | None = None
    if split_anchor:
        path, line = _split_anchor(path)
        if not path:
            raise ValueError(
                f"normalize_input_path failed: empty path after anchor split. Got: {raw!r:.100}"
            )
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest packages/context-injection/tests/test_paths.py -v`
Expected: All tests PASS (73 existing + 3 new = 76, or 75 if `./:42` was already caught)

Note: Check whether `test_rejects_dot_slash_anchor` is caught by the bare `.` guard (line 220) before reaching the anchor split. If `./:42` → normpath → `.:42` → not bare `.` → anchor split → `("", 42)`, then the new guard catches it. If normpath strips the `/` making it `.:42` which doesn't match `path == "."`, then the anchor split guard catches it. Either way, the test should pass after the fix.

**Step 5: Commit**

```bash
git add packages/context-injection/context_injection/paths.py packages/context-injection/tests/test_paths.py
git commit -m "fix(context-injection): guard empty path after anchor split"
```

---

### Task 3: Add pipeline integration tests for normpath + denylist

**Files:**
- Test: `packages/context-injection/tests/test_paths.py`

**Why:** No tests verify that non-canonical inputs to `check_path_compile_time` are still denied after normalization. A pipeline reordering (normpath after denylist, or normpath removing denylist-relevant components) would break the security contract silently. Also missing: negative tests for directory denylist entries, trailing dot segment canonicalization.

**Step 1: Write the tests**

Add to `test_paths.py` after `TestDenylistOnResolvedPath`:

```python
class TestDenylistAfterNormpath:
    """Pipeline integration: non-canonical inputs must still hit denylist after normpath."""

    def test_dot_slash_git_denied(self) -> None:
        """./.git/config normalizes to .git/config — still denied."""
        result = check_path_compile_time(
            "./.git/config",
            repo_root="/tmp/repo",
            git_files={".git/config"},
        )
        assert result.status == "denied"
        assert ".git" in (result.deny_reason or "")

    def test_double_slash_git_denied(self) -> None:
        """.git//config normalizes to .git/config — still denied."""
        result = check_path_compile_time(
            ".git//config",
            repo_root="/tmp/repo",
            git_files={".git/config"},
        )
        assert result.status == "denied"
        assert ".git" in (result.deny_reason or "")

    def test_dot_segments_in_denied_path(self) -> None:
        """src/./node_modules/./lodash/index.js normalizes — node_modules still denied."""
        result = check_path_compile_time(
            "src/./node_modules/./lodash/index.js",
            repo_root="/tmp/repo",
            git_files={"src/node_modules/lodash/index.js"},
        )
        assert result.status == "denied"
        assert "node_modules" in (result.deny_reason or "")

    def test_trailing_slash_on_denied_component(self) -> None:
        """.aws/credentials/ (trailing slash) normalizes — .aws still denied."""
        result = check_path_compile_time(
            ".aws/credentials/",
            repo_root="/tmp/repo",
            git_files={".aws/credentials"},
        )
        assert result.status == "denied"
        assert ".aws" in (result.deny_reason or "")


class TestDenylistNegativeCases:
    """Verify paths that look similar to denylist entries are NOT denied."""

    @pytest.mark.parametrize(
        ("path", "description"),
        [
            ("terraform/main.tf", "terraform (no dot) != .terraform"),
            ("aws-sdk/lib.py", "aws-sdk != .aws"),
            ("docker-compose.yml", "docker-compose != .docker"),
            ("kube-system/config.yaml", "kube-system != .kube"),
            ("gnupg-utils/helper.py", "gnupg-utils != .gnupg"),
        ],
    )
    def test_similar_names_not_denied(self, path: str, description: str) -> None:
        result = check_path_compile_time(
            path,
            repo_root="/tmp/repo",
            git_files={path},
        )
        assert result.status == "allowed", f"False positive: {description}"
```

**Step 2: Add trailing dot segment canonicalization test**

Add to `TestNormalizeInputPathCanonicalization`:

```python
    def test_trailing_dot_segment(self) -> None:
        """a/b/c/. normalizes to a/b/c via posixpath.normpath."""
        assert normalize_input_path("a/b/c/.") == "a/b/c"

    def test_dot_slash_only_rejected(self) -> None:
        """./ normalizes to . — rejected as bare directory."""
        with pytest.raises(ValueError, match="empty"):
            normalize_input_path("./")
```

**Step 3: Run tests to verify they all pass**

Run: `uv run pytest packages/context-injection/tests/test_paths.py -v`
Expected: All tests PASS. These are new tests for existing behavior — they should pass without code changes.

If any test fails, investigate: the failure reveals a bug or incorrect assumption in the test design.

**Step 4: Commit**

```bash
git add packages/context-injection/tests/test_paths.py
git commit -m "test(context-injection): add pipeline integration and negative denylist tests"
```

---

## Verification

After all 3 tasks:

```bash
uv run pytest packages/context-injection/tests/test_paths.py -v
# Expected: ~86 tests pass (73 + 3 anchor + 4 pipeline + 5 negative + 2 canonicalization = 87, minus any that overlap)

uv run ruff check packages/context-injection/
uv run ruff format --check packages/context-injection/
# Expected: clean
```
