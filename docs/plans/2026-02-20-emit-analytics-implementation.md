# emit_analytics.py Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace LLM-constructed echo-append analytics emission with a deterministic Python script that handles parsing, validation, and serialization.

**Architecture:** The `/dialogue` and `/codex` skills write an input JSON file (via Write tool, bypassing shell quoting), then call `emit_analytics.py` which parses synthesis text, applies convergence mapping, validates all fields, serializes with `json.dumps`, and appends to the shared JSONL event log. The script follows the `codex_guard.py` pattern for `_append_log`, `_ts`, and error handling.

**Tech Stack:** Python 3 (stdlib only — json, uuid, re, datetime, pathlib, sys, os), pytest

**Reference:** `docs/plans/2026-02-19-cross-model-plugin-enhancements.md` §4 (authoritative event schema spec)

**Branch:** Create `feature/emit-analytics` from `main`.

**Test command:**
- Script tests: `cd packages/plugins/cross-model && uv run pytest ../../tests/test_emit_analytics.py -v`
- Guard tests (no regression): `cd packages/plugins/cross-model && uv run pytest ../../tests/test_codex_guard.py -v`

**Dependencies between tasks:**
- Task 1: independent (create script)
- Task 2: depends on Task 1 (tests import the script)
- Task 3: depends on Task 1 (SKILL.md references the script)
- Task 4: depends on Task 1 (SKILL.md references the script)

---

## Task 1: Create emit_analytics.py

**Files:**
- Create: `packages/plugins/cross-model/scripts/emit_analytics.py`

**Step 1: Create the script**

Create `packages/plugins/cross-model/scripts/emit_analytics.py` with the following complete content:

```python
"""Deterministic analytics emitter for cross-model plugin.

Reads an input JSON file describing a dialogue or consultation outcome,
parses synthesis text (for dialogue outcomes), validates all fields,
and appends a single-line JSON event to the shared event log.

Usage:
    python3 emit_analytics.py <input_file.json>

Input JSON must contain:
- "event_type": "dialogue_outcome" or "consultation_outcome"
- "pipeline": dict of pipeline state fields
- "synthesis_text": full agent output (dialogue_outcome only)
- "scope_breach": bool (dialogue_outcome only)

Exit codes:
    0 — success (event appended) or degraded (validation ok, write failed)
    1 — error (bad input, validation failure, missing file)
"""

from __future__ import annotations

import json
import os
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_LOG_PATH = Path.home() / ".claude" / ".codex-events.jsonl"
_SCHEMA_VERSION = "0.1.0"

_VALID_POSTURES = {"adversarial", "collaborative", "exploratory", "evaluative"}
_VALID_SEED_CONFIDENCE = {"normal", "low"}
_VALID_CONVERGENCE_CODES = {
    "all_resolved",
    "natural_convergence",
    "budget_exhausted",
    "error",
    "scope_breach",
}
_VALID_MODES = {"server_assisted", "manual_legacy"}
_VALID_TERMINATION_REASONS = {
    "convergence",
    "budget",
    "error",
    "scope_breach",
    "complete",
}

_COUNT_FIELDS = {
    "turn_count",
    "turn_budget",
    "resolved_count",
    "unresolved_count",
    "emerged_count",
    "assumption_count",
    "gatherer_a_lines",
    "gatherer_b_lines",
    "citations_total",
    "unique_files_total",
    "gatherer_a_unique_paths",
    "gatherer_b_unique_paths",
    "shared_citation_paths",
    "counter_count",
    "confirm_count",
    "open_count",
    "claim_count",
    "scout_count",
    "scope_root_count",
}

_DIALOGUE_REQUIRED = {
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
}

_CONSULTATION_REQUIRED = {
    "schema_version",
    "consultation_id",
    "event",
    "ts",
    "posture",
    "turn_count",
    "turn_budget",
    "termination_reason",
}


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def _ts() -> str:
    """ISO 8601 UTC timestamp with Z suffix."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _append_log(entry: dict) -> bool:
    """Append a JSON line to the event log. Returns True on success."""
    try:
        _LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(_LOG_PATH, "a") as f:
            f.write(json.dumps(entry) + "\n")
        return True
    except OSError as exc:
        print(f"log write failed: {exc}", file=sys.stderr)
        return False


def _session_id() -> str | None:
    """Read session ID from environment. Never fabricated."""
    return os.environ.get("CLAUDE_SESSION_ID") or None


# ---------------------------------------------------------------------------
# Section splitter
# ---------------------------------------------------------------------------


def _strip_fenced_blocks(text: str) -> str:
    """Remove fenced code blocks to prevent parsing headers inside them."""
    return re.sub(r"^```.*?^```", "", text, flags=re.MULTILINE | re.DOTALL)


def _split_sections(text: str) -> dict[str, str]:
    """Split synthesis text into named sections using ## or ### headers.

    Returns a dict mapping lowercase section name to section content.
    Strips fenced code blocks first to prevent matching headers inside them.
    """
    cleaned = _strip_fenced_blocks(text)
    sections: dict[str, str] = {}
    pattern = re.compile(r"^#{2,3}\s+(.+)$", re.MULTILINE)
    matches = list(pattern.finditer(cleaned))

    for i, match in enumerate(matches):
        name = match.group(1).strip().lower()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(cleaned)
        sections[name] = cleaned[start:end]

    return sections


# ---------------------------------------------------------------------------
# Synthesis parser
# ---------------------------------------------------------------------------


def parse_synthesis(text: str) -> dict:
    """Extract structured fields from codex-dialogue agent output.

    Splits text into sections for Summary/Continuation fields.
    Checkpoint prefixes (RESOLVED/UNRESOLVED/EMERGED) are searched in
    the original text since they appear inside fenced code blocks that
    get stripped during section splitting.

    Returns dict with 7 fields. Defaults on parse failure:
    - counts: 0
    - strings: None
    - booleans: False
    """
    sections = _split_sections(text)

    summary = sections.get("conversation summary", "")
    continuation = sections.get("continuation", "")

    # --- Counts from original text (not section-scoped) ---
    # Checkpoint content lives inside fenced code blocks in the agent
    # output, so searching the original text is correct here.
    resolved_count = len(
        re.findall(r"^RESOLVED:", text, re.MULTILINE | re.IGNORECASE)
    )
    unresolved_count = len(
        re.findall(r"^UNRESOLVED:", text, re.MULTILINE | re.IGNORECASE)
    )
    emerged_count = len(
        re.findall(r"^EMERGED:", text, re.MULTILINE | re.IGNORECASE)
    )

    # --- Converged from Summary (tolerant) ---
    converged = False
    m = re.search(r"\*\*Converged:\*\*\s*(.+)", summary, re.IGNORECASE)
    if m:
        converged = m.group(1).strip().lower().startswith("yes")

    # --- Turn count from Summary (handles "X of Y" and "X/Y") ---
    turn_count = 0
    m = re.search(r"\*\*Turns:\*\*\s*(\d+)", summary, re.IGNORECASE)
    if m:
        turn_count = int(m.group(1))

    # --- Thread ID from Continuation (strips backticks) ---
    thread_id = None
    m = re.search(r"\*\*Thread ID:\*\*\s*(.+)", continuation, re.IGNORECASE)
    if m:
        value = m.group(1).strip().strip("`")
        if value.lower() != "none":
            thread_id = value

    # --- Scout count from Summary Evidence (NOT Continuation) ---
    # Summary format: "**Evidence:** X scouts / Y turns, ..."
    # Continuation uses "**Evidence trajectory:**" — different field
    scout_count = 0
    m = re.search(r"\*\*Evidence:\*\*\s*(\d+)\s+scouts?", summary, re.IGNORECASE)
    if m:
        scout_count = int(m.group(1))

    return {
        "resolved_count": resolved_count,
        "unresolved_count": unresolved_count,
        "emerged_count": emerged_count,
        "converged": converged,
        "turn_count": turn_count,
        "thread_id": thread_id,
        "scout_count": scout_count,
    }


