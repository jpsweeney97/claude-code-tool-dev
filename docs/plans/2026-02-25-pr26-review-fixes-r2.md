# PR #26 Review Fixes (Round 2) Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Address 8 findings (5 important, 3 test gaps) from the 4-agent PR review of PR #26.

**Architecture:** 4 tasks — 2 Python (code + tests), 2 markdown (comments + skills). No behavioral dependencies. File coupling: `test_cleanup.py` (Tasks 1+2 both add content — sequence 1→2). Tasks 3 and 4 can run in parallel with either.

**Tech Stack:** Python 3.12, pytest, ruff. Markdown skill files. Tests run from `packages/plugins/handoff/`.

**Finding map:**

| ID | Source | Description | Task |
|----|--------|-------------|------|
| I1 | code-reviewer | Unused `import pytest` fails ruff | 1 |
| I2 | error-handler | `get_project_name()` missing `OSError` catch | 1 |
| I3 | comment-analyzer | Skills omit "warn user" on trash failure | 4 |
| I4 | comment-analyzer | `main()` docstring misleading about KeyboardInterrupt | 3 |
| I5 | comment-analyzer | Resume skill Background Cleanup omits state file pruning | 4 |
| T1 | test-analyzer | `get_handoffs_dir()` untested | 2 |
| T2 | test-analyzer | `prune_old_state_files` stat OSError untested | 2 |
| T3 | test-analyzer | `prune_old_state_files` default `state_dir` untested | 2 |

---

### Task 1: Fix lint + harden `get_project_name()` (I1, I2)

**Files:**
- Modify: `packages/plugins/handoff/tests/test_cleanup.py:9` (remove unused import)
- Modify: `packages/plugins/handoff/scripts/cleanup.py:57-60` (add OSError catch)
- Modify: `packages/plugins/handoff/tests/test_cleanup.py` (add OSError test)

**Step 1: Remove unused `import pytest` (I1)**

In `tests/test_cleanup.py`, delete line 9:

```python
# DELETE this line:
import pytest
```

**Step 2: Run ruff to verify lint passes**

Run: `cd packages/plugins/handoff && uv run ruff check tests/test_cleanup.py`
Expected: No errors

**Step 3: Write failing test for I2 — `get_project_name()` OSError**

Add to `TestGetProjectName` in `tests/test_cleanup.py`:

```python
    def test_git_oserror_falls_back(self) -> None:
        """I2: PermissionError on git binary must not escape to main()."""
        with patch(
            "scripts.cleanup.subprocess.run",
            side_effect=PermissionError("not executable"),
        ):
            assert get_project_name() == Path.cwd().name
```

**Step 4: Run test to verify it fails (without the fix)**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_cleanup.py::TestGetProjectName::test_git_oserror_falls_back -v`
Expected: FAIL — `PermissionError: not executable` escapes unhandled

**Step 5: Fix `get_project_name()` — add OSError to except clause**

In `cleanup.py`, replace lines 57-60:

```python
    except subprocess.TimeoutExpired:
        pass  # Git hanging (disk issue, corrupted repo). Fall back to cwd.
    except FileNotFoundError:
        pass  # Git binary not installed. Fall back to cwd.
```

With:

```python
    except subprocess.TimeoutExpired:
        pass  # Git hanging (disk issue, corrupted repo). Fall back to cwd.
    except FileNotFoundError:
        pass  # Git binary not installed. Fall back to cwd.
    except OSError:
        pass  # PermissionError or other OS-level issue. Fall back to cwd.
```

**Step 6: Run all tests to verify pass**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_cleanup.py -v`
Expected: 23/23 pass (22 existing + 1 new)

**Step 7: Commit**

```
fix(handoff): remove unused pytest import, add OSError catch to get_project_name (I1+I2)
```

---

### Task 2: Close test coverage gaps (T1, T2, T3)

**Files:**
- Modify: `packages/plugins/handoff/tests/test_cleanup.py` (3 new tests)

