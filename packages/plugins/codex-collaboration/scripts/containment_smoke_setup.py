#!/usr/bin/env python3
"""Prepare and clean up T4 containment smoke scenarios."""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Add package root to sys.path for server imports.
_PACKAGE_ROOT = Path(__file__).resolve().parent.parent
if str(_PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(_PACKAGE_ROOT))

from server.containment import (  # noqa: E402
    active_run_path,
    clean_stale_files,
    derive_scope_directories,
    read_active_run_id,
    scope_file_path,
    seed_file_path,
    shakedown_dir,
    smoke_control_path,
    transcript_done_path,
    write_json_file,
    write_text_file,
)

_SPAWN_AGENT = "spawn_agent"
_MAIN_THREAD_TOOL = "main_thread_tool"
_POST_RUN_CHECK = "post_run_check"


@dataclass(frozen=True)
class RepoPaths:
    """Concrete B1 paths used by the smoke scaffolding."""

    repo_root: Path
    contracts: Path
    delivery: Path
    foundations: Path
    mcp_server: Path
    dialogue: Path
    out_of_scope: Path

    @property
    def file_anchors(self) -> list[str]:
        return [
            str(self.contracts),
            str(self.delivery),
            str(self.mcp_server),
        ]

    @property
    def scope_directories(self) -> list[str]:
        return derive_scope_directories(self.file_anchors)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Prepare and clean up T4 containment smoke scenarios.",
    )
    parser.add_argument("--data-dir", help="Override CLAUDE_PLUGIN_DATA")
    parser.add_argument("--repo-root", help="Repository root for B1 fixture paths")
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare = subparsers.add_parser("prepare")
    prepare.add_argument("scenario_id")
    prepare.add_argument("--session-id")
    prepare.add_argument("--run-id")
    prepare.add_argument("--delay-ms", type=int, default=1700)

    cleanup = subparsers.add_parser("cleanup")
    cleanup.add_argument("run_id")
    cleanup.add_argument("--session-id")

    args = parser.parse_args(argv)
    data_dir = _resolve_data_dir(args.data_dir)

    if args.command == "prepare":
        repo_paths = _repo_paths(args.repo_root)
        recipe = prepare_scenario(
            scenario_id=args.scenario_id,
            data_dir=data_dir,
            repo_paths=repo_paths,
            session_id=args.session_id,
            run_id=args.run_id,
            delay_ms=args.delay_ms,
        )
        print(json.dumps(recipe, indent=2, sort_keys=True))
        return 0

    cleanup_scenario(
        run_id=args.run_id,
        data_dir=data_dir,
        session_id=args.session_id,
    )
    return 0


def prepare_scenario(
    *,
    scenario_id: str,
    data_dir: Path,
    repo_paths: RepoPaths,
    session_id: str | None,
    run_id: str | None,
    delay_ms: int = 1700,
) -> dict[str, Any]:
    """Write scenario state and return the operator recipe."""

    cleanup_result = clean_stale_files(shakedown_dir(data_dir))
    if cleanup_result.had_errors:
        print(
            cleanup_result.report(prefix="containment_smoke_setup: "),
            file=sys.stderr,
        )
    resolved_session_id = session_id or _read_session_id(data_dir)
    resolved_run_id = run_id or str(uuid.uuid4())
    _assert_no_live_conflict(
        data_dir=data_dir,
        session_id=resolved_session_id,
        run_id=resolved_run_id,
    )

    scenario = _scenario_definition(scenario_id, repo_paths=repo_paths)
    files_written: list[str] = []

    if scenario_id in {
        "scope_file_create",
        "read_allow_anchor",
        "read_allow_scope_directory",
        "read_deny_out_of_scope",
        "grep_rewrite_path_targeted",
        "glob_rewrite_path_targeted",
        "grep_pathless_deny",
        "glob_pathless_deny",
        "poll_success",
        "poll_timeout_deny",
    }:
        files_written.extend(
            _write_seed_state(
                data_dir=data_dir,
                session_id=resolved_session_id,
                run_id=resolved_run_id,
                repo_paths=repo_paths,
            )
        )
        if scenario_id == "poll_success":
            control = {"start_behavior": "delay", "delay_ms": delay_ms}
            write_json_file(smoke_control_path(data_dir, resolved_run_id), control)
            files_written.append(str(smoke_control_path(data_dir, resolved_run_id)))
        if scenario_id == "poll_timeout_deny":
            control = {"start_behavior": "disable"}
            write_json_file(smoke_control_path(data_dir, resolved_run_id), control)
            files_written.append(str(smoke_control_path(data_dir, resolved_run_id)))
    elif scenario_id == "main_thread_passthrough":
        files_written.extend(
            _write_scope_state(
                data_dir=data_dir,
                session_id=resolved_session_id,
                run_id=resolved_run_id,
                repo_paths=repo_paths,
                agent_id="smoke-active-agent",
            )
        )
    elif scenario_id == "agent_id_mismatch_passthrough":
        files_written.extend(
            _write_scope_state(
                data_dir=data_dir,
                session_id=resolved_session_id,
                run_id=resolved_run_id,
                repo_paths=repo_paths,
                agent_id="bogus-agent-id",
            )
        )
    elif scenario_id == "no_active_run_passthrough":
        _clear_stale_pointer(data_dir=data_dir, session_id=resolved_session_id)
    elif scenario_id == "scope_file_remove":
        if run_id is None:
            raise RuntimeError(
                "prepare failed: scope_file_remove requires --run-id from the prior "
                "scope_file_create run. Got: None"
            )
    else:
        raise RuntimeError(
            f"prepare failed: unsupported scenario_id. Got: {scenario_id!r:.100}"
        )

    return {
        "execution_kind": scenario["execution_kind"],
        "expected_branch": scenario["expected_branch"],
        "expected_evidence": scenario["expected_evidence"],
        "files_written": files_written,
        "main_thread_tool_input": scenario.get("main_thread_tool_input"),
        "prompt": scenario.get("prompt"),
        "run_id": resolved_run_id,
        "scenario_id": scenario_id,
        "session_id": resolved_session_id,
    }


