"""Ticket ID allocation and slug generation.

Format: T-YYYYMMDD-NN (date + 2-digit daily sequence, zero-padded).
Legacy IDs (T-NNN, T-[A-F], slugs) are preserved permanently.
"""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from scripts.ticket_parse import extract_fenced_yaml, parse_yaml_block

# ID pattern for v1.0 format.
_DATE_ID_RE = re.compile(r"^T-(\d{8})-(\d{2})$")


def allocate_id(tickets_dir: Path, today: date | None = None) -> str:
    """Allocate the next T-YYYYMMDD-NN ID for the given day.

    Scans existing tickets in tickets_dir for same-day IDs and returns
    the next available sequence number. If tickets_dir doesn't exist,
    returns the first ID for the day.
    """
    if today is None:
        today = date.today()

    date_str = today.strftime("%Y%m%d")
    prefix = f"T-{date_str}-"

    max_seq = 0
    if tickets_dir.is_dir():
        for ticket_file in tickets_dir.glob("*.md"):
            try:
                text = ticket_file.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            yaml_text = extract_fenced_yaml(text)
            if yaml_text is None:
                continue
            data = parse_yaml_block(yaml_text)
            if data is None:
                continue
            ticket_id = data.get("id", "")
            if isinstance(ticket_id, str) and ticket_id.startswith(prefix):
                m = _DATE_ID_RE.match(ticket_id)
                if m and m.group(1) == date_str:
                    seq = int(m.group(2))
                    max_seq = max(max_seq, seq)

    return f"{prefix}{max_seq + 1:02d}"


def generate_slug(title: str) -> str:
    """Generate a URL-safe slug from a ticket title.

    Rules: first 6 words, kebab-case, [a-z0-9-] only, max 60 chars.
    """
    if not title.strip():
        return "untitled"

    # Lowercase and keep only alphanumeric, spaces, hyphens.
    slug = title.lower()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    # Collapse whitespace to single space.
    slug = re.sub(r"\s+", " ", slug).strip()
    # Take first 6 words.
    words = slug.split()[:6]
    slug = "-".join(words)
    # Collapse multiple hyphens.
    slug = re.sub(r"-+", "-", slug)
    # Truncate to 60 chars (don't break mid-word).
    if len(slug) > 60:
        slug = slug[:60].rsplit("-", 1)[0]
    return slug or "untitled"


def build_filename(ticket_id: str, title: str) -> str:
    """Build a ticket filename from ID and title.

    Format: YYYY-MM-DD-<slug>.md (date from ID, slug from title).
    """
    m = _DATE_ID_RE.match(ticket_id)
    if m:
        raw_date = m.group(1)
        date_str = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:8]}"
    else:
        date_str = date.today().strftime("%Y-%m-%d")

    slug = generate_slug(title)
    return f"{date_str}-{slug}.md"


def is_legacy_id(ticket_id: str) -> bool:
    """Check if an ID is a legacy format (not v1.0 T-YYYYMMDD-NN)."""
    return not bool(_DATE_ID_RE.match(ticket_id))


def parse_id_date(ticket_id: str) -> date | None:
    """Extract the date from a v1.0 ID. Returns None for legacy IDs."""
    m = _DATE_ID_RE.match(ticket_id)
    if not m:
        return None
    raw = m.group(1)
    return date(int(raw[:4]), int(raw[4:6]), int(raw[6:8]))
