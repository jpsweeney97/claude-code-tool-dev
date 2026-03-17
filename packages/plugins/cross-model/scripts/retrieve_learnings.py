"""Retrieve relevant learning entries for cross-model consultation briefings.

Reads docs/learnings/learnings.md, filters by tag/keyword relevance to a
query string, and returns formatted markdown for briefing injection.

Fail-soft: missing file, empty file, or parse errors return empty string.

Usage as library:
    from retrieve_learnings import retrieve_learnings
    markdown = retrieve_learnings("credential scan", max_entries=5)

Usage as script:
    python retrieve_learnings.py --query "credential scan" [--max-entries 5] [--path ...]
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# Header pattern: ### YYYY-MM-DD [tag1, tag2, ...]
_ENTRY_HEADER = re.compile(r"^### (\d{4}-\d{2}-\d{2})\s+\[([^\]]+)\]")

# promote-meta comment
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
            entries.append(LearningEntry(
                date=current_date,
                tags=current_tags,
                content=content,
                promoted=has_promote_meta,
            ))
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
    entries: list[LearningEntry], query: str,
) -> list[LearningEntry]:
    """Filter entries by tag or content keyword overlap with query.

    Scoring: each matching tag = 2 points, each matching query word in
    content = 1 point. Returns entries with score > 0, sorted by score
    descending.
    """
    query_lower = query.lower()
    query_words = set(query_lower.split())

    scored: list[tuple[int, LearningEntry]] = []
    for entry in entries:
        score = 0
        entry_tags_lower = {t.lower() for t in entry.tags}
        content_lower = entry.content.lower()

        # Tag matches
        for word in query_words:
            if word in entry_tags_lower:
                score += 2

        # Content keyword matches
        for word in query_words:
            if word in content_lower:
                score += 1

        if score > 0:
            scored.append((score, entry))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [entry for _, entry in scored]


def format_for_briefing(
    entries: list[LearningEntry], max_entries: int = 5,
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
    max_entries: int = 5,
    path: Path | None = None,
) -> str:
    """End-to-end: read file, filter, format. Fail-soft on errors."""
    if path is None:
        path = Path("docs/learnings/learnings.md")

    try:
        text = path.read_text()
    except (OSError, IOError):
        return ""

    entries = parse_learnings(text)
    if not entries:
        return ""

    filtered = filter_by_relevance(entries, query)
    return format_for_briefing(filtered, max_entries=max_entries)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Retrieve relevant learnings")
    parser.add_argument("--query", required=True, help="Consultation query")
    parser.add_argument("--max-entries", type=int, default=5)
    parser.add_argument("--path", type=Path, default=None)
    args = parser.parse_args()

    result = retrieve_learnings(args.query, args.max_entries, args.path)
    if result:
        print(result)
    else:
        sys.exit(0)
