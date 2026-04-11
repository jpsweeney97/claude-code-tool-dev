# T-03 Stale Cleanup Observability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `clean_stale_files()` report what it removed, what it skipped, and why — so that a run where every `unlink()` raises `PermissionError`, where the shakedown root itself is unreadable, or where the root is a dangling symlink is no longer indistinguishable from "nothing to clean". Wire the new signal through *every* caller with proper attribution on every log line.

**Architecture:** Introduce an immutable `CleanStaleResult` dataclass with four outcome buckets (`removed`, `skipped_fresh`, `failed_stat`, `failed_unlink`) plus a `report(prefix: str = "")` method that renders a summary line followed by one line per failure with path and error repr, *each line independently prefixed* so multi-line logs retain caller attribution after grep/aggregation.

Rewrite `clean_stale_files()` to:
- Use a **two-stage root check** — `lstat()` (does not follow symlinks) to detect true filesystem presence, then `stat()` (follows symlinks) to validate the target is a readable directory. This distinguishes "first run" (absent) from "corruption" (dangling symlink, not-a-directory), raising in every corruption case.
- **Enumerate** stale candidates with `os.listdir()` + `fnmatch.fnmatch()` instead of `Path.glob()`. The stdlib `Path.glob()` silently returns `[]` when the directory cannot be read (verified empirically on Python 3.14: `chmod 0o000` on a directory makes `root.glob("seed-*.json")` return `[]` with no exception). `os.listdir()` raises `PermissionError` loudly on the same input, so the enumeration step becomes observable. Note that this case is **not** catchable by the two-stage root check: `stat()` on an unreadable directory succeeds (mode `0o40000`, `S_ISDIR` true) because stat only needs execute permission on the parent — the read bit denial only surfaces at the listing step.
- **Return** an empty `CleanStaleResult` *only* when `lstat()` raises `FileNotFoundError` on the root (the legitimate first-run state).
- **Raise** on every other root-level failure (`OSError` from `lstat`, `OSError` from `stat`, `OSError` from `os.listdir`, non-directory mode bits), with an explicit `"clean_stale_files failed: …"` message that matches the project's error-format convention.
- **Capture** per-file `stat()` and `unlink()` failures into the result buckets so individual errors do not abort the run.
- Replace `path.is_file()` with an explicit `path.stat()` + `S_ISREG` check so per-file stat errors become observable (Python's stdlib `Path.is_file()` silently catches `OSError` and returns `False`, which was absorbing stat errors before the explicit `try/except` could see them).

Update **all three callers** — `clean_stale_shakedown.py` (CLI wrapper), `containment_lifecycle.py:73` (hook handler), and `containment_smoke_setup.py:118` (smoke scenario prep) — so each surfaces **two distinct error surfaces** with caller-appropriate framing:

- **Per-file failures** (e.g., `Path.unlink` raising `PermissionError` mid-sweep) — `clean_stale_files` returns a `CleanStaleResult` with `had_errors=True`. Each caller gates `report(prefix=...)` output on `had_errors` so multi-line reports retain caller attribution after grep/aggregation. The wrapper is silent on clean runs per Round 5 Choice 3B.
- **Root-level failures** (e.g., `chmod 0o000` on the shakedown root, dangling symlink, lstat denied) — `clean_stale_files` raises `OSError` before returning any result. Root-level raises **never go through `report(prefix=...)`** — they propagate to each caller's **outer exception boundary**, which produces a caller-specific wrapper message with a caller-specific exit-code contract: `clean_stale_shakedown failed: <exc>` → exit `1`, `containment-lifecycle: internal error (<exc>)` → return `0` (fail-OPEN), `containment_smoke_setup failed: <exc>` → exit `1`.

Add **in-process seam tests** that force `had_errors=True` via monkeypatched `Path.unlink` and call each caller's seam function (`_handle_subagent_start`, `prepare_scenario`) directly — these pin the per-file surface at the seam (not the outer boundary), so a regression in the `had_errors` gate or `report(prefix=...)` rendering is caught automatically. Add **four outer-boundary tests** for the root-level surface, two per caller: lifecycle subprocess (real `chmod 0o000` through `main()`, asserts exit `0` + caller-attributed stderr) plus lifecycle in-process fallback (Round 5 — platform-agnostic via monkeypatched `os.listdir`, pins the fail-OPEN conversion on root/Windows where the subprocess test skips); and smoke-setup subprocess (Round 5 — real `chmod 0o000` through the `__main__` fail-fast wrapper, asserts exit `1` + wrapper-prefixed stderr) plus smoke-setup in-process fallback (Round 6 — platform-agnostic via monkeypatched `os.listdir` calling the extracted `_run_with_wrapper(argv)` function directly, after a behavior-preserving testability refactor that moves the `__main__` block's try/except into a callable function). These four tests pin the **two different outer-boundary contract shapes** on every platform regardless of `geteuid` availability. **T-03 does not change any caller's exit-code contract**. The lifecycle hook's fail-open policy (exit `0` even on internal errors) is deliberate — the hook runner must never see a failed hook, and the operator observability contract is stderr-based. See the **Fail-Open Hook Policy** subsection under Design Decisions for the rationale and contract shape.

**Tech Stack:** Python 3.11+, `pathlib.Path`, `stat.S_ISREG`/`S_ISDIR`, `@dataclass(frozen=True)`, pytest with `monkeypatch.context()` for scoped patching of `Path.stat`/`Path.unlink`, `capsys` for stderr capture, `importlib.util` for in-process loading of script modules.

**Ticket:** [T-20260410-03](../../tickets/2026-04-10-T-20260410-03-harden-stale-cleanup-observability-and-failure-rep.md)

**Branch:** `fix/t03-stale-cleanup-observability` (already created, based on `origin/main` at `fd7c9365`)

---

## Design Decisions

### Dangling Shakedown Root Symlink

**Decision:** A dangling `shakedown/` symlink (lstat succeeds but stat fails because the target is missing) is treated as **corruption that must be surfaced**, not as a legitimate first-run state.

**Rationale:**
- "First run" means the directory was never created; `lstat()` raises `FileNotFoundError`.
- A dangling symlink means *something* was created at that path and later broke. This is an operational anomaly — a misconfiguration, a cleanup bug in an upstream tool, or a stale artifact from a removed mount point. Silently treating it as empty success would re-create exactly the silent-failure class the ticket is eliminating, just at a slightly higher level than `is_file()`.
- Matches the project's "Explicit over Silent" tenet and is consistent with the rest of this refactor.
- Implementation distinguishes the two cases with a `lstat()` → `stat()` two-stage check.

**Test coverage:** Task 4 adds `test_clean_stale_files_raises_on_dangling_root_symlink` which creates a real dangling symlink via `Path.symlink_to(nonexistent)` and asserts that `clean_stale_files` raises. The test uses `pytest.skip` on systems without symlink support, matching the pattern already established at `test_containment.py:81` for `test_is_path_within_scope_denies_symlink_resolving_outside`.

### Enumeration Primitive: `os.listdir()` instead of `Path.glob()`

**Decision:** Candidate discovery uses `os.listdir()` + `fnmatch.fnmatch()` instead of `Path.glob()`.

**Rationale:**
- Round 3 review exposed that `Path.glob()` silently returns `[]` when the directory cannot be read (`chmod 0o000` on the root still passes `lstat()` and `stat()`, so the two-stage root check does not catch it). This is the exact silent-success class the ticket is supposed to eliminate, relocated from `is_file()` to `glob()`.
- **Empirically verified on Python 3.14** before revising this plan. A `chmod 0o000 shakedown/` directory:
  - `Path.stat()` succeeds with mode `0o40000` (`S_ISDIR` true)
  - `Path.glob("seed-*.json")` returns `[]` with no exception
  - `os.listdir(shakedown)` raises `PermissionError(13, 'Permission denied')`
  - `os.scandir(shakedown)` raises the same
- `os.listdir()` + `fnmatch` is the most direct replacement: stdlib, no context manager, synchronous error reporting, preserves the existing pattern matching semantics. `os.scandir()` is also acceptable but requires a `with` block for cleanup and offers no additional value here (we re-stat each candidate explicitly anyway).
- `os` is already imported at `server/containment.py:6`; only `fnmatch` is a new import.
- Iteration order is not semantically meaningful because the `CleanStaleResult` buckets are consumed by set-based or single-element assertions in all tests; `os.listdir` directory order is platform-dependent but irrelevant to correctness.

**Scale tradeoff:** `os.listdir()` materializes all directory entries into memory as a `list[str]`, and the candidate list is then iterated in a second pass. This is acceptable because the shakedown directory holds state files for a single agent run (typically 5-15 files bounded by `_STALE_PATTERNS`) and is cleaned every 24 hours, so the eager scan never crosses single-digit kilobytes in any reasonable operating envelope. If the shakedown footprint were ever to grow into the thousands of entries, `os.scandir()` with per-entry processing inside a `with` block would be a drop-in replacement preserving the same loud-failure semantics — both helpers raise `PermissionError` on a `chmod 0o000` directory, so the Stage 3 guard remains correct under either primitive. The tradeoff is noted here so a future maintainer who hits the operational envelope understands the swap path without having to re-derive it.

**Test coverage:** Task 4 adds two tests:
- `test_clean_stale_files_raises_when_enumeration_fails` — monkeypatches `os.listdir` to raise `PermissionError`, verifies the error is wrapped with `"cannot enumerate shakedown root"` context. Portable, no platform dependency.
- `test_clean_stale_files_raises_when_root_directory_unreadable` — real `chmod 0o000` on the shakedown directory, exercises the full enumeration path without any monkeypatch. `@pytest.mark.skipif` when running as root (POSIX permission bypass) or on platforms without `os.geteuid` (Windows).

Task 7 Step 7 adds a manual subprocess smoke check that recreates the same chmod scenario end-to-end through the wrapper script.

### Fail-Open Hook Policy for `containment_lifecycle.py`

**Decision:** The lifecycle hook is **deliberately fail-open**. Any exception raised from `clean_stale_files()` (or any other internal code path) is caught by `main()`'s outer `except Exception` boundary at `containment_lifecycle.py:184-188`, logged to stderr as `containment-lifecycle: internal error (<exc>)`, and converted to exit code `0`. T-03 does **not** change this — it only enriches the stderr surface so operators have actionable context when reading hook logs.

**Rationale:**
- Claude Code's hook contract says that hooks are advisory. A hook returning a non-zero exit code to the hook runner is a signal that the *hook runner* should take action (the semantics depend on the hook event). `SubagentStart` treats non-zero as "block the spawn", which is the exact opposite of what we want when the containment state is simply un-enumerable: we want the spawn to proceed under the normal no-scope (passthrough) path, and we want the operator to see the failure on stderr after the fact.
- Returning non-zero from `SubagentStart` when the shakedown root is broken would propagate an infrastructure failure in T4 containment state into a hard block on unrelated agent spawns, which is an unacceptable blast radius for a cleanup-sweep defect. The current behavior correctly contains the blast radius to stderr visibility.
- The failure surface is therefore **observability via stderr, not exit codes**. This is what T-03 rewrites: `main()` already caught exceptions; what was missing was caller-attributed context that maps a terse message (`containment-lifecycle: internal error (OSError(13, ...))`) to the specific defect class so an operator triaging a stderr line knows which repair to make.
- Round 4 exposed that the earlier drafts' "naturally propagates" language was misleading: exceptions do propagate out of `clean_stale_files` → `_handle_subagent_start` → `handle_payload`, but they stop at `main()`'s outer catch-all and never reach the hook runner. That is correct behavior, but it must be asserted by test rather than assumed by prose.

**Assumption — hook-script stderr is a valid observability surface (accepted for T-03):** Fail-open is only useful if operators actually see the `containment-lifecycle: internal error (…)` stderr lines. Precedent at [`docs/tickets/closed-tickets/2026-02-15-plan-review-errata.md:439`](../../tickets/closed-tickets/2026-02-15-plan-review-errata.md) rejected stderr-only logging for the MCP server conversation guard because MCP servers are long-lived background subprocesses with no real monitoring path. **That precedent does NOT apply here**: hook scripts run per-event and their stderr is captured by Claude Code's hook runner (surfaced in session UI, logs, or aggregation pipelines depending on the operator's setup). T-03 accepts this structural difference as load-bearing because: (a) the fail-open rationale bullets above rely on it, (b) flipping to fail-fast has an unacceptable blast radius, (c) the contract shape table below makes the stderr surface itself greppable and testable. **If operational experience later shows hook stderr is being swallowed in practice, the correct fix is NOT to flip fail-open** — it is to add a structured telemetry emission path orthogonal to stderr, which is outside T-03's scope.

**Contract shape** (the exact strings an operator grep can rely on):

| Failure class | stderr contains (all strings) | exit code |
|---|---|---|
| Root `lstat` permission denied | `containment-lifecycle: internal error`, `cannot lstat shakedown root` | `0` |
| Dangling root symlink | `containment-lifecycle: internal error`, `possible broken symlink` | `0` |
| Root not a directory | `containment-lifecycle: internal error`, `shakedown root is not a directory` | `0` |
| Unreadable root (`chmod 0o000`) | `containment-lifecycle: internal error`, `cannot enumerate shakedown root` | `0` |
| Per-file unlink failure (pointer/seed present) | `containment-lifecycle: clean_stale_files:`, `failed_unlink=N`, every line prefixed with `containment-lifecycle: ` | `0` |
| All clean (no failures) | *nothing from the cleanup block* (only standard lifecycle output) | `0` |

**Test coverage:** Task 8 adds three lifecycle tests. The **outer-boundary pair** pins this contract on every platform; the seam test catches a different regression class:

- `test_subagent_start_logs_cleanup_errors_with_lifecycle_prefix` (in-process via `_load_lifecycle_module`) — **seam-level**. Calls `_handle_subagent_start` directly with monkeypatched `Path.unlink` to force `had_errors=True` and asserts every `clean_stale_files:` / `failed_*` line is `containment-lifecycle: `-prefixed. Pins the per-file reporting seam. Does NOT touch `main()` and does NOT pin the fail-open conversion — that is the next two tests.
- `test_subagent_start_surfaces_cleanup_enumeration_failure` (subprocess via `_run_lifecycle`) — **outer-boundary, subprocess**. Real `chmod 0o000` through `main()`; asserts `returncode == 0` **and** stderr contains both `containment-lifecycle: internal error` and `cannot enumerate shakedown root`. Authoritative end-to-end proof of the fail-open exception-to-exit-code conversion. **SKIPs on root and Windows** (`hasattr(os, "geteuid")` + `os.geteuid() == 0` guard).
- `test_main_fail_open_conversion_via_monkeypatched_listdir` (Round 5 in-process fallback) — **outer-boundary, platform-agnostic**. Calls `lifecycle.main()` directly with monkeypatched `os.listdir`, `sys.stdin`, and `CLAUDE_PLUGIN_DATA`; pins the same fail-open conversion contract at the language level. **Runs without a skipif** so root and Windows CI still pin the contract when the subprocess test skips.

Together the two outer-boundary tests (subprocess + in-process fallback) prove that T-03's observability contract survives through `main()`'s fail-open boundary **on every platform** — the subprocess test is the authoritative end-to-end proof where it can run, and the in-process fallback guarantees there is no platform on which the fail-open conversion is unpinned. The seam test catches accidental deletion of the `if cleanup_result.had_errors:` gate or changes to `report(prefix=...)` rendering, which the outer-boundary tests would not detect because they force root-level raises rather than per-file failures.

---

## Scope Notes

**In scope:**
- `packages/plugins/codex-collaboration/server/containment.py` — `clean_stale_files()` rewrite plus new `CleanStaleResult` dataclass with prefixed `report()`
- `packages/plugins/codex-collaboration/scripts/clean_stale_shakedown.py` — wrapper logs `result.report()` to stderr **only on `had_errors`** (Choice 3B, Round 5); root-level raises propagate to the existing outer `except Exception` boundary which prints `clean_stale_shakedown failed: <exc>` and exits `1` (unchanged)
- `packages/plugins/codex-collaboration/scripts/containment_lifecycle.py` — hook handler logs `result.report(prefix="containment-lifecycle: ")` on `had_errors`
- `packages/plugins/codex-collaboration/scripts/containment_smoke_setup.py` — smoke-setup logs `result.report(prefix="containment_smoke_setup: ")` on `had_errors`
- `packages/plugins/codex-collaboration/tests/test_containment.py` — coverage tests for every outcome bucket, root-level failures including dangling symlink, `report()` rendering with and without prefix, mixed-batch scenario, tightened happy-path test
- `packages/plugins/codex-collaboration/tests/test_containment_lifecycle.py` — three new tests: (1) in-process test forcing per-file `had_errors=True` via monkeypatched `Path.unlink` and asserting on captured stderr with the lifecycle prefix on every reported line; (2) subprocess test exercising a real `chmod 0o000` shakedown directory through the `main()` boundary and asserting the fail-open exit code plus caller-attributed stderr context; (3) platform-agnostic in-process fallback test calling `main()` directly with monkeypatched `os.listdir` so the fail-open conversion contract is pinned on root/Windows where the subprocess chmod test skips
- `packages/plugins/codex-collaboration/tests/test_containment_smoke_setup.py` — **new file** (three focused tests): (1) in-process seam test that uses importlib + `monkeypatch.setattr(smoke_setup, "_scenario_definition", raising_stub)` to force per-file `had_errors=True` through `prepare_scenario` via a direct seam, and asserts on stderr with the smoke_setup prefix; (2) subprocess test exercising a real `chmod 0o000` shakedown directory through smoke-setup's `__main__` fail-fast wrapper, pinning smoke-setup's fail-FAST contract (exit 1, outer-wrapper stderr prefix) in contrast to lifecycle's fail-OPEN contract; (3) Round 6 platform-agnostic in-process fallback calling the extracted `_run_with_wrapper(argv)` function directly with monkeypatched `os.listdir`, pinning the same fail-FAST `SystemExit(1)` + wrapper-prefixed stderr contract on root/Windows where the subprocess chmod test skips

**Explicitly out of scope (document, do not change):**
- `read_active_run_id()` and `read_json_file()` lenient helpers at `containment.py:81` and `:114`. Not called by `clean_stale_files`; strict alternates exist at `:92` and `:126`. Migrating their 5+ call sites is a separate refactor.
- Module-scope `server.containment` imports in `containment_lifecycle.py` and `containment_smoke_setup.py` (separate adjacent sharp edge noted in the resumed handoff).

**Key correctness constraints (derived from seven rounds of adversarial review):**
1. **`Path.exists()` silently swallows `OSError`.** Never gate the root check with it — use `lstat()` (and then `stat()` for symlink resolution).
2. **`Path.is_file()` silently swallows `OSError`.** Never use it after a stat call; check `S_ISREG(stat_result.st_mode)` instead.
3. **`Path.stat()` follows symlinks.** A dangling symlink at the shakedown root raises `FileNotFoundError` from `stat()`, which would be indistinguishable from "directory truly absent" without a prior `lstat()` call.
4. **`Path.glob()` silently returns `[]` on unreadable directories.** Its internal `_scandir` wrapper catches `OSError` in the walker, so a `chmod 0o000` directory returns an empty result with no exception. **Verified empirically on Python 3.14 before this plan revision.** Never use `Path.glob()` as the discovery primitive for observability-sensitive cleanup. Use `os.listdir()` (or `os.scandir()`) — both raise `PermissionError` loudly on the same input — and filter names with `fnmatch.fnmatch()`.
5. **Root `stat()` success does not imply root listability.** `stat()` on a directory only needs execute permission on the parent; it returns mode `0o40000` and `S_ISDIR` true even when the directory itself has no read permission. The enumeration guard is therefore a *separate* layer from the two-stage root check, not a consequence of it.
6. **Global `monkeypatch.setattr(Path, "stat", …)` breaks `Path.exists()` and every other stat-based pathlib method.** Scope the patch with `with monkeypatch.context() as patched:` so assertions outside the scope see real stat.
7. **`report()` (not `summary()`) is the operator-facing output.** A count like `failed_unlink=1` is not actionable; operators need the path and the error repr. `summary()` as a standalone method was removed during revision.
8. **`report()` accepts a `prefix` parameter** that it applies to *every* line. Without this, only the summary line carries caller attribution and the per-failure lines become bare `  failed_stat …` entries that are hard to grep in aggregated logs.
9. **Never use `rm -rf`.** Use `trash <path>` per the global CLAUDE.md safety rules.
10. **Caller-wiring bugs must be caught by automated tests, not just manual verification.** The plan's verification steps must force `had_errors=True` in both internal callers and assert on captured stderr.
11. **`containment_lifecycle.py:main()` is deliberately fail-open.** Its outer `except Exception` at lines 184-188 catches every internal error and returns `0`, because `SubagentStart` treats non-zero exit codes as "block the spawn" and a containment-state defect must not escalate into a hard block on unrelated agent spawns. T-03 enriches the stderr surface but never changes this exit-code contract. Any future change that makes `main()` return non-zero on cleanup failures must be paired with an explicit policy update in the Design Decisions section, not slipped in silently. See the **Fail-Open Hook Policy** design decision.

