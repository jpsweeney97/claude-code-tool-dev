# audit-loop v1.1.0: Script Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add scripts for state management, report generation, and validation to enable agentic operation with persistent state.

**Architecture:** Python scripts using stdlib only (skill scripts run in environments without package managers). Subparser-based CLI for state.py. JSON state files with atomic writes. Exit codes: 0=success, 1=error, 2=args, 10=validation fail, 11=not found.

**Tech Stack:** Python 3.12, argparse, json, pathlib, tempfile

---

## Directory Structure

```
.claude/skills/audit-loop/
├── SKILL.md                    # Update version to 1.1.0
├── templates/
│   └── report.md               # Replace with reference note
├── scripts/
│   ├── _common.py              # Shared utilities
│   ├── state.py                # State CRUD with subcommands
│   ├── generate_report.py      # Markdown report generator
│   ├── validate_state.py       # Pre-operation validation
│   └── calculate_stakes.py     # Calibration scoring
└── tests/
    ├── __init__.py
    ├── test_common.py
    ├── test_state.py
    ├── test_generate_report.py
    ├── test_validate_state.py
    └── test_calculate_stakes.py
```

---

## Task 1: Create _common.py Foundation

**Files:**
- Create: `.claude/skills/audit-loop/scripts/_common.py`
- Create: `.claude/skills/audit-loop/tests/__init__.py`
- Create: `.claude/skills/audit-loop/tests/test_common.py`

### Step 1.1: Create tests directory

```bash
mkdir -p .claude/skills/audit-loop/tests
touch .claude/skills/audit-loop/tests/__init__.py
```

### Step 1.2: Write failing test for Result dataclass

```python
# .claude/skills/audit-loop/tests/test_common.py
"""Tests for _common module."""
import json
import sys
from pathlib import Path

# Add scripts to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


def test_result_success():
    """Result.success() creates success result."""
    from _common import Result

    result = Result.success("Operation completed", data={"key": "value"})
    assert result.ok is True
    assert result.message == "Operation completed"
    assert result.data == {"key": "value"}
    assert result.errors == []


def test_result_failure():
    """Result.failure() creates failure result."""
    from _common import Result

    result = Result.failure("Something failed", errors=["Error 1"])
    assert result.ok is False
    assert result.message == "Something failed"
    assert result.errors == ["Error 1"]


def test_result_to_json():
    """Result.to_json() produces valid JSON."""
    from _common import Result

    result = Result.success("Done", data={"count": 5})
    output = result.to_json()
    parsed = json.loads(output)
    assert parsed["ok"] is True
    assert parsed["data"]["count"] == 5
```

### Step 1.3: Run test to verify it fails

Run: `cd .claude/skills/audit-loop && python -m pytest tests/test_common.py::test_result_success -v`
Expected: FAIL with "ModuleNotFoundError: No module named '_common'"

### Step 1.4: Create scripts directory

```bash
mkdir -p .claude/skills/audit-loop/scripts
```

### Step 1.5: Write Result dataclass implementation

```python
# .claude/skills/audit-loop/scripts/_common.py
#!/usr/bin/env python3
"""
Shared utilities for audit-loop skill scripts.

Provides constants, data classes, and helper functions used across
state management, report generation, and validation scripts.
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


# =============================================================================
# EXIT CODES
# =============================================================================

EXIT_SUCCESS: int = 0
EXIT_ERROR: int = 1
EXIT_ARGS: int = 2
EXIT_VALIDATION: int = 10
EXIT_NOT_FOUND: int = 11


# =============================================================================
# CONSTANTS
# =============================================================================

SCHEMA_VERSION: str = "1.0"

PHASES: list[str] = [
    "stakes_assessment",
    "definition",
    "execution",
    "verification",
    "triage",
    "design",
    "verify",
    "ship",
]

MAX_CYCLES: int = 10

CALIBRATION_LEVELS: dict[str, tuple[int, int]] = {
    "light": (4, 6),
    "medium": (7, 9),
    "deep": (10, 12),
}


# =============================================================================
# RESULT DATACLASS
# =============================================================================

@dataclass
class Result:
    """Standardized operation result."""

    ok: bool
    message: str
    data: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @classmethod
    def success(
        cls,
        message: str,
        data: dict[str, Any] | None = None,
        warnings: list[str] | None = None,
    ) -> Result:
        """Create a success result."""
        return cls(
            ok=True,
            message=message,
            data=data or {},
            errors=[],
            warnings=warnings or [],
        )

    @classmethod
    def failure(
        cls,
        message: str,
        errors: list[str] | None = None,
        data: dict[str, Any] | None = None,
    ) -> Result:
        """Create a failure result."""
        return cls(
            ok=False,
            message=message,
            data=data or {},
            errors=errors or [],
            warnings=[],
        )

    def to_json(self, indent: int = 2) -> str:
        """Serialize result to JSON string."""
        return json.dumps(
            {
                "ok": self.ok,
                "message": self.message,
                "data": self.data,
                "errors": self.errors,
                "warnings": self.warnings,
            },
            indent=indent,
        )
```

### Step 1.6: Run test to verify it passes

Run: `cd .claude/skills/audit-loop && python -m pytest tests/test_common.py -v`
Expected: 3 passed

### Step 1.7: Write test for atomic_write

Add to `tests/test_common.py`:

```python
def test_atomic_write_creates_file(tmp_path):
    """atomic_write creates file with content."""
    from _common import atomic_write

    target = tmp_path / "test.json"
    content = '{"key": "value"}'

    atomic_write(target, content)

    assert target.exists()
    assert target.read_text() == content


def test_atomic_write_overwrites_existing(tmp_path):
    """atomic_write replaces existing file atomically."""
    from _common import atomic_write

    target = tmp_path / "test.json"
    target.write_text("old content")

    atomic_write(target, "new content")

    assert target.read_text() == "new content"
```

### Step 1.8: Run test to verify it fails

Run: `cd .claude/skills/audit-loop && python -m pytest tests/test_common.py::test_atomic_write_creates_file -v`
Expected: FAIL with "cannot import name 'atomic_write'"

### Step 1.9: Add atomic_write implementation

Add to `scripts/_common.py`:

```python
# =============================================================================
# FILE OPERATIONS
# =============================================================================

def atomic_write(path: Path, content: str) -> None:
    """
    Write content to file atomically using temp file + rename.

    Prevents data corruption if process is interrupted during write.

    Args:
        path: Target file path
        content: Content to write
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fd, temp_path = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        Path(temp_path).rename(path)
    except Exception:
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        raise
```

### Step 1.10: Run all tests to verify they pass

Run: `cd .claude/skills/audit-loop && python -m pytest tests/test_common.py -v`
Expected: 5 passed

### Step 1.11: Write test for path helpers

Add to `tests/test_common.py`:

```python
def test_get_state_path():
    """get_state_path returns adjacent .audit.json path."""
    from _common import get_state_path

    result = get_state_path(Path("docs/plans/feature.md"))
    assert result == Path("docs/plans/feature.audit.json")


def test_get_archive_path():
    """get_archive_path includes date in filename."""
    from _common import get_archive_path

    result = get_archive_path(Path("docs/plans/feature.md"), "2026-01-06")
    assert result == Path("docs/plans/feature.audit.2026-01-06.json")


def test_get_report_path():
    """get_report_path generates dated report path."""
    from _common import get_report_path

    result = get_report_path(Path("docs/plans/feature.md"), "2026-01-06")
    assert result == Path("docs/plans/feature.audit-report.2026-01-06.md")
```

