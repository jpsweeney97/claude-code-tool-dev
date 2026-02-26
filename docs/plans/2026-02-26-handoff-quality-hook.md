# Handoff Quality Hook Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement a PostToolUse hook that validates handoff/checkpoint quality after Write operations, and update documentation to match the new quality definition.

**Architecture:** Python script (`quality_check.py`) reads PostToolUse JSON from stdin, checks if the written file is a handoff/checkpoint by path, validates against the quality definition (frontmatter, sections, line count), and outputs warnings via `additionalContext`. The hook is registered in the plugin's `hooks/hooks.json` with a `Write` matcher. Non-handoff files are filtered by path check (fast exit, no I/O). Content is read from `tool_input.content` (already in stdin JSON — no disk read needed).

**Tech Stack:** Python 3.11+, pytest, no third-party dependencies.

**Plugin:** `packages/plugins/handoff/` (run tests from this directory: `cd packages/plugins/handoff && uv run pytest`)

---

## Quality Definition (agreed with user)

### Full Handoff

| Check | Requirement |
|---|---|
| Required frontmatter | `date`, `time`, `created_at`, `session_id`, `project`, `title`, `type` |
| `type` value | `"handoff"` — error on any value other than `"handoff"` or `"checkpoint"` |
| Line count floor | 400 body lines (lines after frontmatter closing `---`) |
| Required sections (13) | Goal, Session Narrative, Decisions, Changes, Codebase Knowledge, Context, Learnings, Next Steps, In Progress, Open Questions, Risks, References, Gotchas |
| No empty sections | Every `##` heading must have content beneath it |
| Hollow-handoff guardrail | At least 1 non-empty section from {Decisions, Changes, Learnings} |
| Code fence awareness | `## Heading` inside code fences is not counted as a section |

### Checkpoint

| Check | Requirement |
|---|---|
| Required frontmatter | Same 7 fields |
| `type` value | `"checkpoint"` — error on any value other than `"handoff"` or `"checkpoint"` |
| Title format | Starts with `"Checkpoint:"` |
| Line count range | 20–80 body lines (lines after frontmatter closing `---`) |
| Required sections (5) | Current Task, In Progress, Active Files, Next Action, Verification Snapshot |
| No empty sections | Same |

---

## Task 1: Quality Check Script + Tests

**Files:**
- Create: `packages/plugins/handoff/scripts/quality_check.py`
- Create: `packages/plugins/handoff/tests/test_quality_check.py`

This task creates both the validation script and its test suite. TDD cycle: stub → tests → implement → verify.

**Step 1: Create quality_check.py with constants and stubs**

```python
#!/usr/bin/env python3
"""PostToolUse hook: validates handoff/checkpoint quality after Write.

Reads PostToolUse JSON from stdin. If the written file is a handoff or
checkpoint (path under ~/.claude/handoffs/<project>/), validates:
- Required frontmatter fields present and valid
- Required sections present (13 for handoffs, 5 for checkpoints)
- Line count within range (400+ for handoffs, 20-80 for checkpoints)
- No empty sections

Outputs additionalContext via JSON stdout when issues are found.
Always exits 0 — PostToolUse hooks cannot block (file already written).
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

# --- Constants ---

REQUIRED_FRONTMATTER_FIELDS: tuple[str, ...] = (
    "date",
    "time",
    "created_at",
    "session_id",
    "project",
    "title",
    "type",
)

REQUIRED_HANDOFF_SECTIONS: tuple[str, ...] = (
    "Goal",
    "Session Narrative",
    "Decisions",
    "Changes",
    "Codebase Knowledge",
    "Context",
    "Learnings",
    "Next Steps",
    "In Progress",
    "Open Questions",
    "Risks",
    "References",
    "Gotchas",
)

REQUIRED_CHECKPOINT_SECTIONS: tuple[str, ...] = (
    "Current Task",
    "In Progress",
    "Active Files",
    "Next Action",
    "Verification Snapshot",
)

VALID_TYPES: frozenset[str] = frozenset({"handoff", "checkpoint"})

# At least 1 of these must have non-empty content (hollow-handoff guardrail)
CONTENT_REQUIRED_SECTIONS: tuple[str, ...] = (
    "Decisions",
    "Changes",
    "Learnings",
)

HANDOFF_MIN_LINES: int = 400
CHECKPOINT_MIN_LINES: int = 20
CHECKPOINT_MAX_LINES: int = 80


# --- Data model ---


@dataclass
class Issue:
    """A quality issue found during validation."""

    severity: str  # "error" or "warning"
    message: str


# --- Parsing ---


def parse_frontmatter(content: str) -> dict[str, str]:
    """Extract YAML frontmatter fields as key-value pairs.

    Simple line-by-line parser. Strips surrounding quotes from values.
    Returns empty dict if no valid frontmatter block found (no opening
    or no closing ---).
    """
    raise NotImplementedError


def parse_sections(content: str) -> list[dict[str, str]]:
    """Extract ## sections with their content.

    Returns list of {"heading": str, "content": str} dicts.
    Only captures ## headings (not # or ### or deeper).
    Skips frontmatter block if present.
    Tracks code fences to avoid false headings inside code blocks.
    """
    raise NotImplementedError


# --- Validation ---


def validate_frontmatter(frontmatter: dict[str, str], doc_type: str) -> list[Issue]:
    """Validate frontmatter fields for the given document type.

    Checks: required fields present, checkpoint title starts with
    "Checkpoint:". Type allowlist is checked in validate(), not here.
    """
    raise NotImplementedError


def validate_sections(
    sections: list[dict[str, str]], doc_type: str
) -> list[Issue]:
    """Validate section presence and content for the given document type.

    Checks: all required sections present by name, no empty sections.
    """
    raise NotImplementedError


def count_body_lines(content: str) -> int:
    """Count lines after the frontmatter closing ---.

    If no frontmatter, all lines are body lines.
    """
    raise NotImplementedError


def validate_line_count(content: str, doc_type: str) -> list[Issue]:
    """Validate body line count is within acceptable range.

    Body = lines after frontmatter closing ---.
    Handoff: minimum 400 body lines. Checkpoint: 20-80 body lines.
    """
    raise NotImplementedError


def validate(content: str) -> list[Issue]:
    """Validate a handoff or checkpoint document. Returns list of issues.

    Parses frontmatter, validates type against allowlist (error on
    invalid), defaults to "handoff" for backwards compatibility,
    then runs all validators.
    """
    raise NotImplementedError


# --- Hook integration ---


def is_handoff_path(file_path: str) -> bool:
    """Check if file is a handoff/checkpoint (not archived).

    Valid paths: ~/.claude/handoffs/<project>/<file>.md
    Invalid: archive paths, non-.md files, nested paths, other directories.
    """
    raise NotImplementedError


def format_output(issues: list[Issue]) -> str:
    """Format issues as additionalContext message for Claude."""
    raise NotImplementedError


def main() -> int:
    """PostToolUse hook entry point. Always returns 0."""
    raise NotImplementedError


if __name__ == "__main__":
    sys.exit(main())
```

