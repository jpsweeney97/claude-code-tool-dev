"""Tests for graduation report validator.

17 test cases from delivery.md's test table. Each test creates temp fixture
files (graduation.json, annotations.jsonl, diagnostics directory) and invokes
the validator via subprocess.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

_PKG_ROOT = Path(__file__).resolve().parent.parent


def _run_validator(
    graduation: Path,
    annotations: Path,
    diagnostics_dir: Path,
) -> subprocess.CompletedProcess[str]:
    """Run validate_graduation.py as a subprocess."""
    return subprocess.run(
        [
            "uv", "run", "python", "-m", "scripts.validate_graduation",
            "--graduation", str(graduation),
            "--annotations", str(annotations),
            "--diagnostics-dir", str(diagnostics_dir),
        ],
        capture_output=True,
        text=True,
        cwd=str(_PKG_ROOT),
    )


def _write_graduation(path: Path, data: dict) -> Path:
    """Write a graduation.json file."""
    path.write_text(json.dumps(data))
    return path


def _write_annotations(path: Path, entries: list[dict]) -> Path:
    """Write an annotations.jsonl file."""
    lines = [json.dumps(e) for e in entries]
    path.write_text("\n".join(lines) + "\n" if lines else "")
    return path


def _make_annotation(
    label: str = "true_positive",
    topic_key: str = "hooks.pre_tool_use",
) -> dict:
    """Create a single annotation entry."""
    return {"topic_key": topic_key, "label": label}


def _write_diagnostics_file(path: Path, data: dict) -> Path:
    """Write a single diagnostics JSON file."""
    path.write_text(json.dumps(data))
    return path


def _make_diagnostics(
    *,
    status: str = "shadow",
    phase: str = "full",
    packets_prepared: int = 5,
    packets_injected: int = 3,
    packets_surviving_precedence: int | None = None,
    per_turn_latency_ms: list[int] | None = None,
) -> dict:
    """Create a diagnostics record dict."""
    d: dict = {
        "status": status,
        "phase": phase,
        "packets_prepared": packets_prepared,
        "packets_injected": packets_injected,
        "per_turn_latency_ms": per_turn_latency_ms or [100, 200, 300],
    }
    if packets_surviving_precedence is not None:
        d["packets_surviving_precedence"] = packets_surviving_precedence
    return d


def _base_graduation(**overrides: object) -> dict:
    """Create a valid base graduation.json with sensible defaults."""
    base: dict = {
        "status": "approved",
        "labeled_topics": 150,
        "false_positive_rate": 0.05,
        "evaluated_dialogues": 1,
        "effective_prepare_yield": 0.6,
        "avg_latency_ms": 200.0,
        "shadow_adjusted_yield": 0.6,
        "notes": "Approved after review",
    }
    base.update(overrides)
    return base


def _setup_valid(
    tmp_path: Path,
    *,
    grad_overrides: dict | None = None,
    annotation_count: int = 150,
    fp_count: int | None = None,
    diag_files: list[dict] | None = None,
) -> tuple[Path, Path, Path]:
    """Set up a consistent set of fixture files.

    Creates graduation.json, annotations.jsonl, and diagnostics dir with
    values that pass all checks by default. Override specific parts as needed.
    """
    # Annotations
    if fp_count is None:
        fp_count = round(0.05 * annotation_count)
    tp_count = annotation_count - fp_count
    annotations = [_make_annotation(label="true_positive")] * tp_count + [
        _make_annotation(label="false_positive")
    ] * fp_count
    ann_path = _write_annotations(tmp_path / "annotations.jsonl", annotations)

    # Diagnostics
    diag_dir = tmp_path / "diagnostics"
    diag_dir.mkdir()
    if diag_files is None:
        # Single file that's consistent with base graduation defaults
        diag_files = [
            _make_diagnostics(
                packets_prepared=5,
                packets_injected=3,
                packets_surviving_precedence=3,
                per_turn_latency_ms=[200],
            )
        ]
    for i, diag in enumerate(diag_files):
        _write_diagnostics_file(diag_dir / f"dialogue_{i}.json", diag)

    # Graduation
    grad_data = _base_graduation(
        evaluated_dialogues=len(diag_files),
        labeled_topics=annotation_count,
        false_positive_rate=fp_count / annotation_count if annotation_count > 0 else 0.0,
    )
    if grad_overrides:
        grad_data.update(grad_overrides)
    grad_path = _write_graduation(tmp_path / "graduation.json", grad_data)

    return grad_path, ann_path, diag_dir


# ---------------------------------------------------------------------------
# 1. Annotations count matches labeled_topics
# ---------------------------------------------------------------------------


class TestAnnotationsCountMatch:
    def test_annotations_count_match(self, tmp_path: Path) -> None:
        """labeled_topics matches JSONL line count -> exit 0."""
        grad_path, ann_path, diag_dir = _setup_valid(
            tmp_path,
            annotation_count=150,
            grad_overrides={
                "effective_prepare_yield": 0.6,
                "avg_latency_ms": 200.0,
                "shadow_adjusted_yield": 0.6,
            },
        )
        result = _run_validator(grad_path, ann_path, diag_dir)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "OK" in result.stdout


# ---------------------------------------------------------------------------
# 2. Annotations count mismatches labeled_topics
# ---------------------------------------------------------------------------


class TestAnnotationsCountMismatch:
    def test_annotations_count_mismatch(self, tmp_path: Path) -> None:
        """labeled_topics != JSONL line count -> exit 1."""
        grad_path, ann_path, diag_dir = _setup_valid(
            tmp_path,
            annotation_count=100,
            grad_overrides={"labeled_topics": 150},
        )
        result = _run_validator(grad_path, ann_path, diag_dir)
        assert result.returncode == 1
        assert "100" in result.stderr
        assert "150" in result.stderr


# ---------------------------------------------------------------------------
# 3. False-positive rate arithmetic mismatch
# ---------------------------------------------------------------------------


class TestFalsePositiveRateMismatch:
    def test_false_positive_rate_arithmetic_mismatch(self, tmp_path: Path) -> None:
        """false_positive_rate doesn't match computed -> exit 1."""
        # 8 false_positive out of 120 = 0.0667
        grad_path, ann_path, diag_dir = _setup_valid(
            tmp_path,
            annotation_count=120,
            fp_count=8,
            grad_overrides={"false_positive_rate": 0.04},
        )
        result = _run_validator(grad_path, ann_path, diag_dir)
        assert result.returncode == 1
        assert "false_positive_rate" in result.stderr


