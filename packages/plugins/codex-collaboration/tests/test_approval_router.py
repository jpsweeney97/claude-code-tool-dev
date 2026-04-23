from __future__ import annotations

from pathlib import Path

from server.approval_router import (
    is_within_delegation_boundary,
    parse_pending_server_request,
)


def test_parse_integer_request_id_normalized_to_string() -> None:
    """Integer request IDs are accepted and normalized to string."""
    message = {
        "id": 42,
        "method": "item/commandExecution/requestApproval",
        "params": {
            "itemId": "item-1",
            "threadId": "thr-1",
            "turnId": "turn-1",
            "command": "echo hello",
            "cwd": "/repo",
        },
    }
    result = parse_pending_server_request(
        message, runtime_id="rt-1", collaboration_id="collab-1"
    )
    assert result.request_id == "42"  # Normalized to string
    assert result.kind == "command_approval"


def test_parse_command_approval_preserves_request_payload_opaquely() -> None:
    message = {
        "id": "req-1",
        "method": "item/commandExecution/requestApproval",
        "params": {
            "approvalId": "appr-1",
            "itemId": "item-1",
            "threadId": "thr-1",
            "turnId": "turn-1",
            "command": "pytest packages/plugins/codex-collaboration/tests/test_runtime.py",
            "cwd": "/repo/worktree",
            "commandActions": [
                {
                    "type": "search",
                    "command": "pytest packages/plugins/codex-collaboration/tests/test_runtime.py",
                    "path": "packages/plugins/codex-collaboration/tests/test_runtime.py",
                    "query": None,
                }
            ],
            "proposedExecpolicyAmendment": ["pytest"],
            "reason": "Need to execute tests inside the isolated worktree.",
            "availableDecisions": ["accept", "decline", "cancel"],
        },
    }

    request = parse_pending_server_request(
        message,
        runtime_id="runtime-1",
        collaboration_id="collab-1",
    )

    assert request.request_id == "req-1"
    assert request.runtime_id == "runtime-1"
    assert request.collaboration_id == "collab-1"
    assert request.codex_thread_id == "thr-1"
    assert request.codex_turn_id == "turn-1"
    assert request.item_id == "item-1"
    assert request.kind == "command_approval"
    assert request.available_decisions == ("accept", "decline", "cancel")
    assert request.requested_scope == {
        "approvalId": "appr-1",
        "command": "pytest packages/plugins/codex-collaboration/tests/test_runtime.py",
        "cwd": "/repo/worktree",
        "commandActions": [
            {
                "type": "search",
                "command": "pytest packages/plugins/codex-collaboration/tests/test_runtime.py",
                "path": "packages/plugins/codex-collaboration/tests/test_runtime.py",
                "query": None,
            }
        ],
        "proposedExecpolicyAmendment": ["pytest"],
        "reason": "Need to execute tests inside the isolated worktree.",
    }


def test_parse_file_change_approval_preserves_request_payload_opaquely() -> None:
    message = {
        "id": "req-2",
        "method": "item/fileChange/requestApproval",
        "params": {
            "itemId": "item-2",
            "threadId": "thr-2",
            "turnId": "turn-2",
            "grantRoot": "/repo/worktree/generated",
            "reason": "Need to write generated fixtures outside the default root.",
        },
    }

    request = parse_pending_server_request(
        message,
        runtime_id="runtime-2",
        collaboration_id="collab-2",
    )

    assert request.request_id == "req-2"
    assert request.kind == "file_change"
    assert request.requested_scope == {
        "grantRoot": "/repo/worktree/generated",
        "reason": "Need to write generated fixtures outside the default root.",
    }


def test_parse_unknown_server_request_falls_back_to_unknown_kind() -> None:
    message = {
        "id": "req-3",
        "method": "item/surprise/requestApproval",
        "params": {
            "itemId": "item-3",
            "threadId": "thr-3",
            "turnId": "turn-3",
            "scope": {"surpriseAccess": True},
            "reason": "Need an unsupported access profile.",
        },
    }

    request = parse_pending_server_request(
        message,
        runtime_id="runtime-3",
        collaboration_id="collab-3",
    )

    assert request.request_id == "req-3"
    assert request.kind == "unknown"
    assert request.requested_scope == {
        "scope": {"surpriseAccess": True},
        "reason": "Need an unsupported access profile.",
    }