def cleanup_scenario(
    *,
    run_id: str,
    data_dir: Path,
    session_id: str | None,
) -> None:
    """Remove mutable run state without deleting evidence artifacts."""

    for path in (
        seed_file_path(data_dir, run_id),
        scope_file_path(data_dir, run_id),
        smoke_control_path(data_dir, run_id),
    ):
        try:
            path.unlink()
        except FileNotFoundError:
            pass

    resolved_session_id = session_id or _safe_read_session_id(data_dir)
    if resolved_session_id is None:
        return
    pointer_path = active_run_path(data_dir, resolved_session_id)
    if read_active_run_id(data_dir, resolved_session_id) != run_id:
        return
    try:
        pointer_path.unlink()
    except FileNotFoundError:
        pass


def _resolve_data_dir(data_dir: str | None) -> Path:
    value = data_dir or os.environ.get("CLAUDE_PLUGIN_DATA")
    if not value:
        raise RuntimeError(
            "resolve data dir failed: set --data-dir or CLAUDE_PLUGIN_DATA. "
            f"Got: {value!r:.100}"
        )
    return Path(value).expanduser().resolve()


def _repo_paths(repo_root: str | None) -> RepoPaths:
    root = Path(repo_root).expanduser().resolve() if repo_root else Path.cwd().resolve()
    paths = RepoPaths(
        repo_root=root,
        contracts=root / "docs/superpowers/specs/codex-collaboration/contracts.md",
        delivery=root / "docs/superpowers/specs/codex-collaboration/delivery.md",
        foundations=root / "docs/superpowers/specs/codex-collaboration/foundations.md",
        mcp_server=root / "packages/plugins/codex-collaboration/server/mcp_server.py",
        dialogue=root / "packages/plugins/codex-collaboration/server/dialogue.py",
        out_of_scope=root / "packages/plugins/codex-collaboration/scripts/codex_guard.py",
    )
    missing = [str(path) for path in paths.__dict__.values() if isinstance(path, Path) and not path.exists()]
    if missing:
        raise RuntimeError(
            "resolve repo paths failed: required B1 fixture paths missing. "
            f"Got: {missing!r:.100}"
        )
    return paths


def _read_session_id(data_dir: Path) -> str:
    session_id = _safe_read_session_id(data_dir)
    if session_id is None:
        raise RuntimeError(
            "read session_id failed: missing session_id file. "
            f"Got: {str(data_dir / 'session_id')!r:.100}"
        )
    return session_id


def _safe_read_session_id(data_dir: Path) -> str | None:
    try:
        value = (data_dir / "session_id").read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return value or None


