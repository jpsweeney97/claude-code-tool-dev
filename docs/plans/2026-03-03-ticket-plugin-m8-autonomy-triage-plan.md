# M8: Autonomy + Triage Script — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace Phase 1's agent hard-block with full autonomy enforcement (config-driven modes, session caps, override rejection), and build the triage analysis script.

**Architecture:** Preflight becomes the autonomy enforcement point: it reads config once (snapshot pattern to prevent TOCTOU), checks mode/cap/overrides/action-exclusions, and returns the config in response data for execute's defense-in-depth. The triage script is a standalone read-only analysis tool using existing `ticket_read` and audit trail APIs. Three matching strategies for orphan detection are ported from the handoff triage implementation (not the canonical spec's "text-similarity" description).

**Tech Stack:** Python 3.11+, PyYAML 6.0, pytest 8.0+

**Source design:** `docs/plans/2026-03-03-ticket-plugin-phase2-design.md` lines 185-273

---

## Pre-Implementation Reference

### Key Locations in `ticket_engine_core.py`

| What | Lines | Notes |
|------|-------|-------|
| `_read_autonomy_mode()` | 253-285 | **Replace entirely.** Has bare `except: pass` at line 282. |
| `engine_preflight` signature | 288-301 | Add `hook_injected: bool = False` parameter. |
| Phase 1 agent hard-block (preflight) | 337-351 | **Replace with autonomy enforcement.** |
| `checks_passed.append("autonomy_policy")` | 351 | Moves inside new autonomy logic. |
| Confidence gate | 353-366 | Stays. Agent checks move before this. |
| `_ORIGIN_MODIFIER` / `_T_BASE` | 246-247 | Stays. |
| `engine_execute` signature | 695-707 | Change `autonomy_mode: str` → `autonomy_config: AutonomyConfig | None`. |
| Phase 1 hard-block (execute) | 713-720 | **Remove.** Marked `# M8: Remove this block`. |
| Transport validation (execute) | 722-731 | **Keep.** Becomes primary gate. |
| Audit entry writes | 735-744, 764-775, 779-789 | Update `autonomy_mode` references to `config.mode`. |
| `engine_count_session_creates` | 660-692 | Used by session cap check. No changes. |
| `_audit_append` | 640-657 | No changes. |
| `AUDIT_UNAVAILABLE` | 57 | Used by session cap check. No changes. |

### Entrypoint Wiring

Both `ticket_engine_user.py` and `ticket_engine_agent.py` need identical changes:

| Dispatch | Current Gap | M8 Fix |
|----------|-------------|--------|
| `preflight` | Missing `hook_injected`, `dependency_override` | Add both pass-throughs |
| `execute` | Missing `autonomy_config` | Add `AutonomyConfig.from_dict()` deserialization |

### Existing Test Fixtures

- `tmp_tickets` (conftest.py): creates `tmp_path/docs/tickets/`. No `.claude/` dir → `read_autonomy_config` returns default.
- `make_ticket(...)` (conftest.py): creates a v1.0 ticket file with full frontmatter.
- `tmp_audit` (conftest.py): creates `tmp_path/docs/tickets/.audit/`.

### Autonomy Check Ordering (Preflight)

After origin + action validation, the agent checks flow:

```
1. Agent action exclusions: reopen → user-only
2. Agent override rejection: dedup_override, dependency_override
3. Agent hook_injected check: !hook_injected → policy_blocked
4. Agent autonomy mode:
   a. suggest → policy_blocked
   b. auto_silent → policy_blocked (v1.0 gate)
   c. auto_audit → check session cap → proceed
5. ✓ autonomy_policy passed
```

Users skip all agent checks → `autonomy_policy` always passes.

---

## Task 8: AutonomyConfig + read_autonomy_config()

**Files:**
- Modify: `scripts/ticket_engine_core.py` (replace lines 253-285)
- Create: `tests/test_autonomy.py`

**Dependencies:** None.

### Step 1: Write failing tests

Create `tests/test_autonomy.py`:

```python
"""Tests for autonomy config parsing and enforcement."""
from __future__ import annotations

from pathlib import Path

import pytest

from scripts.ticket_engine_core import AutonomyConfig, read_autonomy_config


@pytest.fixture
def autonomy_env(tmp_path: Path):
    """Set up directory structure for autonomy config tests.

    Creates:
        tmp_path/.claude/          (project root marker)
        tmp_path/docs/tickets/     (tickets_dir)

    Returns (tickets_dir, config_path) tuple.
    """
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    tickets_dir = tmp_path / "docs" / "tickets"
    tickets_dir.mkdir(parents=True)
    config_path = claude_dir / "ticket.local.md"
    return tickets_dir, config_path


class TestAutonomyConfig:
    """Test AutonomyConfig dataclass and read_autonomy_config() parsing."""

    def test_default_when_no_config_file(self, autonomy_env):
        """Missing .claude/ticket.local.md → default suggest/5/no warnings."""
        tickets_dir, _ = autonomy_env
        config = read_autonomy_config(tickets_dir)
        assert config.mode == "suggest"
        assert config.max_creates == 5
        assert config.warnings == []

    def test_valid_auto_audit_config(self, autonomy_env):
        """Valid auto_audit config with custom max_creates."""
        tickets_dir, config_path = autonomy_env
        config_path.write_text(
            "---\nautonomy_mode: auto_audit\nmax_creates_per_session: 10\n---\n"
        )
        config = read_autonomy_config(tickets_dir)
        assert config.mode == "auto_audit"
        assert config.max_creates == 10
        assert config.warnings == []

    def test_valid_auto_silent_config(self, autonomy_env):
        """Valid auto_silent config."""
        tickets_dir, config_path = autonomy_env
        config_path.write_text("---\nautonomy_mode: auto_silent\n---\n")
        config = read_autonomy_config(tickets_dir)
        assert config.mode == "auto_silent"
        assert config.max_creates == 5  # default

    def test_malformed_yaml_warns_and_defaults(self, autonomy_env):
        """Malformed YAML → suggest + warning (NOT silent swallow)."""
        tickets_dir, config_path = autonomy_env
        config_path.write_text("---\n: [invalid yaml\n---\n")
        config = read_autonomy_config(tickets_dir)
        assert config.mode == "suggest"
        assert len(config.warnings) == 1
        assert "failed to parse" in config.warnings[0].lower()

    def test_unknown_mode_warns_and_defaults(self, autonomy_env):
        """Unknown autonomy_mode → suggest + warning."""
        tickets_dir, config_path = autonomy_env
        config_path.write_text("---\nautonomy_mode: yolo\n---\n")
        config = read_autonomy_config(tickets_dir)
        assert config.mode == "suggest"
        assert len(config.warnings) == 1
        assert "yolo" in config.warnings[0]

    def test_non_dict_frontmatter_warns(self, autonomy_env):
        """YAML list instead of dict → suggest + warning."""
        tickets_dir, config_path = autonomy_env
        config_path.write_text("---\n- item1\n- item2\n---\n")
        config = read_autonomy_config(tickets_dir)
        assert config.mode == "suggest"
        assert len(config.warnings) == 1
        assert "not a dict" in config.warnings[0].lower()

    def test_missing_mode_field_defaults_suggest(self, autonomy_env):
        """No autonomy_mode field → suggest (implicit default)."""
        tickets_dir, config_path = autonomy_env
        config_path.write_text("---\nsome_other_field: value\n---\n")
        config = read_autonomy_config(tickets_dir)
        assert config.mode == "suggest"
        assert config.warnings == []

    def test_non_int_max_creates_warns(self, autonomy_env):
        """Non-integer max_creates → default 5 + warning."""
        tickets_dir, config_path = autonomy_env
        config_path.write_text(
            "---\nautonomy_mode: auto_audit\nmax_creates_per_session: lots\n---\n"
        )
        config = read_autonomy_config(tickets_dir)
        assert config.mode == "auto_audit"
        assert config.max_creates == 5
        assert len(config.warnings) == 1
        assert "max_creates" in config.warnings[0].lower()

    def test_zero_max_creates_disables_agent_creates(self, autonomy_env):
        """max_creates=0 means disable all agent creates (not invalid)."""
        tickets_dir, config_path = autonomy_env
        config_path.write_text(
            "---\nautonomy_mode: auto_audit\nmax_creates_per_session: 0\n---\n"
        )
        config = read_autonomy_config(tickets_dir)
        assert config.max_creates == 0
        assert config.warnings == []

    def test_negative_max_creates_warns(self, autonomy_env):
        """Negative max_creates → default 5 + warning."""
        tickets_dir, config_path = autonomy_env
        config_path.write_text(
            "---\nautonomy_mode: auto_audit\nmax_creates_per_session: -1\n---\n"
        )
        config = read_autonomy_config(tickets_dir)
        assert config.max_creates == 5
        assert len(config.warnings) == 1

    def test_no_frontmatter_delimiters_warns(self, autonomy_env):
        """File exists but no --- delimiters → suggest + warning."""
        tickets_dir, config_path = autonomy_env
        config_path.write_text("autonomy_mode: auto_audit\n")
        config = read_autonomy_config(tickets_dir)
        assert config.mode == "suggest"
        assert len(config.warnings) == 1
        assert "no valid frontmatter" in config.warnings[0].lower()

    def test_to_dict_from_dict_round_trip(self):
        """AutonomyConfig serialization round-trips correctly."""
        original = AutonomyConfig(mode="auto_audit", max_creates=10, warnings=["w1"])
        restored = AutonomyConfig.from_dict(original.to_dict())
        assert restored.mode == original.mode
        assert restored.max_creates == original.max_creates
        assert restored.warnings == original.warnings
```

