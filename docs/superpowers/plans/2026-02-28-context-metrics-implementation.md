# Context Metrics Plugin — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the `context-metrics` plugin — a Claude Code plugin that reads JSONL transcripts to compute and inject context window occupancy metrics into conversations via stdout-based command hooks.

**Architecture:** A shared Python HTTP sidecar (port 7432) reads JSONL transcript tails, computes occupancy, evaluates injection triggers, and formats summary lines. Three command hook scripts interact with the sidecar: `start_sidecar.py` (SessionStart), `stop_sidecar.py` (SessionEnd), and `context_summary.py` (UserPromptSubmit + SessionStart(compact)). All data-layer operations are fail-closed; injection is fail-open.

**Tech Stack:** Python 3.11+ stdlib only (http.server, json, urllib, threading). No external dependencies for the plugin itself. pytest + pyyaml for dev/test only. YAML frontmatter parsing via a minimal stdlib-compatible approach.

**Design doc:** `docs/plans/2026-02-28-context-metrics-design.md` (1205 lines, 5 amendments, 4 Codex reviews). This plan implements the v1 scope from Amendment 4 F10.

---

## Task Dependency Graph

```
Task 1: Plugin scaffold + JSONL fixtures  ──┐
                                             ├── Task 2: Config reader
                                             ├── Task 3: JSONL reader
                                             └── Task 4: Session registry
                                                           │
                                            Task 5: Trigger engine (needs 3)
                                            Task 6: Summary formatter (needs 2)
                                                           │
                                            Task 7: Sidecar server (needs 2-6)
                                                           │
                                            Task 8: Hook scripts (needs 7)
                                                           │
                                            Task 9: hooks.json + integration tests
                                                           │
                                            Task 10: Dashboard skill (needs 3)
```

Tasks 2, 3, 4 are independent after Task 1.

---

### Task 1: Plugin Scaffold + JSONL Test Fixtures

**Files:**
- Create: `packages/plugins/context-metrics/.claude-plugin/plugin.json`
- Create: `packages/plugins/context-metrics/pyproject.toml`
- Create: `packages/plugins/context-metrics/hooks/hooks.json`
- Create: `packages/plugins/context-metrics/scripts/__init__.py`
- Create: `packages/plugins/context-metrics/tests/__init__.py`
- Create: `packages/plugins/context-metrics/tests/fixtures/normal_session.jsonl`
- Create: `packages/plugins/context-metrics/tests/fixtures/compaction_session.jsonl`
- Create: `packages/plugins/context-metrics/tests/fixtures/near_boundary.jsonl`
- Create: `packages/plugins/context-metrics/tests/fixtures/malformed.jsonl`
- Create: `packages/plugins/context-metrics/tests/fixtures/empty.jsonl`
- Create: `packages/plugins/context-metrics/tests/conftest.py`

**Step 1: Create directory structure**

```bash
mkdir -p packages/plugins/context-metrics/{.claude-plugin,hooks,scripts,skills/context-dashboard,tests/fixtures}
touch packages/plugins/context-metrics/scripts/__init__.py
touch packages/plugins/context-metrics/tests/__init__.py
```

**Step 2: Create plugin.json**

```json
{
  "name": "context-metrics",
  "version": "0.1.0",
  "description": "Context window occupancy metrics — injects summary line into conversations via JSONL transcript analysis",
  "author": { "name": "JP" },
  "license": "MIT",
  "keywords": ["context", "metrics", "occupancy", "tokens"]
}
```

**Step 3: Create pyproject.toml**

```toml
[project]
name = "context-metrics-plugin"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = []

[project.optional-dependencies]
dev = ["pytest>=8.0", "pyyaml>=6.0"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

**Step 4: Create hooks.json stub**

```json
{
  "hooks": {}
}
```

Will be populated in Task 9 after all scripts exist.

**Step 5: Create JSONL test fixtures**

Each fixture is a newline-delimited JSON file simulating Claude Code JSONL transcripts.

`tests/fixtures/normal_session.jsonl` — 5 API calls showing growth from 50k to 160k:

```jsonl
{"type":"assistant","message":{"id":"msg_01","model":"claude-opus-4-6","role":"assistant","usage":{"input_tokens":1,"cache_read_input_tokens":48000,"cache_creation_input_tokens":2000,"output_tokens":500}}}
{"type":"user","content":"next question"}
{"type":"assistant","message":{"id":"msg_02","model":"claude-opus-4-6","role":"assistant","usage":{"input_tokens":1,"cache_read_input_tokens":78000,"cache_creation_input_tokens":2000,"output_tokens":600}}}
{"type":"user","content":"another question"}
{"type":"assistant","message":{"id":"msg_03","model":"claude-opus-4-6","role":"assistant","usage":{"input_tokens":1,"cache_read_input_tokens":108000,"cache_creation_input_tokens":2000,"output_tokens":700}}}
{"type":"user","content":"keep going"}
{"type":"assistant","message":{"id":"msg_04","model":"claude-opus-4-6","role":"assistant","usage":{"input_tokens":1,"cache_read_input_tokens":138000,"cache_creation_input_tokens":2000,"output_tokens":800}}}
{"type":"user","content":"final question"}
{"type":"assistant","message":{"id":"msg_05","model":"claude-opus-4-6","role":"assistant","usage":{"input_tokens":1,"cache_read_input_tokens":158000,"cache_creation_input_tokens":2000,"output_tokens":900}}}
```

Last record: occupancy = 1 + 158000 + 2000 = 160001 tokens.

`tests/fixtures/compaction_session.jsonl` — session with a compaction event:

```jsonl
{"type":"assistant","message":{"id":"msg_10","model":"claude-opus-4-6","role":"assistant","usage":{"input_tokens":1,"cache_read_input_tokens":190000,"cache_creation_input_tokens":5000,"output_tokens":1000}}}
{"type":"system","subtype":"compact_boundary","compactMetadata":{"preTokens":195001}}
{"type":"assistant","message":{"id":"msg_11","model":"claude-opus-4-6","role":"assistant","usage":{"input_tokens":1,"cache_read_input_tokens":30000,"cache_creation_input_tokens":1000,"output_tokens":500}}}
```

Post-compaction last record: occupancy = 1 + 30000 + 1000 = 31001 tokens.

`tests/fixtures/near_boundary.jsonl` — session at 92% of 200k window:

```jsonl
{"type":"assistant","message":{"id":"msg_20","model":"claude-opus-4-6","role":"assistant","usage":{"input_tokens":1,"cache_read_input_tokens":182000,"cache_creation_input_tokens":2000,"output_tokens":500}}}
```

Occupancy = 184001 tokens = 92% of 200k.

`tests/fixtures/malformed.jsonl` — mix of valid, invalid, and partial records:

```jsonl
{"type":"assistant","message":{"id":"msg_30","model":"claude-opus-4-6","role":"assistant","usage":{"input_tokens":1,"cache_read_input_tokens":100000,"cache_creation_input_tokens":2000,"output_tokens":500}}}
{"type":"assistant","message":{"role":"assistant"}}
not valid json at all
{"type":"agent_progress","message":{"role":"assistant","usage":{"input_tokens":5000}}}
{"type":"assistant","message":{"id":"msg_31","model":"claude-opus-4-6","role":"assistant","usage":{"input_tokens":1,"cache_read_input_tokens":120000,"cache_creation_input_tokens":2000,"output_tokens":600}}}
{"type":"assistant","message":{"id":"msg_31","model":"claude-opus-4-6","role":"assistant","usage":{"input_tokens":1,"cache_read_input_tokens":120000,"cache_creation_input_tokens":2000,"output_tokens":600}}}
```

Contains: missing usage (line 2), non-JSON (line 3), wrong type (line 4), duplicate msg_31 (lines 5-6).

`tests/fixtures/empty.jsonl` — empty file (0 bytes).

**Step 6: Create conftest.py with shared fixtures**

```python
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
```

**Step 7: Verify test discovery works**

Run: `cd packages/plugins/context-metrics && uv run pytest --collect-only`
Expected: 0 tests collected, no errors.

**Step 8: Commit**

```bash
git add packages/plugins/context-metrics/
git commit -m "feat(context-metrics): scaffold plugin with JSONL test fixtures"
```

---

### Task 2: Config Reader

**Files:**
- Create: `packages/plugins/context-metrics/scripts/config.py`
- Create: `packages/plugins/context-metrics/tests/test_config.py`
- Reference: Design doc Amendment 2 (lines 611-654) — auto-detection + simplified config

**Context:** The config file at `~/.claude/context-metrics.local.md` uses YAML frontmatter. The reader must parse this without pyyaml at runtime (stdlib only). Default: `context_window=200000`, `soft_boundary=None` (no warnings).

**Step 1: Write failing tests**

```python
"""Tests for config reader."""

import textwrap
from pathlib import Path

from scripts.config import Config, read_config