# ---------------------------------------------------------------------------
# Convergence mapper
# ---------------------------------------------------------------------------


def map_convergence(
    converged: bool,
    unresolved_count: int,
    turn_count: int,
    turn_budget: int,
    scope_breach: bool = False,
) -> tuple[str, str]:
    """Map dialogue state to (convergence_reason_code, termination_reason).

    Priority order: scope_breach > all_resolved > natural > budget > error.
    """
    if scope_breach:
        return ("scope_breach", "scope_breach")
    if converged and unresolved_count == 0:
        return ("all_resolved", "convergence")
    if converged and unresolved_count > 0:
        return ("natural_convergence", "convergence")
    if not converged and turn_count >= turn_budget:
        return ("budget_exhausted", "budget")
    return ("error", "error")


# ---------------------------------------------------------------------------
# Event builders
# ---------------------------------------------------------------------------


def build_dialogue_outcome(input_data: dict) -> dict:
    """Build a dialogue_outcome event from input JSON."""
    pipeline = input_data.get("pipeline", {})
    synthesis_text = input_data.get("synthesis_text", "")
    scope_breach = input_data.get("scope_breach", False)

    parsed = parse_synthesis(synthesis_text)

    turn_budget = pipeline.get("turn_budget", 1)
    code, reason = map_convergence(
        converged=parsed["converged"],
        unresolved_count=parsed["unresolved_count"],
        turn_count=parsed["turn_count"],
        turn_budget=turn_budget,
        scope_breach=scope_breach,
    )

    return {
        # Core
        "schema_version": _SCHEMA_VERSION,
        "consultation_id": str(uuid.uuid4()),
        "thread_id": parsed["thread_id"],
        "session_id": _session_id(),
        "event": "dialogue_outcome",
        "ts": _ts(),
        # Dialogue parameters
        "posture": pipeline.get("posture"),
        "turn_count": parsed["turn_count"],
        "turn_budget": turn_budget,
        "profile_name": pipeline.get("profile_name"),
        "mode": pipeline.get("mode", "server_assisted"),
        # Outcome
        "converged": parsed["converged"],
        "convergence_reason_code": code,
        "termination_reason": reason,
        "resolved_count": parsed["resolved_count"],
        "unresolved_count": parsed["unresolved_count"],
        "emerged_count": parsed["emerged_count"],
        # Context quality
        "seed_confidence": pipeline.get("seed_confidence", "normal"),
        "low_seed_confidence_reasons": pipeline.get(
            "low_seed_confidence_reasons", []
        ),
        "assumption_count": pipeline.get("assumption_count", 0),
        "no_assumptions_fallback": pipeline.get("no_assumptions_fallback", False),
        # Gatherer metrics
        "gatherer_a_lines": pipeline.get("gatherer_a_lines", 0),
        "gatherer_b_lines": pipeline.get("gatherer_b_lines", 0),
        "gatherer_a_retry": pipeline.get("gatherer_a_retry", False),
        "gatherer_b_retry": pipeline.get("gatherer_b_retry", False),
        "citations_total": pipeline.get("citations_total", 0),
        "unique_files_total": pipeline.get("unique_files_total", 0),
        "gatherer_a_unique_paths": pipeline.get("gatherer_a_unique_paths", 0),
        "gatherer_b_unique_paths": pipeline.get("gatherer_b_unique_paths", 0),
        "shared_citation_paths": pipeline.get("shared_citation_paths", 0),
        "counter_count": pipeline.get("counter_count", 0),
        "confirm_count": pipeline.get("confirm_count", 0),
        "open_count": pipeline.get("open_count", 0),
        "claim_count": pipeline.get("claim_count", 0),
        # Scouting
        "scout_count": parsed["scout_count"],
        # Scope envelope
        "source_classes": pipeline.get("source_classes", []),
        "scope_root_count": pipeline.get("scope_root_count", 0),
        "scope_roots_fingerprint": pipeline.get("scope_roots_fingerprint"),
        # Planning (nullable)
        "question_shaped": None,
        "shape_confidence": None,
        "assumptions_generated_count": None,
        "ambiguity_count": None,
        # Provenance (nullable)
        "provenance_unknown_count": None,
        # Linkage (nullable)
        "episode_id": None,
    }


