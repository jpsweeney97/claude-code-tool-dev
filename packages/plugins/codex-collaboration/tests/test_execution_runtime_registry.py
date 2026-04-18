"""Tests for ExecutionRuntimeRegistry — live-ownership table only, not durability."""

from __future__ import annotations

import pytest

from server.execution_runtime_registry import (
    ExecutionRuntimeEntry,
    ExecutionRuntimeRegistry,
)


class _FakeSession:
    """Minimal session stand-in — the registry only retains it, doesn't call into it."""

    def __init__(self, name: str = "sess") -> None:
        self.name = name


def test_register_and_lookup_round_trip() -> None:
    registry = ExecutionRuntimeRegistry()
    session = _FakeSession("s1")
    registry.register(
        runtime_id="rt-1",
        session=session,  # type: ignore[arg-type]
        thread_id="thr-1",
        job_id="job-1",
    )

    entry = registry.lookup("rt-1")
    assert entry is not None
    assert isinstance(entry, ExecutionRuntimeEntry)
    assert entry.runtime_id == "rt-1"
    assert entry.session is session
    assert entry.thread_id == "thr-1"
    assert entry.job_id == "job-1"


def test_lookup_of_unknown_runtime_returns_none() -> None:
    registry = ExecutionRuntimeRegistry()
    assert registry.lookup("nope") is None


def test_register_rejects_duplicate_runtime_id() -> None:
    registry = ExecutionRuntimeRegistry()
    registry.register(
        runtime_id="rt-1",
        session=_FakeSession("a"),  # type: ignore[arg-type]
        thread_id="thr-1",
        job_id="job-1",
    )
    with pytest.raises(RuntimeError, match="already registered"):
        registry.register(
            runtime_id="rt-1",
            session=_FakeSession("b"),  # type: ignore[arg-type]
            thread_id="thr-1b",
            job_id="job-1b",
        )


def test_release_removes_entry_and_returns_it() -> None:
    registry = ExecutionRuntimeRegistry()
    session = _FakeSession("s1")
    registry.register(
        runtime_id="rt-1",
        session=session,  # type: ignore[arg-type]
        thread_id="thr-1",
        job_id="job-1",
    )

    released = registry.release("rt-1")
    assert released is not None
    assert released.session is session
    assert registry.lookup("rt-1") is None


def test_release_of_unknown_runtime_is_a_noop_returning_none() -> None:
    registry = ExecutionRuntimeRegistry()
    assert registry.release("nope") is None


def test_active_runtime_ids_reflects_live_state() -> None:
    registry = ExecutionRuntimeRegistry()
    registry.register(
        runtime_id="rt-1",
        session=_FakeSession("a"),  # type: ignore[arg-type]
        thread_id="thr-1",
        job_id="job-1",
    )
    registry.register(
        runtime_id="rt-2",
        session=_FakeSession("b"),  # type: ignore[arg-type]
        thread_id="thr-2",
        job_id="job-2",
    )
    assert set(registry.active_runtime_ids()) == {"rt-1", "rt-2"}

    registry.release("rt-1")
    assert set(registry.active_runtime_ids()) == {"rt-2"}