def _assert_no_live_conflict(*, data_dir: Path, session_id: str, run_id: str) -> None:
    existing_run_id = read_active_run_id(data_dir, session_id)
    if existing_run_id is None or existing_run_id == run_id:
        return
    if seed_file_path(data_dir, existing_run_id).exists() or scope_file_path(
        data_dir,
        existing_run_id,
    ).exists():
        raise RuntimeError(
            "prepare failed: another shakedown run is active in this session. "
            f"Got: {existing_run_id!r:.100}"
        )


def _clear_stale_pointer(*, data_dir: Path, session_id: str) -> None:
    existing_run_id = read_active_run_id(data_dir, session_id)
    if existing_run_id is None:
        return
    if seed_file_path(data_dir, existing_run_id).exists() or scope_file_path(
        data_dir,
        existing_run_id,
    ).exists():
        raise RuntimeError(
            "prepare failed: no_active_run_passthrough requires no live run state. "
            f"Got: {existing_run_id!r:.100}"
        )
    try:
        active_run_path(data_dir, session_id).unlink()
    except FileNotFoundError:
        pass


def _write_seed_state(
    *,
    data_dir: Path,
    session_id: str,
    run_id: str,
    repo_paths: RepoPaths,
) -> list[str]:
    write_text_file(active_run_path(data_dir, session_id), run_id)
    write_json_file(
        seed_file_path(data_dir, run_id),
        {
            "session_id": session_id,
            "run_id": run_id,
            "file_anchors": repo_paths.file_anchors,
            "scope_directories": repo_paths.scope_directories,
            "created_at": _timestamp(),
        },
    )
    return [
        str(active_run_path(data_dir, session_id)),
        str(seed_file_path(data_dir, run_id)),
    ]


def _write_scope_state(
    *,
    data_dir: Path,
    session_id: str,
    run_id: str,
    repo_paths: RepoPaths,
    agent_id: str,
) -> list[str]:
    write_text_file(active_run_path(data_dir, session_id), run_id)
    write_json_file(
        scope_file_path(data_dir, run_id),
        {
            "session_id": session_id,
            "run_id": run_id,
            "agent_id": agent_id,
            "file_anchors": repo_paths.file_anchors,
            "scope_directories": repo_paths.scope_directories,
            "created_at": _timestamp(),
        },
    )
    return [
        str(active_run_path(data_dir, session_id)),
        str(scope_file_path(data_dir, run_id)),
    ]


