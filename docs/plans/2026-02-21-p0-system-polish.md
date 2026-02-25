# P0 System Polish Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete the 6 P0 polish items identified by the Codex system-wide evaluative dialogue before starting E-LEARNING.

**Architecture:** Six independent-to-loosely-dependent tasks spanning Python code (emit_analytics.py, new event reader), instruction documents (SKILL.md, agent .md), and reference docs (consultation-contract.md). Tasks 1-2 are XS foundational fixes. Tasks 3-5 are S-effort feature additions. Task 6 is M-effort test infrastructure that validates all prior tasks.

**Tech Stack:** Python 3.12, pytest, ruff, markdown instruction documents

**Reference:** Codex dialogue synthesis from 2026-02-21 session (PR #21 merged at `a12b87f`). Enhancement spec: `docs/plans/2026-02-19-cross-model-plugin-enhancements.md`.

**Adversarial review (2026-02-21):** 6-turn Codex adversarial dialogue reviewed this plan. 11 fixes applied: 2 critical (convergence assertion, section count atomicity), 5 high (reverse invariant test, stale comment, insertion pinning, S17 stubs, docstring update), 4 medium (commit prefix, parity tests, mkdir, baseline count). Thread: `019c81d9-6043-7fe1-833f-c0ba56afc7d8`.

**Branch:** Create `feature/p0-system-polish` from `main`.

**Test command:** `cd packages/plugins/cross-model && uv run pytest ../../../tests/ -v`

**Dependencies between tasks:**
- Task 1 (resolver symmetry): independent — foundational XS fix
- Task 2 (episode linkage freeze): independent — foundational XS fix
- Task 3 (mode truthfulness): independent — instruction doc changes + analytics test
- Task 4 (event reader): independent — new module + tests
- Task 5 (contract learning section): independent — reference doc + contract sync update
- Task 6 (replay conformance tests): depends on Tasks 1-3 (tests validate their fixes)

---

## Task 1: Resolver symmetry for `consultation_outcome` [XS]

**Files:**
- Modify: `packages/plugins/cross-model/scripts/emit_analytics.py:413-434`
- Modify: `tests/test_emit_analytics.py` (TestBuildConsultationOutcome)

**Step 1: Write the failing test**

Add to `TestBuildConsultationOutcome` in `tests/test_emit_analytics.py` (after `test_mode_from_pipeline` at ~line 677):

```python
def test_schema_version_uses_resolver(self) -> None:
    """consultation_outcome uses _resolve_schema_version like dialogue_outcome."""
    pipeline = {
        "posture": "collaborative",
        "thread_id": "thread-xyz-789",
        "turn_count": 1,
        "turn_budget": 1,
        "profile_name": None,
        "mode": "server_assisted",
        "provenance_unknown_count": 0,
    }
    event = MODULE.build_consultation_outcome(_consultation_input(pipeline))
    # With provenance_unknown_count=0 (non-negative int), resolver returns 0.2.0
    assert event["schema_version"] == "0.2.0"
```

**Step 2: Run test to verify it fails**

Run: `cd packages/plugins/cross-model && uv run pytest ../../../tests/test_emit_analytics.py::TestBuildConsultationOutcome::test_schema_version_uses_resolver -v`
Expected: FAIL — currently hardcodes `"0.1.0"`

**Step 3: Fix `build_consultation_outcome` to use the resolver**

In `packages/plugins/cross-model/scripts/emit_analytics.py`, replace lines 413-434:

```python
def build_consultation_outcome(input_data: dict) -> dict:
    """Build a consultation_outcome event from input JSON."""
    pipeline = input_data.get("pipeline", {})

    event = {
        "schema_version": _SCHEMA_VERSION,  # placeholder; resolved below
        "consultation_id": str(uuid.uuid4()),
        "thread_id": pipeline.get("thread_id"),
        "session_id": _session_id(),
        "event": "consultation_outcome",
        "ts": _ts(),
        "posture": pipeline.get("posture"),
        "turn_count": pipeline.get("turn_count", 1),
        "turn_budget": pipeline.get("turn_budget", 1),
        "profile_name": pipeline.get("profile_name"),
        "mode": pipeline.get("mode", "server_assisted"),
        "converged": None,
        "termination_reason": "complete",
        # Nullable feature-flag fields (propagated from pipeline when present)
        "provenance_unknown_count": pipeline.get("provenance_unknown_count"),
        "question_shaped": pipeline.get("question_shaped"),
        "shape_confidence": pipeline.get("shape_confidence"),
        "assumptions_generated_count": pipeline.get("assumptions_generated_count"),
        "ambiguity_count": pipeline.get("ambiguity_count"),
    }

    # Schema version auto-bump: unified resolver (same as build_dialogue_outcome)
    event["schema_version"] = _resolve_schema_version(event)

    return event
```

Key change: (1) Replaced hardcoded `_SCHEMA_VERSION` with resolver call. (2) Added nullable feature-flag fields so the resolver can inspect them. (3) Removed the comment about "must call _resolve_schema_version" — it now does.

**Step 4: Update `test_schema_version_base` to remain valid**

The existing test at line 654-657 asserts `schema_version == "0.1.0"`. This should still pass because the default `_consultation_input()` fixture has no provenance/planning fields — the resolver will return `"0.1.0"`.

Also update the stale comment/docstring in this test: change "Consultation events always use base schema 0.1.0" to "Consultation events default to base schema 0.1.0 when feature-flag fields are absent."

Verify: `cd packages/plugins/cross-model && uv run pytest ../../../tests/test_emit_analytics.py::TestBuildConsultationOutcome::test_schema_version_base -v`
Expected: PASS (no feature flags in default fixture → resolver returns 0.1.0)

**Step 5: Update `test_field_count`**

The existing test asserts `len(event) == 13`. With the new nullable fields (provenance_unknown_count, question_shaped, shape_confidence, assumptions_generated_count, ambiguity_count), the count increases to 18.

Update in `tests/test_emit_analytics.py` at line 633-635:

```python
def test_field_count(self) -> None:
    event = MODULE.build_consultation_outcome(_consultation_input())
    assert len(event) == 18
```

**Step 6: Update `test_consultation_pipeline_keys_cover_builder`**

In `TestPipelineCompleteness` at line 708-717, add the new nullable fields:

```python
def test_consultation_pipeline_keys_cover_builder(self) -> None:
    """All pipeline.get() keys in build_consultation_outcome have explicit values."""
    pipeline = _consultation_input()["pipeline"]
    builder_keys = {
        "thread_id", "posture", "turn_count", "turn_budget",
        "profile_name", "mode", "provenance_unknown_count",
        "question_shaped", "shape_confidence",
        "assumptions_generated_count", "ambiguity_count",
    }
    assert builder_keys.issubset(set(pipeline.keys())), (
        f"Missing pipeline keys: {builder_keys - set(pipeline.keys())}"
    )
```

Also update `_consultation_input` fixture to include the new keys with None defaults:

```python
def _consultation_input(pipeline: dict | None = None) -> dict:
    return {
        "event_type": "consultation_outcome",
        "pipeline": pipeline
        or {
            "posture": "collaborative",
            "thread_id": "thread-xyz-789",
            "turn_count": 1,
            "turn_budget": 1,
            "profile_name": None,
            "mode": "server_assisted",
            "provenance_unknown_count": None,
            "question_shaped": None,
            "shape_confidence": None,
            "assumptions_generated_count": None,
            "ambiguity_count": None,
        },
    }
```

**Step 7: Add reverse invariant test for consultation_outcome**

The `validate()` tri-state planning invariant applies to consultation events too after Task 1 adds the nullable fields. Test that stray companion fields without `question_shaped` trigger validation failure:

```python
def test_reverse_invariant_consultation(self) -> None:
    """Stray shape_confidence without question_shaped triggers validation error."""
    pipeline = {
        "posture": "collaborative",
        "thread_id": None,
        "turn_count": 1,
        "turn_budget": 1,
        "profile_name": None,
        "mode": "server_assisted",
        "provenance_unknown_count": None,
        "question_shaped": None,
        "shape_confidence": "high",
        "assumptions_generated_count": None,
        "ambiguity_count": None,
    }
    event = MODULE.build_consultation_outcome(_consultation_input(pipeline))
    with pytest.raises(ValueError, match="shape_confidence"):
        MODULE.validate(event, "consultation_outcome")
```

**Step 8: Add planning schema version test for consultation_outcome**

```python
def test_schema_version_with_planning(self) -> None:
    """consultation_outcome bumps to 0.3.0 when question_shaped is set."""
    pipeline = {
        "posture": "collaborative",
        "thread_id": None,
        "turn_count": 1,
        "turn_budget": 1,
        "profile_name": "planning",
        "mode": "server_assisted",
        "provenance_unknown_count": None,
        "question_shaped": True,
        "shape_confidence": "high",
        "assumptions_generated_count": 3,
        "ambiguity_count": 1,
    }
    event = MODULE.build_consultation_outcome(_consultation_input(pipeline))
    assert event["schema_version"] == "0.3.0"
```

**Step 9: Run full test suite**

Run: `cd packages/plugins/cross-model && uv run pytest ../../../tests/test_emit_analytics.py -v`
Expected: All tests pass

**Step 10: Lint**

Run: `cd packages/plugins/cross-model && uv run ruff check scripts/emit_analytics.py ../../../tests/test_emit_analytics.py`
Expected: No errors

**Step 11: Commit**

```bash
git add packages/plugins/cross-model/scripts/emit_analytics.py tests/test_emit_analytics.py
git commit -m "fix(analytics): use _resolve_schema_version in build_consultation_outcome

Both event builders now use the same resolver for schema version auto-bump.
Consultation events gain nullable feature-flag fields (provenance, planning)
so the resolver can inspect them.

Previously build_consultation_outcome hardcoded schema_version='0.1.0'
while build_dialogue_outcome used the resolver, creating a divergence."
```

---

## Task 2: Episode linkage policy freeze [XS]

**Files:**
- Modify: `packages/plugins/cross-model/scripts/emit_analytics.py:396-404`
- Modify: `tests/test_emit_analytics.py` (TestBuildDialogueOutcome)

**Step 1: Update the episode_id comment in build_dialogue_outcome**

In `packages/plugins/cross-model/scripts/emit_analytics.py`, replace the comment and assignment at line 403-404:

```python
        # Episode linkage: reserved nullable. Not populated at emit time.
        # E-LEARNING will use append-only episode_link events for post-hoc
        # linkage via consultation_id. Do not add to _DIALOGUE_REQUIRED.
        "episode_id": None,
```

**Step 2: Write test — null episode_id passes validation**

Add to `TestValidate` in `tests/test_emit_analytics.py`:

```python
def test_null_episode_id_passes_validation(self) -> None:
    """episode_id=None should not cause validation errors (reserved nullable)."""
    event = MODULE.build_dialogue_outcome(_dialogue_input())
    assert event["episode_id"] is None
    # Validation should pass — episode_id is not in _DIALOGUE_REQUIRED
    MODULE.validate(event, "dialogue_outcome")  # no exception = pass
```

**Step 3: Write test — episode_id absent from required fields**

```python
def test_episode_id_not_required(self) -> None:
    """episode_id must NOT be in _DIALOGUE_REQUIRED (reserved nullable)."""
    assert "episode_id" not in MODULE._DIALOGUE_REQUIRED
```

**Step 4: Run tests**

Run: `cd packages/plugins/cross-model && uv run pytest ../../../tests/test_emit_analytics.py::TestValidate::test_null_episode_id_passes_validation ../../../tests/test_emit_analytics.py::TestValidate::test_episode_id_not_required -v`
Expected: PASS

**Step 5: Run full suite**

Run: `cd packages/plugins/cross-model && uv run pytest ../../../tests/test_emit_analytics.py -v`
Expected: All tests pass

**Step 6: Commit**

```bash
git add packages/plugins/cross-model/scripts/emit_analytics.py tests/test_emit_analytics.py
git commit -m "test(analytics): freeze episode_id as reserved nullable

Document that episode_id is intentionally never populated at emit time.
E-LEARNING will use append-only episode_link events for post-hoc linkage
via consultation_id. Add tests confirming the reserved nullable status."
```

---

## Task 3: Fix mode truthfulness end-to-end [S]

**Files:**
- Modify: `packages/plugins/cross-model/agents/codex-dialogue.md`
- Modify: `packages/plugins/cross-model/skills/dialogue/SKILL.md`
- Modify: `packages/plugins/cross-model/skills/codex/SKILL.md`
- Modify: `tests/test_emit_analytics.py`

**Step 1: Add explicit mode return to codex-dialogue agent**

In `packages/plugins/cross-model/agents/codex-dialogue.md`, locate the **Output Format** section — specifically the `### Conversation Summary` bullet list and the example block that shows the synthesis structure. Add a `mode` field after the last existing field in that bullet list.

```markdown
- **Mode:** `server_assisted` or `manual_legacy` — the actual mode used for this conversation. Set once at conversation start (server_assisted if context injection tools available, manual_legacy otherwise). Do not change mid-conversation.
```

If the agent has a "return value" or "Task tool return" section, add `mode` there. The key requirement is that the agent explicitly includes the mode string in its synthesis output, not just in the conversation mechanics.

**Step 2: Update dialogue SKILL.md Step 7 — read mode from agent return**

In `packages/plugins/cross-model/skills/dialogue/SKILL.md`, in the Step 7 pipeline field table, update the `mode` row. Currently at line ~384:

Find:
```
| `mode` | Args | `"server_assisted"` or `"manual_legacy"` |
```

Replace with:
```
| `mode` | Step 5 agent return | `"server_assisted"` or `"manual_legacy"`. Read from the `codex-dialogue` agent's explicit mode field in its return value. Do not infer or hardcode. |
```

**Step 3: Update /codex SKILL.md — document server_assisted rationale**

In `packages/plugins/cross-model/skills/codex/SKILL.md`, find the analytics emission section near line 234 where `"mode": "server_assisted"` is hardcoded.

Add a comment explaining the design:

```json
    "mode": "server_assisted"
```

Add a note above the JSON block:
```markdown
**Mode:** `/codex` is always `server_assisted` — it uses the Codex MCP tools directly (no fallback to manual_legacy). The codex-dialogue agent determines its own mode; `/codex` does not delegate to that agent.
```

This is documentation-only — `/codex` correctly hardcodes `server_assisted` because it never falls back to manual_legacy. The fix is in `/dialogue` (Step 2), not here.

**Step 4: Write test — mode passes through from pipeline**

Add to `TestBuildDialogueOutcome` in `tests/test_emit_analytics.py`:

```python
def test_mode_from_pipeline(self) -> None:
    """mode field propagates from pipeline input."""
    event = MODULE.build_dialogue_outcome(_dialogue_input())
    assert event["mode"] == "server_assisted"

def test_mode_manual_legacy(self) -> None:
    """manual_legacy mode propagates correctly."""
    pipeline = {**SAMPLE_PIPELINE, "mode": "manual_legacy"}
    event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
    assert event["mode"] == "manual_legacy"
```

Check if `test_mode_from_pipeline` already exists. If so, only add `test_mode_manual_legacy`.

**Step 5: Write test — consultation_outcome mode passes through**

Add to `TestBuildConsultationOutcome`:

```python
def test_mode_manual_legacy(self) -> None:
    """manual_legacy mode propagates through consultation_outcome."""
    pipeline = {
        "posture": "collaborative",
        "thread_id": None,
        "turn_count": 1,
        "turn_budget": 1,
        "profile_name": None,
        "mode": "manual_legacy",
        "provenance_unknown_count": None,
        "question_shaped": None,
        "shape_confidence": None,
        "assumptions_generated_count": None,
        "ambiguity_count": None,
    }
    event = MODULE.build_consultation_outcome(_consultation_input(pipeline))
    assert event["mode"] == "manual_legacy"
```

**Step 6: Run tests**

Run: `cd packages/plugins/cross-model && uv run pytest ../../../tests/test_emit_analytics.py -v -k "mode"`
Expected: All mode tests pass

**Step 7: Run full suite**

Run: `cd packages/plugins/cross-model && uv run pytest ../../../tests/ -v`
Expected: All tests pass

**Step 8: Commit**

```bash
git add packages/plugins/cross-model/agents/codex-dialogue.md packages/plugins/cross-model/skills/dialogue/SKILL.md packages/plugins/cross-model/skills/codex/SKILL.md tests/test_emit_analytics.py
git commit -m "fix(mode): explicit mode propagation from codex-dialogue to analytics

codex-dialogue now returns mode explicitly in its synthesis output.
dialogue SKILL.md Step 7 reads mode from the agent return value instead
of inferring it. /codex SKILL.md documents why server_assisted is correct
for direct consultations.

Fixes false telemetry where mode was always 'server_assisted' even when
codex-dialogue fell back to manual_legacy."
```

---

## Task 4: Typed mixed-stream event reader [S]

**Files:**
- Create: `packages/plugins/cross-model/scripts/read_events.py`
- Create: `tests/test_read_events.py`

**Step 1: Write failing tests — reader fundamentals**

Create `tests/test_read_events.py`:

```python
"""Tests for packages/plugins/cross-model/scripts/read_events.py.

Tests the typed event reader: JSONL parsing, event classification,
per-event schema validation, and error handling for unknown/malformed events.
"""

from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Module import
# ---------------------------------------------------------------------------

MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "packages"
    / "plugins"
    / "cross-model"
    / "scripts"
    / "read_events.py"
)
SPEC = importlib.util.spec_from_file_location("read_events", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

DIALOGUE_EVENT = {
    "schema_version": "0.1.0",
    "consultation_id": "uuid-1",
    "event": "dialogue_outcome",
    "ts": "2026-02-21T12:00:00Z",
    "posture": "evaluative",
    "turn_count": 4,
    "turn_budget": 8,
    "converged": True,
    "convergence_reason_code": "all_resolved",
    "termination_reason": "natural",
    "resolved_count": 5,
    "unresolved_count": 0,
    "emerged_count": 2,
    "seed_confidence": "normal",
    "mode": "server_assisted",
}

CONSULTATION_EVENT = {
    "schema_version": "0.1.0",
    "consultation_id": "uuid-2",
    "event": "consultation_outcome",
    "ts": "2026-02-21T13:00:00Z",
    "posture": "collaborative",
    "turn_count": 1,
    "turn_budget": 1,
    "termination_reason": "complete",
    "mode": "server_assisted",
}

BLOCK_EVENT = {
    "ts": "2026-02-21T10:00:00Z",
    "event": "block",
    "tool": "Bash",
    "session_id": "sess-1",
    "prompt_length": 500,
    "reason": "denied",
}

SHADOW_EVENT = {
    "ts": "2026-02-21T10:01:00Z",
    "event": "shadow",
    "tool": "Bash",
    "session_id": "sess-1",
    "prompt_length": 600,
}


def _write_jsonl(events: list[dict], path: Path) -> None:
    with open(path, "w") as f:
        for e in events:
            f.write(json.dumps(e) + "\n")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestReadAll:
    def test_reads_all_events(self, tmp_path: Path) -> None:
        path = tmp_path / "events.jsonl"
        _write_jsonl([DIALOGUE_EVENT, CONSULTATION_EVENT, BLOCK_EVENT], path)
        events = MODULE.read_all(path)
        assert len(events) == 3

    def test_empty_file(self, tmp_path: Path) -> None:
        path = tmp_path / "events.jsonl"
        path.write_text("")
        events = MODULE.read_all(path)
        assert events == []

    def test_missing_file(self, tmp_path: Path) -> None:
        path = tmp_path / "nonexistent.jsonl"
        events = MODULE.read_all(path)
        assert events == []

    def test_malformed_line_skipped(self, tmp_path: Path) -> None:
        path = tmp_path / "events.jsonl"
        with open(path, "w") as f:
            f.write(json.dumps(DIALOGUE_EVENT) + "\n")
            f.write("not valid json\n")
            f.write(json.dumps(CONSULTATION_EVENT) + "\n")
        events = MODULE.read_all(path)
        assert len(events) == 2

    def test_blank_lines_skipped(self, tmp_path: Path) -> None:
        path = tmp_path / "events.jsonl"
        with open(path, "w") as f:
            f.write(json.dumps(DIALOGUE_EVENT) + "\n")
            f.write("\n")
            f.write("   \n")
            f.write(json.dumps(CONSULTATION_EVENT) + "\n")
        events = MODULE.read_all(path)
        assert len(events) == 2


class TestFilterByType:
    def test_filter_dialogue_only(self, tmp_path: Path) -> None:
        path = tmp_path / "events.jsonl"
        _write_jsonl([DIALOGUE_EVENT, CONSULTATION_EVENT, BLOCK_EVENT], path)
        events = MODULE.read_by_type(path, "dialogue_outcome")
        assert len(events) == 1
        assert events[0]["event"] == "dialogue_outcome"

    def test_filter_consultation_only(self, tmp_path: Path) -> None:
        path = tmp_path / "events.jsonl"
        _write_jsonl([DIALOGUE_EVENT, CONSULTATION_EVENT], path)
        events = MODULE.read_by_type(path, "consultation_outcome")
        assert len(events) == 1
        assert events[0]["event"] == "consultation_outcome"

    def test_filter_no_matches(self, tmp_path: Path) -> None:
        path = tmp_path / "events.jsonl"
        _write_jsonl([BLOCK_EVENT], path)
        events = MODULE.read_by_type(path, "dialogue_outcome")
        assert events == []

    def test_unknown_event_type_passes_through(self, tmp_path: Path) -> None:
        unknown = {"event": "future_event_type", "ts": "2026-01-01T00:00:00Z"}
        path = tmp_path / "events.jsonl"
        _write_jsonl([unknown, DIALOGUE_EVENT], path)
        all_events = MODULE.read_all(path)
        assert len(all_events) == 2


class TestEventClassification:
    def test_classify_dialogue(self) -> None:
        assert MODULE.classify(DIALOGUE_EVENT) == "dialogue_outcome"

    def test_classify_consultation(self) -> None:
        assert MODULE.classify(CONSULTATION_EVENT) == "consultation_outcome"

    def test_classify_block(self) -> None:
        assert MODULE.classify(BLOCK_EVENT) == "block"

    def test_classify_shadow(self) -> None:
        assert MODULE.classify(SHADOW_EVENT) == "shadow"

    def test_classify_missing_event_field(self) -> None:
        assert MODULE.classify({"ts": "2026-01-01T00:00:00Z"}) == "unknown"

    def test_classify_empty_dict(self) -> None:
        assert MODULE.classify({}) == "unknown"


class TestValidateEvent:
    def test_valid_dialogue_passes(self) -> None:
        errors = MODULE.validate_event(DIALOGUE_EVENT)
        assert errors == []

    def test_valid_consultation_passes(self) -> None:
        errors = MODULE.validate_event(CONSULTATION_EVENT)
        assert errors == []

    def test_dialogue_missing_required_field(self) -> None:
        bad = {k: v for k, v in DIALOGUE_EVENT.items() if k != "turn_count"}
        errors = MODULE.validate_event(bad)
        assert len(errors) >= 1
        assert any("turn_count" in e for e in errors)

    def test_consultation_missing_required_field(self) -> None:
        bad = {k: v for k, v in CONSULTATION_EVENT.items() if k != "mode"}
        errors = MODULE.validate_event(bad)
        assert len(errors) >= 1
        assert any("mode" in e for e in errors)

    def test_block_event_passes_minimal(self) -> None:
        """Block/shadow events have no strict schema — just needs 'event' field."""
        errors = MODULE.validate_event(BLOCK_EVENT)
        assert errors == []

    def test_unknown_event_returns_warning(self) -> None:
        unknown = {"event": "future_unknown", "ts": "2026-01-01T00:00:00Z"}
        errors = MODULE.validate_event(unknown)
        assert len(errors) == 1
        assert "unknown" in errors[0].lower()
```

**Step 2: Run tests to verify they fail**

Run: `cd packages/plugins/cross-model && uv run pytest ../../../tests/test_read_events.py -v`
Expected: ImportError — `read_events.py` does not exist yet

**Step 3: Implement `read_events.py`**

Create `packages/plugins/cross-model/scripts/read_events.py`:

```python
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Typed reader for the cross-model event log (~/.claude/.codex-events.jsonl).

Reads heterogeneous JSONL events (block, shadow, consultation,
dialogue_outcome, consultation_outcome), classifies by event type,
and validates per-event required fields.

Usage as library:
    from read_events import read_all, read_by_type, classify, validate_event

Usage as script:
    python3 read_events.py [--type dialogue_outcome] [--validate] [path]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_DEFAULT_PATH = Path.home() / ".claude" / ".codex-events.jsonl"

# Required fields per event type. Events not in this map are classified
# as their event field value but have no required-field validation.
_REQUIRED_FIELDS: dict[str, set[str]] = {
    "dialogue_outcome": {
        "schema_version",
        "consultation_id",
        "event",
        "ts",
        "posture",
        "turn_count",
        "turn_budget",
        "converged",
        "convergence_reason_code",
        "termination_reason",
        "resolved_count",
        "unresolved_count",
        "emerged_count",
        "seed_confidence",
        "mode",
    },
    "consultation_outcome": {
        "schema_version",
        "consultation_id",
        "event",
        "ts",
        "posture",
        "turn_count",
        "turn_budget",
        "termination_reason",
        "mode",
    },
}

# Known event types that are valid but have no required-field schema
_KNOWN_UNSTRUCTURED = {"block", "shadow", "consultation"}


def classify(event: dict) -> str:
    """Return the event type string, or 'unknown' if missing."""
    return event.get("event", "unknown")


def validate_event(event: dict) -> list[str]:
    """Validate an event against its type's required fields.

    Returns a list of error strings (empty = valid).
    """
    event_type = classify(event)

    if event_type == "unknown":
        return ["unknown event type: missing 'event' field"]

    required = _REQUIRED_FIELDS.get(event_type)
    if required is None:
        if event_type in _KNOWN_UNSTRUCTURED:
            return []
        return [f"unknown event type: '{event_type}'"]

    missing = required - set(event.keys())
    if missing:
        return [f"missing required field: {f}" for f in sorted(missing)]
    return []


def read_all(path: Path | None = None) -> list[dict]:
    """Read all events from the JSONL file. Skips malformed lines.

    Returns empty list if file does not exist.
    """
    path = path or _DEFAULT_PATH
    if not path.exists():
        return []

    events: list[dict] = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return events


def read_by_type(path: Path | None = None, event_type: str = "dialogue_outcome") -> list[dict]:
    """Read events filtered by type."""
    return [e for e in read_all(path) if classify(e) == event_type]


def main() -> None:
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Read cross-model event log")
    parser.add_argument("path", nargs="?", default=str(_DEFAULT_PATH), help="JSONL file path")
    parser.add_argument("--type", dest="event_type", help="Filter by event type")
    parser.add_argument("--validate", action="store_true", help="Validate events and report errors")
    args = parser.parse_args()

    path = Path(args.path)
    events = read_by_type(path, args.event_type) if args.event_type else read_all(path)

    if args.validate:
        total_errors = 0
        for i, event in enumerate(events):
            errors = validate_event(event)
            if errors:
                total_errors += len(errors)
                eid = event.get("consultation_id", f"line-{i}")
                for err in errors:
                    print(f"[{eid}] {err}", file=sys.stderr)
        print(json.dumps({"events": len(events), "errors": total_errors}))
        sys.exit(1 if total_errors > 0 else 0)
    else:
        for event in events:
            print(json.dumps(event))


if __name__ == "__main__":
    main()
```

**Step 4: Run tests**

Run: `cd packages/plugins/cross-model && uv run pytest ../../../tests/test_read_events.py -v`
Expected: All tests pass

**Step 5: Add subset parity tests**

Add to `tests/test_read_events.py` after the `TestValidateEvent` class:

```python
class TestSchemaParityWithEmitter:
    """Guard against reader/emitter schema drift via subset check."""

    def test_dialogue_required_subset(self) -> None:
        """Reader's dialogue required fields must be a subset of emitter's."""
        emitter_path = (
            Path(__file__).resolve().parents[1]
            / "packages" / "plugins" / "cross-model" / "scripts" / "emit_analytics.py"
        )
        spec = importlib.util.spec_from_file_location("emit_analytics", emitter_path)
        emitter = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(emitter)
        reader_required = MODULE._REQUIRED_FIELDS.get("dialogue_outcome", set())
        emitter_required = emitter._DIALOGUE_REQUIRED
        assert reader_required <= emitter_required, (
            f"Reader has fields not in emitter: {reader_required - emitter_required}"
        )

    def test_consultation_required_subset(self) -> None:
        """Reader's consultation required fields must be a subset of emitter's."""
        emitter_path = (
            Path(__file__).resolve().parents[1]
            / "packages" / "plugins" / "cross-model" / "scripts" / "emit_analytics.py"
        )
        spec = importlib.util.spec_from_file_location("emit_analytics", emitter_path)
        emitter = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(emitter)
        reader_required = MODULE._REQUIRED_FIELDS.get("consultation_outcome", set())
        emitter_required = emitter._CONSULTATION_REQUIRED
        assert reader_required <= emitter_required, (
            f"Reader has fields not in emitter: {reader_required - emitter_required}"
        )
```

**Step 6: Lint**

Run: `cd packages/plugins/cross-model && uv run ruff check scripts/read_events.py ../../../tests/test_read_events.py`
Expected: No errors

**Step 7: Commit**

```bash
git add packages/plugins/cross-model/scripts/read_events.py tests/test_read_events.py
git commit -m "feat(analytics): add typed event reader for JSONL log

New read_events.py provides typed reading of the heterogeneous
codex-events.jsonl file. Classifies events by type, validates
per-event required fields, and handles malformed/unknown events
gracefully. E-LEARNING will use this to retrieve prior consultation
data for learning card generation."
```

---

## Task 5: Consultation contract learning retrieval/injection section [S]

**Files:**
- Modify: `packages/plugins/cross-model/references/consultation-contract.md`
- Modify: `scripts/validate_consultation_contract.py`
- Modify: `tests/test_consultation_contract_sync.py`

**Step 1: Add §17 to the consultation contract**

In `packages/plugins/cross-model/references/consultation-contract.md`, after §16 (Conformance Checklist), add:

```markdown
---

## 17. Learning Retrieval and Injection (Normative)

Pre-consultation retrieval of relevant learning cards from prior Codex conversations. Both `/codex` and `/dialogue` paths MUST execute this step before briefing assembly.

### 17.1 Retrieval Protocol

1. **Read learning store:** Read from `docs/learnings/learnings.md` (or the configured learning store path).
2. **Filter by relevance:** Select learning cards whose tags or content overlap with the consultation question. Relevance filtering is best-effort — false positives (including an irrelevant card) are preferable to false negatives (excluding a relevant one).
3. **Cap:** Include at most 5 learning cards per consultation to avoid context dilution.
4. **Fail-soft:** If the learning store is missing, empty, or unreadable, proceed without learning cards. Do not block the consultation.

### 17.2 Injection Point

- **`/dialogue` path:** Inject selected cards into the assembled briefing (Step 3h) as a `## Prior Learnings` section between `## Context` and `## Material`.
- **`/codex` path:** Inject selected cards into the briefing's `## Context` section before the question.
- **`manual_legacy` fallback:** Pre-briefing injection covers this path — no mid-conversation injection required for MVP.

### 17.3 Card Format

Each injected card MUST include:
- **Source consultation_id** (for provenance tracing)
- **Tags** (for relevance matching)
- **Insight text** (the learning content)

Cards MUST NOT include raw Codex responses, credentials, or session-specific identifiers.

### 17.4 Non-Goals (Deferred)

- Mid-dialogue adaptive injection (re-querying the learning store based on conversation turns)
- Automated relevance scoring (machine-learned models for card selection)
- Learning card write-back (creating new cards from consultation outcomes — covered by E-LEARNING Phase 0+)
```

**Step 2: Update §1 scope — remove "learning injection" from out-of-scope**

In `packages/plugins/cross-model/references/consultation-contract.md` line 18, update:

Find: `**Out of scope:** The context injection protocol (see `context-injection-contract.md`), subagent orchestration, event persistence, profile UX flag parsing, and learning injection.`

Replace with: `**Out of scope:** The context injection protocol (see `context-injection-contract.md`), subagent orchestration, event persistence, and profile UX flag parsing.`

**Step 3: Add learning retrieval to §16 conformance checklist**

In `packages/plugins/cross-model/references/consultation-contract.md`, in §16 (Conformance Checklist), add a new section:

```markdown
**Learning Retrieval (§17)**
- [ ] Learning store read attempted before briefing assembly
- [ ] Missing/empty store handled gracefully (fail-soft)
- [ ] Cards capped at 5 per consultation
- [ ] Cards injected at correct point (§17.2)
- [ ] No credentials or raw Codex responses in injected cards
```

**Step 4: Update `validate_consultation_contract.py`**

In `scripts/validate_consultation_contract.py`:

1. Update the constant at line 26:
```python
EXPECTED_SECTION_COUNT = 17
```

2. Update the module docstring (line ~9) from "16 expected sections" to "17 expected sections".

**Step 5: Run contract sync tests**

Run: `cd packages/plugins/cross-model && uv run pytest ../../../tests/test_consultation_contract_sync.py -v`
Expected: `test_validate_passes_on_current_codebase` — PASS (17 sections found, 17 expected)

If `test_complete_16_sections_pass` fails, update it:

In `tests/test_consultation_contract_sync.py` line 92-96:

```python
def test_complete_17_sections_pass() -> None:
    """check_section_count passes when all 17 sections are present."""
    all_sections = set(range(1, 18))
    errors = MODULE.check_section_count(all_sections)
    assert errors == []
```

Also update `test_extra_contract_section_is_caught` at line 83-89:

```python
def test_extra_contract_section_is_caught() -> None:
    """check_section_count flags when an unexpected section number is present."""
    sections_with_extra = set(range(1, 18)) | {18}
    errors = MODULE.check_section_count(sections_with_extra)
    assert len(errors) == 1
    assert "18" in errors[0]
    assert "unexpected" in errors[0]
```

And `test_missing_contract_section_is_caught` at line 73-80 — this test creates a set missing §6 from a 16-section range. Update the range:

```python
def test_missing_contract_section_is_caught() -> None:
    """check_section_count flags when a section number is absent."""
    # Contract has §1-§17; simulate §6 missing
    sections_missing_6 = set(range(1, 18)) - {6}
    errors = MODULE.check_section_count(sections_missing_6)
    assert len(errors) == 1
    assert "6" in errors[0]
    assert "missing" in errors[0]
```

**Step 6: Run full contract sync test suite**

Run: `cd packages/plugins/cross-model && uv run pytest ../../../tests/test_consultation_contract_sync.py -v`
Expected: All 13 tests pass

**Step 7: Run full test suite**

Run: `cd packages/plugins/cross-model && uv run pytest ../../../tests/ -v`
Expected: All tests pass

**Step 8: Add (S17) stub references in skill files**

Add minimal `(S17)` references so implementors know the section exists:

In `packages/plugins/cross-model/skills/dialogue/SKILL.md`, in the Step 7 pipeline field table area, add a note:
```markdown
**Learning retrieval (S17):** Before briefing assembly, attempt to read learning cards per consultation contract §17. Fail-soft: missing store does not block consultation.
```

In `packages/plugins/cross-model/skills/codex/SKILL.md`, in the analytics emission section, add a note:
```markdown
**Learning retrieval (S17):** Before consultation, attempt to read learning cards per consultation contract §17. Fail-soft: missing store does not block consultation.
```

These are documentation stubs only — the actual retrieval implementation is E-LEARNING scope. The stubs ensure governance traceability: every normative contract section has at least one implementor-visible reference.

**Step 9: Commit**

```bash
git add packages/plugins/cross-model/references/consultation-contract.md scripts/validate_consultation_contract.py tests/test_consultation_contract_sync.py packages/plugins/cross-model/skills/dialogue/SKILL.md packages/plugins/cross-model/skills/codex/SKILL.md
git commit -m "feat(contract): add §17 learning retrieval and injection

Establishes the normative protocol for pre-consultation learning card
retrieval. Both /codex and /dialogue paths must attempt retrieval before
briefing assembly. Fail-soft: missing store does not block consultation.

Updates contract section count from 16 to 17. Removes learning injection
from §1 out-of-scope list. Adds conformance checklist items for §17.
Adds (S17) stub references in dialogue and codex skill files for
governance traceability."
```

---

## Task 6: Replay-based analytics conformance tests [M]

**Files:**
- Create: `tests/fixtures/` directory
- Create: `tests/fixtures/dialogue_converged.json`
- Create: `tests/fixtures/dialogue_scope_breach.json`
- Create: `tests/fixtures/dialogue_with_planning.json`
- Create: `tests/fixtures/dialogue_manual_legacy.json`
- Create: `tests/fixtures/consultation_simple.json`
- Modify: `tests/test_emit_analytics.py` (new TestReplayConformance class)

**Step 1: Create fixtures directory and converged dialogue fixture**

First, create the fixtures directory:
```bash
mkdir -p tests/fixtures
```

Create `tests/fixtures/dialogue_converged.json` — a realistic multi-turn dialogue input:

```json
{
  "event_type": "dialogue_outcome",
  "synthesis_text": "### Conversation Summary\n- **Topic:** System architecture review\n- **Goal:** Evaluate integration quality\n- **Posture:** Evaluative\n- **Turns:** 6 of 8 budget\n- **Converged:** Yes -- all unresolved items closed by T6\n- **Trajectory:** T1:advancing -> T2:advancing -> T3:advancing -> T4:advancing -> T5:advancing -> T6:shifting\n- **Evidence:** 2 scouts / 6 turns, entities: emit_analytics.py, codex-dialogue.md\n\n### Key Outcomes\n\nP0 and P1 lists agreed.\n\n### Areas of Agreement\n\nBoth sides agreed on priority ordering.\n\n### Contested Claims\n\nSeverity classification of test gaps was contested and resolved.\n\n### Open Questions\n\nOne design question deferred.\n\n### Continuation\n- **Thread ID:** 019c819e-dc16-79d3-825b-0d54b23627ea\n- **Continuation warranted:** no\n- **Unresolved items carried forward:** none\n- **Recommended posture for continuation:** N/A\n- **Evidence trajectory:** T2: emit_analytics.py (confirmed), T4: codex-dialogue.md (confirmed)\n\n### Synthesis Checkpoint\n```\n## Synthesis Checkpoint\nRESOLVED: Mode truthfulness is P0 [confidence: High] [basis: concession]\nRESOLVED: Replay tests are P0 [confidence: High] [basis: convergence]\nRESOLVED: Event reader is P0 [confidence: High] [basis: convergence]\nRESOLVED: Contract learning section needed [confidence: High] [basis: convergence]\nRESOLVED: Episode_id reserved nullable [confidence: High] [basis: concession]\nRESOLVED: Resolver symmetry fix now [confidence: High] [basis: convergence]\nRESOLVED: Learning injection via contract + assembly [confidence: High] [basis: convergence]\nUNRESOLVED: Learning card retrieval failure interaction [raised: turn 3]\nEMERGED: Transcript replay testing strategy [source: dialogue-born]\nEMERGED: Contract as control plane principle [source: dialogue-born]\n```",
  "scope_breach": false,
  "pipeline": {
    "posture": "evaluative",
    "turn_budget": 8,
    "profile_name": "deep-review",
    "seed_confidence": "normal",
    "low_seed_confidence_reasons": [],
    "assumption_count": 4,
    "no_assumptions_fallback": false,
    "gatherer_a_lines": 33,
    "gatherer_b_lines": 11,
    "gatherer_a_retry": false,
    "gatherer_b_retry": false,
    "citations_total": 39,
    "unique_files_total": 18,
    "gatherer_a_unique_paths": 12,
    "gatherer_b_unique_paths": 9,
    "shared_citation_paths": 3,
    "counter_count": 3,
    "confirm_count": 4,
    "open_count": 9,
    "claim_count": 28,
    "source_classes": ["code", "docs", "tests", "specs"],
    "scope_root_count": 5,
    "scope_roots_fingerprint": null,
    "provenance_unknown_count": 0,
    "scout_count": 2,
    "mode": "server_assisted",
    "question_shaped": null,
    "shape_confidence": null,
    "assumptions_generated_count": null,
    "ambiguity_count": null
  }
}
```

**Step 2: Create scope breach fixture**

Create `tests/fixtures/dialogue_scope_breach.json`:

```json
{
  "event_type": "dialogue_outcome",
  "synthesis_text": "### Conversation Summary\n- **Topic:** Out of scope request\n- **Goal:** Review external system\n- **Posture:** Evaluative\n- **Turns:** 1 of 8 budget\n- **Converged:** No\n- **Trajectory:** T1:static\n- **Evidence:** 0 scouts / 1 turns\n\n### Key Outcomes\n\nScope breach detected. Conversation stopped.\n\n### Areas of Agreement\n\nNone — stopped before substantive exchange.\n\n### Contested Claims\n\nNone.\n\n### Open Questions\n\nAll questions unresolved due to scope breach.\n\n### Continuation\n- **Thread ID:** thread-scope-breach-001\n- **Continuation warranted:** yes -- with expanded scope\n- **Unresolved items carried forward:** all\n- **Recommended posture for continuation:** collaborative\n- **Evidence trajectory:** none\n\n### Synthesis Checkpoint\n```\n## Synthesis Checkpoint\nUNRESOLVED: Original question unanswered [raised: turn 1]\n```",
  "scope_breach": true,
  "pipeline": {
    "posture": "evaluative",
    "turn_budget": 8,
    "profile_name": null,
    "seed_confidence": "normal",
    "low_seed_confidence_reasons": [],
    "assumption_count": 0,
    "no_assumptions_fallback": true,
    "gatherer_a_lines": 0,
    "gatherer_b_lines": 0,
    "gatherer_a_retry": false,
    "gatherer_b_retry": false,
    "citations_total": 0,
    "unique_files_total": 0,
    "gatherer_a_unique_paths": 0,
    "gatherer_b_unique_paths": 0,
    "shared_citation_paths": 0,
    "counter_count": 0,
    "confirm_count": 0,
    "open_count": 0,
    "claim_count": 0,
    "source_classes": [],
    "scope_root_count": 0,
    "scope_roots_fingerprint": null,
    "provenance_unknown_count": null,
    "scout_count": 0,
    "mode": "server_assisted",
    "question_shaped": null,
    "shape_confidence": null,
    "assumptions_generated_count": null,
    "ambiguity_count": null
  }
}
```

**Step 3: Create planning fixture**

Create `tests/fixtures/dialogue_with_planning.json`:

```json
{
  "event_type": "dialogue_outcome",
  "synthesis_text": "### Conversation Summary\n- **Topic:** Feature planning\n- **Goal:** Plan implementation approach\n- **Posture:** Collaborative\n- **Turns:** 3 of 8 budget\n- **Converged:** Yes\n- **Trajectory:** T1:advancing -> T2:advancing -> T3:static\n- **Evidence:** 1 scouts / 3 turns, entities: emit_analytics.py\n\n### Key Outcomes\n\nApproach agreed.\n\n### Areas of Agreement\n\nSingle approach selected.\n\n### Contested Claims\n\nNone.\n\n### Open Questions\n\nNone.\n\n### Continuation\n- **Thread ID:** thread-planning-001\n- **Continuation warranted:** no\n- **Unresolved items carried forward:** none\n- **Recommended posture for continuation:** N/A\n- **Evidence trajectory:** T2: emit_analytics.py (confirmed)\n\n### Synthesis Checkpoint\n```\n## Synthesis Checkpoint\nRESOLVED: Implementation approach agreed [confidence: High] [basis: convergence]\nRESOLVED: Testing strategy defined [confidence: High] [basis: convergence]\nEMERGED: Parallel task opportunity [source: dialogue-born]\n```",
  "scope_breach": false,
  "pipeline": {
    "posture": "collaborative",
    "turn_budget": 8,
    "profile_name": "planning",
    "seed_confidence": "normal",
    "low_seed_confidence_reasons": [],
    "assumption_count": 3,
    "no_assumptions_fallback": false,
    "gatherer_a_lines": 15,
    "gatherer_b_lines": 6,
    "gatherer_a_retry": false,
    "gatherer_b_retry": false,
    "citations_total": 16,
    "unique_files_total": 6,
    "gatherer_a_unique_paths": 5,
    "gatherer_b_unique_paths": 3,
    "shared_citation_paths": 2,
    "counter_count": 1,
    "confirm_count": 2,
    "open_count": 3,
    "claim_count": 12,
    "source_classes": ["code", "tests"],
    "scope_root_count": 3,
    "scope_roots_fingerprint": null,
    "provenance_unknown_count": 0,
    "scout_count": 1,
    "mode": "server_assisted",
    "question_shaped": true,
    "shape_confidence": "high",
    "assumptions_generated_count": 3,
    "ambiguity_count": 1
  }
}
```

**Step 4: Create manual_legacy fixture**

Create `tests/fixtures/dialogue_manual_legacy.json`:

```json
{
  "event_type": "dialogue_outcome",
  "synthesis_text": "### Conversation Summary\n- **Topic:** Quick review\n- **Goal:** Sanity check approach\n- **Posture:** Collaborative\n- **Turns:** 2 of 4 budget\n- **Converged:** Yes\n- **Trajectory:** T1:advancing -> T2:static\n- **Evidence:** 0 scouts / 2 turns\n\n### Key Outcomes\n\nApproach confirmed.\n\n### Areas of Agreement\n\nApproach is sound.\n\n### Contested Claims\n\nNone.\n\n### Open Questions\n\nNone.\n\n### Continuation\n- **Thread ID:** thread-legacy-001\n- **Continuation warranted:** no\n- **Unresolved items carried forward:** none\n- **Recommended posture for continuation:** N/A\n- **Evidence trajectory:** none\n\n### Synthesis Checkpoint\n```\n## Synthesis Checkpoint\nRESOLVED: Approach validated [confidence: High] [basis: convergence]\n```",
  "scope_breach": false,
  "pipeline": {
    "posture": "collaborative",
    "turn_budget": 4,
    "profile_name": null,
    "seed_confidence": "low",
    "low_seed_confidence_reasons": ["zero_output"],
    "assumption_count": 0,
    "no_assumptions_fallback": true,
    "gatherer_a_lines": 0,
    "gatherer_b_lines": 0,
    "gatherer_a_retry": true,
    "gatherer_b_retry": true,
    "citations_total": 0,
    "unique_files_total": 0,
    "gatherer_a_unique_paths": 0,
    "gatherer_b_unique_paths": 0,
    "shared_citation_paths": 0,
    "counter_count": 0,
    "confirm_count": 0,
    "open_count": 0,
    "claim_count": 0,
    "source_classes": [],
    "scope_root_count": 0,
    "scope_roots_fingerprint": null,
    "provenance_unknown_count": null,
    "scout_count": 0,
    "mode": "manual_legacy",
    "question_shaped": null,
    "shape_confidence": null,
    "assumptions_generated_count": null,
    "ambiguity_count": null
  }
}
```

**Step 5: Create consultation fixture**

Create `tests/fixtures/consultation_simple.json`:

```json
{
  "event_type": "consultation_outcome",
  "pipeline": {
    "posture": "collaborative",
    "thread_id": "thread-consult-001",
    "turn_count": 1,
    "turn_budget": 1,
    "profile_name": null,
    "mode": "server_assisted",
    "provenance_unknown_count": null,
    "question_shaped": null,
    "shape_confidence": null,
    "assumptions_generated_count": null,
    "ambiguity_count": null
  }
}
```

**Step 6: Write TestReplayConformance class**

Add to `tests/test_emit_analytics.py`:

```python
# ---------------------------------------------------------------------------
# TestReplayConformance
# ---------------------------------------------------------------------------

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"


def _load_fixture(name: str) -> dict:
    with open(FIXTURE_DIR / name) as f:
        return json.load(f)


class TestReplayConformance:
    """Replay realistic dialogue/consultation inputs through the emitter.

    These fixtures simulate actual codex-dialogue outputs, validating that
    emit_analytics.py produces correct events for real-world scenarios.
    """

    def test_converged_dialogue_turn_count(self) -> None:
        fixture = _load_fixture("dialogue_converged.json")
        event = MODULE.build_dialogue_outcome(fixture)
        assert event["turn_count"] == 6
        assert event["turn_budget"] == 8
        assert event["turn_count"] >= 1, "multi-turn dialogue must have turn_count >= 1"

    def test_converged_dialogue_thread_id(self) -> None:
        fixture = _load_fixture("dialogue_converged.json")
        event = MODULE.build_dialogue_outcome(fixture)
        assert event["thread_id"] == "019c819e-dc16-79d3-825b-0d54b23627ea"
        assert event["thread_id"] is not None, "converged dialogue should have thread_id"

    def test_converged_dialogue_convergence(self) -> None:
        fixture = _load_fixture("dialogue_converged.json")
        event = MODULE.build_dialogue_outcome(fixture)
        assert event["converged"] is True
        assert event["convergence_reason_code"] == "natural_convergence"
        assert event["resolved_count"] == 7
        assert event["unresolved_count"] == 1
        assert event["emerged_count"] == 2

    def test_all_resolved_dialogue_convergence(self) -> None:
        """Fixture with 0 UNRESOLVED lines produces all_resolved."""
        fixture = _load_fixture("dialogue_converged.json")
        # Patch synthesis to have 0 UNRESOLVED lines
        fixture["synthesis_text"] = fixture["synthesis_text"].replace(
            "UNRESOLVED: Learning card retrieval failure interaction [raised: turn 3]\n",
            "",
        )
        event = MODULE.build_dialogue_outcome(fixture)
        assert event["converged"] is True
        assert event["convergence_reason_code"] == "all_resolved"
        assert event["unresolved_count"] == 0

    def test_converged_dialogue_schema_version(self) -> None:
        fixture = _load_fixture("dialogue_converged.json")
        event = MODULE.build_dialogue_outcome(fixture)
        # provenance_unknown_count=0 (non-negative int) -> 0.2.0
        assert event["schema_version"] == "0.2.0"

    def test_converged_dialogue_validates(self) -> None:
        fixture = _load_fixture("dialogue_converged.json")
        event = MODULE.build_dialogue_outcome(fixture)
        MODULE.validate(event, "dialogue_outcome")  # no exception = pass

    def test_scope_breach_convergence(self) -> None:
        fixture = _load_fixture("dialogue_scope_breach.json")
        event = MODULE.build_dialogue_outcome(fixture)
        assert event["converged"] is False
        assert event["convergence_reason_code"] == "scope_breach"
        assert event["termination_reason"] == "scope_breach"
        assert event["turn_count"] == 1

    def test_scope_breach_validates(self) -> None:
        fixture = _load_fixture("dialogue_scope_breach.json")
        event = MODULE.build_dialogue_outcome(fixture)
        MODULE.validate(event, "dialogue_outcome")

    def test_planning_schema_version(self) -> None:
        fixture = _load_fixture("dialogue_with_planning.json")
        event = MODULE.build_dialogue_outcome(fixture)
        assert event["question_shaped"] is True
        assert event["schema_version"] == "0.3.0"
        assert event["shape_confidence"] == "high"
        assert event["assumptions_generated_count"] == 3
        assert event["ambiguity_count"] == 1

    def test_planning_validates(self) -> None:
        fixture = _load_fixture("dialogue_with_planning.json")
        event = MODULE.build_dialogue_outcome(fixture)
        MODULE.validate(event, "dialogue_outcome")

    def test_manual_legacy_mode(self) -> None:
        fixture = _load_fixture("dialogue_manual_legacy.json")
        event = MODULE.build_dialogue_outcome(fixture)
        assert event["mode"] == "manual_legacy"
        assert event["seed_confidence"] == "low"

    def test_manual_legacy_validates(self) -> None:
        fixture = _load_fixture("dialogue_manual_legacy.json")
        event = MODULE.build_dialogue_outcome(fixture)
        MODULE.validate(event, "dialogue_outcome")

    def test_consultation_simple(self) -> None:
        fixture = _load_fixture("consultation_simple.json")
        event = MODULE.build_consultation_outcome(fixture)
        assert event["turn_count"] == 1
        assert event["turn_budget"] == 1
        assert event["mode"] == "server_assisted"
        assert event["schema_version"] == "0.1.0"

    def test_consultation_simple_validates(self) -> None:
        fixture = _load_fixture("consultation_simple.json")
        event = MODULE.build_consultation_outcome(fixture)
        MODULE.validate(event, "consultation_outcome")

    def test_all_fixtures_load(self) -> None:
        """Verify all fixture files are loadable JSON."""
        fixture_files = sorted(FIXTURE_DIR.glob("*.json"))
        assert len(fixture_files) >= 5, f"expected >= 5 fixtures, got {len(fixture_files)}"
        for f in fixture_files:
            data = json.loads(f.read_text())
            assert "event_type" in data or "pipeline" in data
```

**Step 7: Run replay tests**

Run: `cd packages/plugins/cross-model && uv run pytest ../../../tests/test_emit_analytics.py::TestReplayConformance -v`
Expected: All tests pass

**Step 8: Run full suite**

Run: `cd packages/plugins/cross-model && uv run pytest ../../../tests/ -v`
Expected: All tests pass

**Step 9: Lint**

Run: `cd packages/plugins/cross-model && uv run ruff check scripts/ ../../../tests/`
Expected: No errors

**Step 10: Commit**

```bash
git add tests/fixtures/ tests/test_emit_analytics.py
git commit -m "test(analytics): add replay-based conformance tests with fixtures

Five fixture files simulate real codex-dialogue scenarios:
- Converged multi-turn dialogue (6 turns, thread_id, 7 resolved)
- Scope breach dialogue (1 turn, stopped)
- Planning dialogue (--plan flag, schema 0.3.0)
- Manual legacy fallback (zero gatherer output, low seed_confidence)
- Simple consultation (single-turn /codex)

TestReplayConformance verifies turn_count, thread_id, convergence,
schema version resolution, mode propagation, and validation pass
for each scenario. Addresses data quality issues (turn_count=0,
thread_id=null) by testing against realistic inputs."
```

---

## Final Verification

Run: `cd packages/plugins/cross-model && uv run pytest ../../../tests/ -v`
Expected: All tests pass (221 existing + ~30 new from Tasks 1-6)

Run: `cd packages/plugins/cross-model && uv run ruff check scripts/ ../../../tests/`
Expected: No errors

## Summary of Deliverables

| Module | New/Modified | What This Plan Adds |
|--------|-------------|---------------------|
| `emit_analytics.py` | Modified | Resolver symmetry (Task 1), episode_id doc (Task 2) |
| `read_events.py` | New | Typed event reader with per-event schema validation (Task 4) |
| `test_read_events.py` | New | 20 tests for event reader (Task 4) |
| `test_emit_analytics.py` | Modified | Resolver tests (Task 1), episode tests (Task 2), mode tests (Task 3), replay conformance (Task 6) |
| `codex-dialogue.md` | Modified | Explicit mode return (Task 3) |
| `dialogue/SKILL.md` | Modified | Mode read from agent return (Task 3) |
| `codex/SKILL.md` | Modified | Mode documentation (Task 3) |
| `consultation-contract.md` | Modified | §17 learning retrieval/injection (Task 5) |
| `validate_consultation_contract.py` | Modified | Section count 16→17 (Task 5) |
| `test_consultation_contract_sync.py` | Modified | Updated expected counts (Task 5) |
| `tests/fixtures/*.json` | New | 5 replay fixtures (Task 6) |
