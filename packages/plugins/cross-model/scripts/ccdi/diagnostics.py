"""CCDI diagnostics emitter.

Wraps DiagnosticsRecord to provide a recording API for the injection
pipeline.  Three output schemas:

- **active**: Core counters and topic lists; shadow-only fields omitted.
- **shadow**: All active fields plus shadow-only fields and
  ``shadow_adjusted_yield``.
- **unavailable**: Only ``status`` and ``phase`` — emitted when the
  pipeline cannot run (no inventory, disabled, etc.).
"""

from __future__ import annotations

from scripts.ccdi.types import DiagnosticsRecord


class DiagnosticsEmitter:
    """Records pipeline events and emits a DiagnosticsRecord dict."""

    def __init__(
        self,
        status: str,
        phase: str,
        inventory_epoch: str | None,
        config_source: str,
    ) -> None:
        self._record = DiagnosticsRecord(
            status=status,
            phase=phase,
            topics_detected=[],
            topics_injected=[],
            topics_deferred=[],
            topics_suppressed=[],
            packets_prepared=0,
            packets_injected=0,
            packets_deferred_scout=0,
            total_tokens_injected=0,
            semantic_hints_received=0,
            search_failures=0,
            inventory_epoch=inventory_epoch,
            config_source=config_source,
            per_turn_latency_ms=[],
        )
        if status == "shadow":
            self._record.packets_target_relevant = 0
            self._record.packets_surviving_precedence = 0
            self._record.false_positive_topic_detections = 0

    # -- Recording API -------------------------------------------------------

    def record_turn(self, latency_ms: int) -> None:
        """Append a per-turn latency measurement."""
        self._record.per_turn_latency_ms.append(latency_ms)

    def record_topic_detected(self, topic_key: str) -> None:
        """Record a detected topic (deduplicated)."""
        if topic_key not in self._record.topics_detected:
            self._record.topics_detected.append(topic_key)

    def record_topic_injected(self, topic_key: str) -> None:
        """Record an injected topic (deduplicated)."""
        if topic_key not in self._record.topics_injected:
            self._record.topics_injected.append(topic_key)

    def record_topic_deferred(self, topic_key: str) -> None:
        """Record a deferred topic (deduplicated)."""
        if topic_key not in self._record.topics_deferred:
            self._record.topics_deferred.append(topic_key)

    def record_topic_suppressed(self, topic_key: str) -> None:
        """Record a suppressed topic (deduplicated)."""
        if topic_key not in self._record.topics_suppressed:
            self._record.topics_suppressed.append(topic_key)

    def record_packet_prepared(self) -> None:
        """Increment prepared packet counter."""
        self._record.packets_prepared += 1

    def record_packet_injected(self, tokens: int) -> None:
        """Increment injected packet counter and add tokens."""
        self._record.packets_injected += 1
        self._record.total_tokens_injected += tokens

    def record_packet_deferred_scout(self) -> None:
        """Increment scout-deferred packet counter."""
        self._record.packets_deferred_scout += 1

    def record_search_failure(self) -> None:
        """Increment search failure counter."""
        self._record.search_failures += 1

    def record_hint_received(self) -> None:
        """Increment semantic hint counter."""
        self._record.semantic_hints_received += 1

    # -- Emit ----------------------------------------------------------------

    def emit(self) -> dict:
        """Serialize the accumulated record to a dict."""
        return self._record.to_dict()

    @staticmethod
    def unavailable(phase: str = "initial_only") -> dict:
        """Return an unavailable-status diagnostics dict."""
        return {"status": "unavailable", "phase": phase}