**Step 1: Write test for `get_handoffs_dir()` path composition (T1)**

Add new test class after `TestGetProjectName`:

```python
class TestGetHandoffsDir:
    """Tests for get_handoffs_dir path composition."""

    def test_composes_path_from_project_name(self) -> None:
        """T1: Verify path composition logic — ~/.claude/handoffs/<project>/."""
        with patch("scripts.cleanup.get_project_name", return_value="my-project"):
            result = get_handoffs_dir()
        assert result == Path.home() / ".claude" / "handoffs" / "my-project"
```

Add `get_handoffs_dir` to the import block:

```python
from scripts.cleanup import (
    _trash,
    get_handoffs_dir,
    get_project_name,
    main,
    prune_old_handoffs,
    prune_old_state_files,
)
```

**Step 2: Write test for `prune_old_state_files` stat OSError (T2)**

Add to `TestPruneOldStateFiles`:

```python
    def test_stat_oserror_skipped(self, tmp_path: Path) -> None:
        """T2: stat() failure on individual state files doesn't crash the function."""
        state_dir = tmp_path / "session-state"
        state_dir.mkdir()
        target = state_dir / "handoff-abc123"
        target.write_text("content")
        target_str = str(target)

        orig_stat = Path.stat
        hit = False

        def selective_stat(self_path: Path, *args: object, **kwargs: object) -> os.stat_result:
            nonlocal hit
            if str(self_path) == target_str:
                hit = True
                raise OSError("permission denied")
            return orig_stat(self_path, *args, **kwargs)

        with patch("scripts.cleanup.Path.stat", autospec=True, side_effect=selective_stat):
            result = prune_old_state_files(max_age_hours=24, state_dir=state_dir)
        assert hit is True, "Patch must exercise the target file's stat() path"
        assert result == []
```

**Step 3: Write test for `prune_old_state_files` default state_dir (T3)**

Add to `TestPruneOldStateFiles`:

```python
    def test_default_state_dir_uses_home(self, tmp_path: Path) -> None:
        """T3: When state_dir is None, resolves to ~/.claude/.session-state."""
        fake_home = tmp_path / "fakehome"
        state_dir = fake_home / ".claude" / ".session-state"
        state_dir.mkdir(parents=True)
        old = state_dir / "handoff-abc123"
        old.write_text("content")
        old_time = time.time() - (25 * 60 * 60)
        os.utime(old, (old_time, old_time))
        with (
            patch("scripts.cleanup.Path.home", return_value=fake_home),
            patch("scripts.cleanup._trash", return_value=True) as mock_trash,
        ):
            result = prune_old_state_files(max_age_hours=24)
        assert result == [old]
        mock_trash.assert_called_once_with(old)
```

Note: This test creates a real directory structure under `tmp_path` so the function exercises the full default-path resolution AND pruning logic, not just the `exists()` guard.

**Step 4: Run all tests**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_cleanup.py -v`
Expected: 26/26 pass (23 from Task 1 + 3 new)

**Step 5: Commit**

```
test(handoff): add coverage for get_handoffs_dir, state_files stat OSError, default state_dir (T1+T2+T3)
```

---

### Task 3: Fix comment and docstring accuracy in cleanup.py (I4)

**Files:**
- Modify: `packages/plugins/handoff/scripts/cleanup.py` (docstring + comments)

**Step 1: Fix `main()` docstring (I4)**

In `cleanup.py`, replace lines 115-118:

```python
    Returns:
        0 on best-effort completion. A SessionStart hook must never block
        session start. Returns 0 unless process-level termination (e.g.
        SIGKILL, KeyboardInterrupt) interrupts execution.
```

With:

```python
    Returns:
        0 on best-effort completion. A SessionStart hook must never block
        session start. Only BaseException subclasses (e.g., KeyboardInterrupt,
        SystemExit) propagate — these indicate process-level termination.
