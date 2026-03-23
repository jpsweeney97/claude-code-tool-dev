"""Tests for CCDI packet builder.

Covers all 15 test cases from the delivery spec: budget enforcement,
deduplication, citation format, mode selection, quality thresholds,
cardinality constraints, and determinism.
"""

from __future__ import annotations

from scripts.ccdi.config import BUILTIN_DEFAULTS, CCDIConfig
from scripts.ccdi.types import (
    DocRef,
    FactItem,
    FactPacket,
    TopicRegistryEntry,
)

# Import will fail until packets.py exists (TDD red phase)
from scripts.ccdi.packets import build_packet, render_initial, render_mid_turn

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _default_config() -> CCDIConfig:
    """Build CCDIConfig from all built-in defaults."""
    c = BUILTIN_DEFAULTS["classifier"]
    i = BUILTIN_DEFAULTS["injection"]
    p = BUILTIN_DEFAULTS["packets"]
    return CCDIConfig(
        classifier_confidence_high_min_weight=c["confidence_high_min_weight"],
        classifier_confidence_medium_min_score=c["confidence_medium_min_score"],
        classifier_confidence_medium_min_single_weight=c[
            "confidence_medium_min_single_weight"
        ],
        injection_initial_threshold_high_count=i["initial_threshold_high_count"],
        injection_initial_threshold_medium_same_family_count=i[
            "initial_threshold_medium_same_family_count"
        ],
        injection_mid_turn_consecutive_medium_turns=i[
            "mid_turn_consecutive_medium_turns"
        ],
        injection_cooldown_max_new_topics_per_turn=i[
            "cooldown_max_new_topics_per_turn"
        ],
        injection_deferred_ttl_turns=i["deferred_ttl_turns"],
        packets_initial_token_budget_min=p["initial_token_budget_min"],
        packets_initial_token_budget_max=p["initial_token_budget_max"],
        packets_initial_max_topics=p["initial_max_topics"],
        packets_initial_max_facts=p["initial_max_facts"],
        packets_mid_turn_token_budget_min=p["mid_turn_token_budget_min"],
        packets_mid_turn_token_budget_max=p["mid_turn_token_budget_max"],
        packets_mid_turn_max_topics=p["mid_turn_max_topics"],
        packets_mid_turn_max_facts=p["mid_turn_max_facts"],
        packets_quality_min_result_score=p["quality_min_result_score"],
        packets_quality_min_useful_facts=p["quality_min_useful_facts"],
    )


def _make_result(
    chunk_id: str,
    content: str,
    *,
    category: str = "hooks",
    source_file: str = "https://code.claude.com/docs/en/hooks",
    snippet: str = "hook event",
    score: float = 0.85,
) -> dict:
    """Build a search result dict matching search_docs output."""
    return {
        "chunk_id": chunk_id,
        "content": content,
        "snippet": snippet,
        "category": category,
        "source_file": source_file,
        "score": score,
    }


def _make_registry_entry(
    topic_key: str = "hooks.pre_tool_use",
    *,
    injected_chunk_ids: list[str] | None = None,
) -> TopicRegistryEntry:
    """Build a minimal TopicRegistryEntry with given injected chunk IDs."""
    return TopicRegistryEntry(
        topic_key=topic_key,
        family_key="hooks",
        state="injected",
        first_seen_turn=1,
        last_seen_turn=2,
        last_injected_turn=1,
        last_query_fingerprint=None,
        consecutive_medium_count=0,
        suppression_reason=None,
        suppressed_docs_epoch=None,
        deferred_reason=None,
        deferred_ttl=None,
        coverage_target="leaf",
        facet="overview",
        kind="leaf",
        coverage_overview_injected=True,
        coverage_facets_injected=["overview"],
        coverage_pending_facets=[],
        coverage_family_context_available=False,
        coverage_injected_chunk_ids=injected_chunk_ids or [],
    )


# ---------------------------------------------------------------------------
# Test 1: Initial packet within budget (600-1000 tokens)
# ---------------------------------------------------------------------------