### Step 1.12: Run tests to verify they fail

Run: `cd .claude/skills/audit-loop && python -m pytest tests/test_common.py::test_get_state_path -v`
Expected: FAIL with "cannot import name 'get_state_path'"

### Step 1.13: Add path helper implementations

Add to `scripts/_common.py`:

```python
# =============================================================================
# PATH HELPERS
# =============================================================================

def get_state_path(artifact_path: Path) -> Path:
    """Get the .audit.json path for an artifact."""
    artifact_path = Path(artifact_path)
    return artifact_path.parent / f"{artifact_path.stem}.audit.json"


def get_archive_path(artifact_path: Path, date_str: str) -> Path:
    """Get the archived state path with date suffix."""
    artifact_path = Path(artifact_path)
    return artifact_path.parent / f"{artifact_path.stem}.audit.{date_str}.json"


def get_report_path(artifact_path: Path, date_str: str) -> Path:
    """Get the report path with date suffix."""
    artifact_path = Path(artifact_path)
    return artifact_path.parent / f"{artifact_path.stem}.audit-report.{date_str}.md"
```

### Step 1.14: Run all tests

Run: `cd .claude/skills/audit-loop && python -m pytest tests/test_common.py -v`
Expected: 8 passed

### Step 1.15: Commit

```bash
git add .claude/skills/audit-loop/scripts/_common.py .claude/skills/audit-loop/tests/
git commit -m "feat(audit-loop): add _common.py foundation with Result, atomic_write, path helpers"
```

---

## Task 2: Create calculate_stakes.py

**Files:**
- Create: `.claude/skills/audit-loop/scripts/calculate_stakes.py`
- Create: `.claude/skills/audit-loop/tests/test_calculate_stakes.py`

### Step 2.1: Write failing tests

```python
# .claude/skills/audit-loop/tests/test_calculate_stakes.py
"""Tests for calculate_stakes module."""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


def test_calculate_calibration_light():
    """Score 4-6 = light calibration."""
    from calculate_stakes import calculate_calibration

    result = calculate_calibration(1, 1, 1, 1)  # sum = 4
    assert result["score"] == 4
    assert result["level"] == "light"


def test_calculate_calibration_medium():
    """Score 7-9 = medium calibration."""
    from calculate_stakes import calculate_calibration

    result = calculate_calibration(2, 2, 2, 2)  # sum = 8
    assert result["score"] == 8
    assert result["level"] == "medium"


def test_calculate_calibration_deep():
    """Score 10-12 = deep calibration."""
    from calculate_stakes import calculate_calibration

    result = calculate_calibration(3, 3, 3, 3)  # sum = 12
    assert result["score"] == 12
    assert result["level"] == "deep"


def test_calculate_calibration_boundary():
    """Boundary scores land in correct buckets."""
    from calculate_stakes import calculate_calibration

    assert calculate_calibration(1, 2, 1, 2)["level"] == "light"   # 6
    assert calculate_calibration(2, 2, 2, 1)["level"] == "medium"  # 7
    assert calculate_calibration(3, 2, 2, 2)["level"] == "medium"  # 9
    assert calculate_calibration(3, 3, 2, 2)["level"] == "deep"    # 10
```

### Step 2.2: Run tests to verify they fail

Run: `cd .claude/skills/audit-loop && python -m pytest tests/test_calculate_stakes.py::test_calculate_calibration_light -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'calculate_stakes'"

### Step 2.3: Write implementation

```python
# .claude/skills/audit-loop/scripts/calculate_stakes.py
#!/usr/bin/env python3
"""
Calculate calibration level from stakes assessment.

Usage:
    python calculate_stakes.py <rev> <blast> <prec> <vis>    # Direct values (1-3 each)
    python calculate_stakes.py --interactive                  # Guided prompts
    python calculate_stakes.py --json <rev> <blast> <prec> <vis>  # JSON output

Exit codes:
    0 - Success
    2 - Invalid arguments
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import TypedDict


class CalibrationResult(TypedDict):
    """Calibration calculation result."""

    stakes: dict[str, int]
    score: int
    level: str


def calculate_calibration(
    reversibility: int,
    blast_radius: int,
    precedent: int,
    visibility: int,
) -> CalibrationResult:
    """
    Calculate calibration level from stakes values.

    Args:
        reversibility: 1=easy to undo, 2=moderate, 3=permanent
        blast_radius: 1=just you, 2=team, 3=users/org
        precedent: 1=one-off, 2=may be referenced, 3=sets pattern
        visibility: 1=internal, 2=shared, 3=public

    Returns:
        CalibrationResult with stakes, score, and level
    """
    score = reversibility + blast_radius + precedent + visibility

    if score <= 6:
        level = "light"
    elif score <= 9:
        level = "medium"
    else:
        level = "deep"

    return {
        "stakes": {
            "reversibility": reversibility,
            "blast_radius": blast_radius,
            "precedent": precedent,
            "visibility": visibility,
        },
        "score": score,
        "level": level,
    }


def validate_value(value: int, name: str) -> None:
    """Validate stake value is 1-3."""
    if value < 1 or value > 3:
        raise ValueError(f"{name} must be 1-3, got {value}")


def interactive_mode() -> CalibrationResult:
    """Run interactive stakes assessment."""
    print("Stakes Assessment\n")

    prompts = [
        ("Reversibility", "If this design is wrong, how hard to fix?\n  [1] Easy to undo\n  [2] Moderate effort\n  [3] Permanent/very costly"),
        ("Blast radius", "Who's affected if it fails?\n  [1] Just you\n  [2] Your team\n  [3] Users or organization"),
        ("Precedent", "Will this be referenced later?\n  [1] One-off\n  [2] May be referenced\n  [3] Sets a pattern"),
        ("Visibility", "Who will see this?\n  [1] Internal only\n  [2] Shared with others\n  [3] Public"),
    ]

    values = []
    for name, prompt in prompts:
        print(f"\n{prompt}")
        while True:
            try:
                value = int(input(f"{name}: "))
                validate_value(value, name)
                values.append(value)
                break
            except ValueError as e:
                print(f"  Invalid: {e}")

    return calculate_calibration(*values)


def main(argv: list[str] | None = None) -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Calculate calibration level from stakes assessment."
    )
    parser.add_argument(
        "values",
        nargs="*",
        type=int,
        metavar="VALUE",
        help="Stakes values: reversibility blast_radius precedent visibility (1-3 each)",
    )
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Run interactive assessment",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )

    args = parser.parse_args(argv)

    try:
        if args.interactive:
            result = interactive_mode()
        elif len(args.values) == 4:
            for i, (val, name) in enumerate(zip(
                args.values,
                ["reversibility", "blast_radius", "precedent", "visibility"],
            )):
                validate_value(val, name)
            result = calculate_calibration(*args.values)
        else:
            parser.error("Provide 4 values or use --interactive")
            return 2

        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"Calibration: {result['level']} (score {result['score']})")

        return 0

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
```

### Step 2.4: Run tests

Run: `cd .claude/skills/audit-loop && python -m pytest tests/test_calculate_stakes.py -v`
Expected: 4 passed

### Step 2.5: Test CLI directly

Run: `cd .claude/skills/audit-loop && python scripts/calculate_stakes.py 2 2 2 2`
Expected: `Calibration: medium (score 8)`

Run: `cd .claude/skills/audit-loop && python scripts/calculate_stakes.py --json 2 2 2 2`
Expected: JSON output with score 8, level "medium"

### Step 2.6: Commit

```bash
git add .claude/skills/audit-loop/scripts/calculate_stakes.py .claude/skills/audit-loop/tests/test_calculate_stakes.py
git commit -m "feat(audit-loop): add calculate_stakes.py for calibration scoring"
```

---

## Task 3: Create state.py Core Structure

**Files:**
- Create: `.claude/skills/audit-loop/scripts/state.py`
- Create: `.claude/skills/audit-loop/tests/test_state.py`

### Step 3.1: Write failing test for create command

```python
# .claude/skills/audit-loop/tests/test_state.py
"""Tests for state module."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