```

**Step 2: Run tests to confirm no breakage**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_cleanup.py -v`
Expected: All pass (docstring change only)

**Step 3: Commit**

```
docs(handoff): fix main() docstring accuracy about BaseException propagation (I4)
```

---

### Task 4: Fix skill markdown accuracy (I3, I5)

**Files:**
- Modify: `packages/plugins/handoff/skills/checkpointing/SKILL.md:63-64`
- Modify: `packages/plugins/handoff/skills/creating-handoffs/SKILL.md:152-153`
- Modify: `packages/plugins/handoff/skills/resuming-handoffs/SKILL.md:154-158`

**Step 1: Add trash-failure warning to checkpointing skill (I3)**

In `checkpointing/SKILL.md`, replace line 64:

```markdown
   - `trash` the state file at `~/.claude/.session-state/handoff-<session_id>` if it exists
```

With:

```markdown
   - `trash` the state file at `~/.claude/.session-state/handoff-<session_id>` if it exists. If `trash` fails, warn the user that the state file persists but do not block — the 24-hour TTL will clean it up.
```

**Step 2: Add trash-failure warning to creating-handoffs skill (I3)**

In `creating-handoffs/SKILL.md`, replace line 153:

```markdown
   - `trash` the state file at `~/.claude/.session-state/handoff-<session_id>` if it exists
```

With:

```markdown
   - `trash` the state file at `~/.claude/.session-state/handoff-<session_id>` if it exists. If `trash` fails, warn the user that the state file persists but do not block — the 24-hour TTL will clean it up.
```

**Step 3: Add state file pruning to resume skill Background Cleanup (I5)**

In `resuming-handoffs/SKILL.md`, replace lines 154-158:

```markdown
The plugin's SessionStart hook runs silently at session start:

1. Prunes handoffs older than 30 days
2. Prunes archived handoffs older than 90 days
3. Produces no output (no auto-inject, no prompts)
```

With:

```markdown
The plugin's SessionStart hook runs silently at session start:

1. Prunes handoffs older than 30 days
2. Prunes archived handoffs older than 90 days
3. Prunes state files older than 24 hours
4. Produces no output (no auto-inject, no prompts)
```

**Step 4: Verify string-presence checks**

Run grep to confirm all three cleanup responsibilities appear in the resume skill:
- `grep "30 days" packages/plugins/handoff/skills/resuming-handoffs/SKILL.md`
- `grep "90 days" packages/plugins/handoff/skills/resuming-handoffs/SKILL.md`
- `grep "24 hours" packages/plugins/handoff/skills/resuming-handoffs/SKILL.md`

All three must match.

**Step 5: Commit**

```
docs(handoff): add trash-failure warning to skills, state file pruning to resume (I3+I5)
```

---

## Verification

After all 4 tasks:

1. `cd packages/plugins/handoff && uv run pytest tests/test_cleanup.py -v` — expect 26/26 pass
2. `cd packages/plugins/handoff && uv run ruff check` — expect clean
3. String-presence checks:
   - `grep "24-hour TTL" packages/plugins/handoff/skills/checkpointing/SKILL.md` — must match
   - `grep "24-hour TTL" packages/plugins/handoff/skills/creating-handoffs/SKILL.md` — must match
   - `grep "24 hours" packages/plugins/handoff/skills/resuming-handoffs/SKILL.md` — must match
   - `grep "BaseException" packages/plugins/handoff/scripts/cleanup.py` — must match
4. Push to remote

## Dependency Graph

```
Task 1 (I1+I2) ──→ Task 2 (T1-T3)    [sequential: both modify test_cleanup.py]
Task 3 (I4)    ──── independent        [cleanup.py docstring only]
Task 4 (I3+I5) ──── independent        [skill markdown only]
```

No behavioral dependencies. File coupling: Tasks 1 and 2 both modify `test_cleanup.py` — run 1→2 sequentially. Tasks 3 and 4 touch different files and can run in parallel with each other and with the 1→2 chain.