class TestInitialPacketWithinBudget:
    def test_initial_packet_budget_range(self) -> None:
        config = _default_config()
        results = [
            _make_result(
                "hooks#pretooluse",
                "PreToolUse runs before a tool call and can allow, block, or modify it. "
                "This hook is essential for controlling tool execution behavior.",
            ),
            _make_result(
                "hooks#posttooluse",
                "PostToolUse runs after a tool completes successfully. "
                "Use this hook to inspect tool results.",
            ),
        ]
        packet = build_packet(results, "initial", config)
        assert packet is not None
        assert packet.packet_kind == "initial"
        assert 0 < packet.token_estimate <= config.packets_initial_token_budget_max
        assert len(packet.facts) >= 1
        assert len(packet.facts) <= config.packets_initial_max_facts
        assert len(packet.topics) >= 1
        assert len(packet.topics) <= config.packets_initial_max_topics


# ---------------------------------------------------------------------------
# Test 2: Mid-turn packet within budget (250-450 tokens)
# ---------------------------------------------------------------------------


class TestMidTurnPacketWithinBudget:
    def test_mid_turn_packet_budget_range(self) -> None:
        config = _default_config()
        results = [
            _make_result(
                "hooks#posttooluse",
                "PostToolUse runs after a tool completes successfully.",
            ),
        ]
        packet = build_packet(results, "mid_turn", config)
        assert packet is not None
        assert packet.packet_kind == "mid_turn"
        assert 0 < packet.token_estimate <= config.packets_mid_turn_token_budget_max
        assert len(packet.facts) >= 1
        assert len(packet.facts) <= config.packets_mid_turn_max_facts
        assert len(packet.topics) >= 1
        assert len(packet.topics) <= config.packets_mid_turn_max_topics


# ---------------------------------------------------------------------------
# Test 3: Empty results -> no packet (return None)
# ---------------------------------------------------------------------------


class TestEmptyResults:
    def test_empty_list_returns_none(self) -> None:
        config = _default_config()
        assert build_packet([], "initial", config) is None

    def test_empty_list_mid_turn_returns_none(self) -> None:
        config = _default_config()
        assert build_packet([], "mid_turn", config) is None


# ---------------------------------------------------------------------------
# Test 4: Duplicate chunk IDs filtered (already-injected excluded)
# ---------------------------------------------------------------------------


class TestDuplicateChunkFiltering:
    def test_already_injected_chunks_excluded(self) -> None:
        config = _default_config()
        results = [
            _make_result("hooks#pretooluse", "PreToolUse runs before a tool call."),
            _make_result("hooks#posttooluse", "PostToolUse runs after a tool call."),
        ]
        registry = _make_registry_entry(
            injected_chunk_ids=["hooks#pretooluse"],
        )
        packet = build_packet(results, "initial", config, registry_entry=registry)
        assert packet is not None
        # Only the non-duplicate chunk should remain
        all_chunk_ids = [ref.chunk_id for f in packet.facts for ref in f.refs]
        assert "hooks#pretooluse" not in all_chunk_ids
        assert "hooks#posttooluse" in all_chunk_ids

    def test_all_chunks_duplicated_returns_none(self) -> None:
        config = _default_config()
        results = [
            _make_result("hooks#pretooluse", "PreToolUse runs before a tool call."),
        ]
        registry = _make_registry_entry(
            injected_chunk_ids=["hooks#pretooluse"],
        )
        packet = build_packet(results, "initial", config, registry_entry=registry)
        assert packet is None


# ---------------------------------------------------------------------------
# Test 5: Citation format — [ccdocs:<chunk_id>]
# ---------------------------------------------------------------------------


class TestCitationFormat:
    def test_citation_in_rendered_initial(self) -> None:
        config = _default_config()
        results = [
            _make_result(
                "hooks#pretooluse",
                "PreToolUse runs before a tool call and can allow, block, or modify it.",
            ),
        ]
        packet = build_packet(results, "initial", config)
        assert packet is not None
        rendered = render_initial(packet)
        assert "[ccdocs:hooks#pretooluse]" in rendered

    def test_citation_in_rendered_mid_turn(self) -> None:
        config = _default_config()
        results = [
            _make_result(
                "hooks#posttooluse",
                "PostToolUse runs after a tool completes successfully.",
            ),
        ]
        packet = build_packet(results, "mid_turn", config)
        assert packet is not None
        rendered = render_mid_turn(packet)
        assert "[ccdocs:hooks#posttooluse]" in rendered