def test_create_initializes_state(tmp_path):
    """create command initializes .audit.json with correct schema."""
    from state import create_state

    artifact = tmp_path / "feature.md"
    artifact.write_text("# Feature\n\nDescription here.")

    result = create_state(artifact)

    assert result.ok
    state_path = tmp_path / "feature.audit.json"
    assert state_path.exists()

    state = json.loads(state_path.read_text())
    assert state["version"] == "1.0"
    assert state["artifact"] == str(artifact)
    assert state["phase"] == "stakes_assessment"
    assert state["cycle"] == 1
    assert state["findings"] == []


def test_create_fails_if_artifact_missing(tmp_path):
    """create fails when artifact doesn't exist."""
    from state import create_state

    artifact = tmp_path / "missing.md"
    result = create_state(artifact)

    assert not result.ok
    assert "not found" in result.message.lower()


def test_create_fails_if_state_exists(tmp_path):
    """create fails when .audit.json already exists."""
    from state import create_state

    artifact = tmp_path / "feature.md"
    artifact.write_text("# Feature")
    state_path = tmp_path / "feature.audit.json"
    state_path.write_text('{"existing": true}')

    result = create_state(artifact)

    assert not result.ok
    assert "exists" in result.message.lower()
```

### Step 3.2: Run test to verify it fails

Run: `cd .claude/skills/audit-loop && python -m pytest tests/test_state.py::test_create_initializes_state -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'state'"

### Step 3.3: Write state.py with create command

```python
# .claude/skills/audit-loop/scripts/state.py
#!/usr/bin/env python3
"""
State management for audit-loop.

Subcommands:
    create <artifact>     Initialize new .audit.json
    read <artifact>       Display current state
    update <artifact>     Modify state fields
    validate <artifact>   Check state integrity
    list [directory]      Find active audits
    archive <artifact>    Archive completed audit

Exit codes:
    0  - Success
    1  - Error
    2  - Invalid arguments
    10 - Validation failed
    11 - Not found
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from _common import (
    EXIT_ARGS,
    EXIT_ERROR,
    EXIT_NOT_FOUND,
    EXIT_SUCCESS,
    EXIT_VALIDATION,
    MAX_CYCLES,
    PHASES,
    SCHEMA_VERSION,
    Result,
    atomic_write,
    get_archive_path,
    get_state_path,
)


# =============================================================================
# STATE OPERATIONS
# =============================================================================

def create_state(artifact_path: Path, force: bool = False) -> Result:
    """
    Initialize new audit state for an artifact.

    Args:
        artifact_path: Path to the artifact being audited
        force: If True, overwrite existing state

    Returns:
        Result with state path in data
    """
    artifact_path = Path(artifact_path).resolve()
    state_path = get_state_path(artifact_path)

    if not artifact_path.exists():
        return Result.failure(
            f"Artifact not found: {artifact_path}",
            errors=[f"File does not exist: {artifact_path}"],
        )

    if state_path.exists() and not force:
        return Result.failure(
            f"State already exists: {state_path}",
            errors=["Use --force to overwrite existing state"],
        )

    now = datetime.now(timezone.utc).isoformat()
    state = {
        "version": SCHEMA_VERSION,
        "artifact": str(artifact_path),
        "created": now,
        "updated": now,
        "calibration": None,
        "cycle": 1,
        "phase": "stakes_assessment",
        "definition": {
            "goal": None,
            "scope": [],
            "excluded": [],
            "excluded_rationale": None,
            "assumptions": [],
            "done_criteria": None,
        },
        "findings": [],
        "verification": {
            "counter_conclusion": None,
            "limitations": [],
        },
        "history": [
            {"timestamp": now, "event": "created", "data": {}}
        ],
    }

    try:
        atomic_write(state_path, json.dumps(state, indent=2))
        return Result.success(
            f"Created audit state: {state_path}",
            data={"state_path": str(state_path), "state": state},
        )
    except OSError as e:
        return Result.failure(
            f"Failed to write state: {e}",
            errors=[str(e)],
        )


def read_state(artifact_path: Path) -> Result:
    """
    Read and return current audit state.

    Args:
        artifact_path: Path to the artifact being audited

    Returns:
        Result with state in data
    """
    state_path = get_state_path(Path(artifact_path))

    if not state_path.exists():
        return Result.failure(
            f"No audit state found: {state_path}",
            errors=["Run 'state.py create <artifact>' first"],
        )

    try:
        state = json.loads(state_path.read_text())
        return Result.success(
            f"Read state from: {state_path}",
            data={"state_path": str(state_path), "state": state},
        )
    except json.JSONDecodeError as e:
        return Result.failure(
            f"Invalid JSON in state file: {e}",
            errors=[str(e)],
        )
    except OSError as e:
        return Result.failure(
            f"Failed to read state: {e}",
            errors=[str(e)],
        )


# =============================================================================
# CLI
# =============================================================================

def cmd_create(args: argparse.Namespace) -> int:
    """Handle create subcommand."""
    result = create_state(Path(args.artifact), force=args.force)
    if args.json:
        print(result.to_json())
    else:
        print(result.message)
    return EXIT_SUCCESS if result.ok else EXIT_ERROR


def cmd_read(args: argparse.Namespace) -> int:
    """Handle read subcommand."""
    result = read_state(Path(args.artifact))
    if not result.ok:
        if args.json:
            print(result.to_json())
        else:
            print(result.message, file=sys.stderr)
        return EXIT_NOT_FOUND

    if args.json:
        print(json.dumps(result.data["state"], indent=2))
    else:
        state = result.data["state"]
        print(f"Artifact: {state['artifact']}")
        print(f"Phase: {state['phase']}")
        print(f"Cycle: {state['cycle']}")
        if state.get("calibration"):
            print(f"Calibration: {state['calibration']['level']} (score {state['calibration']['score']})")
        print(f"Findings: {len(state['findings'])}")

    return EXIT_SUCCESS


def main(argv: list[str] | None = None) -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Manage audit-loop state files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # create
    p_create = subparsers.add_parser("create", help="Initialize new audit state")
    p_create.add_argument("artifact", help="Path to artifact being audited")
    p_create.add_argument("--force", "-f", action="store_true", help="Overwrite existing state")
    p_create.set_defaults(func=cmd_create)

    # read
    p_read = subparsers.add_parser("read", help="Display current state")
    p_read.add_argument("artifact", help="Path to artifact being audited")
    p_read.set_defaults(func=cmd_read)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
```

### Step 3.4: Run tests

Run: `cd .claude/skills/audit-loop && python -m pytest tests/test_state.py -v`
Expected: 3 passed

### Step 3.5: Test CLI

Run: `cd .claude/skills/audit-loop && echo "# Test" > /tmp/test-artifact.md && python scripts/state.py create /tmp/test-artifact.md`
Expected: `Created audit state: /tmp/test-artifact.audit.json`

