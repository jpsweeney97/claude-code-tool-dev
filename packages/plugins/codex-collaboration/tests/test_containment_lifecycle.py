"""Tests for containment_lifecycle.py hook behavior."""

from __future__ import annotations

import importlib.util
import io
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from server import containment
from server.containment import (
    active_run_path,
    read_json_file,
    scope_file_path,
    seed_file_path,
    smoke_control_path,
    transcript_done_path,
    transcript_error_path,
    transcript_path,
    write_json_file,
    write_text_file,
)

SCRIPT = str(
    Path(__file__).resolve().parent.parent / "scripts" / "containment_lifecycle.py"
)


def _load_lifecycle_module():
    spec = importlib.util.spec_from_file_location(
        "test_containment_lifecycle_module",
        SCRIPT,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run_lifecycle(
    payload: dict[str, object],
    *,
    data_dir: Path,
) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["CLAUDE_PLUGIN_DATA"] = str(data_dir)
    return subprocess.run(
        [sys.executable, SCRIPT],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
    )


def _seed_payload(
    *,
    session_id: str = "session-1",
    run_id: str = "run-1",
) -> dict[str, object]:
    return {
        "session_id": session_id,
        "run_id": run_id,
        "file_anchors": ["/repo/anchor.txt"],
        "scope_directories": ["/repo"],
        "created_at": "2026-04-08T00:00:00Z",
    }


def test_subagent_start_missing_active_run_exits_cleanly(tmp_path: Path) -> None:
    result = _run_lifecycle(
        {
            "hook_event_name": "SubagentStart",
            "session_id": "session-1",
            "agent_id": "agent-1",
        },
        data_dir=tmp_path,
    )

    assert result.returncode == 0
    assert not scope_file_path(tmp_path, "run-1").exists()


def test_subagent_start_promotes_seed_to_scope(tmp_path: Path) -> None:
    write_text_file(active_run_path(tmp_path, "session-1"), "run-1")
    write_json_file(seed_file_path(tmp_path, "run-1"), _seed_payload())

    result = _run_lifecycle(
        {
            "hook_event_name": "SubagentStart",
            "session_id": "session-1",
            "agent_id": "agent-1",
        },
        data_dir=tmp_path,
    )

    assert result.returncode == 0
    scope = read_json_file(scope_file_path(tmp_path, "run-1"))
    assert scope is not None
    assert scope["agent_id"] == "agent-1"
    assert not seed_file_path(tmp_path, "run-1").exists()


def test_subagent_start_duplicate_scope_is_noop(tmp_path: Path) -> None:
    write_text_file(active_run_path(tmp_path, "session-1"), "run-1")
    write_json_file(seed_file_path(tmp_path, "run-1"), _seed_payload())
    write_json_file(
        scope_file_path(tmp_path, "run-1"),
        {
            **_seed_payload(),
            "agent_id": "agent-original",
        },
    )

    result = _run_lifecycle(
        {
            "hook_event_name": "SubagentStart",
            "session_id": "session-1",
            "agent_id": "agent-1",
        },
        data_dir=tmp_path,
    )

    assert result.returncode == 0
    scope = read_json_file(scope_file_path(tmp_path, "run-1"))
    assert scope is not None
    assert scope["agent_id"] == "agent-original"
    assert seed_file_path(tmp_path, "run-1").exists()
    assert "scope already exists" in result.stderr.lower()


def test_subagent_start_smoke_control_delay_calls_sleep(tmp_path: Path) -> None:
    module = _load_lifecycle_module()
    write_text_file(active_run_path(tmp_path, "session-1"), "run-1")
    write_json_file(seed_file_path(tmp_path, "run-1"), _seed_payload())
    write_json_file(
        smoke_control_path(tmp_path, "run-1"),
        {"start_behavior": "delay", "delay_ms": 125},
    )
    calls: list[float] = []

    def _fake_sleep(seconds: float) -> None:
        calls.append(seconds)

    module.time.sleep = _fake_sleep
    module.handle_payload(
        {
            "hook_event_name": "SubagentStart",
            "session_id": "session-1",
            "agent_id": "agent-1",
        },
        data_dir=tmp_path,
    )

    assert calls == [0.125]
    assert scope_file_path(tmp_path, "run-1").exists()


def test_subagent_start_smoke_control_disable_leaves_seed_in_place(
    tmp_path: Path,
) -> None:
    module = _load_lifecycle_module()
    write_text_file(active_run_path(tmp_path, "session-1"), "run-1")
    write_json_file(seed_file_path(tmp_path, "run-1"), _seed_payload())
    write_json_file(
        smoke_control_path(tmp_path, "run-1"),
        {"start_behavior": "disable"},
    )

    module.handle_payload(
        {
            "hook_event_name": "SubagentStart",
            "session_id": "session-1",
            "agent_id": "agent-1",
        },
        data_dir=tmp_path,
    )

    assert not scope_file_path(tmp_path, "run-1").exists()
    assert seed_file_path(tmp_path, "run-1").exists()


def test_subagent_stop_copies_transcript_and_removes_scope(tmp_path: Path) -> None:
    write_text_file(active_run_path(tmp_path, "session-1"), "run-1")
    write_json_file(
        scope_file_path(tmp_path, "run-1"),
        {
            **_seed_payload(),
            "agent_id": "agent-1",
        },
    )
    source = tmp_path / "agent-transcript.jsonl"
    source.write_text('{"message":"done"}\n', encoding="utf-8")

    result = _run_lifecycle(
        {
            "hook_event_name": "SubagentStop",
            "session_id": "session-1",
            "agent_id": "agent-1",
            "agent_transcript_path": str(source),
        },
        data_dir=tmp_path,
    )

    assert result.returncode == 0
    assert transcript_path(tmp_path, "run-1").read_text(encoding="utf-8") == source.read_text(
        encoding="utf-8"
    )
    assert transcript_done_path(tmp_path, "run-1").exists()
    assert not scope_file_path(tmp_path, "run-1").exists()


def test_subagent_stop_writes_error_marker_on_copy_failure(tmp_path: Path) -> None:
    write_text_file(active_run_path(tmp_path, "session-1"), "run-1")
    write_json_file(
        scope_file_path(tmp_path, "run-1"),
        {
            **_seed_payload(),
            "agent_id": "agent-1",
        },
    )

    result = _run_lifecycle(
        {
            "hook_event_name": "SubagentStop",
            "session_id": "session-1",
            "agent_id": "agent-1",
            "agent_transcript_path": str(tmp_path / "missing.jsonl"),
        },
        data_dir=tmp_path,
    )

    assert result.returncode == 0
    assert transcript_error_path(tmp_path, "run-1").exists()
    assert not scope_file_path(tmp_path, "run-1").exists()


def test_subagent_stop_missing_transcript_path_writes_error_marker(tmp_path: Path) -> None:
    write_text_file(active_run_path(tmp_path, "session-1"), "run-1")
    write_json_file(
        scope_file_path(tmp_path, "run-1"),
        {
            **_seed_payload(),
            "agent_id": "agent-1",
        },
    )

    result = _run_lifecycle(
        {
            "hook_event_name": "SubagentStop",
            "session_id": "session-1",
            "agent_id": "agent-1",
        },
        data_dir=tmp_path,
    )

    assert result.returncode == 0
    assert transcript_error_path(tmp_path, "run-1").exists()
    assert not scope_file_path(tmp_path, "run-1").exists()


def test_subagent_stop_agent_id_mismatch_keeps_scope(tmp_path: Path) -> None:
    write_text_file(active_run_path(tmp_path, "session-1"), "run-1")
    write_json_file(
        scope_file_path(tmp_path, "run-1"),
        {
            **_seed_payload(),
            "agent_id": "agent-expected",
        },
    )

    result = _run_lifecycle(
        {
            "hook_event_name": "SubagentStop",
            "session_id": "session-1",
            "agent_id": "agent-other",
            "agent_transcript_path": str(tmp_path / "missing.jsonl"),
        },
        data_dir=tmp_path,
    )

    assert result.returncode == 0
    assert scope_file_path(tmp_path, "run-1").exists()
    assert not transcript_error_path(tmp_path, "run-1").exists()


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