# ---------------------------------------------------------------------------
# Test 6: Snippet mode for field names — exact identifiers use snippet
# ---------------------------------------------------------------------------


class TestSnippetMode:
    def test_backtick_content_uses_snippet_mode(self) -> None:
        config = _default_config()
        results = [
            _make_result(
                "hooks#fields",
                "`hookSpecificOutput.permissionDecision` controls allow/block/ask. "
                "`hookSpecificOutput.stderr` captures error output.",
                snippet="`hookSpecificOutput.permissionDecision`",
            ),
        ]
        packet = build_packet(results, "initial", config)
        assert packet is not None
        snippet_facts = [f for f in packet.facts if f.mode == "snippet"]
        assert len(snippet_facts) >= 1


# ---------------------------------------------------------------------------
# Test 7: Paraphrase mode for concepts — behavioral descriptions use paraphrase
# ---------------------------------------------------------------------------


class TestParaphraseMode:
    def test_conceptual_content_uses_paraphrase(self) -> None:
        config = _default_config()
        results = [
            _make_result(
                "hooks#behavior",
                "Hooks enable runtime customization of Claude Code behavior. "
                "They intercept tool calls at configurable points in the execution pipeline.",
            ),
        ]
        packet = build_packet(results, "initial", config)
        assert packet is not None
        paraphrase_facts = [f for f in packet.facts if f.mode == "paraphrase"]
        assert len(paraphrase_facts) >= 1


# ---------------------------------------------------------------------------
# Test 8: Too-large snippet truncated — graceful under budget pressure
# ---------------------------------------------------------------------------


class TestTooLargeSnippetTruncated:
    def test_large_content_fits_within_budget(self) -> None:
        config = _default_config()
        # Create a very long content that would exceed mid-turn budget
        long_content = (
            "`field_a` is required. " * 50
        )
        results = [
            _make_result("hooks#bigfield", long_content, snippet="field_a"),
        ]
        packet = build_packet(results, "mid_turn", config)
        # Should either return a truncated packet within budget or None
        if packet is not None:
            assert packet.token_estimate <= config.packets_mid_turn_token_budget_max


# ---------------------------------------------------------------------------
# Test 9: Budget boundary — N+1 facts where N fit
# Mid-turn with 4 facts where 3 fit (max_facts=3) -> output <= 3 facts,
# token_estimate <= 450
# ---------------------------------------------------------------------------


class TestBudgetBoundary:
    def test_mid_turn_four_results_three_max(self) -> None:
        config = _default_config()
        results = [
            _make_result(
                f"hooks#fact{i}",
                f"Fact number {i} about hook behavior.",
                score=0.9 - i * 0.01,
            )
            for i in range(4)
        ]
        packet = build_packet(results, "mid_turn", config)
        assert packet is not None
        assert len(packet.facts) <= config.packets_mid_turn_max_facts  # <= 3
        assert packet.token_estimate <= config.packets_mid_turn_token_budget_max  # <= 450


# ---------------------------------------------------------------------------
# Test 10: Quality threshold boundary
# score at 0.3 -> packet IS built; score 0.29 -> no packet
# ---------------------------------------------------------------------------


class TestQualityThreshold:
    def test_score_at_threshold_builds_packet(self) -> None:
        config = _default_config()
        results = [
            _make_result(
                "hooks#edge",
                "Hook edge case behavior.",
                score=0.3,
            ),
        ]
        packet = build_packet(results, "initial", config)
        assert packet is not None

    def test_score_below_threshold_returns_none(self) -> None:
        config = _default_config()
        results = [
            _make_result(
                "hooks#low",
                "Irrelevant low-scoring result.",
                score=0.29,
            ),
        ]
        packet = build_packet(results, "initial", config)
        assert packet is None