### Step 2: Run tests to verify they fail

```bash
cd packages/plugins/ticket && uv run pytest tests/test_autonomy.py -v
```

Expected: `ImportError` — `AutonomyConfig` and `read_autonomy_config` don't exist yet.

### Step 3: Implement AutonomyConfig and read_autonomy_config

In `scripts/ticket_engine_core.py`, add `AutonomyConfig` dataclass after `AUDIT_UNAVAILABLE` (line 57), and replace `_read_autonomy_mode` (lines 253-285) with `read_autonomy_config`:

```python
# After AUDIT_UNAVAILABLE sentinel (line 57):

_VALID_AUTONOMY_MODES = frozenset({"suggest", "auto_audit", "auto_silent"})


@dataclass
class AutonomyConfig:
    """Autonomy configuration parsed from .claude/ticket.local.md.

    mode: "suggest" (default) | "auto_audit" | "auto_silent"
    max_creates: per-session create cap (default 5)
    warnings: parsing warnings (empty if clean parse)
    """

    mode: str = "suggest"
    max_creates: int = 5
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "max_creates": self.max_creates,
            "warnings": self.warnings,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AutonomyConfig:
        """Reconstruct from dict (snapshot deserialization). No validation."""
        return cls(
            mode=data.get("mode", "suggest"),
            max_creates=data.get("max_creates", 5),
            warnings=data.get("warnings", []),
        )
```

Replace `_read_autonomy_mode` (lines 253-285) with:

```python
def read_autonomy_config(tickets_dir: Path) -> AutonomyConfig:
    """Read autonomy config from .claude/ticket.local.md YAML frontmatter.

    Fail-closed: returns AutonomyConfig(mode="suggest") on any error.
    Emits warnings to stderr for malformed/unknown values.
    """
    import sys

    warnings: list[str] = []

    # Walk up from tickets_dir to find project root (.claude/ directory).
    project_root = tickets_dir
    while project_root != project_root.parent:
        if (project_root / ".claude").is_dir():
            break
        project_root = project_root.parent

    config_path = project_root / ".claude" / "ticket.local.md"
    if not config_path.is_file():
        return AutonomyConfig()

    try:
        import yaml

        text = config_path.read_text(encoding="utf-8")
        if not text.startswith("---"):
            warnings.append("ticket.local.md: file exists but has no valid frontmatter (missing --- delimiters)")
            print(f"WARNING: {warnings[-1]}", file=sys.stderr)
            return AutonomyConfig(warnings=warnings)
        parts = text.split("---", 2)
        if len(parts) < 3:
            warnings.append("ticket.local.md: file exists but has no valid frontmatter (incomplete --- delimiters)")
            print(f"WARNING: {warnings[-1]}", file=sys.stderr)
            return AutonomyConfig(warnings=warnings)
        data = yaml.safe_load(parts[1])
        if not isinstance(data, dict):
            warnings.append("ticket.local.md: frontmatter is not a dict")
            print(f"WARNING: {warnings[-1]}", file=sys.stderr)
            return AutonomyConfig(warnings=warnings)
    except Exception as exc:
        warnings.append(f"ticket.local.md: failed to parse YAML: {exc}")
        print(f"WARNING: {warnings[-1]}", file=sys.stderr)
        return AutonomyConfig(warnings=warnings)

    # Parse mode.
    mode = data.get("autonomy_mode", "suggest")
    if mode not in _VALID_AUTONOMY_MODES:
        warnings.append(
            f"ticket.local.md: unknown autonomy_mode {mode!r}, defaulting to 'suggest'"
        )
        print(f"WARNING: {warnings[-1]}", file=sys.stderr)
        mode = "suggest"

    # Parse max_creates.
    max_creates = data.get("max_creates_per_session", 5)
    if not isinstance(max_creates, int) or max_creates < 0:
        warnings.append(
            f"ticket.local.md: invalid max_creates_per_session {max_creates!r}, defaulting to 5"
        )
        print(f"WARNING: {warnings[-1]}", file=sys.stderr)
        max_creates = 5

    return AutonomyConfig(mode=mode, max_creates=max_creates, warnings=warnings)
```

### Step 4: Run tests to verify they pass

```bash
cd packages/plugins/ticket && uv run pytest tests/test_autonomy.py::TestAutonomyConfig -v
```

Expected: 12 tests PASS.

### Step 5: Run full test suite to verify no regressions

```bash
cd packages/plugins/ticket && uv run pytest -v
```

Expected: 201 tests PASS. No existing code calls `_read_autonomy_mode`, so removing it has no callers to break.

### Step 6: Commit

```bash
git add tests/test_autonomy.py scripts/ticket_engine_core.py
git commit -m "feat: add AutonomyConfig dataclass and read_autonomy_config with warnings"
```

---

## Task 9: Autonomy Enforcement (Replace Hard-Blocks)

**Files:**
- Modify: `scripts/ticket_engine_core.py` (preflight lines 337-351, execute lines 695-791)
- Modify: `scripts/ticket_engine_user.py` (lines 16-22, 84-109)
- Modify: `scripts/ticket_engine_agent.py` (lines 16-22, 84-109)
- Modify: `tests/test_engine.py` (update 3 existing tests)
- Add to: `tests/test_autonomy.py` (new test classes)

**Dependencies:** Task 8 complete.

### Step 1: Write failing tests for preflight autonomy enforcement

Add to `tests/test_autonomy.py`:

```python
from scripts.ticket_engine_core import (
    AUDIT_UNAVAILABLE,
    AutonomyConfig,
    engine_count_session_creates,
    engine_execute,
    engine_preflight,
    read_autonomy_config,
)


class TestAutonomyPreflight:
    """Test autonomy enforcement in engine_preflight."""

    @pytest.fixture
    def auto_audit_env(self, autonomy_env):
        """Set up auto_audit config and return tickets_dir."""
        tickets_dir, config_path = autonomy_env
        config_path.write_text(
            "---\nautonomy_mode: auto_audit\nmax_creates_per_session: 3\n---\n"
        )
        return tickets_dir

    def _preflight(self, tickets_dir, **overrides):
        """Helper: call engine_preflight with sensible defaults."""
        defaults = dict(
            ticket_id=None,
            action="create",
            session_id="test-session",
            request_origin="user",
            classify_confidence=0.95,
            classify_intent="create",
            dedup_fingerprint="abc",
            target_fingerprint=None,
            tickets_dir=tickets_dir,
        )
        defaults.update(overrides)
        return engine_preflight(**defaults)

    def test_agent_suggest_mode_blocked(self, autonomy_env):
        """Default suggest mode: agent create is policy_blocked."""
        tickets_dir, _ = autonomy_env  # no config file → suggest
        resp = self._preflight(
            tickets_dir, request_origin="agent", hook_injected=True,
        )
        assert resp.state == "policy_blocked"
        assert "suggest" in resp.message.lower()

    def test_agent_auto_audit_allowed(self, auto_audit_env):
        """auto_audit mode: agent create proceeds (under cap)."""
        resp = self._preflight(
            auto_audit_env, request_origin="agent", hook_injected=True,
        )
        assert resp.state == "ok"
        assert "autonomy_config" in resp.data

    def test_agent_auto_audit_includes_notification(self, auto_audit_env):
        """auto_audit response includes notification template."""
        resp = self._preflight(
            auto_audit_env, request_origin="agent", hook_injected=True,
        )
        assert resp.state == "ok"
        assert "notification" in resp.data

    def test_agent_auto_silent_blocked_v1(self, autonomy_env):
        """auto_silent is feature-gated in v1.0 → policy_blocked."""
        tickets_dir, config_path = autonomy_env
        config_path.write_text("---\nautonomy_mode: auto_silent\n---\n")
        resp = self._preflight(
            tickets_dir, request_origin="agent", hook_injected=True,
        )
        assert resp.state == "policy_blocked"
        assert "auto_silent" in resp.message.lower() or "v1.0" in resp.message.lower()

    def test_agent_reopen_user_only(self, auto_audit_env):
        """Reopen is user-only in v1.0, even in auto_audit mode."""
        resp = self._preflight(
            auto_audit_env,
            request_origin="agent",
            hook_injected=True,
            action="reopen",
            classify_intent="reopen",
            ticket_id="T-20260302-01",
        )
        assert resp.state == "policy_blocked"
        assert "user-only" in resp.message.lower() or "reopen" in resp.message.lower()

    def test_agent_dedup_override_rejected(self, auto_audit_env):
        """Agents cannot use dedup_override."""
        resp = self._preflight(
            auto_audit_env,
            request_origin="agent",
            hook_injected=True,
            dedup_override=True,
        )
        assert resp.state == "policy_blocked"
        assert "dedup_override" in resp.message.lower()

    def test_agent_dependency_override_rejected(self, auto_audit_env):
        """Agents cannot use dependency_override."""
        resp = self._preflight(
            auto_audit_env,
            request_origin="agent",
            hook_injected=True,
            action="close",
            classify_intent="close",
            ticket_id="T-20260302-01",
            dependency_override=True,
        )
        assert resp.state == "policy_blocked"
        assert "dependency_override" in resp.message.lower()

    def test_agent_no_hook_injected_blocked(self, auto_audit_env):
        """Agent without hook_injected → policy_blocked."""
        resp = self._preflight(
            auto_audit_env, request_origin="agent", hook_injected=False,
        )
        assert resp.state == "policy_blocked"
        assert "hook_injected" in resp.message.lower()

    def test_agent_auto_audit_session_cap_reached(self, auto_audit_env):
        """auto_audit: agent create at session cap → policy_blocked."""
        import json
        import os
        from datetime import datetime, timezone

        # Write 3 successful creates to audit trail (cap is 3).
        date_dir = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        audit_dir = auto_audit_env / ".audit" / date_dir
        audit_dir.mkdir(parents=True)
        audit_file = audit_dir / "test-session.jsonl"
        for i in range(3):
            entry = {"action": "create", "result": f"ok_create", "session_id": "test-session"}
            with open(audit_file, "a") as f:
                f.write(json.dumps(entry) + "\n")

        resp = self._preflight(
            auto_audit_env, request_origin="agent", hook_injected=True,
        )
        assert resp.state == "policy_blocked"
        assert "cap" in resp.message.lower() or "3/3" in resp.message

    def test_agent_auto_audit_update_no_cap_check(self, auto_audit_env):
        """auto_audit: agent update proceeds without cap check (cap is create-only)."""
        from tests.conftest import make_ticket

        make_ticket(auto_audit_env, "2026-03-02-test.md")
        resp = self._preflight(
            auto_audit_env,
            request_origin="agent",
            hook_injected=True,
            action="update",
            classify_intent="update",
            ticket_id="T-20260302-01",
        )
        assert resp.state == "ok"

    def test_user_always_passes_autonomy(self, autonomy_env):
        """User requests pass autonomy check regardless of mode."""
        tickets_dir, config_path = autonomy_env
        config_path.write_text("---\nautonomy_mode: auto_silent\n---\n")
        resp = self._preflight(tickets_dir, request_origin="user")
        assert resp.state == "ok"

    def test_preflight_response_includes_autonomy_config(self, autonomy_env):
        """Preflight response data always includes autonomy_config snapshot."""
        tickets_dir, _ = autonomy_env
        resp = self._preflight(tickets_dir, request_origin="user")
        assert resp.state == "ok"
        assert "autonomy_config" in resp.data
        assert resp.data["autonomy_config"]["mode"] == "suggest"
```