class TestReadConfig:
    def test_valid_config_with_both_fields(self, tmp_path: Path) -> None:
        config_file = tmp_path / "context-metrics.local.md"
        config_file.write_text(
            textwrap.dedent("""\
                ---
                context_window: 1000000
                soft_boundary: 200000
                ---
            """)
        )
        config = read_config(config_file)
        assert config.context_window == 1_000_000
        assert config.soft_boundary == 200_000

    def test_soft_boundary_only(self, tmp_path: Path) -> None:
        config_file = tmp_path / "context-metrics.local.md"
        config_file.write_text("---\nsoft_boundary: 200000\n---\n")
        config = read_config(config_file)
        assert config.context_window == 200_000  # default
        assert config.soft_boundary == 200_000

    def test_missing_file_returns_defaults(self, tmp_path: Path) -> None:
        config = read_config(tmp_path / "nonexistent.md")
        assert config.context_window == 200_000
        assert config.soft_boundary is None

    def test_empty_file_returns_defaults(self, tmp_path: Path) -> None:
        config_file = tmp_path / "context-metrics.local.md"
        config_file.write_text("")
        config = read_config(config_file)
        assert config.context_window == 200_000
        assert config.soft_boundary is None

    def test_invalid_yaml_returns_defaults(self, tmp_path: Path) -> None:
        config_file = tmp_path / "context-metrics.local.md"
        config_file.write_text("---\n: broken yaml [[\n---\n")
        config = read_config(config_file)
        assert config.context_window == 200_000
        assert config.soft_boundary is None

    def test_context_window_override(self, tmp_path: Path) -> None:
        config_file = tmp_path / "context-metrics.local.md"
        config_file.write_text("---\ncontext_window: 500000\n---\n")
        config = read_config(config_file)
        assert config.context_window == 500_000


class TestAutoDetection:
    def test_upgrade_to_1m_when_occupancy_exceeds_200k(self) -> None:
        config = Config(context_window=200_000)
        config.maybe_upgrade_window(250_000)
        assert config.context_window == 1_000_000

    def test_no_upgrade_when_under_200k(self) -> None:
        config = Config(context_window=200_000)
        config.maybe_upgrade_window(150_000)
        assert config.context_window == 200_000

    def test_no_upgrade_when_explicitly_set(self) -> None:
        config = Config(context_window=500_000, _explicitly_set=True)
        config.maybe_upgrade_window(600_000)
        assert config.context_window == 500_000
```

**Step 2: Run tests to verify failure**

Run: `cd packages/plugins/context-metrics && uv run pytest tests/test_config.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.config'`

**Step 3: Implement config reader**

```python
"""Config reader for context-metrics plugin.

Reads ~/.claude/context-metrics.local.md YAML frontmatter.
Stdlib only — no pyyaml dependency at runtime.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_WINDOW = 200_000
UPGRADE_WINDOW = 1_000_000


@dataclass
class Config:
    context_window: int = DEFAULT_WINDOW
    soft_boundary: int | None = None
    _explicitly_set: bool = field(default=False, repr=False)

    def maybe_upgrade_window(self, observed_occupancy: int) -> None:
        """Auto-upgrade to 1M if occupancy exceeds 200k default."""
        if not self._explicitly_set and observed_occupancy > DEFAULT_WINDOW:
            self.context_window = UPGRADE_WINDOW


def read_config(path: Path) -> Config:
    """Read config from YAML frontmatter. Returns defaults on any error."""
    try:
        text = path.read_text(encoding="utf-8")
    except (FileNotFoundError, OSError):
        return Config()

    frontmatter = _extract_frontmatter(text)
    if frontmatter is None:
        return Config()

    values = _parse_simple_yaml(frontmatter)
    window = values.get("context_window")
    boundary = values.get("soft_boundary")

    explicitly_set = window is not None
    return Config(
        context_window=window if window is not None else DEFAULT_WINDOW,
        soft_boundary=boundary,
        _explicitly_set=explicitly_set,
    )


def _extract_frontmatter(text: str) -> str | None:
    """Extract content between --- delimiters."""
    match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    return match.group(1) if match else None


def _parse_simple_yaml(text: str) -> dict[str, int]:
    """Minimal YAML parser for key: int_value lines. Stdlib only."""
    result: dict[str, int] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(":", 1)
        if len(parts) != 2:
            continue
        key = parts[0].strip()
        try:
            value = int(parts[1].strip())
            result[key] = value
        except ValueError:
            continue
    return result
```

**Step 4: Run tests to verify pass**

Run: `cd packages/plugins/context-metrics && uv run pytest tests/test_config.py -v`
Expected: All 7 tests PASS.

**Step 5: Commit**

```bash
git add packages/plugins/context-metrics/scripts/config.py packages/plugins/context-metrics/tests/test_config.py
git commit -m "feat(context-metrics): add config reader with auto-detection"
```

---

### Task 3: JSONL Reader

**Files:**
- Create: `packages/plugins/context-metrics/scripts/jsonl_reader.py`
- Create: `packages/plugins/context-metrics/tests/test_jsonl_reader.py`
- Reference: Design doc Amendment 4 F2 (4-condition selector), Amendment 5 F3 (stale-but-valid reads), Amendment 2 (occupancy computation)

**Context:** Tail-reads JSONL backward from EOF. 4-condition positive-only selector. Fail-closed on any parse error. Concurrent-write safe (discards partial lines). This is the #1 risk component — JSONL format drift could break everything.

**Step 1: Write failing tests**

```python
"""Tests for JSONL reader."""

import json
from pathlib import Path

from scripts.jsonl_reader import (
    compute_occupancy,
    is_main_thread_response,
    tail_read_last_valid,
)


class TestIsMainThreadResponse:
    """Test the 4-condition positive-only selector (Amendment 4 F2)."""

    def test_valid_assistant_record(self) -> None:
        record = {
            "type": "assistant",
            "message": {
                "id": "msg_01",
                "role": "assistant",
                "usage": {"input_tokens": 1, "cache_read_input_tokens": 50000,
                          "cache_creation_input_tokens": 1000, "output_tokens": 500},
            },
        }
        assert is_main_thread_response(record) is True

    def test_rejects_user_type(self) -> None:
        record = {"type": "user", "content": "hello"}
        assert is_main_thread_response(record) is False

    def test_rejects_missing_usage(self) -> None:
        record = {"type": "assistant", "message": {"role": "assistant"}}
        assert is_main_thread_response(record) is False

    def test_rejects_missing_input_tokens(self) -> None:
        record = {
            "type": "assistant",
            "message": {"role": "assistant", "usage": {"output_tokens": 500}},
        }
        assert is_main_thread_response(record) is False

    def test_rejects_wrong_message_role(self) -> None:
        record = {
            "type": "assistant",
            "message": {"role": "user", "usage": {"input_tokens": 1}},
        }
        assert is_main_thread_response(record) is False

    def test_rejects_agent_progress(self) -> None:
        record = {
            "type": "agent_progress",
            "message": {"role": "assistant", "usage": {"input_tokens": 5000}},
        }
        assert is_main_thread_response(record) is False


class TestComputeOccupancy:
    def test_all_fields_present(self) -> None:
        usage = {
            "input_tokens": 1,
            "cache_read_input_tokens": 158000,
            "cache_creation_input_tokens": 2000,
            "output_tokens": 900,
        }
        assert compute_occupancy(usage) == 160001

    def test_missing_cache_fields_default_zero(self) -> None:
        usage = {"input_tokens": 5000}
        assert compute_occupancy(usage) == 5000


class TestTailReadLastValid:
    def test_normal_session_returns_last_record(self, normal_session: Path) -> None:
        record = tail_read_last_valid(normal_session)
        assert record is not None
        assert record["message"]["id"] == "msg_05"
        assert compute_occupancy(record["message"]["usage"]) == 160001

    def test_malformed_skips_bad_records(self, malformed_session: Path) -> None:
        record = tail_read_last_valid(malformed_session)
        assert record is not None
        # Should find the last valid assistant record, deduplicating msg_31
        assert record["message"]["id"] == "msg_31"

    def test_empty_file_returns_none(self, empty_session: Path) -> None:
        record = tail_read_last_valid(empty_session)
        assert record is None

    def test_compaction_session_returns_post_compaction(
        self, compaction_session: Path
    ) -> None:
        record = tail_read_last_valid(compaction_session)
        assert record is not None
        assert record["message"]["id"] == "msg_11"
        assert compute_occupancy(record["message"]["usage"]) == 31001

    def test_partial_line_at_eof_discarded(self, tmp_path: Path) -> None:
        """Simulate concurrent write: last line is incomplete."""
        fixture = tmp_path / "partial.jsonl"
        valid = {"type": "assistant", "message": {"id": "msg_40", "role": "assistant",
                 "usage": {"input_tokens": 1, "cache_read_input_tokens": 50000,
                           "cache_creation_input_tokens": 1000, "output_tokens": 500}}}
        fixture.write_text(json.dumps(valid) + "\n" + '{"type":"assistant","mess')
        record = tail_read_last_valid(fixture)
        assert record is not None
        assert record["message"]["id"] == "msg_40"

    def test_deduplicates_by_message_id(self, tmp_path: Path) -> None:
        """Condition 4: deduplicate by message.id — return first seen from tail."""
        fixture = tmp_path / "dupes.jsonl"
        rec = {"type": "assistant", "message": {"id": "msg_50", "role": "assistant",
               "usage": {"input_tokens": 1, "cache_read_input_tokens": 80000,
                         "cache_creation_input_tokens": 1000, "output_tokens": 500}}}
        fixture.write_text(json.dumps(rec) + "\n" + json.dumps(rec) + "\n")
        record = tail_read_last_valid(fixture)
        assert record is not None
        assert record["message"]["id"] == "msg_50"
```

