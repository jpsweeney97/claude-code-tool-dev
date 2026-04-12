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
    # Register in sys.modules before exec_module so that Python 3.14's
    # dataclass annotation resolution (which calls sys.modules[cls.__module__])
    # can find the module. Without this, frozen dataclasses with string
    # annotations (from __future__ import annotations) raise AttributeError
    # on NoneType when the module is not in sys.modules.
    sys.modules[module.__name__] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(module.__name__, None)
        raise
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
    ``prepare_scenario``, out of ``main()``, and is caught by
    ``_run_with_wrapper()`` in ``containment_smoke_setup.py`` (the Round 6
    testability refactor extracted from the ``__main__`` block), which
    prints ``"containment_smoke_setup failed: <exc>"`` to stderr and raises
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