def build_consultation_outcome(input_data: dict) -> dict:
    """Build a consultation_outcome event from input JSON."""
    pipeline = input_data.get("pipeline", {})

    return {
        "schema_version": _SCHEMA_VERSION,
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
    }


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate(event: dict, event_type: str) -> None:
    """Validate event fields. Raises ValueError on failure."""
    required = (
        _DIALOGUE_REQUIRED
        if event_type == "dialogue_outcome"
        else _CONSULTATION_REQUIRED
    )

    # Required fields
    missing = required - set(event.keys())
    if missing:
        raise ValueError(f"missing required fields: {sorted(missing)}")

    # Event type
    if event.get("event") != event_type:
        raise ValueError(
            f"event field mismatch: expected {event_type!r}, "
            f"got {event.get('event')!r}"
        )

    # Enum checks
    posture = event.get("posture")
    if posture is not None and posture not in _VALID_POSTURES:
        raise ValueError(f"invalid posture: {posture!r}")

    code = event.get("convergence_reason_code")
    if event_type == "dialogue_outcome" and code is None:
        raise ValueError("convergence_reason_code required for dialogue_outcome")
    if code is not None and code not in _VALID_CONVERGENCE_CODES:
        raise ValueError(f"invalid convergence_reason_code: {code!r}")

    reason = event.get("termination_reason")
    if reason is not None and reason not in _VALID_TERMINATION_REASONS:
        raise ValueError(f"invalid termination_reason: {reason!r}")

    seed = event.get("seed_confidence")
    if seed is not None and seed not in _VALID_SEED_CONFIDENCE:
        raise ValueError(f"invalid seed_confidence: {seed!r}")

    mode = event.get("mode")
    if mode is not None and mode not in _VALID_MODES:
        raise ValueError(f"invalid mode: {mode!r}")

    # Count fields >= 0
    for field in _COUNT_FIELDS:
        value = event.get(field)
        if value is not None and (not isinstance(value, int) or value < 0):
            raise ValueError(f"{field} must be non-negative int, got {value!r}")

    # Cross-field invariants
    turn_budget = event.get("turn_budget", 1)
    if turn_budget < 1:
        raise ValueError(f"turn_budget must be >= 1, got {turn_budget}")

    turn_count = event.get("turn_count", 0)
    if (
        event_type == "dialogue_outcome"
        and event.get("termination_reason") != "error"
        and turn_count > turn_budget
    ):
        raise ValueError(
            f"turn_count ({turn_count}) > turn_budget ({turn_budget})"
        )

    # Type checks
    converged = event.get("converged")
    if converged is not None and not isinstance(converged, bool):
        raise ValueError(
            f"converged must be bool or None, got {type(converged).__name__}"
        )

    source_classes = event.get("source_classes")
    if source_classes is not None:
        if not isinstance(source_classes, list):
            raise ValueError("source_classes must be a list")
        if not all(isinstance(s, str) for s in source_classes):
            raise ValueError("source_classes must contain only strings")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def _result(status: str, reason: str | None = None) -> str:
    """Format a status result as JSON."""
    d: dict = {"status": status}
    if reason is not None:
        d["reason"] = reason
    return json.dumps(d)


def _process(input_path: Path) -> int:
    """Process input file and emit event. Returns exit code."""
    try:
        input_data = json.loads(input_path.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        print(_result("error", f"input read failed: {exc}"))
        return 1

    event_type = input_data.get("event_type")

    try:
        if event_type == "dialogue_outcome":
            event = build_dialogue_outcome(input_data)
        elif event_type == "consultation_outcome":
            event = build_consultation_outcome(input_data)
        else:
            print(_result("error", f"unknown event_type: {event_type!r}"))
            return 1

        validate(event, event_type)
    except (ValueError, KeyError, TypeError) as exc:
        print(_result("error", str(exc)))
        return 1

    # Append to log (best-effort)
    success = _append_log(event)

    if success:
        print(_result("ok"))
    else:
        print(_result("degraded", "event valid but log write failed"))

    return 0


def main() -> int:
    """Entry point. Returns exit code."""
    if len(sys.argv) < 2:
        print(_result("error", "usage: emit_analytics.py <input_file.json>"))
        return 1

    input_path = Path(sys.argv[1])
    if not input_path.is_file():
        print(_result("error", f"input file not found: {input_path}"))
        return 1

    try:
        return _process(input_path)
    finally:
        try:
            input_path.unlink()
        except OSError:
            pass


if __name__ == "__main__":
    sys.exit(main())
```

**Step 2: Verify script loads without errors**

Run: `cd packages/plugins/cross-model && python3 -c "import importlib.util; s=importlib.util.spec_from_file_location('ea', 'scripts/emit_analytics.py'); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add packages/plugins/cross-model/scripts/emit_analytics.py
git commit -m "feat: add emit_analytics.py for deterministic analytics emission

Replaces LLM-constructed echo-append analytics with a Python script that
handles synthesis parsing, convergence mapping, field validation, and
atomic JSONL append. Follows codex_guard.py patterns (_append_log, _ts).

Key fixes from Codex review:
- Section-scoped synthesis parser (prevents cross-section mismatch)
- scout_count extracted from Summary Evidence (not Continuation)
- scope_breach convergence mapping (5-row table)
- degraded status on log-write failure (not silent ok)
- No stdin fallback (file path required)"
```

---

## Task 2: Create test_emit_analytics.py

**Files:**
- Create: `tests/test_emit_analytics.py`

**Step 1: Create the test file**

Create `tests/test_emit_analytics.py` with the following complete content:

```python
"""Tests for packages/plugins/cross-model/scripts/emit_analytics.py.

Tests the analytics emitter: synthesis parsing, convergence mapping,
event building, validation, and JSONL append.
"""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Module import (same pattern as test_codex_guard.py)
# ---------------------------------------------------------------------------

MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "packages"
    / "plugins"
    / "cross-model"
    / "scripts"
    / "emit_analytics.py"
)
SPEC = importlib.util.spec_from_file_location("emit_analytics", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_SYNTHESIS = """\
### Conversation Summary
- **Topic:** Analytics design
- **Goal:** Evaluate design quality
- **Posture:** Evaluative
- **Turns:** 4 of 8 budget
- **Converged:** Yes — both sides agreed on core findings
- **Trajectory:** T1:advancing → T2:advancing → T3:advancing → T4:static
- **Evidence:** 3 scouts / 4 turns, entities: emit_analytics.py, codex_guard.py

### Key Outcomes

Some narrative content here.

### Areas of Agreement

Points both sides converged on.

### Contested Claims

Some contested claims here.

### Open Questions

Some open questions here.

### Continuation
- **Thread ID:** thread-abc-123
- **Continuation warranted:** No
- **Unresolved items carried forward:** none
- **Recommended posture for continuation:** N/A
- **Evidence trajectory:** T2: emit_analytics.py (CLAIM confirmed), T3: codex_guard.py

### Synthesis Checkpoint
```
## Synthesis Checkpoint
RESOLVED: echo-append is unsafe [confidence: High] [basis: convergence]
RESOLVED: Step 7 ownership correct [confidence: High] [basis: convergence]
RESOLVED: Need deterministic script [confidence: High] [basis: convergence]
RESOLVED: extraction drift confirmed [confidence: High] [basis: evidence]
RESOLVED: session_id policy [confidence: Medium] [basis: concession]
UNRESOLVED: dead field retention [raised: turn 3]
EMERGED: ownership-vs-mechanics [source: dialogue-born]
EMERGED: session_id_source field [source: dialogue-born]
```
"""

SAMPLE_PIPELINE = {
    "posture": "evaluative",
    "turn_budget": 8,
    "profile_name": None,
    "seed_confidence": "normal",
    "low_seed_confidence_reasons": [],
    "assumption_count": 4,
    "no_assumptions_fallback": False,
    "gatherer_a_lines": 23,
    "gatherer_b_lines": 8,
    "gatherer_a_retry": False,
    "gatherer_b_retry": False,
    "citations_total": 24,
    "unique_files_total": 7,
    "gatherer_a_unique_paths": 7,
    "gatherer_b_unique_paths": 3,
    "shared_citation_paths": 3,
    "counter_count": 3,
    "confirm_count": 2,
    "open_count": 7,
    "claim_count": 19,
    "source_classes": ["code", "docs"],
    "scope_root_count": 3,
    "scope_roots_fingerprint": None,
}


def _dialogue_input(
    synthesis: str = SAMPLE_SYNTHESIS,
    pipeline: dict | None = None,
    scope_breach: bool = False,
) -> dict:
    return {
        "event_type": "dialogue_outcome",
        "synthesis_text": synthesis,
        "scope_breach": scope_breach,
        "pipeline": pipeline or SAMPLE_PIPELINE,
    }


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
        },
    }


