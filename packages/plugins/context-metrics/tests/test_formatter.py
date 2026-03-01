"""Tests for summary formatter."""

from scripts.formatter import format_compaction, format_full, format_minimal


class TestFormatFull:
    def test_default_format(self) -> None:
        line = format_full(
            occupancy=142_000, window=200_000, message_count=847,
            compaction_count=2, cost_usd=None, soft_boundary=None,
        )
        assert line == "Context: 142k/200k tokens (71%) | 847 msgs | Phase 3 (2 compactions)"

    def test_with_cost(self) -> None:
        line = format_full(
            occupancy=142_000, window=200_000, message_count=847,
            compaction_count=2, cost_usd=1.24, soft_boundary=None,
        )
        assert "~$1.24" in line

    def test_approaching_soft_boundary(self) -> None:
        line = format_full(
            occupancy=168_000, window=200_000, message_count=500,
            compaction_count=0, cost_usd=None, soft_boundary=200_000,
        )
        assert "approaching" in line.lower()

    def test_exceeded_soft_boundary(self) -> None:
        line = format_full(
            occupancy=287_000, window=1_000_000, message_count=847,
            compaction_count=3, cost_usd=None, soft_boundary=200_000,
        )
        assert "beyond" in line.lower()

    def test_no_compactions(self) -> None:
        line = format_full(
            occupancy=50_000, window=200_000, message_count=100,
            compaction_count=0, cost_usd=None, soft_boundary=None,
        )
        assert "Phase 1" in line
        assert "compaction" not in line.lower()

    def test_1m_window(self) -> None:
        line = format_full(
            occupancy=287_000, window=1_000_000, message_count=847,
            compaction_count=3, cost_usd=None, soft_boundary=None,
        )
        assert "287k/1M" in line or "287k/1000k" in line


class TestFormatMinimal:
    def test_stable_heartbeat(self) -> None:
        line = format_minimal(occupancy=142_000, window=200_000)
        assert line == "Context: ~71% (stable)"

    def test_high_occupancy(self) -> None:
        line = format_minimal(occupancy=180_000, window=200_000)
        assert "90%" in line


class TestFormatCompaction:
    def test_post_compaction_notice(self) -> None:
        line = format_compaction(
            occupancy=34_000, window=200_000, compaction_number=3,
            message_count=847, cost_usd=None, soft_boundary=None,
        )
        assert "Compaction #3" in line
        assert "34k/200k" in line
