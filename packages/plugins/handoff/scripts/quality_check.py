#!/usr/bin/env python3
"""PostToolUse hook: validates handoff/checkpoint quality after Write.

Reads PostToolUse JSON from stdin. If the written file is a handoff or
checkpoint (path under ~/.claude/handoffs/<project>/), validates:
- Required frontmatter fields present, non-blank, and valid
- Required sections present (13 for handoffs, 5 for checkpoints)
- Line count within range (400+ for handoffs, 20-80 for checkpoints)
- No empty sections
- At least 1 of {Decisions, Changes, Learnings} has substantive content
  (hollow-handoff guardrail, handoffs only)

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
    lines = content.splitlines()
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


def parse_sections(content: str) -> list[dict[str, str]]:
    """Extract ## sections with their content.

    Returns list of {"heading": str, "content": str} dicts.
    Only captures ## headings (not # or ### or deeper).
    Skips frontmatter block if present.
    Tracks code fences to avoid false headings inside code blocks.
    """
    lines = content.splitlines()

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
        # Track code fences (CommonMark: backtick or tilde, 0-3 spaces indent)
        stripped = line.lstrip(" ")
        indent = len(line) - len(stripped)
        if indent <= 3 and (
            stripped.startswith("```") or stripped.startswith("~~~")
        ):
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


# --- Validation ---


def validate_frontmatter(frontmatter: dict[str, str], doc_type: str) -> list[Issue]:
    """Validate frontmatter fields for the given document type.

    Checks: required fields present, checkpoint title starts with
    "Checkpoint:". Type allowlist is checked in validate(), not here.
    """
    issues: list[Issue] = []

    missing = [f for f in REQUIRED_FRONTMATTER_FIELDS if f not in frontmatter]
    if missing:
        issues.append(Issue(
            "error", f"Missing required frontmatter: {', '.join(missing)}"
        ))

    blank = [
        f for f in REQUIRED_FRONTMATTER_FIELDS
        if f in frontmatter and not frontmatter[f].strip()
    ]
    if blank:
        issues.append(Issue(
            "error", f"Blank required frontmatter: {', '.join(blank)}"
        ))

    if doc_type == "checkpoint" and "title" in frontmatter:
        title = frontmatter["title"]
        if not title.startswith("Checkpoint:"):
            issues.append(Issue(
                "warning",
                f"Checkpoint title should start with 'Checkpoint:', "
                f"got: '{title[:60]}'",
            ))

    return issues


def validate_sections(
    sections: list[dict[str, str]], doc_type: str
) -> list[Issue]:
    """Validate section presence and content for the given document type.

    Checks: all required sections present by name, no empty sections.
    """
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


def count_body_lines(content: str) -> int:
    """Count lines after the frontmatter closing ---.

    If no frontmatter, all lines are body lines.
    """
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        return len(lines)  # No frontmatter — all lines are body
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return len(lines) - (i + 1)
    return len(lines)  # No closing --- — all lines are body


def validate_line_count(content: str, doc_type: str) -> list[Issue]:
    """Validate body line count is within acceptable range.

    Body = lines after frontmatter closing ---.
    Handoff: minimum 400 body lines. Checkpoint: 20-80 body lines.
    """
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


def validate(content: str) -> list[Issue]:
    """Validate a handoff or checkpoint document. Returns list of issues.

    Parses frontmatter, validates type against allowlist (error on
    invalid), defaults to "handoff" for backwards compatibility
    (still reports missing 'type' as error), then runs all validators.
    """
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


# --- Hook integration ---


def is_handoff_path(file_path: str) -> bool:
    """Check if file is a handoff/checkpoint (not archived).

    Valid paths: ~/.claude/handoffs/<project>/<file>.md
    Invalid: archive paths, non-.md files, nested paths, other directories.
    """
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


def format_output(issues: list[Issue]) -> str:
    """Format issues as additionalContext message for Claude."""
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


def main() -> int:
    """PostToolUse hook entry point. Always returns 0."""
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError, ValueError) as exc:
        print(f"quality_check: stdin parse failed: {exc}", file=sys.stderr)
        return 0

    tool_input = hook_input.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        return 0

    file_path = tool_input.get("file_path", "")
    if not isinstance(file_path, str) or not file_path:
        return 0

    if not is_handoff_path(file_path):
        return 0

    content = tool_input.get("content", "")
    if not isinstance(content, str) or not content:
        return 0

    try:
        issues = validate(content)
    except Exception as exc:
        print(f"quality_check: validation failed: {exc}", file=sys.stderr)
        return 0

    if not issues:
        return 0

    try:
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": format_output(issues),
            }
        }
        json.dump(output, sys.stdout)
    except Exception as exc:
        print(
            f"quality_check: output serialization failed: {exc}",
            file=sys.stderr,
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