# ---------------------------------------------------------------------------
# 4. Diagnostics file count mismatches evaluated_dialogues
# ---------------------------------------------------------------------------


class TestDiagnosticsFileCountMismatch:
    def test_diagnostics_file_count_mismatch(self, tmp_path: Path) -> None:
        """evaluated_dialogues != diagnostics file count -> exit 1."""
        diag_files = [
            _make_diagnostics(
                packets_prepared=5,
                packets_injected=3,
                packets_surviving_precedence=3,
                per_turn_latency_ms=[200],
            )
            for _ in range(10)
        ]
        grad_path, ann_path, diag_dir = _setup_valid(
            tmp_path,
            diag_files=diag_files,
            grad_overrides={"evaluated_dialogues": 12},
        )
        result = _run_validator(grad_path, ann_path, diag_dir)
        assert result.returncode == 1
        assert "10" in result.stderr
        assert "12" in result.stderr


# ---------------------------------------------------------------------------
# 5. Yield metrics heterogeneous — effective_prepare_yield is global ratio
# ---------------------------------------------------------------------------


class TestYieldMetricsHeterogeneous:
    def test_yield_metrics_heterogeneous(self, tmp_path: Path) -> None:
        """effective_prepare_yield is global sum(injected)/sum(prepared)."""
        # Dialogue A: 10 prepared, 8 injected -> 0.8
        # Dialogue B: 2 prepared, 2 injected -> 1.0
        # Global: 10/12 = 0.8333...
        diag_files = [
            _make_diagnostics(
                packets_prepared=10,
                packets_injected=8,
                packets_surviving_precedence=8,
                per_turn_latency_ms=[200],
            ),
            _make_diagnostics(
                packets_prepared=2,
                packets_injected=2,
                packets_surviving_precedence=2,
                per_turn_latency_ms=[200],
            ),
        ]
        # Global yield = 10/12 = 0.8333...
        global_yield = 10 / 12
        grad_path, ann_path, diag_dir = _setup_valid(
            tmp_path,
            diag_files=diag_files,
            grad_overrides={
                "effective_prepare_yield": global_yield,
                "avg_latency_ms": 200.0,
                "shadow_adjusted_yield": global_yield,
            },
        )
        result = _run_validator(grad_path, ann_path, diag_dir)
        assert result.returncode == 0, f"stderr: {result.stderr}"


# ---------------------------------------------------------------------------
# 6. Latency metrics heterogeneous — avg_latency_ms is mean-of-all-turns
# ---------------------------------------------------------------------------


