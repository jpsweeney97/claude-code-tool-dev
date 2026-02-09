#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from statistics import NormalDist


@dataclass(frozen=True)
class WilsonInterval:
    confidence: float
    lower: float
    upper: float


@dataclass(frozen=True)
class SignTestThresholds:
    n_eff: int
    help_significant_min_wins: int | None
    help_suggestive_min_wins: int | None
    harm_significant_max_wins: int | None
    harm_suggestive_max_wins: int | None


@dataclass(frozen=True)
class SkillImpactStats:
    wins: int
    losses: int
    ties: int
    n_eff: int
    total_tasks: int
    win_rate: float | None
    wilson_95_ci: WilsonInterval | None
    p_help: float | None
    p_harm: float | None
    p_two_sided: float | None
    thresholds: SignTestThresholds


def _binom_tail_ge(n_eff: int, wins: int) -> float:
    if n_eff < 0 or wins < 0:
        raise ValueError(f"binomial tail failed: invalid n_eff/wins. Got: {(n_eff, wins)!r}")
    if wins > n_eff:
        return 0.0
    denominator = 2**n_eff
    numerator = sum(math.comb(n_eff, count) for count in range(wins, n_eff + 1))
    return numerator / denominator


def _binom_tail_le(n_eff: int, wins: int) -> float:
    if n_eff < 0 or wins < 0:
        raise ValueError(f"binomial cdf failed: invalid n_eff/wins. Got: {(n_eff, wins)!r}")
    if wins >= n_eff:
        return 1.0
    denominator = 2**n_eff
    numerator = sum(math.comb(n_eff, count) for count in range(0, wins + 1))
    return numerator / denominator


def _wilson_interval(wins: int, n_eff: int, confidence: float = 0.95) -> WilsonInterval | None:
    if n_eff == 0:
        return None
    if not (0 < confidence < 1):
        raise ValueError(f"wilson interval failed: confidence must be in (0, 1). Got: {confidence!r}")

    z = NormalDist().inv_cdf(0.5 + confidence / 2)
    phat = wins / n_eff
    z2_over_n = (z**2) / n_eff
    denominator = 1 + z2_over_n
    center = (phat + (z2_over_n / 2)) / denominator
    margin = z * math.sqrt((phat * (1 - phat) + (z2_over_n / 4)) / n_eff) / denominator
    return WilsonInterval(confidence=confidence, lower=max(0.0, center - margin), upper=min(1.0, center + margin))


def _help_threshold(n_eff: int, alpha: float) -> int | None:
    if n_eff == 0:
        return None
    for wins in range(0, n_eff + 1):
        if _binom_tail_ge(n_eff=n_eff, wins=wins) < alpha:
            return wins
    return None


def _harm_threshold(n_eff: int, alpha: float) -> int | None:
    if n_eff == 0:
        return None
    for wins in range(n_eff, -1, -1):
        if _binom_tail_le(n_eff=n_eff, wins=wins) < alpha:
            return wins
    return None


def compute_skill_impact_stats(
    *,
    wins: int,
    losses: int,
    ties: int,
    confidence: float = 0.95,
    alpha: float = 0.05,
    suggestive_alpha: float = 0.10,
) -> SkillImpactStats:
    if wins < 0 or losses < 0 or ties < 0:
        raise ValueError(f"stats input failed: wins/losses/ties must be non-negative. Got: {(wins, losses, ties)!r}")
    if not (0 < alpha < 1):
        raise ValueError(f"stats input failed: alpha must be in (0, 1). Got: {alpha!r}")
    if not (0 < suggestive_alpha < 1):
        raise ValueError(f"stats input failed: suggestive_alpha must be in (0, 1). Got: {suggestive_alpha!r}")
    if alpha >= suggestive_alpha:
        raise ValueError(
            f"stats input failed: alpha must be smaller than suggestive_alpha. Got: {(alpha, suggestive_alpha)!r}"
        )

    n_eff = wins + losses
    total_tasks = n_eff + ties
    win_rate = None if n_eff == 0 else (wins / n_eff)
    wilson_95_ci = _wilson_interval(wins=wins, n_eff=n_eff, confidence=confidence)
    p_help = None if n_eff == 0 else _binom_tail_ge(n_eff=n_eff, wins=wins)
    p_harm = None if n_eff == 0 else _binom_tail_le(n_eff=n_eff, wins=wins)
    p_two_sided = None if p_help is None or p_harm is None else min(1.0, 2 * min(p_help, p_harm))
    thresholds = SignTestThresholds(
        n_eff=n_eff,
        help_significant_min_wins=_help_threshold(n_eff=n_eff, alpha=alpha),
        help_suggestive_min_wins=_help_threshold(n_eff=n_eff, alpha=suggestive_alpha),
        harm_significant_max_wins=_harm_threshold(n_eff=n_eff, alpha=alpha),
        harm_suggestive_max_wins=_harm_threshold(n_eff=n_eff, alpha=suggestive_alpha),
    )

    return SkillImpactStats(
        wins=wins,
        losses=losses,
        ties=ties,
        n_eff=n_eff,
        total_tasks=total_tasks,
        win_rate=win_rate,
        wilson_95_ci=wilson_95_ci,
        p_help=p_help,
        p_harm=p_harm,
        p_two_sided=p_two_sided,
        thresholds=thresholds,
    )