Run: `cd .claude/skills/audit-loop && python scripts/state.py read /tmp/test-artifact.md`
Expected: Display phase, cycle, findings count

### Step 3.6: Commit

```bash
git add .claude/skills/audit-loop/scripts/state.py .claude/skills/audit-loop/tests/test_state.py
git commit -m "feat(audit-loop): add state.py with create and read commands"
```

---

## Task 4: Add state.py Update and Validate Commands

**Files:**
- Modify: `.claude/skills/audit-loop/scripts/state.py`
- Modify: `.claude/skills/audit-loop/tests/test_state.py`

### Step 4.1: Write failing tests for update

Add to `tests/test_state.py`:

```python
def test_update_phase(tmp_path):
    """update --phase transitions to new phase."""
    from state import create_state, update_state

    artifact = tmp_path / "feature.md"
    artifact.write_text("# Feature")
    create_state(artifact)

    result = update_state(artifact, phase="definition")

    assert result.ok
    state = result.data["state"]
    assert state["phase"] == "definition"


def test_update_phase_invalid(tmp_path):
    """update --phase rejects invalid phase."""
    from state import create_state, update_state

    artifact = tmp_path / "feature.md"
    artifact.write_text("# Feature")
    create_state(artifact)

    result = update_state(artifact, phase="invalid_phase")

    assert not result.ok
    assert "invalid phase" in result.message.lower()


def test_update_add_finding(tmp_path):
    """update --add-finding adds new finding with auto-ID."""
    from state import create_state, update_state

    artifact = tmp_path / "feature.md"
    artifact.write_text("# Feature")
    create_state(artifact)

    result = update_state(
        artifact,
        add_finding={
            "description": "Missing error handling",
            "confidence": "probable",
            "priority": "high",
            "evidence": "lines 45-50",
        },
    )

    assert result.ok
    state = result.data["state"]
    assert len(state["findings"]) == 1
    assert state["findings"][0]["id"] == "F1"
    assert state["findings"][0]["status"] == "open"


def test_update_next_cycle(tmp_path):
    """update --next-cycle increments cycle."""
    from state import create_state, update_state

    artifact = tmp_path / "feature.md"
    artifact.write_text("# Feature")
    create_state(artifact)

    result = update_state(artifact, next_cycle=True)

    assert result.ok
    assert result.data["state"]["cycle"] == 2


def test_update_cycle_limit(tmp_path):
    """update --next-cycle enforces MAX_CYCLES limit."""
    from state import create_state, update_state
    import json
    from _common import MAX_CYCLES, get_state_path

    artifact = tmp_path / "feature.md"
    artifact.write_text("# Feature")
    create_state(artifact)

    # Manually set cycle to MAX_CYCLES
    state_path = get_state_path(artifact)
    state = json.loads(state_path.read_text())
    state["cycle"] = MAX_CYCLES
    state_path.write_text(json.dumps(state))

    result = update_state(artifact, next_cycle=True)

    assert not result.ok
    assert "limit" in result.message.lower()
```

### Step 4.2: Run tests to verify they fail

Run: `cd .claude/skills/audit-loop && python -m pytest tests/test_state.py::test_update_phase -v`
Expected: FAIL with "cannot import name 'update_state'"

### Step 4.3: Add update_state implementation

Add to `scripts/state.py` after `read_state`:

```python
def update_state(
    artifact_path: Path,
    phase: str | None = None,
    add_finding: dict[str, Any] | None = None,
    next_cycle: bool = False,
    calibration: dict[str, Any] | None = None,
) -> Result:
    """
    Update audit state.

    Args:
        artifact_path: Path to the artifact being audited
        phase: New phase value
        add_finding: Finding dict to add (auto-generates ID)
        next_cycle: Increment cycle counter
        calibration: Calibration data to set

    Returns:
        Result with updated state
    """
    read_result = read_state(artifact_path)
    if not read_result.ok:
        return read_result

    state = read_result.data["state"]
    state_path = Path(read_result.data["state_path"])
    now = datetime.now(timezone.utc).isoformat()
    events = []

    # Update phase
    if phase is not None:
        if phase not in PHASES:
            return Result.failure(
                f"Invalid phase: {phase}",
                errors=[f"Valid phases: {', '.join(PHASES)}"],
            )
        old_phase = state["phase"]
        state["phase"] = phase
        events.append({
            "timestamp": now,
            "event": "phase_changed",
            "data": {"from": old_phase, "to": phase},
        })

    # Add finding
    if add_finding is not None:
        # Generate next finding ID
        existing_ids = [f["id"] for f in state["findings"]]
        next_num = 1
        while f"F{next_num}" in existing_ids:
            next_num += 1
        finding_id = f"F{next_num}"

        finding = {
            "id": finding_id,
            "description": add_finding.get("description", ""),
            "confidence": add_finding.get("confidence", "unknown"),
            "priority": add_finding.get("priority", "medium"),
            "evidence": add_finding.get("evidence", ""),
            "status": "open",
            "resolution": None,
        }
        state["findings"].append(finding)
        events.append({
            "timestamp": now,
            "event": "finding_added",
            "data": {"id": finding_id},
        })

    # Next cycle
    if next_cycle:
        if state["cycle"] >= MAX_CYCLES:
            return Result.failure(
                f"Cycle limit reached ({MAX_CYCLES})",
                errors=["Cannot exceed maximum cycles. Consider archiving this audit."],
            )
        state["cycle"] += 1
        events.append({
            "timestamp": now,
            "event": "cycle_started",
            "data": {"cycle": state["cycle"]},
        })

    # Set calibration
    if calibration is not None:
        state["calibration"] = calibration
        events.append({
            "timestamp": now,
            "event": "calibration_set",
            "data": calibration,
        })

    # Update timestamp and history
    state["updated"] = now
    state["history"].extend(events)

    try:
        atomic_write(state_path, json.dumps(state, indent=2))
        return Result.success(
            f"Updated state: {state_path}",
            data={"state_path": str(state_path), "state": state},
        )
    except OSError as e:
        return Result.failure(
            f"Failed to write state: {e}",
            errors=[str(e)],
        )
```

### Step 4.4: Add update CLI subcommand

Add to `main()` in `scripts/state.py`:

```python
def cmd_update(args: argparse.Namespace) -> int:
    """Handle update subcommand."""
    add_finding = None
    if args.add_finding:
        # Parse finding from comma-separated key=value pairs
        finding = {}
        for pair in args.add_finding.split(","):
            if "=" in pair:
                key, value = pair.split("=", 1)
                finding[key.strip()] = value.strip()
        add_finding = finding

    result = update_state(
        Path(args.artifact),
        phase=args.phase,
        add_finding=add_finding,
        next_cycle=args.next_cycle,
    )

    if args.json:
        print(result.to_json())
    else:
        print(result.message)

    return EXIT_SUCCESS if result.ok else EXIT_ERROR
```

Add subparser in `main()`:

```python
    # update
    p_update = subparsers.add_parser("update", help="Modify state fields")
    p_update.add_argument("artifact", help="Path to artifact being audited")
    p_update.add_argument("--phase", help="Set phase")
    p_update.add_argument("--add-finding", help="Add finding: description=...,priority=...,confidence=...")
    p_update.add_argument("--next-cycle", action="store_true", help="Increment cycle")
    p_update.set_defaults(func=cmd_update)
```

