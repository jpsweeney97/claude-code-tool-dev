"""Ticket creation logic for /defer skill.

Deterministic: allocates IDs, renders markdown, writes files.
LLM extraction happens in the SKILL.md — this script receives candidates.
"""
from __future__ import annotations

import json
import re
import sys
import warnings
from pathlib import Path
from typing import Any

try:
    from scripts.ticket_parsing import parse_ticket
    from scripts.provenance import render_defer_meta
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from scripts.ticket_parsing import parse_ticket  # type: ignore[no-redef]
    from scripts.provenance import render_defer_meta  # type: ignore[no-redef]

_DATE_ID_RE = re.compile(r"^T-(\d{8})-(\d{2,})$")


def allocate_id(date_str: str, tickets_dir: Path) -> str:
    """Allocate the next ticket ID for a given date.

    Scans all .md files in tickets_dir, parses their YAML to extract id fields,
    finds the highest sequence number for the date, and returns the next one.
    """
    date_compact = date_str.replace("-", "")
    max_seq = 0

    if tickets_dir.exists():
        for path in sorted(tickets_dir.glob("*.md")):  # P2-10: deterministic order
            ticket = parse_ticket(path)
            if ticket is None:
                warnings.warn(f"Skipping malformed ticket: {path}", stacklevel=2)  # P2-11
                continue
            tid = ticket.frontmatter.get("id", "")
            m = _DATE_ID_RE.match(str(tid))
            if m and m.group(1) == date_compact:
                max_seq = max(max_seq, int(m.group(2)))

    return f"T-{date_compact}-{max_seq + 1:02d}"


def filename_slug(ticket_id: str, summary: str) -> str:
    """Generate a filename from ticket ID and summary.

    Format: YYYY-MM-DD-T-YYYYMMDD-NN-slug.md
    Slug: lowercase, alphanumeric + hyphens, max 50 chars.
    """
    m = _DATE_ID_RE.match(ticket_id)
    date_part = f"{m.group(1)[:4]}-{m.group(1)[4:6]}-{m.group(1)[6:8]}" if m else "unknown"

    slug = re.sub(r"[^a-z0-9\s-]", "", summary.lower())
    slug = re.sub(r"[\s_]+", "-", slug).strip("-")
    slug = re.sub(r"-+", "-", slug)[:50].rstrip("-")

    return f"{date_part}-{ticket_id}-{slug}.md"


_VALID_PRIORITIES = {"low", "medium", "high", "critical"}  # P1-9
_VALID_EFFORTS = {"XS", "S", "M", "L", "XL"}  # P1-9