**Step 2: Create test file with all tests**

```python
"""Tests for quality_check.py — handoff quality validation hook."""

from __future__ import annotations

import io
import json
from pathlib import Path
from unittest.mock import patch

from scripts.quality_check import (
    CHECKPOINT_MAX_LINES,
    CHECKPOINT_MIN_LINES,
    CONTENT_REQUIRED_SECTIONS,
    HANDOFF_MIN_LINES,
    REQUIRED_CHECKPOINT_SECTIONS,
    REQUIRED_HANDOFF_SECTIONS,
    VALID_TYPES,
    Issue,
    count_body_lines,
    format_output,
    is_handoff_path,
    main,
    parse_frontmatter,
    parse_sections,
    validate,
    validate_frontmatter,
    validate_line_count,
    validate_sections,
)


# --- Test helpers ---


def _make_frontmatter(
    overrides: dict[str, str] | None = None,
    *,
    omit: list[str] | None = None,
) -> dict[str, str]:
    """Build a valid frontmatter dict with optional overrides/omissions."""
    base = {
        "date": "2026-02-26",
        "time": "16:00",
        "created_at": "2026-02-26T16:00:00Z",
        "session_id": "test-session-id",
        "project": "test-project",
        "title": "Test Handoff",
        "type": "handoff",
    }
    if overrides:
        base.update(overrides)
    if omit:
        for key in omit:
            base.pop(key, None)
    return base


def _make_content(
    *,
    frontmatter: dict[str, str] | None = None,
    sections: list[str] | None = None,
    lines_per_section: int = 30,
    empty_sections: list[str] | None = None,
) -> str:
    """Build a synthetic handoff/checkpoint document.

    Default: valid handoff with all 13 required sections, ~450 lines.
    """
    if frontmatter is None:
        frontmatter = _make_frontmatter()
    if sections is None:
        sections = list(REQUIRED_HANDOFF_SECTIONS)

    lines = ["---"]
    for key, value in frontmatter.items():
        if key in ("time", "created_at", "title"):
            lines.append(f'{key}: "{value}"')
        else:
            lines.append(f"{key}: {value}")
    lines.append("---")
    lines.append("")
    lines.append("# Test Document")
    lines.append("")

    empty = set(empty_sections or [])
    for section in sections:
        lines.append(f"## {section}")
        lines.append("")
        if section not in empty:
            for i in range(lines_per_section):
                lines.append(f"Content line {i + 1} for {section}.")
            lines.append("")

    return "\n".join(lines)


def _run_main(input_data: dict) -> tuple[int, str]:
    """Run main() with mock stdin and capture stdout."""
    with (
        patch("sys.stdin", io.StringIO(json.dumps(input_data))),
        patch("sys.stdout", new_callable=io.StringIO) as mock_stdout,
    ):
        result = main()
    return result, mock_stdout.getvalue()


def _make_hook_input(file_path: str, content: str) -> dict:
    """Build a PostToolUse hook input dict for Write tool."""
    return {
        "tool_name": "Write",
        "tool_input": {"file_path": file_path, "content": content},
        "tool_response": {"filePath": file_path, "success": True},
        "hook_event_name": "PostToolUse",
    }


HANDOFF_PATH = str(
    Path.home()
    / ".claude"
    / "handoffs"
    / "test-project"
    / "2026-02-26_16-00_test.md"
)


# --- Frontmatter parsing ---


class TestParseFrontmatter:
    """Tests for parse_frontmatter — YAML extraction."""

    def test_extracts_fields(self) -> None:
        content = _make_content()
        fm = parse_frontmatter(content)
        assert fm["date"] == "2026-02-26"
        assert fm["type"] == "handoff"
        assert fm["title"] == "Test Handoff"

    def test_strips_quotes(self) -> None:
        content = '---\ntitle: "Quoted Value"\nother: \'single\'\n---\n'
        fm = parse_frontmatter(content)
        assert fm["title"] == "Quoted Value"
        assert fm["other"] == "single"

    def test_no_frontmatter(self) -> None:
        assert parse_frontmatter("# Just a heading\nContent.") == {}

    def test_unclosed_frontmatter(self) -> None:
        assert parse_frontmatter("---\ndate: 2026-01-01\n# No closing") == {}


# --- Frontmatter validation ---


class TestValidateFrontmatter:
    """Tests for validate_frontmatter — field presence and value checks."""

    def test_valid_handoff(self) -> None:
        assert validate_frontmatter(_make_frontmatter(), "handoff") == []

    def test_missing_field(self) -> None:
        issues = validate_frontmatter(
            _make_frontmatter(omit=["session_id"]), "handoff"
        )
        assert len(issues) == 1
        assert issues[0].severity == "error"
        assert "session_id" in issues[0].message

    def test_multiple_missing_fields(self) -> None:
        issues = validate_frontmatter(
            _make_frontmatter(omit=["date", "time"]), "handoff"
        )
        assert len(issues) == 1  # Single error listing both fields
        assert "date" in issues[0].message
        assert "time" in issues[0].message

    def test_checkpoint_title_missing_prefix(self) -> None:
        fm = _make_frontmatter(
            overrides={"type": "checkpoint", "title": "No Prefix"}
        )
        issues = validate_frontmatter(fm, "checkpoint")
        assert any("Checkpoint:" in i.message for i in issues)

    def test_checkpoint_title_valid(self) -> None:
        fm = _make_frontmatter(
            overrides={"type": "checkpoint", "title": "Checkpoint: Valid"}
        )
        assert validate_frontmatter(fm, "checkpoint") == []


# --- Section parsing ---


class TestParseSections:
    """Tests for parse_sections — ## heading extraction."""

    def test_extracts_sections(self) -> None:
        content = _make_content(
            sections=["Goal", "Next Steps"], lines_per_section=3
        )
        sections = parse_sections(content)
        assert len(sections) == 2
        assert sections[0]["heading"] == "Goal"
        assert sections[1]["heading"] == "Next Steps"

    def test_content_between_headings(self) -> None:
        content = _make_content(sections=["Goal"], lines_per_section=3)
        sections = parse_sections(content)
        assert "Content line 1 for Goal." in sections[0]["content"]

    def test_ignores_h3_subheadings(self) -> None:
        content = (
            "---\ntype: handoff\n---\n## Goal\nContent\n### Sub\nMore"
        )
        sections = parse_sections(content)
        assert len(sections) == 1
        assert "Sub" not in sections[0]["heading"]
        assert "More" in sections[0]["content"]

    def test_no_frontmatter(self) -> None:
        content = "## Section One\nContent\n## Section Two\nMore"
        sections = parse_sections(content)
        assert len(sections) == 2

    def test_ignores_headings_inside_code_fences(self) -> None:
        """## Heading inside a code block is not a section boundary."""
        content = (
            "---\ntype: handoff\n---\n"
            "## Real Section\n"
            "Some content\n"
            "```markdown\n"
            "## Fake Section\n"
            "This is inside a code fence\n"
            "```\n"
            "More content after fence\n"
            "## Another Real Section\n"
            "Final content"
        )
        sections = parse_sections(content)
        assert len(sections) == 2
        assert sections[0]["heading"] == "Real Section"
        assert sections[1]["heading"] == "Another Real Section"
        assert "Fake Section" not in [s["heading"] for s in sections]
        assert "inside a code fence" in sections[0]["content"]


