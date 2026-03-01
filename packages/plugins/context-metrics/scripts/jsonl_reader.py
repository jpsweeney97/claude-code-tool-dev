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


def _int_field(usage: dict, key: str) -> int:
    """Extract an integer field from usage, returning 0 for non-int values."""
    val = usage.get(key, 0)
    return val if isinstance(val, int) else 0


def compute_occupancy(usage: dict) -> int:
    """Compute context window occupancy from usage data.

    occupancy = input_tokens + cache_read_input_tokens + cache_creation_input_tokens

    Non-integer values are treated as 0 (fail-closed against format drift).
    """
    return (
        _int_field(usage, "input_tokens")
        + _int_field(usage, "cache_read_input_tokens")
        + _int_field(usage, "cache_creation_input_tokens")
    )


def count_messages(jsonl_path: Path) -> int:
    """Count user and assistant messages in a JSONL transcript.

    Forward scan — reads the entire file. Only counts records with
    type "user" or "assistant". Malformed lines are skipped.
    Returns 0 on any file error.
    """
    count = 0
    try:
        with open(jsonl_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    continue
                if isinstance(record, dict) and record.get("type") in ("user", "assistant"):
                    count += 1
    except OSError:
        return 0
    return count


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