### Step 4.5: Run tests

Run: `cd .claude/skills/audit-loop && python -m pytest tests/test_state.py -v`
Expected: 8 passed

### Step 4.6: Write validate tests

Add to `tests/test_state.py`:

```python
def test_validate_valid_state(tmp_path):
    """validate returns success for valid state."""
    from state import create_state, validate_state

    artifact = tmp_path / "feature.md"
    artifact.write_text("# Feature")
    create_state(artifact)

    result = validate_state(artifact)

    assert result.ok


def test_validate_missing_state(tmp_path):
    """validate fails when state doesn't exist."""
    from state import validate_state

    artifact = tmp_path / "feature.md"
    artifact.write_text("# Feature")

    result = validate_state(artifact)

    assert not result.ok


def test_validate_corrupt_state(tmp_path):
    """validate fails for invalid JSON."""
    from state import validate_state
    from _common import get_state_path

    artifact = tmp_path / "feature.md"
    artifact.write_text("# Feature")
    state_path = get_state_path(artifact)
    state_path.write_text("not valid json")

    result = validate_state(artifact)

    assert not result.ok
    assert "json" in result.message.lower() or "invalid" in result.message.lower()
```

### Step 4.7: Run tests to verify they fail

Run: `cd .claude/skills/audit-loop && python -m pytest tests/test_state.py::test_validate_valid_state -v`
Expected: FAIL with "cannot import name 'validate_state'"

### Step 4.8: Add validate_state implementation

Add to `scripts/state.py`:

```python
def validate_state(artifact_path: Path) -> Result:
    """
    Validate audit state integrity.

    Checks:
        - State file exists and is valid JSON
        - Required fields present
        - Phase is valid
        - Cycle is within limits
        - Finding IDs are unique

    Returns:
        Result with validation details
    """
    read_result = read_state(artifact_path)
    if not read_result.ok:
        return read_result

    state = read_result.data["state"]
    errors = []
    warnings = []

    # Check required fields
    required = ["version", "artifact", "phase", "cycle", "findings"]
    for field in required:
        if field not in state:
            errors.append(f"Missing required field: {field}")

    if errors:
        return Result.failure(
            "State validation failed",
            errors=errors,
        )

    # Check phase validity
    if state["phase"] not in PHASES:
        errors.append(f"Invalid phase: {state['phase']}")

    # Check cycle limits
    if state["cycle"] > MAX_CYCLES:
        errors.append(f"Cycle {state['cycle']} exceeds limit {MAX_CYCLES}")

    # Check finding ID uniqueness
    finding_ids = [f["id"] for f in state["findings"]]
    if len(finding_ids) != len(set(finding_ids)):
        errors.append("Duplicate finding IDs detected")

    if errors:
        return Result.failure(
            "State validation failed",
            errors=errors,
            data={"state": state},
        )

    return Result.success(
        "State is valid",
        data={"state": state},
        warnings=warnings,
    )
```

Add CLI subcommand:

```python
def cmd_validate(args: argparse.Namespace) -> int:
    """Handle validate subcommand."""
    result = validate_state(Path(args.artifact))
    if args.json:
        print(result.to_json())
    else:
        print(result.message)
        for error in result.errors:
            print(f"  - {error}")

    return EXIT_SUCCESS if result.ok else EXIT_VALIDATION


# In main():
    # validate
    p_validate = subparsers.add_parser("validate", help="Check state integrity")
    p_validate.add_argument("artifact", help="Path to artifact being audited")
    p_validate.set_defaults(func=cmd_validate)
```

### Step 4.9: Run all tests

Run: `cd .claude/skills/audit-loop && python -m pytest tests/test_state.py -v`
Expected: 11 passed

### Step 4.10: Commit

```bash
git add .claude/skills/audit-loop/scripts/state.py .claude/skills/audit-loop/tests/test_state.py
git commit -m "feat(audit-loop): add update and validate commands to state.py"
```

---

## Task 5: Add state.py List and Archive Commands

**Files:**
- Modify: `.claude/skills/audit-loop/scripts/state.py`
- Modify: `.claude/skills/audit-loop/tests/test_state.py`

### Step 5.1: Write failing tests for list

Add to `tests/test_state.py`:

```python
def test_list_finds_active_audits(tmp_path):
    """list finds all .audit.json files in directory."""
    from state import create_state, list_audits

    # Create two audits
    a1 = tmp_path / "feature1.md"
    a1.write_text("# Feature 1")
    create_state(a1)

    a2 = tmp_path / "feature2.md"
    a2.write_text("# Feature 2")
    create_state(a2)

    result = list_audits(tmp_path)

    assert result.ok
    assert len(result.data["audits"]) == 2


def test_list_empty_directory(tmp_path):
    """list returns empty list when no audits exist."""
    from state import list_audits

    result = list_audits(tmp_path)

    assert result.ok
    assert result.data["audits"] == []
```

### Step 5.2: Add list_audits implementation

Add to `scripts/state.py`:

```python
def list_audits(directory: Path) -> Result:
    """
    Find all active audits in a directory.

    Args:
        directory: Directory to search (non-recursive)

    Returns:
        Result with list of audit info
    """
    directory = Path(directory)
    if not directory.is_dir():
        return Result.failure(
            f"Not a directory: {directory}",
            errors=[str(directory)],
        )

    audits = []
    for state_path in directory.glob("*.audit.json"):
        # Skip archived audits (have date suffix before .json)
        name = state_path.stem  # e.g., "feature.audit"
        if name.count(".") > 1:
            continue  # Looks like "feature.audit.2026-01-06"

        try:
            state = json.loads(state_path.read_text())
            audits.append({
                "state_path": str(state_path),
                "artifact": state.get("artifact", "unknown"),
                "phase": state.get("phase", "unknown"),
                "cycle": state.get("cycle", 0),
                "findings": len(state.get("findings", [])),
            })
        except (json.JSONDecodeError, OSError):
            audits.append({
                "state_path": str(state_path),
                "error": "Failed to read state",
            })

    return Result.success(
        f"Found {len(audits)} active audit(s)",
        data={"audits": audits},
    )


def cmd_list(args: argparse.Namespace) -> int:
    """Handle list subcommand."""
    directory = Path(args.directory) if args.directory else Path.cwd()
    result = list_audits(directory)

    if args.json:
        print(result.to_json())
    else:
        print(result.message)
        for audit in result.data["audits"]:
            if "error" in audit:
                print(f"  - {audit['state_path']}: {audit['error']}")
            else:
                print(f"  - {Path(audit['artifact']).name}: {audit['phase']} (cycle {audit['cycle']}, {audit['findings']} findings)")

    return EXIT_SUCCESS if result.ok else EXIT_ERROR


# In main():
    # list
    p_list = subparsers.add_parser("list", help="Find active audits")
    p_list.add_argument("directory", nargs="?", help="Directory to search (default: cwd)")
    p_list.set_defaults(func=cmd_list)
```

### Step 5.3: Write failing tests for archive

Add to `tests/test_state.py`:

```python
def test_archive_moves_state(tmp_path):
    """archive renames state file with date suffix."""
    from state import create_state, archive_audit
    from _common import get_state_path

    artifact = tmp_path / "feature.md"
    artifact.write_text("# Feature")
    create_state(artifact)

    result = archive_audit(artifact, "2026-01-06")

    assert result.ok
    # Original state gone
    assert not get_state_path(artifact).exists()
    # Archived state exists
    archived = tmp_path / "feature.audit.2026-01-06.json"
    assert archived.exists()


def test_archive_fails_if_no_state(tmp_path):
    """archive fails when no state exists."""
    from state import archive_audit

    artifact = tmp_path / "feature.md"
    artifact.write_text("# Feature")

    result = archive_audit(artifact, "2026-01-06")

    assert not result.ok
```