# ---------------------------------------------------------------------------
# Test 11: Mid-turn topics cardinality enforced
# 2 topics in results -> only 1 in output per mid_turn_max_topics
# ---------------------------------------------------------------------------


class TestMidTurnTopicCardinality:
    def test_mid_turn_limits_to_one_topic(self) -> None:
        config = _default_config()
        results = [
            _make_result(
                "hooks#pretooluse",
                "PreToolUse runs before a tool call.",
                category="hooks",
            ),
            _make_result(
                "mcp#servers",
                "MCP servers provide tool implementations.",
                category="mcp",
                source_file="https://code.claude.com/docs/en/mcp",
            ),
        ]
        packet = build_packet(results, "mid_turn", config)
        assert packet is not None
        # mid_turn_max_topics defaults to 1
        assert len(packet.topics) <= config.packets_mid_turn_max_topics


# ---------------------------------------------------------------------------
# Test 12: Mid-turn snippet cardinality — at most 1 snippet-mode fact
# ---------------------------------------------------------------------------


class TestMidTurnSnippetCardinality:
    def test_at_most_one_snippet_in_mid_turn(self) -> None:
        config = _default_config()
        results = [
            _make_result(
                "hooks#field1",
                "`hookSpecificOutput.permissionDecision` is the primary field.",
                snippet="`hookSpecificOutput.permissionDecision`",
            ),
            _make_result(
                "hooks#field2",
                "`hookSpecificOutput.stderr` captures error output.",
                snippet="`hookSpecificOutput.stderr`",
                score=0.84,
            ),
            _make_result(
                "hooks#field3",
                "`hookSpecificOutput.stdout` captures standard output.",
                snippet="`hookSpecificOutput.stdout`",
                score=0.83,
            ),
        ]
        packet = build_packet(results, "mid_turn", config)
        assert packet is not None
        snippet_count = sum(1 for f in packet.facts if f.mode == "snippet")
        assert snippet_count <= 1


# ---------------------------------------------------------------------------
# Test 13: No resolvable topic keys -> return None
# All results filtered -> return None
# ---------------------------------------------------------------------------


class TestNoResolvableTopics:
    def test_all_filtered_by_dedup_returns_none(self) -> None:
        config = _default_config()
        results = [
            _make_result("hooks#only", "Single result about hooks."),
        ]
        registry = _make_registry_entry(
            injected_chunk_ids=["hooks#only"],
        )
        packet = build_packet(results, "initial", config, registry_entry=registry)
        assert packet is None

    def test_all_below_quality_returns_none(self) -> None:
        config = _default_config()
        results = [
            _make_result("hooks#low1", "Low score result 1.", score=0.1),
            _make_result("hooks#low2", "Low score result 2.", score=0.2),
        ]
        packet = build_packet(results, "initial", config)
        assert packet is None


# ---------------------------------------------------------------------------
# Test 14: Chunk-ordering deterministic — same input twice -> identical sequence
# ---------------------------------------------------------------------------


class TestChunkOrderingDeterministic:
    def test_same_input_same_output(self) -> None:
        config = _default_config()
        results = [
            _make_result("hooks#b", "Second hook behavior.", score=0.85),
            _make_result("hooks#a", "First hook behavior.", score=0.85),
            _make_result("hooks#c", "Third hook behavior.", score=0.85),
        ]
        packet1 = build_packet(results, "initial", config)
        packet2 = build_packet(results, "initial", config)
        assert packet1 is not None
        assert packet2 is not None
        # Exact same fact sequence
        assert [f.text for f in packet1.facts] == [f.text for f in packet2.facts]
        # Tiebreaker: chunk_id ascending
        chunk_ids_1 = [ref.chunk_id for f in packet1.facts for ref in f.refs]
        chunk_ids_2 = [ref.chunk_id for f in packet2.facts for ref in f.refs]
        assert chunk_ids_1 == chunk_ids_2

    def test_tiebreaker_is_chunk_id_ascending(self) -> None:
        config = _default_config()
        results = [
            _make_result("hooks#z", "Z hook behavior.", score=0.85),
            _make_result("hooks#a", "A hook behavior.", score=0.85),
            _make_result("hooks#m", "M hook behavior.", score=0.85),
        ]
        packet = build_packet(results, "initial", config)
        assert packet is not None
        chunk_ids = [ref.chunk_id for f in packet.facts for ref in f.refs]
        assert chunk_ids == sorted(chunk_ids)