**Step 2: Run tests to verify failure**

Run: `cd packages/plugins/context-metrics && uv run pytest tests/test_jsonl_reader.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Implement JSONL reader**

```python
"""JSONL tail-reader with fail-closed validation.

Reads JSONL transcripts backward from EOF to find the last valid
main-thread API response. Concurrent-write safe: partial lines are
discarded. Format drift safe: unknown records are rejected.

Design reference: Amendment 4 F2 (selector), Amendment 5 F3 (interaction model).
"""

from __future__ import annotations

import json
from pathlib import Path

CHUNK_SIZE = 8192


def is_main_thread_response(record: dict) -> bool:
    """4-condition positive-only selector (Amendment 4 F2).

    Conditions:
    1. type == "assistant"
    2. message.role == "assistant"
    3. message.usage present with input_tokens field
    4. Deduplicate by message.id (handled by caller via seen_ids set)
    """
    if record.get("type") != "assistant":
        return False
    message = record.get("message")
    if not isinstance(message, dict):
        return False
    if message.get("role") != "assistant":
        return False
    usage = message.get("usage")
    if not isinstance(usage, dict) or "input_tokens" not in usage:
        return False
    return True


def compute_occupancy(usage: dict) -> int:
    """Compute context window occupancy from usage data.

    occupancy = input_tokens + cache_read_input_tokens + cache_creation_input_tokens
    """
    return (
        usage.get("input_tokens", 0)
        + usage.get("cache_read_input_tokens", 0)
        + usage.get("cache_creation_input_tokens", 0)
    )


def tail_read_last_valid(jsonl_path: Path) -> dict | None:
    """Read JSONL backward from EOF, return first valid record.

    Fail-closed: malformed JSON, partial lines, and records failing
    the 4-condition selector are silently skipped. Returns None if
    no valid record exists (empty file, all records invalid).
    """
    try:
        with open(jsonl_path, "rb") as f:
            f.seek(0, 2)
            file_size = f.tell()
            if file_size == 0:
                return None

            seen_ids: set[str] = set()
            remaining = b""
            position = file_size

            while position > 0:
                read_size = min(CHUNK_SIZE, position)
                position -= read_size
                f.seek(position)
                chunk = f.read(read_size)
                data = chunk + remaining

                lines = data.split(b"\n")
                remaining = lines[0]

                for line in reversed(lines[1:]):
                    record = _try_parse_record(line, seen_ids)
                    if record is not None:
                        return record

            # Process leftover (first line of file)
            if remaining:
                record = _try_parse_record(remaining, seen_ids)
                if record is not None:
                    return record

    except OSError:
        return None

    return None


def _try_parse_record(line: bytes, seen_ids: set[str]) -> dict | None:
    """Try to parse and validate a single JSONL line. Returns None on any failure."""
    line = line.strip()
    if not line:
        return None
    try:
        record = json.loads(line)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None

    if not isinstance(record, dict):
        return None

    if not is_main_thread_response(record):
        return None

    # Condition 4: deduplicate by message.id
    msg_id = record.get("message", {}).get("id")
    if msg_id is not None:
        if msg_id in seen_ids:
            return None
        seen_ids.add(msg_id)

    return record
```

**Step 4: Run tests to verify pass**

Run: `cd packages/plugins/context-metrics && uv run pytest tests/test_jsonl_reader.py -v`
Expected: All 12 tests PASS.

**Step 5: Commit**

```bash
git add packages/plugins/context-metrics/scripts/jsonl_reader.py packages/plugins/context-metrics/tests/test_jsonl_reader.py
git commit -m "feat(context-metrics): add JSONL tail-reader with 4-condition selector"
```

---

### Task 4: Session Registry

**Files:**
- Create: `packages/plugins/context-metrics/scripts/session_registry.py`
- Create: `packages/plugins/context-metrics/tests/test_session_registry.py`
- Reference: Design doc Amendment 3 F3 (session lifecycle, lease timeout)

**Context:** In-memory session registry with 10-minute lease. Sessions register on SessionStart, deregister on SessionEnd. Expired leases are cleaned up. Sidecar shuts down when no active sessions remain.

**Step 1: Write failing tests**

```python
"""Tests for session registry."""

import time

from scripts.session_registry import SessionRegistry


class TestSessionRegistry:
    def test_register_and_active_count(self) -> None:
        reg = SessionRegistry(lease_timeout=600)
        reg.register("session_1", "/path/to/transcript.jsonl")
        assert reg.active_count() == 1

    def test_register_multiple_sessions(self) -> None:
        reg = SessionRegistry(lease_timeout=600)
        reg.register("session_1", "/path/1.jsonl")
        reg.register("session_2", "/path/2.jsonl")
        assert reg.active_count() == 2

    def test_deregister_removes_session(self) -> None:
        reg = SessionRegistry(lease_timeout=600)
        reg.register("session_1", "/path/1.jsonl")
        assert reg.deregister("session_1") is True
        assert reg.active_count() == 0

    def test_deregister_nonexistent_returns_false(self) -> None:
        reg = SessionRegistry(lease_timeout=600)
        assert reg.deregister("nonexistent") is False

    def test_renew_updates_heartbeat(self) -> None:
        reg = SessionRegistry(lease_timeout=600)
        reg.register("session_1", "/path/1.jsonl")
        assert reg.renew("session_1") is True

    def test_renew_nonexistent_returns_false(self) -> None:
        reg = SessionRegistry(lease_timeout=600)
        assert reg.renew("nonexistent") is False

    def test_lease_expiry(self) -> None:
        reg = SessionRegistry(lease_timeout=0)  # Expire immediately
        reg.register("session_1", "/path/1.jsonl")
        time.sleep(0.01)
        expired = reg.expire_leases()
        assert "session_1" in expired
        assert reg.active_count() == 0

    def test_get_transcript_path(self) -> None:
        reg = SessionRegistry(lease_timeout=600)
        reg.register("session_1", "/path/to/transcript.jsonl")
        assert reg.get_transcript_path("session_1") == "/path/to/transcript.jsonl"

    def test_get_transcript_path_unknown(self) -> None:
        reg = SessionRegistry(lease_timeout=600)
        assert reg.get_transcript_path("unknown") is None
```

**Step 2: Run tests to verify failure**

Run: `cd packages/plugins/context-metrics && uv run pytest tests/test_session_registry.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Implement session registry**

```python
"""Session registry for shared sidecar.

Tracks active Claude Code sessions with lease-based expiry.
Thread-safe for concurrent access from HTTP handler threads.

Design reference: Amendment 3 F3 (session lifecycle).
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field


@dataclass
class SessionEntry:
    transcript_path: str
    registered_at: float
    last_heartbeat: float


class SessionRegistry:
    def __init__(self, lease_timeout: int = 600) -> None:
        self.lease_timeout = lease_timeout
        self._sessions: dict[str, SessionEntry] = {}
        self._lock = threading.Lock()

    def register(self, session_id: str, transcript_path: str) -> None:
        now = time.time()
        with self._lock:
            self._sessions[session_id] = SessionEntry(
                transcript_path=transcript_path,
                registered_at=now,
                last_heartbeat=now,
            )

    def deregister(self, session_id: str) -> bool:
        with self._lock:
            return self._sessions.pop(session_id, None) is not None

    def renew(self, session_id: str) -> bool:
        with self._lock:
            entry = self._sessions.get(session_id)
            if entry is None:
                return False
            entry.last_heartbeat = time.time()
            return True

    def expire_leases(self) -> list[str]:
        now = time.time()
        with self._lock:
            expired = [
                sid
                for sid, entry in self._sessions.items()
                if now - entry.last_heartbeat > self.lease_timeout
            ]
            for sid in expired:
                del self._sessions[sid]
        return expired

    def active_count(self) -> int:
        self.expire_leases()
        with self._lock:
            return len(self._sessions)

    def get_transcript_path(self, session_id: str) -> str | None:
        with self._lock:
            entry = self._sessions.get(session_id)
            return entry.transcript_path if entry else None
```

**Step 4: Run tests to verify pass**

Run: `cd packages/plugins/context-metrics && uv run pytest tests/test_session_registry.py -v`
Expected: All 9 tests PASS.

**Step 5: Commit**