def render_ticket(candidate: dict[str, Any]) -> str:
    """Render a ticket markdown file from a candidate dict."""
    tid = candidate["id"]
    date = candidate["date"]
    summary = candidate["summary"]
    problem = candidate["problem"]
    source_text = candidate["source_text"]
    proposed = candidate["proposed_approach"]
    criteria = candidate["acceptance_criteria"]
    priority = candidate.get("priority", "medium")
    source_type = candidate.get("source_type", "ad-hoc")
    source_ref = candidate.get("source_ref", "")
    branch = candidate.get("branch", "")
    session_id = candidate.get("session_id", "")
    effort = candidate.get("effort", "S")
    files = candidate.get("files", [])

    # P1-9 fix: validate enum values before rendering
    if priority not in _VALID_PRIORITIES:
        priority = "medium"
    if effort not in _VALID_EFFORTS:
        effort = "S"

    _YAML_IMPLICIT_SCALARS = frozenset({
        "yes", "no", "on", "off", "true", "false", "null", "~",
        "Yes", "No", "On", "Off", "True", "False", "Null",
        "YES", "NO", "ON", "OFF", "TRUE", "FALSE", "NULL",
    })
    _YAML_NUMERIC_RE = re.compile(r'^[-+]?(?:\d|\.(?:inf|nan))', re.IGNORECASE)

    def _quote(val: str) -> str:
        """Quote a YAML string value if it contains YAML-significant characters.

        Handles colons, quotes, braces, backslashes, newlines, YAML
        implicit scalars (yes/no/true/false/null/~ which safe_load coerces),
        and numeric implicit scalars (octals, .inf, .nan which coerce to int/float).
        Values without special characters pass through unquoted.
        """
        if not val:
            return '""'
        if val in _YAML_IMPLICIT_SCALARS or _YAML_NUMERIC_RE.match(val) or any(c in val for c in (':', '#', '{', '}', '[', ']', ',', '&', '*', '?', '|', '-', '<', '>', '=', '!', '%', '@', '`', '"', "'", '\\', '\n', '\r', '\t', '\x85', '\u2028', '\u2029')):
            escaped = val.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t').replace('\x85', '\\N').replace('\u2028', '\\L').replace('\u2029', '\\P')
            return f'"{escaped}"'
        return val

    # Build YAML frontmatter
    yaml_lines = [
        f"id: {tid}",
        f'date: "{date}"',
        "status: deferred",
        f"priority: {_quote(priority)}",  # P1-9 fix: quote to prevent invalid YAML
        f"source_type: {_quote(source_type)}",
        f"source_ref: {_quote(source_ref)}",
        f"branch: {_quote(branch)}",
        "blocked_by: []",
        "blocks: []",
        f"effort: {_quote(effort)}",  # P1-9 fix: quote to prevent invalid YAML
    ]

    if files:
        yaml_lines.append("files:")
        for f in files:
            yaml_lines.append(f"  - {_quote(f)}")

    yaml_lines.append("provenance:")
    # P1-7 fix: write null instead of empty string for session_id
    if session_id:
        yaml_lines.append(f'  source_session: "{session_id}"')
    else:
        yaml_lines.append("  source_session: ~")
    yaml_lines.append(f"  source_type: {_quote(source_type)}")
    yaml_lines.append("  created_by: defer-skill")

    yaml_block = "\n".join(yaml_lines)

    # Build body sections
    criteria_lines = "\n".join(f"- [ ] {c}" for c in criteria)
    meta_comment = render_defer_meta(session_id, source_type, source_ref)

    # P2-9 fix: omit empty Branch:/Session: lines instead of rendering empty backticks
    source_suffix_parts: list[str] = []
    if branch:
        source_suffix_parts.append(f"Branch: `{branch}`.")
    if session_id:
        source_suffix_parts.append(f"Session: `{session_id}`.")
    source_suffix = " ".join(source_suffix_parts)

    return f"""\
# {tid}: {summary}

```yaml
{yaml_block}
```

## Problem

{problem}

## Source

{source_text}
{source_suffix}

## Proposed Approach

{proposed}

## Acceptance Criteria

{criteria_lines}

{meta_comment}
"""


def write_ticket(candidate: dict[str, Any], tickets_dir: Path) -> Path:
    """Write a rendered ticket to disk. Returns the path of the created file."""
    content = render_ticket(candidate)
    slug = filename_slug(candidate["id"], candidate["summary"])
    path = tickets_dir / slug
    tickets_dir.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Reads candidate JSON from stdin, writes ticket files."""
    import argparse

    parser = argparse.ArgumentParser(description="Create deferred work tickets")
    parser.add_argument("--tickets-dir", type=Path, default=Path("docs/tickets"))
    parser.add_argument("--date", required=True, help="Date in YYYY-MM-DD format")
    args = parser.parse_args(argv)

    candidates = json.load(sys.stdin)
    if not isinstance(candidates, list):
        candidates = [candidates]

    created: list[dict[str, str]] = []
    errors: list[dict[str, str]] = []
    for cand in candidates:
        try:
            tid = allocate_id(args.date, args.tickets_dir)
            cand["id"] = tid
            cand["date"] = args.date
            path = write_ticket(cand, args.tickets_dir)
            created.append({"id": tid, "path": str(path)})
        except Exception as exc:
            errors.append({"summary": cand.get("summary", "unknown"), "error": str(exc)})

    if errors and created:
        json.dump({"status": "partial_success", "created": created, "errors": errors}, sys.stdout)
    elif errors:
        json.dump({"status": "error", "created": [], "errors": errors}, sys.stdout)
    else:
        json.dump({"status": "ok", "created": created}, sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