### Step 2: Write failing tests for execute defense-in-depth

Add to `tests/test_autonomy.py`:

```python
class TestAutonomyExecute:
    """Test autonomy defense-in-depth in engine_execute.

    Execute defense uses allowlist semantics: only auto_audit proceeds
    for agents. All other modes (including unknown) are blocked.
    """

    def test_execute_agent_suggest_blocked(self, tmp_tickets):
        """Execute defense-in-depth: agent + suggest → policy_blocked."""
        config = AutonomyConfig(mode="suggest")
        resp = engine_execute(
            action="create",
            ticket_id=None,
            fields={"title": "Test", "problem": "Problem"},
            session_id="sess",
            request_origin="agent",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
            autonomy_config=config,
            hook_injected=True,
        )
        assert resp.state == "policy_blocked"

    def test_execute_agent_unknown_mode_blocked(self, tmp_tickets):
        """Execute defense-in-depth: unknown mode → policy_blocked (allowlist, not blocklist)."""
        config = AutonomyConfig(mode="yolo")
        resp = engine_execute(
            action="create",
            ticket_id=None,
            fields={"title": "Test", "problem": "Problem"},
            session_id="sess",
            request_origin="agent",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
            autonomy_config=config,
            hook_injected=True,
        )
        assert resp.state == "policy_blocked"

    def test_execute_agent_none_config_blocked(self, tmp_tickets):
        """Execute defense-in-depth: autonomy_config=None → default suggest → blocked."""
        resp = engine_execute(
            action="create",
            ticket_id=None,
            fields={"title": "Test", "problem": "Problem"},
            session_id="sess",
            request_origin="agent",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
            autonomy_config=None,
            hook_injected=True,
        )
        assert resp.state == "policy_blocked"

    def test_execute_agent_reopen_blocked(self, tmp_tickets):
        """Execute defense-in-depth mirrors preflight: agent reopen → policy_blocked."""
        from tests.conftest import make_ticket
        make_ticket(tmp_tickets, "t.md", id="T-20260302-01", status="done")
        config = AutonomyConfig(mode="auto_audit")
        resp = engine_execute(
            action="reopen",
            ticket_id="T-20260302-01",
            fields={},
            session_id="sess",
            request_origin="agent",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
            autonomy_config=config,
            hook_injected=True,
        )
        assert resp.state == "policy_blocked"

    def test_execute_agent_dedup_override_blocked(self, tmp_tickets):
        """Execute defense-in-depth mirrors preflight: agent dedup_override → policy_blocked."""
        config = AutonomyConfig(mode="auto_audit")
        resp = engine_execute(
            action="create",
            ticket_id=None,
            fields={"title": "Test", "problem": "Problem"},
            session_id="sess",
            request_origin="agent",
            dedup_override=True,
            dependency_override=False,
            tickets_dir=tmp_tickets,
            autonomy_config=config,
            hook_injected=True,
        )
        assert resp.state == "policy_blocked"

    def test_execute_agent_auto_audit_allowed(self, tmp_tickets):
        """Execute defense-in-depth: agent + auto_audit + under cap → proceed."""
        config = AutonomyConfig(mode="auto_audit", max_creates=5)
        resp = engine_execute(
            action="create",
            ticket_id=None,
            fields={"title": "Test", "problem": "Problem"},
            session_id="sess",
            request_origin="agent",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
            autonomy_config=config,
            hook_injected=True,
        )
        assert resp.state == "ok_create"

    def test_execute_agent_auto_audit_cap_reached(self, tmp_tickets):
        """Execute defense-in-depth: agent + auto_audit + at cap → policy_blocked."""
        import json
        import os
        from datetime import datetime, timezone

        config = AutonomyConfig(mode="auto_audit", max_creates=2)
        # Write 2 successful creates to audit trail.
        date_dir = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        audit_dir = tmp_tickets / ".audit" / date_dir
        audit_dir.mkdir(parents=True)
        audit_file = audit_dir / "sess.jsonl"
        for _ in range(2):
            entry = {"action": "create", "result": "ok_create", "session_id": "sess"}
            with open(audit_file, "a") as f:
                f.write(json.dumps(entry) + "\n")

        resp = engine_execute(
            action="create",
            ticket_id=None,
            fields={"title": "Test", "problem": "Problem"},
            session_id="sess",
            request_origin="agent",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
            autonomy_config=config,
            hook_injected=True,
        )
        assert resp.state == "policy_blocked"

    def test_execute_agent_max_creates_type_safety(self, tmp_tickets):
        """Execute defense-in-depth: non-int max_creates → policy_blocked (type safety)."""
        config = AutonomyConfig.__new__(AutonomyConfig)
        config.mode = "auto_audit"
        config.max_creates = "5"  # type: ignore[assignment]  # intentional crafted payload
        config.warnings = []
        resp = engine_execute(
            action="create",
            ticket_id=None,
            fields={"title": "Test", "problem": "Problem"},
            session_id="sess",
            request_origin="agent",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
            autonomy_config=config,
            hook_injected=True,
        )
        assert resp.state == "policy_blocked"
```

### Step 3: Run tests to verify they fail

```bash
cd packages/plugins/ticket && uv run pytest tests/test_autonomy.py -v -k "Preflight or Execute"
```

Expected: FAIL — `engine_preflight` doesn't accept `hook_injected`, `engine_execute` doesn't accept `autonomy_config`.

### Step 4: Implement preflight autonomy enforcement

In `ticket_engine_core.py`, modify `engine_preflight`:

**4a. Add `hook_injected` parameter to signature (after `dependency_override`):**

```python
def engine_preflight(
    *,
    ticket_id: str | None,
    action: str,
    session_id: str,
    request_origin: str,
    classify_confidence: float,
    classify_intent: str,
    dedup_fingerprint: str | None,
    target_fingerprint: str | None,
    duplicate_of: str | None = None,
    dedup_override: bool = False,
    dependency_override: bool = False,
    hook_injected: bool = False,
    tickets_dir: Path,
) -> EngineResponse:
```

**4b. Replace the Phase 1 agent hard-block (lines 337-351) with autonomy enforcement:**