---

## File Structure

| File | Change type | Responsibility |
|---|---|---|
| `packages/plugins/codex-collaboration/server/containment.py` | Modify | Add `CleanStaleResult` dataclass with `report(prefix)` method; rewrite `clean_stale_files()` with three-stage failure check (`lstat`/`stat`/`os.listdir`), `fnmatch`-based discovery, and per-file failure capture |
| `packages/plugins/codex-collaboration/scripts/clean_stale_shakedown.py` | Modify | Capture result and print `report()` (no prefix) to stderr **on `had_errors`** (Choice 3B, Round 5); root-level raises surface via the existing outer `except Exception` boundary as `clean_stale_shakedown failed: <exc>` + exit `1` (unchanged) |
| `packages/plugins/codex-collaboration/scripts/containment_lifecycle.py` | Modify | Capture result in `_handle_subagent_start` and `_log_error(result.report(prefix="containment-lifecycle: "))` when `had_errors` |
| `packages/plugins/codex-collaboration/scripts/containment_smoke_setup.py` | Modify | Capture result in `prepare_scenario` and print `result.report(prefix="containment_smoke_setup: ")` to stderr when `had_errors`. **Round 6 testability refactor** (behavior-preserving): extract the `__main__` block's try/except into a module-level `_run_with_wrapper(argv)` function so the fail-FAST wrapper is callable from in-process tests. Same stderr text, same `SystemExit(1)` on exception, same `SystemExit(main(argv))` happy path — no contract change, only structural. |
| `packages/plugins/codex-collaboration/tests/test_containment.py` | Modify | Add 13 new tests; tighten 1 existing test |
| `packages/plugins/codex-collaboration/tests/test_containment_lifecycle.py` | Modify | Add 3 new tests covering both error surfaces: (1) in-process test forcing per-file `had_errors=True` and asserting on prefixed stderr; (2) subprocess test exercising a real `chmod 0o000` through `main()` and asserting fail-open exit code plus caller-attributed stderr context; (3) platform-agnostic in-process fallback test that calls `main()` directly with monkeypatched `os.listdir` so root/Windows still pin the fail-open conversion contract |
| `packages/plugins/codex-collaboration/tests/test_containment_smoke_setup.py` | **Create** | New file with 3 focused tests covering both error surfaces: (1) in-process test forcing per-file `had_errors=True` through `prepare_scenario` via direct `_scenario_definition` stub, asserting on prefixed stderr (pins the **seam** for the per-file surface); (2) subprocess test exercising a real `chmod 0o000` through smoke-setup's `__main__` wrapper, asserting fail-fast exit 1 plus outer-wrapper-attributed stderr context (pins the **outer boundary** for the root-level surface on non-root POSIX); (3) **Round 6 in-process fallback** that monkeypatches `os.listdir` and calls the extracted `_run_with_wrapper(argv)` function directly, asserting `SystemExit(1)` + wrapper-prefixed stderr — pins the same outer-boundary contract on every platform regardless of `os.geteuid` availability |

---

## Task 1: Rewrite `clean_stale_files` to return `CleanStaleResult` with three-stage failure check

**Files:**
- Modify: `packages/plugins/codex-collaboration/server/containment.py`
- Test: `packages/plugins/codex-collaboration/tests/test_containment.py`

This task lands the full refactor in one atomic commit covering: the `CleanStaleResult` dataclass, the `report(prefix)` method, the two-stage `lstat()`/`stat()` root check, the replacement of `is_file()` with explicit stat, and per-file failure capture. Subsequent tasks add coverage tests that pass immediately against this implementation. If any later coverage test fails on first run, the Task 1 implementation drifted from this spec.

- [ ] **Step 1: Write the happy-path return-value test**

Add this test to `tests/test_containment.py` right after the existing `test_clean_stale_files_removes_old_state_only` test (after line 213):

```python
def test_clean_stale_files_returns_result_with_removed_and_fresh(
    tmp_path: Path,
) -> None:
    shakedown = containment.shakedown_dir(tmp_path)
    shakedown.mkdir(parents=True)
    old_scope = shakedown / "scope-run-1.json"
    fresh_seed = shakedown / "seed-run-2.json"
    old_scope.write_text("{}", encoding="utf-8")
    fresh_seed.write_text("{}", encoding="utf-8")
    stale_time = time.time() - (26 * 3600)
    os.utime(old_scope, (stale_time, stale_time))

    result = containment.clean_stale_files(shakedown)

    assert isinstance(result, containment.CleanStaleResult)
    assert result.removed == (old_scope,)
    assert result.skipped_fresh == (fresh_seed,)
    assert result.failed_stat == ()
    assert result.failed_unlink == ()
    assert result.had_errors is False
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd packages/plugins/codex-collaboration
uv run pytest tests/test_containment.py::test_clean_stale_files_returns_result_with_removed_and_fresh -v
```

Expected: FAIL with `AttributeError: module 'server.containment' has no attribute 'CleanStaleResult'`.

- [ ] **Step 3: Add imports to `server/containment.py`**

In `server/containment.py`, add `import fnmatch` between the existing `import json` (line 5) and `import os` (line 6) so the plain imports stay alphabetized. Then after the existing `from typing import Any` line (line 9), add:

```python
from dataclasses import dataclass
from stat import S_ISDIR, S_ISREG
```

The final import block should look like:

```python
from __future__ import annotations

import fnmatch
import json
import os
import time
from pathlib import Path
from typing import Any
from dataclasses import dataclass
from stat import S_ISDIR, S_ISREG
```

`fnmatch` is stdlib and carries no dependency risk. It is needed because Task 1 Step 5 replaces `Path.glob(pattern)` (which silently swallows directory-read failures) with `os.listdir()` + `fnmatch.fnmatch(name, pattern)`.

- [ ] **Step 4: Add the `CleanStaleResult` dataclass with prefixed `report()`**

Insert the dataclass immediately before the existing `clean_stale_files` function (before line 290):

```python
@dataclass(frozen=True)
class CleanStaleResult:
    """Outcome of a :func:`clean_stale_files` sweep.

    Attributes:
        removed: Paths that were successfully unlinked.
        skipped_fresh: Paths under the age cutoff that were left in place.
        failed_stat: ``(path, error_repr)`` pairs where ``stat()`` raised
            ``OSError`` on an individual file. These files could not be
            checked for age and were not attempted for deletion.
        failed_unlink: ``(path, error_repr)`` pairs where ``unlink()`` raised
            ``OSError`` after a successful stat. The file is still on disk.

    Root-level access failures (an absent-but-existing root entry, an
    unreadable root, a dangling symlink root, or a root path that is not
    a directory) are raised rather than captured here, because they
    indicate a global abort condition rather than a per-file outcome.
    """

    removed: tuple[Path, ...]
    skipped_fresh: tuple[Path, ...]
    failed_stat: tuple[tuple[Path, str], ...]
    failed_unlink: tuple[tuple[Path, str], ...]

    @property
    def had_errors(self) -> bool:
        """Return True when any per-file stat or unlink call failed."""

        return bool(self.failed_stat or self.failed_unlink)

    def report(self, prefix: str = "") -> str:
        """Return an operator-facing multi-line report of the sweep.

        Args:
            prefix: Optional string prepended to *every* line, so that
                multi-line reports retain caller attribution when
                aggregated with other log output. Defaults to empty
                (suitable when the report is printed in an unambiguous
                single-source context such as the standalone CLI wrapper).

        Returns:
            A string whose first line is a terse count summary
            ("removed=N, fresh=N, ...") and whose remaining lines are
            one entry per failure, each rendered as
            ``  failed_stat <path>: <error_repr>`` or
            ``  failed_unlink <path>: <error_repr>``. Every line is
            prefixed with ``prefix``. Designed for printing to stderr.
        """

        parts = [
            f"removed={len(self.removed)}",
            f"fresh={len(self.skipped_fresh)}",
        ]
        if self.failed_stat:
            parts.append(f"failed_stat={len(self.failed_stat)}")
        if self.failed_unlink:
            parts.append(f"failed_unlink={len(self.failed_unlink)}")
        lines = [prefix + "clean_stale_files: " + ", ".join(parts)]
        for path, error in self.failed_stat:
            lines.append(f"{prefix}  failed_stat {path}: {error}")
        for path, error in self.failed_unlink:
            lines.append(f"{prefix}  failed_unlink {path}: {error}")
        return "\n".join(lines)
```

- [ ] **Step 5: Rewrite the `clean_stale_files` function body**

Replace lines 290-310 (the existing `clean_stale_files` function) with:

```python
def clean_stale_files(
    shakedown_path: Path, max_age_hours: int = 24
) -> CleanStaleResult:
    """Remove stale shakedown state files older than ``max_age_hours``.

    Returns a :class:`CleanStaleResult` describing what was removed, what was
    skipped because it was still fresh, and any per-file ``stat()`` or
    ``unlink()`` failures encountered during the sweep. Per-file errors do
    not abort the run.

    Root-level handling uses a **three-stage check** to distinguish a
    legitimate first-run absence from every corruption mode:

    - Stage 1 (``lstat``): ``FileNotFoundError`` means the path entry does
      not exist at the filesystem level — the legitimate first-run state.
      Returns an empty :class:`CleanStaleResult`. Any other ``OSError``
      (permission denied on the parent, stale NFS handle, etc.) is
      re-raised with an explicit ``"cannot lstat"`` context message.
    - Stage 2 (``stat``): Follows symlinks and validates the resolved
      target. A dangling symlink raises ``FileNotFoundError`` *from this
      call* (not Stage 1), re-raised as ``OSError`` with a
      ``"possible broken symlink"`` context message. A non-directory
      target (``S_ISDIR`` false) raises ``NotADirectoryError``.
    - Stage 3 (``os.listdir``): Enumerates candidate entries. A
      ``chmod 0o000`` directory passes Stage 2 (``stat`` on a directory
      only needs execute permission on the parent, so mode ``0o40000``
      still comes back with ``S_ISDIR`` true), but ``os.listdir`` raises
      ``PermissionError`` when it actually tries to read the directory
      contents. Re-raised with a ``"cannot enumerate"`` context message.
      This stage is necessary because the stdlib ``Path.glob()`` helper
      would silently return ``[]`` on the same input, which would mask
      the failure as a clean empty result.

    Stages 1 and 2 run without touching directory contents; Stage 3 is
    the first operation that requires the directory's read bit. Any
    earlier "stat succeeded" signal does not imply listability.

    Raises:
        OSError: If the shakedown root exists but cannot be stat-ed or
            cannot be enumerated. Covers three distinct failure classes:
            lstat failure on an existing entry, stat failure after
            lstat succeeds (dangling symlink or similar), and
            ``os.listdir`` failure after stat succeeds (unreadable
            directory contents). Matches the "Explicit over Silent"
            tenet.
        NotADirectoryError: If the shakedown root (after symlink
            resolution) is not a directory. Subclass of ``OSError``.
    """

    removed: list[Path] = []
    skipped_fresh: list[Path] = []
    failed_stat: list[tuple[Path, str]] = []
    failed_unlink: list[tuple[Path, str]] = []

    # Stage 1: lstat() without following symlinks. Distinguishes true
    # filesystem absence from a dangling-symlink corruption state.
    try:
        shakedown_path.lstat()
    except FileNotFoundError:
        return CleanStaleResult(
            removed=tuple(removed),
            skipped_fresh=tuple(skipped_fresh),
            failed_stat=tuple(failed_stat),
            failed_unlink=tuple(failed_unlink),
        )
    except OSError as exc:
        raise OSError(
            f"clean_stale_files failed: cannot lstat shakedown root. "
            f"Got: {exc!r:.100}"
        ) from exc

    # Stage 2: stat() follows symlinks and validates the resolved target.
    try:
        root_stat = shakedown_path.stat()
    except OSError as exc:
        raise OSError(
            f"clean_stale_files failed: shakedown root is unreadable "
            f"(possible broken symlink). Got: {exc!r:.100}"
        ) from exc

    if not S_ISDIR(root_stat.st_mode):
        raise NotADirectoryError(
            f"clean_stale_files failed: shakedown root is not a directory. "
            f"Got: {str(shakedown_path)!r:.100}"
        )

    # Stage 3: enumerate candidates with os.listdir. Path.glob silently
    # returns [] on directories we cannot read (verified on Python 3.14:
    # chmod 0o000 on a directory makes root.glob("seed-*.json") return []
    # with no exception). os.listdir raises PermissionError loudly on
    # the same input. This stage is necessary because stat() on an
    # unreadable directory succeeds with mode 0o40000 — the two-stage
    # root check above cannot detect this class.
    try:
        entry_names = os.listdir(shakedown_path)
    except OSError as exc:
        raise OSError(
            f"clean_stale_files failed: cannot enumerate shakedown root. "
            f"Got: {exc!r:.100}"
        ) from exc

    candidates = [
        shakedown_path / name
        for name in entry_names
        if any(fnmatch.fnmatch(name, pattern) for pattern in _STALE_PATTERNS)
    ]

    cutoff = max_age_hours * 3600
    current_time = time.time()
    for path in candidates:
        try:
            stat_result = path.stat()
        except OSError as exc:
            failed_stat.append((path, f"{exc!r:.100}"))
            continue
        if not S_ISREG(stat_result.st_mode):
            continue
        age_seconds = current_time - stat_result.st_mtime
        if age_seconds <= cutoff:
            skipped_fresh.append(path)
            continue
        try:
            path.unlink()
        except OSError as exc:
            failed_unlink.append((path, f"{exc!r:.100}"))
            continue
        removed.append(path)

    return CleanStaleResult(
        removed=tuple(removed),
        skipped_fresh=tuple(skipped_fresh),
        failed_stat=tuple(failed_stat),
        failed_unlink=tuple(failed_unlink),
    )
```

- [ ] **Step 6: Run the new test**

```bash
cd packages/plugins/codex-collaboration
uv run pytest tests/test_containment.py::test_clean_stale_files_returns_result_with_removed_and_fresh -v
```

Expected: PASS.

- [ ] **Step 7: Run the full containment test file to confirm no regression**

```bash
cd packages/plugins/codex-collaboration
uv run pytest tests/test_containment.py -v
```

Expected: all tests pass, including the existing `test_clean_stale_files_removes_old_state_only` (it only asserts on filesystem state, which is unchanged).

- [ ] **Step 8: Commit**

```bash
git add packages/plugins/codex-collaboration/server/containment.py packages/plugins/codex-collaboration/tests/test_containment.py
git commit -m "feat(containment): return CleanStaleResult with three-stage failure check"
```

---

## Task 2: Coverage for per-file `unlink()` failure

**Files:**
- Test: `packages/plugins/codex-collaboration/tests/test_containment.py`

- [ ] **Step 1: Add the test**

Add this test right after the test from Task 1:

```python
def test_clean_stale_files_captures_unlink_failures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    shakedown = containment.shakedown_dir(tmp_path)
    shakedown.mkdir(parents=True)
    stale = shakedown / "scope-run-1.json"
    stale.write_text("{}", encoding="utf-8")
    stale_time = time.time() - (26 * 3600)
    os.utime(stale, (stale_time, stale_time))

    original_unlink = Path.unlink

    def failing_unlink(self: Path, *args: object, **kwargs: object) -> None:
        if self == stale:
            raise PermissionError(13, "denied", str(self))
        return original_unlink(self, *args, **kwargs)  # type: ignore[arg-type]

    with monkeypatch.context() as patched:
        patched.setattr(Path, "unlink", failing_unlink)
        result = containment.clean_stale_files(shakedown)

    assert stale.exists(), "stale file should still be on disk after failed unlink"
    assert result.removed == ()
    assert len(result.failed_unlink) == 1
    failed_path, failed_repr = result.failed_unlink[0]
    assert failed_path == stale
    assert "PermissionError" in failed_repr
    assert result.had_errors is True
```

- [ ] **Step 2: Run the test**

```bash
cd packages/plugins/codex-collaboration
uv run pytest tests/test_containment.py::test_clean_stale_files_captures_unlink_failures -v
```

Expected: PASS (Task 1 already implemented `failed_unlink` capture).

- [ ] **Step 3: Commit**

```bash
git add packages/plugins/codex-collaboration/tests/test_containment.py
git commit -m "test(containment): cover clean_stale_files unlink failure capture"
```

---

## Task 3: Coverage for per-file `stat()` failure

**Files:**
- Test: `packages/plugins/codex-collaboration/tests/test_containment.py`

- [ ] **Step 1: Add the test**

Add this test right after Task 2's test:

```python
def test_clean_stale_files_captures_stat_failures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    shakedown = containment.shakedown_dir(tmp_path)
    shakedown.mkdir(parents=True)
    unreadable = shakedown / "seed-run-1.json"
    unreadable.write_text("{}", encoding="utf-8")

    original_stat = Path.stat

    def failing_stat(self: Path, *args: object, **kwargs: object) -> os.stat_result:
        if self == unreadable:
            raise PermissionError(13, "denied", str(self))
        return original_stat(self, *args, **kwargs)  # type: ignore[arg-type]

    with monkeypatch.context() as patched:
        patched.setattr(Path, "stat", failing_stat)
        result = containment.clean_stale_files(shakedown)

    # Patch reverted here — safe to use .exists() again.
    assert unreadable.exists(), "stat failure should not cause deletion attempt"
    assert result.removed == ()
    assert result.failed_unlink == ()
    assert len(result.failed_stat) == 1
    failed_path, failed_repr = result.failed_stat[0]
    assert failed_path == unreadable
    assert "PermissionError" in failed_repr
    assert result.had_errors is True
```

Note: the root `shakedown` directory is a separate `Path` object from `unreadable`, so the `if self == unreadable:` filter lets the root stat calls (both `lstat` and `stat`) go through to the real implementation.

- [ ] **Step 2: Run the test**

```bash
cd packages/plugins/codex-collaboration
uv run pytest tests/test_containment.py::test_clean_stale_files_captures_stat_failures -v
```

Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add packages/plugins/codex-collaboration/tests/test_containment.py
git commit -m "test(containment): cover clean_stale_files per-file stat failure capture"
```

---

## Task 4: Coverage for whole-sweep failures (root stat and enumeration)

**Files:**
- Test: `packages/plugins/codex-collaboration/tests/test_containment.py`

Six scenarios for whole-sweep failures — four at the root-stat layer, two at the enumeration layer:

1. **Missing root** (`lstat` raises `FileNotFoundError`): legitimate first-run → returns empty
2. **Unreadable parent / lstat fails** (`lstat` raises `PermissionError` or similar): raises `OSError` with `"cannot lstat"` context
3. **Dangling symlink root** (`lstat` succeeds, `stat` raises `FileNotFoundError`): raises `OSError` with `"possible broken symlink"` context
4. **Root is not a directory** (stat succeeds, `S_ISDIR` false): raises `NotADirectoryError`
5. **Enumeration fails (mock-based)** (`os.listdir` monkeypatched to raise): raises `OSError` with `"cannot enumerate"` context — portable, no platform dependency
6. **Enumeration fails (real permission)** (`chmod 0o000` on the root directory): raises `OSError` with `"cannot enumerate"` context — exercises the full code path without any monkeypatch, skipped when running as root or on Windows

Scenarios 1-4 are root-stat checks; scenarios 5-6 are the enumeration guard. The separation matters: a directory with `chmod 0o000` passes all four stat checks (lstat succeeds, stat succeeds with mode `0o40000`, `S_ISDIR` is true) but fails at the listing step, which is exactly the silent-failure class `Path.glob()` would hide.

- [ ] **Step 1: Add the six whole-sweep failure tests**

Add these tests right after Task 3's test:

```python
def test_clean_stale_files_returns_empty_when_shakedown_root_missing(
    tmp_path: Path,
) -> None:
    shakedown = containment.shakedown_dir(tmp_path)
    assert not shakedown.exists()

    result = containment.clean_stale_files(shakedown)

    assert result.removed == ()
    assert result.skipped_fresh == ()
    assert result.failed_stat == ()
    assert result.failed_unlink == ()
    assert result.had_errors is False