# ---------------------------------------------------------------------------
# TestSplitSections
# ---------------------------------------------------------------------------


class TestSplitSections:
    def test_basic_split(self) -> None:
        text = "### Section One\ncontent one\n### Section Two\ncontent two\n"
        result = MODULE._split_sections(text)
        assert "section one" in result
        assert "section two" in result

    def test_case_normalized_keys(self) -> None:
        text = "### Synthesis Checkpoint\nstuff\n### Synthesis checkpoint\nmore\n"
        result = MODULE._split_sections(text)
        assert "synthesis checkpoint" in result

    def test_strips_fenced_blocks(self) -> None:
        text = "### Outer\n```\n## Inner Header\ncontent\n```\n"
        result = MODULE._split_sections(text)
        assert "inner header" not in result
        assert "outer" in result

    def test_nested_fence_with_level2_header(self) -> None:
        """Regression: ## Synthesis Checkpoint inside code fence must not create section."""
        text = (
            "### Synthesis Checkpoint\n"
            "```\n"
            "## Synthesis Checkpoint\n"
            "RESOLVED: item [confidence: High]\n"
            "```\n"
        )
        result = MODULE._split_sections(text)
        # Only one section, from the ### header
        assert len(result) == 1
        assert "synthesis checkpoint" in result


# ---------------------------------------------------------------------------
# TestParseSynthesis
# ---------------------------------------------------------------------------


class TestParseSynthesis:
    def test_full_parse(self) -> None:
        result = MODULE.parse_synthesis(SAMPLE_SYNTHESIS)
        assert result["resolved_count"] == 5
        assert result["unresolved_count"] == 1
        assert result["emerged_count"] == 2
        assert result["converged"] is True
        assert result["turn_count"] == 4
        assert result["thread_id"] == "thread-abc-123"
        assert result["scout_count"] == 3

    def test_converged_no(self) -> None:
        text = "### Conversation Summary\n- **Converged:** No -- hit turn limit\n"
        result = MODULE.parse_synthesis(text)
        assert result["converged"] is False

    def test_converged_yes_case_insensitive(self) -> None:
        text = "### Conversation Summary\n- **Converged:** YES - strong agreement\n"
        result = MODULE.parse_synthesis(text)
        assert result["converged"] is True

    def test_converged_missing(self) -> None:
        result = MODULE.parse_synthesis("### Conversation Summary\n- **Topic:** test\n")
        assert result["converged"] is False

    def test_turn_count(self) -> None:
        text = "### Conversation Summary\n- **Turns:** 6 of 10 budget\n"
        result = MODULE.parse_synthesis(text)
        assert result["turn_count"] == 6

    def test_thread_id_none(self) -> None:
        text = "### Continuation\n- **Thread ID:** none\n"
        result = MODULE.parse_synthesis(text)
        assert result["thread_id"] is None

    def test_thread_id_with_backticks(self) -> None:
        text = "### Continuation\n- **Thread ID:** `thread-abc`\n"
        result = MODULE.parse_synthesis(text)
        assert result["thread_id"] == "thread-abc"

    def test_scout_count_from_summary_not_continuation(self) -> None:
        """Regression: scout_count must come from Summary Evidence, not Continuation."""
        text = (
            "### Conversation Summary\n"
            "- **Evidence:** 5 scouts / 8 turns, entities: foo.py\n"
            "\n### Continuation\n"
            "- **Evidence trajectory:** T2: foo.py, T5: bar.py\n"
        )
        result = MODULE.parse_synthesis(text)
        assert result["scout_count"] == 5

    def test_scout_count_zero_when_none(self) -> None:
        text = "### Conversation Summary\n- **Evidence:** 0 scouts / 4 turns\n"
        result = MODULE.parse_synthesis(text)
        assert result["scout_count"] == 0

    def test_empty_text(self) -> None:
        result = MODULE.parse_synthesis("")
        assert result["resolved_count"] == 0
        assert result["unresolved_count"] == 0
        assert result["emerged_count"] == 0
        assert result["converged"] is False
        assert result["turn_count"] == 0
        assert result["thread_id"] is None
        assert result["scout_count"] == 0

    def test_partial_synthesis_missing_continuation(self) -> None:
        text = (
            "### Conversation Summary\n"
            "- **Converged:** Yes\n"
            "- **Turns:** 3 of 5\n"
            "- **Evidence:** 1 scout / 3 turns\n"
            "\n### Synthesis Checkpoint\n"
            "RESOLVED: something [confidence: High]\n"
        )
        result = MODULE.parse_synthesis(text)
        assert result["converged"] is True
        assert result["turn_count"] == 3
        assert result["thread_id"] is None
        assert result["resolved_count"] == 1
        assert result["scout_count"] == 1

    def test_checkpoint_case_insensitive(self) -> None:
        text = "### Synthesis Checkpoint\nresolved: item one\nResolved: item two\n"
        result = MODULE.parse_synthesis(text)
        assert result["resolved_count"] == 2

    def test_checkpoint_fallback_to_whole_text(self) -> None:
        """When no Synthesis Checkpoint section header, search whole text."""
        text = "RESOLVED: item one\nRESOLVED: item two\nUNRESOLVED: item three\n"
        result = MODULE.parse_synthesis(text)
        assert result["resolved_count"] == 2
        assert result["unresolved_count"] == 1

    def test_scout_count_none_natural_language(self) -> None:
        """Agent may emit 'none (no scouts executed)' instead of '0 scouts'."""
        text = "### Conversation Summary\n- **Evidence:** none (no scouts executed)\n"
        result = MODULE.parse_synthesis(text)
        assert result["scout_count"] == 0