# --- Section validation ---


class TestValidateSections:
    """Tests for validate_sections — required sections and empty checks."""

    def test_all_handoff_sections_present(self) -> None:
        sections = [
            {"heading": s, "content": "text"}
            for s in REQUIRED_HANDOFF_SECTIONS
        ]
        assert validate_sections(sections, "handoff") == []

    def test_missing_section(self) -> None:
        sections = [
            {"heading": s, "content": "text"}
            for s in REQUIRED_HANDOFF_SECTIONS
            if s != "Goal"
        ]
        issues = validate_sections(sections, "handoff")
        assert any("Goal" in i.message for i in issues)

    def test_all_checkpoint_sections_present(self) -> None:
        sections = [
            {"heading": s, "content": "text"}
            for s in REQUIRED_CHECKPOINT_SECTIONS
        ]
        assert validate_sections(sections, "checkpoint") == []

    def test_empty_section_warned(self) -> None:
        sections = [{"heading": "Goal", "content": ""}]
        issues = validate_sections(sections, "handoff")
        assert any(
            i.severity == "warning" and "Goal" in i.message for i in issues
        )

    def test_whitespace_only_is_empty(self) -> None:
        sections = [{"heading": "Goal", "content": "   \n  \n  "}]
        issues = validate_sections(sections, "handoff")
        assert any(
            i.severity == "warning" and "Empty" in i.message for i in issues
        )

    def test_extra_sections_allowed(self) -> None:
        sections = [
            {"heading": s, "content": "text"}
            for s in REQUIRED_HANDOFF_SECTIONS
        ]
        sections.append(
            {"heading": "Conversation Highlights", "content": "text"}
        )
        assert validate_sections(sections, "handoff") == []

    def test_hollow_handoff_guardrail(self) -> None:
        """All 13 sections present but Decisions/Changes/Learnings all empty."""
        sections = []
        for s in REQUIRED_HANDOFF_SECTIONS:
            if s in CONTENT_REQUIRED_SECTIONS:
                sections.append({"heading": s, "content": "No changes."})
            else:
                sections.append({"heading": s, "content": "text"})
        # Replace content-required sections with placeholder-only
        for i, sec in enumerate(sections):
            if sec["heading"] in CONTENT_REQUIRED_SECTIONS:
                sections[i] = {"heading": sec["heading"], "content": ""}
        issues = validate_sections(sections, "handoff")
        assert any(
            i.severity == "error" and "Decisions" in i.message
            for i in issues
        )

    def test_hollow_handoff_passes_with_one_content_section(self) -> None:
        """Guardrail passes when at least one of {Decisions, Changes, Learnings} has content."""
        sections = []
        for s in REQUIRED_HANDOFF_SECTIONS:
            if s == "Decisions":
                sections.append({"heading": s, "content": "Chose X over Y."})
            elif s in CONTENT_REQUIRED_SECTIONS:
                sections.append({"heading": s, "content": ""})
            else:
                sections.append({"heading": s, "content": "text"})
        issues = validate_sections(sections, "handoff")
        # Should have empty-section warnings but no guardrail error
        assert not any(
            "Decisions, Changes, Learnings" in i.message for i in issues
        )

    def test_hollow_guardrail_skipped_when_sections_absent(self) -> None:
        """When content-required sections are entirely absent, only missing-sections fires."""
        sections = [
            {"heading": s, "content": "text"}
            for s in REQUIRED_HANDOFF_SECTIONS
            if s not in CONTENT_REQUIRED_SECTIONS
        ]
        issues = validate_sections(sections, "handoff")
        # Missing-sections error should fire
        assert any("Missing required sections" in i.message for i in issues)
        # Hollow-handoff guardrail should NOT fire (sections absent, not empty)
        assert not any("Hollow handoff" in i.message for i in issues)


# --- Line count validation ---


class TestValidateLineCount:
    """Tests for validate_line_count — range enforcement."""

    def test_handoff_above_minimum(self) -> None:
        content = "\n".join(["line"] * 450)
        assert validate_line_count(content, "handoff") == []

    def test_handoff_below_minimum(self) -> None:
        content = "\n".join(["line"] * 200)
        issues = validate_line_count(content, "handoff")
        assert len(issues) == 1
        assert issues[0].severity == "error"
        assert "200" in issues[0].message

    def test_handoff_at_exact_minimum(self) -> None:
        content = "\n".join(["line"] * HANDOFF_MIN_LINES)
        assert validate_line_count(content, "handoff") == []

    def test_checkpoint_within_range(self) -> None:
        content = "\n".join(["line"] * 50)
        assert validate_line_count(content, "checkpoint") == []

    def test_checkpoint_below_minimum(self) -> None:
        content = "\n".join(["line"] * 15)
        issues = validate_line_count(content, "checkpoint")
        assert len(issues) == 1
        assert "15" in issues[0].message

    def test_checkpoint_above_maximum(self) -> None:
        content = "\n".join(["line"] * 100)
        issues = validate_line_count(content, "checkpoint")
        assert len(issues) == 1
        assert "100" in issues[0].message

    def test_checkpoint_at_exact_boundaries(self) -> None:
        at_min = "\n".join(["line"] * CHECKPOINT_MIN_LINES)
        at_max = "\n".join(["line"] * CHECKPOINT_MAX_LINES)
        assert validate_line_count(at_min, "checkpoint") == []
        assert validate_line_count(at_max, "checkpoint") == []


