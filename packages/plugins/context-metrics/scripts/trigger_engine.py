"""Trigger engine for delta-gated injection.

Evaluates 5 trigger types per UserPromptSubmit with OR semantics.
Counter resets on injection. Compaction always injects and resets baseline.

OR semantics: any single trigger fires injection. Format priority:
compaction > full (delta/boundary) > minimal (heartbeat) > none.
"""

from __future__ import annotations

from dataclasses import dataclass, field

BOUNDARIES = frozenset({0.25, 0.50, 0.75, 0.90})
HEARTBEAT_NORMAL = 8
HEARTBEAT_CRITICAL = 3
TOKEN_DELTA_NORMAL = 5000
TOKEN_DELTA_HEADROOM = 2000
HEADROOM_THRESHOLD = 0.85
CRITICAL_THRESHOLD = 0.90
PERCENTAGE_DELTA = 0.02


@dataclass
class SessionState:
    last_injected_occupancy: int = 0
    prompts_since_injection: int = 0
    last_boundaries_crossed: frozenset[float] = field(default_factory=frozenset)
    compaction_pending: bool = False
    compaction_count: int = 0


@dataclass
class TriggerResult:
    should_inject: bool
    format: str  # "full", "minimal", "compaction", "none"
    triggers_fired: list[str]


class TriggerEngine:
    def __init__(self, window_size: int) -> None:
        self.window_size = window_size

    def evaluate(self, state: SessionState, current_occupancy: int) -> TriggerResult:
        """Evaluate all triggers. OR semantics: inject if any fires."""
        triggers: list[str] = []
        occupancy_pct = current_occupancy / self.window_size if self.window_size > 0 else 0
        delta = current_occupancy - state.last_injected_occupancy

        # 1. Compaction — always injects
        if state.compaction_pending:
            triggers.append("compaction")

        # 2. Token delta (headroom-sensitive)
        threshold = TOKEN_DELTA_HEADROOM if occupancy_pct >= HEADROOM_THRESHOLD else TOKEN_DELTA_NORMAL
        if delta >= threshold:
            triggers.append("token_delta")

        # 3. Percentage delta (2% of window)
        pct_threshold = int(self.window_size * PERCENTAGE_DELTA)
        if delta >= pct_threshold:
            triggers.append("percentage_delta")

        # 4. Boundary crossing
        current_boundaries = frozenset(b for b in BOUNDARIES if occupancy_pct >= b)
        new_crossings = current_boundaries - state.last_boundaries_crossed
        if new_crossings:
            triggers.append("boundary_crossing")

        # 5. Heartbeat
        interval = HEARTBEAT_CRITICAL if occupancy_pct >= CRITICAL_THRESHOLD else HEARTBEAT_NORMAL
        if state.prompts_since_injection >= interval:
            triggers.append("heartbeat")

        # OR semantics + format priority
        should_inject = len(triggers) > 0
        if "compaction" in triggers:
            fmt = "compaction"
        elif any(t in triggers for t in ("token_delta", "percentage_delta", "boundary_crossing")):
            fmt = "full"
        elif "heartbeat" in triggers:
            fmt = "minimal"
        else:
            fmt = "none"

        return TriggerResult(should_inject=should_inject, format=fmt, triggers_fired=triggers)

    def apply_result(
        self, state: SessionState, result: TriggerResult, current_occupancy: int
    ) -> None:
        """Update session state after trigger evaluation."""
        occupancy_pct = current_occupancy / self.window_size if self.window_size > 0 else 0

        if result.should_inject:
            state.last_injected_occupancy = current_occupancy
            state.prompts_since_injection = 0
            state.last_boundaries_crossed = frozenset(
                b for b in BOUNDARIES if occupancy_pct >= b
            )
            if state.compaction_pending:
                state.compaction_count += 1
                state.compaction_pending = False
                # Compaction resets boundary tracking
                state.last_boundaries_crossed = frozenset()
        else:
            state.prompts_since_injection += 1