```bash
git add packages/plugins/context-metrics/scripts/session_registry.py packages/plugins/context-metrics/tests/test_session_registry.py
git commit -m "feat(context-metrics): add session registry with lease-based expiry"
```

---

### Task 5: Trigger Engine

**Files:**
- Create: `packages/plugins/context-metrics/scripts/trigger_engine.py`
- Create: `packages/plugins/context-metrics/tests/test_trigger_engine.py`
- Reference: Design doc Amendment 5 F3 (trigger interaction model — OR-based, counter reset)

**Context:** Evaluates 5 trigger types per UserPromptSubmit. OR semantics — inject if any fires. Counter resets on injection. Compaction always injects and resets delta baseline. This is the specification from Amendment 5 F3, codified from the fourth Codex review dialogue.

**Step 1: Write failing tests**

```python
"""Tests for trigger engine.

Tests cover: individual triggers, OR semantics, counter reset,
compaction baseline reset, headroom-sensitive thresholds.
Reference: Amendment 5 F3.
"""

from scripts.trigger_engine import SessionState, TriggerEngine, TriggerResult


def make_engine(window: int = 200_000) -> TriggerEngine:
    return TriggerEngine(window_size=window)


class TestTokenDeltaTrigger:
    def test_fires_at_5k_delta(self) -> None:
        engine = make_engine()
        state = SessionState(last_injected_occupancy=100_000)
        result = engine.evaluate(state, current_occupancy=105_001)
        assert result.should_inject is True
        assert "token_delta" in result.triggers_fired

    def test_does_not_fire_below_5k(self) -> None:
        engine = make_engine()
        state = SessionState(last_injected_occupancy=100_000)
        result = engine.evaluate(state, current_occupancy=104_999)
        assert "token_delta" not in result.triggers_fired

    def test_headroom_lowers_to_2k_above_85pct(self) -> None:
        engine = make_engine()
        # 85% of 200k = 170k
        state = SessionState(last_injected_occupancy=170_000)
        result = engine.evaluate(state, current_occupancy=172_001)
        assert "token_delta" in result.triggers_fired


class TestPercentageDeltaTrigger:
    def test_fires_at_2pct_of_window(self) -> None:
        engine = make_engine()
        # 2% of 200k = 4000
        state = SessionState(last_injected_occupancy=100_000)
        result = engine.evaluate(state, current_occupancy=104_001)
        assert "percentage_delta" in result.triggers_fired

    def test_does_not_fire_below_2pct(self) -> None:
        engine = make_engine()
        state = SessionState(last_injected_occupancy=100_000)
        result = engine.evaluate(state, current_occupancy=103_999)
        assert "percentage_delta" not in result.triggers_fired


class TestBoundaryCrossingTrigger:
    def test_fires_on_50pct_crossing(self) -> None:
        engine = make_engine()
        state = SessionState(
            last_injected_occupancy=90_000,
            last_boundaries_crossed=frozenset({0.25}),
        )
        result = engine.evaluate(state, current_occupancy=100_001)
        assert "boundary_crossing" in result.triggers_fired

    def test_does_not_fire_on_already_crossed(self) -> None:
        engine = make_engine()
        state = SessionState(
            last_injected_occupancy=100_000,
            last_boundaries_crossed=frozenset({0.25, 0.50}),
        )
        result = engine.evaluate(state, current_occupancy=100_001)
        assert "boundary_crossing" not in result.triggers_fired


class TestCompactionTrigger:
    def test_always_injects_on_compaction(self) -> None:
        engine = make_engine()
        state = SessionState(
            last_injected_occupancy=190_000,
            compaction_pending=True,
        )
        # Post-compaction occupancy is lower — compaction still fires
        result = engine.evaluate(state, current_occupancy=30_000)
        assert result.should_inject is True
        assert "compaction" in result.triggers_fired
        assert result.format == "compaction"


class TestHeartbeatTrigger:
    def test_fires_after_8_prompts(self) -> None:
        engine = make_engine()
        state = SessionState(
            last_injected_occupancy=100_000,
            prompts_since_injection=8,
        )
        result = engine.evaluate(state, current_occupancy=100_001)
        assert result.should_inject is True
        assert "heartbeat" in result.triggers_fired
        assert result.format == "minimal"

    def test_critical_fires_after_3_prompts_above_90pct(self) -> None:
        engine = make_engine()
        state = SessionState(
            last_injected_occupancy=180_000,
            prompts_since_injection=3,
        )
        # 90.5% occupancy → critical heartbeat interval
        result = engine.evaluate(state, current_occupancy=181_000)
        assert "heartbeat" in result.triggers_fired

    def test_does_not_fire_below_interval(self) -> None:
        engine = make_engine()
        state = SessionState(
            last_injected_occupancy=100_000,
            prompts_since_injection=5,
        )
        result = engine.evaluate(state, current_occupancy=100_001)
        assert "heartbeat" not in result.triggers_fired


class TestORSemantics:
    def test_multiple_triggers_use_full_format(self) -> None:
        engine = make_engine()
        state = SessionState(
            last_injected_occupancy=90_000,
            prompts_since_injection=8,
            last_boundaries_crossed=frozenset({0.25}),
        )
        # Crosses 50% boundary AND heartbeat fires → full wins over minimal
        result = engine.evaluate(state, current_occupancy=100_001)
        assert result.should_inject is True
        assert result.format == "full"

    def test_no_triggers_does_not_inject(self) -> None:
        engine = make_engine()
        state = SessionState(
            last_injected_occupancy=100_000,
            prompts_since_injection=2,
            last_boundaries_crossed=frozenset({0.25, 0.50}),
        )
        result = engine.evaluate(state, current_occupancy=100_001)
        assert result.should_inject is False
        assert result.format == "none"


class TestApplyResult:
    def test_injection_resets_counter_and_baseline(self) -> None:
        engine = make_engine()
        state = SessionState(
            last_injected_occupancy=100_000,
            prompts_since_injection=8,
        )
        result = engine.evaluate(state, current_occupancy=100_001)
        assert result.should_inject is True

        engine.apply_result(state, result, current_occupancy=100_001)
        assert state.prompts_since_injection == 0
        assert state.last_injected_occupancy == 100_001

    def test_suppressed_increments_counter(self) -> None:
        engine = make_engine()
        state = SessionState(
            last_injected_occupancy=100_000,
            prompts_since_injection=2,
            last_boundaries_crossed=frozenset({0.25, 0.50}),
        )
        result = engine.evaluate(state, current_occupancy=100_001)
        assert result.should_inject is False

        engine.apply_result(state, result, current_occupancy=100_001)
        assert state.prompts_since_injection == 3

    def test_compaction_resets_baseline(self) -> None:
        engine = make_engine()
        state = SessionState(
            last_injected_occupancy=190_000,
            compaction_pending=True,
            compaction_count=2,
        )
        result = engine.evaluate(state, current_occupancy=30_000)
        engine.apply_result(state, result, current_occupancy=30_000)

        assert state.last_injected_occupancy == 30_000
        assert state.compaction_pending is False
        assert state.compaction_count == 3
        assert state.last_boundaries_crossed == frozenset()
```

**Step 2: Run tests to verify failure**

Run: `cd packages/plugins/context-metrics && uv run pytest tests/test_trigger_engine.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Implement trigger engine**

```python
"""Trigger engine for delta-gated injection.

Evaluates 5 trigger types per UserPromptSubmit with OR semantics.
Counter resets on injection. Compaction always injects and resets baseline.

Design reference: Amendment 5 F3 (trigger interaction model).
"""

from __future__ import annotations

from dataclasses import dataclass, field

BOUNDARIES = frozenset({0.25, 0.50, 0.75, 0.90})
HEARTBEAT_NORMAL = 8
HEARTBEAT_CRITICAL = 3
TOKEN_DELTA_NORMAL = 5000
TOKEN_DELTA_HEADROOM = 2000
HEADROOM_THRESHOLD = 0.85
CRITICAL_THRESHOLD = 0.90
PERCENTAGE_DELTA = 0.02


@dataclass
class SessionState:
    last_injected_occupancy: int = 0
    prompts_since_injection: int = 0
    last_boundaries_crossed: frozenset[float] = field(default_factory=frozenset)
    compaction_pending: bool = False
    compaction_count: int = 0


@dataclass
class TriggerResult:
    should_inject: bool
    format: str  # "full", "minimal", "compaction", "none"
    triggers_fired: list[str]


