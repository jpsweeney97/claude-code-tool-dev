"""Shared test fixtures for context-metrics plugin tests."""

from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES_DIR


@pytest.fixture
def normal_session(fixtures_dir: Path) -> Path:
    return fixtures_dir / "normal_session.jsonl"


@pytest.fixture
def compaction_session(fixtures_dir: Path) -> Path:
    return fixtures_dir / "compaction_session.jsonl"


@pytest.fixture
def near_boundary(fixtures_dir: Path) -> Path:
    return fixtures_dir / "near_boundary.jsonl"


@pytest.fixture
def malformed_session(fixtures_dir: Path) -> Path:
    return fixtures_dir / "malformed.jsonl"


@pytest.fixture
def empty_session(fixtures_dir: Path) -> Path:
    return fixtures_dir / "empty.jsonl"