Replace this block:
```python
    # --- Agent policy: Phase 1 strict fail-closed (Codex finding 5: before confidence) ---
    # Moved before confidence gate so all agent requests get policy_blocked,
    # not a misleading preflight_failed for coincidental confidence issues.
    if request_origin == "agent":
        return EngineResponse(
            state="policy_blocked",
            message="Agent mutations are hard-blocked in Phase 1. "
            "The PreToolUse hook (Phase 2) is required for legitimate agent invocations.",
            error_code="policy_blocked",
            data={
                "checks_passed": checks_passed,
                "checks_failed": [{"check": "agent_phase1_block", "reason": "Phase 1 fail-closed policy"}],
            },
        )
    checks_passed.append("autonomy_policy")
```

With:
```python
    # --- Autonomy policy (Codex finding 5: agent checks before confidence) ---
    config = read_autonomy_config(tickets_dir)
    notification: str | None = None

    if request_origin == "agent":
        # Action exclusions: reopen is user-only in v1.0.
        if action == "reopen":
            return EngineResponse(
                state="policy_blocked",
                message="Reopen is user-only in v1.0",
                error_code="policy_blocked",
                data={
                    "checks_passed": checks_passed,
                    "checks_failed": [
                        {"check": "agent_action_exclusion", "reason": "reopen is user-only"},
                    ],
                    "autonomy_config": config.to_dict(),
                },
            )

        # Override rejection: agents cannot use dedup_override or dependency_override.
        if dedup_override:
            return EngineResponse(
                state="policy_blocked",
                message="Agents cannot use dedup_override",
                error_code="policy_blocked",
                data={
                    "checks_passed": checks_passed,
                    "checks_failed": [
                        {"check": "agent_override_rejection", "reason": "dedup_override not allowed for agents"},
                    ],
                    "autonomy_config": config.to_dict(),
                },
            )
        if dependency_override:
            return EngineResponse(
                state="policy_blocked",
                message="Agents cannot use dependency_override",
                error_code="policy_blocked",
                data={
                    "checks_passed": checks_passed,
                    "checks_failed": [
                        {"check": "agent_override_rejection", "reason": "dependency_override not allowed for agents"},
                    ],
                    "autonomy_config": config.to_dict(),
                },
            )

        # Hook validation: agent must have hook_injected.
        if not hook_injected:
            return EngineResponse(
                state="policy_blocked",
                message="Agent mutations require hook_injected=True (missing trust field)",
                error_code="policy_blocked",
                data={
                    "checks_passed": checks_passed,
                    "checks_failed": [
                        {"check": "hook_injected", "reason": "missing trust field"},
                    ],
                    "autonomy_config": config.to_dict(),
                },
            )

        # Autonomy mode enforcement.
        if config.mode == "suggest":
            return EngineResponse(
                state="policy_blocked",
                message=f"Autonomy mode 'suggest': agent {action} requires user approval",
                error_code="policy_blocked",
                data={
                    "checks_passed": checks_passed,
                    "checks_failed": [
                        {"check": "autonomy_mode", "reason": "suggest mode blocks agents"},
                    ],
                    "autonomy_config": config.to_dict(),
                },
            )

        if config.mode == "auto_silent":
            return EngineResponse(
                state="policy_blocked",
                message="Autonomy mode 'auto_silent' is not available in v1.0",
                error_code="policy_blocked",
                data={
                    "checks_passed": checks_passed,
                    "checks_failed": [
                        {"check": "autonomy_mode", "reason": "auto_silent gated in v1.0"},
                    ],
                    "autonomy_config": config.to_dict(),
                },
            )

        # auto_audit: check session cap for create actions.
        if config.mode == "auto_audit" and action == "create":
            count = engine_count_session_creates(session_id, tickets_dir)
            if count is AUDIT_UNAVAILABLE:
                return EngineResponse(
                    state="policy_blocked",
                    message="Cannot verify session create count (audit trail unavailable)",
                    error_code="policy_blocked",
                    data={
                        "checks_passed": checks_passed,
                        "checks_failed": [
                            {"check": "session_cap", "reason": "audit unavailable"},
                        ],
                        "autonomy_config": config.to_dict(),
                    },
                )
            if count >= config.max_creates:
                return EngineResponse(
                    state="policy_blocked",
                    message=f"Session create cap reached: {count}/{config.max_creates}",
                    error_code="policy_blocked",
                    data={
                        "checks_passed": checks_passed,
                        "checks_failed": [
                            {"check": "session_cap", "reason": f"{count}/{config.max_creates}"},
                        ],
                        "autonomy_config": config.to_dict(),
                    },
                )
            notification = (
                f"Auto-audit: agent {action} approved "
                f"(session creates: {count}/{config.max_creates})"
            )
        elif config.mode == "auto_audit":
            notification = f"Auto-audit: agent {action} approved"

    checks_passed.append("autonomy_policy")
```

**4c. Update the preflight return to include autonomy_config and notification:**

Replace the final return (line ~473):
```python
    return EngineResponse(
        state="ok",
        message="All preflight checks passed",
        data={"checks_passed": checks_passed, "checks_failed": checks_failed},
    )
```

With:
```python
    response_data: dict[str, Any] = {
        "checks_passed": checks_passed,
        "checks_failed": checks_failed,
        "autonomy_config": config.to_dict(),
    }
    if notification:
        response_data["notification"] = notification
    return EngineResponse(
        state="ok",
        message="All preflight checks passed",
        data=response_data,
    )
```

### Step 5: Implement execute defense-in-depth

**5a. Change `engine_execute` signature:**

Replace:
```python
    autonomy_mode: str = "suggest",
```

With:
```python
    autonomy_config: AutonomyConfig | None = None,
```

**5b. Add config resolution at top of `engine_execute`:**

After the docstring:
```python
    config = autonomy_config or AutonomyConfig()
```

**5c. Remove Phase 1 hard-block (lines 713-720):**

Delete this block entirely:
```python
    # Phase 1: hard-block all agent mutations (defense-in-depth, mirrors preflight).
    # M8: Remove this block. The transport-layer validation below becomes the primary gate.
    if request_origin == "agent":
        return EngineResponse(
            state="policy_blocked",
            message="Phase 1: agent mutations are hard-blocked",
            error_code="policy_blocked",
        )
```

**5d. Add autonomy defense-in-depth after transport validation (after line ~731):**

After the existing transport validation block (`if request_origin == "agent" and not hook_injected:`), add:

```python
    # --- Autonomy defense-in-depth (belt-and-suspenders, self-contained) ---
    # If preflight is bypassed, execute still enforces full autonomy policy.
    # Uses ALLOWLIST semantics: only auto_audit proceeds. All other modes
    # (including unknown/crafted values) are blocked.
    if request_origin == "agent":
        # Mirror preflight action exclusions: reopen is user-only.
        if action == "reopen":
            return EngineResponse(
                state="policy_blocked",
                message="Defense-in-depth: reopen is user-only in v1.0",
                error_code="policy_blocked",
            )

        # Mirror preflight override rejection.
        if dedup_override:
            return EngineResponse(
                state="policy_blocked",
                message="Defense-in-depth: agents cannot use dedup_override",
                error_code="policy_blocked",
            )
        if dependency_override:
            return EngineResponse(
                state="policy_blocked",
                message="Defense-in-depth: agents cannot use dependency_override",
                error_code="policy_blocked",
            )

        # Allowlist: only auto_audit proceeds. Block everything else.
        if config.mode != "auto_audit":
            return EngineResponse(
                state="policy_blocked",
                message=f"Defense-in-depth: autonomy mode {config.mode!r} blocks agent mutations",
                error_code="policy_blocked",
            )

        # auto_audit session cap (with type safety for crafted payloads).
        if action == "create":
            if not isinstance(config.max_creates, int):
                return EngineResponse(
                    state="policy_blocked",
                    message="Defense-in-depth: invalid max_creates type in config",
                    error_code="policy_blocked",
                )
            count = engine_count_session_creates(session_id, tickets_dir)
            if count is AUDIT_UNAVAILABLE or (isinstance(count, int) and count >= config.max_creates):
                return EngineResponse(
                    state="policy_blocked",
                    message=f"Defense-in-depth: session create cap ({config.max_creates})",
                    error_code="policy_blocked",
                )
```

**5e. Update audit entry `autonomy_mode` references:**

In the three audit entry dicts (attempt_started, error, result), replace:
```python
        "autonomy_mode": autonomy_mode,
```

With:
```python
        "autonomy_mode": config.mode,
```

### Step 6: Update entrypoints

In both `ticket_engine_user.py` and `ticket_engine_agent.py`:

**6a. Update imports:**

Add `AutonomyConfig` to the import:
```python
from scripts.ticket_engine_core import (
    AutonomyConfig,
    EngineResponse,
    engine_classify,
    engine_execute,
    engine_plan,
    engine_preflight,
)
```

**6b. Update preflight dispatch to pass `hook_injected` and `dependency_override`:**