### Step 5.4: Add archive_audit implementation

Add to `scripts/state.py`:

```python
def archive_audit(artifact_path: Path, date_str: str | None = None) -> Result:
    """
    Archive completed audit by renaming state file with date suffix.

    Args:
        artifact_path: Path to the artifact
        date_str: Date string for archive (default: today)

    Returns:
        Result with archive path
    """
    state_path = get_state_path(artifact_path)

    if not state_path.exists():
        return Result.failure(
            f"No audit state found: {state_path}",
            errors=["Nothing to archive"],
        )

    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")

    archive_path = get_archive_path(artifact_path, date_str)

    try:
        # Read state, add shipped event
        state = json.loads(state_path.read_text())
        now = datetime.now(timezone.utc).isoformat()
        state["history"].append({
            "timestamp": now,
            "event": "archived",
            "data": {"archive_path": str(archive_path)},
        })

        # Write to archive location
        atomic_write(archive_path, json.dumps(state, indent=2))

        # Remove original
        state_path.unlink()

        return Result.success(
            f"Archived to: {archive_path}",
            data={"archive_path": str(archive_path)},
        )
    except OSError as e:
        return Result.failure(
            f"Archive failed: {e}",
            errors=[str(e)],
        )


def cmd_archive(args: argparse.Namespace) -> int:
    """Handle archive subcommand."""
    result = archive_audit(Path(args.artifact), args.date)

    if args.json:
        print(result.to_json())
    else:
        print(result.message)

    return EXIT_SUCCESS if result.ok else EXIT_ERROR


# In main():
    # archive
    p_archive = subparsers.add_parser("archive", help="Archive completed audit")
    p_archive.add_argument("artifact", help="Path to artifact being audited")
    p_archive.add_argument("--date", help="Date suffix (default: today)")
    p_archive.set_defaults(func=cmd_archive)
```

### Step 5.5: Run all tests

Run: `cd .claude/skills/audit-loop && python -m pytest tests/test_state.py -v`
Expected: 15 passed

### Step 5.6: Commit

```bash
git add .claude/skills/audit-loop/scripts/state.py .claude/skills/audit-loop/tests/test_state.py
git commit -m "feat(audit-loop): add list and archive commands to state.py"
```

---

## Task 6: Create generate_report.py

**Files:**
- Create: `.claude/skills/audit-loop/scripts/generate_report.py`
- Create: `.claude/skills/audit-loop/tests/test_generate_report.py`

### Step 6.1: Write failing tests

```python
# .claude/skills/audit-loop/tests/test_generate_report.py
"""Tests for generate_report module."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


def test_generate_report_basic(tmp_path):
    """generate_report produces markdown from state."""
    from generate_report import generate_report
    from state import create_state, update_state

    artifact = tmp_path / "feature.md"
    artifact.write_text("# Feature\n\nDescription here.")
    create_state(artifact)
    update_state(artifact, calibration={"stakes": {}, "score": 8, "level": "medium"})

    result = generate_report(artifact)

    assert result.ok
    report = result.data["report"]
    assert "# Audit Report" in report
    assert "feature.md" in report
    assert "medium" in report.lower()


def test_generate_report_includes_findings(tmp_path):
    """generate_report includes findings table."""
    from generate_report import generate_report
    from state import create_state, update_state

    artifact = tmp_path / "feature.md"
    artifact.write_text("# Feature")
    create_state(artifact)
    update_state(artifact, add_finding={
        "description": "Missing validation",
        "priority": "high",
        "confidence": "certain",
        "evidence": "line 42",
    })

    result = generate_report(artifact)

    assert result.ok
    report = result.data["report"]
    assert "F1" in report
    assert "Missing validation" in report
    assert "high" in report.lower()


def test_generate_report_missing_state(tmp_path):
    """generate_report fails when state doesn't exist."""
    from generate_report import generate_report

    artifact = tmp_path / "feature.md"
    artifact.write_text("# Feature")

    result = generate_report(artifact)

    assert not result.ok
```

### Step 6.2: Run tests to verify they fail

Run: `cd .claude/skills/audit-loop && python -m pytest tests/test_generate_report.py::test_generate_report_basic -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'generate_report'"

### Step 6.3: Write implementation

```python
# .claude/skills/audit-loop/scripts/generate_report.py
#!/usr/bin/env python3
"""
Generate markdown audit report from state.

Usage:
    python generate_report.py <artifact>           # Output to stdout
    python generate_report.py <artifact> --save    # Save to dated file

Exit codes:
    0  - Success
    1  - Error
    11 - State not found
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

from _common import (
    EXIT_ERROR,
    EXIT_NOT_FOUND,
    EXIT_SUCCESS,
    Result,
    atomic_write,
    get_report_path,
    get_state_path,
)
from state import read_state


def generate_report(artifact_path: Path) -> Result:
    """
    Generate markdown report from audit state.

    Args:
        artifact_path: Path to the artifact being audited

    Returns:
        Result with report markdown in data
    """
    read_result = read_state(artifact_path)
    if not read_result.ok:
        return read_result

    state = read_result.data["state"]
    lines = []

    # Header
    lines.append("# Audit Report")
    lines.append("")
    lines.append(f"**Artifact:** {Path(state['artifact']).name}")
    lines.append(f"**Date:** {datetime.now().strftime('%Y-%m-%d')}")

    if state.get("calibration"):
        cal = state["calibration"]
        lines.append(f"**Calibration:** {cal['level']} (score {cal['score']})")

    lines.append(f"**Cycles:** {state['cycle']}")
    lines.append("")

    # Summary
    lines.append("## Summary")
    lines.append("")
    findings = state.get("findings", [])
    high = sum(1 for f in findings if f.get("priority") == "high")
    medium = sum(1 for f in findings if f.get("priority") == "medium")
    low = sum(1 for f in findings if f.get("priority") == "low")
    lines.append(f"Found **{len(findings)}** findings: {high} high, {medium} medium, {low} low priority.")
    lines.append("")

    # Scope
    definition = state.get("definition", {})
    if definition.get("scope"):
        lines.append("## Scope")
        lines.append("")
        lines.append("**Examined:**")
        for item in definition["scope"]:
            lines.append(f"- {item}")
        lines.append("")

    if definition.get("excluded"):
        lines.append("**Excluded:**")
        for item in definition["excluded"]:
            lines.append(f"- {item}")
        if definition.get("excluded_rationale"):
            lines.append(f"\n*Rationale:* {definition['excluded_rationale']}")
        lines.append("")

    # Findings
    if findings:
        lines.append("## Findings")
        lines.append("")
        lines.append("| ID | Description | Priority | Confidence | Status |")
        lines.append("|----|-------------|----------|------------|--------|")
        for f in findings:
            status = f.get("status", "open")
            status_icon = "✅" if status == "addressed" else "🔄" if status == "partial" else "⚪"
            lines.append(
                f"| {f['id']} | {f['description'][:50]} | {f.get('priority', '-')} | {f.get('confidence', '-')} | {status_icon} {status} |"
            )
        lines.append("")

        # Finding details
        lines.append("### Finding Details")
        lines.append("")
        for f in findings:
            lines.append(f"#### {f['id']}: {f['description']}")
            lines.append("")
            if f.get("evidence"):
                lines.append(f"**Evidence:** {f['evidence']}")
            if f.get("resolution"):
                lines.append(f"**Resolution:** {f['resolution']}")
            lines.append("")

    # Verification
    verification = state.get("verification", {})
    if verification.get("limitations"):
        lines.append("## Limitations")
        lines.append("")
        for item in verification["limitations"]:
            lines.append(f"- {item}")
        lines.append("")

    if verification.get("counter_conclusion"):
        lines.append("## Counter-Conclusion")
        lines.append("")
        lines.append(verification["counter_conclusion"])
        lines.append("")

    # Audit Trail
    lines.append("## Audit Trail")
    lines.append("")
    for event in state.get("history", [])[-10:]:  # Last 10 events
        lines.append(f"- **{event['timestamp'][:10]}** {event['event']}")
    lines.append("")

    report = "\n".join(lines)
    return Result.success(
        "Report generated",
        data={"report": report},
    )


def main(argv: list[str] | None = None) -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate markdown audit report from state."
    )
    parser.add_argument("artifact", help="Path to artifact being audited")
    parser.add_argument("--save", action="store_true", help="Save to dated file")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args(argv)
    artifact = Path(args.artifact)

    result = generate_report(artifact)

    if not result.ok:
        if args.json:
            print(result.to_json())
        else:
            print(result.message, file=sys.stderr)
        return EXIT_NOT_FOUND

    if args.save:
        date_str = datetime.now().strftime("%Y-%m-%d")
        report_path = get_report_path(artifact, date_str)
        try:
            atomic_write(report_path, result.data["report"])
            print(f"Saved: {report_path}")
        except OSError as e:
            print(f"Failed to save: {e}", file=sys.stderr)
            return EXIT_ERROR
    elif args.json:
        print(result.to_json())
    else:
        print(result.data["report"])

    return EXIT_SUCCESS


if __name__ == "__main__":
    sys.exit(main())
```

### Step 6.4: Run tests

Run: `cd .claude/skills/audit-loop && python -m pytest tests/test_generate_report.py -v`
Expected: 3 passed

### Step 6.5: Test CLI

Run: `cd .claude/skills/audit-loop && python scripts/generate_report.py /tmp/test-artifact.md`
Expected: Markdown report output

### Step 6.6: Commit

```bash
git add .claude/skills/audit-loop/scripts/generate_report.py .claude/skills/audit-loop/tests/test_generate_report.py
git commit -m "feat(audit-loop): add generate_report.py for markdown reports"
```

---

## Task 7: Create validate_state.py

**Files:**
- Create: `.claude/skills/audit-loop/scripts/validate_state.py`
- Create: `.claude/skills/audit-loop/tests/test_validate_state.py`

### Step 7.1: Write failing tests

```python
# .claude/skills/audit-loop/tests/test_validate_state.py
"""Tests for validate_state module."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