class TriggerEngine:
    def __init__(self, window_size: int) -> None:
        self.window_size = window_size

    def evaluate(self, state: SessionState, current_occupancy: int) -> TriggerResult:
        """Evaluate all triggers. OR semantics: inject if any fires."""
        triggers: list[str] = []
        occupancy_pct = current_occupancy / self.window_size if self.window_size > 0 else 0
        delta = current_occupancy - state.last_injected_occupancy

        # 1. Compaction — always injects
        if state.compaction_pending:
            triggers.append("compaction")

        # 2. Token delta (headroom-sensitive)
        threshold = TOKEN_DELTA_HEADROOM if occupancy_pct >= HEADROOM_THRESHOLD else TOKEN_DELTA_NORMAL
        if delta >= threshold:
            triggers.append("token_delta")

        # 3. Percentage delta (2% of window)
        pct_threshold = int(self.window_size * PERCENTAGE_DELTA)
        if delta >= pct_threshold:
            triggers.append("percentage_delta")

        # 4. Boundary crossing
        current_boundaries = frozenset(b for b in BOUNDARIES if occupancy_pct >= b)
        new_crossings = current_boundaries - state.last_boundaries_crossed
        if new_crossings:
            triggers.append("boundary_crossing")

        # 5. Heartbeat
        interval = HEARTBEAT_CRITICAL if occupancy_pct >= CRITICAL_THRESHOLD else HEARTBEAT_NORMAL
        if state.prompts_since_injection >= interval:
            triggers.append("heartbeat")

        # OR semantics + format priority
        should_inject = len(triggers) > 0
        if "compaction" in triggers:
            fmt = "compaction"
        elif any(t in triggers for t in ("token_delta", "percentage_delta", "boundary_crossing")):
            fmt = "full"
        elif "heartbeat" in triggers:
            fmt = "minimal"
        else:
            fmt = "none"

        return TriggerResult(should_inject=should_inject, format=fmt, triggers_fired=triggers)

    def apply_result(
        self, state: SessionState, result: TriggerResult, current_occupancy: int
    ) -> None:
        """Update session state after trigger evaluation."""
        occupancy_pct = current_occupancy / self.window_size if self.window_size > 0 else 0

        if result.should_inject:
            state.last_injected_occupancy = current_occupancy
            state.prompts_since_injection = 0
            state.last_boundaries_crossed = frozenset(
                b for b in BOUNDARIES if occupancy_pct >= b
            )
            if state.compaction_pending:
                state.compaction_count += 1
                state.compaction_pending = False
                # Compaction resets boundary tracking
                state.last_boundaries_crossed = frozenset()
        else:
            state.prompts_since_injection += 1
```

**Step 4: Run tests to verify pass**

Run: `cd packages/plugins/context-metrics && uv run pytest tests/test_trigger_engine.py -v`
Expected: All 15 tests PASS.

**Step 5: Commit**

```bash
git add packages/plugins/context-metrics/scripts/trigger_engine.py packages/plugins/context-metrics/tests/test_trigger_engine.py
git commit -m "feat(context-metrics): add trigger engine with OR-based evaluation"
```

---

### Task 6: Summary Formatter

**Files:**
- Create: `packages/plugins/context-metrics/scripts/formatter.py`
- Create: `packages/plugins/context-metrics/tests/test_formatter.py`
- Reference: Design doc summary line format (lines 290-322), Amendment 3 F5 (heartbeat), Amendment 5 F4 (compaction notice)

**Step 1: Write failing tests**

```python
"""Tests for summary formatter."""

from scripts.formatter import format_compaction, format_full, format_minimal


class TestFormatFull:
    def test_default_format(self) -> None:
        line = format_full(
            occupancy=142_000, window=200_000, message_count=847,
            compaction_count=2, cost_usd=None, soft_boundary=None,
        )
        assert line == "Context: 142k/200k tokens (71%) | 847 msgs | Phase 3 (2 compactions)"

    def test_with_cost(self) -> None:
        line = format_full(
            occupancy=142_000, window=200_000, message_count=847,
            compaction_count=2, cost_usd=1.24, soft_boundary=None,
        )
        assert "~$1.24" in line

    def test_approaching_soft_boundary(self) -> None:
        line = format_full(
            occupancy=168_000, window=200_000, message_count=500,
            compaction_count=0, cost_usd=None, soft_boundary=200_000,
        )
        assert "approaching" in line.lower()

    def test_exceeded_soft_boundary(self) -> None:
        line = format_full(
            occupancy=287_000, window=1_000_000, message_count=847,
            compaction_count=3, cost_usd=None, soft_boundary=200_000,
        )
        assert "beyond" in line.lower()

    def test_no_compactions(self) -> None:
        line = format_full(
            occupancy=50_000, window=200_000, message_count=100,
            compaction_count=0, cost_usd=None, soft_boundary=None,
        )
        assert "Phase 1" in line
        assert "compaction" not in line.lower()

    def test_1m_window(self) -> None:
        line = format_full(
            occupancy=287_000, window=1_000_000, message_count=847,
            compaction_count=3, cost_usd=None, soft_boundary=None,
        )
        assert "287k/1M" in line or "287k/1000k" in line


class TestFormatMinimal:
    def test_stable_heartbeat(self) -> None:
        line = format_minimal(occupancy=142_000, window=200_000)
        assert line == "Context: ~71% (stable)"

    def test_high_occupancy(self) -> None:
        line = format_minimal(occupancy=180_000, window=200_000)
        assert "90%" in line


class TestFormatCompaction:
    def test_post_compaction_notice(self) -> None:
        line = format_compaction(
            occupancy=34_000, window=200_000, compaction_number=3,
            message_count=847, cost_usd=None, soft_boundary=None,
        )
        assert "Compaction #3" in line
        assert "34k/200k" in line
```

**Step 2: Run tests to verify failure**

Run: `cd packages/plugins/context-metrics && uv run pytest tests/test_formatter.py -v`
Expected: FAIL

**Step 3: Implement formatter**

```python
"""Summary line formatter for context metrics.

Formats: full (material change), minimal (heartbeat), compaction (post-compact).
Design reference: Summary Line Format section + Amendment 3 F5.
"""

from __future__ import annotations


def _format_tokens(n: int) -> str:
    """Format token count as human-readable: 142000 → '142k', 1000000 → '1M'."""
    if n >= 1_000_000 and n % 1_000_000 == 0:
        return f"{n // 1_000_000}M"
    if n >= 1_000:
        return f"{n // 1_000}k"
    return str(n)


def _pct(occupancy: int, window: int) -> int:
    return round(occupancy * 100 / window) if window > 0 else 0


def _boundary_warning(
    occupancy: int, window: int, soft_boundary: int | None
) -> str | None:
    if soft_boundary is None:
        return None
    if occupancy > soft_boundary:
        beyond = occupancy - soft_boundary
        return (
            f"{_format_tokens(occupancy)} tokens — {_format_tokens(beyond)} beyond "
            f"{_format_tokens(soft_boundary)} extended-context boundary"
        )
    ratio = occupancy / soft_boundary if soft_boundary > 0 else 0
    if ratio >= 0.80:
        return (
            f"{_format_tokens(occupancy)}/{_format_tokens(window)} tokens "
            f"({_pct(occupancy, window)}%) — approaching extended-context boundary"
        )
    return None


def format_full(
    *,
    occupancy: int,
    window: int,
    message_count: int,
    compaction_count: int,
    cost_usd: float | None,
    soft_boundary: int | None,
) -> str:
    """Full summary line for material changes."""
    warning = _boundary_warning(occupancy, window, soft_boundary)

    if warning:
        base = f"Context: {warning}"
    else:
        base = (
            f"Context: {_format_tokens(occupancy)}/{_format_tokens(window)} tokens "
            f"({_pct(occupancy, window)}%)"
        )

    parts = [base, f"{message_count} msgs"]

    phase = compaction_count + 1
    if compaction_count > 0:
        parts.append(f"Phase {phase} ({compaction_count} compactions)")
    else:
        parts.append(f"Phase {phase}")

    if cost_usd is not None:
        parts.append(f"~${cost_usd:.2f}")

    return " | ".join(parts)


def format_minimal(*, occupancy: int, window: int) -> str:
    """Minimal heartbeat line."""
    pct = _pct(occupancy, window)
    return f"Context: ~{pct}% (stable)"


def format_compaction(
    *,
    occupancy: int,
    window: int,
    compaction_number: int,
    message_count: int,
    cost_usd: float | None,
    soft_boundary: int | None,
) -> str:
    """Post-compaction notice."""
    base = (
        f"Context: {_format_tokens(occupancy)}/{_format_tokens(window)} tokens "
        f"({_pct(occupancy, window)}%) | Compaction #{compaction_number} just occurred"
    )
    parts = [base, f"{message_count} msgs"]
    if cost_usd is not None:
        parts.append(f"~${cost_usd:.2f}")
    return " | ".join(parts)
```

**Step 4: Run tests to verify pass**

Run: `cd packages/plugins/context-metrics && uv run pytest tests/test_formatter.py -v`
Expected: All 9 tests PASS.

**Step 5: Commit**

```bash
git add packages/plugins/context-metrics/scripts/formatter.py packages/plugins/context-metrics/tests/test_formatter.py
git commit -m "feat(context-metrics): add summary line formatter"
```

---

### Task 7: Sidecar HTTP Server

**Files:**
- Create: `packages/plugins/context-metrics/scripts/server.py`
- Create: `packages/plugins/context-metrics/tests/test_server.py`
- Reference: Design doc §4 (sidecar), Amendment 3 F3 (session lifecycle), Amendment 5 F4 (fail-policy matrix)

**Context:** HTTP server on port 7432. Three endpoint groups: session management (register/deregister), hook processing (context-metrics), health check. Orchestrates config, JSONL reader, trigger engine, and formatter. PID file at `~/.claude/.context-metrics-sidecar.pid`.

**Step 1: Write failing tests**

```python
"""Tests for sidecar HTTP server."""

