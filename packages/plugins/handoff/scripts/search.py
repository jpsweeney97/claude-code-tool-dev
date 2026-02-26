#!/usr/bin/env python3
"""search.py - Search handoff history for decisions, learnings, and context.

Parses handoff markdown files into section trees, searches within sections,
and outputs structured JSON results.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
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


def get_project_name() -> tuple[str, str]:
    """Get project name from git root directory, falling back to current directory name.

    Returns:
        (project_name, source) where source is "git" or "cwd".
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return Path(result.stdout.strip()).name, "git"
    except subprocess.TimeoutExpired:
        pass
    except FileNotFoundError:
        pass
    except OSError:
        pass
    return Path.cwd().name, "cwd"


def get_handoffs_dir() -> Path:
    """Get handoffs directory: ~/.claude/handoffs/<project>/"""
    name, _ = get_project_name()
    return Path.home() / ".claude" / "handoffs" / name


def search_handoffs(
    handoffs_dir: Path,
    query: str,
    *,
    regex: bool = False,
    skipped: list[dict] | None = None,
) -> list[dict]:
    """Search handoff files for matching sections.

    Args:
        handoffs_dir: Directory containing handoff .md files (with optional .archive/ subdirectory)
        query: Search string or regex pattern
        regex: If True, treat query as regex. If False, literal case-insensitive match.

    Returns:
        List of result dicts sorted by date descending. Each dict contains:
        file, title, date, type, archived, section_heading, section_content
    """
    if not handoffs_dir.exists():
        return []

    # Compile search pattern
    flags = 0 if regex else re.IGNORECASE
    if not regex:
        query = re.escape(query)
    pattern = re.compile(query, flags)

    results: list[dict] = []

    # Collect .md files from top-level and .archive/
    md_files: list[tuple[Path, bool]] = []
    for f in handoffs_dir.glob("*.md"):
        md_files.append((f, False))
    archive_dir = handoffs_dir / ".archive"
    if archive_dir.exists():
        for f in archive_dir.glob("*.md"):
            md_files.append((f, True))

    for path, archived in md_files:
        try:
            handoff = parse_handoff(path)
        except (OSError, UnicodeDecodeError) as e:
            if skipped is not None:
                skipped.append({"file": path.name, "reason": str(e)})
            continue  # Skip unreadable or malformed files

        for section in handoff.sections:
            search_text = f"{section.heading}\n{section.content}"
            if pattern.search(search_text):
                results.append({
                    "file": path.name,
                    "title": handoff.frontmatter.get("title", path.stem),
                    "date": handoff.frontmatter.get("date", ""),
                    "type": handoff.frontmatter.get("type", "handoff"),
                    "archived": archived,
                    "section_heading": section.heading,
                    "section_content": section.content,
                })

    # Sort by date descending
    results.sort(key=lambda r: r["date"], reverse=True)
    return results


def main(argv: list[str] | None = None) -> str:
    """CLI entry point. Returns JSON string.

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:] if None).

    Returns:
        JSON string with search results.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Search handoff history")
    parser.add_argument("query", help="Search query (text or regex)")
    parser.add_argument("--regex", action="store_true", help="Treat query as regex")
    args = parser.parse_args(argv)
    _, project_source = get_project_name()

    handoffs_dir = get_handoffs_dir()

    if not handoffs_dir.exists():
        return json.dumps({
            "query": args.query,
            "total_matches": 0,
            "results": [],
            "skipped": [],
            "project_source": project_source,
            "error": f"Handoffs directory not found: {handoffs_dir}",
        })

    skipped_files: list[dict] = []
    try:
        results = search_handoffs(handoffs_dir, args.query, regex=args.regex, skipped=skipped_files)
    except re.error as e:
        return json.dumps({
            "query": args.query,
            "total_matches": 0,
            "results": [],
            "skipped": skipped_files,
            "project_source": project_source,
            "error": f"Invalid regex: {e}",
        })

    return json.dumps({
        "query": args.query,
        "total_matches": len(results),
        "results": results,
        "skipped": skipped_files,
        "project_source": project_source,
        "error": None,
    })


if __name__ == "__main__":
    print(main())
    sys.exit(0)