# ---------------------------------------------------------------------------
# TestMapConvergence
# ---------------------------------------------------------------------------


class TestMapConvergence:
    def test_all_resolved(self) -> None:
        assert MODULE.map_convergence(True, 0, 4, 8) == (
            "all_resolved",
            "convergence",
        )

    def test_natural_convergence(self) -> None:
        assert MODULE.map_convergence(True, 2, 4, 8) == (
            "natural_convergence",
            "convergence",
        )

    def test_budget_exhausted(self) -> None:
        assert MODULE.map_convergence(False, 1, 8, 8) == (
            "budget_exhausted",
            "budget",
        )

    def test_error(self) -> None:
        assert MODULE.map_convergence(False, 0, 3, 8) == ("error", "error")

    def test_scope_breach_overrides(self) -> None:
        """scope_breach takes priority even if converged=True."""
        assert MODULE.map_convergence(True, 0, 4, 8, scope_breach=True) == (
            "scope_breach",
            "scope_breach",
        )


# ---------------------------------------------------------------------------
# TestBuildDialogueOutcome
# ---------------------------------------------------------------------------


class TestBuildDialogueOutcome:
    def test_all_fields_present(self) -> None:
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        expected_fields = {
            "schema_version", "consultation_id", "thread_id", "session_id",
            "event", "ts", "posture", "turn_count", "turn_budget",
            "profile_name", "mode", "converged", "convergence_reason_code",
            "termination_reason", "resolved_count", "unresolved_count",
            "emerged_count", "seed_confidence", "low_seed_confidence_reasons",
            "assumption_count", "no_assumptions_fallback",
            "gatherer_a_lines", "gatherer_b_lines",
            "gatherer_a_retry", "gatherer_b_retry",
            "citations_total", "unique_files_total",
            "gatherer_a_unique_paths", "gatherer_b_unique_paths",
            "shared_citation_paths", "counter_count", "confirm_count",
            "open_count", "claim_count", "scout_count",
            "source_classes", "scope_root_count", "scope_roots_fingerprint",
            "question_shaped", "shape_confidence",
            "assumptions_generated_count", "ambiguity_count",
            "provenance_unknown_count", "episode_id",
        }
        assert set(event.keys()) == expected_fields

    def test_consultation_id_is_uuid(self) -> None:
        import uuid as uuid_mod

        event = MODULE.build_dialogue_outcome(_dialogue_input())
        uuid_mod.UUID(event["consultation_id"])  # raises on invalid

    def test_ts_format(self) -> None:
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        assert event["ts"].endswith("Z")
        assert "T" in event["ts"]

    def test_ts_format_strict(self) -> None:
        """Timestamp must be ISO 8601 with Z suffix, no microseconds."""
        import re as re_mod

        event = MODULE.build_dialogue_outcome(_dialogue_input())
        assert re_mod.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", event["ts"])

    def test_session_id_from_env(self, monkeypatch) -> None:
        monkeypatch.setenv("CLAUDE_SESSION_ID", "sess-test-123")
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        assert event["session_id"] == "sess-test-123"

    def test_session_id_missing(self, monkeypatch) -> None:
        monkeypatch.delenv("CLAUDE_SESSION_ID", raising=False)
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        assert event["session_id"] is None

    def test_pipeline_fields_passed_through(self) -> None:
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        assert event["posture"] == "evaluative"
        assert event["turn_budget"] == 8
        assert event["gatherer_a_lines"] == 23
        assert event["source_classes"] == ["code", "docs"]

    def test_nullable_fields_are_none(self) -> None:
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        assert event["question_shaped"] is None
        assert event["provenance_unknown_count"] is None
        assert event["episode_id"] is None

    def test_scope_breach_event(self) -> None:
        event = MODULE.build_dialogue_outcome(
            _dialogue_input(scope_breach=True)
        )
        assert event["convergence_reason_code"] == "scope_breach"
        assert event["termination_reason"] == "scope_breach"


# ---------------------------------------------------------------------------
# TestBuildConsultationOutcome
# ---------------------------------------------------------------------------