def _format_percent(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{(100 * value):.1f}%"


def _format_float(value: float | None, digits: int = 4) -> str:
    if value is None:
        return "N/A"
    return f"{value:.{digits}f}"


def _format_threshold(threshold: int | None, n_eff: int) -> str:
    if threshold is None or n_eff == 0:
        return "N/A"
    return f"{threshold} wins ({_format_percent(threshold / n_eff)})"


def _p_help_label(*, p_help: float | None, n_eff: int, alpha: float, suggestive_alpha: float) -> str:
    if p_help is None or n_eff < 12:
        return "inconclusive"
    if p_help < alpha:
        return "significant"
    if p_help < suggestive_alpha:
        return "suggestive"
    return "not significant"


def infer_verdict(
    *,
    stats: SkillImpactStats,
    primary_comparison: str,
    alpha: float,
    suggestive_alpha: float,
) -> str:
    if stats.n_eff < 12 or stats.p_help is None or stats.p_harm is None:
        return "inconclusive"
    if stats.p_harm < alpha:
        return "harmful"
    if stats.p_help < alpha:
        return "clearly helps"
    if stats.p_help < suggestive_alpha:
        return "suggestive"
    if primary_comparison == "placebo":
        return "no incremental value"
    return "no effect"


def _format_ci_percent(interval: WilsonInterval | None) -> tuple[str, str]:
    if interval is None:
        return ("N/A", "N/A")
    return (_format_percent(interval.lower), _format_percent(interval.upper))


def render_report_lines(
    *,
    stats: SkillImpactStats,
    primary_comparison: str,
    alpha: float,
    suggestive_alpha: float,
    verdict_override: str | None,
    tier1_result: str,
    tier2_result: str,
    tier3_result: str,
    holdout_stats: SkillImpactStats | None,
) -> str:
    win_rate = _format_percent(stats.win_rate)
    tie_rate = None if stats.total_tasks == 0 else (stats.ties / stats.total_tasks)
    tie_rate_text = _format_percent(tie_rate)
    ci_low, ci_high = _format_ci_percent(stats.wilson_95_ci)
    p_help_label = _p_help_label(p_help=stats.p_help, n_eff=stats.n_eff, alpha=alpha, suggestive_alpha=suggestive_alpha)
    verdict = verdict_override or infer_verdict(
        stats=stats,
        primary_comparison=primary_comparison,
        alpha=alpha,
        suggestive_alpha=suggestive_alpha,
    )

    lines: list[str] = []
    lines.append(
        f"- Win rate: {win_rate} ({stats.wins} wins / {stats.n_eff} non-tied tasks), "
        f"Wilson 95% CI: [{ci_low}, {ci_high}]"
    )
    lines.append(f"- Primary comparison: test vs {primary_comparison}")
    lines.append(f"- Ties: {stats.ties}/{stats.total_tasks} tasks (tie rate: {tie_rate_text})")
    lines.append(
        f"- Sign test: p_help = {_format_float(stats.p_help)} ({p_help_label}); "
        f"p_harm = {_format_float(stats.p_harm)}"
    )

    if holdout_stats is None:
        lines.append("- Holdout (if run): not run")
    else:
        holdout_verdict = infer_verdict(
            stats=holdout_stats,
            primary_comparison=primary_comparison,
            alpha=alpha,
            suggestive_alpha=suggestive_alpha,
        )
        lines.append(
            f"- Holdout (if run): win rate = {_format_percent(holdout_stats.win_rate)}; "
            f"p_help = {_format_float(holdout_stats.p_help)}; "
            f"p_harm = {_format_float(holdout_stats.p_harm)}; "
            f"verdict = {holdout_verdict}"
        )

    lines.append(f"- Tier 1: {tier1_result} | Tier 2: {tier2_result} | Tier 3: {tier3_result}")
    lines.append(f"- Verdict: {verdict}")
    return "\n".join(lines)


def render_text(stats: SkillImpactStats, *, alpha: float, suggestive_alpha: float) -> str:
    lines: list[str] = []
    lines.append(
        f"Input: wins={stats.wins}, losses={stats.losses}, ties={stats.ties}, "
        f"N_eff={stats.n_eff}, total_tasks={stats.total_tasks}"
    )

    if stats.win_rate is None:
        lines.append("Win rate: N/A (no non-tied tasks)")
        lines.append("Wilson CI: N/A (no non-tied tasks)")
        lines.append("Sign test: N/A (no non-tied tasks)")
    else:
        lines.append(f"Win rate: {_format_float(stats.win_rate)} ({_format_percent(stats.win_rate)})")
        if stats.wilson_95_ci is None:
            lines.append("Wilson CI: N/A")
        else:
            lines.append(
                f"Wilson {int(stats.wilson_95_ci.confidence * 100)}% CI: "
                f"[{_format_float(stats.wilson_95_ci.lower)}, {_format_float(stats.wilson_95_ci.upper)}]"
            )
        lines.append(
            "Sign test: "
            f"p_help={_format_float(stats.p_help)}; "
            f"p_harm={_format_float(stats.p_harm)}; "
            f"p_two_sided={_format_float(stats.p_two_sided)}"
        )

    lines.append("Thresholds (one-tailed, from N_eff):")
    lines.append(
        f"- help significant (p < {alpha:.2f}): "
        f"{_format_threshold(stats.thresholds.help_significant_min_wins, stats.n_eff)}"
    )
    lines.append(
        f"- help suggestive (p < {suggestive_alpha:.2f}): "
        f"{_format_threshold(stats.thresholds.help_suggestive_min_wins, stats.n_eff)}"
    )
    lines.append(
        f"- harm significant (p < {alpha:.2f}): "
        f"{_format_threshold(stats.thresholds.harm_significant_max_wins, stats.n_eff)}"
    )
    lines.append(
        f"- harm suggestive (p < {suggestive_alpha:.2f}): "
        f"{_format_threshold(stats.thresholds.harm_suggestive_max_wins, stats.n_eff)}"
    )

    if stats.n_eff < 12:
        lines.append("Warning: N_eff < 12; assessment is likely underpowered/inconclusive per spec.")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Compute reproducible skill-impact stats from wins/losses/ties: "
            "p_help, p_harm, two-sided p, Wilson CI, and sign-test thresholds."
        )
    )
    parser.add_argument("--wins", type=int, required=True, help="Treatment task wins (non-negative integer).")
    parser.add_argument("--losses", type=int, required=True, help="Treatment task losses (non-negative integer).")
    parser.add_argument("--ties", type=int, required=True, help="Task ties (non-negative integer).")
    parser.add_argument("--confidence", type=float, default=0.95, help="Wilson CI confidence level (default: 0.95).")
    parser.add_argument("--alpha", type=float, default=0.05, help="Significance alpha (default: 0.05).")
    parser.add_argument(
        "--suggestive-alpha",
        type=float,
        default=0.10,
        help="Suggestive threshold alpha (default: 0.10).",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--report-lines",
        action="store_true",
        help="Emit paste-ready `## Summary` bullet lines aligned with the measurement spec.",
    )
    parser.add_argument(
        "--primary-comparison",
        choices=("baseline", "placebo"),
        default="baseline",
        help="Primary comparator used in the sign test (default: baseline).",
    )
    parser.add_argument(
        "--tier1-result",
        default="X/9",
        help="Tier 1 summary token for report-lines mode (default: X/9).",
    )
    parser.add_argument(
        "--tier2-result",
        default="X/5",
        help="Tier 2 summary token for report-lines mode (default: X/5).",
    )
    parser.add_argument(
        "--tier3-result",
        default="X/3",
        help="Tier 3 summary token for report-lines mode (default: X/3).",
    )
    parser.add_argument(
        "--verdict",
        default=None,
        help="Optional explicit verdict override for report-lines mode.",
    )
    parser.add_argument("--holdout-wins", type=int, default=None, help="Optional holdout wins for report-lines mode.")
    parser.add_argument(
        "--holdout-losses",
        type=int,
        default=None,
        help="Optional holdout losses for report-lines mode.",
    )
    parser.add_argument("--holdout-ties", type=int, default=None, help="Optional holdout ties for report-lines mode.")
    args = parser.parse_args()

    stats = compute_skill_impact_stats(
        wins=args.wins,
        losses=args.losses,
        ties=args.ties,
        confidence=args.confidence,
        alpha=args.alpha,
        suggestive_alpha=args.suggestive_alpha,
    )

    holdout_values = (args.holdout_wins, args.holdout_losses, args.holdout_ties)
    has_any_holdout = any(value is not None for value in holdout_values)
    has_all_holdout = all(value is not None for value in holdout_values)
    if has_any_holdout and not has_all_holdout:
        raise SystemExit(
            f"report-lines failed: holdout values must include wins/losses/ties together. Got: {holdout_values!r}"
        )
    holdout_stats = None
    if has_all_holdout:
        holdout_stats = compute_skill_impact_stats(
            wins=args.holdout_wins,
            losses=args.holdout_losses,
            ties=args.holdout_ties,
            confidence=args.confidence,
            alpha=args.alpha,
            suggestive_alpha=args.suggestive_alpha,
        )

    if args.report_lines:
        print(
            render_report_lines(
                stats=stats,
                primary_comparison=args.primary_comparison,
                alpha=args.alpha,
                suggestive_alpha=args.suggestive_alpha,
                verdict_override=args.verdict,
                tier1_result=args.tier1_result,
                tier2_result=args.tier2_result,
                tier3_result=args.tier3_result,
                holdout_stats=holdout_stats,
            )
        )
        return

    if args.format == "json":
        print(json.dumps(asdict(stats), indent=2, sort_keys=True))
        return

    print(render_text(stats, alpha=args.alpha, suggestive_alpha=args.suggestive_alpha))


if __name__ == "__main__":
    main()