def test_validate_for_ship_passes_no_high(tmp_path):
    """--for ship passes when no high priority findings remain."""
    from validate_state import validate_for_ship
    from state import create_state, update_state

    artifact = tmp_path / "feature.md"
    artifact.write_text("# Feature")
    create_state(artifact)
    update_state(artifact, add_finding={
        "description": "Minor issue",
        "priority": "low",
    })

    result = validate_for_ship(artifact)

    assert result.ok


def test_validate_for_ship_fails_open_high(tmp_path):
    """--for ship fails when open high priority findings exist."""
    from validate_state import validate_for_ship
    from state import create_state, update_state

    artifact = tmp_path / "feature.md"
    artifact.write_text("# Feature")
    create_state(artifact)
    update_state(artifact, add_finding={
        "description": "Critical issue",
        "priority": "high",
    })

    result = validate_for_ship(artifact)

    assert not result.ok
    assert "high" in result.message.lower()


def test_validate_for_iterate_passes_within_limit(tmp_path):
    """--for iterate passes when under cycle limit."""
    from validate_state import validate_for_iterate
    from state import create_state

    artifact = tmp_path / "feature.md"
    artifact.write_text("# Feature")
    create_state(artifact)

    result = validate_for_iterate(artifact)

    assert result.ok


def test_validate_for_iterate_fails_at_limit(tmp_path):
    """--for iterate fails at MAX_CYCLES."""
    from validate_state import validate_for_iterate
    from state import create_state
    from _common import MAX_CYCLES, get_state_path

    artifact = tmp_path / "feature.md"
    artifact.write_text("# Feature")
    create_state(artifact)

    # Set cycle to MAX_CYCLES
    state_path = get_state_path(artifact)
    state = json.loads(state_path.read_text())
    state["cycle"] = MAX_CYCLES
    state_path.write_text(json.dumps(state))

    result = validate_for_iterate(artifact)

    assert not result.ok
    assert "limit" in result.message.lower()