```python
    elif subcommand == "preflight":
        return engine_preflight(
            ticket_id=payload.get("ticket_id"),
            action=payload.get("action", ""),
            session_id=payload.get("session_id", ""),
            request_origin=REQUEST_ORIGIN,
            classify_confidence=payload.get("classify_confidence", 0.0),
            classify_intent=payload.get("classify_intent", ""),
            dedup_fingerprint=payload.get("dedup_fingerprint"),
            target_fingerprint=payload.get("target_fingerprint"),
            duplicate_of=payload.get("duplicate_of"),
            dedup_override=payload.get("dedup_override", False),
            dependency_override=payload.get("dependency_override", False),
            hook_injected=payload.get("hook_injected", False),
            tickets_dir=tickets_dir,
        )
```

**6c. Update execute dispatch to pass `autonomy_config`:**

```python
    elif subcommand == "execute":
        config_data = payload.get("autonomy_config")
        autonomy_config = AutonomyConfig.from_dict(config_data) if config_data else None
        return engine_execute(
            action=payload.get("action", ""),
            ticket_id=payload.get("ticket_id"),
            fields=payload.get("fields", {}),
            session_id=payload.get("session_id", ""),
            request_origin=REQUEST_ORIGIN,
            dedup_override=payload.get("dedup_override", False),
            dependency_override=payload.get("dependency_override", False),
            tickets_dir=tickets_dir,
            autonomy_config=autonomy_config,
            hook_injected=payload.get("hook_injected", False),
        )
```

### Step 7: Update existing tests in test_engine.py

Three tests need updating (assertions only, not restructuring):

**7a. `test_agent_hard_blocked_phase1` (line 242):**

Update docstring and assertion — agent is now blocked by suggest mode (default), not Phase 1 hard-block. Agent without `hook_injected` hits the hook check first:

```python
    def test_agent_blocked_without_hook_injected(self, tmp_tickets):
        """Agent without hook_injected → policy_blocked (hook trust check)."""
        resp = engine_preflight(
            ticket_id=None,
            action="create",
            session_id="test-session",
            request_origin="agent",
            classify_confidence=0.95,
            classify_intent="create",
            dedup_fingerprint="abc",
            target_fingerprint=None,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "policy_blocked"
        assert "hook_injected" in resp.message.lower()
```

**7b. `test_agent_reopen_hard_blocked_phase1` (line 258):**

Update to test user-only action exclusion:

```python
    def test_agent_reopen_user_only(self, tmp_tickets):
        """Agent reopen → policy_blocked (user-only in v1.0)."""
        resp = engine_preflight(
            ticket_id="T-20260302-01",
            action="reopen",
            session_id="test-session",
            request_origin="agent",
            classify_confidence=0.95,
            classify_intent="reopen",
            dedup_fingerprint=None,
            target_fingerprint=None,
            tickets_dir=tmp_tickets,
            hook_injected=True,
        )
        assert resp.state == "policy_blocked"
```

**7c. `TestTransportValidation.test_agent_without_hook_injected_rejected` (line 928):**

Update docstring only — behavior same (policy_blocked) but different code path (transport validation, not Phase 1 hard-block):

```python
    def test_agent_without_hook_injected_rejected(self, tmp_tickets):
        """Agent without hook_injected → policy_blocked (transport validation)."""
```

### Step 8: Run tests to verify all pass

```bash
cd packages/plugins/ticket && uv run pytest -v
```

Expected: 201 existing + 22 new autonomy tests (12 config + 12 preflight + 9 execute, minus 3 updated) = ~222 tests PASS.

### Step 9: Commit

```bash
git add scripts/ticket_engine_core.py scripts/ticket_engine_user.py scripts/ticket_engine_agent.py tests/test_autonomy.py tests/test_engine.py
git commit -m "feat: replace Phase 1 agent hard-block with autonomy enforcement modes"
```

---

## Task 10a: Core Triage Dashboard

**Files:**
- Create: `scripts/ticket_triage.py`
- Create: `tests/test_triage.py`

**Dependencies:** None (independent of Tasks 8-9).

### Step 1: Write failing tests

Create `tests/test_triage.py`:

```python
"""Tests for the triage analysis script."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from tests.conftest import make_ticket


class TestDashboard:
    """Test triage_dashboard counts and alerts."""

    @pytest.fixture
    def populated_tickets(self, tmp_tickets):
        """Create a mix of tickets for dashboard testing."""
        make_ticket(tmp_tickets, "t1.md", id="T-20260302-01", status="open")
        make_ticket(tmp_tickets, "t2.md", id="T-20260302-02", status="in_progress")
        make_ticket(tmp_tickets, "t3.md", id="T-20260302-03", status="blocked",
                    blocked_by=["T-20260302-01"])
        make_ticket(tmp_tickets, "t4.md", id="T-20260302-04", status="done")
        return tmp_tickets

    def test_status_counts(self, populated_tickets):
        from scripts.ticket_triage import triage_dashboard
        result = triage_dashboard(populated_tickets)
        assert result["counts"]["open"] == 1
        assert result["counts"]["in_progress"] == 1
        assert result["counts"]["blocked"] == 1
        # list_tickets(include_closed=False) returns all tickets in the active
        # directory regardless of status. total filters to non-terminal statuses.
        assert result["total"] == 3  # open + in_progress + blocked (done excluded by filter)

    def test_empty_directory(self, tmp_tickets):
        from scripts.ticket_triage import triage_dashboard
        result = triage_dashboard(tmp_tickets)
        assert result["total"] == 0
        assert result["stale"] == []


class TestStaleDetection:
    """Test stale ticket detection."""

    def test_stale_ticket_detected(self, tmp_tickets):
        """Ticket older than 7 days in open status → stale."""
        old_date = (datetime.now(timezone.utc) - timedelta(days=10)).strftime("%Y-%m-%d")
        make_ticket(tmp_tickets, "old.md", id="T-20260220-01", date=old_date, status="open")
        from scripts.ticket_triage import triage_dashboard
        result = triage_dashboard(tmp_tickets)
        assert len(result["stale"]) == 1
        assert result["stale"][0]["id"] == "T-20260220-01"

    def test_recent_ticket_not_stale(self, tmp_tickets):
        """Ticket from today → not stale."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        make_ticket(tmp_tickets, "new.md", id="T-20260302-01", date=today, status="open")
        from scripts.ticket_triage import triage_dashboard
        result = triage_dashboard(tmp_tickets)
        assert result["stale"] == []

    def test_done_ticket_not_stale(self, tmp_tickets):
        """Done tickets are never stale (regardless of age)."""
        old_date = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
        make_ticket(tmp_tickets, "done.md", id="T-20260201-01", date=old_date, status="done")
        from scripts.ticket_triage import triage_dashboard
        result = triage_dashboard(tmp_tickets)
        assert result["stale"] == []


class TestBlockedChain:
    """Test blocked chain analysis."""

    def test_root_blocker_found(self, tmp_tickets):
        """Follow blocked_by chain to find root blocker."""
        make_ticket(tmp_tickets, "root.md", id="T-20260302-01", status="open")
        make_ticket(tmp_tickets, "mid.md", id="T-20260302-02", status="blocked",
                    blocked_by=["T-20260302-01"])
        make_ticket(tmp_tickets, "leaf.md", id="T-20260302-03", status="blocked",
                    blocked_by=["T-20260302-02"])
        from scripts.ticket_triage import triage_dashboard
        result = triage_dashboard(tmp_tickets)
        chains = {c["id"]: c for c in result["blocked_chains"]}
        assert "T-20260302-03" in chains
        assert "T-20260302-01" in chains["T-20260302-03"]["root_blockers"]

    def test_missing_blocker_is_root(self, tmp_tickets):
        """Blocker not found in ticket map → treated as root."""
        make_ticket(tmp_tickets, "blocked.md", id="T-20260302-01", status="blocked",
                    blocked_by=["T-MISSING-01"])
        from scripts.ticket_triage import triage_dashboard
        result = triage_dashboard(tmp_tickets)
        assert result["blocked_chains"][0]["root_blockers"] == ["T-MISSING-01"]

    def test_circular_dependency_no_infinite_loop(self, tmp_tickets):
        """Circular blocked_by chain → visited set prevents infinite loop, empty roots."""
        make_ticket(tmp_tickets, "a.md", id="T-20260302-01", status="blocked",
                    blocked_by=["T-20260302-02"])
        make_ticket(tmp_tickets, "b.md", id="T-20260302-02", status="blocked",
                    blocked_by=["T-20260302-01"])
        from scripts.ticket_triage import triage_dashboard
        result = triage_dashboard(tmp_tickets)
        # Both are blocked with circular deps. The visited set prevents loops.
        # Root blockers will be empty for pure cycles (no unblocked root found).
        chains = {c["id"]: c for c in result["blocked_chains"]}
        assert len(chains) == 2
        # No infinite loop occurred — test completes.


class TestDocSize:
    """Test document size warnings."""

    def test_large_doc_strong_warning(self, tmp_tickets):
        """Ticket >32KB → strong_warn."""
        path = make_ticket(tmp_tickets, "big.md", id="T-20260302-01")
        # Pad file to >32KB.
        with open(path, "a") as f:
            f.write("x" * 33000)
        from scripts.ticket_triage import triage_dashboard
        result = triage_dashboard(tmp_tickets)
        assert len(result["size_warnings"]) == 1
        assert "strong_warn" in result["size_warnings"][0]["warning"]

    def test_medium_doc_warning(self, tmp_tickets):
        """Ticket >16KB but <32KB → warn."""
        path = make_ticket(tmp_tickets, "med.md", id="T-20260302-01")
        with open(path, "a") as f:
            f.write("x" * 17000)
        from scripts.ticket_triage import triage_dashboard
        result = triage_dashboard(tmp_tickets)
        assert len(result["size_warnings"]) == 1
        assert "warn" in result["size_warnings"][0]["warning"]
        assert "strong" not in result["size_warnings"][0]["warning"]

    def test_normal_doc_no_warning(self, tmp_tickets):
        """Normal-sized ticket → no warning."""
        make_ticket(tmp_tickets, "normal.md", id="T-20260302-01")
        from scripts.ticket_triage import triage_dashboard
        result = triage_dashboard(tmp_tickets)
        assert result["size_warnings"] == []
```