def test_clean_stale_files_raises_when_root_lstat_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    shakedown = containment.shakedown_dir(tmp_path)
    shakedown.mkdir(parents=True)

    original_lstat = Path.lstat

    def failing_lstat(
        self: Path, *args: object, **kwargs: object
    ) -> os.stat_result:
        if self == shakedown:
            raise PermissionError(13, "denied", str(self))
        return original_lstat(self, *args, **kwargs)  # type: ignore[arg-type]

    with monkeypatch.context() as patched:
        patched.setattr(Path, "lstat", failing_lstat)
        with pytest.raises(OSError, match="cannot lstat shakedown root"):
            containment.clean_stale_files(shakedown)


def test_clean_stale_files_raises_on_dangling_root_symlink(
    tmp_path: Path,
) -> None:
    target = tmp_path / "nonexistent-target"
    link = tmp_path / "shakedown"
    try:
        link.symlink_to(target)
    except OSError as exc:
        pytest.skip(f"symlink creation unavailable: {exc}")
    assert not target.exists()
    assert link.is_symlink()

    with pytest.raises(OSError, match="possible broken symlink"):
        containment.clean_stale_files(link)


def test_clean_stale_files_raises_when_root_is_not_a_directory(
    tmp_path: Path,
) -> None:
    not_a_dir = tmp_path / "not-a-dir"
    not_a_dir.write_text("this is a file", encoding="utf-8")

    with pytest.raises(
        NotADirectoryError, match="shakedown root is not a directory"
    ):
        containment.clean_stale_files(not_a_dir)