class TestLatencyMetricsHeterogeneous:
    def test_latency_metrics_heterogeneous(self, tmp_path: Path) -> None:
        """avg_latency_ms is mean of ALL turns, not mean of dialogue means.

        Dialogue A: [100, 300] -> mean 200
        Dialogue B: [400] -> mean 400
        Mean-of-means: (200+400)/2 = 300
        Mean-of-all-turns: (100+300+400)/3 = 266.67
        graduation.json declares mean-of-means (300) -> should FAIL.
        """
        diag_files = [
            _make_diagnostics(
                packets_prepared=5,
                packets_injected=3,
                packets_surviving_precedence=3,
                per_turn_latency_ms=[100, 300],
            ),
            _make_diagnostics(
                packets_prepared=5,
                packets_injected=3,
                packets_surviving_precedence=3,
                per_turn_latency_ms=[400],
            ),
        ]
        grad_path, ann_path, diag_dir = _setup_valid(
            tmp_path,
            diag_files=diag_files,
            grad_overrides={
                "avg_latency_ms": 300.0,  # mean-of-means, not mean-of-all-turns
                "effective_prepare_yield": 0.6,
                "shadow_adjusted_yield": 0.6,
            },
        )
        result = _run_validator(grad_path, ann_path, diag_dir)
        assert result.returncode == 1
        assert "avg_latency_ms" in result.stderr


# ---------------------------------------------------------------------------
# 7. Missing annotations file
# ---------------------------------------------------------------------------


class TestMissingAnnotations:
    def test_missing_annotations(self, tmp_path: Path) -> None:
        """--annotations file doesn't exist -> exit 1."""
        grad_path = _write_graduation(
            tmp_path / "graduation.json", _base_graduation()
        )
        diag_dir = tmp_path / "diagnostics"
        diag_dir.mkdir()
        _write_diagnostics_file(
            diag_dir / "d1.json",
            _make_diagnostics(per_turn_latency_ms=[200]),
        )
        missing = tmp_path / "nonexistent.jsonl"
        result = _run_validator(grad_path, missing, diag_dir)
        assert result.returncode == 1
        assert "annotations" in result.stderr.lower() or "not found" in result.stderr.lower()


# ---------------------------------------------------------------------------
# 8. Missing diagnostics directory
# ---------------------------------------------------------------------------


class TestMissingDiagnostics:
    def test_missing_diagnostics(self, tmp_path: Path) -> None:
        """--diagnostics-dir empty or missing -> exit 1."""
        grad_path = _write_graduation(
            tmp_path / "graduation.json", _base_graduation()
        )
        ann_path = _write_annotations(
            tmp_path / "annotations.jsonl",
            [_make_annotation()] * 150,
        )
        missing_dir = tmp_path / "no_such_dir"
        result = _run_validator(grad_path, ann_path, missing_dir)
        assert result.returncode == 1
        assert "diagnostics" in result.stderr.lower() or "not found" in result.stderr.lower()


# ---------------------------------------------------------------------------
# 9. Malformed annotations
# ---------------------------------------------------------------------------


class TestMalformedAnnotations:
    def test_malformed_annotations(self, tmp_path: Path) -> None:
        """Invalid JSONL -> exit 1."""
        grad_path = _write_graduation(
            tmp_path / "graduation.json", _base_graduation()
        )
        ann_path = tmp_path / "annotations.jsonl"
        ann_path.write_text(
            '{"topic_key": "x", "label": "true_positive"}\n'
            "not valid json\n"
            '{"topic_key": "y", "label": "false_positive"}\n'
        )
        diag_dir = tmp_path / "diagnostics"
        diag_dir.mkdir()
        _write_diagnostics_file(
            diag_dir / "d1.json",
            _make_diagnostics(per_turn_latency_ms=[200]),
        )
        result = _run_validator(grad_path, ann_path, diag_dir)
        assert result.returncode == 1
        assert "line 2" in result.stderr.lower() or "parse" in result.stderr.lower()


# ---------------------------------------------------------------------------
# 10. Sample size below minimum
# ---------------------------------------------------------------------------


class TestSampleSizeBelowMinimum:
    def test_sample_size_below_minimum(self, tmp_path: Path) -> None:
        """labeled_topics < 100 -> exit 1."""
        grad_path, ann_path, diag_dir = _setup_valid(
            tmp_path,
            annotation_count=50,
            fp_count=2,
            grad_overrides={"status": "approved"},
        )
        result = _run_validator(grad_path, ann_path, diag_dir)
        assert result.returncode == 1
        assert "50" in result.stderr
        assert "100" in result.stderr


# ---------------------------------------------------------------------------
# 11. Floating-point tolerance
# ---------------------------------------------------------------------------


