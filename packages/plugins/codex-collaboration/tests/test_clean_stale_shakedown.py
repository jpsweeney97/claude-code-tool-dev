"""Tests for clean_stale_shakedown.py CLI wrapper behavior.

Closes the coverage gap identified by PR #104's test-analyzer review:
before this file existed, ``scripts/clean_stale_shakedown.py`` had zero
direct tests despite being the primary CLI entry point into
``clean_stale_files``. These tests pin:

1. **Round 5 Choice 3B** — ``main()`` is silent on clean runs (no stderr
   chatter when ``CleanStaleResult.had_errors`` is False). Without a
   regression guard, a future refactor could quietly reverse the gate and
   train operators to ignore cleanup stderr.
2. **Per-file failure reporting** — ``had_errors=True`` emits the full
   ``CleanStaleResult.report()`` (summary line + per-failure lines) to
   stderr so operators can distinguish clean sweeps from failure sweeps.
3. **Env-var validation** — missing or non-directory ``CLAUDE_PLUGIN_DATA``
   exits ``1`` with operator-actionable context.
4. **Fail-FAST ``__main__`` wrapper** — unexpected exceptions from
   ``main()`` are converted by the outer try/except block into
   ``SystemExit(1)`` with a ``clean_stale_shakedown failed: unexpected
   error`` stderr prefix, mirroring ``containment_smoke_setup.py``'s
   fail-FAST contract in explicit contrast to
   ``containment_lifecycle.py``'s fail-OPEN policy.
"""

from __future__ import annotations

import importlib.util
import os
import runpy
import subprocess
import sys
from pathlib import Path

import pytest

from server import containment
from server.containment import CleanStaleResult, FileFailure

SCRIPT = str(
    Path(__file__).resolve().parent.parent / "scripts" / "clean_stale_shakedown.py"
)


def _load_shakedown_module():
    """Load clean_stale_shakedown.py as an in-process module.

    Parallels ``_load_lifecycle_module`` in ``test_containment_lifecycle.py``.
    No ``sys.modules`` registration needed because ``clean_stale_shakedown.py``
    defines no frozen dataclasses — see ``_load_smoke_setup_module`` in
    ``test_containment_smoke_setup.py`` for the Python 3.14 workaround that
    applies only to modules that contain dataclass definitions with
    ``from __future__ import annotations``.
    """
    spec = importlib.util.spec_from_file_location(
        "test_clean_stale_shakedown_module",
        SCRIPT,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run_shakedown(
    *,
    data_dir: Path | None,
) -> subprocess.CompletedProcess[str]:
    """Invoke clean_stale_shakedown.py as a subprocess.

    Parallels ``_run_lifecycle`` in ``test_containment_lifecycle.py``.
    Copies the parent environment and overrides ``CLAUDE_PLUGIN_DATA``
    (or removes it when ``data_dir`` is ``None``), so the subprocess
    inherits tooling env vars like ``PATH`` without leaking
    ``CLAUDE_PLUGIN_DATA`` from the test runner's shell.
    """
    env = dict(os.environ)
    if data_dir is None:
        env.pop("CLAUDE_PLUGIN_DATA", None)
    else:
        env["CLAUDE_PLUGIN_DATA"] = str(data_dir)
    return subprocess.run(
        [sys.executable, SCRIPT],
        capture_output=True,
        text=True,
        env=env,
    )


# ===== In-process main() wiring tests =====


def test_clean_stale_shakedown_is_silent_on_clean_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Round 5 Choice 3B regression guard: clean runs produce no stderr.

    The wrapper gates ``print(result.report(), file=sys.stderr)`` on
    ``result.had_errors`` specifically so operators see cleanup stderr
    only when something went wrong. If a future refactor unconditionally
    prints the report on every invocation, operators would learn to
    discount cleanup stderr and miss real errors — the contract protected
    by this test is "silence on success, loud on failure", not "always
    report".
    """
    data_dir = tmp_path
    (data_dir / "shakedown").mkdir(parents=True)

    monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(data_dir))

    module = _load_shakedown_module()
    exit_code = module.main()

    assert exit_code == 0
    captured = capsys.readouterr()
    assert captured.err == "", (
        "clean run must leave stderr empty (Round 5 Choice 3B); "
        f"got stderr={captured.err!r}"
    )
    assert captured.out == ""


def test_clean_stale_shakedown_emits_report_on_had_errors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Per-file failures captured in CleanStaleResult surface via stderr.

    ``main()`` performs a delayed ``from server.containment import
    clean_stale_files`` inside the function body, so patching
    ``containment.clean_stale_files`` before calling ``main()`` is
    sufficient — the ``from ... import`` line resolves the attribute at
    call time from the already-cached ``server.containment`` module.
    """
    data_dir = tmp_path
    shakedown = data_dir / "shakedown"
    shakedown.mkdir(parents=True)

    monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(data_dir))

    failure_path = shakedown / "seed-stub.json"

    def _stub_clean_stale_files(_shakedown_path: Path) -> CleanStaleResult:
        return CleanStaleResult(
            removed=(),
            skipped_fresh=(),
            failed_stat=(),
            failed_unlink=(FileFailure(failure_path, "OSError(1, 'simulated unlink failure')"),),
        )

    monkeypatch.setattr(containment, "clean_stale_files", _stub_clean_stale_files)

    module = _load_shakedown_module()
    exit_code = module.main()

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "clean_stale_files:" in captured.err, (
        "had_errors=True must emit the summary line; "
        f"got stderr={captured.err!r}"
    )
    assert "failed_unlink=1" in captured.err, (
        "summary line must reflect the failed_unlink bucket count; "
        f"got stderr={captured.err!r}"
    )
    assert "seed-stub.json" in captured.err, (
        "report must include the failing path; "
        f"got stderr={captured.err!r}"
    )
    assert "simulated unlink failure" in captured.err, (
        "report must include the captured error repr; "
        f"got stderr={captured.err!r}"
    )