class TestBuildConsultationOutcome:
    def test_field_count(self) -> None:
        event = MODULE.build_consultation_outcome(_consultation_input())
        assert len(event) == 13

    def test_converged_null(self) -> None:
        event = MODULE.build_consultation_outcome(_consultation_input())
        assert event["converged"] is None

    def test_termination_complete(self) -> None:
        event = MODULE.build_consultation_outcome(_consultation_input())
        assert event["termination_reason"] == "complete"

    def test_no_convergence_reason_code(self) -> None:
        """consultation_outcome should not include convergence_reason_code."""
        event = MODULE.build_consultation_outcome(_consultation_input())
        assert "convergence_reason_code" not in event

    def test_thread_id_from_pipeline(self) -> None:
        event = MODULE.build_consultation_outcome(_consultation_input())
        assert event["thread_id"] == "thread-xyz-789"


# ---------------------------------------------------------------------------
# TestValidate
# ---------------------------------------------------------------------------


class TestValidate:
    def test_valid_dialogue_passes(self) -> None:
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        MODULE.validate(event, "dialogue_outcome")  # no exception

    def test_valid_consultation_passes(self) -> None:
        event = MODULE.build_consultation_outcome(_consultation_input())
        MODULE.validate(event, "consultation_outcome")  # no exception

    def test_missing_required_field(self) -> None:
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        del event["consultation_id"]
        with pytest.raises(ValueError, match="missing required fields"):
            MODULE.validate(event, "dialogue_outcome")

    def test_invalid_posture_enum(self) -> None:
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        event["posture"] = "aggressive"
        with pytest.raises(ValueError, match="invalid posture"):
            MODULE.validate(event, "dialogue_outcome")

    def test_invalid_termination_reason(self) -> None:
        event = MODULE.build_consultation_outcome(_consultation_input())
        event["termination_reason"] = "timeout"
        with pytest.raises(ValueError, match="invalid termination_reason"):
            MODULE.validate(event, "consultation_outcome")

    def test_negative_count(self) -> None:
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        event["resolved_count"] = -1
        with pytest.raises(ValueError, match="non-negative int"):
            MODULE.validate(event, "dialogue_outcome")

    def test_turn_count_exceeds_budget(self) -> None:
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        event["turn_count"] = 10
        event["turn_budget"] = 8
        with pytest.raises(ValueError, match="turn_count.*turn_budget"):
            MODULE.validate(event, "dialogue_outcome")

    def test_turn_count_exceeds_budget_allowed_on_error(self) -> None:
        """turn_count > turn_budget is allowed when termination_reason is error."""
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        event["turn_count"] = 10
        event["turn_budget"] = 8
        event["termination_reason"] = "error"
        MODULE.validate(event, "dialogue_outcome")  # no exception

    def test_dialogue_rejects_none_convergence_code(self) -> None:
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        event["convergence_reason_code"] = None
        with pytest.raises(ValueError, match="convergence_reason_code required"):
            MODULE.validate(event, "dialogue_outcome")

    def test_consultation_multi_turn_valid(self) -> None:
        """Multi-turn /codex: turn_count > turn_budget is valid."""
        event = MODULE.build_consultation_outcome(
            _consultation_input({"posture": "collaborative", "turn_count": 3, "turn_budget": 1})
        )
        MODULE.validate(event, "consultation_outcome")  # no exception

    def test_invalid_mode(self) -> None:
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        event["mode"] = "raw_socket"
        with pytest.raises(ValueError, match="invalid mode"):
            MODULE.validate(event, "dialogue_outcome")


# ---------------------------------------------------------------------------
# TestAppendLog
# ---------------------------------------------------------------------------


class TestAppendLog:
    def test_appends_valid_jsonl(self, tmp_path, monkeypatch) -> None:
        log_path = tmp_path / "events.jsonl"
        monkeypatch.setattr(MODULE, "_LOG_PATH", log_path)
        entry = {"event": "test", "value": 42}
        assert MODULE._append_log(entry) is True
        line = log_path.read_text().strip()
        assert json.loads(line) == entry

    def test_appends_multiple(self, tmp_path, monkeypatch) -> None:
        log_path = tmp_path / "events.jsonl"
        monkeypatch.setattr(MODULE, "_LOG_PATH", log_path)
        MODULE._append_log({"n": 1})
        MODULE._append_log({"n": 2})
        lines = log_path.read_text().strip().split("\n")
        assert len(lines) == 2
        assert json.loads(lines[0])["n"] == 1
        assert json.loads(lines[1])["n"] == 2

    def test_creates_parent_dir(self, tmp_path, monkeypatch) -> None:
        log_path = tmp_path / "nested" / "dir" / "events.jsonl"
        monkeypatch.setattr(MODULE, "_LOG_PATH", log_path)
        assert MODULE._append_log({"test": True}) is True
        assert log_path.exists()

    def test_oserror_returns_false(self, tmp_path, monkeypatch) -> None:
        log_path = tmp_path / "readonly" / "events.jsonl"
        (tmp_path / "readonly").mkdir()
        (tmp_path / "readonly").chmod(0o444)
        monkeypatch.setattr(MODULE, "_LOG_PATH", log_path)
        assert MODULE._append_log({"test": True}) is False
        (tmp_path / "readonly").chmod(0o755)  # cleanup


# ---------------------------------------------------------------------------
# TestMain
# ---------------------------------------------------------------------------