def test_clean_stale_files_raises_when_enumeration_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Enumeration failure (directory exists and is stat-able but cannot be
    listed) must raise with actionable context, not silently return empty.

    This is the Round 3 review gap: ``stat()`` on a ``chmod 0o000``
    directory succeeds with mode ``0o40000`` (because stat only needs
    execute permission on the parent), so the two-stage ``lstat``/``stat``
    root check cannot detect this class. The enumeration guard is a
    separate layer on top of the stat checks, and this test forces
    ``os.listdir`` to raise to verify the guard propagates the error
    with the expected context message.

    Monkeypatches ``os.listdir`` so the test is portable (no reliance on
    the host's permission semantics). The companion test
    ``test_clean_stale_files_raises_when_root_directory_unreadable``
    exercises the same code path using a real ``chmod 0o000``.
    """
    shakedown = containment.shakedown_dir(tmp_path)
    shakedown.mkdir(parents=True)

    def failing_listdir(path: object) -> list[str]:
        raise PermissionError(13, "Permission denied", str(path))

    with monkeypatch.context() as patched:
        patched.setattr(os, "listdir", failing_listdir)
        with pytest.raises(OSError, match="cannot enumerate shakedown root"):
            containment.clean_stale_files(shakedown)


@pytest.mark.skipif(
    not hasattr(os, "geteuid") or os.geteuid() == 0,
    reason=(
        "POSIX permission check: chmod 0o000 is bypassed by root "
        "and unavailable on platforms without os.geteuid"
    ),
)
def test_clean_stale_files_raises_when_root_directory_unreadable(
    tmp_path: Path,
) -> None:
    """Real ``chmod 0o000`` on the shakedown root exercises the full
    enumeration path without any monkeypatch.

    Verifies the end-to-end claim:
    - ``Path.lstat`` succeeds on a mode-0o000 directory (it's still a
      filesystem entry)
    - ``Path.stat`` succeeds with mode ``0o40000`` (stat only needs
      execute on the parent)
    - ``S_ISDIR(0o40000)`` is True
    - ``os.listdir`` raises ``PermissionError`` (no read bit)
    - ``clean_stale_files`` re-raises with ``"cannot enumerate"`` context

    Without this test, a refactor that accidentally replaced
    ``os.listdir`` with ``Path.glob`` (or some other silent-swallow
    primitive) could pass the mock-based test above (which only exercises
    the raise path) while reintroducing the silent-failure class this
    ticket is meant to eliminate. The real chmod exercise catches that.

    Skipped when running as root (POSIX permission checks are bypassed)
    or on platforms without ``os.geteuid`` (e.g., Windows).
    """
    shakedown = containment.shakedown_dir(tmp_path)
    shakedown.mkdir(parents=True)
    (shakedown / "scope-run-1.json").write_text("{}", encoding="utf-8")
    try:
        os.chmod(shakedown, 0o000)
        with pytest.raises(OSError, match="cannot enumerate shakedown root"):
            containment.clean_stale_files(shakedown)
    finally:
        # Restore permissions so pytest's tmp_path teardown can remove
        # the directory and its contents.
        os.chmod(shakedown, 0o755)
```

- [ ] **Step 2: Run all six whole-sweep failure tests**

```bash
cd packages/plugins/codex-collaboration
uv run pytest tests/test_containment.py -k "test_clean_stale_files_returns_empty_when_shakedown_root_missing or test_clean_stale_files_raises_when_root_lstat_fails or test_clean_stale_files_raises_on_dangling_root_symlink or test_clean_stale_files_raises_when_root_is_not_a_directory or test_clean_stale_files_raises_when_enumeration_fails or test_clean_stale_files_raises_when_root_directory_unreadable" -v
```

Expected: all six PASS (or five PASS + one SKIP if running as root or on Windows — see the skip conditions below).

Diagnostic paths for failures:

- If `test_clean_stale_files_raises_on_dangling_root_symlink` is skipped, the host filesystem does not support symlinks — acceptable on very restricted CI environments, but on macOS/Linux it must PASS.
- If `test_clean_stale_files_raises_when_root_directory_unreadable` is skipped, the test is running as root (POSIX permission bypass) or on a platform without `os.geteuid` (e.g., Windows) — acceptable, because the companion mock-based test still exercises the raise path.
- If `test_clean_stale_files_raises_when_root_lstat_fails` returns an empty result instead of raising, Task 1 Step 5 is using `exists()` or a single-stage stat — re-read Task 1 Step 5 and correct.
- If `test_clean_stale_files_raises_when_enumeration_fails` returns an empty result instead of raising, Task 1 Step 5 is still using `Path.glob()` (or is silently catching `OSError` around `os.listdir`) — re-read Task 1 Step 5 and verify the Stage 3 block is present.
- If `test_clean_stale_files_raises_when_root_directory_unreadable` PASSES by returning an empty result instead of raising, the real `chmod 0o000` path is reaching `Path.glob()` somewhere — Stage 3 is missing entirely. This is the most severe diagnostic class and indicates the Round 3 review finding was not addressed.

- [ ] **Step 3: Commit**

```bash
git add packages/plugins/codex-collaboration/tests/test_containment.py
git commit -m "test(containment): cover whole-sweep failures (root stat and enumeration)"
```

---

## Task 5: Coverage for `CleanStaleResult.report()` including the prefix parameter

**Files:**
- Test: `packages/plugins/codex-collaboration/tests/test_containment.py`

Three tests: clean run (terse single line), failures without prefix, and prefix applied to every line.

- [ ] **Step 1: Add the three report tests**

Add these tests right after Task 4's tests:

```python
def test_clean_stale_result_report_clean_run_is_single_summary_line(
    tmp_path: Path,
) -> None:
    result = containment.CleanStaleResult(
        removed=(tmp_path / "scope-run-1.json",),
        skipped_fresh=(tmp_path / "seed-run-2.json",),
        failed_stat=(),
        failed_unlink=(),
    )
    assert result.report() == "clean_stale_files: removed=1, fresh=1"


def test_clean_stale_result_report_renders_failure_paths_and_errors(
    tmp_path: Path,
) -> None:
    stat_failed = tmp_path / "seed-run-1.json"
    unlink_failed = tmp_path / "transcript-run-1.jsonl"
    result = containment.CleanStaleResult(
        removed=(tmp_path / "scope-run-1.json",),
        skipped_fresh=(),
        failed_stat=((stat_failed, "PermissionError(13, 'denied')"),),
        failed_unlink=((unlink_failed, "PermissionError(13, 'denied')"),),
    )

    lines = result.report().splitlines()

    assert lines[0] == (
        "clean_stale_files: removed=1, fresh=0, failed_stat=1, failed_unlink=1"
    )
    assert lines[1] == f"  failed_stat {stat_failed}: PermissionError(13, 'denied')"
    assert lines[2] == (
        f"  failed_unlink {unlink_failed}: PermissionError(13, 'denied')"
    )
    assert len(lines) == 3


def test_clean_stale_result_report_applies_prefix_to_every_line(
    tmp_path: Path,
) -> None:
    stat_failed = tmp_path / "seed-run-1.json"
    unlink_failed = tmp_path / "transcript-run-1.jsonl"
    result = containment.CleanStaleResult(
        removed=(tmp_path / "scope-run-1.json",),
        skipped_fresh=(),
        failed_stat=((stat_failed, "PermissionError(13, 'denied')"),),
        failed_unlink=((unlink_failed, "PermissionError(13, 'denied')"),),
    )

    lines = result.report(prefix="containment-lifecycle: ").splitlines()

    assert lines[0] == (
        "containment-lifecycle: clean_stale_files: "
        "removed=1, fresh=0, failed_stat=1, failed_unlink=1"
    )
    assert lines[1] == (
        f"containment-lifecycle:   failed_stat {stat_failed}: "
        f"PermissionError(13, 'denied')"
    )
    assert lines[2] == (
        f"containment-lifecycle:   failed_unlink {unlink_failed}: "
        f"PermissionError(13, 'denied')"
    )
    assert len(lines) == 3
    # Regression guard against P3: every report line carries the prefix so
    # caller attribution is not lost when the per-failure lines are grepped
    # or aggregated separately from the summary line.
    for line in lines:
        assert line.startswith("containment-lifecycle:")
```

- [ ] **Step 2: Run the report tests**

```bash
cd packages/plugins/codex-collaboration
uv run pytest tests/test_containment.py -k "test_clean_stale_result_report" -v
```

Expected: all three PASS.

- [ ] **Step 3: Commit**

```bash
git add packages/plugins/codex-collaboration/tests/test_containment.py
git commit -m "test(containment): cover CleanStaleResult.report rendering and prefix"
```

---

## Task 6: Mixed-batch scenario and happy-path tightening

**Files:**
- Test: `packages/plugins/codex-collaboration/tests/test_containment.py`

- [ ] **Step 1: Add the mixed-batch test**

Add this test right after Task 5's tests:

```python
def test_clean_stale_files_mixed_batch_tracks_every_outcome(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    shakedown = containment.shakedown_dir(tmp_path)
    shakedown.mkdir(parents=True)
    removable = shakedown / "scope-run-1.json"
    fresh = shakedown / "seed-run-2.json"
    stat_fails = shakedown / "transcript-run-3.jsonl"
    unlink_fails = shakedown / "transcript-run-4.done"
    for path in (removable, fresh, stat_fails, unlink_fails):
        path.write_text("{}", encoding="utf-8")
    stale_time = time.time() - (26 * 3600)
    os.utime(removable, (stale_time, stale_time))
    os.utime(unlink_fails, (stale_time, stale_time))

    original_stat = Path.stat
    original_unlink = Path.unlink

    def failing_stat(
        self: Path, *args: object, **kwargs: object
    ) -> os.stat_result:
        if self == stat_fails:
            raise PermissionError(13, "denied", str(self))
        return original_stat(self, *args, **kwargs)  # type: ignore[arg-type]

    def failing_unlink(self: Path, *args: object, **kwargs: object) -> None:
        if self == unlink_fails:
            raise PermissionError(13, "denied", str(self))
        return original_unlink(self, *args, **kwargs)  # type: ignore[arg-type]

    with monkeypatch.context() as patched:
        patched.setattr(Path, "stat", failing_stat)
        patched.setattr(Path, "unlink", failing_unlink)
        result = containment.clean_stale_files(shakedown)

    # Patch reverted here — .exists() is safe again.
    assert result.removed == (removable,)
    assert result.skipped_fresh == (fresh,)
    assert len(result.failed_stat) == 1
    assert result.failed_stat[0][0] == stat_fails
    assert len(result.failed_unlink) == 1
    assert result.failed_unlink[0][0] == unlink_fails
    assert result.had_errors is True
    assert "failed_stat=1" in result.report()
    assert "failed_unlink=1" in result.report()
    assert not removable.exists()
    assert fresh.exists()
    assert stat_fails.exists()
    assert unlink_fails.exists()
```

- [ ] **Step 2: Run the mixed-batch test**

```bash
cd packages/plugins/codex-collaboration
uv run pytest tests/test_containment.py::test_clean_stale_files_mixed_batch_tracks_every_outcome -v
```

Expected: PASS.

- [ ] **Step 3: Tighten the existing happy-path test**

Find the existing `test_clean_stale_files_removes_old_state_only` test (around line 191). Replace its body with:

```python
def test_clean_stale_files_removes_old_state_only(tmp_path: Path) -> None:
    shakedown_dir = containment.shakedown_dir(tmp_path)
    shakedown_dir.mkdir(parents=True)
    old_scope = shakedown_dir / "scope-run-1.json"
    old_done = shakedown_dir / "transcript-run-1.done"
    fresh_seed = shakedown_dir / "seed-run-2.json"
    retained_transcript = shakedown_dir / "transcript-run-1.jsonl"
    old_scope.write_text("{}", encoding="utf-8")
    old_done.write_text("", encoding="utf-8")
    fresh_seed.write_text("{}", encoding="utf-8")
    retained_transcript.write_text("[]", encoding="utf-8")

    stale_time = time.time() - (26 * 3600)
    os.utime(old_scope, (stale_time, stale_time))
    os.utime(old_done, (stale_time, stale_time))

    result = containment.clean_stale_files(shakedown_dir)

    assert not old_scope.exists()
    assert not old_done.exists()
    assert fresh_seed.exists()
    assert retained_transcript.exists()
    assert set(result.removed) == {old_scope, old_done}
    assert set(result.skipped_fresh) == {fresh_seed, retained_transcript}
    assert result.failed_stat == ()
    assert result.failed_unlink == ()
    assert result.had_errors is False
```

- [ ] **Step 4: Run the full containment test file**

```bash
cd packages/plugins/codex-collaboration
uv run pytest tests/test_containment.py -v
```

Expected: every test passes.

- [ ] **Step 5: Commit**

```bash
git add packages/plugins/codex-collaboration/tests/test_containment.py
git commit -m "test(containment): cover mixed-batch outcomes and tighten happy path"
```

---

## Task 7: Update `clean_stale_shakedown.py` wrapper

**Files:**
- Modify: `packages/plugins/codex-collaboration/scripts/clean_stale_shakedown.py`

- [ ] **Step 1: Confirm the current wrapper state**

```bash
cat packages/plugins/codex-collaboration/scripts/clean_stale_shakedown.py
```

Expected: lines 38-41 show the delayed import and current call site, untouched by any prior task.

- [ ] **Step 2: Modify the wrapper**

Edit `scripts/clean_stale_shakedown.py`. Find this block:

```python
    from server.containment import clean_stale_files, shakedown_dir

    clean_stale_files(shakedown_dir(data_dir))
    return 0
```

Replace with:

```python
    from server.containment import clean_stale_files, shakedown_dir

    result = clean_stale_files(shakedown_dir(data_dir))
    if result.had_errors:
        print(result.report(), file=sys.stderr)
    return 0
```

No prefix is passed because the wrapper's sole purpose is cleanup — its stderr output is unambiguous without additional attribution. The print is **gated on `had_errors`** so the wrapper is silent on clean runs (Unix convention: tools are silent on success, noisy on error). This preserves the stderr signal: operators who run the wrapper as part of a cleanup script only see output when something actually needs their attention, so they do not learn to discount cleanup stderr. The outer `try/except Exception` at lines 44-52 handles any root-level `OSError` raised by `clean_stale_files`, printing the canonical `"clean_stale_shakedown failed: unexpected error. Got: …"` and exiting `1`.

- [ ] **Step 3: Run file-scoped Ruff**

```bash
cd packages/plugins/codex-collaboration
uv run ruff check scripts/clean_stale_shakedown.py
```

Expected: silent success or `All checks passed!`.

- [ ] **Step 4: Manually verify the happy path**

Use `trash` for cleanup (global CLAUDE.md forbids `rm` and `rm -rf`). Use `rc` not `status` in zsh (gotcha #5 in the resumed handoff).

```bash
cd packages/plugins/codex-collaboration
TEMP_PLUGIN_DATA=$(mktemp -d)
mkdir -p "$TEMP_PLUGIN_DATA/shakedown"
CLAUDE_PLUGIN_DATA="$TEMP_PLUGIN_DATA" uv run python scripts/clean_stale_shakedown.py
rc=$?
echo "exit=$rc"
trash "$TEMP_PLUGIN_DATA"
```

Expected stderr: *(empty — wrapper is silent on clean runs per Choice 3B, Round 5)*
Expected: `exit=0`

- [ ] **Step 5: Manually verify the first-run path (missing shakedown dir)**

```bash
cd packages/plugins/codex-collaboration
TEMP_PLUGIN_DATA=$(mktemp -d)
# Intentionally do NOT create shakedown/ — simulate first run
CLAUDE_PLUGIN_DATA="$TEMP_PLUGIN_DATA" uv run python scripts/clean_stale_shakedown.py
rc=$?
echo "exit=$rc"
trash "$TEMP_PLUGIN_DATA"
```

Expected stderr: *(empty — wrapper is silent on clean runs per Choice 3B, Round 5)*
Expected: `exit=0`

- [ ] **Step 6: Manually verify the dangling-symlink corruption path**

This is the new corruption-surfacing behavior. A dangling symlink should fail loudly, not return empty.

```bash
cd packages/plugins/codex-collaboration
TEMP_PLUGIN_DATA=$(mktemp -d)
ln -s "$TEMP_PLUGIN_DATA/nonexistent-target" "$TEMP_PLUGIN_DATA/shakedown"
CLAUDE_PLUGIN_DATA="$TEMP_PLUGIN_DATA" uv run python scripts/clean_stale_shakedown.py
rc=$?
echo "exit=$rc"
trash "$TEMP_PLUGIN_DATA"
```

Expected stderr contains: `clean_stale_shakedown failed: unexpected error. Got: OSError('clean_stale_files failed: shakedown root is unreadable (possible broken symlink). …')`
Expected: `exit=1`

If stderr is empty and `exit=0`, the dangling symlink is being silently absorbed — Task 1 Step 5 is not using the two-stage `lstat()`/`stat()` pattern. (Note: the wrapper is silent on clean runs after Choice 3B, so a clean-looking stderr on this test is itself the bug signal.) Fix before continuing.

- [ ] **Step 7: Manually verify the unreadable-directory corruption path (chmod 0o000)**

This is the Round-3 enumeration-failure case. The shakedown directory exists, passes `lstat` and `stat`, and is a directory — but cannot be listed because its read bit is cleared. Without the `os.listdir` guard, `Path.glob()` would silently return `[]` and this scenario would look identical to "nothing to clean". After the refactor, it must raise loudly through the wrapper's outer exception boundary.

Skip this step if running as root (POSIX permission checks are bypassed).

```bash
cd packages/plugins/codex-collaboration
TEMP_PLUGIN_DATA=$(mktemp -d)
mkdir "$TEMP_PLUGIN_DATA/shakedown"
echo '{}' > "$TEMP_PLUGIN_DATA/shakedown/scope-run-1.json"
chmod 000 "$TEMP_PLUGIN_DATA/shakedown"
CLAUDE_PLUGIN_DATA="$TEMP_PLUGIN_DATA" uv run python scripts/clean_stale_shakedown.py
rc=$?
echo "exit=$rc"
# Restore permissions so trash can walk into the directory to delete it.
chmod 755 "$TEMP_PLUGIN_DATA/shakedown"
trash "$TEMP_PLUGIN_DATA"
```

Expected stderr contains: `clean_stale_shakedown failed: unexpected error. Got: OSError('clean_stale_files failed: cannot enumerate shakedown root. …')`
Expected: `exit=1`

If stderr is empty and `exit=0`, the enumeration is still going through `Path.glob()` — Task 1 Step 5's Stage 3 (`os.listdir` guard) is missing or incorrectly wrapped in a silent `except` clause. (Note: the wrapper is silent on clean runs after Choice 3B, so a clean-looking stderr on this test is itself the bug signal — before Round 5 this would have been `clean_stale_files: removed=0, fresh=0` unconditionally.) This is the exact silent-success class the Round 3 review identified; do not continue until the output matches the expected raise.

If the `chmod 755` restore step fails with "operation not permitted", you are running as root in a filesystem that rejects the chmod for some reason; rerun without root. The restore is mandatory — without it, `trash` cannot walk into the directory to delete its contents.

- [ ] **Step 8: Manually verify the empty-env and nonexistent-path negative paths still work**

Unchanged T-04 behavior, regression guard only.

```bash
cd packages/plugins/codex-collaboration
unset CLAUDE_PLUGIN_DATA
uv run python scripts/clean_stale_shakedown.py
rc=$?
echo "exit=$rc"
```

Expected stderr: `clean_stale_shakedown failed: CLAUDE_PLUGIN_DATA not set. Got: ''`
Expected: `exit=1`

```bash
cd packages/plugins/codex-collaboration
CLAUDE_PLUGIN_DATA=/tmp/definitely-not-a-real-path-t03 uv run python scripts/clean_stale_shakedown.py
rc=$?
echo "exit=$rc"
```

Expected stderr: `clean_stale_shakedown failed: CLAUDE_PLUGIN_DATA is not a directory. Got: '/tmp/definitely-not-a-real-path-t03'`
Expected: `exit=1`

- [ ] **Step 9: Commit**

```bash
git add packages/plugins/codex-collaboration/scripts/clean_stale_shakedown.py
git commit -m "feat(shakedown): clean_stale_shakedown logs cleanup report to stderr"
```

---

## Task 8: Update internal callers with prefixed attribution + add wiring tests

**Files:**
- Modify: `packages/plugins/codex-collaboration/scripts/containment_lifecycle.py`
- Modify: `packages/plugins/codex-collaboration/scripts/containment_smoke_setup.py`
- Modify: `packages/plugins/codex-collaboration/tests/test_containment_lifecycle.py`
- Create: `packages/plugins/codex-collaboration/tests/test_containment_smoke_setup.py`

Both internal callers have **two distinct error surfaces** that T-03 treats separately:

**Per-file failures** (e.g., `Path.unlink` raising `PermissionError` mid-sweep) — `clean_stale_files` returns a `CleanStaleResult` with `had_errors=True`. Each caller now wraps the call with `if cleanup_result.had_errors:` and logs `cleanup_result.report(prefix="…")` so every line carries caller attribution.

**Root-level failures** (e.g., `chmod 0o000` on the shakedown root, dangling symlink, lstat denied) — `clean_stale_files` raises `OSError` before returning any result. The exception propagates through the caller's entry function (`_handle_subagent_start` or `prepare_scenario`) and is caught by the caller's outer exception boundary, which has a **different contract shape per caller**:

| Caller | Outer boundary | stderr wrapper | Exit code | Intent |
|---|---|---|---|---|
| `containment_lifecycle.py` | `main()` at lines 184-188 | `containment-lifecycle: internal error (<exc>)` | `0` | **Fail-OPEN** — see the Fail-Open Hook Policy design decision. `SubagentStart` treats non-zero as "block the spawn"; a containment-state defect must not escalate into blocking unrelated agent spawns. |
| `containment_smoke_setup.py` | `__main__` at lines 505-510 | `containment_smoke_setup failed: <exc>` | `1` | **Fail-FAST** — the smoke-setup script is a developer/operator tool invoked directly (not by a hook runner). Loud failure is the correct default. |

Root-level raises **do not go through `report(prefix=…)`** — `report()` is a method on `CleanStaleResult`, which does not exist when the helper raises before returning. Instead, each caller's outer boundary produces its own wrapper message using the strings above. Any documentation or assertion that says "all three callers print `report()` on error" is wrong at the root-level surface (Round 5 drift fix).

The wiring tests in this task cover both error surfaces, but at **different layers**:

- **Per-file surface** (seam-level coverage) — in-process tests via `_load_lifecycle_module()` and `_load_smoke_setup_module()` that monkeypatch `Path.unlink` to force `had_errors=True`, call the caller's **seam function** (`_handle_subagent_start`, `prepare_scenario`) directly, and assert on `capsys`-captured stderr. These pin the `if cleanup_result.had_errors:` gate and `report(prefix=...)` rendering **at the seam** — they do NOT exercise `main()` or `__main__` and therefore do NOT pin outer-boundary behavior for the per-file path. No additional outer-boundary regression is required for the per-file path because that path returns normally and does not cross the exception boundary. Without these seam tests, the plan's verification would pass even if the new logging block were accidentally deleted.

- **Root-level surface** (outer-boundary coverage) — **two tests per caller** (four total), pinning the **outer exception boundary** for each caller's contract shape on every platform:
  - **Lifecycle (fail-OPEN, exit 0)**: `test_subagent_start_surfaces_cleanup_enumeration_failure` (subprocess via `_run_lifecycle` using real `chmod 0o000`, authoritative end-to-end proof on non-root POSIX; SKIPs on root/Windows) + `test_main_fail_open_conversion_via_monkeypatched_listdir` (Round 5 platform-agnostic in-process fallback calling `main()` directly with monkeypatched `os.listdir`, runs on every platform).
  - **Smoke-setup (fail-FAST, exit 1)**: `test_prepare_scenario_surfaces_cleanup_enumeration_failure` (subprocess via `_run_smoke_setup` using real `chmod 0o000`, authoritative end-to-end proof on non-root POSIX; SKIPs on root/Windows) + `test_prepare_scenario_main_wrapper_fail_fast_via_monkeypatched_listdir` (Round 6 platform-agnostic in-process fallback calling the extracted `_run_with_wrapper(argv)` function directly with monkeypatched `os.listdir`, runs on every platform).

These four tests pin the **two different outer-boundary contract shapes** in the table above — a root-level failure regression in either caller cannot ship with every other T-03 test passing, and root/Windows CI runs still have automated coverage of both contract shapes via the in-process fallbacks. The Round 6 smoke-setup in-process fallback is enabled by a behavior-preserving testability refactor that extracts the `__main__` block's try/except into a module-level `_run_with_wrapper(argv)` function — see Task 8 Step 2 for the refactor and the Round 6 Resolution Map entry for the rationale.

- [ ] **Step 1: Update `containment_lifecycle.py:73`**

In `scripts/containment_lifecycle.py`, find this block inside `_handle_subagent_start` (starts at line 72):

```python
    clean_stale_files(shakedown_dir(data_dir))
    run_id = read_active_run_id(data_dir, session_id)
```

Replace with:

```python
    cleanup_result = clean_stale_files(shakedown_dir(data_dir))
    if cleanup_result.had_errors:
        _log_error(cleanup_result.report(prefix="containment-lifecycle: "))
    run_id = read_active_run_id(data_dir, session_id)
```

The existing `_log_error` helper at lines 43-44 writes to stderr. No new imports needed.

- [ ] **Step 2: Update `containment_smoke_setup.py:118`**

In `scripts/containment_smoke_setup.py`, find this block inside `prepare_scenario` (starts at line 118):

```python
    clean_stale_files(shakedown_dir(data_dir))
    resolved_session_id = session_id or _read_session_id(data_dir)
```

Replace with:

```python
    cleanup_result = clean_stale_files(shakedown_dir(data_dir))
    if cleanup_result.had_errors:
        print(
            cleanup_result.report(prefix="containment_smoke_setup: "),
            file=sys.stderr,
        )
    resolved_session_id = session_id or _read_session_id(data_dir)
```

`sys` is already imported at line 9.

Also refactor the `__main__` block to expose the fail-fast wrapper as a testable function (Round 6 Option C — behavior-preserving testability refactor). Find this block at lines 505-510 of `scripts/containment_smoke_setup.py`:

```python
if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"containment_smoke_setup failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
```

Replace with:

```python
def _run_with_wrapper(argv: list[str] | None = None) -> None:
    """Call ``main()`` and apply the fail-fast wrapper.

    Extracted from the ``__main__`` block so the wrapper is testable
    in-process via direct call (Round 6 testability refactor).
    **Behavior-preserving**: same stderr text
    (``containment_smoke_setup failed: <exc>``), same ``SystemExit(1)``
    on any exception from ``main(argv)``, and same ``SystemExit(main(argv))``
    happy-path exit for normal flow. The only structural change is that the
    ``__main__`` block now dispatches through a callable function so tests
    can exercise the full wrapper boundary without spawning a subprocess.
    """
    try:
        raise SystemExit(main(argv))
    except Exception as exc:
        print(f"containment_smoke_setup failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    _run_with_wrapper()
```

**Why this is a refactor and not a contract change** — the `__main__` behavior is bit-for-bit identical:

- **Happy path** — `main(argv)` returns normally → `raise SystemExit(main(argv))` fires with the returned exit code. `SystemExit` inherits from `BaseException`, not `Exception`, so the `except Exception` does NOT catch it; the `SystemExit(N)` propagates up through `_run_with_wrapper()` and out to the Python runtime, producing exit code `N` — same as before.
- **Exception path** — `main(argv)` raises → `raise SystemExit(main(argv))` never reaches the `SystemExit` side because `main(argv)` raises first; the `except Exception` catches it, prints `containment_smoke_setup failed: <exc>` to stderr, and raises `SystemExit(1) from exc` — same stderr text, same exit code, same exception chaining as before.

The refactor's sole purpose is testability: the wrapper is now callable as `smoke_setup._run_with_wrapper(argv)`, which enables the Round 6 in-process fallback test in Step 5 to exercise the full wrapper boundary on every platform — including root and Windows, where the subprocess `chmod 0o000` test skips. See the Round 6 Resolution Map entry for the motivation and the asymmetry it resolves (lifecycle's `main()` is already callable because the fail-open boundary is inside `main()` itself; smoke-setup's fail-FAST boundary was trapped in the `__main__` guard block and was therefore only reachable via subprocess).

- [ ] **Step 3: Add the three lifecycle caller-wiring tests**

Three tests go in `tests/test_containment_lifecycle.py`:

1. **In-process seam test** (`test_subagent_start_logs_cleanup_errors_with_lifecycle_prefix`) — uses `_load_lifecycle_module` to call `_handle_subagent_start` directly with monkeypatched `Path.unlink`. Pins the per-file `had_errors=True` → `report(prefix=...)` wiring **at the seam**. Does NOT touch `main()` and therefore does NOT pin outer-boundary behavior — that is covered by the next two tests.
2. **Subprocess outer-boundary test** (`test_subagent_start_surfaces_cleanup_enumeration_failure`) — uses `_run_lifecycle` to invoke the script via `subprocess.run` with a real `chmod 0o000` on the shakedown directory. Exercises the full `main()` boundary including the fail-open `except Exception → return 0` conversion. Authoritative end-to-end proof on non-root POSIX; SKIPs on root/Windows.
3. **In-process outer-boundary fallback** (`test_main_fail_open_conversion_via_monkeypatched_listdir`, Round 5) — calls `main()` directly with monkeypatched `os.listdir`, `sys.stdin`, and `CLAUDE_PLUGIN_DATA`. Pins the same fail-open exception-to-exit-code conversion contract as the subprocess test but runs on every platform regardless of `os.geteuid` availability, so root and Windows CI still have automated coverage when the subprocess test skips.

The subprocess pattern is mandatory for test #2 to exercise the REAL OS-level boundary (argv parsing, `sys.executable` resolution, `SystemExit` raised by `raise SystemExit(main())`) on supported platforms. Test #3 is the platform-agnostic fallback that pins the language-level fail-open conversion where test #2 cannot run.

Add these imports (if missing) and all three tests. The file already imports `os` and `subprocess`; `time` and `pytest` may need to be added at the top with the other imports:

```python
# Verify these imports are present at the top of test_containment_lifecycle.py;
# add any that are missing. `io` and `json` are new in Round 5 for the
# in-process fallback test. `json` may already be present (it is used by
# `_run_lifecycle` below); verify and add if missing. `subprocess` and `sys`
# should already be present (also used by `_run_lifecycle`).
import io
import json
import os
import time
from pathlib import Path

import pytest

from server import containment
```

Then add this test at the end of the file:

```python
def test_subagent_start_logs_cleanup_errors_with_lifecycle_prefix(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Force a per-file unlink failure during _handle_subagent_start's cleanup
    step and verify the lifecycle caller logs the cleanup report via _log_error
    with the ``containment-lifecycle:`` prefix on every reported line.

    **Pins the per-file surface at the seam, not the outer boundary**: this
    test calls ``_handle_subagent_start`` directly and never touches
    ``main()``, so it does not exercise the fail-open exception-to-exit-code
    conversion. That contract is pinned by
    ``test_subagent_start_surfaces_cleanup_enumeration_failure`` (subprocess)
    and ``test_main_fail_open_conversion_via_monkeypatched_listdir`` (Round 5
    in-process fallback).

    Uses the in-process importlib pattern so Path.unlink can be monkeypatched.
    """

    lifecycle = _load_lifecycle_module()

    shakedown = containment.shakedown_dir(tmp_path)
    shakedown.mkdir(parents=True)
    stale = shakedown / "scope-run-1.json"
    stale.write_text("{}", encoding="utf-8")
    stale_time = time.time() - (26 * 3600)
    os.utime(stale, (stale_time, stale_time))

    original_unlink = Path.unlink

    def failing_unlink(self: Path, *args: object, **kwargs: object) -> None:
        if self == stale:
            raise PermissionError(13, "denied", str(self))
        return original_unlink(self, *args, **kwargs)  # type: ignore[arg-type]

    payload = {
        "hook_event_name": "SubagentStart",
        "session_id": "session-1",
        "agent_id": "agent-1",
    }

    with monkeypatch.context() as patched:
        patched.setattr(Path, "unlink", failing_unlink)
        lifecycle._handle_subagent_start(payload, data_dir=tmp_path)

    captured = capsys.readouterr()

    # Regression guard against P1 (caller ignoring had_errors) and P3
    # (multi-line report losing caller attribution after the first line).
    assert "containment-lifecycle:" in captured.err, (
        "caller must log cleanup report when had_errors is True"
    )
    assert "failed_unlink=1" in captured.err
    assert str(stale) in captured.err
    assert "PermissionError" in captured.err

    report_lines = [
        line
        for line in captured.err.splitlines()
        if "clean_stale_files:" in line or "failed_unlink" in line
    ]
    assert len(report_lines) >= 2, (
        "expected at least a summary line and one failure line; "
        f"got: {report_lines!r}"
    )
    for line in report_lines:
        assert line.startswith("containment-lifecycle:"), (
            f"every report line must carry caller attribution; got: {line!r}"
        )


@pytest.mark.skipif(
    not hasattr(os, "geteuid") or os.geteuid() == 0,
    reason=(
        "POSIX permission check: chmod 0o000 is bypassed by root "
        "and unavailable on platforms without os.geteuid"
    ),
)
def test_subagent_start_surfaces_cleanup_enumeration_failure(
    tmp_path: Path,
) -> None:
    """Root-level cleanup failure surfaces through ``main()``'s fail-open boundary.

    Real ``chmod 0o000`` on the shakedown directory makes ``clean_stale_files``
    raise ``OSError('clean_stale_files failed: cannot enumerate shakedown
    root. …')`` from Stage 3. That exception propagates out of
    ``_handle_subagent_start``, out of ``handle_payload``, and is caught by
    ``main()``'s outer ``except Exception`` block at lines 184-188 of
    ``containment_lifecycle.py``, which logs ``containment-lifecycle:
    internal error (<exc>)`` to stderr and returns ``0``.

    This test locks in the deliberate fail-open policy: the hook returns
    ``0`` (so the hook runner never sees a failed hook and unrelated agent
    spawns are not blocked by a containment-state defect), BUT stderr must
    contain both the lifecycle caller prefix and the actionable
    cleanup-failure context so an operator reading stderr can identify
    which failure class occurred. See the **Fail-Open Hook Policy** design
    decision in the plan for the full contract.

    The subprocess pattern is mandatory here: an in-process call to
    ``_handle_subagent_start`` would bypass ``main()``'s outer try/except
    and therefore could not observe the exception-to-exit-code conversion,
    which is exactly the contract under test.

    Skipped when running as root (POSIX permission checks are bypassed)
    or on platforms without ``os.geteuid`` (e.g., Windows).
    """
    shakedown = tmp_path / "shakedown"
    shakedown.mkdir(parents=True)
    (shakedown / "scope-run-1.json").write_text("{}", encoding="utf-8")

    try:
        os.chmod(shakedown, 0o000)
        result = _run_lifecycle(
            {
                "hook_event_name": "SubagentStart",
                "session_id": "session-1",
                "agent_id": "agent-1",
            },
            data_dir=tmp_path,
        )
    finally:
        # Restore permissions so pytest's tmp_path teardown can walk
        # into the directory. This MUST happen even if the assertions
        # below fail, otherwise tmp_path cleanup raises and masks the
        # real failure.
        os.chmod(shakedown, 0o755)

    # Fail-open contract: the hook runner does NOT see a failed hook.
    assert result.returncode == 0, (
        "lifecycle hook must fail open on internal errors; "
        f"got exit={result.returncode}, stderr={result.stderr!r}"
    )
    # Observability contract: stderr contains caller attribution AND the
    # specific cleanup-failure context from clean_stale_files.
    assert "containment-lifecycle: internal error" in result.stderr, (
        "main() must wrap internal errors with its caller prefix; "
        f"got stderr={result.stderr!r}"
    )
    assert "cannot enumerate shakedown root" in result.stderr, (
        "wrapped error must carry the clean_stale_files failure context "
        f"(Stage 3 enumeration); got stderr={result.stderr!r}"
    )


def test_main_fail_open_conversion_via_monkeypatched_listdir(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Platform-agnostic proof that ``main()``'s fail-open boundary converts a
    cleanup ``OSError`` to ``return 0`` + caller-prefixed stderr context.

    This test complements (does not replace)
    ``test_subagent_start_surfaces_cleanup_enumeration_failure``, which uses a
    real ``chmod 0o000`` + subprocess for the end-to-end proof. The
    subprocess test is the authoritative end-to-end proof WHEN the platform
    supports it (non-root POSIX with ``os.geteuid``); when that test SKIPs
    (root or Windows), this in-process fallback still pins the ``main()``-
    level fail-open conversion contract via monkeypatched ``os.listdir``.

    Why both tests are necessary (Round 5 resolution):

    - The subprocess test exercises the REAL OS-level subprocess boundary
      including argv parsing, env-var lookup, stdin JSON decoding, and the
      ``SystemExit`` raised by ``raise SystemExit(main())``. That end-to-end
      behavior cannot be proven by an in-process call.
    - This in-process test runs on every platform regardless of ``geteuid``
      availability, ensuring root and Windows still have automated coverage
      of the specific ``exception → return 0 + stderr log`` conversion at
      ``main()`` lines 184-188.

    Together they pin the fail-open contract under both platform conditions.
    Without this in-process fallback, root and Windows CI runs had no
    automated proof of the ``main()`` fail-open conversion at all — only the
    helper-level enumeration test would run, and that tests the helper
    directly, not through the caller boundary.

    Runs on every platform (no skipif).
    """
    data_dir = tmp_path
    shakedown = containment.shakedown_dir(data_dir)
    shakedown.mkdir(parents=True)
    (shakedown / "scope-run-1.json").write_text("{}", encoding="utf-8")

    def _raising_listdir(path: object) -> list[str]:
        raise PermissionError(13, "Permission denied", str(path))

    payload_json = json.dumps(
        {
            "hook_event_name": "SubagentStart",
            "session_id": "session-1",
            "agent_id": "agent-1",
        }
    )

    lifecycle = _load_lifecycle_module()

    # Patch os.listdir, CLAUDE_PLUGIN_DATA env var, and sys.stdin in a
    # ``monkeypatch.context()`` block so the patches revert immediately
    # after ``main()`` returns. Constraint #6 in the Key correctness
    # constraints list requires every monkeypatch in this plan to be
    # scoped to a ``with monkeypatch.context()`` block so the patches do
    # not leak into other tests or into ``capsys.readouterr()`` below.
    #
    # The ``os.listdir`` patch works because ``containment.py`` uses
    # ``import os; os.listdir(...)`` (attribute lookup at call time), not
    # ``from os import listdir`` (reference captured at import time). If
    # a future refactor changes the import style in ``containment.py``,
    # this monkeypatch target becomes wrong — see Task 8 Step 4 diagnostic
    # paths for the recovery hint.
    with monkeypatch.context() as patched:
        patched.setattr("os.listdir", _raising_listdir)
        patched.setenv("CLAUDE_PLUGIN_DATA", str(data_dir))
        patched.setattr("sys.stdin", io.StringIO(payload_json))
        exit_code = lifecycle.main()

    captured = capsys.readouterr()

    # Fail-open conversion: main() returns 0 even though clean_stale_files
    # raised.
    assert exit_code == 0, (
        "main() must convert cleanup OSError to return 0 (fail-open); "
        f"got exit_code={exit_code!r}, stderr={captured.err!r}"
    )
    # Caller prefix + actionable context: operator reading stderr can
    # identify which failure class occurred.
    assert "containment-lifecycle: internal error" in captured.err, (
        "main() must wrap internal errors with its caller prefix; "
        f"got stderr={captured.err!r}"
    )
    assert "cannot enumerate shakedown root" in captured.err, (
        "wrapped error must carry the clean_stale_files failure context "
        f"(Stage 3 enumeration); got stderr={captured.err!r}"
    )
```

- [ ] **Step 4: Run all three lifecycle caller-wiring tests**

```bash
cd packages/plugins/codex-collaboration
uv run pytest \
  tests/test_containment_lifecycle.py::test_subagent_start_logs_cleanup_errors_with_lifecycle_prefix \
  tests/test_containment_lifecycle.py::test_subagent_start_surfaces_cleanup_enumeration_failure \
  tests/test_containment_lifecycle.py::test_main_fail_open_conversion_via_monkeypatched_listdir \
  -v
```

Expected:

- The in-process per-file test PASSES on every platform.
- The subprocess chmod test PASSES on non-root POSIX with `os.geteuid`; SKIPs if running as root or on Windows.
- The in-process fallback test PASSES on every platform regardless of `os.geteuid` (no skipif — the fallback's entire purpose is to guarantee coverage when the subprocess test skips).

Diagnostic paths for failures:

- If the in-process test FAILS with `containment-lifecycle:` missing from stderr, Step 1's caller update was not applied.
- If the in-process test FAILS because only the first line has the prefix and later lines do not, Task 1 Step 4's `report()` method is not applying the prefix to every line — re-read the method body in Task 1 Step 4 and verify every `lines.append(...)` call prefixes with `{prefix}`.
- If the subprocess test FAILS with a non-zero return code, the fail-open policy in `containment_lifecycle.py:main()` has been inadvertently changed; check whether the outer `except Exception` block at lines 184-188 still exists and still returns `0`.
- If the subprocess test FAILS because stderr contains `containment-lifecycle: clean_stale_files: removed=0` instead of `containment-lifecycle: internal error`, the Stage 3 enumeration guard in Task 1 Step 5 is missing (or silently wrapped in `except OSError: pass`) and the `chmod 0o000` path is being swallowed before it reaches `main()`'s except block. This is the Round 3 / Round 4 silent-success regression; do not proceed until fixed.
- If the subprocess test FAILS because stderr is missing `cannot enumerate shakedown root`, Task 1 Step 5 is raising a different error message than the plan specifies — re-read the Stage 3 block and verify the `raise OSError(f"clean_stale_files failed: cannot enumerate shakedown root. …")` formatting is literal.
- If the **in-process fallback test FAILS with `exit_code != 0`**, the fail-open policy has been inadvertently changed in `containment_lifecycle.py:main()`. Same diagnostic as the subprocess test: check the outer `except Exception` block at lines 184-188.
- If the **in-process fallback test FAILS because stderr is empty** (no `containment-lifecycle: internal error` line), the `monkeypatch.setattr("os.listdir", _raising_listdir)` is not taking effect. Two likely causes: (a) `containment.py` was refactored to use `from os import listdir` instead of `os.listdir`, making the attribute-lookup patch a no-op — in that case, patch `containment.os.listdir` directly, or revert the import style; (b) the test loads a cached `_load_lifecycle_module()` result that was imported before the patch was applied — use `monkeypatch.setattr` BEFORE calling `_load_lifecycle_module()`, not after.
- If the **in-process fallback test FAILS with `json.decoder.JSONDecodeError`** from inside `main()`, the `monkeypatch.setattr("sys.stdin", io.StringIO(payload_json))` is not taking effect. Verify that the monkeypatch is applied before `lifecycle.main()` is called and that `payload_json` is valid JSON.
- If the **in-process fallback test FAILS because stderr contains `containment-lifecycle: clean_stale_files: removed=0`** (instead of `containment-lifecycle: internal error`), the monkeypatched `os.listdir` is being bypassed entirely because Task 1 Step 5's Stage 3 path is not actually calling `os.listdir` — it may still be using `Path.glob()` or `os.scandir()`. Re-read the Stage 3 block in Task 1 Step 5.

- [ ] **Step 5: Create `tests/test_containment_smoke_setup.py`**

Create a new file at `tests/test_containment_smoke_setup.py` with this exact content. Note the direct seam: instead of relying on `scenario_id="scope_file_remove"` + `run_id=None` to trigger a scenario-specific `RuntimeError` (which is fragile to refactors that validate `scope_file_remove` earlier or rename the scenario), the test monkeypatches `smoke_setup._scenario_definition` to raise a sentinel `RuntimeError` **after** `clean_stale_files()` has already run and logged. The cleanup step is at the very top of `prepare_scenario` (line 118), before `_read_session_id`, `_assert_no_live_conflict`, or any scenario-specific validation, so by the time the stub raises, the cleanup's stderr output is already captured. This tests the stable contract ("cleanup runs first, then logging happens") rather than the current choreography of any individual scenario.

```python
"""Tests for containment_smoke_setup.py caller behavior."""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from server import containment

SCRIPT = str(
    Path(__file__).resolve().parent.parent
    / "scripts"
    / "containment_smoke_setup.py"
)


def _load_smoke_setup_module():
    spec = importlib.util.spec_from_file_location(
        "test_containment_smoke_setup_module",
        SCRIPT,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run_smoke_setup(argv: list[str]) -> subprocess.CompletedProcess[str]:
    """Invoke the smoke-setup script as a subprocess.

    Captures stdout and stderr as text for assertion. Uses ``sys.executable``
    so the test inherits pytest's Python environment. Deliberately does not
    pass ``env=`` — the caller is expected to use ``--data-dir`` for data
    directory override, so the subprocess inherits the parent environment.

    Used by ``test_prepare_scenario_surfaces_cleanup_enumeration_failure``
    (added in Round 5) to pin smoke-setup's fail-FAST ``__main__`` wrapper
    contract for root-level cleanup failures.
    """
    return subprocess.run(
        [sys.executable, SCRIPT, *argv],
        capture_output=True,
        text=True,
    )


def test_prepare_scenario_logs_cleanup_errors_with_smoke_setup_prefix(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Force a per-file unlink failure during prepare_scenario's cleanup step
    and verify the smoke-setup caller logs the cleanup report to stderr with
    the ``containment_smoke_setup:`` prefix on every reported line.

    **Pins the per-file surface at the seam, not the outer boundary**: this
    test calls ``prepare_scenario`` directly and never touches ``main()`` or
    the ``__main__`` fail-fast wrapper, so it does not exercise the
    exception-to-exit conversion. That contract is pinned by
    ``test_prepare_scenario_surfaces_cleanup_enumeration_failure`` (Round 5
    subprocess) and
    ``test_prepare_scenario_main_wrapper_fail_fast_via_monkeypatched_listdir``
    (Round 6 in-process fallback via the extracted ``_run_with_wrapper()``
    testability refactor).

    Uses a **direct seam** to decouple the test from scenario choreography:
    monkeypatches ``smoke_setup._scenario_definition`` to raise a sentinel
    ``RuntimeError`` *after* the cleanup step has already run and logged.
    This tests the stable contract ("cleanup runs first, then logging
    happens, then any later failure terminates") rather than any specific
    scenario's validation path.

    The older version of this test used ``scenario_id="scope_file_remove"``
    with ``run_id=None`` to trigger a scenario-specific ``RuntimeError``,
    but that coupled the test to a single scenario's validation ordering —
    a harmless refactor that validated ``scope_file_remove`` earlier (or
    renamed the scenario) would have broken the test even if the cleanup
    wiring was still correct. See the Round 4 review resolution for the
    full rationale.

    RepoPaths is constructed directly with non-existent paths because
    ``_scenario_definition`` is stubbed and never evaluates
    ``repo_paths.file_anchors`` or ``repo_paths.scope_directories``; the
    dataclass fields only need to be ``Path`` objects to satisfy the type
    annotations at construction time.
    """

    smoke_setup = _load_smoke_setup_module()

    shakedown = containment.shakedown_dir(tmp_path)
    shakedown.mkdir(parents=True)
    stale = shakedown / "scope-run-1.json"
    stale.write_text("{}", encoding="utf-8")
    stale_time = time.time() - (26 * 3600)
    os.utime(stale, (stale_time, stale_time))

    original_unlink = Path.unlink

    def failing_unlink(self: Path, *args: object, **kwargs: object) -> None:
        if self == stale:
            raise PermissionError(13, "denied", str(self))
        return original_unlink(self, *args, **kwargs)  # type: ignore[arg-type]

    # The stub terminates prepare_scenario *after* cleanup runs, before any
    # scenario-specific validation. The sentinel message is deliberately
    # generic so the assertion does not accidentally re-couple to a real
    # scenario's error text.
    def raising_scenario_definition(
        scenario_id: str, *, repo_paths: object
    ) -> dict[str, object]:
        raise RuntimeError("smoke-setup wiring test termination sentinel")

    # Minimal RepoPaths — never evaluated because _scenario_definition is
    # stubbed. Fields must still be Path objects to satisfy the dataclass
    # type annotations, but the target paths do not need to exist because
    # we construct RepoPaths directly (bypassing _repo_paths() which calls
    # path.exists() on every field).
    fake_repo = tmp_path / "fake-repo"
    repo_paths = smoke_setup.RepoPaths(
        repo_root=fake_repo,
        contracts=fake_repo / "contracts.md",
        delivery=fake_repo / "delivery.md",
        foundations=fake_repo / "foundations.md",
        mcp_server=fake_repo / "mcp_server.py",
        dialogue=fake_repo / "dialogue.py",
        out_of_scope=fake_repo / "out_of_scope.py",
    )

    with monkeypatch.context() as patched:
        patched.setattr(Path, "unlink", failing_unlink)
        patched.setattr(
            smoke_setup, "_scenario_definition", raising_scenario_definition
        )
        with pytest.raises(
            RuntimeError, match="smoke-setup wiring test termination sentinel"
        ):
            smoke_setup.prepare_scenario(
                # scenario_id does not matter — _scenario_definition is
                # stubbed. The string is only here because prepare_scenario
                # passes it through to the stub.
                scenario_id="wiring-test-any-id",
                data_dir=tmp_path,
                # session_id is explicit so _read_session_id is never called
                # (the `session_id or _read_session_id(data_dir)` short-circuit
                # returns the explicit value without touching the filesystem).
                session_id="wiring-test-session",
                # run_id is explicit so uuid.uuid4() is not called and the
                # test remains deterministic.
                run_id="wiring-test-run",
                repo_paths=repo_paths,
            )

    captured = capsys.readouterr()

    # Regression guard against P1 (caller ignoring had_errors) and P3
    # (multi-line report losing caller attribution after the first line).
    assert "containment_smoke_setup:" in captured.err, (
        "caller must log cleanup report when had_errors is True"
    )
    assert "failed_unlink=1" in captured.err
    assert str(stale) in captured.err
    assert "PermissionError" in captured.err

    report_lines = [
        line
        for line in captured.err.splitlines()
        if "clean_stale_files:" in line or "failed_unlink" in line
    ]
    assert len(report_lines) >= 2, (
        "expected at least a summary line and one failure line; "
        f"got: {report_lines!r}"
    )
    for line in report_lines:
        assert line.startswith("containment_smoke_setup:"), (
            f"every report line must carry caller attribution; got: {line!r}"
        )


@pytest.mark.skipif(
    not hasattr(os, "geteuid") or os.geteuid() == 0,
    reason=(
        "POSIX permission check: chmod 0o000 is bypassed by root "
        "and unavailable on platforms without os.geteuid"
    ),
)
def test_prepare_scenario_surfaces_cleanup_enumeration_failure(
    tmp_path: Path,
) -> None:
    """Root-level cleanup failure surfaces through smoke-setup's ``__main__``
    **fail-FAST** boundary.

    Real ``chmod 0o000`` on the shakedown directory makes ``clean_stale_files``
    raise ``OSError('clean_stale_files failed: cannot enumerate shakedown
    root. …')`` from Stage 3. That exception propagates out of
    ``prepare_scenario``, out of ``main()``, and is caught by the ``__main__``
    wrapper at ``containment_smoke_setup.py:505-510``, which prints
    ``"containment_smoke_setup failed: <exc>"`` to stderr and raises
    ``SystemExit(1)``.

    This is the smoke-setup counterpart to
    ``test_subagent_start_surfaces_cleanup_enumeration_failure`` in
    ``test_containment_lifecycle.py`` — it pins smoke-setup's fail-FAST
    contract (exit ``1``, outer wrapper stderr prefix
    ``"containment_smoke_setup failed:"``) in explicit contrast to
    lifecycle's fail-OPEN contract (exit ``0``, stderr prefix
    ``"containment-lifecycle: internal error"``). Without this test, a
    regression that changes smoke-setup's wrapper exception-handling could
    ship with every other T-03 test passing — the helper-level enumeration
    tests would pass, the lifecycle boundary tests would pass, and the
    per-file smoke-setup wiring test above would pass, but smoke-setup's
    caller boundary would be unpinned. Round 5 added this test to close
    that gap.

    Coupling note (Round 5 resolution): the ``prepare`` command requires
    ``--repo-root`` for ``_repo_paths()`` validation against B1 fixture
    files (``docs/superpowers/specs/codex-collaboration/contracts.md``,
    ``delivery.md``, ``foundations.md``, ``packages/.../mcp_server.py``,
    etc.). The repo root is derived from the test file's own location via
    ``Path(__file__).resolve().parents[4]``, which stays within the same
    filesystem-layout coupling class as the existing ``SCRIPT`` constant
    (``SCRIPT`` already uses ``Path(__file__).parent.parent / "scripts" /
    ...``). Deriving the repo root from the test file location is
    deliberately preferred over ``subprocess.check_output(["git",
    "rev-parse", ...])`` so the test does not introduce a new external
    dependency at test-setup time. If any B1 fixture file is moved or
    renamed, this test will fail with ``"resolve repo paths failed:
    required B1 fixture paths missing"`` — see Task 8 Step 6 diagnostic
    paths for the recovery procedure.

    Skipped when running as root (POSIX permission checks are bypassed)
    or on platforms without ``os.geteuid`` (e.g., Windows).
    """
    repo_root = Path(__file__).resolve().parents[4]
    shakedown = tmp_path / "shakedown"
    shakedown.mkdir(parents=True)
    (shakedown / "scope-run-1.json").write_text("{}", encoding="utf-8")

    try:
        os.chmod(shakedown, 0o000)
        result = _run_smoke_setup(
            [
                "--data-dir", str(tmp_path),
                "--repo-root", str(repo_root),
                "prepare", "scope_file_remove",
                "--session-id", "wiring-test-session",
                "--run-id", "wiring-test-run",
            ],
        )
    finally:
        # Restore permissions so pytest's tmp_path teardown can walk
        # into the directory. This MUST happen even if the assertions
        # below fail, otherwise tmp_path cleanup raises and masks the
        # real failure.
        os.chmod(shakedown, 0o755)

    # Fail-FAST contract: smoke-setup exits 1 on any internal error (the
    # opposite of lifecycle's fail-OPEN exit 0). This is deliberate — the
    # smoke-setup script is a developer/operator tool invoked directly,
    # not a hook, so loud failure is the correct default.
    assert result.returncode == 1, (
        "smoke-setup must fail-fast on root-level cleanup failure (exit 1); "
        f"got exit={result.returncode}, stdout={result.stdout!r}, "
        f"stderr={result.stderr!r}"
    )
    # Outer-boundary contract: stderr carries the __main__ wrapper prefix.
    assert "containment_smoke_setup failed" in result.stderr, (
        "__main__ wrapper must wrap internal errors with its caller prefix; "
        f"got stderr={result.stderr!r}"
    )
    # Observability contract: the wrapped exception carries the Stage 3
    # enumeration failure context from clean_stale_files.
    assert "cannot enumerate shakedown root" in result.stderr, (
        "wrapped error must carry the clean_stale_files failure context "
        f"(Stage 3 enumeration); got stderr={result.stderr!r}"
    )


def test_prepare_scenario_main_wrapper_fail_fast_via_monkeypatched_listdir(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Platform-agnostic proof that smoke-setup's ``_run_with_wrapper``
    fail-FAST boundary converts a cleanup ``OSError`` to ``SystemExit(1)`` +
    wrapper-prefixed stderr.

    This test complements (does not replace)
    ``test_prepare_scenario_surfaces_cleanup_enumeration_failure``, which
    uses a real ``chmod 0o000`` + subprocess for the end-to-end proof. The
    subprocess test is the authoritative end-to-end proof WHEN the platform
    supports it (non-root POSIX with ``os.geteuid``); when that test SKIPs
    (root or Windows), this in-process fallback still pins the
    language-level wrapper conversion contract at
    ``containment_smoke_setup._run_with_wrapper()``.

    Parallels ``test_main_fail_open_conversion_via_monkeypatched_listdir``
    in ``test_containment_lifecycle.py`` — same pattern (monkeypatched
    ``os.listdir``, direct in-process call, ``monkeypatch.context()``
    scoping), different contract shape: fail-FAST ``SystemExit(1)`` with
    ``containment_smoke_setup failed:`` prefix, not lifecycle's fail-OPEN
    ``return 0``. Both in-process fallbacks together pin the two different
    outer-boundary contract shapes on every platform regardless of
    ``os.geteuid`` availability.

    Why this fallback requires a refactor (Round 6 resolution): lifecycle's
    fail-OPEN boundary is inside ``main()`` itself, so calling
    ``lifecycle.main()`` directly exercises it. Smoke-setup's fail-FAST
    boundary was originally in the ``__main__`` guard block — structurally
    unreachable from an in-process test. Round 6 extracted the ``__main__``
    try/except into ``smoke_setup._run_with_wrapper(argv)`` as a
    **behavior-preserving refactor** (same stderr text, same
    ``SystemExit(1)`` on exception, same happy-path
    ``SystemExit(main(argv))``). The wrapper is now callable from this
    test, closing the platform-gating gap without weakening the Round 5
    promise that a smoke-setup root-failure regression cannot ship with
    every other T-03 test passing.

    Coupling note: the ``prepare`` command requires ``--repo-root`` for
    ``_repo_paths()`` validation against B1 fixture files, so the test
    must provide a valid repo root even though the test never reaches
    ``prepare_scenario`` choreography (the monkeypatched ``os.listdir``
    raises during ``clean_stale_files`` earlier in ``prepare_scenario``).
    The repo root is derived from the test file's own location via
    ``Path(__file__).resolve().parents[4]``, staying within the same
    filesystem-layout coupling class as the existing ``SCRIPT`` constant
    and the sibling subprocess test — deepen existing coupling rather than
    broaden dependency surface.

    Runs on every platform (no skipif).
    """
    smoke_setup = _load_smoke_setup_module()

    shakedown = containment.shakedown_dir(tmp_path)
    shakedown.mkdir(parents=True)
    (shakedown / "scope-run-1.json").write_text("{}", encoding="utf-8")

    repo_root = Path(__file__).resolve().parents[4]

    def _raising_listdir(path: object) -> list[str]:
        raise PermissionError(13, "Permission denied", str(path))

    argv = [
        "--data-dir", str(tmp_path),
        "--repo-root", str(repo_root),
        "prepare", "scope_file_remove",
        "--session-id", "wiring-test-session",
        "--run-id", "wiring-test-run",
    ]

    # Patch os.listdir in a ``monkeypatch.context()`` block so the patch
    # reverts immediately after ``_run_with_wrapper`` returns. Constraint
    # #6 in the Key correctness constraints list requires every monkeypatch
    # in this plan to be scoped to a ``with monkeypatch.context()`` block
    # so the patches do not leak into other tests or into
    # ``capsys.readouterr()`` below.
    #
    # The ``os.listdir`` patch works because ``containment.py`` uses
    # ``import os; os.listdir(...)`` (attribute lookup at call time), not
    # ``from os import listdir`` (reference captured at import time). If a
    # future refactor changes the import style in ``containment.py``, this
    # monkeypatch target becomes wrong — see Step 6 diagnostic paths for
    # the recovery hint.
    with monkeypatch.context() as patched:
        patched.setattr("os.listdir", _raising_listdir)

        with pytest.raises(SystemExit) as exc_info:
            smoke_setup._run_with_wrapper(argv)

    # Fail-FAST conversion: wrapper raises SystemExit(1) — NOT lifecycle's
    # fail-OPEN return 0. The smoke-setup script is a developer/operator
    # tool invoked directly, not a hook, so loud failure is the correct
    # default. See the contract shape table in the Task 8 lead-in.
    assert exc_info.value.code == 1, (
        "smoke-setup _run_with_wrapper must fail-fast on internal errors; "
        f"got exit={exc_info.value.code!r}"
    )

    captured = capsys.readouterr()
    # Outer-boundary contract: stderr carries the wrapper prefix.
    assert "containment_smoke_setup failed" in captured.err, (
        "_run_with_wrapper must wrap internal errors with its caller "
        f"prefix; got stderr={captured.err!r}"
    )
    # Observability contract: the wrapped exception carries the Stage 3
    # enumeration failure context from clean_stale_files.
    assert "cannot enumerate shakedown root" in captured.err, (
        "wrapped error must carry the clean_stale_files failure context "
        f"(Stage 3 enumeration); got stderr={captured.err!r}"
    )
```

- [ ] **Step 6: Run the smoke-setup caller-wiring tests**

```bash
cd packages/plugins/codex-collaboration
uv run pytest tests/test_containment_smoke_setup.py -v
```

Expected: all three tests PASS on non-root POSIX with `os.geteuid`. The subprocess `test_prepare_scenario_surfaces_cleanup_enumeration_failure` SKIPs when running as root or on Windows (same skipif guard as the other chmod tests). The in-process seam test `test_prepare_scenario_logs_cleanup_errors_with_smoke_setup_prefix` runs on every platform. The Round 6 in-process fallback `test_prepare_scenario_main_wrapper_fail_fast_via_monkeypatched_listdir` also runs on every platform — its purpose is to guarantee wrapper-contract coverage when the subprocess chmod test skips.

Diagnostic paths for the in-process test failures:

- If the test FAILS because `containment_smoke_setup:` is missing from stderr, Step 2's caller update was not applied — re-read Step 2 and verify the `if cleanup_result.had_errors:` block is in place after the `clean_stale_files(...)` call.
- If the test FAILS because `monkeypatch.setattr(smoke_setup, "_scenario_definition", …)` has no effect (i.e., the real `_scenario_definition` runs and raises `RuntimeError: scenario definition failed: unknown scenario_id. Got: 'wiring-test-any-id'`), the monkeypatch target is wrong — verify the module object returned by `_load_smoke_setup_module()` is the one whose `_scenario_definition` is being patched, and that no intermediate import path is shadowing it.
- If the test FAILS because `prepare_scenario` raises from `_read_session_id` before the stub is called, the explicit `session_id="wiring-test-session"` argument is being ignored — check that `session_id or _read_session_id(data_dir)` still short-circuits on a truthy argument.
- If the test FAILS because `failed_unlink=1` is missing from stderr but `failed_unlink=0` is present, Task 1's per-file unlink capture is not working — the `Path.unlink` monkeypatch is not reaching the cleanup code path; verify `stale` equality comparison in `failing_unlink` (Path equality can be surprising with symlinks; the shakedown directory under `tmp_path` should not involve symlinks).

Diagnostic paths for the subprocess test failures (Round 5 additions):

- If the **subprocess test FAILS with `returncode == 0`** (when 1 was expected), the smoke-setup `__main__` wrapper at `containment_smoke_setup.py:505-510` has been inadvertently changed to fail-open. Verify that the `try: raise SystemExit(main()) except Exception as exc: print("containment_smoke_setup failed: …"); raise SystemExit(1) from exc` block is intact. **This is a fail-fast contract regression — do not proceed until fixed.**
- If the **subprocess test FAILS because stderr is missing `"containment_smoke_setup failed"`**, the `__main__` wrapper's print statement has been changed or removed. Re-read lines 505-510 of the script.
- If the **subprocess test FAILS because stderr is missing `"cannot enumerate shakedown root"`**, Task 1 Step 5's Stage 3 raise is not formatted as expected. Re-read the Stage 3 block and verify the `raise OSError(f"clean_stale_files failed: cannot enumerate shakedown root. …")` formatting is literal.
- If the **subprocess test FAILS with `RuntimeError("resolve repo paths failed: required B1 fixture paths missing")`** in stderr, one of the B1 fixture files has been moved, renamed, or deleted. The fixtures referenced are `docs/superpowers/specs/codex-collaboration/contracts.md`, `delivery.md`, `foundations.md`, `packages/plugins/codex-collaboration/server/mcp_server.py`, `packages/plugins/codex-collaboration/server/dialogue.py`, and `packages/plugins/codex-collaboration/scripts/codex_guard.py`. Recovery options: (a) restore the missing fixture file at its expected location, (b) update `_repo_paths()` in `containment_smoke_setup.py` to point at the new location, or (c) update the test to use a different `--repo-root` (last resort — couples the test to a different repo layout).
- If the **subprocess test FAILS because `Path(__file__).resolve().parents[4]` does not point at the repo root**, the test file has been moved within the repo. Recompute the `parents[N]` index based on the new location: count the directories from the test file up to the repo root. Currently the test is at `packages/plugins/codex-collaboration/tests/test_containment_smoke_setup.py`, so `parents[4]` walks `tests → codex-collaboration → plugins → packages → repo_root`.
- If the **subprocess test FAILS because the chmod restore in the `finally` block raises**, you are running as root in a filesystem that rejects the chmod for some reason. Rerun without root. The `finally` block's `os.chmod(shakedown, 0o755)` is mandatory for `tmp_path` teardown.

Diagnostic paths for the in-process fallback test failures (Round 6 additions):

- If the **in-process fallback test FAILS with `AttributeError: module '...' has no attribute '_run_with_wrapper'`**, Step 2's testability refactor was not applied or was applied incorrectly. Re-read Step 2 and verify the `__main__` block was replaced with a module-level `def _run_with_wrapper(argv: list[str] | None = None) -> None:` function definition followed by a 1-line `if __name__ == "__main__": _run_with_wrapper()` dispatch. The function must be at **module level** — NOT nested inside another function and NOT inside the `if __name__ == "__main__":` guard, otherwise `_load_smoke_setup_module()` cannot see it.
- If the **in-process fallback test FAILS because `SystemExit` is never raised** (i.e., `pytest.raises(SystemExit)` reports `Failed: DID NOT RAISE`), the `os.listdir` monkeypatch is not taking effect and `main()` is completing the scenario normally. Two likely causes: (a) `containment.py` may have been refactored to use `from os import listdir` instead of `os.listdir`, making the attribute-lookup patch a no-op — patch `containment.os.listdir` directly, or revert the import style; (b) the `_run_with_wrapper` refactor was applied but the `raise SystemExit(main(argv))` line was replaced with plain `main(argv)` — then happy-path `main()` never converts its return code into `SystemExit` and only the exception path would reach the wrapper.
- If the **in-process fallback test FAILS with `exc_info.value.code == 0`** (when 1 was expected), the `_run_with_wrapper` refactor has lost behavior: the `except Exception` block is not converting the caught exception into `SystemExit(1)`. Re-read Step 2's refactor and verify `raise SystemExit(main(argv))` is inside the `try:` so an exception from `main(argv)` gets caught before the `SystemExit` can fire, and that the `except` block unconditionally raises `SystemExit(1) from exc`.
- If the **in-process fallback test FAILS because stderr is empty** (no `containment_smoke_setup failed` line), the `_run_with_wrapper` refactor is missing the `print(f"containment_smoke_setup failed: {exc}", file=sys.stderr)` call in the except block. Re-read Step 2 — the print MUST precede the `raise SystemExit(1) from exc` so the stderr output is emitted before Python starts tearing down the stack.
- If the **in-process fallback test FAILS with `RuntimeError("resolve repo paths failed: required B1 fixture paths missing")`** raised before the monkeypatch fires, one of the B1 fixture files has been moved, renamed, or deleted. Same B1 fixture coupling as the subprocess test — `_repo_paths()` validation runs in `main()` BEFORE `prepare_scenario` calls `clean_stale_files`. Recovery options match the subprocess test's recovery options above: restore the missing fixture, update `_repo_paths()`, or update the test's `--repo-root` argument.
- If the **in-process fallback test FAILS because `Path(__file__).resolve().parents[4]` does not point at the repo root**, the test file has been moved within the repo. Same recovery as the subprocess test above: recompute the `parents[N]` index based on the new location (currently `tests → codex-collaboration → plugins → packages → repo_root` = 4 levels up).
- If the **in-process fallback test FAILS with an argparse error** (a `SystemExit(2)` from argparse instead of `SystemExit(1)` from the wrapper, typically preceded by argparse's `usage: ...` stderr output), the `argv` list passed to `_run_with_wrapper` is malformed. Verify: flat list of strings (no nested lists), all required subcommand args present (`prepare`, `scope_file_remove`), and all required parent-parser options provided (`--data-dir`, `--repo-root`, `--session-id`, `--run-id`). Note that an argparse `SystemExit(2)` is ALSO caught by `pytest.raises(SystemExit)` — the `.code` comparison is what distinguishes the two failure modes.

- [ ] **Step 7: Run the full lifecycle and smoke-setup test files to catch regressions**

```bash
cd packages/plugins/codex-collaboration
uv run pytest tests/test_containment_lifecycle.py tests/test_containment_smoke_setup.py -v
```

Expected: every test passes. Pre-existing lifecycle tests should be unaffected because they exercise happy-path flows where `clean_stale_files` returns a clean result (no stderr output emitted from the new `if had_errors:` block).

- [ ] **Step 8: Run file-scoped Ruff on the four changed/created files**

```bash
cd packages/plugins/codex-collaboration
uv run ruff check scripts/containment_lifecycle.py scripts/containment_smoke_setup.py tests/test_containment_lifecycle.py tests/test_containment_smoke_setup.py
```

Expected: silent success or `All checks passed!`.

- [ ] **Step 9: Commit**

```bash
git add packages/plugins/codex-collaboration/scripts/containment_lifecycle.py packages/plugins/codex-collaboration/scripts/containment_smoke_setup.py packages/plugins/codex-collaboration/tests/test_containment_lifecycle.py packages/plugins/codex-collaboration/tests/test_containment_smoke_setup.py
git commit -m "feat(containment): lifecycle and smoke-setup log cleanup errors with prefix"
```

---

## Task 9: Full verification and PR preparation

**Files:**
- No file edits; verification only

- [ ] **Step 1: Run the full codex-collaboration test suite**

```bash
cd packages/plugins/codex-collaboration
uv run pytest
```

Expected: all tests pass. Previous baseline was `519 passed`. T-03 adds the following tests:

| Task | Tests added |
|---|---|
| 1 | `test_clean_stale_files_returns_result_with_removed_and_fresh` |
| 2 | `test_clean_stale_files_captures_unlink_failures` |
| 3 | `test_clean_stale_files_captures_stat_failures` |
| 4 | `test_clean_stale_files_returns_empty_when_shakedown_root_missing` |
| 4 | `test_clean_stale_files_raises_when_root_lstat_fails` |
| 4 | `test_clean_stale_files_raises_on_dangling_root_symlink` |
| 4 | `test_clean_stale_files_raises_when_root_is_not_a_directory` |
| 4 | `test_clean_stale_files_raises_when_enumeration_fails` |
| 4 | `test_clean_stale_files_raises_when_root_directory_unreadable` |
| 5 | `test_clean_stale_result_report_clean_run_is_single_summary_line` |
| 5 | `test_clean_stale_result_report_renders_failure_paths_and_errors` |
| 5 | `test_clean_stale_result_report_applies_prefix_to_every_line` |
| 6 | `test_clean_stale_files_mixed_batch_tracks_every_outcome` |
| 8 | `test_subagent_start_logs_cleanup_errors_with_lifecycle_prefix` |
| 8 | `test_subagent_start_surfaces_cleanup_enumeration_failure` |
| 8 | `test_main_fail_open_conversion_via_monkeypatched_listdir` (Round 5 — platform-agnostic in-process fallback for the lifecycle fail-open conversion contract) |
| 8 | `test_prepare_scenario_logs_cleanup_errors_with_smoke_setup_prefix` |
| 8 | `test_prepare_scenario_surfaces_cleanup_enumeration_failure` (Round 5 — smoke-setup subprocess root-failure test pinning the fail-FAST `__main__` wrapper contract) |
| 8 | `test_prepare_scenario_main_wrapper_fail_fast_via_monkeypatched_listdir` (Round 6 — platform-agnostic in-process fallback for the smoke-setup fail-FAST wrapper contract via the `_run_with_wrapper()` testability refactor) |

19 new tests plus 1 tightened existing test (13 in `test_containment.py`, 3 in `test_containment_lifecycle.py`, 3 in the new `test_containment_smoke_setup.py`). Expected new baseline: `538 passed`.

Platform-conditional outcomes (all acceptable). After Round 5 there are now **three** chmod tests that share the same `hasattr(os, "geteuid") + os.geteuid() == 0` skipif guard:

1. `test_clean_stale_files_raises_when_root_directory_unreadable` (Task 4 — helper-level chmod test)
2. `test_subagent_start_surfaces_cleanup_enumeration_failure` (Task 8 — lifecycle subprocess chmod test)
3. `test_prepare_scenario_surfaces_cleanup_enumeration_failure` (Task 8 — smoke-setup subprocess chmod test, Round 5)

All three skip together on root or Windows. Two platform-agnostic in-process fallbacks run on every platform regardless of `geteuid` availability, ensuring root and Windows still have automated coverage of both outer-boundary contracts that the subprocess chmod tests pin on supported platforms:

- `test_main_fail_open_conversion_via_monkeypatched_listdir` (Task 8, Round 5) — pins lifecycle's fail-OPEN conversion contract by calling `lifecycle.main()` directly with monkeypatched `os.listdir`.
- `test_prepare_scenario_main_wrapper_fail_fast_via_monkeypatched_listdir` (Task 8, Round 6) — pins smoke-setup's fail-FAST wrapper contract by calling `smoke_setup._run_with_wrapper(argv)` directly with monkeypatched `os.listdir`. Enabled by the Round 6 testability refactor that extracts the `__main__` block's try/except into a module-level callable function (see Task 8 Step 2).

| Condition | Baseline | Notes |
|---|---|---|
| macOS/Linux non-root (primary dev + CI) | `538 passed` | All 19 new tests run |
| Running as root | `535 passed, 3 skipped` | All three chmod tests skip; both in-process fallbacks (lifecycle Round 5 + smoke-setup Round 6) still run |
| No symlink support (rare CI) | `537 passed, 1 skipped` | Dangling-symlink test skips |
| Running as root AND no symlink support | `534 passed, 4 skipped` | 3 chmod + 1 symlink |
| Windows | `535 passed, 3 skipped` | All three chmod tests skip via `hasattr(os, "geteuid")`; both in-process fallbacks still run |

- [ ] **Step 2: Run file-scoped Ruff on every changed/created file**

```bash
cd packages/plugins/codex-collaboration
uv run ruff check \
  server/containment.py \
  scripts/clean_stale_shakedown.py \
  scripts/containment_lifecycle.py \
  scripts/containment_smoke_setup.py \
  tests/test_containment.py \
  tests/test_containment_lifecycle.py \
  tests/test_containment_smoke_setup.py
```

Expected: `All checks passed!` or silent success.

**Do NOT run package-wide `uv run ruff check`** — it surfaces unrelated pre-existing failures in `codex_runtime_bootstrap.py`, `tests/conftest.py`, `tests/test_credential_scan.py`, and `tests/test_dialogue_profiles.py`, documented in the resumed handoff (learning #3).

- [ ] **Step 3: Review the full branch diff**

```bash
git diff origin/main...HEAD -- \
  server/containment.py \
  scripts/clean_stale_shakedown.py \
  scripts/containment_lifecycle.py \
  scripts/containment_smoke_setup.py \
  tests/test_containment.py \
  tests/test_containment_lifecycle.py \
  tests/test_containment_smoke_setup.py
```

Scan for:
- No stray debug prints
- No unused imports (specifically: `fnmatch`, `S_ISDIR`, `S_ISREG`, `dataclass`, `importlib.util` all referenced in code)
- `server/containment.py` must NOT contain `shakedown_path.glob(` — any remaining occurrence means Task 1 Step 5's Stage 3 rewrite was not applied and the Round 3 silent-enumeration defect is still present. Grep: `git diff origin/main -- server/containment.py | grep -F '.glob('` should produce no `+` lines adding a glob call; only `-` lines removing the old one.
- No accidental edits to unrelated files
- Every monkeypatch of `Path.stat`, `Path.lstat`, or `Path.unlink` is wrapped in `with monkeypatch.context() as patched:` (P2 regression guard — grep the plan's test diff for `monkeypatch.setattr(Path,` and verify every occurrence is inside a context block)
- The Task 4 enumeration test's `monkeypatch.setattr(os, "listdir", …)` is also inside a `with monkeypatch.context() as patched:` block
- No `rm` or `rm -rf` anywhere in the smoke-check commands
- Every `report(prefix=...)` call in caller code uses the correct prefix: `"containment-lifecycle: "` in `containment_lifecycle.py`, `"containment_smoke_setup: "` in `containment_smoke_setup.py`, no prefix in `clean_stale_shakedown.py`

- [ ] **Step 4: Verify branch ancestry is publication-clean**

```bash
git log --oneline origin/main..HEAD
git diff --name-only origin/main...HEAD
```

Expected:
- Exactly 8 commits (one per Task 1-8; Task 9 is verification-only)
- Exactly 7 changed files:
  - `server/containment.py`
  - `scripts/clean_stale_shakedown.py`
  - `scripts/containment_lifecycle.py`
  - `scripts/containment_smoke_setup.py`
  - `tests/test_containment.py`
  - `tests/test_containment_lifecycle.py`
  - `tests/test_containment_smoke_setup.py`

If the commit list or file list contains anything else, stop and investigate before pushing. This is the PR-pollution class warned about in the resumed handoff (learning #5).

- [ ] **Step 5: Push and open the draft PR**

```bash
git push -u origin fix/t03-stale-cleanup-observability
gh pr create --draft --title "[codex] Harden stale cleanup observability and failure reporting" --body "$(cat <<'EOF'
## Summary
- `clean_stale_files` now returns a `CleanStaleResult` with four buckets: `removed`, `skipped_fresh`, `failed_stat`, `failed_unlink`
- **Whole-sweep failures now raise** instead of silently returning success. Three distinct stages cover the full failure surface:
  - Stage 1 (`lstat`): unreadable parent raises; only `FileNotFoundError` on the root itself is treated as first-run
  - Stage 2 (`stat`): dangling symlink raises with `"possible broken symlink"`; non-directory raises `NotADirectoryError`
  - Stage 3 (`os.listdir`): unreadable directory (e.g., `chmod 0o000`) raises with `"cannot enumerate"`. This stage is necessary because `stat()` on a `chmod 0o000` directory succeeds (mode `0o40000`, `S_ISDIR` true) — the two-stage root check above cannot detect this class, and the stdlib `Path.glob()` would silently return `[]` here. `os.listdir()` + `fnmatch.fnmatch()` replaces the `glob` loop.
- Replaces `Path.is_file()` with explicit `Path.stat()` + `S_ISREG` so per-file stat failures become observable (stdlib `is_file()` silently catches `OSError`)
- `CleanStaleResult.report(prefix="")` renders a multi-line operator-facing report with summary line plus one line per failure with path and error repr. The `prefix` parameter applies to *every* line so multi-line reports retain caller attribution after grep/aggregation.
- All three callers now surface cleanup failures at **two distinct error surfaces**:
  - **Per-file surface** (`clean_stale_files` returns `CleanStaleResult` with `had_errors=True`):
    - `clean_stale_shakedown.py` — prints `report()` to stderr **only when `had_errors`** (Round 5 Choice 3B: silent on clean runs to preserve operator signal; loud on failure)
    - `containment_lifecycle.py` — logs `report(prefix="containment-lifecycle: ")` via `_log_error` on `had_errors`
    - `containment_smoke_setup.py` — prints `report(prefix="containment_smoke_setup: ")` to stderr on `had_errors`
  - **Root-level surface** (`clean_stale_files` raises `OSError` before returning — never produces a `CleanStaleResult`, so `report()` is not invoked; each caller's outer exception boundary handles the raise with its own contract shape):
    - `clean_stale_shakedown.py` — outer `except Exception` prints `clean_stale_shakedown failed: ...` → exit `1` (fail-fast CLI tool)
    - `containment_lifecycle.py` — `main()`'s outer `except Exception` at lines 184-188 logs `containment-lifecycle: internal error (...)` → return `0` (**fail-OPEN** hook policy — see Fail-Open Hook Policy design decision)
    - `containment_smoke_setup.py` — `_run_with_wrapper()`'s outer `except Exception` (Round 6 testability refactor of the `__main__` block) prints `containment_smoke_setup failed: ...` → exit `1` (fail-fast operator tool)
- Wiring tests pin both surfaces: in-process **seam tests** force `had_errors=True` in each internal caller and assert on captured stderr; **four outer-boundary tests** exercise root-level raises through each caller's outer exception boundary (lifecycle subprocess + Round 5 in-process fallback; smoke-setup subprocess + Round 6 in-process fallback via `_run_with_wrapper()`). Regressions at either surface are caught automatically on every supported platform.

## Implements
- Ticket [T-20260410-03](docs/tickets/2026-04-10-T-20260410-03-harden-stale-cleanup-observability-and-failure-rep.md)

## Scope notes
- `read_active_run_id` and `read_json_file` lenient helpers are intentionally not modified. They are not called by `clean_stale_files`, and strict alternates already exist at `containment.py:92` and `:126`. Migrating their 5+ call sites is a separate refactor.
- Sibling module-scope `server.containment` imports in `containment_lifecycle.py` and `containment_smoke_setup.py` are left unchanged (adjacent sharp edge outside T-03's scope).

## Test plan
- [ ] CI: `uv run pytest` in `packages/plugins/codex-collaboration` (expected: 538 passed on macOS/Linux non-root; 535 passed + 3 skipped if running as root or on Windows — all three chmod tests skip; 537 passed + 1 skipped if no symlink support; 534 passed + 4 skipped in the root-or-Windows ∩ no-symlink intersection)
- [ ] CI: file-scoped `uv run ruff check` over every modified/created file
- [ ] Manual: happy-path, first-run, dangling-symlink-corruption, unreadable-directory (`chmod 0o000`), empty-env, and nonexistent-path subprocess smoke checks for `scripts/clean_stale_shakedown.py`

EOF
)"
```

Expected: PR URL printed.

- [ ] **Step 6: Verify the published PR shape (guard against stale GitHub cache)**

```bash
PR_NUM=$(gh pr view --json number --jq .number)
gh pr view "$PR_NUM" --json state,isDraft,mergeable,commits,files,headRefOid
```

Expected:
- `state: OPEN`
- `isDraft: true`
- `mergeable: MERGEABLE` or `UNKNOWN` (UNKNOWN for a few seconds after push is fine)
- `commits` length: `8`
- `files` length: `7`

Cross-check with local:

```bash
git log --oneline origin/main..HEAD | wc -l
git diff --name-only origin/main...HEAD | wc -l
```

Expected: `8` and `7` respectively.

If `gh pr diff --name-only "$PR_NUM"` returns a different file count than local immediately after push, treat as stale GitHub cache (handoff learning #6) — wait 10 seconds and rerun before investigating.

---

## Self-Review Checklist

**Spec coverage (ticket acceptance criteria):**

| Criterion | Covered by |
|---|---|
| `clean_stale_files` returns or logs explicit cleanup results rather than silently succeeding when deletions fail | Task 1 (returns `CleanStaleResult`; raises on every root-level failure *except* legitimate first-run); Task 7 (wrapper logs `report()` on `had_errors`, silent on clean runs per Round 5 Choice 3B); Task 8 (internal callers log on `had_errors`, verified by wiring tests for both per-file and root-level surfaces) |
| `PermissionError` and related `OSError` cases during stale cleanup are surfaced to callers with actionable context | **Per-file surface** (returned via `CleanStaleResult.had_errors`): Task 1 (`failed_stat` and `failed_unlink` hold `(path, repr)` tuples; `report()` renders path + error_repr per line, not just counts); Task 5 (verifies the rendering includes actionable data); Tasks 7-8 log `report(prefix=…)` on `had_errors` in all three callers (the wrapper gates its print on `had_errors` per Choice 3B; lifecycle and smoke-setup gate via `_log_error` and `print` respectively). **Root-level surface** (raised as `OSError`, never `report()`): caught by each caller's outer exception boundary — `clean_stale_shakedown.py:main()` prints `"clean_stale_shakedown failed: <exc>"` and exits `1`; `containment_lifecycle.py:main()` prints `"containment-lifecycle: internal error (<exc>)"` and returns `0` (fail-OPEN, see Fail-Open Hook Policy design decision); `containment_smoke_setup.py:_run_with_wrapper()` (Round 6 testability refactor of the `__main__` block) prints `"containment_smoke_setup failed: <exc>"` and exits `1` (fail-FAST). Root-level coverage **through each caller's outer boundary** is pinned by **four automated tests** added across Rounds 5 and 6: `test_subagent_start_surfaces_cleanup_enumeration_failure` (Task 8 — lifecycle subprocess chmod, fail-OPEN contract, non-root POSIX only), `test_main_fail_open_conversion_via_monkeypatched_listdir` (Task 8 Round 5 — platform-agnostic in-process fallback for the lifecycle fail-OPEN conversion that runs even on root/Windows), `test_prepare_scenario_surfaces_cleanup_enumeration_failure` (Task 8 Round 5 — smoke-setup subprocess chmod, fail-FAST contract, non-root POSIX only), and `test_prepare_scenario_main_wrapper_fail_fast_via_monkeypatched_listdir` (Task 8 Round 6 — platform-agnostic in-process fallback for the smoke-setup fail-FAST conversion via the `_run_with_wrapper()` refactor, runs on every platform). Both contract shapes (fail-OPEN and fail-FAST) are therefore pinned on every platform regardless of `os.geteuid` availability. The CLI wrapper's (`clean_stale_shakedown.py`) root-level boundary is covered by Task 7 Steps 6-7 manual probes, not by an automated test. |
| Cleanup tests cover undeletable files, broken directory entries, and mixed success/failure batches | Task 2 (undeletable), Task 3 (per-file stat failure), Task 4 (4 root-level scenarios including dangling symlink), Task 6 (mixed batch exercising every bucket), Task 8 (caller wiring tests forcing `had_errors`) |
| Helper paths used by cleanup no longer collapse materially different failure modes into the same 'missing' result when that would hide operational state | Task 1 replaces `shakedown_path.exists()` with a two-stage `lstat()`/`stat()` check that distinguishes "truly absent" from "dangling symlink" from "permission denied". Replaces per-file `path.is_file()` with explicit `path.stat()` + `S_ISREG`. The `read_active_run_id`/`read_json_file` lenient helpers are documented as out of scope because they are not called by `clean_stale_files` itself. |

**Resolution map for all review findings (six review rounds):**

| Finding | Resolution |
|---|---|
| Round 1 P1: Root directory unreadable collapses to clean success | Task 1 Step 5: two-stage `lstat()`/`stat()` check raises on every `OSError` except `FileNotFoundError` at `lstat()`. Task 4 covers with `test_clean_stale_files_raises_when_root_lstat_fails`. *Note:* Round 3 exposed that this check alone is insufficient for the `chmod 0o000` case because `stat` succeeds on the directory itself (stat only needs execute on the parent). The enumeration guard below is the complementary fix. |
| Round 1 P1: Normal lifecycle/setup entrypoints still hide cleanup failures | Task 8: updates both `containment_lifecycle.py:73` and `containment_smoke_setup.py:118` to capture result and log `report(prefix=…)` on `had_errors`. |
| Round 1 P2: Operator output not actionable (counts only) | Task 1 Step 4: `report()` renders per-failure `(path, error_repr)` lines. Task 5 verifies. Tasks 7-8 print `report()` (not a count-only summary). |
| Round 1 P2: Stat-failure test fails for the wrong reason (monkeypatch breaking `.exists()`) | Tasks 3, 4, 6: every `monkeypatch.setattr(Path, "stat", …)` and `Path.unlink` patch is wrapped in `with monkeypatch.context() as patched:` so the patch reverts before `.exists()` assertions. Task 9 Step 3 includes a grep-based regression guard. |
| Round 1 P3: `rm -rf` violates global CLAUDE.md | Task 7 Steps 4-8 use `trash "$TEMP_PLUGIN_DATA"`. No `rm` in the plan. |
| Round 2 P2: Broken shakedown-root symlink still collapses to first-run success | Task 1 Step 5: two-stage `lstat()` (to detect true filesystem presence) followed by `stat()` (to validate symlink target) — dangling symlink raises `OSError` with "possible broken symlink" message. Task 4 covers with `test_clean_stale_files_raises_on_dangling_root_symlink`. Task 7 Step 6 adds a subprocess smoke check that creates a real dangling symlink. |
| Round 2 P2: Smoke-setup caller wiring not verifiable (referenced non-existent test file; happy-path-only verification) | Task 8: creates `tests/test_containment_smoke_setup.py` (new file) with one focused test that forces `had_errors=True` via monkeypatched `Path.unlink` and asserts on prefixed stderr. Also adds the equivalent test to `tests/test_containment_lifecycle.py` (existing file). Both tests are run in Task 8 Step 4 and Step 6, and again in the full suite in Task 9 Step 1. |
| Round 2 P3: Multi-line cleanup reports lose caller attribution after the first line | Task 1 Step 4: `report()` accepts `prefix: str = ""` and prefixes *every* line. Task 5 adds `test_clean_stale_result_report_applies_prefix_to_every_line` to verify. Tasks 7-8 pass the appropriate prefix from each caller. Both wiring tests in Task 8 assert that every `clean_stale_files:` / `failed_*` line starts with the caller prefix. |
| **Round 3 Critical**: `Path.glob()` silently returns `[]` on unreadable directories, so the cleanup sweep still reports clean success when the shakedown root cannot be listed. Root `stat` succeeds because stat only needs execute on the parent; the two-stage root check cannot detect this class. | Task 1 Step 3 adds `import fnmatch`. Task 1 Step 5 replaces the `for pattern in _STALE_PATTERNS: for path in shakedown_path.glob(pattern):` loop with a Stage 3 block: `os.listdir(shakedown_path)` wrapped in `try/except OSError` that re-raises with `"cannot enumerate shakedown root"` context, followed by name-filtering via `fnmatch.fnmatch(name, pattern)`. Empirically verified on Python 3.14 before writing the plan (`chmod 0o000` + `root.glob("seed-*.json")` returns `[]`; same input to `os.listdir` raises `PermissionError`). |
| **Round 3 High**: Verification matrix does not test the enumeration failure — every listed test passes even if enumeration silently swallows errors | Task 4 adds two tests: `test_clean_stale_files_raises_when_enumeration_fails` (monkeypatches `os.listdir`, portable, runs everywhere) and `test_clean_stale_files_raises_when_root_directory_unreadable` (real `chmod 0o000`, exercises the full code path without any mock, skipped when running as root or on Windows via `hasattr(os, "geteuid")`). Task 7 Step 7 adds a matching subprocess-level manual probe via `chmod 000` on the shakedown directory. Task 4 Step 2's diagnostic list calls out the most severe failure mode explicitly (real chmod test passes by returning empty = Stage 3 missing entirely). |
| **Round 3 Minor**: Plan bookkeeping drift — file structure said "10 new tests" in `test_containment.py` but body defined 11 | Fixed the file-structure row to `"Add 13 new tests"` (which is the post-Round-3 count: 11 from the prior draft + 2 new enumeration tests). Task 9 Step 1 test table is the authoritative count and has been updated. |
| **Round 4 High**: Fail-open policy in `containment_lifecycle.py:main()` is an unspoken assumption — prior drafts claimed exceptions "propagate naturally" but `main()`'s outer `except Exception` at lines 184-188 catches them and returns `0`. The plan must either elevate root-level cleanup failures to an explicit hook-failure contract or endorse fail-open and test the stderr-based observability contract instead. | Added the **Fail-Open Hook Policy for `containment_lifecycle.py`** design decision which endorses fail-open as deliberate (rationale: `SubagentStart` treats non-zero exit as "block the spawn" and a containment-state defect must not escalate into a hard block on unrelated spawns), documents the contract shape as a table of (failure class → stderr strings + exit code) pairs, and commits T-03 to **not** change any caller's exit-code contract. Added constraint #11 to the Key correctness constraints list so a future maintainer cannot silently flip the policy. Added the new `test_subagent_start_surfaces_cleanup_enumeration_failure` test (Task 8 Step 3) which exercises a real `chmod 0o000` through the subprocess boundary and asserts on both the fail-open return code (`0`) and the stderr caller-prefix + actionable context (`containment-lifecycle: internal error` + `cannot enumerate shakedown root`). The architecture paragraph at the top of the plan was rewritten to explicitly say "T-03 does not change any caller's exit-code contract". |
| **Round 4 Medium**: Smoke-setup wiring test overfitted to `scope_file_remove requires --run-id` — the test termination path depends on a specific scenario's validation, so a harmless refactor to that scenario can break a test that is supposed to be about the cleanup logging wiring. | Task 8 Step 5 replaced the test body with a direct-seam version: `monkeypatch.setattr(smoke_setup, "_scenario_definition", raising_stub)` so that the termination sentinel is unrelated to any specific scenario. The stub raises `RuntimeError("smoke-setup wiring test termination sentinel")`. The test passes `session_id` and `run_id` explicitly so `_read_session_id` and `uuid.uuid4()` are never reached, and `scenario_id` becomes irrelevant because the stub ignores it. The test now measures only the stable contract: "cleanup runs first, logging happens, then any later failure terminates". The docstring explains the prior fragility so the pattern is not reintroduced. |
| **Round 4 Medium**: No automated test verifies root-level failure through an internal caller — the prior draft's wiring tests only forced `had_errors=True` through per-file unlink failure and did not cover root-level raises propagating through the lifecycle/smoke-setup outer boundaries. | Task 8 Step 3 adds `test_subagent_start_surfaces_cleanup_enumeration_failure`, which uses `_run_lifecycle` (subprocess invocation of `scripts/containment_lifecycle.py`) with a real `chmod 0o000` shakedown directory to exercise the full failure propagation: `clean_stale_files` raises Stage 3 `OSError` → propagates through `_handle_subagent_start` and `handle_payload` → caught by `main()`'s outer `except Exception` → converted to `_log_error("containment-lifecycle: internal error (<exc>)")` + `return 0`. The test asserts `returncode == 0` AND stderr contains `containment-lifecycle: internal error` AND `cannot enumerate shakedown root`. This is the first test that exercises the lifecycle `main()` boundary for a root-level failure; it complements (rather than replaces) the existing per-file wiring test. |
| **Round 4 Low**: Eager `os.listdir()` tradeoff unstated — a future maintainer hitting an unusual shakedown scale will want to know whether `os.scandir()` is a drop-in replacement. | Added the "**Scale tradeoff**" paragraph to the Enumeration Primitive design decision, noting that `os.listdir()` materializes entries into memory, that the shakedown directory typically holds 5-15 files bounded by `_STALE_PATTERNS` and cleaned every 24 hours, and that `os.scandir()` is a drop-in replacement with identical loud-failure semantics if the operational envelope ever changes. |
| **Round 5 High**: Smoke-setup caller had no automated proof of its root-level failure boundary — the lifecycle subprocess test pinned only lifecycle's fail-OPEN contract; smoke-setup's structurally different fail-FAST `__main__` wrapper at `containment_smoke_setup.py:505-510` was unpinned. A smoke-setup root-error regression could ship with every other T-03 test passing. | Task 8 Step 5 adds `test_prepare_scenario_surfaces_cleanup_enumeration_failure`, a subprocess test that does a real `chmod 0o000` on the shakedown directory, invokes the smoke-setup script via a new `_run_smoke_setup` helper (modeled on `_run_lifecycle`), and asserts: (a) `returncode == 1` (fail-FAST contract), (b) stderr contains `"containment_smoke_setup failed"` (outer wrapper prefix), (c) stderr contains `"cannot enumerate shakedown root"` (Stage 3 actionable context). The test shares the same `hasattr(os, "geteuid") + os.geteuid() == 0` skipif guard as the other two chmod tests. The repo root for `--repo-root` is derived from `Path(__file__).resolve().parents[4]` (staying within the same filesystem-layout coupling class as the existing `SCRIPT` constant) rather than via `git rev-parse` (to avoid introducing a new external dependency at test-setup time). The B1 fixture coupling is documented inline in the test docstring and in Task 8 Step 6 diagnostic paths. |
| **Round 5 Medium (documentation drift, Task 8 lead-in)**: Plan line 1136 still said "root-level `OSError` propagates naturally" + "each caller uses `report(prefix=…)`" — exactly the wording Round 4 explicitly flagged as misleading at line 72. The Fail-Open Hook Policy design decision corrected the framing in one place, but the sibling Task 8 lead-in was never updated. This pattern (sibling-section drift after a fix) is itself worth flagging. | Task 8 lead-in fully rewritten to distinguish **two error surfaces** (per-file `had_errors` → `report(prefix=…)` vs root-level raise → caller's outer exception boundary), with a contract shape table showing the **two different boundary contracts** (lifecycle fail-OPEN at `main()` lines 184-188 vs smoke-setup fail-FAST at `__main__` lines 505-510). Explicit note added: "Root-level raises do not go through `report(prefix=…)` — `report()` is a method on `CleanStaleResult`, which does not exist when the helper raises before returning." Wiring-test paragraph rewritten to map both surfaces to specific tests. |
| **Round 5 Medium (documentation drift, self-review row 2)**: Plan line 1742 said "Tasks 7-8 (all three callers print `report()` on error)" — false at the root-level path because `clean_stale_files` raises before returning a `CleanStaleResult`, so `report()` is never produced. At the root-level path, each caller's outer boundary prints its own wrapper-specific message (`"clean_stale_shakedown failed: …"`, `"containment-lifecycle: internal error (…)"`, `"containment_smoke_setup failed: …"`). | Self-review row rewritten with explicit per-file vs root-level surface distinction, listing each caller's outer-boundary wrapper message verbatim, and pointing at the three Round 5 root-level tests (lifecycle subprocess, in-process fallback, smoke-setup subprocess). |
| **Round 5 Medium (assumption — stderr monitoring path)**: The Round 4 Fail-Open Hook Policy assumes that operators reading hook stderr actually see the `containment-lifecycle: internal error (…)` lines, but the assumption was never explicitly validated. The reviewer cross-referenced [`docs/tickets/closed-tickets/2026-02-15-plan-review-errata.md:439`](../../tickets/closed-tickets/2026-02-15-plan-review-errata.md), which rejected stderr-only logging for the MCP server conversation guard with the conclusion "MCP servers run as subprocesses with no stderr monitoring path. Fail-fast or nothing." | Added an explicit assumption paragraph to the Fail-Open Hook Policy design decision distinguishing hook-script stderr from MCP-server stderr: hook scripts run per-event and their stderr is captured by Claude Code's hook runner, while MCP servers are long-lived background subprocesses with no real monitoring path. T-03 accepts this structural difference as load-bearing, but also commits that "if operational experience later shows hook stderr is being swallowed in practice, the correct fix is NOT to flip fail-open — it is to add a structured telemetry emission path orthogonal to stderr." Empirical validation of the hook stderr monitoring path is a potential follow-up outside T-03's scope. |
| **Round 5 Medium (platform gating)**: The lifecycle root-failure subprocess test `test_subagent_start_surfaces_cleanup_enumeration_failure` is gated on `hasattr(os, "geteuid") + os.geteuid() == 0`, so on root or Windows the only automated proof of `main()`'s fail-open conversion through the caller boundary disappears. Helper-level coverage via `test_clean_stale_files_raises_when_enumeration_fails` still runs everywhere, but it tests the helper directly, not through the caller boundary. | Task 8 Step 3 adds `test_main_fail_open_conversion_via_monkeypatched_listdir`, a platform-agnostic in-process fallback that uses `monkeypatch.setattr("os.listdir", _raising_listdir)` + `monkeypatch.setattr("sys.stdin", io.StringIO(payload_json))` + `monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(data_dir))` to call `lifecycle.main()` directly and assert: (a) exit code 0 (fail-open conversion), (b) stderr contains `"containment-lifecycle: internal error"`, (c) stderr contains `"cannot enumerate shakedown root"`. This test runs on every platform regardless of `geteuid` availability, so root and Windows CI runs still have automated coverage of the lifecycle fail-open conversion contract. Subprocess and in-process tests are kept side-by-side (not one replacing the other): the subprocess test is the authoritative end-to-end proof on supported platforms; the in-process test is the platform-agnostic minimum coverage. |
| **Round 5 Medium (wrapper signal-to-noise)**: Task 7 Step 2's wrapper code printed `result.report()` to stderr unconditionally, so on a clean run the wrapper produced `clean_stale_files: removed=0, fresh=0` to stderr. This trains operators to discount cleanup stderr — they learn the cleanup output is normal noise and stop reading it, which defeats the entire observability rewrite when an actual error occurs. | Task 7 Step 2 wrapper code gated on `if result.had_errors: print(result.report(), file=sys.stderr)` so the wrapper is silent on clean runs and only prints on actual errors. Matches Unix convention (silent on success, noisy on failure) and matches the existing internal-caller pattern (lifecycle and smoke-setup already gated on `had_errors`). Task 7 Step 2 prose updated to explain the gating rationale. Task 7 Step 4 and Step 5 expected stderr changed from `clean_stale_files: removed=0, fresh=0` to *(empty)*. Task 7 Step 6 and Step 7 diagnostic notes updated: the regression-detection signal is now "stderr is empty + exit=0" rather than "stderr contains `clean_stale_files: removed=0, fresh=0` + exit=0". Self-review bullet at line 1685 ("prints `report()` to stderr unconditionally") and self-review row at line 1741 ("wrapper logs unconditionally") both updated to reflect the gated behavior. |
| **Round 6 Medium (smoke-setup outer-boundary asymmetry)**: The lifecycle `main()` boundary had both a subprocess chmod test and a platform-agnostic in-process fallback (Round 5), but smoke-setup's `__main__` boundary had only the subprocess chmod test. On root or Windows — where the subprocess chmod test skips — the lifecycle fail-OPEN contract was still pinned by the in-process fallback calling `main()` directly, but the smoke-setup fail-FAST contract was entirely unpinned. The plan's claim that "a smoke-setup root-failure regression cannot ship with every other T-03 test passing" and that root-level coverage is pinned "through each caller's outer boundary" was only true on non-root POSIX. Structural cause of the asymmetry: lifecycle's fail-OPEN boundary was inside `main()` itself (callable from tests), but smoke-setup's fail-FAST boundary lived in the `__main__` guard block (structurally unreachable from in-process tests without `runpy`). | Round 6 **testability refactor (Option C, behavior-preserving)**: extract the `containment_smoke_setup.py` `__main__` try/except into a module-level `_run_with_wrapper(argv: list[str] \| None = None) -> None` function, keeping bit-for-bit identical behavior (same stderr text `containment_smoke_setup failed: <exc>`, same `SystemExit(1)` on any `Exception`, same `SystemExit(main(argv))` for the happy path). Task 8 Step 2 now includes this refactor as a second edit block alongside the per-file `had_errors` wiring. Task 8 Step 5 adds `test_prepare_scenario_main_wrapper_fail_fast_via_monkeypatched_listdir` — a platform-agnostic in-process fallback that calls `smoke_setup._run_with_wrapper(argv)` directly with `monkeypatch.setattr("os.listdir", _raising_listdir)` scoped in a `monkeypatch.context()` block (per constraint #6), catches `SystemExit` via `pytest.raises`, and asserts: (a) `exc_info.value.code == 1` (fail-FAST contract), (b) stderr contains `"containment_smoke_setup failed"` (wrapper prefix), (c) stderr contains `"cannot enumerate shakedown root"` (Stage 3 actionable context). Task 8 Step 6 diagnostic paths extended with 7 new branches covering the refactor's failure modes (missing `_run_with_wrapper`, `SystemExit` never raised, exit code 0, empty stderr, B1 fixture missing, `parents[N]` index off, argparse `SystemExit(2)` masquerading as wrapper exit). Both outer-boundary contract shapes (fail-OPEN and fail-FAST) are now pinned on every platform regardless of `os.geteuid` availability. The Round 5 "cannot ship" promise now holds unconditionally. |
| **Round 6 Medium (top-of-document summary drift)**: Round 5 corrected the per-file vs root-level error-surface distinction in Task 8's lead-in and in self-review row 2, but **four sibling locations at the top of the document** still flattened the distinction: (a) the architecture paragraph at line 17 still described the work as "log `report(prefix=...)` to stderr when `had_errors` is True" plus "one subprocess-level lifecycle test" — stale, there are now four root-level tests covering both contract shapes on every platform; (b) the Scope in-scope row at line 99 said "wrapper logs `result.report()`" without the Choice 3B gating or the root-level outer-boundary path; (c) the File Structure row at line 130 had the same flattening; (d) the PR body at line 1948 said "All three callers now log the report on errors" followed by per-file-only bullets — false for the root-level path, where `clean_stale_files` raises before returning a `CleanStaleResult` and each caller's outer boundary produces its own wrapper message instead of `report(prefix=...)`. Round 6 reviewer: "that is false for root-level raises and reintroduces the same summary-drift pattern Round 5 was fixing." The "find sibling sections" pattern recursed: Round 5 caught two drift locations; four more lived at the top of the document. | Rewrote all four locations to distinguish the per-file surface (caller gates `report(prefix=...)` on `had_errors`) from the root-level surface (caller's outer exception boundary produces a caller-specific wrapper message with a caller-specific exit-code contract). Architecture paragraph (line 17) now uses bullets to make the two-surface structure visually explicit, names all four root-level tests (lifecycle subprocess + Round 5 in-process fallback + smoke-setup subprocess + Round 6 in-process fallback), and states the three outer-boundary wrapper messages verbatim: `clean_stale_shakedown failed: <exc>` → exit 1, `containment-lifecycle: internal error (<exc>)` → return 0, `containment_smoke_setup failed: <exc>` → exit 1. Scope row and File Structure rows for `clean_stale_shakedown.py` now spell out both Choice 3B gating and the root-level outer-boundary path. PR body splits the single bullet list into two nested groups — "Per-file surface" with the three existing `report(prefix=...)` bullets, and "Root-level surface" with the three wrapper messages verbatim plus each caller's exit-code contract (fail-fast vs fail-OPEN). |
| **Round 6 Low (Task 8 per-file test scope overstatement)**: Task 8's lead-in at line 1152 claimed the wiring tests cover "both error surfaces **through each caller's outer boundary**", but the per-file lifecycle test at line 1205 (`test_subagent_start_logs_cleanup_errors_with_lifecycle_prefix`) explicitly calls `_handle_subagent_start` directly — its own docstring says "Does NOT touch `main()`" — and the per-file smoke-setup test at line 1548 (`test_prepare_scenario_logs_cleanup_errors_with_smoke_setup_prefix`) calls `prepare_scenario` directly via a monkeypatched `_scenario_definition` seam. Those tests prove the `if cleanup_result.had_errors:` gate and `report(prefix=...)` rendering **at the seam** — they do NOT exercise `main()` or `__main__` and therefore do NOT pin outer-boundary behavior for the per-file path. The distinction matters because the draft's value now is being precise about which boundary each test actually pins. | Rewrote Task 8's lead-in (line 1152) to distinguish **seam-level coverage** (per-file surface, proven by calling the seam function directly) from **outer-boundary coverage** (root-level surface, proven by the subprocess tests and the in-process fallbacks). Added the tightened phrasing: "No additional outer-boundary regression is required for the per-file path because that path returns normally and does not cross the exception boundary." Docstring precision notes added to both per-file tests at lines 1205 and 1548 stating explicitly that they pin the per-file surface at the seam (not the outer boundary) and naming which tests pin the outer boundary. |
| **Round 7 Medium (Fail-Open Hook Policy test-coverage drift)**: The Fail-Open Hook Policy design decision's **Test coverage** paragraph at line 92 still described Task 8 as adding "two lifecycle tests" with both tests claimed to prove the contract "through the real hook boundary". This was stale and partially false in three independent ways after Round 6: (a) Task 8 Step 3 now defines **three** lifecycle tests, not two; (b) the first test (`test_subagent_start_logs_cleanup_errors_with_lifecycle_prefix`) was reclassified as seam-level in Round 6 and explicitly does NOT touch `main()` — so describing it as proving the contract "through the real hook boundary" was false by its own docstring; (c) `test_main_fail_open_conversion_via_monkeypatched_listdir` (Round 5) was **omitted entirely** from this section even though it is the only test that pins the fail-open conversion on root and Windows where the subprocess chmod test skips. The "together pin this contract" wording was therefore inaccurate on exactly the platforms where the in-process fallback was designed to compensate. The "find sibling sections" drift pattern recursed for a third consecutive review: Round 5 caught two locations; Round 6 caught four more at the top of the document; Round 7 caught this Fail-Open Hook Policy Test coverage block that Round 6's sweep did not reach. | Rewrote the Test coverage paragraph at line 92 to list all three lifecycle tests with explicit classification: (a) the seam test is labeled **seam-level** with an explicit "does NOT pin the fail-open conversion" disclaimer; (b) the subprocess test is labeled **outer-boundary, subprocess** with its `hasattr(os, "geteuid")` + `os.geteuid() == 0` skipif gating called out; (c) the in-process fallback is labeled **outer-boundary, platform-agnostic** with "Runs without a skipif" emphasized. Closing paragraph rewritten to say "the two outer-boundary tests prove the contract on every platform" instead of "the two tests together prove the contract", with an explicit note that the seam test catches a different regression class (`had_errors` gate deletion or `report(prefix=...)` rendering changes) that the outer-boundary tests would not detect because they force root-level raises rather than per-file failures. |
| **Round 7 Low (Scope Notes smoke-setup test count)**: The Scope Notes row for `tests/test_containment_smoke_setup.py` at line 109 still described the new file as having **two focused tests**, but the File Structure row at line 140 correctly said three tests (the Round 6 in-process fallback was added there) and Task 9's verification inventory at line 2051 included the third test in its run. An implementer using the Scope Notes as the quick checklist could stop one test short. Same drift class as Finding 1: a Round 6 test-count update did not propagate back to an earlier summary row. | Updated the Scope Notes row to say **three focused tests** and added the third bullet: `(3) Round 6 platform-agnostic in-process fallback calling the extracted _run_with_wrapper(argv) function directly with monkeypatched os.listdir, pinning the same fail-FAST SystemExit(1) + wrapper-prefixed stderr contract on root/Windows where the subprocess chmod test skips`. Also bumped the constraint-list header at line 115 from "six rounds of adversarial review" to "seven rounds" to record this review pass in the same place all prior round counts are tracked. |

**Explicit design decisions documented:**

Three forced design decisions live in the "Design Decisions" section at the top of this plan:

1. **Dangling shakedown root symlink** → corruption, not first-run. Tested in Task 4 (`test_clean_stale_files_raises_on_dangling_root_symlink`) and manually verified in Task 7 Step 6.
2. **Enumeration primitive is `os.listdir()` + `fnmatch.fnmatch()`**, not `Path.glob()`. `Path.glob()` silently returns `[]` on unreadable directories (verified empirically on Python 3.14); `os.listdir()` raises loudly. Tested in Task 4 (`test_clean_stale_files_raises_when_enumeration_fails` + `test_clean_stale_files_raises_when_root_directory_unreadable`) and manually verified in Task 7 Step 7 via a real `chmod 0o000` scenario through the wrapper script. Scale tradeoff is noted inline (materializing the full directory listing is acceptable at current shakedown scale; `os.scandir()` is a drop-in replacement if the envelope ever grows).
3. **Fail-Open Hook Policy for `containment_lifecycle.py`**: `main()` at lines 184-188 deliberately catches every internal exception and returns `0`, because `SubagentStart` treats non-zero exit codes as "block the spawn" and a containment-state defect must not escalate into blocking unrelated agent spawns. T-03 enriches the stderr surface but does not change this exit-code contract. The contract shape is documented as a table of (failure class → stderr strings + exit code) pairs in the design decision. Locked in by constraint #11 in the Key correctness constraints list so a future maintainer cannot silently flip the policy. Round 5 added an explicit hook-stderr-monitoring assumption note distinguishing this context from the MCP-server stderr precedent at [`docs/tickets/closed-tickets/2026-02-15-plan-review-errata.md:439`](../../tickets/closed-tickets/2026-02-15-plan-review-errata.md). Tested in Task 8 via **two complementary lifecycle tests**: (a) `test_subagent_start_surfaces_cleanup_enumeration_failure` (subprocess via `_run_lifecycle` + real `chmod 0o000`, the authoritative end-to-end proof on supported platforms; SKIPs on root/Windows), and (b) `test_main_fail_open_conversion_via_monkeypatched_listdir` (Round 5 — platform-agnostic in-process fallback that calls `lifecycle.main()` directly with monkeypatched `os.listdir`, runs on every platform, ensures root/Windows still pin the contract). Both pin the dual-assertion contract (`exit_code == 0` AND stderr contains caller-prefixed actionable context). The smoke-setup script's structurally different fail-FAST contract (exit 1, not exit 0) is now pinned by **two complementary tests** mirroring the lifecycle pair: (c) Round 5's `test_prepare_scenario_surfaces_cleanup_enumeration_failure` (subprocess via `_run_smoke_setup` + real `chmod 0o000`, authoritative end-to-end proof on non-root POSIX; SKIPs on root/Windows) and (d) Round 6's `test_prepare_scenario_main_wrapper_fail_fast_via_monkeypatched_listdir` (platform-agnostic in-process fallback calling the extracted `_run_with_wrapper(argv)` function directly with monkeypatched `os.listdir`, runs on every platform). The Round 6 testability refactor that extracts the `__main__` block's try/except into `_run_with_wrapper()` is **behavior-preserving** (same stderr text `containment_smoke_setup failed: <exc>`, same `SystemExit(1)` on any exception, same `SystemExit(main(argv))` happy path) — no contract change, only structural. The smoke-setup fail-FAST contract is not a forced T-03 design decision because it is pre-existing in the script, but T-03 now adds two regression tests for it AND makes it testable in-process via the Round 6 refactor, so both outer-boundary contract shapes (fail-OPEN and fail-FAST) are pinned on every platform regardless of `os.geteuid` availability.

**Placeholder scan:** No "TBD", "TODO", "implement later", or hand-waved language. Every test body, code replacement, and expected output is inlined.

**Type consistency:**
- `CleanStaleResult.removed`, `skipped_fresh`: `tuple[Path, ...]`
- `failed_stat`, `failed_unlink`: `tuple[tuple[Path, str], ...]`
- `clean_stale_files` return type: `CleanStaleResult` (never `None`)
- `had_errors`: `@property` (no parentheses on access)
- `report`: method signature `report(self, prefix: str = "") -> str`
- Every caller uses the correct prefix: `""` (wrapper), `"containment-lifecycle: "` (lifecycle), `"containment_smoke_setup: "` (smoke_setup)
- Every `monkeypatch.setattr(Path, …)`, every `monkeypatch.setattr(os, "listdir", …)` (or its dotted-string equivalent `monkeypatch.setattr("os.listdir", …)`), every `monkeypatch.setattr(smoke_setup, "_scenario_definition", …)`, AND the Round 5 in-process fallback's `monkeypatch.setattr("os.listdir", …)` + `monkeypatch.setenv("CLAUDE_PLUGIN_DATA", …)` + `monkeypatch.setattr("sys.stdin", …)` triple is inside `with monkeypatch.context() as patched:` so the patch reverts before later assertions run real I/O, touch unpatched module globals, or call `capsys.readouterr()` outside the patched scope

**Risk verification:**
- Existing `test_clean_stale_files_removes_old_state_only` continues passing (Task 1) and is tightened in Task 6
- Existing non-test callers are updated in Task 8 with additive changes only (clean runs behave identically)
- Existing `tests/test_containment_lifecycle.py` tests run in Task 8 Step 7 to catch regression before commit
- The new `tests/test_containment_smoke_setup.py` file establishes the testing location for future smoke-setup coverage
- Branch is `fix/t03-stale-cleanup-observability` cut from `origin/main` directly; no PR-pollution risk from ahead-only local `main`
- `report()` emits failures in `os.listdir()` directory-entry order, which is platform-dependent; tests use single-element or set-based assertions rather than full-list order comparisons to avoid flakiness
- All **three** `chmod 0o000` tests restore `chmod 0o755` in a `finally` block so pytest's `tmp_path` fixture can tear down the directory even if the test body raises — verified by inspection of (a) `test_clean_stale_files_raises_when_root_directory_unreadable` in Task 4 (helper-level), (b) `test_subagent_start_surfaces_cleanup_enumeration_failure` subprocess test in Task 8 (lifecycle caller boundary, fail-open contract), and (c) Round 5's `test_prepare_scenario_surfaces_cleanup_enumeration_failure` subprocess test in Task 8 (smoke-setup caller boundary, fail-fast contract). All three tests share the same `@pytest.mark.skipif(not hasattr(os, "geteuid") or os.geteuid() == 0, …)` decorator so they skip consistently on the same platforms
- The lifecycle subprocess test uses the existing `_run_lifecycle` helper at `test_containment_lifecycle.py:41-54` (which invokes the script via `subprocess.run([sys.executable, SCRIPT], …)` with `CLAUDE_PLUGIN_DATA` injected via `env`). No new subprocess plumbing is introduced for lifecycle — the test reuses the established pattern, which means a breakage in that helper would surface in existing lifecycle tests before reaching the new one
- Round 5's smoke-setup subprocess test introduces a parallel `_run_smoke_setup` helper modeled on `_run_lifecycle` (same shape: `subprocess.run([sys.executable, SCRIPT, *argv], capture_output=True, text=True)`). The deliberate divergence is that `_run_smoke_setup` does NOT pass `env=` because smoke-setup uses `--data-dir` for data directory override; the subprocess inherits the parent environment unmodified
- Round 5's in-process fallback test `test_main_fail_open_conversion_via_monkeypatched_listdir` runs on every platform regardless of `os.geteuid` availability — verified by inspection that it has no `@pytest.mark.skipif` decorator and uses pure monkeypatching (`os.listdir`, `sys.stdin`, `CLAUDE_PLUGIN_DATA`) instead of real chmod. This guarantees that root and Windows CI runs still have automated coverage of the lifecycle fail-open conversion contract through `main()`'s outer except block, which the subprocess chmod test cannot provide on those platforms
- Round 5's wrapper signal-to-noise change (Task 7 Step 2 gating `print` on `had_errors`) is verified by Task 7 Step 4 and Step 5 manual probes (expected stderr empty on clean and first-run paths). The internal callers (lifecycle, smoke-setup) were already gated on `had_errors` since the original draft, so this change brings the wrapper into alignment with them rather than introducing a new pattern
- Round 6's `_run_with_wrapper` testability refactor (Task 8 Step 2, second edit block) is **behavior-preserving** by inspection of the three preserved invariants: (1) stderr text is identical (`containment_smoke_setup failed: {exc}`), (2) `SystemExit(1)` is raised on any `Exception` caught from `main(argv)`, (3) happy-path `SystemExit(main(argv))` propagates the main-returned exit code unchanged (because `SystemExit` inherits from `BaseException` and is not caught by `except Exception`). The only structural change is that the try/except moves from the `__main__` guard block into a module-level `_run_with_wrapper(argv)` function, which the `__main__` block now dispatches to via a single `_run_with_wrapper()` call. Ruff's redundant-call detection and the existing smoke-setup subprocess test both catch regressions to any of the three invariants
- Round 6's in-process fallback `test_prepare_scenario_main_wrapper_fail_fast_via_monkeypatched_listdir` runs on every platform regardless of `os.geteuid` availability — verified by inspection that it has no `@pytest.mark.skipif` decorator and uses pure monkeypatching (`os.listdir` only) instead of real chmod. This closes the Round 5 coverage gap where smoke-setup's outer-boundary contract was only pinned on non-root POSIX: the subprocess chmod test still covers the real OS-level boundary when the platform allows it, and the Round 6 in-process fallback guarantees the language-level wrapper conversion contract is pinned everywhere else (root, Windows, any future CI environment without chmod support)
- Round 6's new monkeypatch (`monkeypatch.setattr("os.listdir", _raising_listdir)` in `test_prepare_scenario_main_wrapper_fail_fast_via_monkeypatched_listdir`) is inside `with monkeypatch.context() as patched:` per constraint #6, matching the pattern of the Round 5 lifecycle fallback and every other monkeypatch in this plan. No unscoped monkeypatches are introduced
