"""Event logging for ecosystem-builder runs."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class Event:
    """A logged event."""

    type: str
    data: dict[str, Any]
    timestamp: str


class EventLogger:
    """Appends events to a JSONL log file."""

    def __init__(self, log_file: Path) -> None:
        self.log_file = log_file
        if not self.log_file.exists():
            self.log_file.touch()

    def log(self, event_type: str, data: dict[str, Any]) -> Event:
        """Log an event and return it."""
        event = Event(
            type=event_type,
            data=data,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        line = json.dumps({
            "type": event.type,
            "data": event.data,
            "timestamp": event.timestamp,
        })

        try:
            with self.log_file.open("a") as f:
                f.write(line + "\n")
        except OSError as e:
            raise RuntimeError(
                f"Failed to log event '{event_type}' to {self.log_file}: {e}"
            ) from e

        return event

    def read_all(self) -> list[Event]:
        """Read all events from the log.

        Skips malformed lines rather than failing entirely.
        """
        events = []
        try:
            content = self.log_file.read_text()
        except OSError as e:
            logging.warning(f"Failed to read log file {self.log_file}: {e}")
            return []
        except UnicodeDecodeError as e:
            logging.warning(f"Log file {self.log_file} contains invalid encoding: {e}")
            return []

        lines = content.strip().split("\n")
        for line_num, line in enumerate(lines, 1):
            if not line:
                continue
            try:
                data = json.loads(line)
                events.append(Event(
                    type=data["type"],
                    data=data["data"],
                    timestamp=data["timestamp"],
                ))
            except (json.JSONDecodeError, KeyError) as e:
                logging.warning(f"Skipping malformed log entry at line {line_num}: {e}")
                continue
        return events
