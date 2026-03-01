"""Summary line formatter for context metrics.

Three formats: full (material token change or boundary crossing), minimal
(heartbeat with no significant change), compaction (post-compact notice).
"""

from __future__ import annotations


def _format_tokens(n: int) -> str:
    """Format token count as human-readable: 142000 -> '142k', 1000000 -> '1M'.

    Truncates toward zero (floor division). Non-round values lose the
    remainder: 142,500 -> '142k', 999,999 -> '999k'. This is intentional —
    context metrics are approximate and exact counts would add visual noise.
    """
    if n >= 1_000_000 and n % 1_000_000 == 0:
        return f"{n // 1_000_000}M"
    if n >= 1_000:
        return f"{n // 1_000}k"
    return str(n)


def _pct(occupancy: int, window: int) -> int:
    return round(occupancy * 100 / window) if window > 0 else 0


def _boundary_warning(
    occupancy: int, window: int, soft_boundary: int | None
) -> str | None:
    if soft_boundary is None:
        return None
    if occupancy > soft_boundary:
        beyond = occupancy - soft_boundary
        return (
            f"{_format_tokens(occupancy)} tokens — {_format_tokens(beyond)} beyond "
            f"{_format_tokens(soft_boundary)} extended-context boundary"
        )
    ratio = occupancy / soft_boundary if soft_boundary > 0 else 0
    if ratio >= 0.80:
        return (
            f"{_format_tokens(occupancy)}/{_format_tokens(window)} tokens "
            f"({_pct(occupancy, window)}%) — approaching extended-context boundary"
        )
    return None


def format_full(
    *,
    occupancy: int,
    window: int,
    message_count: int,
    compaction_count: int,
    cost_usd: float | None,
    soft_boundary: int | None,
) -> str:
    """Full summary line for material changes."""
    warning = _boundary_warning(occupancy, window, soft_boundary)

    if warning:
        base = f"Context: {warning}"
    else:
        base = (
            f"Context: {_format_tokens(occupancy)}/{_format_tokens(window)} tokens "
            f"({_pct(occupancy, window)}%)"
        )

    parts = [base, f"{message_count} msgs"]

    phase = compaction_count + 1
    if compaction_count > 0:
        parts.append(f"Phase {phase} ({compaction_count} compactions)")
    else:
        parts.append(f"Phase {phase}")

    if cost_usd is not None:
        parts.append(f"~${cost_usd:.2f}")

    return " | ".join(parts)


def format_minimal(*, occupancy: int, window: int) -> str:
    """Minimal heartbeat line."""
    pct = _pct(occupancy, window)
    return f"Context: ~{pct}% (stable)"


def format_compaction(
    *,
    occupancy: int,
    window: int,
    compaction_number: int,
    message_count: int,
    cost_usd: float | None,
    soft_boundary: int | None,
) -> str:
    """Post-compaction notice."""
    base = (
        f"Context: {_format_tokens(occupancy)}/{_format_tokens(window)} tokens "
        f"({_pct(occupancy, window)}%) | Compaction #{compaction_number} just occurred"
    )
    parts = [base, f"{message_count} msgs"]
    if cost_usd is not None:
        parts.append(f"~${cost_usd:.2f}")
    return " | ".join(parts)
