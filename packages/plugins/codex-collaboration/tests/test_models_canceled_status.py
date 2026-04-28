"""Packet 1: JobStatus + DelegationTerminalStatus + _TERMINAL_STATUS_MAP admit canceled."""

from __future__ import annotations

from typing import get_args

from server.delegation_controller import _TERMINAL_STATUS_MAP
from server.models import DelegationTerminalStatus, JobStatus


def test_job_status_admits_canceled() -> None:
    assert "canceled" in get_args(JobStatus)


def test_delegation_terminal_status_admits_canceled() -> None:
    assert "canceled" in get_args(DelegationTerminalStatus)


def test_terminal_status_map_maps_canceled_to_canceled() -> None:
    assert _TERMINAL_STATUS_MAP.get("canceled") == "canceled"


def test_terminal_status_map_has_four_entries_post_packet_1() -> None:
    assert set(_TERMINAL_STATUS_MAP.keys()) == {"completed", "failed", "canceled", "unknown"}