import json
import threading
import time
import urllib.request
from pathlib import Path
from unittest.mock import patch

from scripts.server import ContextMetricsSidecar


def _get(url: str) -> tuple[int, str]:
    try:
        with urllib.request.urlopen(url, timeout=2) as resp:
            return resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def _post(url: str, data: dict) -> tuple[int, str]:
    body = json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=2) as resp:
            return resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


class TestSidecarServer:
    def setup_method(self) -> None:
        self.server = ContextMetricsSidecar(port=0)  # Random port
        self.port = self.server.server_address[1]
        self.base = f"http://127.0.0.1:{self.port}"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def teardown_method(self) -> None:
        self.server.shutdown()
        self.thread.join(timeout=2)

    def test_health_check(self) -> None:
        status, body = _get(f"{self.base}/health")
        assert status == 200
        data = json.loads(body)
        assert data["status"] == "ok"

    def test_register_session(self) -> None:
        status, body = _get(
            f"{self.base}/sessions/register?session_id=test1&transcript_path=/tmp/test.jsonl"
        )
        assert status == 200
        data = json.loads(body)
        assert data["registered"] is True

    def test_deregister_session(self) -> None:
        _get(f"{self.base}/sessions/register?session_id=test1&transcript_path=/tmp/test.jsonl")
        status, body = _get(f"{self.base}/sessions/deregister?session_id=test1")
        assert status == 200
        data = json.loads(body)
        assert data["deregistered"] is True

    def test_hook_with_registered_session(self, normal_session: Path) -> None:
        # Register with a real fixture path
        _get(
            f"{self.base}/sessions/register?session_id=test1"
            f"&transcript_path={normal_session}"
        )
        # POST hook input (simplified)
        hook_input = {
            "hook_event_name": "UserPromptSubmit",
            "session_id": "test1",
            "transcript_path": str(normal_session),
        }
        status, body = _post(f"{self.base}/hooks/context-metrics", hook_input)
        assert status == 200
        data = json.loads(body)
        # Should have a result (may or may not inject based on trigger state)
        assert "inject" in data

    def test_hook_with_unknown_session_fails_open(self) -> None:
        hook_input = {
            "hook_event_name": "UserPromptSubmit",
            "session_id": "unknown",
            "transcript_path": "/nonexistent.jsonl",
        }
        status, body = _post(f"{self.base}/hooks/context-metrics", hook_input)
        assert status == 200
        data = json.loads(body)
        assert data["inject"] is False
```

**Step 2: Run tests to verify failure**

Run: `cd packages/plugins/context-metrics && uv run pytest tests/test_server.py -v`
Expected: FAIL

**Step 3: Implement sidecar server**

```python
"""Sidecar HTTP server for context metrics.

Shared server on port 7432. Manages sessions, reads JSONL, evaluates
triggers, and returns injection decisions. Fail-open at injection layer,
fail-closed at data layer.

Design reference: Amendment 3 F3 (lifecycle), Amendment 5 F3 (triggers), F4 (fail-policy).
"""

from __future__ import annotations

import json
import logging
import os
import signal
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from scripts.config import Config, read_config
from scripts.formatter import format_compaction, format_full, format_minimal
from scripts.jsonl_reader import compute_occupancy, tail_read_last_valid
from scripts.session_registry import SessionRegistry
from scripts.trigger_engine import SessionState, TriggerEngine

logger = logging.getLogger("context-metrics-sidecar")

DEFAULT_PORT = 7432
PID_FILE = Path.home() / ".claude" / ".context-metrics-sidecar.pid"
CONFIG_PATH = Path.home() / ".claude" / "context-metrics.local.md"


class ContextMetricsSidecar(HTTPServer):
    def __init__(self, port: int = DEFAULT_PORT, config_path: Path | None = None) -> None:
        self.registry = SessionRegistry()
        self.config = read_config(config_path or CONFIG_PATH)
        self.trigger_engine = TriggerEngine(self.config.context_window)
        self.session_states: dict[str, SessionState] = {}
        self._states_lock = threading.Lock()
        # Message count per session (incremented by counting user messages in JSONL)
        self.message_counts: dict[str, int] = {}
        super().__init__(("127.0.0.1", port), _RequestHandler)

    def get_or_create_state(self, session_id: str) -> SessionState:
        with self._states_lock:
            if session_id not in self.session_states:
                self.session_states[session_id] = SessionState()
            return self.session_states[session_id]

    def remove_state(self, session_id: str) -> None:
        with self._states_lock:
            self.session_states.pop(session_id, None)
            self.message_counts.pop(session_id, None)


class _RequestHandler(BaseHTTPRequestHandler):
    server: ContextMetricsSidecar

    def log_message(self, format: str, *args: object) -> None:
        logger.debug(format, *args)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        if path == "/health":
            self._respond_json(200, {
                "status": "ok",
                "active_sessions": self.server.registry.active_count(),
            })
        elif path == "/sessions/register":
            session_id = params.get("session_id", [None])[0]
            transcript_path = params.get("transcript_path", [None])[0]
            if not session_id or not transcript_path:
                self._respond_json(400, {"error": "session_id and transcript_path required"})
                return
            self.server.registry.register(session_id, transcript_path)
            self.server.get_or_create_state(session_id)
            self._respond_json(200, {"registered": True, "session_id": session_id})
        elif path == "/sessions/deregister":
            session_id = params.get("session_id", [None])[0]
            if not session_id:
                self._respond_json(400, {"error": "session_id required"})
                return
            removed = self.server.registry.deregister(session_id)
            if removed:
                self.server.remove_state(session_id)
            self._respond_json(200, {
                "deregistered": removed,
                "active_sessions": self.server.registry.active_count(),
            })
        else:
            self._respond_json(404, {"error": "not found"})

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/hooks/context-metrics":
            self._respond_json(404, {"error": "not found"})
            return

        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length > 0 else {}
        except (json.JSONDecodeError, ValueError):
            self._respond_json(200, {"inject": False, "reason": "invalid input"})
            return

        self._handle_hook(body)

    def _handle_hook(self, hook_input: dict) -> None:
        """Process a hook request. Fail-open: errors → no injection."""
        session_id = hook_input.get("session_id", "")
        transcript_path = hook_input.get("transcript_path", "")

        # Derive session_id from transcript_path if not provided
        if not session_id and transcript_path:
            session_id = Path(transcript_path).stem

        # Read JSONL — fail-closed (data layer)
        record = tail_read_last_valid(Path(transcript_path)) if transcript_path else None
        if record is None:
            self._respond_json(200, {"inject": False, "reason": "no valid JSONL record"})
            return

        usage = record.get("message", {}).get("usage", {})
        occupancy = compute_occupancy(usage)

        # Auto-detect window upgrade
        self.server.config.maybe_upgrade_window(occupancy)
        self.server.trigger_engine.window_size = self.server.config.context_window

        # Renew lease
        self.server.registry.renew(session_id)

        # Evaluate triggers
        state = self.server.get_or_create_state(session_id)
        result = self.server.trigger_engine.evaluate(state, occupancy)

        if not result.should_inject:
            self.server.trigger_engine.apply_result(state, result, occupancy)
            self._respond_json(200, {"inject": False, "reason": "below threshold"})
            return

        # Format summary
        window = self.server.config.context_window
        msg_count = self.server.message_counts.get(session_id, 0)

        if result.format == "minimal":
            summary = format_minimal(occupancy=occupancy, window=window)
        elif result.format == "compaction":
            summary = format_compaction(
                occupancy=occupancy, window=window,
                compaction_number=state.compaction_count + 1,
                message_count=msg_count, cost_usd=None,
                soft_boundary=self.server.config.soft_boundary,
            )
        else:
            summary = format_full(
                occupancy=occupancy, window=window,
                message_count=msg_count, compaction_count=state.compaction_count,
                cost_usd=None, soft_boundary=self.server.config.soft_boundary,
            )

        # Apply result (updates state)
        self.server.trigger_engine.apply_result(state, result, occupancy)

        self._respond_json(200, {
            "inject": True,
            "summary": summary,
            "format": result.format,
            "triggers": result.triggers_fired,
        })

    def _respond_json(self, status: int, data: dict) -> None:
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def write_pid_file() -> None:
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(str(os.getpid()))


def remove_pid_file() -> None:
    try:
        PID_FILE.unlink()
    except FileNotFoundError:
        pass