# --- Body line counting ---


class TestCountBodyLines:
    """Tests for count_body_lines — frontmatter-aware line counting."""

    def test_with_frontmatter(self) -> None:
        content = "---\ntype: handoff\ndate: 2026-01-01\n---\nLine 1\nLine 2\nLine 3"
        assert count_body_lines(content) == 3

    def test_without_frontmatter(self) -> None:
        content = "Line 1\nLine 2\nLine 3"
        assert count_body_lines(content) == 3

    def test_trailing_newline(self) -> None:
        """Trailing newline should not inflate the count."""
        with_newline = "---\ntype: handoff\n---\nLine 1\nLine 2\n"
        without_newline = "---\ntype: handoff\n---\nLine 1\nLine 2"
        assert count_body_lines(with_newline) == count_body_lines(without_newline)

    def test_unclosed_frontmatter(self) -> None:
        """Unclosed frontmatter means all lines are body."""
        content = "---\ntype: handoff\nLine 1\nLine 2"
        assert count_body_lines(content) == 4


# --- Top-level validate ---


class TestValidate:
    """Tests for validate — full document validation."""

    def test_valid_handoff(self) -> None:
        assert validate(_make_content()) == []

    def test_valid_checkpoint(self) -> None:
        content = _make_content(
            frontmatter=_make_frontmatter(
                overrides={
                    "type": "checkpoint",
                    "title": "Checkpoint: Test",
                }
            ),
            sections=list(REQUIRED_CHECKPOINT_SECTIONS),
            lines_per_section=5,
        )
        assert validate(content) == []

    def test_no_frontmatter(self) -> None:
        issues = validate("# No frontmatter\n## Goal\nContent")
        assert len(issues) == 1
        assert "frontmatter" in issues[0].message.lower()

    def test_defaults_to_handoff_when_type_missing(self) -> None:
        """Missing type field is an error but doc still validates as handoff."""
        content = _make_content(frontmatter=_make_frontmatter(omit=["type"]))
        issues = validate(content)
        assert any("type" in i.message for i in issues)

    def test_invalid_type_errors(self) -> None:
        """type: foo should produce an error and stop — no section/line-count errors."""
        content = _make_content(
            frontmatter=_make_frontmatter(overrides={"type": "foo"}),
        )
        issues = validate(content)
        assert len(issues) == 1, f"Expected exactly 1 issue (type error), got {len(issues)}: {issues}"
        assert issues[0].severity == "error"
        assert "foo" in issues[0].message
        assert all(t in issues[0].message for t in sorted(VALID_TYPES))

    def test_accumulates_multiple_issues(self) -> None:
        content = _make_content(
            frontmatter=_make_frontmatter(omit=["session_id"]),
            sections=["Goal", "Next Steps"],
            lines_per_section=5,
        )
        issues = validate(content)
        # Missing field + missing sections + under line count
        assert len(issues) >= 3


# --- Path filtering ---


class TestIsHandoffPath:
    """Tests for is_handoff_path — file path detection."""

    def test_valid_path(self) -> None:
        assert is_handoff_path(HANDOFF_PATH) is True

    def test_archive_rejected(self) -> None:
        path = str(
            Path.home()
            / ".claude"
            / "handoffs"
            / "proj"
            / ".archive"
            / "test.md"
        )
        assert is_handoff_path(path) is False

    def test_non_handoff_directory(self) -> None:
        assert is_handoff_path("/tmp/random/file.md") is False

    def test_non_md_file(self) -> None:
        path = str(
            Path.home() / ".claude" / "handoffs" / "proj" / "file.txt"
        )
        assert is_handoff_path(path) is False

    def test_nested_too_deep(self) -> None:
        path = str(
            Path.home()
            / ".claude"
            / "handoffs"
            / "proj"
            / "sub"
            / "file.md"
        )
        assert is_handoff_path(path) is False

    def test_directly_in_handoffs_dir(self) -> None:
        """File at handoffs/ level (no project dir) is rejected."""
        path = str(Path.home() / ".claude" / "handoffs" / "file.md")
        assert is_handoff_path(path) is False


# --- Output formatting ---


class TestFormatOutput:
    """Tests for format_output — message generation."""

    def test_errors_and_warnings(self) -> None:
        issues = [
            Issue("error", "Missing field: date"),
            Issue("warning", "Empty section: Goal"),
        ]
        msg = format_output(issues)
        assert "1 error(s)" in msg
        assert "1 warning(s)" in msg
        assert "Missing field: date" in msg
        assert "Empty section: Goal" in msg

    def test_errors_only(self) -> None:
        issues = [Issue("error", "Test error")]
        msg = format_output(issues)
        assert "Errors:" in msg
        assert "Warnings:" not in msg
        assert "Fix the errors" in msg

    def test_warnings_only_no_fix_instruction(self) -> None:
        """Warnings-only output should NOT say 'Fix the errors and rewrite'."""
        issues = [Issue("warning", "Test warning")]
        msg = format_output(issues)
        assert "Warnings:" in msg
        assert "Errors:" not in msg
        assert "Fix the errors" not in msg
        assert "review" in msg.lower()  # Softer language for warnings


# --- Hook integration ---


