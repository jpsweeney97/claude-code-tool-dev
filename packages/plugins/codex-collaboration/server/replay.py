"""Shared JSONL replay helper with corruption classification.

Single-pass replay with deferred trailing-truncation classification.
Per-store callbacks handle schema validation and record application.
See the persistence hardening design spec for the full contract.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Literal, TypeVar

T = TypeVar("T")


class SchemaViolation(Exception):
    """Raised by store callback when a parsed record has wrong/missing fields."""


class UnknownOperation(Exception):
    """Raised by store callback when a parsed record has an unrecognized op."""

    def __init__(self, op: str | None) -> None:
        self.op = op
        super().__init__(f"unknown operation: {op!r}")


@dataclass(frozen=True)
class ReplayDiagnostic:
    """Single diagnosed issue during JSONL replay."""

    line_number: int  # Physical file line number (1-based)
    label: Literal[
        "trailing_truncation",
        "mid_file_corruption",
        "schema_violation",
        "unknown_operation",
    ]
    detail: str


@dataclass(frozen=True)
class ReplayDiagnostics:
    """Collection of diagnostics from a single replay pass."""

    diagnostics: tuple[ReplayDiagnostic, ...]

    @property
    def has_warnings(self) -> bool:
        """True if any non-trailing-truncation diagnostics exist (includes errors)."""
        return any(d.label != "trailing_truncation" for d in self.diagnostics)

    @property
    def schema_violations(self) -> tuple[ReplayDiagnostic, ...]:
        """Return only diagnostics labelled schema_violation."""
        return tuple(d for d in self.diagnostics if d.label == "schema_violation")


def replay_jsonl(
    path: Path,
    apply: Callable[[dict[str, Any]], T | None],
) -> tuple[tuple[T, ...], ReplayDiagnostics]:
    """Replay a JSONL file with corruption classification and structured diagnostics.

    Single-pass with deferred trailing-truncation classification:
    - Lines where json.loads fails are classified after the loop based on
      whether valid JSON appeared after them (mid-file) or not (trailing).
    - Non-dict JSON is a schema_violation emitted before the callback.
    - SchemaViolation and UnknownOperation from the callback are caught and diagnosed.
    - All other callback exceptions propagate as programmer bugs.
    """
    if not path.exists():
        return ((), ReplayDiagnostics(()))

    results: list[T] = []
    immediate_diagnostics: list[ReplayDiagnostic] = []
    pending_parse_failures: list[int] = []
    last_valid_json_line: int = 0

    with path.open(encoding="utf-8") as f:
        for line_number, raw_line in enumerate(f, start=1):
            line = raw_line.strip()
            if not line:
                continue

            try:
                parsed = json.loads(line)
            except json.JSONDecodeError:
                pending_parse_failures.append(line_number)
                continue

            # JSON parsed successfully — record for trailing classification
            last_valid_json_line = line_number

            if type(parsed) is not dict:
                immediate_diagnostics.append(
                    ReplayDiagnostic(
                        line_number=line_number,
                        label="schema_violation",
                        detail=f"expected JSON object, got {type(parsed).__name__}",
                    )
                )
                continue

            try:
                result = apply(parsed)
            except SchemaViolation as exc:
                immediate_diagnostics.append(
                    ReplayDiagnostic(
                        line_number=line_number,
                        label="schema_violation",
                        detail=str(exc),
                    )
                )
                continue
            except UnknownOperation as exc:
                immediate_diagnostics.append(
                    ReplayDiagnostic(
                        line_number=line_number,
                        label="unknown_operation",
                        detail=str(exc),
                    )
                )
                continue

            if result is not None:
                results.append(result)

    # Deferred classification of parse failures
    classified: list[ReplayDiagnostic] = []
    for ln in pending_parse_failures:
        if last_valid_json_line == 0:
            label: Literal["trailing_truncation", "mid_file_corruption"] = (
                "mid_file_corruption"
            )
        elif ln > last_valid_json_line:
            label = "trailing_truncation"
        else:
            label = "mid_file_corruption"
        classified.append(
            ReplayDiagnostic(
                line_number=ln,
                label=label,
                detail="invalid JSON",
            )
        )

    all_diagnostics = sorted(
        immediate_diagnostics + classified,
        key=lambda d: d.line_number,
    )
    return (tuple(results), ReplayDiagnostics(tuple(all_diagnostics)))