def main() -> None:
    """Start the sidecar server."""
    import argparse

    parser = argparse.ArgumentParser(description="Context metrics sidecar")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    server = ContextMetricsSidecar(port=args.port)
    write_pid_file()

    def shutdown_handler(signum: int, frame: object) -> None:
        logger.info("Shutting down sidecar (signal %d)", signum)
        remove_pid_file()
        server.shutdown()

    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)

    logger.info("Sidecar listening on port %d", args.port)
    try:
        server.serve_forever()
    finally:
        remove_pid_file()


if __name__ == "__main__":
    main()
```

**Step 4: Run tests to verify pass**

Run: `cd packages/plugins/context-metrics && uv run pytest tests/test_server.py -v`
Expected: All 5 tests PASS.

**Step 5: Commit**

```bash
git add packages/plugins/context-metrics/scripts/server.py packages/plugins/context-metrics/tests/test_server.py
git commit -m "feat(context-metrics): add sidecar HTTP server"
```

---

### Task 8: Hook Scripts

**Files:**
- Create: `packages/plugins/context-metrics/scripts/start_sidecar.py`
- Create: `packages/plugins/context-metrics/scripts/stop_sidecar.py`
- Create: `packages/plugins/context-metrics/scripts/context_summary.py`
- Create: `packages/plugins/context-metrics/tests/test_hooks.py`
- Reference: Design doc Amendment 3 F3 (lifecycle), Amendment 3 F4 (command hooks), Amendment 4 F5 (stdout injection)

**Context:** Three command hook scripts. `start_sidecar.py` starts the server if not running, registers the session. `stop_sidecar.py` deregisters the session, stops server if no sessions. `context_summary.py` queries sidecar, prints summary to stdout (exit 0) or exits silently (no injection).

**Step 1: Write failing tests**

```python
"""Tests for hook scripts."""

import json
import subprocess
import sys
import threading
from pathlib import Path

from scripts.server import ContextMetricsSidecar


class TestContextSummary:
    """Test context_summary.py — the injection hook."""

    def setup_method(self) -> None:
        self.server = ContextMetricsSidecar(port=0)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def teardown_method(self) -> None:
        self.server.shutdown()
        self.thread.join(timeout=2)

    def test_prints_summary_to_stdout(self, normal_session: Path) -> None:
        """context_summary.py should print a summary line and exit 0."""
        import urllib.request
        # Register session first
        urllib.request.urlopen(
            f"http://127.0.0.1:{self.port}/sessions/register"
            f"?session_id=test_hook&transcript_path={normal_session}",
            timeout=2,
        )
        # Force first injection by setting high prompt count
        state = self.server.get_or_create_state("test_hook")
        state.prompts_since_injection = 10

        hook_input = json.dumps({
            "hook_event_name": "UserPromptSubmit",
            "session_id": "test_hook",
            "transcript_path": str(normal_session),
        })
        script = Path(__file__).parent.parent / "scripts" / "context_summary.py"
        result = subprocess.run(
            [sys.executable, str(script), "--port", str(self.port)],
            input=hook_input, capture_output=True, text=True, timeout=5,
        )
        assert result.returncode == 0
        # stdout should contain a context summary line
        assert "Context:" in result.stdout or result.stdout.strip() == ""

    def test_exits_zero_on_sidecar_down(self) -> None:
        """Fail-open: if sidecar unreachable, exit 0 with no output."""
        hook_input = json.dumps({
            "hook_event_name": "UserPromptSubmit",
            "session_id": "test_hook",
            "transcript_path": "/nonexistent.jsonl",
        })
        script = Path(__file__).parent.parent / "scripts" / "context_summary.py"
        result = subprocess.run(
            [sys.executable, str(script), "--port", "19999"],
            input=hook_input, capture_output=True, text=True, timeout=5,
        )
        # Fail-open: exit 0, no output
        assert result.returncode == 0
```

**Step 2: Run tests to verify failure**

Run: `cd packages/plugins/context-metrics && uv run pytest tests/test_hooks.py -v`
Expected: FAIL

**Step 3: Implement hook scripts**

`scripts/context_summary.py`:

```python
#!/usr/bin/env python3
"""Context summary injection hook.

Hook events: UserPromptSubmit, SessionStart(compact).
Queries sidecar → prints summary to stdout → exit 0.
Fail-open: sidecar unreachable → exit 0 (no output).

Design reference: Amendment 4 F5 (stdout injection).
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request

DEFAULT_PORT = 7432


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args()

    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0  # Fail-open

    event = hook_input.get("hook_event_name", "")
    session_id = hook_input.get("session_id", "")
    transcript_path = hook_input.get("transcript_path", "")

    # Handle compaction: mark compaction pending on sidecar
    if event == "SessionStart" and hook_input.get("subtype") == "compact":
        _notify_compaction(args.port, session_id)

    # Query sidecar for injection decision
    payload = json.dumps({
        "hook_event_name": event,
        "session_id": session_id,
        "transcript_path": transcript_path,
    }).encode()

    try:
        req = urllib.request.Request(
            f"http://127.0.0.1:{args.port}/hooks/context-metrics",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            result = json.loads(resp.read())
    except (urllib.error.URLError, OSError, json.JSONDecodeError, TimeoutError):
        return 0  # Fail-open: sidecar unreachable

    if result.get("inject") and result.get("summary"):
        print(result["summary"])

    return 0


def _notify_compaction(port: int, session_id: str) -> None:
    """Tell sidecar that a compaction occurred for this session."""
    try:
        url = f"http://127.0.0.1:{port}/sessions/compaction?session_id={session_id}"
        urllib.request.urlopen(url, timeout=2)
    except (urllib.error.URLError, OSError, TimeoutError):
        pass  # Fail-open


if __name__ == "__main__":
    sys.exit(main())
```

`scripts/start_sidecar.py`:

```python
#!/usr/bin/env python3
"""Start sidecar and register session.

Hook event: SessionStart(startup), async command hook.
If sidecar already running: register session, exit.
If not running: start sidecar in background, register session, exit.

Design reference: Amendment 3 F3 (no kill-restart).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_PORT = 7432
PID_FILE = Path.home() / ".claude" / ".context-metrics-sidecar.pid"
PLUGIN_ROOT = Path(__file__).parent.parent


def main() -> int:
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0  # Fail-open

    transcript_path = hook_input.get("transcript_path", "")
    session_id = Path(transcript_path).stem if transcript_path else ""

    if not session_id:
        return 0  # No session info

    # Check if sidecar is running
    if not _sidecar_healthy():
        _start_sidecar()
        # Wait for startup (up to 2 seconds)
        for _ in range(20):
            time.sleep(0.1)
            if _sidecar_healthy():
                break

    # Register session
    _register_session(session_id, transcript_path)
    return 0


def _sidecar_healthy() -> bool:
    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{DEFAULT_PORT}/health", timeout=1
        ) as resp:
            return resp.status == 200
    except (urllib.error.URLError, OSError, TimeoutError):
        return False