### Step 2: Run tests to verify they fail

```bash
cd packages/plugins/ticket && uv run pytest tests/test_triage.py -v -k "Dashboard or Stale or Blocked or DocSize"
```

Expected: `ModuleNotFoundError` — `ticket_triage` doesn't exist.

### Step 3: Implement core triage script

Create `scripts/ticket_triage.py`:

```python
"""Ticket triage — read-only analysis of ticket health and audit activity."""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


_TERMINAL_STATUSES = frozenset({"done", "wontfix"})


def triage_dashboard(tickets_dir: Path) -> dict[str, Any]:
    """Generate a triage dashboard with ticket counts and alerts.

    Filters to non-terminal statuses (excludes done/wontfix).
    list_tickets(include_closed=False) returns all tickets in the active
    directory regardless of status field — filtering by status is our job.
    Returns dict with: counts, total, stale, blocked_chains, size_warnings.
    """
    from scripts.ticket_read import list_tickets

    all_tickets = list_tickets(tickets_dir, include_closed=False)
    # Filter to actionable tickets (non-terminal status).
    tickets = [t for t in all_tickets if t.status not in _TERMINAL_STATUSES]
    ticket_map = {t.id: t for t in tickets}

    counts: dict[str, int] = {"open": 0, "in_progress": 0, "blocked": 0}
    stale: list[dict[str, str]] = []
    blocked_chains: list[dict[str, Any]] = []
    size_warnings: list[dict[str, str]] = []

    for ticket in tickets:
        # Count by status.
        if ticket.status in counts:
            counts[ticket.status] += 1

        # Stale detection: open/in_progress > 7 days.
        if _is_stale(ticket):
            stale.append({"id": ticket.id, "status": ticket.status, "date": ticket.date})

        # Blocked chain analysis.
        if ticket.status == "blocked" and ticket.blocked_by:
            root_blockers = _find_root_blockers(ticket, ticket_map)
            blocked_chains.append({"id": ticket.id, "root_blockers": root_blockers})

        # Doc size warnings.
        warning = _check_doc_size(ticket)
        if warning:
            size_warnings.append({"id": ticket.id, "warning": warning})

    return {
        "counts": counts,
        "total": len(tickets),
        "stale": stale,
        "blocked_chains": blocked_chains,
        "size_warnings": size_warnings,
    }


def _is_stale(ticket: Any, cutoff_days: int = 7) -> bool:
    """Check if ticket is stale (open/in_progress >7 days by ticket date).

    v1.0: uses ticket.date as proxy for activity. Activity-based stale
    detection (via updated_at or audit trail) deferred to future version.
    """
    if ticket.status not in ("open", "in_progress"):
        return False
    try:
        ticket_date = datetime.strptime(ticket.date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - ticket_date).days > cutoff_days
    except ValueError:
        return False


def _find_root_blockers(ticket: Any, ticket_map: dict[str, Any]) -> list[str]:
    """Follow blocked_by chains to find root blockers."""
    visited: set[str] = set()
    roots: list[str] = []

    def _walk(tid: str) -> None:
        if tid in visited:
            return
        visited.add(tid)
        t = ticket_map.get(tid)
        if t is None or not t.blocked_by:
            roots.append(tid)
            return
        for bid in t.blocked_by:
            _walk(bid)

    for bid in ticket.blocked_by:
        _walk(bid)
    return roots


def _check_doc_size(ticket: Any) -> str | None:
    """Check ticket document size, return warning string if large."""
    try:
        size = Path(ticket.path).stat().st_size
    except OSError:
        return None
    if size >= 32768:
        return f"strong_warn: {size // 1024}KB (>32KB)"
    if size >= 16384:
        return f"warn: {size // 1024}KB (>16KB)"
    return None
```

### Step 4: Run tests to verify they pass

```bash
cd packages/plugins/ticket && uv run pytest tests/test_triage.py -v -k "Dashboard or Stale or Blocked or DocSize"
```

Expected: 11 tests PASS.

### Step 5: Commit

```bash
git add scripts/ticket_triage.py tests/test_triage.py
git commit -m "feat: add core triage dashboard with stale/blocked/size analysis"
```

---

## Task 10b: Audit Trail Reader

**Files:**
- Modify: `scripts/ticket_triage.py`
- Add to: `tests/test_triage.py`

**Dependencies:** Task 10a complete.

### Step 1: Write failing tests

Add to `tests/test_triage.py`:

```python
class TestAuditReport:
    """Test audit trail report generation."""

    @pytest.fixture
    def audit_env(self, tmp_tickets):
        """Create audit trail with sample entries."""
        date_dir = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        audit_dir = tmp_tickets / ".audit" / date_dir
        audit_dir.mkdir(parents=True)

        # Session 1: 2 creates, 1 update.
        s1_file = audit_dir / "session-1.jsonl"
        entries = [
            {"action": "create", "result": "ok_create", "session_id": "session-1"},
            {"action": "create", "result": "ok_create", "session_id": "session-1"},
            {"action": "update", "result": "ok_update", "session_id": "session-1"},
        ]
        s1_file.write_text("\n".join(json.dumps(e) for e in entries) + "\n")

        # Session 2: 1 blocked attempt.
        s2_file = audit_dir / "session-2.jsonl"
        s2_file.write_text(json.dumps(
            {"action": "create", "result": "policy_blocked", "session_id": "session-2"}
        ) + "\n")

        return tmp_tickets

    def test_total_entries_counted(self, audit_env):
        from scripts.ticket_triage import triage_audit_report
        result = triage_audit_report(audit_env)
        assert result["total_entries"] == 4

    def test_by_action_aggregation(self, audit_env):
        from scripts.ticket_triage import triage_audit_report
        result = triage_audit_report(audit_env)
        assert result["by_action"]["create"] == 3
        assert result["by_action"]["update"] == 1

    def test_by_result_aggregation(self, audit_env):
        from scripts.ticket_triage import triage_audit_report
        result = triage_audit_report(audit_env)
        assert result["by_result"]["ok_create"] == 2
        assert result["by_result"]["policy_blocked"] == 1

    def test_session_count(self, audit_env):
        from scripts.ticket_triage import triage_audit_report
        result = triage_audit_report(audit_env)
        assert result["sessions"] == 2

    def test_no_audit_dir_returns_empty(self, tmp_tickets):
        from scripts.ticket_triage import triage_audit_report
        result = triage_audit_report(tmp_tickets)
        assert result["total_entries"] == 0
        assert result["sessions"] == 0
```

### Step 2: Run tests to verify they fail

```bash
cd packages/plugins/ticket && uv run pytest tests/test_triage.py::TestAuditReport -v
```

Expected: `ImportError` — `triage_audit_report` doesn't exist.

### Step 3: Implement audit trail reader

Add to `scripts/ticket_triage.py`:

```python
def triage_audit_report(tickets_dir: Path, days: int = 7) -> dict[str, Any]:
    """Summarize recent autonomous actions from audit trail.

    Reads .audit/YYYY-MM-DD/<session_id>.jsonl files within the lookback window.
    Returns dict with: total_entries, by_action, by_result, sessions.
    """
    audit_base = tickets_dir / ".audit"
    if not audit_base.is_dir():
        return {"total_entries": 0, "by_action": {}, "by_result": {}, "sessions": 0}

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    entries: list[dict[str, Any]] = []
    session_ids: set[str] = set()

    for date_dir in sorted(audit_base.iterdir()):
        if not date_dir.is_dir():
            continue
        try:
            dir_date = datetime.strptime(date_dir.name, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        if dir_date < cutoff:
            continue
        for jsonl_file in date_dir.glob("*.jsonl"):
            session_ids.add(jsonl_file.stem)
            try:
                for line in jsonl_file.read_text(encoding="utf-8").strip().split("\n"):
                    if not line.strip():
                        continue
                    try:
                        entries.append(json.loads(line))
                    except (json.JSONDecodeError, ValueError):
                        continue
            except OSError:
                continue

    by_action: dict[str, int] = {}
    by_result: dict[str, int] = {}
    for entry in entries:
        action = entry.get("action", "unknown")
        by_action[action] = by_action.get(action, 0) + 1
        result = entry.get("result")
        if result is not None:
            by_result[str(result)] = by_result.get(str(result), 0) + 1

    return {
        "total_entries": len(entries),
        "by_action": by_action,
        "by_result": by_result,
        "sessions": len(session_ids),
    }
```