def _scenario_definition(
    scenario_id: str,
    *,
    repo_paths: RepoPaths,
) -> dict[str, Any]:
    docs_scope = repo_paths.scope_directories[0]
    scenarios: dict[str, dict[str, Any]] = {
        "scope_file_create": {
            "execution_kind": _SPAWN_AGENT,
            "expected_branch": "read_allow_anchor",
            "expected_evidence": [
                "poll-telemetry.jsonl contains a read_allow_anchor row for this run_id",
                "transcript-<run_id>.done marker exists after agent completes",
            ],
            "prompt": (
                f'Call Read once on "{repo_paths.contracts}" and stop after the first result.'
            ),
        },
        "scope_file_remove": {
            "execution_kind": _POST_RUN_CHECK,
            "expected_branch": "scope_file_remove",
            "expected_evidence": [
                "scope-<run_id>.json is absent after the agent completes",
                f"{transcript_done_path(Path('<data-dir>'), '<run_id>').name} exists for the same run",
            ],
            "prompt": None,
        },
        "read_allow_anchor": {
            "execution_kind": _SPAWN_AGENT,
            "expected_branch": "read_allow_anchor",
            "expected_evidence": ["Read succeeds on a file anchor"],
            "prompt": (
                f'Call Read once on "{repo_paths.contracts}" and stop after the first result.'
            ),
        },
        "read_allow_scope_directory": {
            "execution_kind": _SPAWN_AGENT,
            "expected_branch": "read_allow_scope_directory",
            "expected_evidence": ["Read succeeds on an in-scope non-anchor file"],
            "prompt": (
                f'Call Read once on "{repo_paths.foundations}" and stop after the first result.'
            ),
        },
        "read_deny_out_of_scope": {
            "execution_kind": _SPAWN_AGENT,
            "expected_branch": "read_deny_out_of_scope",
            "expected_evidence": ["Read is denied for an out-of-scope file"],
            "prompt": (
                f'Call Read once on "{repo_paths.out_of_scope}" and stop after the denial.'
            ),
        },
        "grep_rewrite_path_targeted": {
            "execution_kind": _SPAWN_AGENT,
            "expected_branch": "grep_rewrite_path_targeted",
            "expected_evidence": ["Grep is auto-approved with a rewritten path"],
            "prompt": (
                "Call Grep once with "
                f'pattern "TOOL_DEFINITIONS" and path "{repo_paths.mcp_server}", '
                "then stop."
            ),
        },
        "glob_rewrite_path_targeted": {
            "execution_kind": _SPAWN_AGENT,
            "expected_branch": "glob_rewrite_path_targeted",
            "expected_evidence": ["Glob is auto-approved with a rewritten directory path"],
            "prompt": (
                f'Call Glob once with pattern "*.md" and path "{docs_scope}", then stop.'
            ),
        },
        "grep_pathless_deny": {
            "execution_kind": _SPAWN_AGENT,
            "expected_branch": "grep_pathless_deny",
            "expected_evidence": ["Grep is denied without an explicit path"],
            "prompt": 'Call Grep once with pattern "ControlPlane" and no path, then stop.',
        },
        "glob_pathless_deny": {
            "execution_kind": _SPAWN_AGENT,
            "expected_branch": "glob_pathless_deny",
            "expected_evidence": ["Glob is denied without an explicit path"],
            "prompt": 'Call Glob once with pattern "*.py" and no path, then stop.',
        },
        "main_thread_passthrough": {
            "execution_kind": _MAIN_THREAD_TOOL,
            "expected_branch": "main_thread_passthrough",
            "expected_evidence": ["Main-thread Read is not constrained by shakedown scope"],
            "main_thread_tool_input": {
                "tool_name": "Read",
                "tool_input": {"file_path": str(repo_paths.out_of_scope)},
            },
            "prompt": None,
        },
        "no_active_run_passthrough": {
            "execution_kind": _SPAWN_AGENT,
            "expected_branch": "no_active_run_passthrough",
            "expected_evidence": ["Containment stays inactive without an active-run pointer"],
            "prompt": (
                f'Call Read once on "{repo_paths.out_of_scope}" and stop after the first result.'
            ),
        },
        "agent_id_mismatch_passthrough": {
            "execution_kind": _SPAWN_AGENT,
            "expected_branch": "agent_id_mismatch_passthrough",
            "expected_evidence": ["Scope exists but does not match the spawned agent_id"],
            "prompt": (
                f'Call Read once on "{repo_paths.out_of_scope}" and stop after the first result.'
            ),
        },
        "poll_success": {
            "execution_kind": _SPAWN_AGENT,
            "expected_branch": "poll_success",
            "expected_evidence": [
                "smoke-control delay leaves the guard in bootstrap poll mode",
                "scope promotion lands before the 2s timeout",
            ],
            "prompt": (
                f'Call Read once on "{repo_paths.delivery}" and stop after the first result.'
            ),
        },
        "poll_timeout_deny": {
            "execution_kind": _SPAWN_AGENT,
            "expected_branch": "poll_timeout_deny",
            "expected_evidence": [
                "smoke-control disable leaves the seed in place",
                "guard denies after the bounded 2s poll window",
            ],
            "prompt": (
                f'Call Read once on "{repo_paths.delivery}" and stop after the denial.'
            ),
        },
    }
    if scenario_id not in scenarios:
        raise RuntimeError(
            f"scenario definition failed: unknown scenario_id. Got: {scenario_id!r:.100}"
        )
    return scenarios[scenario_id]


def _timestamp() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _run_with_wrapper(argv: list[str] | None = None) -> None:
    """Call ``main()`` and apply the fail-fast wrapper.

    Extracted from the ``__main__`` block so the wrapper is testable
    in-process via direct call (Round 6 testability refactor). On any
    exception from ``main(argv)``, prints
    ``containment_smoke_setup failed: unexpected error. Got: <repr(exc)>``
    to stderr (capped at 100 chars via ``{exc!r:.100}``) and raises
    ``SystemExit(1)``. The happy path exits via ``SystemExit(main(argv))``.
    The structural change from inlined-in-``__main__`` to extracted is so
    tests can exercise the full wrapper boundary without spawning a
    subprocess. The ``Got: {exc!r:.100}`` format mirrors the lifecycle
    fail-OPEN log convention so both outer-boundary contracts produce a
    parseable, class-preserving exception trail.
    """
    try:
        raise SystemExit(main(argv))
    except Exception as exc:
        print(
            f"containment_smoke_setup failed: unexpected error. Got: {exc!r:.100}",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc


if __name__ == "__main__":
    _run_with_wrapper()
