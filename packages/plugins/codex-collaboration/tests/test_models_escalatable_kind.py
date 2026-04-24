"""Packet 1: EscalatableRequestKind narrows PendingEscalationView.kind to 3 literals."""

from __future__ import annotations

from typing import get_args, get_type_hints

from server.models import (
    EscalatableRequestKind,
    PendingEscalationView,
    PendingRequestKind,
)


def test_escalatable_kind_has_three_literals() -> None:
    assert set(get_args(EscalatableRequestKind)) == {
        "command_approval",
        "file_change",
        "request_user_input",
    }


def test_escalatable_kind_excludes_unknown() -> None:
    assert "unknown" not in get_args(EscalatableRequestKind)


def test_pending_request_kind_unchanged() -> None:
    # PendingRequestKind is still the 4-literal persisted kind; unknown is a
    # valid persisted kind (parse-failure audit record) but NOT escalatable.
    assert set(get_args(PendingRequestKind)) == {
        "command_approval",
        "file_change",
        "request_user_input",
        "unknown",
    }


def test_pending_escalation_view_kind_narrowed() -> None:
    hints = get_type_hints(PendingEscalationView)
    assert hints["kind"] is EscalatableRequestKind