class TestMain:
    def test_dialogue_end_to_end(self, tmp_path, monkeypatch, capsys) -> None:
        log_path = tmp_path / "events.jsonl"
        monkeypatch.setattr(MODULE, "_LOG_PATH", log_path)

        input_file = tmp_path / "input.json"
        input_file.write_text(json.dumps(_dialogue_input()))
        monkeypatch.setattr("sys.argv", ["emit_analytics.py", str(input_file)])

        exit_code = MODULE.main()
        assert exit_code == 0
        assert not input_file.exists()  # cleaned up

        output = json.loads(capsys.readouterr().out.strip())
        assert output["status"] == "ok"

        event = json.loads(log_path.read_text().strip())
        assert event["event"] == "dialogue_outcome"
        assert event["schema_version"] == "0.1.0"
        assert event["resolved_count"] == 5

    def test_consultation_end_to_end(self, tmp_path, monkeypatch) -> None:
        log_path = tmp_path / "events.jsonl"
        monkeypatch.setattr(MODULE, "_LOG_PATH", log_path)

        input_file = tmp_path / "input.json"
        input_file.write_text(json.dumps(_consultation_input()))
        monkeypatch.setattr("sys.argv", ["emit_analytics.py", str(input_file)])

        exit_code = MODULE.main()
        assert exit_code == 0

        event = json.loads(log_path.read_text().strip())
        assert event["event"] == "consultation_outcome"
        assert event["convergence_reason_code"] is None

    def test_invalid_json(self, tmp_path, monkeypatch, capsys) -> None:
        input_file = tmp_path / "bad.json"
        input_file.write_text("not json")
        monkeypatch.setattr("sys.argv", ["emit_analytics.py", str(input_file)])

        exit_code = MODULE.main()
        assert exit_code == 1
        output = json.loads(capsys.readouterr().out.strip())
        assert output["status"] == "error"

    def test_unknown_event_type(self, tmp_path, monkeypatch, capsys) -> None:
        input_file = tmp_path / "input.json"
        input_file.write_text(json.dumps({"event_type": "unknown"}))
        monkeypatch.setattr("sys.argv", ["emit_analytics.py", str(input_file)])

        exit_code = MODULE.main()
        assert exit_code == 1
        output = json.loads(capsys.readouterr().out.strip())
        assert output["status"] == "error"

    def test_missing_file(self, monkeypatch, capsys) -> None:
        monkeypatch.setattr(
            "sys.argv", ["emit_analytics.py", "/nonexistent/input.json"]
        )
        exit_code = MODULE.main()
        assert exit_code == 1

    def test_no_args(self, monkeypatch, capsys) -> None:
        monkeypatch.setattr("sys.argv", ["emit_analytics.py"])
        exit_code = MODULE.main()
        assert exit_code == 1

    def test_degraded_on_write_failure(self, tmp_path, monkeypatch, capsys) -> None:
        readonly_dir = tmp_path / "readonly"
        readonly_dir.mkdir()
        log_path = readonly_dir / "events.jsonl"
        readonly_dir.chmod(0o444)
        monkeypatch.setattr(MODULE, "_LOG_PATH", log_path)

        input_file = tmp_path / "input.json"
        input_file.write_text(json.dumps(_consultation_input()))
        monkeypatch.setattr("sys.argv", ["emit_analytics.py", str(input_file)])

        exit_code = MODULE.main()
        assert exit_code == 0  # non-blocking
        output = json.loads(capsys.readouterr().out.strip())
        assert output["status"] == "degraded"
        readonly_dir.chmod(0o755)  # cleanup

    def test_input_cleanup_on_validation_error(self, tmp_path, monkeypatch) -> None:
        """Input file must be deleted even when validation fails."""
        log_path = tmp_path / "events.jsonl"
        monkeypatch.setattr(MODULE, "_LOG_PATH", log_path)

        input_file = tmp_path / "input.json"
        input_file.write_text(json.dumps({"event_type": "unknown_type"}))
        monkeypatch.setattr("sys.argv", ["emit_analytics.py", str(input_file)])

        MODULE.main()
        assert not input_file.exists()  # cleaned up despite error
```

**Step 2: Run tests**

Run: `cd packages/plugins/cross-model && uv run pytest ../../tests/test_emit_analytics.py -v`
Expected: ALL PASS (~60 tests)

**Step 3: Run existing guard tests (no regression)**

Run: `cd packages/plugins/cross-model && uv run pytest ../../tests/test_codex_guard.py -v`
Expected: ALL PASS (28 tests)

**Step 4: Commit**

```bash
git add tests/test_emit_analytics.py
git commit -m "test: add 60 tests for emit_analytics.py

Covers section splitting (fence-aware, case-normalized), synthesis
parsing (section-scoped extraction, scout_count drift regression),
convergence mapping (5-row table including scope_breach), event
builders (dialogue 44-field + consultation 13-field), validation
(enums, mode, event-type-specific convergence codes, cross-field
invariants), JSONL append, input cleanup on error paths, and
end-to-end integration via main() entry point."
```

---

## Task 3: Rewrite dialogue SKILL.md Step 7

**Files:**
- Modify: `packages/plugins/cross-model/skills/dialogue/SKILL.md:190-331`

**Step 1: Replace Step 7 section**

In `packages/plugins/cross-model/skills/dialogue/SKILL.md`, replace lines 190-302 (from `### Step 7: Emit analytics` through the `echo` append block) with:

```markdown
### Step 7: Emit analytics

After presenting synthesis to the user, emit a `dialogue_outcome` event via the analytics emitter script. Analytics is best-effort — failures do not block the user from seeing the synthesis.

**7a. Write input file**

Use the Write tool to create `/tmp/claude_analytics_{random_suffix}.json` containing the input JSON for the emitter script. The file has three top-level fields:

| Field | Type | Source |
|-------|------|--------|
| `event_type` | `"dialogue_outcome"` | Literal |
| `synthesis_text` | string | Full raw output from the `codex-dialogue` agent's Task tool return value |
| `scope_breach` | bool | Determined during Step 5-6 delegation. `true` if the codex-dialogue agent returned a resume capsule instead of a synthesis (per consultation contract §6 scope breach protocol). `false` otherwise. Passed through as pipeline state — not inferred from synthesis text. |
| `pipeline` | object | Pipeline state accumulated during Steps 1-6 (see field table below) |

Pipeline fields to include:

| Pipeline Field | Source Step | Type |
|----------------|-----------|------|
| `posture` | Args | string |
| `turn_budget` | Args | int |
| `profile_name` | Args | string or null |
| `seed_confidence` | Step 4 | `"normal"` or `"low"` |
| `low_seed_confidence_reasons` | Step 4 | list (empty at schema 0.1.0) |
| `assumption_count` | Step 1 | int |
| `no_assumptions_fallback` | Step 1 | bool |
| `gatherer_a_lines` | Step 3 | int |
| `gatherer_b_lines` | Step 3 | int |
| `gatherer_a_retry` | Step 3 | bool |
| `gatherer_b_retry` | Step 3 | bool |
| `citations_total` | Step 4 | int |
| `unique_files_total` | Step 4 | int |
| `gatherer_a_unique_paths` | Step 3 | int |
| `gatherer_b_unique_paths` | Step 3 | int |
| `shared_citation_paths` | Step 3 | int |
| `counter_count` | Step 3 | int |
| `confirm_count` | Step 3 | int |
| `open_count` | Step 3 | int |
| `claim_count` | Step 3 | int |
| `source_classes` | Step 5 | list of strings |
| `scope_root_count` | Step 5 | int |
| `scope_roots_fingerprint` | Step 5 | string or null |
| `mode` | Args | `"server_assisted"` or `"manual_legacy"` |

**7b. Run emitter**

The emitter script is at `scripts/emit_analytics.py` within this plugin. Construct the path from this skill's base directory (shown in the header): replace the trailing `skills/dialogue` with `scripts/emit_analytics.py`.

```bash
python3 "{plugin_root}/scripts/emit_analytics.py" /tmp/claude_analytics_{random_suffix}.json
```

**7c. Check result**

The script prints a JSON status line to stdout:
- `{"status": "ok"}` — event appended successfully
- `{"status": "degraded", "reason": "..."}` — input valid, but log write failed
- `{"status": "error", "reason": "..."}` — bad input or validation failure

On `error` or `degraded`, warn the user: `"Analytics emission failed: {reason}. This does not affect the consultation results."` Do not retry.
```

