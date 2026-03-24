#!/usr/bin/env python3
"""Graduation report validator.

Validates consistency between graduation.json, annotations.jsonl, and
per-dialogue diagnostics files. Exit 0 = all checks pass, exit 1 = failure.

Usage:
    python -m scripts.validate_graduation \
        --graduation <path> \
        --annotations <path> \
        --diagnostics-dir <path>
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_STATUS_VALUES: set[str] = {"approved", "rejected"}
TOLERANCE: float = 1e-6

# Kill-criteria thresholds (approved status only)
MIN_YIELD: float = 0.40
MAX_LATENCY_MS: float = 500.0
MAX_FALSE_POSITIVE_RATE: float = 0.10
MIN_SAMPLE_SIZE: int = 100
ESCALATION_RATE_THRESHOLD: float = 0.07
ESCALATED_SAMPLE_SIZE: int = 200


@dataclass
class ValidationResult:
    """Result of graduation report validation."""

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _close(a: float, b: float) -> bool:
    """Check if two floats are within relative tolerance."""
    return math.isclose(a, b, rel_tol=TOLERANCE, abs_tol=TOLERANCE)


def _load_graduation(path: Path) -> dict:
    """Load and return graduation.json contents."""
    with path.open() as f:
        return json.load(f)


def _load_annotations(path: Path) -> list[dict]:
    """Load and parse annotations.jsonl. Raises on malformed lines."""
    entries: list[dict] = []
    with path.open() as f:
        for i, line in enumerate(f, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                entries.append(json.loads(stripped))
            except json.JSONDecodeError as e:
                msg = f"annotations parse failure at line {i}: {e}"
                raise ValueError(msg) from e
    return entries


def _load_diagnostics(diag_dir: Path) -> list[dict]:
    """Load all JSON files from the diagnostics directory."""
    files = sorted(diag_dir.glob("*.json"))
    result: list[dict] = []
    for f in files:
        with f.open() as fh:
            result.append(json.load(fh))
    return result


# ---------------------------------------------------------------------------
# Validation checks
# ---------------------------------------------------------------------------


def validate_detailed(
    graduation: dict,
    annotations: list[dict],
    diagnostics: list[dict],
    diag_file_count: int,
) -> ValidationResult:
    """Run all validation checks. Returns ValidationResult with errors and warnings."""
    errors: list[str] = []
    warnings: list[str] = []
    status = graduation.get("status", "")

    # --- Status validation ---
    if status not in VALID_STATUS_VALUES:
        errors.append(f"unknown status: {status!r}; valid values: {VALID_STATUS_VALUES}")

    # --- Rejected status requires non-empty notes ---
    if status == "rejected":
        notes = graduation.get("notes", "")
        if not notes or not notes.strip():
            errors.append(
                "notes field required and must be non-empty when status is rejected"
            )

    # --- Annotation count ---
    declared_count = graduation.get("labeled_topics", 0)
    actual_count = len(annotations)
    if declared_count != actual_count:
        errors.append(
            f"labeled_topics: expected {declared_count}, got {actual_count}"
        )

    # --- Sample size minimum (approved only) ---
    if status == "approved" and declared_count < MIN_SAMPLE_SIZE:
        errors.append(
            f"labeled_topics: {declared_count} is below minimum "
            f"{MIN_SAMPLE_SIZE} required for false_positive_rate evaluation"
        )

    # --- False-positive rate ---
    if actual_count > 0:
        fp_count = sum(1 for a in annotations if a.get("label") == "false_positive")
        computed_rate = fp_count / actual_count
        declared_rate = graduation.get("false_positive_rate", 0.0)
        if not _close(computed_rate, declared_rate):
            errors.append(
                f"false_positive_rate: declared {declared_rate}, "
                f"computed {computed_rate:.6f} from annotations"
            )

        # --- Sample-size escalation (approved only) ---
        if status == "approved" and computed_rate >= ESCALATION_RATE_THRESHOLD:
            if actual_count < ESCALATED_SAMPLE_SIZE:
                errors.append(
                    f"insufficient-power warning: preliminary false-positive "
                    f"rate >= 7% requires labeled_topics >= "
                    f"{ESCALATED_SAMPLE_SIZE}; got {actual_count}"
                )

    # --- Diagnostics file count ---
    declared_dialogues = graduation.get("evaluated_dialogues", 0)
    if declared_dialogues != diag_file_count:
        errors.append(
            f"evaluated_dialogues: expected {declared_dialogues}, "
            f"got {diag_file_count}"
        )

    # --- Yield metrics (global ratio) ---
    effective_yield_valid = False
    if diagnostics:
        total_prepared = sum(d.get("packets_prepared", 0) for d in diagnostics)
        # Use packets_surviving_precedence if available, else packets_injected
        total_surviving = sum(
            d.get("packets_surviving_precedence", d.get("packets_injected", 0))
            for d in diagnostics
        )
        if total_prepared > 0:
            computed_yield = total_surviving / total_prepared
            declared_yield = graduation.get("effective_prepare_yield", 0.0)
            if not _close(computed_yield, declared_yield):
                errors.append(
                    f"effective_prepare_yield: declared {declared_yield}, "
                    f"computed {computed_yield:.6f} (global ratio)"
                )
            else:
                effective_yield_valid = True

        # --- Latency metrics (mean-of-all-turns) ---
        all_latencies: list[float] = []
        for d in diagnostics:
            all_latencies.extend(d.get("per_turn_latency_ms", []))
        if all_latencies:
            computed_latency = sum(all_latencies) / len(all_latencies)
            declared_latency = graduation.get("avg_latency_ms", 0.0)
            if not _close(computed_latency, declared_latency):
                errors.append(
                    f"avg_latency_ms: declared {declared_latency}, "
                    f"computed {computed_latency:.6f} (mean-of-all-turns)"
                )

    # --- Kill-criteria thresholds (approved only) ---
    if status == "approved":
        declared_yield = graduation.get("effective_prepare_yield", 0.0)
        if declared_yield < MIN_YIELD:
            errors.append(
                f"effective_prepare_yield {declared_yield} is below "
                f"minimum threshold {MIN_YIELD} for approved status"
            )

        declared_latency = graduation.get("avg_latency_ms", 0.0)
        if declared_latency > MAX_LATENCY_MS:
            errors.append(
                f"avg_latency_ms {declared_latency} is above "
                f"maximum threshold {MAX_LATENCY_MS} for approved status"
            )

        declared_fp_rate = graduation.get("false_positive_rate", 0.0)
        if declared_fp_rate > MAX_FALSE_POSITIVE_RATE:
            errors.append(
                f"false_positive_rate {declared_fp_rate} is above "
                f"maximum threshold {MAX_FALSE_POSITIVE_RATE} for approved status"
            )

        # shadow_adjusted_yield threshold (when present)
        shadow_yield = graduation.get("shadow_adjusted_yield")
        if shadow_yield is not None and shadow_yield < MIN_YIELD:
            errors.append(
                f"shadow_adjusted_yield {shadow_yield} is below "
                f"minimum threshold {MIN_YIELD} for approved status"
            )

        # Freshness guardrail warning: shadow_adjusted_yield absent
        if shadow_yield is None and effective_yield_valid:
            warnings.append(
                "warning: shadow_adjusted_yield absent; treating omission as "
                "freshness guardrail activation and using "
                "effective_prepare_yield as the gating metric"
            )

    return ValidationResult(errors=errors, warnings=warnings)


def validate(
    graduation: dict,
    annotations: list[dict],
    diagnostics: list[dict],
    diag_file_count: int,
) -> list[str]:
    """Run all validation checks. Returns list of error strings (empty = pass).

    Backward-compatible wrapper around validate_detailed().
    """
    return validate_detailed(
        graduation, annotations, diagnostics, diag_file_count,
    ).errors


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    """Entry point for the graduation validator CLI."""
    parser = argparse.ArgumentParser(
        description="Validate graduation report consistency."
    )
    parser.add_argument(
        "--graduation", required=True, type=Path,
        help="Path to graduation.json",
    )
    parser.add_argument(
        "--annotations", required=True, type=Path,
        help="Path to annotations.jsonl",
    )
    parser.add_argument(
        "--diagnostics-dir", required=True, type=Path,
        help="Path to diagnostics directory",
    )
    args = parser.parse_args()

    # --- File existence checks ---
    if not args.graduation.exists():
        print(f"graduation file not found: {args.graduation}", file=sys.stderr)
        sys.exit(1)

    if not args.annotations.exists():
        print(f"annotations file not found: {args.annotations}", file=sys.stderr)
        sys.exit(1)

    if not args.diagnostics_dir.exists() or not args.diagnostics_dir.is_dir():
        print(
            f"diagnostics directory not found: {args.diagnostics_dir}",
            file=sys.stderr,
        )
        sys.exit(1)

    # --- Load data ---
    graduation = _load_graduation(args.graduation)

    try:
        annotations = _load_annotations(args.annotations)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

    diagnostics = _load_diagnostics(args.diagnostics_dir)
    diag_file_count = len(list(args.diagnostics_dir.glob("*.json")))

    # --- Validate ---
    result = validate_detailed(graduation, annotations, diagnostics, diag_file_count)

    for warning in result.warnings:
        print(warning, file=sys.stderr)

    if result.errors:
        for err in result.errors:
            print(err, file=sys.stderr)
        sys.exit(1)

    print("OK")


if __name__ == "__main__":
    main()