class TestFloatingPointTolerance:
    def test_floating_point_tolerance(self, tmp_path: Path) -> None:
        """Tiny floating-point rounding -> still passes (tolerance 1e-6)."""
        # 5 fp out of 100 = 0.05. Declare 0.0500001 — within tolerance.
        grad_path, ann_path, diag_dir = _setup_valid(
            tmp_path,
            annotation_count=100,
            fp_count=5,
            grad_overrides={
                "false_positive_rate": 0.0500001,
                "effective_prepare_yield": 0.6,
                "avg_latency_ms": 200.0,
                "shadow_adjusted_yield": 0.6,
            },
        )
        result = _run_validator(grad_path, ann_path, diag_dir)
        assert result.returncode == 0, f"stderr: {result.stderr}"


# ---------------------------------------------------------------------------
# 12. Yield arithmetic heterogeneous packets_prepared
# ---------------------------------------------------------------------------


class TestYieldArithmeticHeterogeneous:
    def test_yield_arithmetic_heterogeneous_packets_prepared(self, tmp_path: Path) -> None:
        """Different packets_prepared across dialogues.

        Dialogue A: prepared=10, surviving_precedence=8
        Dialogue B: prepared=2, surviving_precedence=2
        Global ratio: 10/12 = 0.833
        graduation.json declares 0.9 (per-dialogue mean) -> FAIL.
        """
        diag_files = [
            _make_diagnostics(
                packets_prepared=10,
                packets_injected=8,
                packets_surviving_precedence=8,
                per_turn_latency_ms=[200],
            ),
            _make_diagnostics(
                packets_prepared=2,
                packets_injected=2,
                packets_surviving_precedence=2,
                per_turn_latency_ms=[200],
            ),
        ]
        grad_path, ann_path, diag_dir = _setup_valid(
            tmp_path,
            diag_files=diag_files,
            grad_overrides={
                "effective_prepare_yield": 0.9,  # per-dialogue mean, WRONG
                "avg_latency_ms": 200.0,
                "shadow_adjusted_yield": 0.9,
            },
        )
        result = _run_validator(grad_path, ann_path, diag_dir)
        assert result.returncode == 1
        assert "effective_prepare_yield" in result.stderr


# ---------------------------------------------------------------------------
# 13. Rejected status with absent notes
# ---------------------------------------------------------------------------


class TestRejectedStatusAbsentNotes:
    def test_rejected_status_with_absent_notes(self, tmp_path: Path) -> None:
        """status='rejected' with missing/empty notes -> exit 1."""
        grad_path, ann_path, diag_dir = _setup_valid(
            tmp_path,
            grad_overrides={"status": "rejected", "notes": ""},
        )
        result = _run_validator(grad_path, ann_path, diag_dir)
        assert result.returncode == 1
        assert "notes" in result.stderr.lower()


# ---------------------------------------------------------------------------
# 14. Approved with yield below threshold
# ---------------------------------------------------------------------------


class TestApprovedYieldBelowThreshold:
    def test_approved_with_yield_below_threshold(self, tmp_path: Path) -> None:
        """yield < 0.40 -> exit 1."""
        grad_path, ann_path, diag_dir = _setup_valid(
            tmp_path,
            grad_overrides={
                "status": "approved",
                "effective_prepare_yield": 0.30,
                "shadow_adjusted_yield": 0.30,
            },
        )
        result = _run_validator(grad_path, ann_path, diag_dir)
        assert result.returncode == 1
        assert "effective_prepare_yield" in result.stderr or "0.30" in result.stderr
        assert "0.40" in result.stderr or "threshold" in result.stderr.lower()


# ---------------------------------------------------------------------------
# 15. Approved with latency above threshold
# ---------------------------------------------------------------------------


class TestApprovedLatencyAboveThreshold:
    def test_approved_with_latency_above_threshold(self, tmp_path: Path) -> None:
        """latency > 500 -> exit 1."""
        diag_files = [
            _make_diagnostics(
                packets_prepared=5,
                packets_injected=3,
                packets_surviving_precedence=3,
                per_turn_latency_ms=[600],
            ),
        ]
        grad_path, ann_path, diag_dir = _setup_valid(
            tmp_path,
            diag_files=diag_files,
            grad_overrides={
                "status": "approved",
                "avg_latency_ms": 600.0,
                "effective_prepare_yield": 0.6,
                "shadow_adjusted_yield": 0.6,
            },
        )
        result = _run_validator(grad_path, ann_path, diag_dir)
        assert result.returncode == 1
        assert "latency" in result.stderr.lower() or "avg_latency_ms" in result.stderr


# ---------------------------------------------------------------------------
# 16. Shadow-adjusted yield validation
# ---------------------------------------------------------------------------