# ---------------------------------------------------------------------------
# Test 15: Paraphrase selection deterministic — same content twice -> identical
# ---------------------------------------------------------------------------


class TestParaphraseSelectionDeterministic:
    def test_same_content_same_paraphrase(self) -> None:
        config = _default_config()
        results = [
            _make_result(
                "hooks#behavior",
                "Hooks enable runtime customization. "
                "They intercept tool calls at configurable points. "
                "This provides fine-grained control over execution.",
            ),
        ]
        packet1 = build_packet(results, "initial", config)
        packet2 = build_packet(results, "initial", config)
        assert packet1 is not None
        assert packet2 is not None
        assert [f.text for f in packet1.facts] == [f.text for f in packet2.facts]


# ---------------------------------------------------------------------------
# Render tests
# ---------------------------------------------------------------------------


class TestRenderInitial:
    def test_header_and_topics(self) -> None:
        packet = FactPacket(
            packet_kind="initial",
            topics=["hooks.pre_tool_use", "hooks.post_tool_use"],
            facet="overview",
            facts=[
                FactItem(
                    mode="paraphrase",
                    facet="overview",
                    text="PreToolUse runs before a tool call and can allow, block, or modify it.",
                    refs=[DocRef("hooks#pretooluse", "hooks", "https://code.claude.com/docs/en/hooks")],
                ),
            ],
            token_estimate=50,
        )
        rendered = render_initial(packet)
        assert "### Claude Code Extension Reference" in rendered
        assert "hooks.pre_tool_use" in rendered
        assert "hooks.post_tool_use" in rendered
        assert "[ccdocs:hooks#pretooluse]" in rendered

    def test_render_order_paraphrase_before_snippet(self) -> None:
        packet = FactPacket(
            packet_kind="initial",
            topics=["hooks.pre_tool_use"],
            facet="overview",
            facts=[
                FactItem(
                    mode="snippet",
                    facet="schema",
                    text="`hookSpecificOutput.permissionDecision`",
                    refs=[DocRef("hooks#fields", "hooks", "https://code.claude.com/docs/en/hooks")],
                ),
                FactItem(
                    mode="paraphrase",
                    facet="overview",
                    text="PreToolUse runs before a tool call.",
                    refs=[DocRef("hooks#pretooluse", "hooks", "https://code.claude.com/docs/en/hooks")],
                ),
            ],
            token_estimate=80,
        )
        rendered = render_initial(packet)
        lines = rendered.strip().split("\n")
        # Find lines with citations to check order
        citation_lines = [line for line in lines if "[ccdocs:" in line]
        assert len(citation_lines) >= 2
        # Paraphrase fact should come before snippet fact
        para_idx = next(i for i, line in enumerate(lines) if "runs before" in line)
        snip_idx = next(i for i, line in enumerate(lines) if "permissionDecision" in line)
        assert para_idx < snip_idx


class TestRenderMidTurn:
    def test_metadata_comment(self) -> None:
        packet = FactPacket(
            packet_kind="mid_turn",
            topics=["hooks.post_tool_use"],
            facet="schema",
            facts=[
                FactItem(
                    mode="paraphrase",
                    facet="schema",
                    text="PostToolUse runs after a tool completes successfully.",
                    refs=[DocRef("hooks#posttooluse", "hooks", "https://code.claude.com/docs/en/hooks")],
                ),
            ],
            token_estimate=40,
        )
        rendered = render_mid_turn(packet)
        assert "<!-- ccdi-packet" in rendered
        assert 'topics="hooks.post_tool_use"' in rendered
        assert 'facet="schema"' in rendered
        assert "Claude Code docs context:" in rendered
        assert "[ccdocs:hooks#posttooluse]" in rendered