class TestMain:
    """Tests for main — PostToolUse hook entry point."""

    def test_non_handoff_path_silent(self) -> None:
        """Non-handoff file produces no output."""
        result, output = _run_main(
            _make_hook_input("/tmp/test.py", "print('hello')")
        )
        assert result == 0
        assert output == ""

    def test_valid_handoff_silent(self) -> None:
        """Valid handoff produces no output."""
        result, output = _run_main(
            _make_hook_input(HANDOFF_PATH, _make_content())
        )
        assert result == 0
        assert output == ""

    def test_invalid_handoff_outputs_context(self) -> None:
        """Invalid handoff produces additionalContext JSON with correct contract."""
        content = "---\ntype: handoff\n---\n## Goal\nShort."
        result, output = _run_main(
            _make_hook_input(HANDOFF_PATH, content)
        )
        assert result == 0
        parsed = json.loads(output)
        hook_output = parsed["hookSpecificOutput"]
        assert hook_output["hookEventName"] == "PostToolUse"
        assert "error" in hook_output["additionalContext"].lower()

    def test_malformed_json_silent(self) -> None:
        """Malformed stdin JSON produces no output, exit 0."""
        with (
            patch("sys.stdin", io.StringIO("not json")),
            patch("sys.stdout", new_callable=io.StringIO) as mock_stdout,
        ):
            result = main()
        assert result == 0
        assert mock_stdout.getvalue() == ""

    def test_empty_content_silent(self) -> None:
        """Empty content field produces no output."""
        result, output = _run_main(
            _make_hook_input(HANDOFF_PATH, "")
        )
        assert result == 0
        assert output == ""

    def test_archive_path_silent(self) -> None:
        """Archive path is not validated."""
        archive_path = str(
            Path.home()
            / ".claude"
            / "handoffs"
            / "test-project"
            / ".archive"
            / "old.md"
        )
        result, output = _run_main(
            _make_hook_input(archive_path, "---\ntype: handoff\n---\nShort")
        )
        assert result == 0
        assert output == ""
```

**Step 3: Run tests to verify they fail**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_quality_check.py -v`
Expected: All tests FAIL with `NotImplementedError`

**Step 4: Implement all functions in quality_check.py**

Replace the stub functions with these implementations:

`parse_frontmatter`:
```python
def parse_frontmatter(content: str) -> dict[str, str]:
    lines = content.split("\n")
    if not lines or lines[0].strip() != "---":
        return {}

    frontmatter: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" in line:
            key, _, value = line.partition(":")
            value = value.strip()
            if (value.startswith('"') and value.endswith('"')) or (
                value.startswith("'") and value.endswith("'")
            ):
                value = value[1:-1]
            frontmatter[key.strip()] = value
    else:
        return {}  # No closing ---

    return frontmatter
```

`parse_sections`:
```python
def parse_sections(content: str) -> list[dict[str, str]]:
    lines = content.split("\n")

    # Skip frontmatter
    body_start = 0
    if lines and lines[0].strip() == "---":
        for i, line in enumerate(lines[1:], start=1):
            if line.strip() == "---":
                body_start = i + 1
                break

    sections: list[dict[str, str]] = []
    current_heading: str | None = None
    current_content: list[str] = []
    inside_fence: bool = False

    for line in lines[body_start:]:
        # Track code fences to avoid false headings inside code blocks
        if line.startswith("```"):
            inside_fence = not inside_fence

        if (
            not inside_fence
            and line.startswith("## ")
            and not line.startswith("### ")
        ):
            if current_heading is not None:
                sections.append({
                    "heading": current_heading,
                    "content": "\n".join(current_content).strip(),
                })
            current_heading = line[3:].strip()
            current_content = []
        elif current_heading is not None:
            current_content.append(line)

    if current_heading is not None:
        sections.append({
            "heading": current_heading,
            "content": "\n".join(current_content).strip(),
        })

    return sections
```

`validate_frontmatter`:
```python
def validate_frontmatter(frontmatter: dict[str, str], doc_type: str) -> list[Issue]:
    issues: list[Issue] = []

    missing = [f for f in REQUIRED_FRONTMATTER_FIELDS if f not in frontmatter]
    if missing:
        issues.append(Issue(
            "error", f"Missing required frontmatter: {', '.join(missing)}"
        ))

    # Type allowlist is checked in validate(), not here.
    # This function only checks type-specific constraints.

    if doc_type == "checkpoint" and "title" in frontmatter:
        title = frontmatter["title"]
        if not title.startswith("Checkpoint:"):
            issues.append(Issue(
                "warning",
                f"Checkpoint title should start with 'Checkpoint:', "
                f"got: '{title[:60]}'",
            ))

    return issues
```

`validate_sections`:
```python
def validate_sections(
    sections: list[dict[str, str]], doc_type: str
) -> list[Issue]:
    issues: list[Issue] = []

    required = (
        REQUIRED_HANDOFF_SECTIONS
        if doc_type == "handoff"
        else REQUIRED_CHECKPOINT_SECTIONS
    )
    section_names = [s["heading"] for s in sections]

    missing = [name for name in required if name not in section_names]
    if missing:
        issues.append(Issue(
            "error", f"Missing required sections: {', '.join(missing)}"
        ))

    for section in sections:
        if not section["content"].strip():
            issues.append(Issue(
                "warning", f"Empty section: '{section['heading']}'"
            ))

    # Hollow-handoff guardrail: at least 1 of {Decisions, Changes, Learnings}
    # must have non-empty content (handoffs only).
    # Only fires when all 3 sections are present but empty — missing sections
    # are already caught by the missing-sections check above.
    if doc_type == "handoff":
        present_content_sections = [
            s for s in sections
            if s["heading"] in CONTENT_REQUIRED_SECTIONS
        ]
        if len(present_content_sections) == len(CONTENT_REQUIRED_SECTIONS):
            has_substance = any(
                s["content"].strip() for s in present_content_sections
            )
            if not has_substance:
                issues.append(Issue(
                    "error",
                    "Hollow handoff: at least 1 of {Decisions, Changes, Learnings} "
                    "must have substantive content.",
                ))

    return issues
```

`count_body_lines`:
```python
def count_body_lines(content: str) -> int:
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        return len(lines)  # No frontmatter — all lines are body
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return len(lines) - (i + 1)
    return len(lines)  # No closing --- — all lines are body
```

`validate_line_count`:
```python
def validate_line_count(content: str, doc_type: str) -> list[Issue]:
    issues: list[Issue] = []
    body_lines = count_body_lines(content)

    if doc_type == "handoff":
        if body_lines < HANDOFF_MIN_LINES:
            issues.append(Issue(
                "error",
                f"Handoff body is {body_lines} lines "
                f"(minimum: {HANDOFF_MIN_LINES}). "
                "Under-capturing session content.",
            ))
    elif doc_type == "checkpoint":
        if body_lines < CHECKPOINT_MIN_LINES:
            issues.append(Issue(
                "error",
                f"Checkpoint body is {body_lines} lines "
                f"(minimum: {CHECKPOINT_MIN_LINES}). "
                "Missing required sections.",
            ))
        elif body_lines > CHECKPOINT_MAX_LINES:
            issues.append(Issue(
                "warning",
                f"Checkpoint body is {body_lines} lines "
                f"(maximum: {CHECKPOINT_MAX_LINES}). "
                "Consider a full handoff instead.",
            ))

    return issues
