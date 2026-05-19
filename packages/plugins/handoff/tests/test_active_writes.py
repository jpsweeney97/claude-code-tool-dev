from __future__ import annotations

import hashlib
import json
import os
import socket
import subprocess
import sys
import time
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
import handoff_runtime.active_writes as active_writes
import handoff_runtime.session_state as session_state
import handoff_runtime.storage_primitives as storage_primitives
from handoff_runtime.chain_state import chain_state_recovery_inventory, read_chain_state
from handoff_runtime.quality_check import (
    HANDOFF_MIN_LINES,
    REQUIRED_HANDOFF_SECTIONS,
    REQUIRED_SUMMARY_SECTIONS,
    SUMMARY_MAX_LINES,
    count_body_lines,
    validate,
)

# ---------------------------------------------------------------------------
# Test content helpers — produce minimal content that passes the integrity gate.
# ---------------------------------------------------------------------------

_HANDOFF_SECTIONS = (
    "Goal",
    "Session Narrative",
    "Decisions",
    "Changes",
    "Codebase Knowledge",
    "Context",
    "Learnings",
    "Next Steps",
    "In Progress",
    "Open Questions",
    "Risks",
    "References",
    "Gotchas",
)
_SUMMARY_SECTIONS = (
    "Goal",
    "Session Narrative",
    "Decisions",
    "Changes",
    "Codebase Knowledge",
    "Learnings",
    "Next Steps",
    "Project Arc",
)
_CHECKPOINT_SECTIONS = (
    "Current Task",
    "In Progress",
    "Active Files",
    "Next Action",
    "Verification Snapshot",
)
_SECTIONS_BY_OPERATION = {
    "save": ("handoff", _HANDOFF_SECTIONS),
    "summary": ("summary", _SUMMARY_SECTIONS),
    "quicksave": ("checkpoint", _CHECKPOINT_SECTIONS),
}


def _valid_test_content(operation: str = "save", label: str = "test") -> str:
    """Return minimal markdown that passes the commit-time integrity gate.

    Frontmatter has all 7 required fields; all required sections are present;
    for handoff/summary the Decisions section has content so the hollow-doc
    guardrail is satisfied.
    """
    doc_type, sections = _SECTIONS_BY_OPERATION.get(
        operation, ("handoff", _HANDOFF_SECTIONS)
    )
    lines = [
        "---",
        "date: 2026-05-13",
        'time: "16:45"',
        "created_at: 2026-05-13T16:45:00+00:00",
        "session_id: test-run",
        "project: demo",
        f"title: {label}",
        f"type: {doc_type}",
        "---",
        "",
    ]
    for section in sections:
        lines.append(f"## {section}")
        lines.append("")
        # Decisions gets content so the hollow-handoff guardrail is satisfied.
        if section == "Decisions":
            lines.append(f"{label} content.")
        lines.append("")
    return "\n".join(lines)


@pytest.mark.parametrize(
    ("operation", "expected_slug"),
    [
        ("save", "handoff"),
        ("summary", "summary"),
        ("quicksave", "checkpoint"),
    ],
)
def test_active_writer_flow_cli_runs_begin_generate_write_protocol(
    tmp_path: Path,
    operation: str,
    expected_slug: str,
) -> None:
    script = Path(__file__).parent.parent / "scripts" / "session_state.py"

    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "active-writer-flow",
            "--project-root",
            str(tmp_path),
            "--project",
            "demo",
            "--operation",
            operation,
            "--created-at",
            "2026-05-13T16:45:00Z",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    operation_state_path = Path(payload["operation_state_path"])
    active_path = Path(payload["active_path"])
    state = json.loads(operation_state_path.read_text(encoding="utf-8"))

    assert payload["status"] == "completed"
    assert payload["operation"] == operation
    assert payload["bound_slug"] == expected_slug
    assert payload["content_hash"] == state["content_hash"]
    assert active_path == (
        tmp_path
        / ".claude"
        / "handoffs"
        / f"2026-05-13_16-45_{operation}-{expected_slug}.md"
    )
    assert state["status"] == "committed"
    assert active_path.read_text(encoding="utf-8").startswith("---\n")


@pytest.mark.parametrize(
    ("operation", "expected_slug"),
    [
        ("save", "handoff"),
        ("summary", "summary"),
        ("quicksave", "checkpoint"),
    ],
)
def test_active_writer_flow_cli_bridges_legacy_state_and_marks_source_consumed(
    tmp_path: Path,
    operation: str,
    expected_slug: str,
) -> None:
    script = Path(__file__).parent.parent / "scripts" / "session_state.py"
    archive = tmp_path / "docs" / "handoffs" / "archive" / "previous.md"
    archive.parent.mkdir(parents=True)
    archive.write_text("---\ntitle: Previous\n---\n", encoding="utf-8")
    legacy_state = (
        tmp_path / "docs" / "handoffs" / ".session-state" / "handoff-demo-token-b.json"
    )
    legacy_state.parent.mkdir(parents=True)
    legacy_payload = {
        "state_path": str(legacy_state),
        "project": "demo",
        "resume_token": "token-b",
        "archive_path": str(archive),
        "created_at": "2026-05-13T16:00:00Z",
    }
    legacy_state.write_text(json.dumps(legacy_payload, indent=2), encoding="utf-8")
    legacy_bytes = legacy_state.read_bytes()

    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "active-writer-flow",
            "--project-root",
            str(tmp_path),
            "--project",
            "demo",
            "--operation",
            operation,
            "--run-id",
            f"{operation}-bridge-flow",
            "--created-at",
            "2026-05-13T16:45:00Z",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    operation_state_path = Path(payload["operation_state_path"])
    operation_state = json.loads(operation_state_path.read_text(encoding="utf-8"))
    primary_state = (
        tmp_path
        / ".claude"
        / "handoffs"
        / ".session-state"
        / "handoff-demo-token-b.json"
    )
    inventory = chain_state_recovery_inventory(tmp_path, project_name="demo")
    by_path = {
        candidate["project_relative_state_path"]: candidate
        for candidate in inventory["candidates"]
    }

    assert Path(payload["active_path"]) == (
        tmp_path
        / ".claude"
        / "handoffs"
        / f"2026-05-13_16-45_{operation}-{expected_slug}.md"
    )
    assert operation_state["resumed_from_path"] == str(archive)
    assert (
        operation_state["resumed_from_hash"]
        == hashlib.sha256(archive.read_bytes()).hexdigest()
    )
    assert operation_state["state_cleanup_action"] == "cleared-primary-state"
    assert operation_state["state_cleanup_path"] == str(primary_state)
    assert primary_state.exists() is False
    assert legacy_state.read_bytes() == legacy_bytes
    assert (
        by_path["docs/handoffs/.session-state/handoff-demo-token-b.json"][
            "marker_status"
        ]
        == "consumed"
    )
    assert read_chain_state(tmp_path, project_name="demo")["status"] == "absent"


def test_begin_active_write_rejects_corrupt_resume_state_snapshot(
    tmp_path: Path,
) -> None:
    state_dir = tmp_path / ".claude" / "handoffs" / ".session-state"
    state_dir.mkdir(parents=True)
    corrupt = state_dir / "handoff-demo-bad.json"
    corrupt.write_text("{bad", encoding="utf-8")

    with pytest.raises(
        active_writes.ActiveWriteError, match="resume state unreadable"
    ) as exc_info:
        active_writes.begin_active_write(
            tmp_path,
            project_name="demo",
            operation="summary",
            slug="corrupt-state",
            created_at="2026-05-13T16:45:00Z",
        )

    assert repr(str(corrupt))[:100] in str(exc_info.value)
    assert isinstance(exc_info.value.__cause__, json.JSONDecodeError)


def test_active_writer_flow_cli_reuses_same_run_retry(
    tmp_path: Path,
) -> None:
    script = Path(__file__).parent.parent / "scripts" / "session_state.py"
    command = [
        sys.executable,
        str(script),
        "active-writer-flow",
        "--project-root",
        str(tmp_path),
        "--project",
        "demo",
        "--operation",
        "save",
        "--run-id",
        "stable-flow",
        "--created-at",
        "2026-05-13T16:45:00Z",
    ]
    first = subprocess.run(command, check=True, capture_output=True, text=True)

    second = subprocess.run(command, check=False, capture_output=True, text=True)

    assert second.returncode == 0, second.stderr
    first_payload = json.loads(first.stdout)
    second_payload = json.loads(second.stdout)
    assert second_payload["transaction_id"] == first_payload["transaction_id"]
    assert second_payload["active_path"] == first_payload["active_path"]
    assert second_payload["status"] == "completed"


