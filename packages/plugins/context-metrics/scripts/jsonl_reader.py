"""JSONL tail-reader with fail-closed validation.

Reads JSONL transcripts backward from EOF to find the last valid
main-thread API response. Concurrent-write safe: partial lines are
discarded. Format drift safe: unknown records are rejected.

Design reference: Amendment 4 F2 (selector), Amendment 5 F3 (interaction model).
"""

from __future__ import annotations

import json
from pathlib import Path

CHUNK_SIZE = 8192


def is_main_thread_response(record: dict) -> bool:
    """4-condition positive-only selector (Amendment 4 F2).

    Conditions:
    1. type == "assistant"
    2. message.role == "assistant"
    3. message.usage present with input_tokens field
    4. Deduplicate by message.id (handled by caller via seen_ids set)
    """
    if record.get("type") != "assistant":
        return False
    message = record.get("message")
    if not isinstance(message, dict):
        return False
    if message.get("role") != "assistant":
        return False
    usage = message.get("usage")
    if not isinstance(usage, dict) or "input_tokens" not in usage:
        return False
    return True


def compute_occupancy(usage: dict) -> int:
    """Compute context window occupancy from usage data.

    occupancy = input_tokens + cache_read_input_tokens + cache_creation_input_tokens
    """
    return (
        usage.get("input_tokens", 0)
        + usage.get("cache_read_input_tokens", 0)
        + usage.get("cache_creation_input_tokens", 0)
    )


def tail_read_last_valid(jsonl_path: Path) -> dict | None:
    """Read JSONL backward from EOF, return first valid record.

    Fail-closed: malformed JSON, partial lines, and records failing
    the 4-condition selector are silently skipped. Returns None if
    no valid record exists (empty file, all records invalid).
    """
    try:
        with open(jsonl_path, "rb") as f:
            f.seek(0, 2)
            file_size = f.tell()
            if file_size == 0:
                return None

            seen_ids: set[str] = set()
            remaining = b""
            position = file_size

            while position > 0:
                read_size = min(CHUNK_SIZE, position)
                position -= read_size
                f.seek(position)
                chunk = f.read(read_size)
                data = chunk + remaining

                lines = data.split(b"\n")
                remaining = lines[0]

                for line in reversed(lines[1:]):
                    record = _try_parse_record(line, seen_ids)
                    if record is not None:
                        return record

            # Process leftover (first line of file)
            if remaining:
                record = _try_parse_record(remaining, seen_ids)
                if record is not None:
                    return record

    except OSError:
        return None

    return None


def _try_parse_record(line: bytes, seen_ids: set[str]) -> dict | None:
    """Try to parse and validate a single JSONL line. Returns None on any failure."""
    line = line.strip()
    if not line:
        return None
    try:
        record = json.loads(line)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None

    if not isinstance(record, dict):
        return None

    if not is_main_thread_response(record):
        return None

    # Condition 4: deduplicate by message.id
    msg_id = record.get("message", {}).get("id")
    if msg_id is not None:
        if msg_id in seen_ids:
            return None
        seen_ids.add(msg_id)

    return record