```

`validate`:
```python
def validate(content: str) -> list[Issue]:
    frontmatter = parse_frontmatter(content)

    if not frontmatter:
        return [Issue(
            "error",
            "No frontmatter found. Document must start with --- YAML block.",
        )]

    # Default to handoff for backwards compatibility
    doc_type = frontmatter.get("type", "handoff")

    issues: list[Issue] = []

    # Type allowlist — validate before branching to prevent
    # untrusted input controlling which validation rules apply
    if doc_type not in VALID_TYPES:
        issues.append(Issue(
            "error",
            f"Invalid type '{doc_type}'. Must be one of: {', '.join(sorted(VALID_TYPES))}.",
        ))
        return issues  # Can't validate sections/lines without valid type

    issues.extend(validate_frontmatter(frontmatter, doc_type))
    issues.extend(validate_sections(parse_sections(content), doc_type))
    issues.extend(validate_line_count(content, doc_type))

    return issues
```

`is_handoff_path`:
```python
def is_handoff_path(file_path: str) -> bool:
    path = Path(file_path)
    handoffs_dir = Path.home() / ".claude" / "handoffs"

    try:
        relative = path.relative_to(handoffs_dir)
    except ValueError:
        return False

    if path.suffix != ".md":
        return False

    if ".archive" in relative.parts:
        return False

    # Must be exactly: <project>/<file>.md (2 parts)
    if len(relative.parts) != 2:
        return False

    return True
```

`format_output`:
```python
def format_output(issues: list[Issue]) -> str:
    errors = [i for i in issues if i.severity == "error"]
    warnings = [i for i in issues if i.severity == "warning"]

    parts: list[str] = []
    parts.append(
        f"Handoff quality check found "
        f"{len(errors)} error(s) and {len(warnings)} warning(s)."
    )

    if errors:
        parts.append("\nErrors:")
        for e in errors:
            parts.append(f"- {e.message}")

    if warnings:
        parts.append("\nWarnings:")
        for w in warnings:
            parts.append(f"- {w.message}")

    if errors:
        parts.append("\nFix the errors and rewrite the handoff.")
    else:
        parts.append("\nPlease review the warnings above.")

    return "\n".join(parts)
```

`main`:
```python
def main() -> int:
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError, ValueError):
        return 0

    file_path = hook_input.get("tool_input", {}).get("file_path", "")

    if not is_handoff_path(file_path):
        return 0

    content = hook_input.get("tool_input", {}).get("content", "")
    if not content:
        return 0

    issues = validate(content)

    if not issues:
        return 0

    output = {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": format_output(issues),
        }
    }

    json.dump(output, sys.stdout)
    return 0
```

**Step 5: Run tests to verify they pass**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_quality_check.py -v`
Expected: All 55 tests PASS

**Step 6: Run full test suite to verify no regressions**

Run: `cd packages/plugins/handoff && uv run pytest -v`
Expected: All 110 tests PASS (55 existing + 55 new)

Actually the existing count is 55 (26 cleanup + 29 search). We're adding 44. Total expected: 99 tests. But that's only if I have exactly 44 tests. Let me count from the test file:
- TestParseFrontmatter: 4
- TestValidateFrontmatter: 6
- TestParseSections: 4
- TestValidateSections: 6
- TestValidateLineCount: 7
- TestValidate: 5
- TestIsHandoffPath: 6
- TestFormatOutput: 3
- TestMain: 6

New counts after Codex review fixes:
- TestParseFrontmatter: 4
- TestValidateFrontmatter: 5 (removed test_wrong_type — dead code)
- TestParseSections: 5 (added code fence test)
- TestValidateSections: 9 (added 2 hollow-handoff guardrail + 1 double-fire regression)
- TestCountBodyLines: 4 (new — frontmatter/no-frontmatter/trailing-newline/unclosed)
- TestValidateLineCount: 7
- TestValidate: 6 (added invalid type test)
- TestIsHandoffPath: 6
- TestFormatOutput: 3 (updated warnings_only test)
- TestMain: 6

Total: 55 tests. Plus 55 existing = 110 total.

Run: `cd packages/plugins/handoff && uv run pytest -v`
Expected: All tests PASS (55 existing + 55 new = 110 total)

**Step 7: Commit**

```bash
git add packages/plugins/handoff/scripts/quality_check.py packages/plugins/handoff/tests/test_quality_check.py
git commit -m "feat(handoff): add quality validation script with tests

PostToolUse hook script validates handoff/checkpoint quality:
- 7 required frontmatter fields
- 13 required sections (handoff) / 5 (checkpoint)
- Body line count: 400+ (handoff) / 20-80 (checkpoint)
- Empty section detection + hollow-handoff guardrail
- Type allowlist validation
- Code fence-aware section parsing
- Checkpoint title prefix validation
- Conditional error/warning messaging

50 tests covering parsing, validation, path filtering, and hook integration."
```

---

## Task 2: Hook Registration + Version Bump

**Files:**
- Modify: `packages/plugins/handoff/hooks/hooks.json`
- Modify: `packages/plugins/handoff/.claude-plugin/plugin.json`
- Modify: `packages/plugins/handoff/pyproject.toml`

**Step 1: Update hooks.json**

Replace entire file content:
```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cleanup.py"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ${CLAUDE_PLUGIN_ROOT}/scripts/quality_check.py"
          }
        ]
      }
    ]
  }
}
```

**Step 2: Bump version in plugin.json**

Change `"version": "1.2.0"` → `"version": "1.3.0"`

**Step 3: Bump version in pyproject.toml**

Change `version = "1.2.0"` → `version = "1.3.0"`

**Step 4: Commit**

```bash
git add packages/plugins/handoff/hooks/hooks.json packages/plugins/handoff/.claude-plugin/plugin.json packages/plugins/handoff/pyproject.toml
git commit -m "feat(handoff): register quality check PostToolUse hook

Adds Write matcher hook pointing to quality_check.py.
Bumps plugin version to 1.3.0."
```

---

## Task 3: Documentation Updates

**Files:**
- Modify: `packages/plugins/handoff/skills/creating-handoffs/SKILL.md`
- Modify: `packages/plugins/handoff/references/format-reference.md`
- Modify: `docs/tickets/handoff-quality-hook.md`

**Step 1: Update SKILL.md**

Five edits:

**Edit A — Line 61:** Change section inclusion policy.