### Step 4: Run tests to verify they pass

```bash
cd packages/plugins/ticket && uv run pytest tests/test_triage.py::TestAuditReport -v
```

Expected: 5 tests PASS.

### Step 5: Commit

```bash
git add scripts/ticket_triage.py tests/test_triage.py
git commit -m "feat: add audit trail reader to triage script"
```

---

## Task 10c: Orphan Detection

**Files:**
- Modify: `scripts/ticket_triage.py`
- Add to: `tests/test_triage.py`

**Dependencies:** Task 10a complete.

**Note:** Adapts matching strategies from `packages/plugins/handoff/scripts/triage.py` — NOT the canonical spec's "text-similarity" description. Three strategies: `uid_match` (session ID), `id_ref` (ticket ID in text), `manual_review` (fallback).

**Intentional simplification vs handoff triage.py:** The handoff triage operates at per-extracted-item granularity (`extract_handoff_items()` + per-item `match_orphan_item()`), while this implementation matches at whole-file level. This is acceptable for v1.0 because: (1) handoff files are small enough that whole-file matching has no false positive risk for session IDs (UUIDs don't collide), (2) ticket ID regex matching is deterministic regardless of granularity, (3) the manual_review fallback catches any missed edge cases. The session matching uses substring containment (`if sid in text`) rather than equality-based `session_matches()` — equivalent for UUID-format session IDs.

### Step 1: Write failing tests

Add to `tests/test_triage.py`:

```python
class TestOrphanDetection:
    """Test handoff orphan detection with three matching strategies."""

    @pytest.fixture
    def orphan_env(self, tmp_path):
        """Set up tickets and handoffs directories."""
        tickets_dir = tmp_path / "docs" / "tickets"
        tickets_dir.mkdir(parents=True)
        handoffs_dir = tmp_path / "handoffs"
        handoffs_dir.mkdir()
        return tickets_dir, handoffs_dir

    def test_uid_match_by_session(self, orphan_env):
        """Handoff matching ticket's source.session → uid_match."""
        tickets_dir, handoffs_dir = orphan_env
        make_ticket(tickets_dir, "t1.md", id="T-20260302-01", session="session-abc")
        (handoffs_dir / "handoff-1.md").write_text(
            "# Handoff\nSession session-abc produced this work.\n"
        )
        from scripts.ticket_triage import triage_orphan_detection
        result = triage_orphan_detection(tickets_dir, handoffs_dir)
        assert len(result["matched"]) == 1
        assert result["matched"][0]["match_type"] == "uid_match"
        assert result["matched"][0]["matched_ticket"] == "T-20260302-01"

    def test_id_ref_match(self, orphan_env):
        """Handoff mentioning ticket ID → id_ref match."""
        tickets_dir, handoffs_dir = orphan_env
        make_ticket(tickets_dir, "t1.md", id="T-20260302-01")
        (handoffs_dir / "handoff-1.md").write_text(
            "# Handoff\nRelated to T-20260302-01.\n"
        )
        from scripts.ticket_triage import triage_orphan_detection
        result = triage_orphan_detection(tickets_dir, handoffs_dir)
        assert len(result["matched"]) == 1
        assert result["matched"][0]["match_type"] == "id_ref"

    def test_manual_review_fallback(self, orphan_env):
        """Handoff with no matching ticket → manual_review."""
        tickets_dir, handoffs_dir = orphan_env
        (handoffs_dir / "handoff-1.md").write_text(
            "# Handoff\nSome unrelated work.\n"
        )
        from scripts.ticket_triage import triage_orphan_detection
        result = triage_orphan_detection(tickets_dir, handoffs_dir)
        assert len(result["orphaned"]) == 1
        assert result["orphaned"][0]["match_type"] == "manual_review"

    def test_no_handoffs_dir(self, tmp_tickets):
        """Missing handoffs directory → empty results."""
        from scripts.ticket_triage import triage_orphan_detection
        result = triage_orphan_detection(tmp_tickets, Path("/nonexistent"))
        assert result["total_items"] == 0

    def test_uid_match_takes_priority_over_id_ref(self, orphan_env):
        """uid_match is checked before id_ref — first match wins."""
        tickets_dir, handoffs_dir = orphan_env
        make_ticket(tickets_dir, "t1.md", id="T-20260302-01", session="session-xyz")
        (handoffs_dir / "handoff-1.md").write_text(
            "# Handoff\nSession session-xyz about T-20260302-01.\n"
        )
        from scripts.ticket_triage import triage_orphan_detection
        result = triage_orphan_detection(tickets_dir, handoffs_dir)
        assert len(result["matched"]) == 1
        assert result["matched"][0]["match_type"] == "uid_match"
```

### Step 2: Run tests to verify they fail

```bash
cd packages/plugins/ticket && uv run pytest tests/test_triage.py::TestOrphanDetection -v
```

Expected: `ImportError` — `triage_orphan_detection` doesn't exist.

### Step 3: Implement orphan detection

Add to `scripts/ticket_triage.py`:

```python
# Ticket ID patterns for id_ref matching (from handoff triage.py).
_TICKET_ID_PATTERNS = [
    re.compile(r"T-\d{8}-\d{2,}"),  # v1.0: T-YYYYMMDD-NN
    re.compile(r"T-\d{3}"),          # Gen 3: T-NNN
    re.compile(r"T-[A-F]"),          # Gen 2: T-X
]


def triage_orphan_detection(
    tickets_dir: Path,
    handoffs_dir: Path,
) -> dict[str, Any]:
    """Detect orphaned handoff items not linked to any ticket.

    Three matching strategies (ported from handoff triage.py):
    1. uid_match: handoff text contains ticket's source.session
    2. id_ref: handoff text contains a ticket ID
    3. manual_review: no deterministic match
    """
    from scripts.ticket_read import list_tickets

    tickets = list_tickets(tickets_dir, include_closed=True)
    ticket_ids = {t.id for t in tickets}
    session_map: dict[str, str] = {}  # session_id → ticket_id
    for t in tickets:
        sid = t.source.get("session", "")
        if sid:
            session_map[sid] = t.id

    matched: list[dict[str, Any]] = []
    orphaned: list[dict[str, Any]] = []

    if not handoffs_dir.is_dir():
        return {"matched": matched, "orphaned": orphaned, "total_items": 0}

    for hf in sorted(handoffs_dir.glob("*.md")):
        try:
            text = hf.read_text(encoding="utf-8")
        except OSError:
            continue

        item: dict[str, str] = {"file": hf.name, "path": str(hf)}
        match_found = False

        # Strategy 1: uid_match — session ID in handoff text.
        for sid, tid in session_map.items():
            if sid in text:
                matched.append({"match_type": "uid_match", "matched_ticket": tid, "item": item})
                match_found = True
                break

        if match_found:
            continue

        # Strategy 2: id_ref — ticket ID referenced in handoff text.
        for pattern in _TICKET_ID_PATTERNS:
            refs = pattern.findall(text)
            for ref in refs:
                if ref in ticket_ids:
                    matched.append({"match_type": "id_ref", "matched_ticket": ref, "item": item})
                    match_found = True
                    break
            if match_found:
                break

        if match_found:
            continue

        # Strategy 3: manual_review — no deterministic match.
        orphaned.append({"match_type": "manual_review", "matched_ticket": None, "item": item})

    return {
        "matched": matched,
        "orphaned": orphaned,
        "total_items": len(matched) + len(orphaned),
    }
```

### Step 4: Run tests to verify they pass

```bash
cd packages/plugins/ticket && uv run pytest tests/test_triage.py::TestOrphanDetection -v
```

Expected: 5 tests PASS.

### Step 5: Run full triage test suite

```bash
cd packages/plugins/ticket && uv run pytest tests/test_triage.py -v
```

Expected: 21 triage tests PASS.

### Step 6: Commit

```bash
git add scripts/ticket_triage.py tests/test_triage.py
git commit -m "feat: add orphan detection with uid_match/id_ref/manual_review strategies"
```

---

## Task 11: Autonomy Integration Tests

**Files:**
- Create: `tests/test_autonomy_integration.py`

**Dependencies:** Tasks 8, 9 complete.

### Step 1: Write integration tests

Create `tests/test_autonomy_integration.py`:

```python
"""Integration tests: config → preflight → execute → audit trail."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from scripts.ticket_engine_core import (
    AutonomyConfig,
    engine_count_session_creates,
    engine_execute,
    engine_preflight,
    read_autonomy_config,
)


@pytest.fixture
def integration_env(tmp_path: Path):
    """Full integration environment: .claude config + tickets dir."""
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    tickets_dir = tmp_path / "docs" / "tickets"
    tickets_dir.mkdir(parents=True)
    config_path = claude_dir / "ticket.local.md"
    return tickets_dir, config_path


class TestAutonomyIntegration:
    """End-to-end: config → preflight → execute → audit."""

    def test_suggest_mode_blocks_agent_create(self, integration_env):
        """Full flow: default suggest mode → preflight blocks → no execute."""
        tickets_dir, _ = integration_env  # No config file → suggest

        resp = engine_preflight(
            ticket_id=None,
            action="create",
            session_id="int-session",
            request_origin="agent",
            classify_confidence=0.95,
            classify_intent="create",
            dedup_fingerprint="fp1",
            target_fingerprint=None,
            tickets_dir=tickets_dir,
            hook_injected=True,
        )
        assert resp.state == "policy_blocked"
        assert resp.data["autonomy_config"]["mode"] == "suggest"

    def test_auto_audit_full_create_flow(self, integration_env):
        """Full flow: auto_audit → preflight ok → execute creates → audit recorded."""
        tickets_dir, config_path = integration_env
        config_path.write_text("---\nautonomy_mode: auto_audit\nmax_creates_per_session: 5\n---\n")

        # Preflight.
        pf_resp = engine_preflight(
            ticket_id=None,
            action="create",
            session_id="int-session",
            request_origin="agent",
            classify_confidence=0.95,
            classify_intent="create",
            dedup_fingerprint="fp1",
            target_fingerprint=None,
            tickets_dir=tickets_dir,
            hook_injected=True,
        )
        assert pf_resp.state == "ok"
        config_snapshot = pf_resp.data["autonomy_config"]
        assert "notification" in pf_resp.data

        # Execute with snapshot.
        config = AutonomyConfig.from_dict(config_snapshot)
        ex_resp = engine_execute(
            action="create",
            ticket_id=None,
            fields={"title": "Auto-created", "problem": "Agent found an issue"},
            session_id="int-session",
            request_origin="agent",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tickets_dir,
            autonomy_config=config,
            hook_injected=True,
        )
        assert ex_resp.state == "ok_create"

        # Verify audit trail recorded.
        count = engine_count_session_creates("int-session", tickets_dir)
        assert count == 1

    def test_auto_audit_session_cap_enforced(self, integration_env):
        """Full flow: auto_audit cap reached → preflight blocks."""
        tickets_dir, config_path = integration_env
        config_path.write_text("---\nautonomy_mode: auto_audit\nmax_creates_per_session: 2\n---\n")

        # Create 2 tickets (reaching the cap).
        for i in range(2):
            config = AutonomyConfig(mode="auto_audit", max_creates=2)
            engine_execute(
                action="create",
                ticket_id=None,
                fields={"title": f"Ticket {i}", "problem": "Issue"},
                session_id="cap-session",
                request_origin="agent",
                dedup_override=False,
                dependency_override=False,
                tickets_dir=tickets_dir,
                autonomy_config=config,
                hook_injected=True,
            )

        # Third create should be blocked by preflight.
        resp = engine_preflight(
            ticket_id=None,
            action="create",
            session_id="cap-session",
            request_origin="agent",
            classify_confidence=0.95,
            classify_intent="create",
            dedup_fingerprint="fp3",
            target_fingerprint=None,
            tickets_dir=tickets_dir,
            hook_injected=True,
        )
        assert resp.state == "policy_blocked"
        assert "cap" in resp.message.lower() or "2/2" in resp.message

    def test_user_unaffected_by_autonomy_config(self, integration_env):
        """User operations pass regardless of autonomy config."""
        tickets_dir, config_path = integration_env
        # Even auto_silent (which blocks agents) doesn't affect users.
        config_path.write_text("---\nautonomy_mode: auto_silent\n---\n")

        resp = engine_preflight(
            ticket_id=None,
            action="create",
            session_id="user-session",
            request_origin="user",
            classify_confidence=0.95,
            classify_intent="create",
            dedup_fingerprint="fp1",
            target_fingerprint=None,
            tickets_dir=tickets_dir,
        )
        assert resp.state == "ok"

        ex_resp = engine_execute(
            action="create",
            ticket_id=None,
            fields={"title": "User ticket", "problem": "User issue"},
            session_id="user-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tickets_dir,
        )
        assert ex_resp.state == "ok_create"

    def test_config_snapshot_prevents_toctou(self, integration_env):
        """Config snapshot from preflight is used in execute, not re-read."""
        tickets_dir, config_path = integration_env
        config_path.write_text("---\nautonomy_mode: auto_audit\nmax_creates_per_session: 5\n---\n")

        # Preflight reads auto_audit.
        pf_resp = engine_preflight(
            ticket_id=None,
            action="create",
            session_id="toctou-session",
            request_origin="agent",
            classify_confidence=0.95,
            classify_intent="create",
            dedup_fingerprint="fp1",
            target_fingerprint=None,
            tickets_dir=tickets_dir,
            hook_injected=True,
        )
        assert pf_resp.state == "ok"
        snapshot = AutonomyConfig.from_dict(pf_resp.data["autonomy_config"])
        assert snapshot.mode == "auto_audit"

        # Config changes to suggest between preflight and execute.
        config_path.write_text("---\nautonomy_mode: suggest\n---\n")

        # Execute uses snapshot (auto_audit) → proceeds.
        ex_resp = engine_execute(
            action="create",
            ticket_id=None,
            fields={"title": "TOCTOU test", "problem": "Testing snapshot"},
            session_id="toctou-session",
            request_origin="agent",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tickets_dir,
            autonomy_config=snapshot,
            hook_injected=True,
        )
        assert ex_resp.state == "ok_create"
```

### Step 2: Run tests to verify they pass

```bash
cd packages/plugins/ticket && uv run pytest tests/test_autonomy_integration.py -v
```

Expected: 5 tests PASS (these test the full implemented flow, so they should pass if Tasks 8-9 are done).

### Step 3: Run full test suite

```bash
cd packages/plugins/ticket && uv run pytest -v
```

Expected: 201 prior + 34 (T8/T9) + 21 (T10a/b/c) + 5 (T11) = **261 tests PASS**.

### Step 4: Commit

```bash
git add tests/test_autonomy_integration.py
git commit -m "test: add integration tests for autonomy config → preflight → execute → audit flow"
```

---

## Gate Card

| Check | Expected |
|-------|----------|
| All tests pass | 261 tests (201 + 60 new) |
| Phase 1 hard-block removed | Preflight + execute use autonomy modes |
| `_read_autonomy_mode` replaced | `read_autonomy_config` with warnings |
| `hook_injected` on preflight | Parameter added, wired in entrypoints |
| Snapshot pattern working | Preflight → response data → execute |
| Execute defense allowlist | Only `auto_audit` proceeds; unknown modes blocked |
| Execute mirrors preflight | Action exclusions + override rejection in execute |
| max_creates=0 accepted | Disables agent creates (not treated as invalid) |
| Triage dashboard | Counts (non-terminal only), stale, blocked chains, doc size |
| Audit report | Action/result aggregation, session count |
| Orphan detection | uid_match, id_ref, manual_review (file-level, documented) |
| No regressions | All 201 prior tests pass |
| Entrypoints updated | Both user + agent pass new params |

## Execution Notes

- **Task ordering:** T8 → T9 → T10a → T10b → T10c → T11 (T10a-c are independent of T8-9 but sequential among themselves)
- **Existing test updates (T9):** Three tests in `test_engine.py` need assertion updates — they test the same behavioral boundary but the error messages change.
- **Flaky test policy (standing directive):** If you notice a flaky test during execution, fix it immediately regardless of scope.
- **Pyright in worktrees:** Diagnostics may be stale. Verify with grep + test run.
- **`_read_autonomy_mode` callers:** Grep for `_read_autonomy_mode` before removing. If any callers exist, update them to use `read_autonomy_config().mode`.

## Codex Review Fixes Applied

This plan was reviewed via deep-review Codex dialogue (5 turns, evaluative posture). All P0, P1, and P2 findings were addressed:

| Finding | Severity | Fix |
|---------|----------|-----|
| Execute defense fail-open for unknown modes | P0 | Replaced blocklist with allowlist: only `auto_audit` proceeds |
| `max_creates=0` silently expands to 5 | P0 | Changed validation from `< 1` to `< 0`; added test for 0 |
| Execute defense missing action/override mirroring | P0 | Added reopen exclusion + dedup/dependency override rejection to execute |
| Dashboard `total==3` deterministic failure | P1 | Filter by non-terminal status before counting |
| Orphan detection granularity diverges | P1 | Documented as intentional simplification with rationale |
| Execute `autonomy_config=None` untested | P1 | Added `test_execute_agent_none_config_blocked` |
| No frontmatter delimiter warnings | P2 | Added warnings for missing/incomplete `---` delimiters |
| Stale detection uses ticket date | P2 | Updated docstring; activity-based detection deferred |
| Circular dependency gap | P2 | Added `test_circular_dependency_no_infinite_loop` |
| `max_creates` type validation | P2 | Added type check in execute defense + `test_execute_agent_max_creates_type_safety` |
