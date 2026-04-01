"""Retrieve relevant learning entries for consultation briefings.

Fail-soft: missing file, empty file, or parse errors return empty string.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

_ENTRY_HEADER = re.compile(r"^### (\d{4}-\d{2}-\d{2})\s+\[([^\]]+)\]")
_PROMOTE_META = re.compile(r"<!--\s*promote-meta\s+")


@dataclass(frozen=True)
class LearningEntry:
    """A single parsed learning entry."""

    date: str
    tags: list[str] = field(default_factory=list)
    content: str = ""
    promoted: bool = False


def parse_learnings(text: str) -> list[LearningEntry]:
    """Parse learnings markdown into LearningEntry objects."""
    entries: list[LearningEntry] = []
    current_date: str | None = None
    current_tags: list[str] = []
    content_lines: list[str] = []
    has_promote_meta = False

    def _flush() -> None:
        nonlocal current_date, current_tags, content_lines, has_promote_meta
        if current_date is not None:
            content = "\n".join(content_lines).strip()
            entries.append(
                LearningEntry(
                    date=current_date,
                    tags=current_tags,
                    content=content,
                    promoted=has_promote_meta,
                )
            )
        current_date = None
        current_tags = []
        content_lines = []
        has_promote_meta = False

    for line in text.splitlines():
        match = _ENTRY_HEADER.match(line)
        if match:
            _flush()
            current_date = match.group(1)
            current_tags = [t.strip() for t in match.group(2).split(",")]
            continue

        if current_date is not None:
            if _PROMOTE_META.search(line):
                has_promote_meta = True
                continue
            content_lines.append(line)

    _flush()
    return entries


def filter_by_relevance(
    entries: list[LearningEntry],
    query: str,
) -> list[LearningEntry]:
    """Filter entries by tag or content keyword overlap with query."""
    query_lower = query.lower()
    query_words = set(query_lower.split())

    scored: list[tuple[int, LearningEntry]] = []
    for entry in entries:
        score = 0
        entry_tags_lower = {t.lower() for t in entry.tags}
        content_lower = entry.content.lower()

        for word in query_words:
            if word in entry_tags_lower:
                score += 2
        for word in query_words:
            if word in content_lower:
                score += 1

        if score > 0:
            scored.append((score, entry))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [entry for _, entry in scored]


def format_for_briefing(
    entries: list[LearningEntry],
    max_entries: int = 5,
) -> str:
    """Format selected entries as markdown for briefing injection."""
    if not entries:
        return ""

    selected = entries[:max_entries]
    lines: list[str] = []
    for entry in selected:
        lines.append(f"### {entry.date} [{', '.join(entry.tags)}]")
        lines.append("")
        lines.append(entry.content)
        lines.append("")

    lines.append(f"<!-- learnings-injected: {len(selected)} -->")
    return "\n".join(lines)


def retrieve_learnings(
    query: str,
    *,
    repo_root: Path,
    max_entries: int = 5,
) -> str:
    """End-to-end: read file, filter, format. Fail-soft on errors.

    repo_root is required — plugin cwd is CLAUDE_PLUGIN_ROOT, not the
    user's repository. Callers must pass the resolved repo root.
    """
    try:
        path = repo_root / "docs" / "learnings" / "learnings.md"
        text = path.read_text(encoding="utf-8")
        entries = parse_learnings(text)
        if not entries:
            return ""

        filtered = filter_by_relevance(entries, query)
        return format_for_briefing(filtered, max_entries=max_entries)
    except Exception:
        return ""