Old:
```
- Body with relevant sections from checklist (only non-empty sections included)
```
New:
```
- Body with all 13 required sections (placeholder content when not applicable)
```

**Edit B — Line 70:** Change line count target.

Old:
```
| Body line count | >=300 for simple sessions, >=500 for complex |
```
New:
```
| Body line count | >=400 for all sessions, >=500 for complex |
```

**Edit C — Lines 128-138:** Update section selection and depth check.

Old:
```
5. **Select relevant sections** using the checklist in [format-reference.md](../../references/format-reference.md)
   - If no sections have content, **STOP** and ask: "I don't see anything to hand off. What should I capture?"
   - Omit empty sections from output
   - **Calibration:** Distinguish verified facts (explicitly discussed) from inferred conclusions (reasonable next steps) from assumed context (background not verified this session)

5b. **Depth check before writing:**
   - Verify minimum 6 body sections with content (most sessions should populate 8+)
   - Verify each Decision entry has all 8 elements from the synthesis prompts
   - Estimate body line count — target 300-700 depending on session complexity
   - If estimate is under 300, you are almost certainly under-capturing. Re-examine: implicit decisions, codebase knowledge gained, conversation dynamics, exploration arc, files read that produced understanding.
   - **Default to inclusion.** If you're unsure whether something belongs, include it.
```
New:
```
5. **Select relevant sections** using the checklist in [format-reference.md](../../references/format-reference.md)
   - If no sections have content, **STOP** and ask: "I don't see anything to hand off. What should I capture?"
   - Include all 13 required sections. Use brief placeholder content (e.g., "No risks identified this session.") for sections that genuinely don't apply
   - **Calibration:** Distinguish verified facts (explicitly discussed) from inferred conclusions (reasonable next steps) from assumed context (background not verified this session)

5b. **Depth check before writing:**
   - Verify all 13 required sections present: Goal, Session Narrative, Decisions, Changes, Codebase Knowledge, Context, Learnings, Next Steps, In Progress, Open Questions, Risks, References, Gotchas
   - Verify each Decision entry has all 8 elements from the synthesis prompts
   - Estimate body line count — target 400-700 depending on session complexity
   - If estimate is under 400, you are almost certainly under-capturing. Re-examine: implicit decisions, codebase knowledge gained, conversation dynamics, exploration arc, files read that produced understanding.
   - **Default to inclusion.** If you're unsure whether something belongs, include it.
```

**Edit D — Lines 219-223:** Update quality calibration table.

Old:
```
| Complexity | Target Lines | Required Sections |
|------------|-------------|-------------------|
| Simple (pure execution of known plan) | 300+ | Goal, Decisions, Changes, Codebase Knowledge, Session Narrative, Next Steps |
| Moderate (decisions, exploration) | 400-500 | Above + Context, Learnings, Conversation Highlights, User Preferences |
| Complex (pivots, design work, discovery) | 500-700+ | All sections fully populated, including Rejected Approaches, Open Questions, Risks, References |
```
New:
```
| Complexity | Target Lines | Required Sections |
|------------|-------------|-------------------|
| All sessions | 400+ | All 13 required: Goal, Session Narrative, Decisions, Changes, Codebase Knowledge, Context, Learnings, Next Steps, In Progress, Open Questions, Risks, References, Gotchas |
| Moderate (decisions, exploration) | 500+ | Above + Conversation Highlights, User Preferences |
| Complex (pivots, design work, discovery) | 500-700+ | All sections fully populated, including Rejected Approaches |
```

**Edit E — Line 211:** Update anti-pattern threshold.

Old:
```
| Handoffs under 300 lines | Indicates significant information loss | Re-examine session for under-capture — implicit decisions, codebase knowledge, conversation dynamics |
```
New:
```
| Handoffs under 400 lines | Indicates significant information loss | Re-examine session for under-capture — implicit decisions, codebase knowledge, conversation dynamics |
```

**Step 2: Update format-reference.md**

Two edits:

**Edit A — Lines 30-32:** Update section policy.

Old:
```
## Section Checklist

Include sections relevant to the session. Empty sections are omitted. Depth targets are minimums — exceed them when the session warrants it.
```
New:
```
## Section Checklist

**Required sections (13):** Goal, Session Narrative, Decisions, Changes, Codebase Knowledge, Context, Learnings, Next Steps, In Progress, Open Questions, Risks, References, Gotchas. All must be present. Use placeholder content (e.g., "No risks identified this session.") when a section genuinely doesn't apply. Depth targets are minimums — exceed them when the session warrants it.
```

**Edit B — Lines 705-713:** Update quality calibration.

Old:
```
## Quality Calibration

| Complexity | Target Lines | Characteristics |
|------------|-------------|-----------------|
| Simple (pure execution of known plan) | 300+ | Detailed changes, codebase knowledge, session narrative, next steps with approach suggestions |
| Moderate (decisions, exploration) | 400-500 | Full decisions with reasoning chains, session narrative with pivots, learnings with mechanisms, context |
| Complex (pivots, design work, discovery) | 500-700+ | All sections fully populated, deep decision analysis with trade-off matrices, architecture maps, conversation highlights with quotes |

A handoff under 300 lines almost certainly has significant information loss. Re-examine the session for: implicit decisions, codebase knowledge gained, conversation dynamics, exploration arc, and files that produced understanding worth preserving.
```
New:
```
## Quality Calibration

| Complexity | Target Lines | Characteristics |
|------------|-------------|-----------------|
| All sessions | 400+ | All 13 required sections present with meaningful content |
| Moderate (decisions, exploration) | 500+ | Deep decisions with reasoning chains, learnings with mechanisms, rich context |
| Complex (pivots, design work, discovery) | 500-700+ | All sections fully populated, deep decision analysis with trade-off matrices, architecture maps, conversation highlights with quotes |

A handoff under 400 lines almost certainly has significant information loss. Re-examine the session for: implicit decisions, codebase knowledge gained, conversation dynamics, exploration arc, and files that produced understanding worth preserving.
```

**Step 3: Update ticket**

In `docs/tickets/handoff-quality-hook.md`:

**Edit A:** Change status.

Old: `status: planning`
New: `status: implementing`

**Edit B:** Replace acceptance criteria.

