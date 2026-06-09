"""Tests for trigger engine.

Tests cover: individual triggers, OR semantics, counter reset,
compaction baseline reset, headroom-sensitive thresholds.
Reference: Amendment 5 F3.
"""

from scripts.trigger_engine import SessionState, TriggerEngine, TriggerResult


def make_engine(window: int = 200_000) -> TriggerEngine:
    return TriggerEngine(window_size=window)


class TestTokenDeltaTrigger:
    def test_fires_at_5k_delta(self) -> None:
        engine = make_engine()
        state = SessionState(last_injected_occupancy=100_000)
        result = engine.evaluate(state, current_occupancy=105_001)
        assert result.should_inject is True
        assert "token_delta" in result.triggers_fired

    def test_does_not_fire_below_5k(self) -> None:
        engine = make_engine()
        state = SessionState(last_injected_occupancy=100_000)
        result = engine.evaluate(state, current_occupancy=104_999)
        assert "token_delta" not in result.triggers_fired

    def test_headroom_lowers_to_2k_above_85pct(self) -> None:
        engine = make_engine()
        # 85% of 200k = 170k
        state = SessionState(last_injected_occupancy=170_000)
        result = engine.evaluate(state, current_occupancy=172_001)
        assert "token_delta" in result.triggers_fired


class TestPercentageDeltaTrigger:
    def test_fires_at_2pct_of_window(self) -> None:
        engine = make_engine()
        # 2% of 200k = 4000
        state = SessionState(last_injected_occupancy=100_000)
        result = engine.evaluate(state, current_occupancy=104_001)
        assert "percentage_delta" in result.triggers_fired

    def test_does_not_fire_below_2pct(self) -> None:
        engine = make_engine()
        state = SessionState(last_injected_occupancy=100_000)
        result = engine.evaluate(state, current_occupancy=103_999)
        assert "percentage_delta" not in result.triggers_fired


class TestBoundaryCrossingTrigger:
    def test_fires_on_50pct_crossing(self) -> None:
        engine = make_engine()
        state = SessionState(
            last_injected_occupancy=90_000,
            last_boundaries_crossed=frozenset({0.25}),
        )
        result = engine.evaluate(state, current_occupancy=100_001)
        assert "boundary_crossing" in result.triggers_fired

    def test_does_not_fire_on_already_crossed(self) -> None:
        engine = make_engine()
        state = SessionState(
            last_injected_occupancy=100_000,
            last_boundaries_crossed=frozenset({0.25, 0.50}),
        )
        result = engine.evaluate(state, current_occupancy=100_001)
        assert "boundary_crossing" not in result.triggers_fired


class TestCompactionTrigger:
    def test_always_injects_on_compaction(self) -> None:
        engine = make_engine()
        state = SessionState(
            last_injected_occupancy=190_000,
            compaction_pending=True,
        )
        # Post-compaction occupancy is lower — compaction still fires
        result = engine.evaluate(state, current_occupancy=30_000)
        assert result.should_inject is True
        assert "compaction" in result.triggers_fired
        assert result.format == "compaction"


class TestHeartbeatTrigger:
    def test_fires_after_8_prompts(self) -> None:
        engine = make_engine()
        state = SessionState(
            last_injected_occupancy=100_000,
            prompts_since_injection=8,
            last_boundaries_crossed=frozenset({0.25, 0.50}),
        )
        result = engine.evaluate(state, current_occupancy=100_001)
        assert result.should_inject is True
        assert "heartbeat" in result.triggers_fired
        assert result.format == "minimal"

    def test_critical_fires_after_3_prompts_above_90pct(self) -> None:
        engine = make_engine()
        state = SessionState(
            last_injected_occupancy=180_000,
            prompts_since_injection=3,
        )
        # 90.5% occupancy → critical heartbeat interval
        result = engine.evaluate(state, current_occupancy=181_000)
        assert "heartbeat" in result.triggers_fired

    def test_does_not_fire_below_interval(self) -> None:
        engine = make_engine()
        state = SessionState(
            last_injected_occupancy=100_000,
            prompts_since_injection=5,
        )
        result = engine.evaluate(state, current_occupancy=100_001)
        assert "heartbeat" not in result.triggers_fired


class TestORSemantics:
    def test_multiple_triggers_use_full_format(self) -> None:
        engine = make_engine()
        state = SessionState(
            last_injected_occupancy=90_000,
            prompts_since_injection=8,
            last_boundaries_crossed=frozenset({0.25}),
        )
        # Crosses 50% boundary AND heartbeat fires → full wins over minimal
        result = engine.evaluate(state, current_occupancy=100_001)
        assert result.should_inject is True
        assert result.format == "full"

    def test_no_triggers_does_not_inject(self) -> None:
        engine = make_engine()
        state = SessionState(
            last_injected_occupancy=100_000,
            prompts_since_injection=2,
            last_boundaries_crossed=frozenset({0.25, 0.50}),
        )
        result = engine.evaluate(state, current_occupancy=100_001)
        assert result.should_inject is False
        assert result.format == "none"


class TestApplyResult:
    def test_injection_resets_counter_and_baseline(self) -> None:
        engine = make_engine()
        state = SessionState(
            last_injected_occupancy=100_000,
            prompts_since_injection=8,
        )
        result = engine.evaluate(state, current_occupancy=100_001)
        assert result.should_inject is True

        engine.apply_result(state, result, current_occupancy=100_001)
        assert state.prompts_since_injection == 0
        assert state.last_injected_occupancy == 100_001

    def test_suppressed_increments_counter(self) -> None:
        engine = make_engine()
        state = SessionState(
            last_injected_occupancy=100_000,
            prompts_since_injection=2,
            last_boundaries_crossed=frozenset({0.25, 0.50}),
        )
        result = engine.evaluate(state, current_occupancy=100_001)
        assert result.should_inject is False

        engine.apply_result(state, result, current_occupancy=100_001)
        assert state.prompts_since_injection == 3

    def test_compaction_resets_baseline(self) -> None:
        engine = make_engine()
        state = SessionState(
            last_injected_occupancy=190_000,
            compaction_pending=True,
            compaction_count=2,
        )
        result = engine.evaluate(state, current_occupancy=30_000)
        engine.apply_result(state, result, current_occupancy=30_000)

        assert state.last_injected_occupancy == 30_000
        assert state.compaction_pending is False
        assert state.compaction_count == 3
        assert state.last_boundaries_crossed == frozenset()
