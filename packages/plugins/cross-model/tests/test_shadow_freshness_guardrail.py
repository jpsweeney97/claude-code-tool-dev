"""Freshness guardrail tests for shadow_adjusted_yield in graduation validation.

When classify_result_hash values are identical across all shadow turns for a
topic (stale classifier), the graduation tooling omits shadow_adjusted_yield
from graduation.json. The validator then falls back to effective_prepare_yield
as the gate metric. These tests verify all three paths:

1. Stale classify (shadow_adjusted_yield absent) -> fallback to
   effective_prepare_yield, exit 0
2. Fresh classify, shadow_adjusted_yield above threshold -> exit 0
3. Fresh classify, shadow_adjusted_yield below threshold -> exit 1
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


def _write_json(path: Path, data: object) -> Path:
    """Write a JSON file."""
    path.write_text(json.dumps(data))
    return path


def _write_annotations(path: Path, count: int, fp_count: int) -> Path:
    """Write an annotations.jsonl file with the given TP/FP distribution."""
    tp_count = count - fp_count
    lines = (
        [json.dumps({"topic_key": "hooks.pre_tool_use", "label": "true_positive"})]
        * tp_count
        + [json.dumps({"topic_key": "hooks.pre_tool_use", "label": "false_positive"})]
        * fp_count
    )
    path.write_text("\n".join(lines) + "\n")
    return path


def _make_diagnostics(
    *,
    packets_prepared: int = 5,
    packets_injected: int = 3,
    packets_surviving_precedence: int = 3,
    per_turn_latency_ms: list[int] | None = None,
) -> dict:
    """Create a diagnostics record dict."""
    return {
        "status": "shadow",
        "phase": "full",
        "packets_prepared": packets_prepared,
        "packets_injected": packets_injected,
        "packets_surviving_precedence": packets_surviving_precedence,
        "per_turn_latency_ms": per_turn_latency_ms or [200],
    }


def _setup_freshness_fixture(
    tmp_path: Path,
    *,
    include_shadow_yield: bool,
    shadow_adjusted_yield: float = 0.60,
    effective_prepare_yield: float = 0.65,
    annotation_count: int = 150,
    fp_count: int = 8,
) -> tuple[Path, Path, Path]:
    """Build fixture files for freshness guardrail tests.

    Args:
        include_shadow_yield: If True, include shadow_adjusted_yield in
            graduation.json. If False, omit it (simulates stale-classify
            scenario where graduation tooling detected staleness).
        shadow_adjusted_yield: Value to use when include_shadow_yield is True.
        effective_prepare_yield: The effective_prepare_yield value.
        annotation_count: Total annotation count.
        fp_count: Number of false-positive annotations.
    """
    # Diagnostics: single dialogue with values consistent with declared yield
    diag = _make_diagnostics(
        packets_prepared=20,
        packets_injected=13,
        packets_surviving_precedence=13,
        per_turn_latency_ms=[200],
    )
    diag_dir = tmp_path / "diagnostics"
    diag_dir.mkdir()
    _write_json(diag_dir / "dialogue_0.json", diag)

    # Annotations
    ann_path = _write_annotations(
        tmp_path / "annotations.jsonl",
        count=annotation_count,
        fp_count=fp_count,
    )

    # Graduation data — yield = 13/20 = 0.65
    grad_data: dict = {
        "status": "approved",
        "labeled_topics": annotation_count,
        "false_positive_rate": fp_count / annotation_count,
        "evaluated_dialogues": 1,
        "effective_prepare_yield": effective_prepare_yield,
        "avg_latency_ms": 200.0,
        "notes": "Approved after review",
    }
    if include_shadow_yield:
        grad_data["shadow_adjusted_yield"] = shadow_adjusted_yield

    grad_path = _write_json(tmp_path / "graduation.json", grad_data)

    return grad_path, ann_path, diag_dir


class TestShadowFreshnessGuardrail:
    """Freshness guardrail: stale classify → shadow_adjusted_yield absent."""

    def test_freshness_guardrail_fires_on_stale_classify(
        self, tmp_path: Path,
    ) -> None:
        """Stale classify hashes -> shadow_adjusted_yield absent -> exit 0.

        When all classify_result_hash values are identical across shadow turns,
        the graduation tooling detects staleness and omits
        shadow_adjusted_yield. The validator falls back to
        effective_prepare_yield as the gate metric. Since effective_prepare_yield
        (0.65) exceeds the 0.40 threshold, the validator exits 0.
        """
        grad_path, ann_path, diag_dir = _setup_freshness_fixture(
            tmp_path,
            include_shadow_yield=False,
            effective_prepare_yield=0.65,
        )
        result = _run_validator(grad_path, ann_path, diag_dir)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "OK" in result.stdout
        assert "shadow_adjusted_yield absent" in result.stderr
        assert "freshness guardrail" in result.stderr

    def test_freshness_guardrail_positive_path(
        self, tmp_path: Path,
    ) -> None:
        """Fresh classify, shadow_adjusted_yield above threshold -> exit 0.

        Different classify_result_hash values across turns means fresh data.
        shadow_adjusted_yield (0.60) is present and exceeds 0.40 threshold.
        """
        grad_path, ann_path, diag_dir = _setup_freshness_fixture(
            tmp_path,
            include_shadow_yield=True,
            shadow_adjusted_yield=0.60,
            effective_prepare_yield=0.65,
        )
        result = _run_validator(grad_path, ann_path, diag_dir)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "OK" in result.stdout
        assert "shadow_adjusted_yield absent" not in result.stderr

    def test_freshness_guardrail_negative_path(
        self, tmp_path: Path,
    ) -> None:
        """Fresh classify, shadow_adjusted_yield below threshold -> exit 1.

        shadow_adjusted_yield (0.35) is present but below the 0.40 threshold.
        Validator should exit 1 and cite shadow_adjusted_yield.
        """
        grad_path, ann_path, diag_dir = _setup_freshness_fixture(
            tmp_path,
            include_shadow_yield=True,
            shadow_adjusted_yield=0.35,
            effective_prepare_yield=0.65,
        )
        result = _run_validator(grad_path, ann_path, diag_dir)
        assert result.returncode == 1
        assert "shadow_adjusted_yield" in result.stderr
        assert "0.35" in result.stderr or "0.40" in result.stderr

    def test_freshness_guardrail_combined_warning_and_error(
        self, tmp_path: Path,
    ) -> None:
        """Stale classify AND effective_prepare_yield below threshold -> exit 1.

        shadow_adjusted_yield is absent (freshness guardrail), so the validator
        falls back to effective_prepare_yield. But effective_prepare_yield (0.30)
        is below the 0.40 threshold. Both the freshness warning and the
        threshold error appear in stderr.
        """
        diag_dir = tmp_path / "diagnostics"
        diag_dir.mkdir()
        _write_json(
            diag_dir / "dialogue_0.json",
            _make_diagnostics(
                packets_prepared=20,
                packets_injected=6,
                packets_surviving_precedence=6,
                per_turn_latency_ms=[200],
            ),
        )
        _write_annotations(
            tmp_path / "annotations.jsonl", count=150, fp_count=8,
        )
        grad_path = _write_json(
            tmp_path / "graduation.json",
            {
                "status": "approved",
                "labeled_topics": 150,
                "false_positive_rate": 8 / 150,
                "evaluated_dialogues": 1,
                "effective_prepare_yield": 0.30,
                "avg_latency_ms": 200.0,
                "notes": "Approved after review",
            },
        )
        result = _run_validator(
            grad_path, tmp_path / "annotations.jsonl", diag_dir,
        )
        assert result.returncode == 1
        # Freshness warning present
        assert "shadow_adjusted_yield absent" in result.stderr
        assert "freshness guardrail" in result.stderr
        # Threshold error also present
        assert "effective_prepare_yield" in result.stderr
        assert "below" in result.stderr

    def test_freshness_guardrail_rejected_no_warning(
        self, tmp_path: Path,
    ) -> None:
        """Rejected status, shadow absent -> exit 0, no freshness warning.

        The freshness warning is approved-only. Rejected reports skip it.
        """
        diag_dir = tmp_path / "diagnostics"
        diag_dir.mkdir()
        _write_json(
            diag_dir / "dialogue_0.json",
            _make_diagnostics(
                packets_prepared=20,
                packets_injected=13,
                packets_surviving_precedence=13,
                per_turn_latency_ms=[200],
            ),
        )
        _write_annotations(
            tmp_path / "annotations.jsonl", count=150, fp_count=8,
        )
        grad_path = _write_json(
            tmp_path / "graduation.json",
            {
                "status": "rejected",
                "labeled_topics": 150,
                "false_positive_rate": 8 / 150,
                "evaluated_dialogues": 1,
                "effective_prepare_yield": 0.65,
                "avg_latency_ms": 200.0,
                "notes": "Rejected - yield issues",
            },
        )
        result = _run_validator(
            grad_path, tmp_path / "annotations.jsonl", diag_dir,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "OK" in result.stdout
        assert "shadow_adjusted_yield absent" not in result.stderr
