from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import subprocess

import pytest


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "skill_impact_stats.py"
SPEC = importlib.util.spec_from_file_location("skill_impact_stats_module", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"test import failed: unable to load module spec. Got: {str(MODULE_PATH)!r}")
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_known_values_for_13_4_0() -> None:
    stats = MODULE.compute_skill_impact_stats(wins=13, losses=4, ties=0)

    assert stats.n_eff == 17
    assert stats.win_rate == pytest.approx(13 / 17, abs=1e-12)
    assert stats.p_help == pytest.approx(0.0245208740234375, abs=1e-12)
    assert stats.p_harm == pytest.approx(0.9936370849609375, abs=1e-12)
    assert stats.p_two_sided == pytest.approx(0.049041748046875, abs=1e-12)

    assert stats.wilson_95_ci is not None
    assert stats.wilson_95_ci.lower == pytest.approx(0.527, abs=0.002)
    assert stats.wilson_95_ci.upper == pytest.approx(0.904, abs=0.002)

    assert stats.thresholds.help_significant_min_wins == 13
    assert stats.thresholds.help_suggestive_min_wins == 12
    assert stats.thresholds.harm_significant_max_wins == 4
    assert stats.thresholds.harm_suggestive_max_wins == 5


def test_thresholds_match_n_eff_15_reference_cutoffs() -> None:
    stats = MODULE.compute_skill_impact_stats(wins=11, losses=4, ties=0)

    assert stats.n_eff == 15
    assert stats.thresholds.help_significant_min_wins == 12
    assert stats.thresholds.help_suggestive_min_wins == 11
    assert stats.thresholds.harm_significant_max_wins == 3
    assert stats.thresholds.harm_suggestive_max_wins == 4


def test_all_ties_is_reported_as_no_effective_sample() -> None:
    stats = MODULE.compute_skill_impact_stats(wins=0, losses=0, ties=17)

    assert stats.n_eff == 0
    assert stats.win_rate is None
    assert stats.wilson_95_ci is None
    assert stats.p_help is None
    assert stats.p_harm is None
    assert stats.p_two_sided is None
    assert stats.thresholds.help_significant_min_wins is None
    assert stats.thresholds.harm_significant_max_wins is None


def test_alpha_must_be_smaller_than_suggestive_alpha() -> None:
    with pytest.raises(ValueError, match="alpha must be smaller than suggestive_alpha"):
        MODULE.compute_skill_impact_stats(wins=12, losses=5, ties=0, alpha=0.1, suggestive_alpha=0.1)


def test_render_report_lines_infers_statistical_verdict() -> None:
    stats = MODULE.compute_skill_impact_stats(wins=13, losses=4, ties=0)

    report = MODULE.render_report_lines(
        stats=stats,
        primary_comparison="baseline",
        alpha=0.05,
        suggestive_alpha=0.10,
        verdict_override=None,
        tier1_result="8/9",
        tier2_result="4/5",
        tier3_result="2/3",
        holdout_stats=None,
    )

    assert "- Win rate: 76.5% (13 wins / 17 non-tied tasks), Wilson 95% CI: [52.7%, 90.4%]" in report
    assert "- Primary comparison: test vs baseline" in report
    assert "- Sign test: p_help = 0.0245 (significant); p_harm = 0.9936" in report
    assert "- Holdout (if run): not run" in report
    assert "- Tier 1: 8/9 | Tier 2: 4/5 | Tier 3: 2/3" in report
    assert "- Verdict: clearly helps" in report


def test_report_lines_requires_complete_holdout_triplet() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(MODULE_PATH),
            "--wins",
            "13",
            "--losses",
            "4",
            "--ties",
            "0",
            "--report-lines",
            "--holdout-wins",
            "10",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode != 0
    assert "holdout values must include wins/losses/ties together" in completed.stderr