**Step 2: Update Constants table entries**

In the Constants table (around line 304), replace the analytics entries:

Replace:
```markdown
| Analytics schema version | 0.1.0 | Event schema version |
| Analytics event log | `~/.claude/.codex-events.jsonl` | Shared with codex_guard.py |
```

With:
```markdown
| Analytics emitter | `scripts/emit_analytics.py` | Relative to plugin root |
| Analytics event log | `~/.claude/.codex-events.jsonl` | Shared with codex_guard.py |
```

**Step 3: Update Failure Modes entries**

In the Failure Modes table, replace:
```markdown
| Analytics emission fails | Warn user, do not retry. Synthesis already presented. |
| Synthesis parse failure | Use defaults (0/null/false). Emit event with available fields. |
```

With:
```markdown
| Analytics emitter returns error | Warn user with reason from script output. Do not retry. |
| Analytics emitter returns degraded | Warn user. Event was valid but log write failed. Do not retry. |
| Analytics emitter script not found | Warn user: "Analytics emitter not found." Skip emission. |
```

**Step 4: Commit**

```bash
git add packages/plugins/cross-model/skills/dialogue/SKILL.md
git commit -m "refactor(dialogue): rewrite Step 7 to use emit_analytics.py

Step 7 now writes an input JSON file (via Write tool) and calls the
deterministic emitter script instead of constructing 44-field JSON in
LLM working memory and echo-appending it. The script handles synthesis
parsing, convergence mapping, validation, and atomic JSONL append.

Fixes:
- scout_count extraction source (Summary Evidence, not Continuation)
- scope_breach convergence mapping
- session_id from CLAUDE_SESSION_ID env var
- dead fields default to null (not empty)"
```

---

## Task 4: Rewrite codex SKILL.md Analytics Emission

**Files:**
- Modify: `packages/plugins/cross-model/skills/codex/SKILL.md:217-248`

**Step 1: Replace Analytics Emission section**

In `packages/plugins/cross-model/skills/codex/SKILL.md`, replace lines 217-248 (from `### Analytics Emission` through `If the append fails, log a warning. Do not retry.`) with:

```markdown
### Analytics Emission

After capturing diagnostics, emit a `consultation_outcome` event via the analytics emitter script. Analytics is best-effort — failures do not block the consultation response.

**Write input file**

Use the Write tool to create `/tmp/claude_analytics_{random_suffix}.json`:

```json
{
  "event_type": "consultation_outcome",
  "pipeline": {
    "posture": "{resolved posture}",
    "thread_id": "{threadId from Codex response, or null}",
    "turn_count": 1,
    "turn_budget": 1,
    "profile_name": null,
    "mode": "server_assisted"
  }
}
```

For multi-turn `/codex` consultations (continued with `codex-reply`), increment `turn_count` for each round-trip.

**Run emitter**

The emitter script is at `scripts/emit_analytics.py` within this plugin. Construct the path from this skill's base directory: replace the trailing `skills/codex` with `scripts/emit_analytics.py`.

```bash
python3 "{plugin_root}/scripts/emit_analytics.py" /tmp/claude_analytics_{random_suffix}.json
```

On `error` or `degraded` output, warn the user. Do not retry.
```

**Step 2: Commit**

```bash
git add packages/plugins/cross-model/skills/codex/SKILL.md
git commit -m "refactor(codex): rewrite analytics emission to use emit_analytics.py

Replaces echo-append with Write-tool-to-file + script invocation.
consultation_outcome emits 13 fields (no convergence_reason_code —
per authoritative spec, this field is dialogue-only)."
```

---

## Final Verification

1. Run: `cd packages/plugins/cross-model && uv run pytest ../../tests/test_emit_analytics.py -v`
   Expected: ALL PASS (~60 tests)

2. Run: `cd packages/plugins/cross-model && uv run pytest ../../tests/test_codex_guard.py -v`
   Expected: ALL PASS (28 tests, no regression)

3. Marketplace update: `claude plugin marketplace update cross-model && claude plugin install cross-model@cross-model`

4. Integration test `/dialogue`: run a dialogue, verify `dialogue_outcome` event with `jq 'select(.event == "dialogue_outcome")' ~/.claude/.codex-events.jsonl | tail -1`

5. Integration test `/codex`: run a consultation, verify `consultation_outcome` event with `jq 'select(.event == "consultation_outcome")' ~/.claude/.codex-events.jsonl | tail -1`

6. JSONL integrity: `jq empty ~/.claude/.codex-events.jsonl`

## Summary of Deliverables

| File | New/Modified | What This Plan Adds |
|------|-------------|---------------------|
| `scripts/emit_analytics.py` | New | Deterministic analytics emitter — synthesis parser, convergence mapper, validators, atomic JSONL append |
| `tests/test_emit_analytics.py` | New | ~60 tests — section splitting, parser, mapper, builders, validation (event-type-specific), integration, cleanup |
| `skills/dialogue/SKILL.md` | Modified | Step 7 rewritten: Write input file + call script (was: LLM-constructed JSON + echo-append) |
| `skills/codex/SKILL.md` | Modified | Analytics Emission rewritten: Write input file + call script. 13 fields (no convergence_reason_code) |

All `scripts/` and `skills/` paths relative to `packages/plugins/cross-model/`.
