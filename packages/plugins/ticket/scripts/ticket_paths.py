"""Shared path validation helpers for ticket scripts."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any


def resolve_tickets_dir(
    raw_tickets_dir: Any,
    *,
    project_root: Path,
) -> tuple[Path | None, str | None]:
    """Resolve and validate tickets_dir against project root."""
    value = "docs/tickets" if raw_tickets_dir is None else raw_tickets_dir
    if not isinstance(value, (str, os.PathLike)):
        return (
            None,
            f"tickets_dir validation failed: expected string path. Got: {value!r:.100}",
        )

    try:
        root = project_root.resolve()
        candidate = Path(value)
        resolved = candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()
    except OSError as exc:
        return (
            None,
            f"tickets_dir resolution failed: {exc}. Got: {str(value)!r:.100}",
        )

    try:
        resolved.relative_to(root)
    except ValueError:
        return (
            None,
            f"tickets_dir validation failed: path escapes project root {str(root)!r}. Got: {str(value)!r:.100}",
        )
    return resolved, None