def test_clean_stale_shakedown_exits_1_when_env_var_missing(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Missing CLAUDE_PLUGIN_DATA exits 1 with an actionable stderr line."""
    monkeypatch.delenv("CLAUDE_PLUGIN_DATA", raising=False)

    module = _load_shakedown_module()
    exit_code = module.main()

    assert exit_code == 1
    captured = capsys.readouterr()
    assert (
        "clean_stale_shakedown failed: CLAUDE_PLUGIN_DATA not set"
        in captured.err
    ), (
        "missing env var must surface with the canonical caller prefix; "
        f"got stderr={captured.err!r}"
    )


def test_clean_stale_shakedown_exits_1_when_env_var_is_regular_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """CLAUDE_PLUGIN_DATA pointing at a regular file exits 1 with operator context.

    ``is_dir()`` returns False for regular files, broken symlinks, and
    missing paths alike, so this one test covers the whole "env var set
    but not a directory" failure class.
    """
    regular_file = tmp_path / "not_a_directory"
    regular_file.write_text("oops", encoding="utf-8")

    monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(regular_file))

    module = _load_shakedown_module()
    exit_code = module.main()

    assert exit_code == 1
    captured = capsys.readouterr()
    assert (
        "clean_stale_shakedown failed: CLAUDE_PLUGIN_DATA is not a directory"
        in captured.err
    ), (
        "non-directory env var must surface with the canonical caller prefix; "
        f"got stderr={captured.err!r}"
    )


# ===== Outer __main__ wrapper (fail-FAST boundary) tests =====


@pytest.mark.skipif(
    not hasattr(os, "geteuid") or os.geteuid() == 0,
    reason=(
        "chmod 0o000 permission checks are bypassed when running as root; "
        "os.geteuid is unavailable on Windows"
    ),
)
def test_clean_stale_shakedown_subprocess_fails_fast_on_unreadable_shakedown(
    tmp_path: Path,
) -> None:
    """Root-level cleanup failure surfaces through the ``__main__`` wrapper's
    **fail-FAST** boundary (subprocess end-to-end).

    Real ``chmod 0o000`` on the shakedown directory makes
    ``clean_stale_files`` raise ``OSError('clean_stale_files failed:
    cannot enumerate shakedown root. …')`` from Stage 3. That exception
    propagates out of ``main()`` and is caught by the ``__main__`` block's
    ``try/except Exception``, which prints ``"clean_stale_shakedown failed:
    unexpected error. Got: <repr(exc)>"`` to stderr and raises
    ``SystemExit(1)``.

    This is the ``clean_stale_shakedown`` counterpart to
    ``test_subagent_start_surfaces_cleanup_enumeration_failure``
    (lifecycle fail-OPEN, exit ``0``) and
    ``test_prepare_scenario_surfaces_cleanup_enumeration_failure``
    (smoke-setup fail-FAST, exit ``1``). The three callers together pin
    two distinct outer-boundary contracts — ``clean_stale_shakedown``
    uses fail-FAST because it is a CLI tool invoked directly by operators
    or the shakedown-b1 harness, not a hook, so loud failure is the
    correct default.

    The subprocess pattern is mandatory here: an in-process call to
    ``main()`` would bypass the ``__main__`` wrapper entirely and
    therefore could not observe the exception-to-exit-code conversion,
    which is exactly the contract under test. The sibling
    ``test_clean_stale_shakedown_wrapper_converts_exception_to_exit_1_via_runpy``
    uses ``runpy.run_path(..., run_name="__main__")`` to pin the same
    contract on root/Windows where ``chmod 0o000`` skips.

    Skipped when running as root (POSIX permission checks are bypassed)
    or on platforms without ``os.geteuid`` (e.g., Windows).
    """
    data_dir = tmp_path
    shakedown = data_dir / "shakedown"
    shakedown.mkdir(parents=True)
    (shakedown / "scope-run-1.json").write_text("{}", encoding="utf-8")

    try:
        os.chmod(shakedown, 0o000)
        result = _run_shakedown(data_dir=data_dir)
    finally:
        # Restore permissions so pytest's tmp_path teardown can walk
        # into the directory. This MUST happen even if the assertions
        # below fail, otherwise tmp_path cleanup raises and masks the
        # real failure.
        os.chmod(shakedown, 0o755)

    # Fail-FAST contract: the CLI wrapper exits 1 on any internal error
    # (the opposite of lifecycle's fail-OPEN exit 0). Deliberate — the
    # shakedown cleanup script is an operator tool, not a hook.
    assert result.returncode == 1, (
        "clean_stale_shakedown must fail-fast on root-level cleanup failure "
        "(exit 1); "
        f"got exit={result.returncode}, stdout={result.stdout!r}, "
        f"stderr={result.stderr!r}"
    )
    assert "clean_stale_shakedown failed: unexpected error" in result.stderr, (
        "__main__ wrapper must wrap internal errors with its caller prefix; "
        f"got stderr={result.stderr!r}"
    )
    assert "cannot enumerate shakedown root" in result.stderr, (
        "wrapped error must carry the clean_stale_files failure context "
        f"(Stage 3 enumeration); got stderr={result.stderr!r}"
    )


def test_clean_stale_shakedown_wrapper_converts_exception_to_exit_1_via_runpy(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Platform-agnostic proof that the ``__main__`` wrapper converts a
    cleanup ``OSError`` to ``SystemExit(1)`` + caller-prefixed stderr context.

    This test complements (does not replace)
    ``test_clean_stale_shakedown_subprocess_fails_fast_on_unreadable_shakedown``,
    which uses real ``chmod 0o000`` + subprocess for the end-to-end proof.
    The subprocess test is the authoritative end-to-end proof WHEN the
    platform supports it (non-root POSIX with ``os.geteuid``); when that
    test SKIPs (root or Windows), this in-process fallback still pins the
    ``__main__``-level exception-to-``SystemExit(1)`` conversion via
    monkeypatched ``os.listdir``.

    Why both tests are necessary (parallel to Round 5 lifecycle resolution
    and Round 6 smoke-setup resolution):

    - The subprocess test exercises the REAL OS-level subprocess boundary
      including argv parsing, env-var lookup, ``SystemExit`` raised by
      ``raise SystemExit(main())``, and the outer ``try/except Exception``.
      That end-to-end behavior cannot be proven by an in-process call.
    - This in-process test runs on every platform regardless of
      ``geteuid`` availability, ensuring root and Windows still have
      automated coverage of the specific ``exception → SystemExit(1) +
      stderr log`` conversion in the ``__main__`` wrapper.

    Implementation: ``runpy.run_path(SCRIPT, run_name="__main__")``
    executes the script with ``__name__ == "__main__"``, so the outer
    ``if __name__ == "__main__":`` block runs. Unlike
    ``containment_smoke_setup.py`` (which has a Round 6
    ``_run_with_wrapper()`` extraction for direct in-process calls),
    ``clean_stale_shakedown.py`` keeps its wrapper inlined, so
    ``runpy.run_path`` is the minimum-intrusive way to exercise the
    wrapper boundary without modifying production code. ``capsys``
    captures stderr because the executed script writes via ``print(...,
    file=sys.stderr)`` which resolves to pytest's replaced ``sys.stderr``
    at print time.

    Relies on ``server/containment.py`` using module-scope ``import os``
    and calling ``os.listdir(...)`` via attribute lookup at call time. A
    future refactor that changes to ``from os import listdir`` would
    silently break this test (the attribute binding would be captured at
    import time, not at call time), in which case the monkeypatch would
    become a no-op and the test would fail because ``SystemExit(1)`` is
    never raised.

    Runs on every platform (no skipif).
    """
    data_dir = tmp_path
    shakedown = data_dir / "shakedown"
    shakedown.mkdir(parents=True)
    (shakedown / "scope-run-1.json").write_text("{}", encoding="utf-8")

    monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(data_dir))

    def _raising_listdir(path: object, /) -> list[str]:
        raise PermissionError(13, "Permission denied", str(path))

    monkeypatch.setattr("os.listdir", _raising_listdir)

    with pytest.raises(SystemExit) as exc_info:
        runpy.run_path(SCRIPT, run_name="__main__")

    assert exc_info.value.code == 1, (
        "clean_stale_shakedown __main__ wrapper must exit 1 on unexpected "
        "error; "
        f"got SystemExit code={exc_info.value.code!r}"
    )
    captured = capsys.readouterr()
    assert "clean_stale_shakedown failed: unexpected error" in captured.err, (
        "__main__ wrapper must wrap internal errors with its caller prefix; "
        f"got stderr={captured.err!r}"
    )
    assert "cannot enumerate shakedown root" in captured.err, (
        "wrapped error must carry the clean_stale_files Stage 3 context; "
        f"got stderr={captured.err!r}"
    )