class TestShadowAdjustedYieldValidation:
    def test_shadow_adjusted_yield_below_threshold(self, tmp_path: Path) -> None:
        """shadow_adjusted_yield below threshold -> exit 1."""
        grad_path, ann_path, diag_dir = _setup_valid(
            tmp_path,
            grad_overrides={
                "status": "approved",
                "shadow_adjusted_yield": 0.35,
                "effective_prepare_yield": 0.65,
            },
        )
        result = _run_validator(grad_path, ann_path, diag_dir)
        assert result.returncode == 1
        assert "shadow_adjusted_yield" in result.stderr
        assert "0.35" in result.stderr or "0.40" in result.stderr

    def test_shadow_adjusted_yield_absent_freshness_guardrail(self, tmp_path: Path) -> None:
        """shadow_adjusted_yield absent (freshness guardrail) -> exit 0.

        effective_prepare_yield used as fallback gate.
        """
        grad_data = _base_graduation(
            status="approved",
            effective_prepare_yield=0.65,
            avg_latency_ms=200.0,
        )
        # Remove shadow_adjusted_yield to simulate freshness guardrail
        grad_data.pop("shadow_adjusted_yield", None)

        diag_files = [
            _make_diagnostics(
                packets_prepared=20,
                packets_injected=13,
                packets_surviving_precedence=13,
                per_turn_latency_ms=[200],
            ),
        ]
        diag_dir = tmp_path / "diagnostics"
        diag_dir.mkdir()
        for i, diag in enumerate(diag_files):
            _write_diagnostics_file(diag_dir / f"dialogue_{i}.json", diag)

        ann_path = _write_annotations(
            tmp_path / "annotations.jsonl",
            [_make_annotation(label="true_positive")] * 143
            + [_make_annotation(label="false_positive")] * 7,
        )
        grad_data["labeled_topics"] = 150
        grad_data["false_positive_rate"] = 7 / 150
        grad_data["evaluated_dialogues"] = 1
        grad_path = _write_graduation(tmp_path / "graduation.json", grad_data)

        result = _run_validator(grad_path, ann_path, diag_dir)
        assert result.returncode == 0, f"stderr: {result.stderr}"

    def test_shadow_adjusted_yield_valid_with_effective(self, tmp_path: Path) -> None:
        """Both shadow_adjusted_yield and effective_prepare_yield valid -> exit 0."""
        diag_files = [
            _make_diagnostics(
                packets_prepared=10,
                packets_injected=7,
                packets_surviving_precedence=7,
                per_turn_latency_ms=[200],
            ),
        ]
        grad_path, ann_path, diag_dir = _setup_valid(
            tmp_path,
            diag_files=diag_files,
            grad_overrides={
                "status": "approved",
                "shadow_adjusted_yield": 0.72,
                "effective_prepare_yield": 0.7,
                "avg_latency_ms": 200.0,
            },
        )
        result = _run_validator(grad_path, ann_path, diag_dir)
        assert result.returncode == 0, f"stderr: {result.stderr}"


# ---------------------------------------------------------------------------
# 17. Sample size escalation
# ---------------------------------------------------------------------------


class TestSampleSizeEscalation:
    def test_sample_size_escalation(self, tmp_path: Path) -> None:
        """preliminary rate >= 7% AND labeled_topics < 200 -> exit 1."""
        # false_positive_rate = 0.08 (>= 7%), labeled_topics = 120 (< 200)
        grad_path, ann_path, diag_dir = _setup_valid(
            tmp_path,
            annotation_count=120,
            fp_count=10,  # 10/120 ≈ 0.083
            grad_overrides={
                "status": "approved",
                "false_positive_rate": 10 / 120,
            },
        )
        result = _run_validator(grad_path, ann_path, diag_dir)
        assert result.returncode == 1
        assert "200" in result.stderr
        assert "120" in result.stderr


# ---------------------------------------------------------------------------
# Additional: Approved with false positive above threshold
# ---------------------------------------------------------------------------


class TestApprovedFalsePositiveAboveThreshold:
    def test_approved_with_false_positive_above_threshold(self, tmp_path: Path) -> None:
        """false_positive_rate > 0.10 -> exit 1."""
        # 23 fp out of 150 = 0.1533
        grad_path, ann_path, diag_dir = _setup_valid(
            tmp_path,
            annotation_count=150,
            fp_count=23,
            grad_overrides={
                "status": "approved",
                "false_positive_rate": 23 / 150,
            },
        )
        result = _run_validator(grad_path, ann_path, diag_dir)
        assert result.returncode == 1
        assert "false_positive_rate" in result.stderr