def test_active_writer_flow_cli_rejects_changed_content_retry(
    tmp_path: Path,
) -> None:
    script = Path(__file__).parent.parent / "scripts" / "session_state.py"
    command = [
        sys.executable,
        str(script),
        "active-writer-flow",
        "--project-root",
        str(tmp_path),
        "--project",
        "demo",
        "--operation",
        "save",
        "--run-id",
        "stable-flow",
        "--created-at",
        "2026-05-13T16:45:00Z",
    ]
    first = subprocess.run(command, check=True, capture_output=True, text=True)

    changed = subprocess.run(
        [*command, "--content-note", "changed bytes"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert changed.returncode == 1
    assert "content mismatch" in changed.stderr
    first_payload = json.loads(first.stdout)
    state = json.loads(
        Path(first_payload["operation_state_path"]).read_text(encoding="utf-8")
    )
    assert state["status"] == "committed"
    assert state["content_hash"] == first_payload["content_hash"]


def test_active_writer_flow_cli_rejects_slug_change_retry(
    tmp_path: Path,
) -> None:
    script = Path(__file__).parent.parent / "scripts" / "session_state.py"
    command = [
        sys.executable,
        str(script),
        "active-writer-flow",
        "--project-root",
        str(tmp_path),
        "--project",
        "demo",
        "--operation",
        "save",
        "--run-id",
        "stable-flow",
        "--created-at",
        "2026-05-13T16:45:00Z",
    ]
    first = subprocess.run(command, check=True, capture_output=True, text=True)

    changed_slug = subprocess.run(
        [*command, "--slug", "changed-slug"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert changed_slug.returncode == 1
    assert "another slug" in changed_slug.stderr
    first_payload = json.loads(first.stdout)
    state = json.loads(
        Path(first_payload["operation_state_path"]).read_text(encoding="utf-8")
    )
    assert state["status"] == "committed"
    assert state["bound_slug"] == "handoff"
    assert state["active_path"] == first_payload["active_path"]


def test_active_writer_flow_cli_recovers_context_loss_from_inventory(
    tmp_path: Path,
) -> None:
    reservation = active_writes.begin_active_write(
        tmp_path,
        project_name="demo",
        operation="summary",
        slug="resume-me",
        created_at="2026-05-13T16:45:00Z",
    )
    script = Path(__file__).parent.parent / "scripts" / "session_state.py"

    resumed = subprocess.run(
        [
            sys.executable,
            str(script),
            "active-writer-flow",
            "--project-root",
            str(tmp_path),
            "--project",
            "demo",
            "--operation",
            "summary",
            "--resume-pending",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert resumed.returncode == 0, resumed.stderr
    payload = json.loads(resumed.stdout)
    assert payload["operation_state_path"] == str(reservation.operation_state_path)
    assert payload["transaction_id"] == reservation.transaction_id
    assert payload["status"] == "completed"
    assert reservation.allocated_active_path.exists()


def test_active_writer_flow_cli_fails_on_ambiguous_pending_inventory(
    tmp_path: Path,
) -> None:
    first = active_writes.begin_active_write(
        tmp_path,
        project_name="demo",
        operation="summary",
        slug="first",
        created_at="2026-05-13T16:45:00Z",
    )
    state_dir = tmp_path / ".claude" / "handoffs" / ".session-state"
    chain_state = state_dir / "handoff-demo-resume.json"
    chain_state.write_text(
        json.dumps({"project": "demo", "archive_path": "/tmp/archive.md"}),
        encoding="utf-8",
    )
    second = active_writes.begin_active_write(
        tmp_path,
        project_name="demo",
        operation="summary",
        slug="second",
        created_at="2026-05-13T16:46:00Z",
    )
    script = Path(__file__).parent.parent / "scripts" / "session_state.py"

    resumed = subprocess.run(
        [
            sys.executable,
            str(script),
            "active-writer-flow",
            "--project-root",
            str(tmp_path),
            "--project",
            "demo",
            "--operation",
            "summary",
            "--resume-pending",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert resumed.returncode == 1
    assert "expected exactly one pending active write" in resumed.stderr
    assert "Traceback" not in resumed.stderr
    assert first.allocated_active_path.exists() is False
    assert second.allocated_active_path.exists() is False


def test_active_writer_flow_cli_cleanup_falls_back_to_unlink_when_trash_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    archive = tmp_path / ".claude" / "handoffs" / "archive" / "previous.md"
    archive.parent.mkdir(parents=True)
    archive.write_text("---\ntitle: Previous\n---\n", encoding="utf-8")
    state_dir = tmp_path / ".claude" / "handoffs" / ".session-state"
    state_dir.mkdir(parents=True)
    state_path = state_dir / "handoff-demo-resume.json"
    state_path.write_text(
        json.dumps(
            {
                "state_path": str(state_path),
                "project": "demo",
                "resume_token": "resume",
                "archive_path": str(archive),
                "created_at": "2026-05-13T16:00:00Z",
            }
        ),
        encoding="utf-8",
    )
    original_subprocess_run = active_writes._storage_primitives.subprocess.run

    def fail_trash(*args: object, **kwargs: object) -> object:
        if not args or not isinstance(args[0], list) or args[0][:1] != ["trash"]:
            return original_subprocess_run(*args, **kwargs)
        raise FileNotFoundError("trash")

    monkeypatch.setattr(active_writes._storage_primitives.subprocess, "run", fail_trash)

    result = session_state.main(
        [
            "active-writer-flow",
            "--project-root",
            str(tmp_path),
            "--project",
            "demo",
            "--operation",
            "save",
            "--run-id",
            "flow-cleanup-failure",
            "--created-at",
            "2026-05-13T16:45:00Z",
        ]
    )

    captured = capsys.readouterr()
    assert result == 0
    assert "Traceback" not in captured.err
    operation_state_path = (
        tmp_path
        / ".claude"
        / "handoffs"
        / ".session-state"
        / "active-writes"
        / "demo"
        / "flow-cleanup-failure.json"
    )
    operation_state = json.loads(operation_state_path.read_text(encoding="utf-8"))
    active_path = Path(operation_state["active_path"])
    transaction = json.loads(
        Path(operation_state["transaction_path"]).read_text(encoding="utf-8")
    )
    assert active_path.exists()
    assert not state_path.exists()
    assert operation_state["status"] == "committed"
    assert operation_state["state_cleanup_action"] == "cleared-primary-state"
    assert operation_state["state_cleanup_mechanism"] == "unlink"
    assert transaction["status"] == "completed"
    assert not state_path.exists()


@pytest.mark.parametrize(
    ("operation", "slug"),
    [
        ("save", "handoff"),
        ("summary", "summary"),
        ("quicksave", "checkpoint"),
    ],
)
def test_active_writer_flow_cli_allocates_collision_safe_paths_through_02(
    tmp_path: Path,
    operation: str,
    slug: str,
) -> None:
    script = Path(__file__).parent.parent / "scripts" / "session_state.py"
    payloads = []
    for index in range(3):
        result = subprocess.run(
            [
                sys.executable,
                str(script),
                "active-writer-flow",
                "--project-root",
                str(tmp_path),
                "--project",
                "demo",
                "--operation",
                operation,
                "--run-id",
                f"{operation}-collision-{index}",
                "--created-at",
                "2026-05-13T16:45:00Z",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        payloads.append(json.loads(result.stdout))

    active_dir = tmp_path / ".claude" / "handoffs"
    assert [payload["active_path"] for payload in payloads] == [
        str(active_dir / f"2026-05-13_16-45_{operation}-{slug}.md"),
        str(active_dir / f"2026-05-13_16-45_{operation}-{slug}-01.md"),
        str(active_dir / f"2026-05-13_16-45_{operation}-{slug}-02.md"),
    ]
    assert all(Path(payload["active_path"]).exists() for payload in payloads)


def test_active_writer_flow_releases_lock_during_generation_and_reacquires_for_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    lock_path = (
        tmp_path
        / ".claude"
        / "handoffs"
        / ".session-state"
        / "locks"
        / "active-write.lock"
    )
    original_generator = session_state._deterministic_active_writer_content
    observed: dict[str, bool] = {}

    def generate_while_competing_lock_exists(
        operation_state: dict[str, object],
        *,
        content_note: str | None = None,
    ) -> str:
        observed["lock_released_during_generation"] = not lock_path.exists()
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        lock_path.write_text(
            json.dumps(
                {
                    "lock_id": "competing-writer",
                    "project": "demo",
                    "operation": "save",
                    "hostname": socket.gethostname(),
                    "created_at": datetime.now(UTC).isoformat(),
                    "timeout_seconds": 1800,
                }
            ),
            encoding="utf-8",
        )
        return original_generator(operation_state, content_note=content_note)

    monkeypatch.setattr(
        session_state,
        "_deterministic_active_writer_content",
        generate_while_competing_lock_exists,
    )

    result = session_state.main(
        [
            "active-writer-flow",
            "--project-root",
            str(tmp_path),
            "--project",
            "demo",
            "--operation",
            "save",
            "--run-id",
            "flow-lock-reacquire",
            "--created-at",
            "2026-05-13T16:45:00Z",
        ]
    )

    captured = capsys.readouterr()
    assert observed["lock_released_during_generation"] is True
    assert result == 1
    assert "lock is already held" in captured.err
    operation_state_path = (
        tmp_path
        / ".claude"
        / "handoffs"
        / ".session-state"
        / "active-writes"
        / "demo"
        / "flow-lock-reacquire.json"
    )
    operation_state = json.loads(operation_state_path.read_text(encoding="utf-8"))
    assert operation_state["status"] == "begun"
    assert Path(operation_state["allocated_active_path"]).exists() is False


def test_begin_active_write_persists_operation_state_before_content_generation(
    tmp_path: Path,
) -> None:
    script = Path(__file__).parent.parent / "scripts" / "session_state.py"

    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "begin-active-write",
            "--project-root",
            str(tmp_path),
            "--project",
            "demo",
            "--operation",
            "save",
            "--slug",
            "next-step",
            "--created-at",
            "2026-05-13T16:45:00Z",
            "--field",
            "operation_state_path",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    operation_state_path = Path(result.stdout.strip())
    payload = json.loads(operation_state_path.read_text(encoding="utf-8"))

    assert payload["schema_version"] == 1
    assert payload["project"] == "demo"
    assert payload["operation"] == "save"
    assert payload["status"] == "begun"
    assert payload["run_id"]
    assert operation_state_path.name == f"{payload['run_id']}.json"
    assert payload["transaction_id"]
    assert payload["idempotency_key"]
    assert payload["bound_slug"] == "next-step"
    assert payload["slug_source"] == "caller-predeclared"
    assert payload["allocated_active_path"] == str(
        tmp_path / ".claude" / "handoffs" / "2026-05-13_16-45_save-next-step.md"
    )
    assert payload["operation_state_path"] == str(operation_state_path)
    assert payload["lease_id"]
    assert payload["lease_expires_at"]
    assert payload["transaction_watermark"]
    assert payload["state_snapshot_hash"]
    assert payload["recovery_commands"]["continue"]["command"] == (
        "active-write-transaction-recover"
    )
    assert payload["recovery_commands"]["continue"]["args"]["project_root"] == str(
        tmp_path
    )
    assert payload["recovery_commands"]["continue"]["args"][
        "operation_state_path"
    ] == str(operation_state_path)
    assert (
        payload["recovery_commands"]["retry_write"]["command"] == "write-active-handoff"
    )
    assert payload["recovery_commands"]["abandon"]["command"] == "abandon-active-write"

    transaction_path = Path(payload["transaction_path"])
    transaction = json.loads(transaction_path.read_text(encoding="utf-8"))
    assert transaction["operation"] == "save"
    assert transaction["status"] == "pending_before_write"
    assert transaction["allocated_active_path"] == payload["allocated_active_path"]
    assert not (
        tmp_path
        / ".claude"
        / "handoffs"
        / ".session-state"
        / "locks"
        / "active-write.lock"
    ).exists()


def test_begin_active_write_mints_helper_default_slug_before_content_generation(
    tmp_path: Path,
) -> None:
    script = Path(__file__).parent.parent / "scripts" / "session_state.py"

    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "begin-active-write",
            "--project-root",
            str(tmp_path),
            "--project",
            "demo",
            "--operation",
            "summary",
            "--created-at",
            "2026-05-13T16:45:00Z",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["bound_slug"] == "summary"
    assert payload["slug_source"] == "helper-default"
    assert payload["allocated_active_path"] == str(
        tmp_path / ".claude" / "handoffs" / "2026-05-13_16-45_summary-summary.md"
    )
    assert not Path(payload["allocated_active_path"]).exists()


def test_allocate_active_path_cli_returns_collision_safe_primary_path(
    tmp_path: Path,
) -> None:
    script = Path(__file__).parent.parent / "scripts" / "session_state.py"
    existing = tmp_path / ".claude" / "handoffs" / "2026-05-13_16-45_save-repeat.md"
    existing.parent.mkdir(parents=True)
    existing.write_text("existing\n", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "allocate-active-path",
            "--project-root",
            str(tmp_path),
            "--operation",
            "save",
            "--slug",
            "repeat",
            "--created-at",
            "2026-05-13T16:45:00Z",
            "--field",
            "active_path",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == str(
        tmp_path / ".claude" / "handoffs" / "2026-05-13_16-45_save-repeat-01.md"
    )
    assert existing.read_text(encoding="utf-8") == "existing\n"


def test_allocate_active_path_treats_dangling_symlink_as_occupied(
    tmp_path: Path,
) -> None:
    existing = tmp_path / ".claude" / "handoffs" / "2026-05-13_16-45_save-repeat.md"
    existing.parent.mkdir(parents=True)
    existing.symlink_to(tmp_path / "missing-target.md")

    active_path = active_writes.allocate_active_path(
        tmp_path,
        operation="save",
        slug="repeat",
        created_at="2026-05-13T16:45:00Z",
    )

    assert (
        active_path
        == tmp_path / ".claude" / "handoffs" / "2026-05-13_16-45_save-repeat-01.md"
    )


def test_allocate_active_path_treats_tracked_missing_path_as_occupied(
    tmp_path: Path,
) -> None:
    subprocess.run(
        ["git", "init"], cwd=tmp_path, check=True, capture_output=True, text=True
    )
    existing = tmp_path / ".claude" / "handoffs" / "2026-05-13_16-45_save-repeat.md"
    existing.parent.mkdir(parents=True)
    existing.write_text("tracked candidate\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", str(existing.relative_to(tmp_path))],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )
    existing.unlink()

    active_path = active_writes.allocate_active_path(
        tmp_path,
        operation="save",
        slug="repeat",
        created_at="2026-05-13T16:45:00Z",
    )

    assert (
        active_path
        == tmp_path / ".claude" / "handoffs" / "2026-05-13_16-45_save-repeat-01.md"
    )


def test_allocate_active_path_rejects_path_like_slug(tmp_path: Path) -> None:
    with pytest.raises(
        active_writes.ActiveWriteError, match="slug must be a filename segment"
    ):
        active_writes.allocate_active_path(
            tmp_path,
            operation="save",
            slug="../escape",
            created_at="2026-05-13T16:45:00Z",
        )


def test_allocate_active_path_reports_parent_file_conflict(tmp_path: Path) -> None:
    (tmp_path / ".claude").write_text("not a directory\n", encoding="utf-8")

    with pytest.raises(active_writes.ActiveWriteError, match="parent path conflict"):
        active_writes.allocate_active_path(
            tmp_path,
            operation="save",
            slug="conflict",
            created_at="2026-05-13T16:45:00Z",
        )


def test_begin_active_write_reuses_existing_run_id_reservation(tmp_path: Path) -> None:
    first = active_writes.begin_active_write(
        tmp_path,
        project_name="demo",
        operation="save",
        slug="same-run",
        run_id="stable-run",
        created_at="2026-05-13T16:45:00Z",
    )

    second = active_writes.begin_active_write(
        tmp_path,
        project_name="demo",
        operation="save",
        slug="same-run",
        run_id="stable-run",
        created_at="2026-05-13T17:00:00Z",
    )

    assert second.run_id == first.run_id
    assert second.transaction_id == first.transaction_id
    assert second.operation_state_path == first.operation_state_path
    assert second.allocated_active_path == first.allocated_active_path
    transactions = sorted(
        (tmp_path / ".claude" / "handoffs" / ".session-state" / "transactions").glob(
            "*.json"
        )
    )
    assert transactions == [first.transaction_path]


def test_begin_active_write_rejects_slug_change_for_existing_run_id(
    tmp_path: Path,
) -> None:
    first = active_writes.begin_active_write(
        tmp_path,
        project_name="demo",
        operation="save",
        slug="first-slug",
        run_id="stable-run",
        created_at="2026-05-13T16:45:00Z",
    )
    before = json.loads(first.operation_state_path.read_text(encoding="utf-8"))

    with pytest.raises(active_writes.ActiveWriteError, match="another slug"):
        active_writes.begin_active_write(
            tmp_path,
            project_name="demo",
            operation="save",
            slug="changed-slug",
            run_id="stable-run",
            created_at="2026-05-13T17:00:00Z",
        )

    after = json.loads(first.operation_state_path.read_text(encoding="utf-8"))
    transactions = sorted(
        (tmp_path / ".claude" / "handoffs" / ".session-state" / "transactions").glob(
            "*.json"
        )
    )
    assert after == before
    assert transactions == [first.transaction_path]


def test_begin_active_write_rejects_second_live_reservation_for_same_state(
    tmp_path: Path,
) -> None:
    first = active_writes.begin_active_write(
        tmp_path,
        project_name="demo",
        operation="save",
        slug="first",
        created_at="2026-05-13T16:45:00Z",
    )

    with pytest.raises(
        active_writes.ActiveWriteError, match="active write already reserved"
    ):
        active_writes.begin_active_write(
            tmp_path,
            project_name="demo",
            operation="save",
            slug="second",
            created_at="2026-05-13T16:46:00Z",
        )

    transactions = sorted(
        (tmp_path / ".claude" / "handoffs" / ".session-state" / "transactions").glob(
            "*.json"
        )
    )
    assert transactions == [first.transaction_path]
    assert not (
        tmp_path / ".claude" / "handoffs" / "2026-05-13_16-46_save-second.md"
    ).exists()


def test_begin_active_write_auto_expires_stale_pre_output_reservation(
    tmp_path: Path,
) -> None:
    first = active_writes.begin_active_write(
        tmp_path,
        project_name="demo",
        operation="save",
        slug="expired",
        created_at="2026-05-13T16:45:00Z",
        lease_seconds=-1,
    )

    replacement = active_writes.begin_active_write(
        tmp_path,
        project_name="demo",
        operation="save",
        slug="replacement",
        created_at="2026-05-13T16:46:00Z",
    )

    expired_operation_state = json.loads(
        first.operation_state_path.read_text(encoding="utf-8")
    )
    expired_transaction = json.loads(first.transaction_path.read_text(encoding="utf-8"))
    assert expired_operation_state["status"] == "reservation_expired"
    assert expired_transaction["status"] == "reservation_expired"
    assert replacement.transaction_id != first.transaction_id
    assert replacement.allocated_active_path == (
        tmp_path / ".claude" / "handoffs" / "2026-05-13_16-46_save-replacement.md"
    )

    transactions = sorted(
        (tmp_path / ".claude" / "handoffs" / ".session-state" / "transactions").glob(
            "*.json"
        )
    )
    assert set(transactions) == {first.transaction_path, replacement.transaction_path}


def test_begin_active_write_does_not_auto_expire_after_content_hash_exists(
    tmp_path: Path,
) -> None:
    first = active_writes.begin_active_write(
        tmp_path,
        project_name="demo",
        operation="save",
        slug="post-content",
        created_at="2026-05-13T16:45:00Z",
        lease_seconds=-1,
    )

    operation_state = json.loads(first.operation_state_path.read_text(encoding="utf-8"))
    operation_state["content_hash"] = "a" * 64
    first.operation_state_path.write_text(
        json.dumps(operation_state, indent=2), encoding="utf-8"
    )

    with pytest.raises(
        active_writes.ActiveWriteError, match="active write already reserved"
    ):
        active_writes.begin_active_write(
            tmp_path,
            project_name="demo",
            operation="save",
            slug="replacement",
            created_at="2026-05-13T16:46:00Z",
        )


def test_write_active_handoff_commits_reserved_output(tmp_path: Path) -> None:
    script = Path(__file__).parent.parent / "scripts" / "session_state.py"
    begin = subprocess.run(
        [
            sys.executable,
            str(script),
            "begin-active-write",
            "--project-root",
            str(tmp_path),
            "--project",
            "demo",
            "--operation",
            "save",
            "--slug",
            "write-phase",
            "--created-at",
            "2026-05-13T16:45:00Z",
            "--field",
            "operation_state_path",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    operation_state_path = Path(begin.stdout.strip())
    content = _valid_test_content("save", "Write phase")
    content_path = tmp_path / "content.md"
    content_path.write_text(content, encoding="utf-8")
    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

    write = subprocess.run(
        [
            sys.executable,
            str(script),
            "write-active-handoff",
            "--project-root",
            str(tmp_path),
            "--operation-state-path",
            str(operation_state_path),
            "--content-file",
            str(content_path),
            "--content-sha256",
            content_hash,
            "--field",
            "active_path",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert write.returncode == 0, write.stderr
    active_path = Path(write.stdout.strip())
    assert (
        active_path
        == tmp_path / ".claude" / "handoffs" / "2026-05-13_16-45_save-write-phase.md"
    )
    assert active_path.read_text(encoding="utf-8") == content
    state = json.loads(operation_state_path.read_text(encoding="utf-8"))
    assert state["status"] == "committed"
    assert state["content_hash"] == content_hash
    assert state["output_sha256"] == content_hash
    transaction = json.loads(
        Path(state["transaction_path"]).read_text(encoding="utf-8")
    )
    assert transaction["status"] == "completed"
    assert transaction["active_path"] == str(active_path)
    assert transaction["temp_active_path"].startswith(
        str(active_path.parent / f".{active_path.name}.")
    )
    assert transaction["temp_active_path"].endswith(".tmp")
    assert not (
        tmp_path
        / ".claude"
        / "handoffs"
        / ".session-state"
        / "locks"
        / "active-write.lock"
    ).exists()


def test_list_active_writes_reports_pending_operation_state_without_mutation(
    tmp_path: Path,
) -> None:
    script = Path(__file__).parent.parent / "scripts" / "session_state.py"
    begin = subprocess.run(
        [
            sys.executable,
            str(script),
            "begin-active-write",
            "--project-root",
            str(tmp_path),
            "--project",
            "demo",
            "--operation",
            "summary",
            "--slug",
            "recover-me",
            "--created-at",
            "2026-05-13T16:45:00Z",
            "--field",
            "operation_state_path",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    operation_state_path = Path(begin.stdout.strip())

    listing = subprocess.run(
        [
            sys.executable,
            str(script),
            "list-active-writes",
            "--project-root",
            str(tmp_path),
            "--project",
            "demo",
            "--operation",
            "summary",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert listing.returncode == 0, listing.stderr
    payload = json.loads(listing.stdout)
    assert payload["total"] == 1
    assert payload["active_writes"][0]["operation_state_path"] == str(
        operation_state_path
    )
    assert payload["active_writes"][0]["status"] == "begun"
    assert not Path(payload["active_writes"][0]["allocated_active_path"]).exists()


def test_list_active_writes_surfaces_unreadable_operation_state(tmp_path: Path) -> None:
    active_writes_dir = (
        tmp_path / ".claude" / "handoffs" / ".session-state" / "active-writes" / "demo"
    )
    active_writes_dir.mkdir(parents=True)
    corrupt = active_writes_dir / "corrupt.json"
    corrupt.write_text("{bad", encoding="utf-8")

    records = active_writes.list_active_writes(
        tmp_path,
        project_name="demo",
        operation="summary",
    )

    assert records == [
        {
            "operation_state_path": str(corrupt),
            "status": "unreadable",
            "operation": "unknown",
            "requested_operation": "summary",
            "error": records[0]["error"],
        }
    ]
    assert "active-write operation-state record unreadable" in str(records[0]["error"])
    assert "JSONDecodeError" in str(records[0]["error"])


def test_write_active_handoff_changed_content_retry_preserves_committed_state(
    tmp_path: Path,
) -> None:
    script = Path(__file__).parent.parent / "scripts" / "session_state.py"
    begin = subprocess.run(
        [
            sys.executable,
            str(script),
            "begin-active-write",
            "--project-root",
            str(tmp_path),
            "--project",
            "demo",
            "--operation",
            "quicksave",
            "--slug",
            "retry",
            "--created-at",
            "2026-05-13T16:45:00Z",
            "--field",
            "operation_state_path",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    operation_state_path = Path(begin.stdout.strip())
    original = _valid_test_content("quicksave", "Retry original")
    original_path = tmp_path / "original.md"
    original_path.write_text(original, encoding="utf-8")
    original_hash = hashlib.sha256(original.encode("utf-8")).hexdigest()
    subprocess.run(
        [
            sys.executable,
            str(script),
            "write-active-handoff",
            "--project-root",
            str(tmp_path),
            "--operation-state-path",
            str(operation_state_path),
            "--content-file",
            str(original_path),
            "--content-sha256",
            original_hash,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    changed = _valid_test_content("quicksave", "Retry changed")
    changed_path = tmp_path / "changed.md"
    changed_path.write_text(changed, encoding="utf-8")
    changed_hash = hashlib.sha256(changed.encode("utf-8")).hexdigest()

    retry = subprocess.run(
        [
            sys.executable,
            str(script),
            "write-active-handoff",
            "--project-root",
            str(tmp_path),
            "--operation-state-path",
            str(operation_state_path),
            "--content-file",
            str(changed_path),
            "--content-sha256",
            changed_hash,
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    state = json.loads(operation_state_path.read_text(encoding="utf-8"))
    assert retry.returncode == 1
    assert "content mismatch" in retry.stderr
    assert state["status"] == "committed"
    assert state["content_hash"] == original_hash
    assert Path(state["active_path"]).read_text(encoding="utf-8") == original


def test_write_active_handoff_reports_unreadable_existing_active_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reservation = active_writes.begin_active_write(
        tmp_path,
        project_name="demo",
        operation="summary",
        slug="unreadable-output",
        created_at="2026-05-13T16:45:00Z",
    )
    reservation.allocated_active_path.parent.mkdir(parents=True, exist_ok=True)
    reservation.allocated_active_path.write_text("existing", encoding="utf-8")
    content = _valid_test_content("summary", "Unreadable")
    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    original_sha256_file = active_writes._sha256_file

    def fail_active_hash(path: Path) -> str:
        if path == reservation.allocated_active_path:
            raise PermissionError("read denied")
        return original_sha256_file(path)

    monkeypatch.setattr(active_writes, "_sha256_file", fail_active_hash)

    with pytest.raises(
        active_writes.ActiveWriteError, match="active output unreadable"
    ):
        active_writes.write_active_handoff(
            tmp_path,
            operation_state_path=reservation.operation_state_path,
            content=content,
            content_sha256=content_hash,
        )

    state = json.loads(reservation.operation_state_path.read_text(encoding="utf-8"))
    assert state["status"] == "content-generated"


def test_write_active_handoff_records_content_generated_before_output_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reservation = active_writes.begin_active_write(
        tmp_path,
        project_name="demo",
        operation="save",
        slug="generated-before-write",
        created_at="2026-05-13T16:45:00Z",
    )
    content = _valid_test_content("save", "Generated before write")
    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    original_write_text = Path.write_text

    def fail_active_temp_write(path: Path, *args: object, **kwargs: object) -> int:
        if (
            path.parent == reservation.allocated_active_path.parent
            and path.name.startswith(".")
        ):
            raise OSError("active temp write failed")
        return original_write_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", fail_active_temp_write)

    with pytest.raises(
        active_writes.ActiveWriteError, match="active output write failed"
    ):
        active_writes.write_active_handoff(
            tmp_path,
            operation_state_path=reservation.operation_state_path,
            content=content,
            content_sha256=content_hash,
        )

    state = json.loads(reservation.operation_state_path.read_text(encoding="utf-8"))
    transaction = json.loads(reservation.transaction_path.read_text(encoding="utf-8"))
    assert state["status"] == "content-generated"
    assert state["content_hash"] == content_hash
    assert transaction["status"] == "content-generated"
    assert transaction["content_hash"] == content_hash


def test_abandon_active_write_marks_operation_and_transaction_without_deleting_output(
    tmp_path: Path,
) -> None:
    script = Path(__file__).parent.parent / "scripts" / "session_state.py"
    begin = subprocess.run(
        [
            sys.executable,
            str(script),
            "begin-active-write",
            "--project-root",
            str(tmp_path),
            "--project",
            "demo",
            "--operation",
            "save",
            "--slug",
            "abandon-me",
            "--created-at",
            "2026-05-13T16:45:00Z",
            "--field",
            "operation_state_path",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    operation_state_path = Path(begin.stdout.strip())
    state = json.loads(operation_state_path.read_text(encoding="utf-8"))
    reserved_output = Path(state["allocated_active_path"])
    reserved_output.write_text("operator-owned bytes\n", encoding="utf-8")

    abandoned = subprocess.run(
        [
            sys.executable,
            str(script),
            "abandon-active-write",
            "--project-root",
            str(tmp_path),
            "--operation-state-path",
            str(operation_state_path),
            "--reason",
            "operator selected a new save",
            "--field",
            "status",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert abandoned.returncode == 0, abandoned.stderr
    assert abandoned.stdout.strip() == "abandoned"
    updated = json.loads(operation_state_path.read_text(encoding="utf-8"))
    transaction = json.loads(
        Path(updated["transaction_path"]).read_text(encoding="utf-8")
    )
    assert updated["status"] == "abandoned"
    assert updated["abandon_reason"] == "operator selected a new save"
    assert transaction["status"] == "abandoned"
    assert reserved_output.read_text(encoding="utf-8") == "operator-owned bytes\n"


def test_active_write_transaction_recover_commits_verified_written_output(
    tmp_path: Path,
) -> None:
    script = Path(__file__).parent.parent / "scripts" / "session_state.py"
    begin = subprocess.run(
        [
            sys.executable,
            str(script),
            "begin-active-write",
            "--project-root",
            str(tmp_path),
            "--project",
            "demo",
            "--operation",
            "summary",
            "--slug",
            "recover-written",
            "--created-at",
            "2026-05-13T16:45:00Z",
            "--field",
            "operation_state_path",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    operation_state_path = Path(begin.stdout.strip())
    state = json.loads(operation_state_path.read_text(encoding="utf-8"))
    active_path = Path(state["allocated_active_path"])
    content = "---\ntitle: Recover\n---\n\n# Written\n"
    active_path.write_text(content, encoding="utf-8")
    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    state["status"] = "written_not_confirmed"
    state["content_hash"] = content_hash
    state["output_sha256"] = content_hash
    operation_state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")

    recovered = subprocess.run(
        [
            sys.executable,
            str(script),
            "active-write-transaction-recover",
            "--project-root",
            str(tmp_path),
            "--operation-state-path",
            str(operation_state_path),
            "--field",
            "status",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert recovered.returncode == 0, recovered.stderr
    assert recovered.stdout.strip() == "committed"
    updated = json.loads(operation_state_path.read_text(encoding="utf-8"))
    transaction = json.loads(
        Path(updated["transaction_path"]).read_text(encoding="utf-8")
    )
    assert updated["status"] == "committed"
    assert updated["active_path"] == str(active_path)
    assert updated["recovered_from_status"] == "written_not_confirmed"
    assert transaction["status"] == "completed"
    assert transaction["active_path"] == str(active_path)
    assert transaction["recovered_from_status"] == "written_not_confirmed"


def test_active_write_transaction_recover_records_content_mismatch(
    tmp_path: Path,
) -> None:
    reservation = active_writes.begin_active_write(
        tmp_path,
        project_name="demo",
        operation="summary",
        slug="mismatch",
        created_at="2026-05-13T16:45:00Z",
    )
    expected = "---\ntitle: Expected\n---\n\n# Expected\n"
    expected_hash = hashlib.sha256(expected.encode("utf-8")).hexdigest()
    reservation.allocated_active_path.write_text(
        "---\ntitle: Different\n---\n\n# Different\n",
        encoding="utf-8",
    )
    state = json.loads(reservation.operation_state_path.read_text(encoding="utf-8"))
    state["status"] = "written_not_confirmed"
    state["content_hash"] = expected_hash
    state["output_sha256"] = expected_hash
    reservation.operation_state_path.write_text(
        json.dumps(state, indent=2), encoding="utf-8"
    )

    with pytest.raises(active_writes.ActiveWriteError, match="content mismatch"):
        active_writes.recover_active_write_transaction(
            tmp_path,
            operation_state_path=reservation.operation_state_path,
        )

    updated = json.loads(reservation.operation_state_path.read_text(encoding="utf-8"))
    transaction = json.loads(reservation.transaction_path.read_text(encoding="utf-8"))
    assert updated["status"] == "content_mismatch"
    assert transaction["status"] == "content_mismatch"
    assert transaction["active_path"] == str(reservation.allocated_active_path)


def test_active_write_transaction_recover_reports_unreadable_active_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reservation = active_writes.begin_active_write(
        tmp_path,
        project_name="demo",
        operation="summary",
        slug="unreadable-recover",
        created_at="2026-05-13T16:45:00Z",
    )
    expected = "---\ntitle: Expected\n---\n\n# Expected\n"
    expected_hash = hashlib.sha256(expected.encode("utf-8")).hexdigest()
    reservation.allocated_active_path.write_text(expected, encoding="utf-8")
    state = json.loads(reservation.operation_state_path.read_text(encoding="utf-8"))
    state["status"] = "written_not_confirmed"
    state["content_hash"] = expected_hash
    state["output_sha256"] = expected_hash
    reservation.operation_state_path.write_text(
        json.dumps(state, indent=2), encoding="utf-8"
    )
    original_sha256_file = active_writes._sha256_file

    def fail_active_hash(path: Path) -> str:
        if path == reservation.allocated_active_path:
            raise PermissionError("read denied")
        return original_sha256_file(path)

    monkeypatch.setattr(active_writes, "_sha256_file", fail_active_hash)

    with pytest.raises(
        active_writes.ActiveWriteError, match="active output unreadable"
    ):
        active_writes.recover_active_write_transaction(
            tmp_path,
            operation_state_path=reservation.operation_state_path,
        )

    updated = json.loads(reservation.operation_state_path.read_text(encoding="utf-8"))
    assert updated["status"] == "written_not_confirmed"


def test_active_write_transaction_recover_records_pending_before_write(
    tmp_path: Path,
) -> None:
    reservation = active_writes.begin_active_write(
        tmp_path,
        project_name="demo",
        operation="summary",
        slug="pending",
        created_at="2026-05-13T16:45:00Z",
    )
    state = json.loads(reservation.operation_state_path.read_text(encoding="utf-8"))
    state["status"] = "written_not_confirmed"
    state["content_hash"] = hashlib.sha256(b"missing output").hexdigest()
    state["output_sha256"] = state["content_hash"]
    reservation.operation_state_path.write_text(
        json.dumps(state, indent=2), encoding="utf-8"
    )

    recovered = active_writes.recover_active_write_transaction(
        tmp_path,
        operation_state_path=reservation.operation_state_path,
    )

    transaction = json.loads(reservation.transaction_path.read_text(encoding="utf-8"))
    assert recovered["status"] == "pending_before_write"
    assert transaction["status"] == "pending_before_write"
    assert transaction["active_path"] == str(reservation.allocated_active_path)


def test_write_active_handoff_clears_snapshotted_primary_state_after_output_write(
    tmp_path: Path,
) -> None:
    script = Path(__file__).parent.parent / "scripts" / "session_state.py"
    archive = tmp_path / ".claude" / "handoffs" / "archive" / "previous.md"
    archive.parent.mkdir(parents=True)
    archive.write_text("---\ntitle: Previous\n---\n", encoding="utf-8")
    state_dir = tmp_path / ".claude" / "handoffs" / ".session-state"
    state_dir.mkdir(parents=True)
    state_path = state_dir / "handoff-demo-resume.json"
    state_path.write_text(
        json.dumps(
            {
                "state_path": str(state_path),
                "project": "demo",
                "resume_token": "resume",
                "archive_path": str(archive),
                "created_at": "2026-05-13T16:00:00Z",
            }
        ),
        encoding="utf-8",
    )
    begin = subprocess.run(
        [
            sys.executable,
            str(script),
            "begin-active-write",
            "--project-root",
            str(tmp_path),
            "--project",
            "demo",
            "--operation",
            "save",
            "--slug",
            "clears-state",
            "--created-at",
            "2026-05-13T16:45:00Z",
            "--field",
            "operation_state_path",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    operation_state_path = Path(begin.stdout.strip())
    content = _valid_test_content("save", "Clears state")
    content_path = tmp_path / "content.md"
    content_path.write_text(content, encoding="utf-8")
    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

    write = subprocess.run(
        [
            sys.executable,
            str(script),
            "write-active-handoff",
            "--project-root",
            str(tmp_path),
            "--operation-state-path",
            str(operation_state_path),
            "--content-file",
            str(content_path),
            "--content-sha256",
            content_hash,
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert write.returncode == 0, write.stderr
    assert not state_path.exists()
    state = json.loads(operation_state_path.read_text(encoding="utf-8"))
    transaction = json.loads(
        Path(state["transaction_path"]).read_text(encoding="utf-8")
    )
    assert state["state_cleanup_action"] == "cleared-primary-state"
    assert state["state_cleanup_path"] == str(state_path)
    assert transaction["state_cleanup_action"] == "cleared-primary-state"


def test_write_active_handoff_falls_back_to_unlink_when_trash_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    archive = tmp_path / ".claude" / "handoffs" / "archive" / "previous.md"
    archive.parent.mkdir(parents=True)
    archive.write_text("---\ntitle: Previous\n---\n", encoding="utf-8")
    state_dir = tmp_path / ".claude" / "handoffs" / ".session-state"
    state_dir.mkdir(parents=True)
    state_path = state_dir / "handoff-demo-resume.json"
    state_path.write_text(
        json.dumps(
            {
                "state_path": str(state_path),
                "project": "demo",
                "resume_token": "resume",
                "archive_path": str(archive),
                "created_at": "2026-05-13T16:00:00Z",
            }
        ),
        encoding="utf-8",
    )
    reservation = active_writes.begin_active_write(
        tmp_path,
        project_name="demo",
        operation="save",
        slug="cleanup-fallback",
        created_at="2026-05-13T16:45:00Z",
    )
    content = _valid_test_content("save", "Cleanup fallback")
    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

    original_subprocess_run = active_writes._storage_primitives.subprocess.run

    def fail_trash(*args: object, **kwargs: object) -> object:
        if not args or not isinstance(args[0], list) or args[0][:1] != ["trash"]:
            return original_subprocess_run(*args, **kwargs)
        raise FileNotFoundError("trash")

    monkeypatch.setattr(active_writes._storage_primitives.subprocess, "run", fail_trash)

    result = active_writes.write_active_handoff(
        tmp_path,
        operation_state_path=reservation.operation_state_path,
        content=content,
        content_sha256=content_hash,
    )

    operation_state = json.loads(
        reservation.operation_state_path.read_text(encoding="utf-8")
    )
    assert result["status"] == "completed"
    assert operation_state["state_cleanup_action"] == "cleared-primary-state"
    assert operation_state["state_cleanup_mechanism"] == "unlink"
    assert not state_path.exists()


def test_write_active_handoff_persists_cleanup_failed_when_both_mechanisms_fail(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    archive = tmp_path / ".claude" / "handoffs" / "archive" / "previous.md"
    archive.parent.mkdir(parents=True)
    archive.write_text("---\ntitle: Previous\n---\n", encoding="utf-8")
    state_dir = tmp_path / ".claude" / "handoffs" / ".session-state"
    state_dir.mkdir(parents=True)
    state_path = state_dir / "handoff-demo-resume.json"
    state_path.write_text(
        json.dumps(
            {
                "state_path": str(state_path),
                "project": "demo",
                "resume_token": "resume",
                "archive_path": str(archive),
                "created_at": "2026-05-13T16:00:00Z",
            }
        ),
        encoding="utf-8",
    )
    reservation = active_writes.begin_active_write(
        tmp_path,
        project_name="demo",
        operation="save",
        slug="cleanup-both-fail",
        created_at="2026-05-13T16:45:00Z",
    )
    content = _valid_test_content("save", "Cleanup both fail")
    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

    original_subprocess_run = active_writes._storage_primitives.subprocess.run

    def fail_trash(*args: object, **kwargs: object) -> object:
        if not args or not isinstance(args[0], list) or args[0][:1] != ["trash"]:
            return original_subprocess_run(*args, **kwargs)
        raise FileNotFoundError("trash")

    original_unlink = Path.unlink

    def fail_unlink(self: Path, *args: object, **kwargs: object) -> None:
        if self == state_path:
            raise PermissionError("unlink denied")
        return original_unlink(self, *args, **kwargs)

    monkeypatch.setattr(active_writes._storage_primitives.subprocess, "run", fail_trash)
    monkeypatch.setattr(Path, "unlink", fail_unlink)

    with pytest.raises(active_writes.ActiveWriteError):
        active_writes.write_active_handoff(
            tmp_path,
            operation_state_path=reservation.operation_state_path,
            content=content,
            content_sha256=content_hash,
        )

    operation_state = json.loads(
        reservation.operation_state_path.read_text(encoding="utf-8")
    )
    transaction = json.loads(
        Path(operation_state["transaction_path"]).read_text(encoding="utf-8")
    )
    assert operation_state["status"] == "cleanup_failed"
    assert operation_state["state_cleanup_action"] == "cleanup_failed"
    assert transaction["status"] == "cleanup_failed"


def test_write_active_handoff_rejects_expired_reservation_before_output_write(
    tmp_path: Path,
) -> None:
    reservation = active_writes.begin_active_write(
        tmp_path,
        project_name="demo",
        operation="summary",
        slug="expired",
        created_at="2026-05-13T16:45:00Z",
    )
    operation_state = json.loads(
        reservation.operation_state_path.read_text(encoding="utf-8")
    )
    operation_state["lease_expires_at"] = "2000-01-01T00:00:00+00:00"
    reservation.operation_state_path.write_text(
        json.dumps(operation_state, indent=2),
        encoding="utf-8",
    )
    content = "---\ntitle: Expired\n---\n\n# Handoff\n"
    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

    with pytest.raises(active_writes.ActiveWriteError, match="reservation expired"):
        active_writes.write_active_handoff(
            tmp_path,
            operation_state_path=reservation.operation_state_path,
            content=content,
            content_sha256=content_hash,
        )

    updated = json.loads(reservation.operation_state_path.read_text(encoding="utf-8"))
    active_path = Path(updated["allocated_active_path"])
    transaction = json.loads(
        Path(updated["transaction_path"]).read_text(encoding="utf-8")
    )
    assert updated["status"] == "reservation_expired"
    assert transaction["status"] == "reservation_expired"
    assert not active_path.exists()


def test_write_active_handoff_rejects_changed_state_snapshot_before_output_write(
    tmp_path: Path,
) -> None:
    reservation = active_writes.begin_active_write(
        tmp_path,
        project_name="demo",
        operation="save",
        slug="state-conflict",
        created_at="2026-05-13T16:45:00Z",
    )
    state_dir = tmp_path / ".claude" / "handoffs" / ".session-state"
    conflicting_state = state_dir / "handoff-demo-conflict.json"
    conflicting_state.write_text(
        json.dumps(
            {
                "state_path": str(conflicting_state),
                "project": "demo",
                "resume_token": "conflict",
                "archive_path": "/tmp/other.md",
                "created_at": "2026-05-13T16:01:00Z",
            }
        ),
        encoding="utf-8",
    )
    content = "---\ntitle: State conflict\n---\n\n# Handoff\n"
    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

    with pytest.raises(active_writes.ActiveWriteError, match="state snapshot changed"):
        active_writes.write_active_handoff(
            tmp_path,
            operation_state_path=reservation.operation_state_path,
            content=content,
            content_sha256=content_hash,
        )

    updated = json.loads(reservation.operation_state_path.read_text(encoding="utf-8"))
    active_path = Path(updated["allocated_active_path"])
    transaction = json.loads(
        Path(updated["transaction_path"]).read_text(encoding="utf-8")
    )
    assert updated["status"] == "reservation_conflict"
    assert updated["conflict_reason"] == "state_snapshot_changed"
    assert transaction["status"] == "reservation_conflict"
    assert not active_path.exists()


def test_write_active_handoff_rejects_changed_transaction_watermark_before_output_write(
    tmp_path: Path,
) -> None:
    reservation = active_writes.begin_active_write(
        tmp_path,
        project_name="demo",
        operation="save",
        slug="transaction-conflict",
        created_at="2026-05-13T16:45:00Z",
    )
    conflict_transaction = (
        tmp_path
        / ".claude"
        / "handoffs"
        / ".session-state"
        / "transactions"
        / "external-conflict.json"
    )
    conflict_transaction.write_text(
        json.dumps(
            {
                "transaction_id": "external-conflict",
                "operation": "load",
                "status": "completed",
            }
        ),
        encoding="utf-8",
    )
    content = "---\ntitle: Transaction conflict\n---\n\n# Handoff\n"
    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

    with pytest.raises(
        active_writes.ActiveWriteError, match="transaction watermark changed"
    ):
        active_writes.write_active_handoff(
            tmp_path,
            operation_state_path=reservation.operation_state_path,
            content=content,
            content_sha256=content_hash,
        )

    updated = json.loads(reservation.operation_state_path.read_text(encoding="utf-8"))
    active_path = Path(updated["allocated_active_path"])
    transaction = json.loads(
        Path(updated["transaction_path"]).read_text(encoding="utf-8")
    )
    assert updated["status"] == "reservation_conflict"
    assert updated["conflict_reason"] == "transaction_watermark_changed"
    assert transaction["status"] == "reservation_conflict"
    assert not active_path.exists()


# ── Lock liveness tests ─────────────────────────────────────────────


def _lock_path(tmp_path: Path) -> Path:
    return (
        tmp_path
        / ".claude"
        / "handoffs"
        / ".session-state"
        / "locks"
        / "active-write.lock"
    )


def _valid_lock_metadata(
    *,
    created_at: datetime | None = None,
    timeout_seconds: int = 1800,
    hostname: str | None = None,
) -> dict[str, object]:
    return {
        "project": "demo",
        "operation": "save",
        "transaction_id": "existing-lock",
        "lock_id": "existing-lock",
        "pid": os.getpid(),
        "hostname": hostname or socket.gethostname(),
        "created_at": (created_at or datetime.now(UTC)).isoformat(),
        "timeout_seconds": timeout_seconds,
    }


def _stage_lock(tmp_path: Path, metadata: dict[str, object]) -> Path:
    lock = _lock_path(tmp_path)
    lock.parent.mkdir(parents=True, exist_ok=True)
    lock.write_text(json.dumps(metadata), encoding="utf-8")
    return lock


def test_active_write_lock_blocks_within_timeout(tmp_path: Path) -> None:
    lock = _stage_lock(tmp_path, _valid_lock_metadata(created_at=datetime.now(UTC)))
    with pytest.raises(active_writes.ActiveWriteError, match="lock is already held"):
        active_writes.begin_active_write(
            tmp_path,
            project_name="demo",
            operation="save",
            created_at="2026-05-13T16:45:00Z",
        )
    assert lock.exists()


def test_active_write_lock_held_diagnostic_preserves_wrapper_message(
    tmp_path: Path,
) -> None:
    lock = _stage_lock(tmp_path, _valid_lock_metadata(created_at=datetime.now(UTC)))
    expected = (
        "begin-active-write failed: project active-write lock is already held. "
        f"Got: {str(lock)!r:.100}"
    )
    with pytest.raises(active_writes.ActiveWriteError) as exc_info:
        active_writes._acquire_lock(
            lock,
            project="demo",
            operation="save",
            transaction_id="new-lock",
        )
    assert str(exc_info.value) == expected


def test_active_write_lock_recovers_from_stale_lock_same_host_after_timeout(
    tmp_path: Path,
) -> None:
    stale_time = datetime.now(UTC) - timedelta(hours=2)
    _stage_lock(tmp_path, _valid_lock_metadata(created_at=stale_time))
    reservation = active_writes.begin_active_write(
        tmp_path,
        project_name="demo",
        operation="save",
        created_at="2026-05-13T16:45:00Z",
    )
    lock = _lock_path(tmp_path)
    assert not lock.exists()
    state = json.loads(reservation.operation_state_path.read_text(encoding="utf-8"))
    assert state["transaction_id"] != "existing-lock"


def test_active_write_lock_fails_closed_on_unparseable_metadata(tmp_path: Path) -> None:
    lock = _lock_path(tmp_path)
    lock.parent.mkdir(parents=True, exist_ok=True)
    lock.write_text("not-json", encoding="utf-8")
    with pytest.raises(
        active_writes.ActiveWriteError, match="lock metadata unreadable"
    ):
        active_writes.begin_active_write(
            tmp_path,
            project_name="demo",
            operation="save",
            created_at="2026-05-13T16:45:00Z",
        )
    assert lock.exists()


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param([1, 2, 3], id="non-dict"),
        pytest.param({"project": "demo"}, id="missing-created_at"),
        pytest.param(
            {"created_at": "2026-01-01T00:00:00Z", "hostname": socket.gethostname()},
            id="missing-timeout_seconds",
        ),
        pytest.param(
            {"created_at": "2026-01-01T00:00:00Z", "timeout_seconds": 1800},
            id="missing-hostname",
        ),
        pytest.param(
            {
                "created_at": 12345,
                "timeout_seconds": 1800,
                "hostname": socket.gethostname(),
            },
            id="wrong-type-created_at",
        ),
        pytest.param(
            {
                "created_at": "2026-01-01T00:00:00Z",
                "timeout_seconds": "nope",
                "hostname": socket.gethostname(),
            },
            id="wrong-type-timeout_seconds",
        ),
        pytest.param(
            {
                "created_at": "2026-01-01T00:00:00Z",
                "timeout_seconds": 1800,
                "hostname": 42,
            },
            id="wrong-type-hostname",
        ),
        pytest.param(
            {
                "created_at": "not-a-date",
                "timeout_seconds": 1800,
                "hostname": socket.gethostname(),
            },
            id="unparsable-created_at",
        ),
    ],
)
def test_active_write_lock_fails_closed_on_malformed_json_metadata(
    tmp_path: Path,
    payload: object,
) -> None:
    lock = _lock_path(tmp_path)
    lock.parent.mkdir(parents=True, exist_ok=True)
    lock.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(active_writes.ActiveWriteError, match="lock metadata malformed"):
        active_writes.begin_active_write(
            tmp_path,
            project_name="demo",
            operation="save",
            created_at="2026-05-13T16:45:00Z",
        )
    assert lock.exists()


def test_active_write_lock_fails_closed_on_foreign_host(tmp_path: Path) -> None:
    stale_time = datetime.now(UTC) - timedelta(hours=2)
    lock = _stage_lock(
        tmp_path,
        _valid_lock_metadata(created_at=stale_time, hostname="different-host"),
    )
    with pytest.raises(
        active_writes.ActiveWriteError, match="stale lock from another host"
    ):
        active_writes.begin_active_write(
            tmp_path,
            project_name="demo",
            operation="save",
            created_at="2026-05-13T16:45:00Z",
        )
    assert lock.exists()


def test_active_write_lock_records_new_owner_during_critical_section(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stale_time = datetime.now(UTC) - timedelta(hours=2)
    _stage_lock(tmp_path, _valid_lock_metadata(created_at=stale_time))
    lock = _lock_path(tmp_path)
    observed: dict[str, object] = {}
    original = active_writes._continue_legacy_chain_state_if_unambiguous

    def spy(project_root: Path, *, project: str) -> None:
        if lock.exists():
            observed["metadata"] = json.loads(lock.read_text(encoding="utf-8"))
        original(project_root, project=project)

    monkeypatch.setattr(
        active_writes, "_continue_legacy_chain_state_if_unambiguous", spy
    )
    reservation = active_writes.begin_active_write(
        tmp_path,
        project_name="demo",
        operation="save",
        created_at="2026-05-13T16:45:00Z",
    )
    state = json.loads(reservation.operation_state_path.read_text(encoding="utf-8"))
    assert not lock.exists()
    assert observed["metadata"]["lock_id"] == state["transaction_id"]  # type: ignore[index]
    assert observed["metadata"]["lock_id"] != "existing-lock"  # type: ignore[index]


def test_active_write_lock_recovery_claim_present_fails_closed_with_live_hint(
    tmp_path: Path,
) -> None:
    stale_time = datetime.now(UTC) - timedelta(hours=2)
    lock = _stage_lock(tmp_path, _valid_lock_metadata(created_at=stale_time))
    claim_path = lock.with_name(lock.name + ".recovery")
    claim_path.write_text(
        json.dumps(
            {
                "pid": os.getpid(),
                "hostname": socket.gethostname(),
                "created_at": datetime.now(UTC).isoformat(),
                "timeout_seconds": 60,
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(
        active_writes.ActiveWriteError, match="recovery claim file present"
    ) as exc_info:
        active_writes.begin_active_write(
            tmp_path,
            project_name="demo",
            operation="save",
            created_at="2026-05-13T16:45:00Z",
        )
    assert "(live recoverer:" in str(exc_info.value)
    assert "trash" in str(exc_info.value)
    assert lock.exists()
    assert claim_path.exists()


def test_active_write_recovery_claim_diagnostic_preserves_wrapper_message(
    tmp_path: Path,
) -> None:
    lock = _stage_lock(
        tmp_path,
        _valid_lock_metadata(created_at=datetime.now(UTC) - timedelta(hours=2)),
    )
    claim_path = lock.with_name(lock.name + ".recovery")
    claim_payload = {
        "pid": 12345,
        "hostname": "test-host",
        "created_at": datetime.now(UTC).isoformat(),
        "timeout_seconds": 60,
    }
    claim_path.write_text(json.dumps(claim_payload), encoding="utf-8")
    expected = (
        "begin-active-write failed: recovery claim file present "
        "(live recoverer: pid=12345 host='test-host'); "
        f"if no process is actively recovering this lock, run `trash {claim_path}` and retry. "
        f"Got: {str(claim_path)!r:.100}"
    )
    with pytest.raises(active_writes.ActiveWriteError) as exc_info:
        active_writes._acquire_lock(
            lock,
            project="demo",
            operation="save",
            transaction_id="new-lock",
        )
    assert str(exc_info.value) == expected


def test_active_write_lock_recovery_claim_present_fails_closed_with_stale_hint(
    tmp_path: Path,
) -> None:
    stale_time = datetime.now(UTC) - timedelta(hours=2)
    lock = _stage_lock(tmp_path, _valid_lock_metadata(created_at=stale_time))
    claim_path = lock.with_name(lock.name + ".recovery")
    stale_claim_time = datetime.now(UTC) - timedelta(minutes=5)
    claim_path.write_text(
        json.dumps(
            {
                "pid": os.getpid(),
                "hostname": socket.gethostname(),
                "created_at": stale_claim_time.isoformat(),
                "timeout_seconds": 60,
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(
        active_writes.ActiveWriteError, match="recovery claim file present"
    ) as exc_info:
        active_writes.begin_active_write(
            tmp_path,
            project_name="demo",
            operation="save",
            created_at="2026-05-13T16:45:00Z",
        )
    assert "(likely stale:" in str(exc_info.value)
    assert "trash" in str(exc_info.value)
    assert lock.exists()
    assert claim_path.exists()


def test_active_write_lock_recovery_claim_unparseable_fails_closed(
    tmp_path: Path,
) -> None:
    stale_time = datetime.now(UTC) - timedelta(hours=2)
    lock = _stage_lock(tmp_path, _valid_lock_metadata(created_at=stale_time))
    claim_path = lock.with_name(lock.name + ".recovery")
    claim_path.write_text("not-json", encoding="utf-8")
    with pytest.raises(
        active_writes.ActiveWriteError, match="recovery claim file present"
    ) as exc_info:
        active_writes.begin_active_write(
            tmp_path,
            project_name="demo",
            operation="save",
            created_at="2026-05-13T16:45:00Z",
        )
    assert "(claim metadata unreadable)" in str(exc_info.value)
    assert "trash" in str(exc_info.value)
    assert lock.exists()
    assert claim_path.exists()


def test_active_write_lock_recovery_claim_malformed_fails_closed(
    tmp_path: Path,
) -> None:
    stale_time = datetime.now(UTC) - timedelta(hours=2)
    lock = _stage_lock(tmp_path, _valid_lock_metadata(created_at=stale_time))
    claim_path = lock.with_name(lock.name + ".recovery")
    claim_path.write_text(
        json.dumps({"created_at": 12345, "timeout_seconds": "nope"}),
        encoding="utf-8",
    )
    with pytest.raises(
        active_writes.ActiveWriteError, match="recovery claim file present"
    ):
        active_writes.begin_active_write(
            tmp_path,
            project_name="demo",
            operation="save",
            created_at="2026-05-13T16:45:00Z",
        )
    assert lock.exists()
    assert claim_path.exists()


def test_active_write_lock_recovery_claim_removed_then_operation_succeeds(
    tmp_path: Path,
) -> None:
    stale_time = datetime.now(UTC) - timedelta(hours=2)
    lock = _stage_lock(tmp_path, _valid_lock_metadata(created_at=stale_time))
    claim_path = lock.with_name(lock.name + ".recovery")
    stale_claim_time = datetime.now(UTC) - timedelta(minutes=5)
    claim_path.write_text(
        json.dumps(
            {
                "pid": os.getpid(),
                "hostname": socket.gethostname(),
                "created_at": stale_claim_time.isoformat(),
                "timeout_seconds": 60,
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(
        active_writes.ActiveWriteError, match="recovery claim file present"
    ):
        active_writes.begin_active_write(
            tmp_path,
            project_name="demo",
            operation="save",
            created_at="2026-05-13T16:45:00Z",
        )
    claim_path.unlink()
    reservation = active_writes.begin_active_write(
        tmp_path,
        project_name="demo",
        operation="save",
        created_at="2026-05-13T16:45:00Z",
    )
    assert not _lock_path(tmp_path).exists()
    state = json.loads(reservation.operation_state_path.read_text(encoding="utf-8"))
    assert state["transaction_id"] != "existing-lock"


def test_release_lock_preserves_session_state_dir(tmp_path: Path) -> None:
    reservation = active_writes.begin_active_write(
        tmp_path,
        project_name="demo",
        operation="save",
        created_at="2026-05-13T16:45:00Z",
    )
    session_state_dir = tmp_path / ".claude" / "handoffs" / ".session-state"
    assert session_state_dir.exists()
    assert not _lock_path(tmp_path).exists()
    assert reservation.operation_state_path.exists()


@pytest.mark.slow
def test_active_write_lock_live_contention_with_subprocess(tmp_path: Path) -> None:
    plugin_root = str(Path(__file__).resolve().parent.parent)

    lock_path = (
        tmp_path
        / ".claude"
        / "handoffs"
        / ".session-state"
        / "locks"
        / "active-write.lock"
    )
    lock_path_repr = repr(str(lock_path))

    ready_marker = tmp_path / "ready.marker"
    release_marker = tmp_path / "release.marker"
    ready_marker_repr = repr(str(ready_marker))
    release_marker_repr = repr(str(release_marker))

    code_a = f"""\
import sys, time
from pathlib import Path
from handoff_runtime.active_writes import _acquire_lock, _release_lock
lock_path = Path({lock_path_repr})
ready = Path({ready_marker_repr})
release = Path({release_marker_repr})
lock_path.parent.mkdir(parents=True, exist_ok=True)
_acquire_lock(lock_path, project="demo", operation="save", transaction_id="A")
ready.write_text("ready", encoding="utf-8")
deadline = time.monotonic() + 30.0
while not release.exists() and time.monotonic() < deadline:
    time.sleep(0.01)
if not release.exists():
    sys.exit(2)
_release_lock(lock_path)
"""

    code_b = f"""\
import sys
from pathlib import Path
from handoff_runtime.active_writes import _acquire_lock
lock_path = Path({lock_path_repr})
try:
    _acquire_lock(lock_path, project="demo", operation="save", transaction_id="B")
except Exception as exc:
    print(str(exc), file=sys.stderr)
    sys.exit(1)
"""

    proc_a = subprocess.Popen(
        [sys.executable, "-c", code_a],
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
        cwd=plugin_root,
    )
    deadline = time.monotonic() + 30.0
    while not ready_marker.exists() and time.monotonic() < deadline:
        time.sleep(0.01)
    assert ready_marker.exists(), (
        f"Process A did not become ready. "
        f"stderr={proc_a.stderr.read().decode() if proc_a.stderr else 'N/A'}"
    )

    result_b = subprocess.run(
        [sys.executable, "-c", code_b],
        capture_output=True,
        text=True,
        cwd=plugin_root,
    )
    assert result_b.returncode != 0, (
        f"Process B should have failed. stdout={result_b.stdout}"
    )
    assert "lock is already held" in result_b.stderr, (
        f"Expected 'lock is already held' in stderr. stderr={result_b.stderr}"
    )

    release_marker.write_text("release", encoding="utf-8")
    exit_code = proc_a.wait(timeout=10)
    assert exit_code == 0, (
        f"Process A exited with {exit_code}. "
        f"stderr={proc_a.stderr.read().decode() if proc_a.stderr else 'N/A'}"
    )

    result_b2 = subprocess.run(
        [sys.executable, "-c", code_b],
        capture_output=True,
        text=True,
        cwd=plugin_root,
    )
    assert result_b2.returncode == 0, (
        f"Process B should succeed after A released. stderr={result_b2.stderr}"
    )


# ── Corruption fail-closed tests ────────────────────────────────────


def test_ensure_no_compatible_reservation_fails_closed_on_corrupt_record(
    tmp_path: Path,
) -> None:
    corrupt_dir = (
        tmp_path / ".claude" / "handoffs" / ".session-state" / "active-writes" / "demo"
    )
    corrupt_dir.mkdir(parents=True, exist_ok=True)
    corrupt_file = corrupt_dir / "garbage.json"
    corrupt_file.write_text("not-json{{{", encoding="utf-8")
    with pytest.raises(
        active_writes.ActiveWriteError, match="active-write record unreadable"
    ):
        active_writes.begin_active_write(
            tmp_path,
            project_name="demo",
            operation="save",
            created_at="2026-05-13T16:45:00Z",
        )


def test_existing_reservation_reports_corrupt_operation_state(tmp_path: Path) -> None:
    state_dir = tmp_path / ".claude" / "handoffs" / ".session-state"
    operation_state_path = state_dir / "active-writes" / "demo" / "run-1.json"
    operation_state_path.parent.mkdir(parents=True, exist_ok=True)
    operation_state_path.write_text("{bad", encoding="utf-8")

    with pytest.raises(
        active_writes.ActiveWriteError, match="operation state unreadable"
    ):
        active_writes.begin_active_write(
            tmp_path,
            project_name="demo",
            operation="save",
            run_id="run-1",
            created_at="2026-05-14T00:00:00Z",
        )


def test_write_active_handoff_reports_corrupt_operation_state(tmp_path: Path) -> None:
    operation_state_path = (
        tmp_path
        / ".claude"
        / "handoffs"
        / ".session-state"
        / "active-writes"
        / "demo"
        / "run-2.json"
    )
    operation_state_path.parent.mkdir(parents=True, exist_ok=True)
    operation_state_path.write_text("{bad", encoding="utf-8")

    with pytest.raises(
        active_writes.ActiveWriteError, match="operation state unreadable"
    ):
        active_writes.write_active_handoff(
            tmp_path,
            operation_state_path=operation_state_path,
            content="content",
            content_sha256=hashlib.sha256(b"content").hexdigest(),
        )


def test_integrity_failure_rejected_before_promotion(tmp_path: Path) -> None:
    reservation = active_writes.begin_active_write(
        tmp_path,
        project_name="demo",
        operation="save",
        slug="integrity-gate",
        created_at="2026-05-13T16:45:00Z",
    )
    operation_state_path = reservation.operation_state_path
    allocated_active_path = reservation.allocated_active_path
    # Valid frontmatter, all required sections present but empty -> hollow
    # (hollow-handoff guardrail fires at the integrity tier).
    hollow = (
        '---\ndate: 2026-01-01\ntime: "00:00"\ncreated_at: x\n'
        "session_id: s\nproject: p\ntitle: t\ntype: handoff\n---\n"
        + "".join(f"## {s}\n\n" for s in _HANDOFF_SECTIONS)
    )
    sha = hashlib.sha256(hollow.encode()).hexdigest()

    with pytest.raises(active_writes.ActiveWriteError) as ei:
        active_writes.write_active_handoff(
            tmp_path,
            operation_state_path=operation_state_path,
            content=hollow,
            content_sha256=sha,
        )

    assert "integrity" in str(ei.value).lower()
    assert not allocated_active_path.exists()  # NOT promoted


def test_integrity_gate_reservation_stays_recoverable(tmp_path: Path) -> None:
    reservation = active_writes.begin_active_write(
        tmp_path,
        project_name="demo",
        operation="save",
        slug="integrity-gate-recovery",
        created_at="2026-05-13T16:45:00Z",
    )
    operation_state_path = reservation.operation_state_path
    allocated_active_path = reservation.allocated_active_path
    hollow = (
        '---\ndate: 2026-01-01\ntime: "00:00"\ncreated_at: x\n'
        "session_id: s\nproject: p\ntitle: t\ntype: handoff\n---\n"
        + "".join(f"## {s}\n\n" for s in _HANDOFF_SECTIONS)
    )
    sha = hashlib.sha256(hollow.encode()).hexdigest()

    with pytest.raises(active_writes.ActiveWriteError):
        active_writes.write_active_handoff(
            tmp_path,
            operation_state_path=operation_state_path,
            content=hollow,
            content_sha256=sha,
        )

    # (a) operation_state_path still exists
    assert operation_state_path.exists()

    # (b) recovery commands include continue/retry_write/abandon
    recovery = active_writes._recovery_commands(tmp_path, operation_state_path)
    assert "continue" in recovery
    assert "retry_write" in recovery
    assert "abandon" in recovery

    # (c) no partial .md at allocated_active_path, no leftover .tmp sibling
    assert not allocated_active_path.exists()
    siblings = list(
        allocated_active_path.parent.glob(f".{allocated_active_path.name}.*.tmp")
    )
    assert not siblings

    # (d) status still "begun" — no operation-state mutation occurred
    state = json.loads(operation_state_path.read_text(encoding="utf-8"))
    assert state["status"] == "begun"


def test_persist_operation_and_transaction_failure_leaves_operation_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Characterization (PR #15 #5): if the transaction write fails after the
    operation-state write, the error propagates and operation state is on disk
    (recovery keys off operation state, written first). The transaction file
    must not exist."""
    op_path = tmp_path / "active-writes" / "demo" / "run.json"
    tx_path = tmp_path / "transactions" / "run.json"
    state: dict[str, object] = {"project": "demo", "status": "write-pending"}

    real_write = storage_primitives.write_json_atomic

    def selective_write(path: Path, payload: dict[str, object]) -> None:
        if path == tx_path:
            raise OSError("transaction write failed")
        real_write(path, payload)

    monkeypatch.setattr(storage_primitives, "write_json_atomic", selective_write)

    with pytest.raises(OSError, match="transaction write failed"):
        active_writes._persist_operation_and_transaction(
            op_path,
            tx_path,
            state,
            transaction_status="write-pending",
        )

    assert op_path.exists()
    assert json.loads(op_path.read_text(encoding="utf-8"))["status"] == "write-pending"
    assert not tx_path.exists()


# ── AC#5 test matrix ──────────────────────────────────────────────────
#
# Cells (b5) and (e) are already covered by Task 2:
#   (b5) hollow → test_integrity_failure_rejected_before_promotion
#   (e)  reservation/staging cleanup after rejection →
#            test_integrity_gate_reservation_stays_recoverable
#
# The remaining cells are below.


def _build_handoff_content(
    *,
    body_lines: int | None = None,
    omit_section: str | None = None,
    omit_field: str | None = None,
    override_type: str | None = None,
    no_frontmatter: bool = False,
) -> str:
    """Build a handoff document string with optional defects injected.

    Produces a document that, when no defects are requested, passes the
    integrity gate exactly: all 7 frontmatter fields, all 13 handoff
    sections present, Decisions has substantive content (hollow guardrail
    satisfied).  Body line count is NOT padded by default — callers set
    body_lines to control length.

    Args:
        body_lines: lower bound: pads with filler if natural body is shorter;
            ignored if natural body is already longer.  None → use natural
            section body.
        omit_section: drop this section name from the body.
        omit_field: drop this frontmatter key.
        override_type: replace the `type` frontmatter value.
        no_frontmatter: if True, omit the entire YAML block.
    """
    doc_type = override_type if override_type is not None else "handoff"

    frontmatter_fields: dict[str, str] = {
        "date": "2026-05-13",
        "time": '"16:45"',
        "created_at": "2026-05-13T16:45:00+00:00",
        "session_id": "ac5-test-run",
        "project": "demo",
        "title": "AC5 matrix test",
        "type": doc_type,
    }
    if omit_field is not None:
        frontmatter_fields.pop(omit_field, None)

    sections = [s for s in REQUIRED_HANDOFF_SECTIONS if s != omit_section]

    # Build section bodies — Decisions gets substantive content.
    section_lines: list[str] = []
    for section in sections:
        section_lines.append(f"## {section}")
        section_lines.append("")
        if section == "Decisions":
            section_lines.append("Decision: proceed with implementation.")
        section_lines.append("")

    # Pad body to reach body_lines if requested.
    if body_lines is not None:
        current = len(section_lines)
        while current < body_lines:
            section_lines.append("filler line for line-count test")
            current += 1

    body = "\n".join(section_lines)

    if no_frontmatter:
        return body

    fm_pairs = "\n".join(f"{k}: {v}" for k, v in frontmatter_fields.items())
    return f"---\n{fm_pairs}\n---\n\n{body}"


def _build_summary_content(*, body_lines: int) -> str:
    """Build a summary document that passes the integrity gate.

    All 8 required summary sections present; Decisions has substantive
    content.  body_lines is a lower bound: pads with filler if natural body
    is shorter; ignored if natural body is already longer.
    """
    section_lines: list[str] = []
    for section in REQUIRED_SUMMARY_SECTIONS:
        section_lines.append(f"## {section}")
        section_lines.append("")
        if section == "Decisions":
            section_lines.append("Decision: summary approach confirmed.")
        section_lines.append("")

    while len(section_lines) < body_lines:
        section_lines.append("filler line for over-max summary test")

    body = "\n".join(section_lines)
    fm = (
        "---\n"
        "date: 2026-05-13\n"
        'time: "16:45"\n'
        "created_at: 2026-05-13T16:45:00+00:00\n"
        "session_id: ac5-summary-run\n"
        "project: demo\n"
        "title: Summary: AC5 over-max test\n"
        "type: summary\n"
        "---\n\n"
    )
    return fm + body


# ── (a) clean handoff promotes ────────────────────────────────────────


def test_ac5_clean_handoff_promotes(tmp_path: Path) -> None:
    """(a) A document with all required fields, all required sections,
    substantive Decisions content, and body >= HANDOFF_MIN_LINES promotes
    without error and is written byte-equal to the input.
    """
    content = _build_handoff_content(body_lines=HANDOFF_MIN_LINES + 10)
    assert count_body_lines(content) >= HANDOFF_MIN_LINES

    reservation = active_writes.begin_active_write(
        tmp_path,
        project_name="demo",
        operation="save",
        slug="ac5-clean",
        created_at="2026-05-13T16:45:00Z",
    )
    operation_state_path = reservation.operation_state_path
    allocated_active_path = reservation.allocated_active_path
    sha = hashlib.sha256(content.encode()).hexdigest()

    # Must not raise.
    active_writes.write_active_handoff(
        tmp_path,
        operation_state_path=operation_state_path,
        content=content,
        content_sha256=sha,
    )

    assert allocated_active_path.exists()
    assert allocated_active_path.read_text(encoding="utf-8") == content
    # Explicit: no integrity-tier issues.
    integrity_issues = [i for i in validate(content) if i.tier == "integrity"]
    assert not integrity_issues


# ── (b1-b4) integrity rejection cases ────────────────────────────────


@pytest.mark.parametrize(
    ("label", "content_builder", "expected_message_fragment"),
    [
        pytest.param(
            "b1-no-frontmatter",
            lambda: _build_handoff_content(no_frontmatter=True),
            "No frontmatter",
            id="b1-no-frontmatter",
        ),
        pytest.param(
            "b2-invalid-type",
            lambda: _build_handoff_content(override_type="bogus"),
            "Invalid type",
            id="b2-invalid-type",
        ),
        pytest.param(
            "b3-missing-required-field",
            lambda: _build_handoff_content(omit_field="session_id"),
            "Missing required frontmatter",
            id="b3-missing-required-field",
        ),
        pytest.param(
            "b4-missing-required-section",
            lambda: _build_handoff_content(omit_section="Decisions"),
            "Missing required sections",
            id="b4-missing-required-section",
        ),
        # (b5) hollow → already covered by test_integrity_failure_rejected_before_promotion
    ],
)
def test_ac5_integrity_rejection(
    tmp_path: Path,
    label: str,
    content_builder: Callable[[], str],
    expected_message_fragment: str,
) -> None:
    """(b1-b4) Each integrity-tier defect raises ActiveWriteError before promotion.

    For each variant: the error message mentions 'integrity', the allocated
    active path is NOT created, and validate() confirms at least one
    tier='integrity' issue whose message contains the expected fragment.
    """
    content = content_builder()
    sha = hashlib.sha256(content.encode()).hexdigest()

    reservation = active_writes.begin_active_write(
        tmp_path,
        project_name="demo",
        operation="save",
        slug=label,
        created_at="2026-05-13T16:45:00Z",
    )
    operation_state_path = reservation.operation_state_path
    allocated_active_path = reservation.allocated_active_path

    with pytest.raises(active_writes.ActiveWriteError, match="integrity"):
        active_writes.write_active_handoff(
            tmp_path,
            operation_state_path=operation_state_path,
            content=content,
            content_sha256=sha,
        )

    assert not allocated_active_path.exists()

    integrity_issues = [i for i in validate(content) if i.tier == "integrity"]
    assert integrity_issues, "validate() must yield at least one integrity-tier issue"
    messages = " ".join(i.message for i in integrity_issues)
    assert expected_message_fragment in messages, (
        f"Expected {expected_message_fragment!r} in integrity issues: {messages!r}"
    )


# ── (c) LINCHPIN: under-min still promotes ────────────────────────────


def test_ac5_under_min_still_promotes(tmp_path: Path) -> None:
    """(c) AC#5 linchpin: validate_line_count's severity='error' under-min
    issue is tier='advisory'; the gate must NOT reject it.

    Gating on severity here would break /save under context pressure — the
    exact failure mode the tier partition exists to prevent.
    """
    # Build a document that passes all integrity checks but is under the
    # HANDOFF_MIN_LINES body threshold.  Sections are all present; Decisions
    # has substantive content; body is STRICTLY less than HANDOFF_MIN_LINES.
    content = _build_handoff_content(body_lines=HANDOFF_MIN_LINES - 10)

    # Precondition: self-check that body IS under minimum.
    actual_body = count_body_lines(content)
    assert actual_body < HANDOFF_MIN_LINES, (
        f"Test setup error: body_lines={actual_body} is not < HANDOFF_MIN_LINES={HANDOFF_MIN_LINES}"
    )

    reservation = active_writes.begin_active_write(
        tmp_path,
        project_name="demo",
        operation="save",
        slug="ac5-under-min",
        created_at="2026-05-13T16:45:00Z",
    )
    operation_state_path = reservation.operation_state_path
    allocated_active_path = reservation.allocated_active_path
    sha = hashlib.sha256(content.encode()).hexdigest()

    # Must NOT raise — advisory issues must not gate.
    active_writes.write_active_handoff(
        tmp_path,
        operation_state_path=operation_state_path,
        content=content,
        content_sha256=sha,
    )

    assert allocated_active_path.exists()
    assert allocated_active_path.read_text(encoding="utf-8") == content

    # Explicit: validate produces the expected advisory under-min issue
    # with severity='error' AND tier='advisory', confirming the decoupling.
    issues = validate(content)
    under_min_issues = [
        i
        for i in issues
        if i.severity == "error" and i.tier == "advisory" and "minimum" in i.message
    ]
    assert under_min_issues, (
        "Expected at least one severity='error', tier='advisory' issue mentioning 'minimum'. "
        f"Got: {[(i.severity, i.tier, i.message) for i in issues]}"
    )
    # And no integrity-tier issues — they would have blocked.
    integrity_issues = [i for i in issues if i.tier == "integrity"]
    assert not integrity_issues


# ── (d) over-max still promotes (summary) ────────────────────────────


def test_ac5_over_max_still_promotes(tmp_path: Path) -> None:
    """(d) A summary document whose body exceeds SUMMARY_MAX_LINES still
    promotes — over-max is tier='advisory', never blocks the gate.
    """
    content = _build_summary_content(body_lines=SUMMARY_MAX_LINES + 20)

    # Precondition: self-check body IS over maximum.
    actual_body = count_body_lines(content)
    assert actual_body > SUMMARY_MAX_LINES, (
        f"Test setup error: body_lines={actual_body} is not > SUMMARY_MAX_LINES={SUMMARY_MAX_LINES}"
    )

    reservation = active_writes.begin_active_write(
        tmp_path,
        project_name="demo",
        operation="summary",
        slug="ac5-over-max",
        created_at="2026-05-13T16:45:00Z",
    )
    operation_state_path = reservation.operation_state_path
    allocated_active_path = reservation.allocated_active_path
    sha = hashlib.sha256(content.encode()).hexdigest()

    # Must NOT raise — over-max is advisory.
    active_writes.write_active_handoff(
        tmp_path,
        operation_state_path=operation_state_path,
        content=content,
        content_sha256=sha,
    )

    assert allocated_active_path.exists()
    assert allocated_active_path.read_text(encoding="utf-8") == content

    # Explicit: validate yields a tier='advisory' over-max issue.
    issues = validate(content)
    over_max_issues = [
        i
        for i in issues
        if i.severity == "warning" and i.tier == "advisory" and "maximum" in i.message
    ]
    assert over_max_issues, (
        "Expected at least one tier='advisory' issue mentioning 'maximum'. "
        f"Got: {[(i.severity, i.tier, i.message) for i in issues]}"
    )
    # And no integrity-tier issues.
    integrity_issues = [i for i in issues if i.tier == "integrity"]
    assert not integrity_issues