def test_parse_permissions_request_falls_back_to_unknown_kind() -> None:
    message = {
        "id": "req-4",
        "method": "item/permissions/requestApproval",
        "params": {
            "itemId": "item-4",
            "threadId": "thr-4",
            "turnId": "turn-4",
            "reason": "Select a workspace root",
            "permissions": {
                "fileSystem": {
                    "write": ["/repo/worktree", "/repo/shared"],
                }
            },
        },
    }

    request = parse_pending_server_request(
        message,
        runtime_id="runtime-4",
        collaboration_id="collab-4",
    )

    assert request.request_id == "req-4"
    assert request.kind == "unknown"
    assert request.available_decisions == ()
    assert request.requested_scope == {
        "reason": "Select a workspace root",
        "permissions": {
            "fileSystem": {
                "write": ["/repo/worktree", "/repo/shared"],
            }
        },
    }


def test_malformed_available_decisions_fails_closed() -> None:
    """Present but malformed availableDecisions must fail closed (empty tuple)."""
    message = {
        "id": "req-5",
        "method": "item/commandExecution/requestApproval",
        "params": {
            "itemId": "item-5",
            "threadId": "thr-5",
            "turnId": "turn-5",
            "command": "ls",
            "availableDecisions": "cancel",
        },
    }

    request = parse_pending_server_request(
        message, runtime_id="rt-5", collaboration_id="collab-5"
    )

    assert request.available_decisions == ()


def test_absent_available_decisions_uses_schema_default() -> None:
    """When availableDecisions is completely absent, use the schema default for the kind."""
    message = {
        "id": "req-6",
        "method": "item/commandExecution/requestApproval",
        "params": {
            "itemId": "item-6",
            "threadId": "thr-6",
            "turnId": "turn-6",
            "command": "ls",
        },
    }

    request = parse_pending_server_request(
        message, runtime_id="rt-6", collaboration_id="collab-6"
    )

    assert "accept" in request.available_decisions
    assert "cancel" in request.available_decisions


def test_command_approval_never_counts_as_within_boundary() -> None:
    """Opaque command payloads must always escalate, even with in-worktree cwd."""
    message = {
        "id": "req-7",
        "method": "item/commandExecution/requestApproval",
        "params": {
            "itemId": "item-7",
            "threadId": "thr-7",
            "turnId": "turn-7",
            "command": "/bin/cat /etc/passwd",
            "cwd": "/repo/worktree/src",
            "availableDecisions": ["accept", "decline", "cancel"],
        },
    }

    request = parse_pending_server_request(
        message, runtime_id="rt-7", collaboration_id="collab-7"
    )

    assert (
        is_within_delegation_boundary(request, Path("/repo/worktree")) is False
    )


def test_file_change_with_in_worktree_grant_root_is_within_boundary() -> None:
    """File-change inline accept remains keyed to the actual grant scope."""
    message = {
        "id": "req-8",
        "method": "item/fileChange/requestApproval",
        "params": {
            "itemId": "item-8",
            "threadId": "thr-8",
            "turnId": "turn-8",
            "grantRoot": "/repo/worktree/generated",
        },
    }

    request = parse_pending_server_request(
        message, runtime_id="rt-8", collaboration_id="collab-8"
    )

    assert is_within_delegation_boundary(request, Path("/repo/worktree")) is True


def test_file_change_with_out_of_worktree_grant_root_is_outside_boundary() -> None:
    """Grant roots outside the worktree still fail the boundary check."""
    message = {
        "id": "req-9",
        "method": "item/fileChange/requestApproval",
        "params": {
            "itemId": "item-9",
            "threadId": "thr-9",
            "turnId": "turn-9",
            "grantRoot": "/tmp/generated",
        },
    }

    request = parse_pending_server_request(
        message, runtime_id="rt-9", collaboration_id="collab-9"
    )

    assert is_within_delegation_boundary(request, Path("/repo/worktree")) is False
