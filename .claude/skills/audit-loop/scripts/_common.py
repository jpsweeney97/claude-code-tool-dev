#!/usr/bin/env python3
"""
Shared utilities for audit-loop skill scripts.

Provides constants, data classes, and helper functions used across
state management, report generation, and validation scripts.
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# =============================================================================
# EXIT CODES
# =============================================================================

EXIT_SUCCESS: int = 0
EXIT_ERROR: int = 1
EXIT_ARGS: int = 2
EXIT_VALIDATION: int = 10
EXIT_NOT_FOUND: int = 11


# =============================================================================
# CONSTANTS
# =============================================================================

SCHEMA_VERSION: str = "1.0"

PHASES: list[str] = [
    "stakes_assessment",
    "definition",
    "execution",
    "verification",
    "triage",
    "design",
    "verify",
    "ship",
]

MAX_CYCLES: int = 10

CALIBRATION_LEVELS: dict[str, tuple[int, int]] = {
    "light": (4, 6),
    "medium": (7, 9),
    "deep": (10, 12),
}


# =============================================================================
# RESULT DATACLASS
# =============================================================================

@dataclass
class Result:
    """Standardized operation result."""

    ok: bool
    message: str
    data: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @classmethod
    def success(
        cls,
        message: str,
        data: dict[str, Any] | None = None,
        warnings: list[str] | None = None,
    ) -> Result:
        """Create a success result."""
        return cls(
            ok=True,
            message=message,
            data=data or {},
            errors=[],
            warnings=warnings or [],
        )

    @classmethod
    def failure(
        cls,
        message: str,
        errors: list[str] | None = None,
        data: dict[str, Any] | None = None,
    ) -> Result:
        """Create a failure result."""
        return cls(
            ok=False,
            message=message,
            data=data or {},
            errors=errors or [],
            warnings=[],
        )

    def to_json(self, indent: int = 2) -> str:
        """Serialize result to JSON string."""
        return json.dumps(
            {
                "ok": self.ok,
                "message": self.message,
                "data": self.data,
                "errors": self.errors,
                "warnings": self.warnings,
            },
            indent=indent,
        )


# =============================================================================
# FILE OPERATIONS
# =============================================================================

def atomic_write(path: Path, content: str) -> None:
    """
    Write content to file atomically using temp file + rename.

    Prevents data corruption if process is interrupted during write.

    Args:
        path: Target file path
        content: Content to write
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fd, temp_path = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        Path(temp_path).rename(path)
    except Exception:
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        raise


# =============================================================================
# PATH HELPERS
# =============================================================================

def get_state_path(artifact_path: Path) -> Path:
    """Get the .audit.json path for an artifact."""
    artifact_path = Path(artifact_path)
    return artifact_path.parent / f"{artifact_path.stem}.audit.json"


def get_archive_path(artifact_path: Path, date_str: str) -> Path:
    """Get the archived state path with date suffix."""
    artifact_path = Path(artifact_path)
    return artifact_path.parent / f"{artifact_path.stem}.audit.{date_str}.json"


def get_report_path(artifact_path: Path, date_str: str) -> Path:
    """Get the report path with date suffix."""
    artifact_path = Path(artifact_path)
    return artifact_path.parent / f"{artifact_path.stem}.audit-report.{date_str}.md"