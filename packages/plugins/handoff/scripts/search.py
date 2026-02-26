#!/usr/bin/env python3
"""search.py - Search handoff history for decisions, learnings, and context.

Parses handoff markdown files into section trees, searches within sections,
and outputs structured JSON results.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Section:
    heading: str
    level: int
    content: str
    line_start: int


@dataclass
class HandoffFile:
    path: str
    frontmatter: dict[str, str]
    sections: list[Section]


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Extract YAML frontmatter from markdown text.

    Returns (frontmatter_dict, remaining_text). Handles simple key: value
    pairs and quoted strings. Does not depend on PyYAML.

    Multiline YAML values (e.g., files: lists) are silently skipped —
    only single-line key: value pairs are extracted. This is sufficient
    for search (which uses title, date, type).
    """
    if not text.startswith("---"):
        return {}, text

    # Find closing ---
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text

    fm_text = text[4:end]  # Skip opening ---\n
    remaining = text[end + 4:]  # Skip closing ---\n

    frontmatter: dict[str, str] = {}
    for line in fm_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.match(r'^(\w[\w-]*)\s*:\s*(.+)$', line)
        if match:
            key = match.group(1)
            value = match.group(2).strip()
            # Strip surrounding quotes
            if (value.startswith('"') and value.endswith('"')) or (
                value.startswith("'") and value.endswith("'")
            ):
                value = value[1:-1]
            frontmatter[key] = value

    return frontmatter, remaining


def parse_sections(text: str) -> list[Section]:
    """Split markdown text into ## sections.

    Each section includes everything from its ## heading until the next
    ## heading or EOF. ### subsections are included within their parent.
    Code-fenced regions are tracked to avoid treating ## lines inside
    fences as section boundaries. The heading line itself is NOT included
    in section.content to avoid duplication when displaying heading + content.
    """
    sections: list[Section] = []
    lines = text.splitlines(keepends=True)
    current_heading = ""
    current_lines: list[str] = []
    current_start = 0
    inside_fence = False

    for i, line in enumerate(lines):
        stripped = line.rstrip()
        if stripped.startswith("```"):
            inside_fence = not inside_fence
        if not inside_fence and line.startswith("## "):
            # Save previous section if any
            if current_heading:
                content = "".join(current_lines).strip()
                sections.append(Section(
                    heading=current_heading,
                    level=2,
                    content=content,
                    line_start=current_start,
                ))
            current_heading = line.strip()
            current_lines = []
            current_start = i + 1  # 1-indexed
        elif current_heading:
            current_lines.append(line)

    # Save last section
    if current_heading:
        content = "".join(current_lines).strip()
        sections.append(Section(
            heading=current_heading,
            level=2,
            content=content,
            line_start=current_start,
        ))

    return sections


def parse_handoff(path: Path) -> HandoffFile:
    """Parse a handoff markdown file into structured data."""
    text = path.read_text(encoding="utf-8")
    frontmatter, body = parse_frontmatter(text)
    sections = parse_sections(body)
    return HandoffFile(path=str(path), frontmatter=frontmatter, sections=sections)