```

### Step 7.2: Write implementation

```python
# .claude/skills/audit-loop/scripts/validate_state.py
#!/usr/bin/env python3
"""
Pre-operation validation for audit-loop.

Usage:
    python validate_state.py <artifact>                      # Basic validation
    python validate_state.py <artifact> --for ship           # Exit criteria check
    python validate_state.py <artifact> --for iterate        # Cycle limit check
    python validate_state.py <artifact> --for phase --target definition

Exit codes:
    0  - Validation passed
    10 - Validation failed
    11 - State not found
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _common import (
    EXIT_NOT_FOUND,
    EXIT_SUCCESS,
    EXIT_VALIDATION,
    MAX_CYCLES,
    PHASES,
    Result,
)
from state import read_state, validate_state


def validate_for_ship(artifact_path: Path) -> Result:
    """
    Validate state meets ship criteria.

    Criteria:
        - No open high-priority findings
        - For deep calibration: no open medium-priority findings

    Returns:
        Result indicating if ship is allowed
    """
    read_result = read_state(artifact_path)
    if not read_result.ok:
        return read_result

    state = read_result.data["state"]
    findings = state.get("findings", [])
    calibration = state.get("calibration", {})
    level = calibration.get("level", "medium")

    open_high = [f for f in findings if f.get("status") == "open" and f.get("priority") == "high"]
    open_medium = [f for f in findings if f.get("status") == "open" and f.get("priority") == "medium"]

    errors = []

    if open_high:
        errors.append(f"{len(open_high)} open high-priority finding(s): {', '.join(f['id'] for f in open_high)}")

    if level == "deep" and open_medium:
        errors.append(f"{len(open_medium)} open medium-priority finding(s) (required for deep calibration)")

    if errors:
        return Result.failure(
            "Ship criteria not met",
            errors=errors,
            data={"open_high": len(open_high), "open_medium": len(open_medium)},
        )

    return Result.success(
        "Ship criteria met",
        data={"findings_addressed": len([f for f in findings if f.get("status") == "addressed"])},
    )


def validate_for_iterate(artifact_path: Path) -> Result:
    """
    Validate state allows another iteration.

    Criteria:
        - Current cycle < MAX_CYCLES

    Returns:
        Result indicating if iteration is allowed
    """
    read_result = read_state(artifact_path)
    if not read_result.ok:
        return read_result

    state = read_result.data["state"]
    cycle = state.get("cycle", 1)

    if cycle >= MAX_CYCLES:
        return Result.failure(
            f"Cycle limit reached ({MAX_CYCLES})",
            errors=["Consider archiving this audit and starting fresh if more iterations needed"],
        )

    return Result.success(
        f"Iteration allowed (cycle {cycle} of {MAX_CYCLES})",
        data={"current_cycle": cycle, "max_cycles": MAX_CYCLES},
    )


def validate_for_phase(artifact_path: Path, target_phase: str) -> Result:
    """
    Validate state allows transition to target phase.

    Returns:
        Result indicating if phase transition is allowed
    """
    if target_phase not in PHASES:
        return Result.failure(
            f"Invalid target phase: {target_phase}",
            errors=[f"Valid phases: {', '.join(PHASES)}"],
        )

    read_result = read_state(artifact_path)
    if not read_result.ok:
        return read_result

    state = read_result.data["state"]
    current = state.get("phase", "stakes_assessment")

    current_idx = PHASES.index(current) if current in PHASES else 0
    target_idx = PHASES.index(target_phase)

    # Allow forward transitions or same phase
    if target_idx >= current_idx:
        return Result.success(
            f"Phase transition allowed: {current} → {target_phase}",
        )

    # Backward transitions only allowed for iterate/expand
    if target_phase in ("execution", "definition"):
        return Result.success(
            f"Phase transition allowed (iteration): {current} → {target_phase}",
        )

    return Result.failure(
        f"Invalid phase transition: {current} → {target_phase}",
        errors=["Backward transitions only allowed for iteration"],
    )


def main(argv: list[str] | None = None) -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate audit state for operations."
    )
    parser.add_argument("artifact", help="Path to artifact being audited")
    parser.add_argument("--for", dest="operation", choices=["ship", "iterate", "phase"], help="Validation mode")
    parser.add_argument("--target-phase", help="Target phase (with --for phase)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args(argv)
    artifact = Path(args.artifact)

    if args.operation == "ship":
        result = validate_for_ship(artifact)
    elif args.operation == "iterate":
        result = validate_for_iterate(artifact)
    elif args.operation == "phase":
        if not args.target_phase:
            parser.error("--target-phase required with --for phase")
        result = validate_for_phase(artifact, args.target_phase)
    else:
        result = validate_state(artifact)

    if args.json:
        print(result.to_json())
    else:
        print(result.message)
        for error in result.errors:
            print(f"  - {error}")

    return EXIT_SUCCESS if result.ok else EXIT_VALIDATION if result.errors else EXIT_NOT_FOUND


if __name__ == "__main__":
    sys.exit(main())
```

### Step 7.3: Run tests

Run: `cd .claude/skills/audit-loop && python -m pytest tests/test_validate_state.py -v`
Expected: 4 passed

### Step 7.4: Commit

```bash
git add .claude/skills/audit-loop/scripts/validate_state.py .claude/skills/audit-loop/tests/test_validate_state.py
git commit -m "feat(audit-loop): add validate_state.py for pre-operation validation"
```

---

## Task 8: Update SKILL.md and templates/report.md

**Files:**
- Modify: `.claude/skills/audit-loop/SKILL.md`
- Modify: `.claude/skills/audit-loop/templates/report.md`

### Step 8.1: Update SKILL.md version and add Scripts Reference

Add after "## Integration" section:

```markdown
---

## Scripts Reference

Scripts enable agentic operation with persistent state.

### state.py

State CRUD operations:

```bash
# Initialize audit
python scripts/state.py create docs/plan.md

# View state
python scripts/state.py read docs/plan.md --json

# Update phase
python scripts/state.py update docs/plan.md --phase definition

# Add finding
python scripts/state.py update docs/plan.md --add-finding "description=Missing validation,priority=high"

# Start next cycle
python scripts/state.py update docs/plan.md --next-cycle

# List active audits
python scripts/state.py list docs/

# Archive completed audit
python scripts/state.py archive docs/plan.md
```

### generate_report.py

Generate markdown report:

```bash
# Output to stdout
python scripts/generate_report.py docs/plan.md

# Save to dated file
python scripts/generate_report.py docs/plan.md --save
```

### validate_state.py

Pre-operation validation:

```bash
# Check ship criteria
python scripts/validate_state.py docs/plan.md --for ship

# Check iteration allowed
python scripts/validate_state.py docs/plan.md --for iterate

# Check phase transition
python scripts/validate_state.py docs/plan.md --for phase --target-phase design
```

### calculate_stakes.py

Calculate calibration level:

```bash
# Direct values (reversibility, blast_radius, precedent, visibility)
python scripts/calculate_stakes.py 2 2 2 2

# Interactive mode
python scripts/calculate_stakes.py --interactive
```
```

### Step 8.2: Update version in frontmatter

Change `version: 1.0.0` to `version: 1.1.0`

### Step 8.3: Update templates/report.md

```markdown
# Report Template

> **Note:** Report generation is now handled by `scripts/generate_report.py`.
>
> The Handlebars template has been replaced with Python string formatting
> for reliable, dependency-free report generation.

## Usage

```bash
# Generate to stdout
python scripts/generate_report.py <artifact>

# Save to dated file
python scripts/generate_report.py <artifact> --save
```

## Report Sections

1. **Header** — Artifact name, date, calibration, cycles
2. **Summary** — Finding counts by priority
3. **Scope** — Examined and excluded areas
4. **Findings** — Table and details
5. **Limitations** — Known blind spots
6. **Counter-Conclusion** — Best argument artifact is fine
7. **Audit Trail** — Recent history events
```

### Step 8.4: Commit

```bash
git add .claude/skills/audit-loop/SKILL.md .claude/skills/audit-loop/templates/report.md
git commit -m "docs(audit-loop): update to v1.1.0 with scripts reference"
```

---

## Task 9: Run Full Test Suite

### Step 9.1: Run all tests

Run: `cd .claude/skills/audit-loop && python -m pytest tests/ -v`
Expected: All tests pass

### Step 9.2: Manual verification

Run: `cd .claude/skills/audit-loop && python scripts/state.py create /tmp/verify-test.md`
Expected: Creates state file

Run: `cd .claude/skills/audit-loop && python scripts/state.py list /tmp/`
Expected: Lists the audit

Run: `cd .claude/skills/audit-loop && python scripts/calculate_stakes.py 2 2 2 2`
Expected: `Calibration: medium (score 8)`

Run: `cd .claude/skills/audit-loop && python scripts/generate_report.py /tmp/verify-test.md`
Expected: Markdown report

Run: `cd .claude/skills/audit-loop && python scripts/validate_state.py /tmp/verify-test.md --for ship`
Expected: Ship criteria met (no findings)

### Step 9.3: Final commit

```bash
git add -A
git commit -m "test(audit-loop): verify full test suite passes"
```

---

## Verification Checklist

After implementation:
- [ ] `python scripts/state.py create docs/test.md` creates state file
- [ ] `python scripts/state.py list` finds active audits
- [ ] `python scripts/state.py validate docs/test.md` returns 0
- [ ] `python scripts/generate_report.py docs/test.md` produces markdown
- [ ] `python scripts/calculate_stakes.py 2 2 2 2` outputs medium/8
- [ ] `python -m pytest tests/ -v` all tests pass
- [ ] SKILL.md version is 1.1.0

---

## Execution Handoff

**Plan complete and saved to `docs/plans/2026-01-06-audit-loop-v1.1.0-scripts.md`. Two execution options:**

**1. Subagent-Driven (this session)** — I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** — Open new session with executing-plans, batch execution with checkpoints

**Which approach?**