Old:
```
## Acceptance Criteria

- [ ] PostToolUse hook fires on Write to `~/.claude/handoffs/`
- [ ] Warns when full handoff is under 300 lines
- [ ] Warns when checkpoint is under 20 lines (missing required sections)
- [ ] Warns when checkpoint exceeds 80 lines (drifting toward handoff territory)
- [ ] Warns when required frontmatter fields are missing
- [ ] Warns when fewer than 4 sections present (handoff) or 5 sections (checkpoint)
- [ ] Uses `type` field to select threshold set (checkpoint: 20-80, handoff: 300+)
- [ ] Warning appears as `additionalContext` system reminder
- [ ] Hook completes in under 2 seconds
- [ ] Hook never blocks session or tool execution (exit 0 always)
```
New:
```
## Acceptance Criteria

- [ ] PostToolUse hook fires on Write to `~/.claude/handoffs/`
- [ ] Warns when full handoff is under 400 lines
- [ ] Warns when checkpoint is under 20 lines
- [ ] Warns when checkpoint exceeds 80 lines
- [ ] Warns when any of 7 required frontmatter fields are missing
- [ ] Warns when any of 13 required sections missing (handoff) or 5 sections (checkpoint)
- [ ] Warns when sections have no content (empty heading)
- [ ] Uses `type` field to select threshold set (checkpoint: 20-80, handoff: 400+)
- [ ] Validates checkpoint title starts with "Checkpoint:"
- [ ] Warning appears as `additionalContext` system reminder
- [ ] Type validated against {handoff, checkpoint} allowlist before branching
- [ ] Code fence-aware section parsing (## inside ``` not counted)
- [ ] Hollow-handoff guardrail: ≥1 non-empty from {Decisions, Changes, Learnings}
- [ ] Body line count (after frontmatter), not total line count
- [ ] Conditional tail message (errors → "fix and rewrite", warnings → "review")
- [ ] Hook completes in under 2 seconds
- [ ] Hook never blocks session or tool execution (exit 0 always)
- [ ] SKILL.md updated: 13 required sections, 400-line minimum
- [ ] format-reference.md updated to match new quality definition
```

**Step 4: Commit**

```bash
git add packages/plugins/handoff/skills/creating-handoffs/SKILL.md packages/plugins/handoff/references/format-reference.md docs/tickets/handoff-quality-hook.md
git commit -m "docs(handoff): update quality requirements to match hook

- SKILL.md: 13 required sections, 400-line minimum
- format-reference.md: required section list, updated calibration
- Ticket: updated acceptance criteria and status"
```

---

## Task 4: Final Verification

**Step 1: Run full test suite**

Run: `cd packages/plugins/handoff && uv run pytest -v`
Expected: All tests PASS (55 existing + 55 new = 110 total)

**Step 2: Run lint**

Run: `cd packages/plugins/handoff && ruff check scripts/quality_check.py tests/test_quality_check.py`
Expected: Clean (no issues)

**Step 3: Manual hook test**

Test the hook script directly with mock input:

```bash
echo '{"tool_name":"Write","tool_input":{"file_path":"/Users/jp/.claude/handoffs/test/bad.md","content":"---\ntype: handoff\n---\n## Goal\nShort."},"tool_response":{"success":true},"hook_event_name":"PostToolUse"}' | python3 packages/plugins/handoff/scripts/quality_check.py
```

Expected: JSON output with `additionalContext` containing errors (missing sections, under 400 lines, missing frontmatter fields).

```bash
echo '{"tool_name":"Write","tool_input":{"file_path":"/tmp/unrelated.py","content":"print(1)"},"tool_response":{"success":true},"hook_event_name":"PostToolUse"}' | python3 packages/plugins/handoff/scripts/quality_check.py
```

Expected: No output (non-handoff path, fast exit).

---

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Hook matcher | `Write` only (not `Edit\|Write`) | Handoffs are created with Write. If Claude fixes issues, it rewrites (Write again). Matching Edit would fire on every file edit session-wide. |
| Content source | `tool_input.content` from stdin | Available for Write tool, no disk I/O. Faster and more reliable than reading from disk. |
| Output format | `additionalContext` in `hookSpecificOutput` | Confirmed working pattern (A1 from audit). Appears as system-reminder in Claude's context. |
| Frontmatter parser | Duplicate from search.py | Shared modules break hook invocation (accepted trade-off from Enhancement #1, Finding #6). |
| Section matching | Exact case-sensitive heading names | Matches convention in SKILL.md and all existing handoffs. Typos are caught as "missing section." |
| Default type | `"handoff"` when `type` field missing | Backwards compatibility per handoff-contract.md. Missing `type` is still reported as an error. |
| Type allowlist | Error on `type` not in `{handoff, checkpoint}` before branching | Prevents untrusted input controlling which validation rules apply. Eliminates dead-code mismatch branch. (Codex review) |
| Code fence tracking | `parse_sections` tracks ``` fences | Prevents false-pass where `## Gotchas` inside a code block satisfies the section check. Pattern from `search.py:85-91`. (Codex review) |
| Body line count | Count lines after frontmatter closing `---` | Quality targets (400, 20-80) refer to body lines. Counting total lines inflated by ~15 frontmatter lines. (Codex review) |
| Hollow-handoff guardrail | Require ≥1 non-empty from {Decisions, Changes, Learnings} | Catches structurally complete but content-empty handoffs. (Codex review) |
| Conditional tail message | "Fix the errors and rewrite" only when errors present | "Fix errors" is misleading for warnings-only output. (Codex review) |
| Exit code | Always 0 | PostToolUse cannot block. Non-zero exits are non-blocking errors that only show in verbose mode. |

## Key Risks

| Risk | Mitigation |
|------|------------|
| Hook fires on every Write, adding latency | Path check is a string comparison — exits in <1ms for non-handoff files. No I/O for the fast path. |
| `additionalContext` might not be visible enough | If Claude ignores warnings, can switch to `decision: "block"` + `reason` (PostToolUse "block" prompts Claude with the reason). |
| False positives on legitimate short sessions | 400-line minimum is high. Sessions that are purely "fix a typo" may legitimately produce thin handoffs. But those sessions shouldn't use `/handoff` at all — the skill already says "skip if no meaningful decisions/progress." |
| Edit bypass | Write-only matcher means Claude could use Edit on a handoff without triggering validation. Non-blocking for v1: handoffs are write-once, the skill uses Write, corrections trigger full rewrites. Document as known limitation. (Codex review) |
| Rewrite-loop risk | If Claude writes a bad handoff, gets warned, rewrites, still fails — could loop. Mitigated by PostToolUse being non-blocking (additionalContext, not hard block) and the "Fix errors" instruction being conditional on errors existing. Monitor in practice. (Codex review) |