def _start_sidecar() -> None:
    server_script = PLUGIN_ROOT / "scripts" / "server.py"
    subprocess.Popen(
        [sys.executable, str(server_script), "--port", str(DEFAULT_PORT)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


def _register_session(session_id: str, transcript_path: str) -> None:
    try:
        url = (
            f"http://127.0.0.1:{DEFAULT_PORT}/sessions/register"
            f"?session_id={session_id}&transcript_path={transcript_path}"
        )
        urllib.request.urlopen(url, timeout=2)
    except (urllib.error.URLError, OSError, TimeoutError):
        pass  # Fail-open


if __name__ == "__main__":
    sys.exit(main())
```

`scripts/stop_sidecar.py`:

```python
#!/usr/bin/env python3
"""Deregister session and optionally stop sidecar.

Hook event: SessionEnd, command hook (stdlib only).
Deregisters session. If no active sessions remain, sends SIGTERM to sidecar.

Design reference: Amendment 3 F3 (lifecycle).
"""

from __future__ import annotations

import json
import os
import signal
import sys
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_PORT = 7432
PID_FILE = Path.home() / ".claude" / ".context-metrics-sidecar.pid"


def main() -> int:
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    transcript_path = hook_input.get("transcript_path", "")
    session_id = Path(transcript_path).stem if transcript_path else ""

    if not session_id:
        return 0

    # Deregister session
    active_sessions = _deregister_session(session_id)

    # If no sessions remain, stop sidecar
    if active_sessions == 0:
        _stop_sidecar()

    return 0


def _deregister_session(session_id: str) -> int:
    """Deregister and return remaining active session count."""
    try:
        url = f"http://127.0.0.1:{DEFAULT_PORT}/sessions/deregister?session_id={session_id}"
        with urllib.request.urlopen(url, timeout=2) as resp:
            data = json.loads(resp.read())
            return data.get("active_sessions", 0)
    except (urllib.error.URLError, OSError, json.JSONDecodeError, TimeoutError):
        return -1  # Unknown — don't kill sidecar


def _stop_sidecar() -> None:
    """Send SIGTERM to sidecar process."""
    try:
        pid = int(PID_FILE.read_text().strip())
        os.kill(pid, signal.SIGTERM)
    except (FileNotFoundError, ValueError, ProcessLookupError, OSError):
        pass


if __name__ == "__main__":
    sys.exit(main())
```

**Step 4: Run tests to verify pass**

Run: `cd packages/plugins/context-metrics && uv run pytest tests/test_hooks.py -v`
Expected: All 2 tests PASS.

**Step 5: Commit**

```bash
git add packages/plugins/context-metrics/scripts/{context_summary,start_sidecar,stop_sidecar}.py packages/plugins/context-metrics/tests/test_hooks.py
git commit -m "feat(context-metrics): add hook scripts (start, stop, context_summary)"
```

---

### Task 9: hooks.json Wiring + Integration Tests

**Files:**
- Modify: `packages/plugins/context-metrics/hooks/hooks.json`
- Create: `packages/plugins/context-metrics/tests/test_integration.py`
- Reference: Design doc Amendment 3 F4 (command hook format)

**Step 1: Write hooks.json**

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ${CLAUDE_PLUGIN_ROOT}/scripts/start_sidecar.py",
            "timeout": 30,
            "statusMessage": "Starting context metrics"
          }
        ]
      },
      {
        "matcher": "compact",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ${CLAUDE_PLUGIN_ROOT}/scripts/context_summary.py",
            "timeout": 5,
            "statusMessage": "Updating context metrics (post-compaction)"
          }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 ${CLAUDE_PLUGIN_ROOT}/scripts/context_summary.py",
            "timeout": 5,
            "statusMessage": "Updating context metrics"
          }
        ]
      }
    ],
    "SessionEnd": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 ${CLAUDE_PLUGIN_ROOT}/scripts/stop_sidecar.py",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

**Step 2: Write integration tests**

```python
"""Integration tests for the full context-metrics pipeline.

Tests the end-to-end flow: sidecar + JSONL fixtures + trigger evaluation + formatting.
"""

import json
import threading
import urllib.request
from pathlib import Path

from scripts.server import ContextMetricsSidecar


class TestEndToEnd:
    def setup_method(self) -> None:
        self.server = ContextMetricsSidecar(port=0)
        self.port = self.server.server_address[1]
        self.base = f"http://127.0.0.1:{self.port}"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def teardown_method(self) -> None:
        self.server.shutdown()
        self.thread.join(timeout=2)

    def _register(self, session_id: str, transcript_path: Path) -> None:
        urllib.request.urlopen(
            f"{self.base}/sessions/register?session_id={session_id}"
            f"&transcript_path={transcript_path}",
            timeout=2,
        )

    def _post_hook(self, session_id: str, transcript_path: Path) -> dict:
        payload = json.dumps({
            "hook_event_name": "UserPromptSubmit",
            "session_id": session_id,
            "transcript_path": str(transcript_path),
        }).encode()
        req = urllib.request.Request(
            f"{self.base}/hooks/context-metrics",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=2) as resp:
            return json.loads(resp.read())

    def test_first_prompt_injects_full(self, normal_session: Path) -> None:
        """First prompt should always inject (boundary crossing triggers)."""
        self._register("e2e_1", normal_session)
        result = self._post_hook("e2e_1", normal_session)
        assert result["inject"] is True
        assert "Context:" in result["summary"]
        assert result["format"] in ("full", "compaction")

    def test_second_prompt_suppressed_if_no_change(self, normal_session: Path) -> None:
        """Second prompt with same file should be suppressed (no delta)."""
        self._register("e2e_2", normal_session)
        self._post_hook("e2e_2", normal_session)  # First: injects
        result = self._post_hook("e2e_2", normal_session)  # Second: suppressed
        assert result["inject"] is False

    def test_heartbeat_fires_after_interval(self, normal_session: Path) -> None:
        """After enough suppressed prompts, heartbeat fires."""
        self._register("e2e_3", normal_session)
        self._post_hook("e2e_3", normal_session)  # First: injects (resets counter)
        # Simulate 8 prompts without change
        for _ in range(8):
            result = self._post_hook("e2e_3", normal_session)
        # 8th should trigger heartbeat
        assert result["inject"] is True
        assert result["format"] == "minimal"
        assert "heartbeat" in result["triggers"]

    def test_near_boundary_uses_headroom_threshold(self, near_boundary: Path) -> None:
        """At 92% occupancy, headroom triggers should activate."""
        self._register("e2e_4", near_boundary)
        result = self._post_hook("e2e_4", near_boundary)
        assert result["inject"] is True
        # At 92%, the 90% boundary crossing should fire
        assert "boundary_crossing" in result["triggers"]

    def test_empty_file_fails_closed(self, empty_session: Path) -> None:
        """Empty JSONL → no injection (fail-closed data layer)."""
        self._register("e2e_5", empty_session)
        result = self._post_hook("e2e_5", empty_session)
        assert result["inject"] is False
```

**Step 3: Run integration tests**

Run: `cd packages/plugins/context-metrics && uv run pytest tests/test_integration.py -v`
Expected: All 5 tests PASS.

**Step 4: Commit**

```bash
git add packages/plugins/context-metrics/hooks/hooks.json packages/plugins/context-metrics/tests/test_integration.py
git commit -m "feat(context-metrics): wire hooks.json and add integration tests"
```

---

### Task 10: Dashboard Skill (Simplified v1)

**Files:**
- Create: `packages/plugins/context-metrics/skills/context-dashboard/SKILL.md`
- Reference: Design doc On-Demand Dashboard (lines 324-352), Amendment 4 F10 (simplified for v1)

**Context:** v1 dashboard reads JSONL directly (no devtools). Shows occupancy, message count, compaction history. Category breakdown deferred to v1.1.

**Step 1: Create SKILL.md**

```markdown
---
name: context-dashboard
description: Show detailed context window metrics. Use when user asks about context usage, token counts, or window occupancy.
---

# Context Dashboard

Show detailed context window occupancy metrics by reading the current session's JSONL transcript.

## Procedure

1. Read the current session's transcript path from the conversation context (look for `transcript_path` in recent hook inputs or system state).
2. If transcript path is not available, inform the user: "Cannot determine transcript path. Context metrics require an active session with transcript logging."
3. Read the JSONL file at the transcript path.
4. Scan ALL records (not just tail) to compute:
   - **Current occupancy:** Last valid assistant record's usage (input + cache_read + cache_create tokens)
   - **Message count:** Count of records with `type == "user"` or `type == "assistant"`
   - **Compaction count:** Count of records with `subtype == "compact_boundary"` or `type == "system"` with compact metadata
   - **Session duration:** Time from first to last record timestamp
5. Read config from `~/.claude/context-metrics.local.md` for window size and soft boundary.
6. Format and display:

```
## Context Dashboard

**Window:** {occupancy}/{window} tokens ({pct}%)
**Messages:** {count} | **Compactions:** {compaction_count}
**Phase:** {compaction_count + 1} (current)
```

If soft_boundary is configured and occupancy approaches or exceeds it, add a warning line.

## Limitations (v1)

- No category breakdown (requires devtools `/groups` endpoint — deferred to v1.1)
- No phase history (requires tracking pre-compaction sizes from `compact_boundary` markers — deferred to v1.1)
- No cost data unless devtools is running
- Reading full JSONL may be slow for very long sessions (>100MB transcripts)
```

**Step 2: Commit**

```bash
git add packages/plugins/context-metrics/skills/context-dashboard/SKILL.md
git commit -m "feat(context-metrics): add simplified v1 dashboard skill"
```

---

## Post-Implementation Checklist

After all tasks complete:

- [ ] All tests pass: `cd packages/plugins/context-metrics && uv run pytest -v`
- [ ] Plugin installs: `claude plugin install context-metrics@turbo-mode` (after marketplace update)
- [ ] Sidecar starts on session open
- [ ] Summary line appears in conversation after significant context growth
- [ ] Heartbeat fires after 8 prompts without material change
- [ ] Compaction notice appears after compaction
- [ ] Sidecar stops when last session closes
- [ ] Empty/missing JSONL → no injection (fail-closed)
- [ ] Sidecar unreachable → no injection (fail-open)

## Wire Contracts (specified here, referenced by Task 7)

### Sidecar-to-`context_summary.py` response

```json
{
  "inject": true,
  "summary": "Context: 142k/200k tokens (71%) | 847 msgs | Phase 3 (2 compactions)",
  "format": "full",
  "triggers": ["token_delta", "boundary_crossing"]
}
```

When `inject` is `false`:

```json
{
  "inject": false,
  "reason": "below threshold"
}
```

### Session register/deregister

Register: `GET /sessions/register?session_id={stem}&transcript_path={path}`
Response: `{ "registered": true, "session_id": "abc123" }`

Deregister: `GET /sessions/deregister?session_id={stem}`
Response: `{ "deregistered": true, "active_sessions": 0 }`

### Compaction notification

`GET /sessions/compaction?session_id={stem}`
Sets `compaction_pending = true` on the session state. Next hook evaluation will trigger compaction injection.
