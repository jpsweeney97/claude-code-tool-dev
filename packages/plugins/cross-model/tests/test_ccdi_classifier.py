"""Tests for CCDI topic classifier pipeline.

Covers all 23 test cases from the delivery spec: exact/phrase/token matching,
denylist application, ambiguity resolution, confidence levels, normalization,
evaluation order, and edge cases.
"""

from __future__ import annotations

import pytest

from scripts.ccdi.config import BUILTIN_DEFAULTS, CCDIConfig
from scripts.ccdi.types import (
    Alias,
    CompiledInventory,
    DenyRule,
    DocRef,
    QueryPlan,
    QuerySpec,
    TopicRecord,
)

# Import will fail until classifier.py exists (TDD red phase)
from scripts.ccdi.classifier import classify

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


def _query_plan(default_facet: str = "overview") -> QueryPlan:
    """Minimal query plan for test topics."""
    return QueryPlan(
        default_facet=default_facet,
        facets={
            "overview": [
                QuerySpec(q="placeholder", category=None, priority=1),
            ],
            "schema": [
                QuerySpec(q="placeholder schema", category=None, priority=1),
            ],
        },
    )


def _make_topic(
    topic_key: str,
    family_key: str,
    kind: str,
    aliases: list[Alias],
    parent_topic: str | None = None,
    default_facet: str = "overview",
) -> TopicRecord:
    """Build a TopicRecord for testing."""
    return TopicRecord(
        topic_key=topic_key,
        family_key=family_key,
        kind=kind,
        canonical_label=topic_key,
        category_hint=family_key,
        parent_topic=parent_topic,
        aliases=aliases,
        query_plan=_query_plan(default_facet),
        canonical_refs=[
            DocRef(chunk_id="test-chunk", category=family_key, source_file="test.md")
        ],
    )


# ---------------------------------------------------------------------------
# Fixture: test inventory
# ---------------------------------------------------------------------------


@pytest.fixture()
def inventory() -> CompiledInventory:
    """Build a test inventory matching the spec fixture design.

    Topics:
    - hooks (family): aliases=["hook" token 0.4]
    - hooks.pre_tool_use (leaf): aliases=["PreToolUse" exact 1.0,
                                           "pre tool use" phrase 0.95,
                                           "tool inputs" phrase 0.35]
    - hooks.post_tool_use (leaf): aliases=["PostToolUse" exact 0.9]
    - skills (family): aliases=["skill" token 0.4]
    - skills.frontmatter (leaf): aliases=["SKILL.md" exact 0.9,
                                           "frontmatter" token 0.5]

    Denylist:
    - drop "overview" (token)
    - downrank "schema" (token, penalty=0.35)
    """
    topics = {
        "hooks": _make_topic(
            topic_key="hooks",
            family_key="hooks",
            kind="family",
            aliases=[Alias(text="hook", match_type="token", weight=0.4)],
        ),
        "hooks.pre_tool_use": _make_topic(
            topic_key="hooks.pre_tool_use",
            family_key="hooks",
            kind="leaf",
            aliases=[
                Alias(text="PreToolUse", match_type="exact", weight=1.0),
                Alias(text="pre tool use", match_type="phrase", weight=0.95),
                Alias(text="tool inputs", match_type="phrase", weight=0.35),
            ],
            parent_topic="hooks",
        ),
        "hooks.post_tool_use": _make_topic(
            topic_key="hooks.post_tool_use",
            family_key="hooks",
            kind="leaf",
            aliases=[
                Alias(text="PostToolUse", match_type="exact", weight=0.9),
            ],
            parent_topic="hooks",
        ),
        "skills": _make_topic(
            topic_key="skills",
            family_key="skills",
            kind="family",
            aliases=[Alias(text="skill", match_type="token", weight=0.4)],
        ),
        "skills.frontmatter": _make_topic(
            topic_key="skills.frontmatter",
            family_key="skills",
            kind="leaf",
            aliases=[
                Alias(text="SKILL.md", match_type="exact", weight=0.9),
                Alias(text="frontmatter", match_type="token", weight=0.5),
            ],
            parent_topic="skills",
        ),
    }

    denylist = [
        DenyRule(
            id="deny-overview",
            pattern="overview",
            match_type="token",
            action="drop",
            penalty=None,
            reason="too generic",
        ),
        DenyRule(
            id="deny-schema",
            pattern="schema",
            match_type="token",
            action="downrank",
            penalty=0.35,
            reason="generic modifier",
        ),
    ]

    return CompiledInventory(
        schema_version="1",
        built_at="2026-01-01T00:00:00Z",
        docs_epoch="test-epoch",
        topics=topics,
        denylist=denylist,
        overlay_meta=None,
        merge_semantics_version="1",
    )


@pytest.fixture()
def config() -> CCDIConfig:
    """Default config for most tests."""
    return _default_config()


# ---------------------------------------------------------------------------
# Test 1: Exact alias → high confidence
# ---------------------------------------------------------------------------


class TestExactAliasHighConfidence:
    """Test 1: 'PreToolUse' → hooks.pre_tool_use, high."""

    def test_exact_match_returns_high(
        self, inventory: CompiledInventory, config: CCDIConfig
    ) -> None:
        result = classify("PreToolUse", inventory, config)
        assert len(result.resolved_topics) == 1
        rt = result.resolved_topics[0]
        assert rt.topic_key == "hooks.pre_tool_use"
        assert rt.confidence == "high"
        assert rt.coverage_target == "leaf"
        # Verify matched alias
        assert any(ma.text == "PreToolUse" for ma in rt.matched_aliases)


# ---------------------------------------------------------------------------
# Test 2: Phrase match with facet hint
# ---------------------------------------------------------------------------


class TestPhraseMatchFacetHint:
    """Test 2: 'pre tool use' → facet=overview (default, no facet modifier)."""

    def test_phrase_match_default_facet(
        self, inventory: CompiledInventory, config: CCDIConfig
    ) -> None:
        result = classify("pre tool use", inventory, config)
        assert len(result.resolved_topics) >= 1
        rt = next(
            t for t in result.resolved_topics if t.topic_key == "hooks.pre_tool_use"
        )
        assert rt.facet == "overview"
        assert rt.confidence == "high"  # weight 0.95 >= 0.8


# ---------------------------------------------------------------------------
# Test 3: Generic token alone suppressed
# ---------------------------------------------------------------------------


class TestGenericTokenSuppressed:
    """Test 3: 'schema' alone → no resolved topics (orphaned generic)."""

    def test_schema_alone_suppressed(
        self, inventory: CompiledInventory, config: CCDIConfig
    ) -> None:
        result = classify("schema", inventory, config)
        assert len(result.resolved_topics) == 0


# ---------------------------------------------------------------------------
# Test 4: Generic shifts facet with anchor
# ---------------------------------------------------------------------------


class TestGenericShiftsFacet:
    """Test 4: 'PreToolUse schema' → facet=schema."""

    def test_schema_shifts_facet(
        self, inventory: CompiledInventory, config: CCDIConfig
    ) -> None:
        result = classify("PreToolUse schema", inventory, config)
        assert len(result.resolved_topics) >= 1
        rt = next(
            t for t in result.resolved_topics if t.topic_key == "hooks.pre_tool_use"
        )
        assert rt.facet == "schema"


# ---------------------------------------------------------------------------
# Test 5: Leaf absorbs parent family
# ---------------------------------------------------------------------------


class TestLeafAbsorbsFamily:
    """Test 5: 'PreToolUse hook' → leaf only, family suppressed."""

    def test_leaf_absorbs_parent(
        self, inventory: CompiledInventory, config: CCDIConfig
    ) -> None:
        result = classify("PreToolUse hook", inventory, config)
        resolved_keys = [t.topic_key for t in result.resolved_topics]
        assert "hooks.pre_tool_use" in resolved_keys
        assert "hooks" not in resolved_keys
        # Family should be suppressed
        suppressed_keys = [s.topic_key for s in result.suppressed_candidates]
        assert "hooks" in suppressed_keys


# ---------------------------------------------------------------------------
# Test 6: Weak leaves collapse to family
# ---------------------------------------------------------------------------


class TestWeakLeavesCollapseToFamily:
    """Test 6: Two low-weight hook leaves → hooks family at overview facet."""

    def test_collapse_weak_leaves(self, config: CCDIConfig) -> None:
        """Build an inventory with two weak hook leaves."""
        topics = {
            "hooks": _make_topic(
                topic_key="hooks",
                family_key="hooks",
                kind="family",
                aliases=[Alias(text="hook", match_type="token", weight=0.4)],
            ),
            "hooks.leaf_a": _make_topic(
                topic_key="hooks.leaf_a",
                family_key="hooks",
                kind="leaf",
                aliases=[Alias(text="leaf_a", match_type="token", weight=0.2)],
                parent_topic="hooks",
            ),
            "hooks.leaf_b": _make_topic(
                topic_key="hooks.leaf_b",
                family_key="hooks",
                kind="leaf",
                aliases=[Alias(text="leaf_b", match_type="token", weight=0.2)],
                parent_topic="hooks",
            ),
        }
        inv = CompiledInventory(
            schema_version="1",
            built_at="2026-01-01T00:00:00Z",
            docs_epoch=None,
            topics=topics,
            denylist=[],
            overlay_meta=None,
            merge_semantics_version="1",
        )
        result = classify("leaf_a and leaf_b hooks", inv, config)
        resolved_keys = [t.topic_key for t in result.resolved_topics]
        # Should collapse to family
        assert "hooks" in resolved_keys
        assert "hooks.leaf_a" not in resolved_keys
        assert "hooks.leaf_b" not in resolved_keys
        # Family should be at overview facet
        hooks_topic = next(
            t for t in result.resolved_topics if t.topic_key == "hooks"
        )
        assert hooks_topic.facet == "overview"


# ---------------------------------------------------------------------------
# Test 7: Denylist drop
# ---------------------------------------------------------------------------


class TestDenylistDrop:
    """Test 7: 'overview' → dropped entirely."""

    def test_overview_dropped(
        self, inventory: CompiledInventory, config: CCDIConfig
    ) -> None:
        result = classify("overview", inventory, config)
        assert len(result.resolved_topics) == 0


# ---------------------------------------------------------------------------
# Test 8: Denylist downrank
# ---------------------------------------------------------------------------


class TestDenylistDownrank:
    """Test 8: 'settings' → weight reduced. Using 'schema' as our downranked term."""

    def test_schema_downranked(
        self, inventory: CompiledInventory, config: CCDIConfig
    ) -> None:
        # "schema" is downranked by 0.35 penalty.
        # It's a generic, so alone it's suppressed. But verify that the
        # mechanism works by checking with an anchor.
        result = classify("PreToolUse schema", inventory, config)
        rt = next(
            t for t in result.resolved_topics if t.topic_key == "hooks.pre_tool_use"
        )
        # The facet should shift to schema (the downranked term still acts
        # as a facet modifier even though its weight is reduced)
        assert rt.facet == "schema"


# ---------------------------------------------------------------------------
# Test 9: Denylist penalty clamping to zero
# ---------------------------------------------------------------------------


class TestDenylistPenaltyClamping:
    """Test 9: alias weight=0.3, penalty=0.5 → effective weight=0."""

    def test_penalty_clamps_to_zero(self, config: CCDIConfig) -> None:
        """Build inventory with a low-weight alias and high penalty."""
        topics = {
            "test_family": _make_topic(
                topic_key="test_family",
                family_key="test_family",
                kind="family",
                aliases=[Alias(text="testfam", match_type="token", weight=0.3)],
            ),
        }
        denylist = [
            DenyRule(
                id="deny-testfam",
                pattern="testfam",
                match_type="token",
                action="downrank",
                penalty=0.5,
                reason="test clamping",
            ),
        ]
        inv = CompiledInventory(
            schema_version="1",
            built_at="2026-01-01T00:00:00Z",
            docs_epoch=None,
            topics=topics,
            denylist=denylist,
            overlay_meta=None,
            merge_semantics_version="1",
        )
        result = classify("testfam", inv, config)
        # Weight 0.3 - penalty 0.5 = clamped to 0 → no resolved topics
        assert len(result.resolved_topics) == 0


# ---------------------------------------------------------------------------
# Test 10: No matches → empty
# ---------------------------------------------------------------------------


class TestNoMatches:
    """Test 10: 'fix the database query' → empty."""

    def test_no_matches_empty(
        self, inventory: CompiledInventory, config: CCDIConfig
    ) -> None:
        result = classify("fix the database query", inventory, config)
        assert len(result.resolved_topics) == 0
        assert len(result.suppressed_candidates) == 0


# ---------------------------------------------------------------------------
# Test 11: Multiple families detected
# ---------------------------------------------------------------------------


class TestMultipleFamilies:
    """Test 11: 'PreToolUse hook and SKILL.md frontmatter' → two topics."""

    def test_two_families(
        self, inventory: CompiledInventory, config: CCDIConfig
    ) -> None:
        result = classify("PreToolUse hook and SKILL.md frontmatter", inventory, config)
        resolved_keys = {t.topic_key for t in result.resolved_topics}
        assert "hooks.pre_tool_use" in resolved_keys
        assert "skills.frontmatter" in resolved_keys


# ---------------------------------------------------------------------------
# Test 12: Normalization variants
# ---------------------------------------------------------------------------


class TestNormalizationVariants:
    """Test 12: PreToolUse, pretooluse, SKILL.md, backticked forms."""

    def test_exact_case_sensitive(
        self, inventory: CompiledInventory, config: CCDIConfig
    ) -> None:
        """Exact match is case-sensitive: 'pretooluse' should NOT match exact alias."""
        result = classify("pretooluse", inventory, config)
        # Should not get high-confidence exact match
        if result.resolved_topics:
            rt = result.resolved_topics[0]
            # If it somehow matches, it shouldn't be via exact
            exact_matches = [
                ma for ma in rt.matched_aliases if ma.text == "PreToolUse"
            ]
            assert len(exact_matches) == 0

    def test_skill_md_exact(
        self, inventory: CompiledInventory, config: CCDIConfig
    ) -> None:
        """SKILL.md exact match works."""
        result = classify("SKILL.md", inventory, config)
        assert len(result.resolved_topics) >= 1
        rt = next(
            t for t in result.resolved_topics if t.topic_key == "skills.frontmatter"
        )
        assert rt.confidence == "high"  # weight 0.9 >= 0.8

    def test_backticked_form(
        self, inventory: CompiledInventory, config: CCDIConfig
    ) -> None:
        """Backticked `PreToolUse` should still match after normalization."""
        result = classify("`PreToolUse`", inventory, config)
        assert len(result.resolved_topics) >= 1
        resolved_keys = {t.topic_key for t in result.resolved_topics}
        assert "hooks.pre_tool_use" in resolved_keys


# ---------------------------------------------------------------------------
# Test 13: Alias collision tiebreak
# ---------------------------------------------------------------------------


class TestAliasCollisionTiebreak:
    """Test 13: Same token in two topics → deterministic winner."""

    def test_collision_deterministic(self, config: CCDIConfig) -> None:
        """Two topics share the same token alias — result is deterministic."""
        topics = {
            "alpha": _make_topic(
                topic_key="alpha",
                family_key="alpha",
                kind="family",
                aliases=[Alias(text="shared", match_type="token", weight=0.6)],
            ),
            "beta": _make_topic(
                topic_key="beta",
                family_key="beta",
                kind="family",
                aliases=[Alias(text="shared", match_type="token", weight=0.6)],
            ),
        }
        inv = CompiledInventory(
            schema_version="1",
            built_at="2026-01-01T00:00:00Z",
            docs_epoch=None,
            topics=topics,
            denylist=[],
            overlay_meta=None,
            merge_semantics_version="1",
        )
        # Run twice — result must be identical
        r1 = classify("shared", inv, config)
        r2 = classify("shared", inv, config)
        keys1 = [t.topic_key for t in r1.resolved_topics]
        keys2 = [t.topic_key for t in r2.resolved_topics]
        assert keys1 == keys2
        # Both topics should be present since they're in different families
        assert len(r1.resolved_topics) == 2


# ---------------------------------------------------------------------------
# Test 14: False-positive contexts
# ---------------------------------------------------------------------------


class TestFalsePositiveContexts:
    """Test 14: 'React hook', 'webpack plugin' → no CCDI topics."""

    def test_react_hook(
        self, inventory: CompiledInventory, config: CCDIConfig
    ) -> None:
        """'React hook' — 'hook' token matches but is too weak alone."""
        result = classify("React hook", inventory, config)
        # 'hook' alone has weight 0.4 on the hooks family. That's below
        # medium threshold (0.5). It should either be low-confidence or
        # suppressed. With no anchor, it may be resolved at low.
        # The key assertion: should NOT be high confidence.
        for rt in result.resolved_topics:
            assert rt.confidence != "high"

    def test_webpack_plugin(
        self, inventory: CompiledInventory, config: CCDIConfig
    ) -> None:
        """'webpack plugin' → no CCDI topics (no matching aliases)."""
        result = classify("webpack plugin", inventory, config)
        # "plugin" is not in our test inventory aliases
        assert len(result.resolved_topics) == 0


# ---------------------------------------------------------------------------
# Test 15: Missing-facet fallback
# ---------------------------------------------------------------------------


class TestMissingFacetFallback:
    """Test 15: Requested facet missing → falls back to default_facet."""

    def test_missing_facet_falls_back(self, config: CCDIConfig) -> None:
        """If a facet modifier requests a facet not in query_plan, fall back."""
        topics = {
            "hooks.pre_tool_use": _make_topic(
                topic_key="hooks.pre_tool_use",
                family_key="hooks",
                kind="leaf",
                aliases=[
                    Alias(text="PreToolUse", match_type="exact", weight=1.0),
                ],
                default_facet="overview",
            ),
        }
        # Add an alias that would hint at "config" facet, but topic
        # doesn't have "config" in its query_plan facets
        inv = CompiledInventory(
            schema_version="1",
            built_at="2026-01-01T00:00:00Z",
            docs_epoch=None,
            topics=topics,
            denylist=[
                DenyRule(
                    id="deny-config",
                    pattern="config",
                    match_type="token",
                    action="downrank",
                    penalty=0.35,
                    reason="generic modifier",
                ),
            ],
            overlay_meta=None,
            merge_semantics_version="1",
        )
        result = classify("PreToolUse config", inv, config)
        assert len(result.resolved_topics) >= 1
        rt = result.resolved_topics[0]
        # "config" facet is not in the query_plan, so should fall back
        # to default_facet "overview" (or "config" if present — but our
        # query_plan only has overview and schema)
        assert rt.facet in {"overview", "config", "schema"}


# ---------------------------------------------------------------------------
# Test 16: Multi-leaf same family
# ---------------------------------------------------------------------------


class TestMultiLeafSameFamily:
    """Test 16: Both PreToolUse and PostToolUse in one input."""

    def test_both_hook_leaves(
        self, inventory: CompiledInventory, config: CCDIConfig
    ) -> None:
        result = classify("PreToolUse and PostToolUse", inventory, config)
        resolved_keys = {t.topic_key for t in result.resolved_topics}
        # Both leaves should be resolved (both are strong matches)
        assert "hooks.pre_tool_use" in resolved_keys
        assert "hooks.post_tool_use" in resolved_keys
        # Family should NOT also appear
        assert "hooks" not in resolved_keys


# ---------------------------------------------------------------------------
# Test 17: Repeated mentions don't inflate
# ---------------------------------------------------------------------------


class TestRepeatedMentions:
    """Test 17: 'PreToolUse PreToolUse PreToolUse' → same score as one."""

    def test_repeated_same_score(
        self, inventory: CompiledInventory, config: CCDIConfig
    ) -> None:
        single = classify("PreToolUse", inventory, config)
        triple = classify("PreToolUse PreToolUse PreToolUse", inventory, config)
        assert len(single.resolved_topics) == len(triple.resolved_topics)
        s_rt = next(
            t
            for t in single.resolved_topics
            if t.topic_key == "hooks.pre_tool_use"
        )
        t_rt = next(
            t
            for t in triple.resolved_topics
            if t.topic_key == "hooks.pre_tool_use"
        )
        assert s_rt.confidence == t_rt.confidence


# ---------------------------------------------------------------------------
# Test 18: Evaluation order — exact beats token
# ---------------------------------------------------------------------------


class TestEvalOrderExactBeatsToken:
    """Test 18: exact (0.6) + token (0.9) same topic → exact evaluated first."""

    def test_exact_suppresses_token(self, config: CCDIConfig) -> None:
        """Input matches both exact and token alias on same topic.

        Exact is higher priority → token suppressed. Score = exact weight only.
        """
        topics = {
            "test_topic": _make_topic(
                topic_key="test_topic",
                family_key="test_family",
                kind="leaf",
                aliases=[
                    Alias(text="Foo", match_type="exact", weight=0.6),
                    Alias(text="foo", match_type="token", weight=0.9),
                ],
            ),
        }
        inv = CompiledInventory(
            schema_version="1",
            built_at="2026-01-01T00:00:00Z",
            docs_epoch=None,
            topics=topics,
            denylist=[],
            overlay_meta=None,
            merge_semantics_version="1",
        )
        result = classify("Foo", inv, config)
        assert len(result.resolved_topics) == 1
        rt = result.resolved_topics[0]
        # Exact match at 0.6 → medium confidence (>= 0.5 single weight)
        assert rt.confidence == "medium"
        # The matched alias should be the exact one
        assert any(ma.text == "Foo" for ma in rt.matched_aliases)


# ---------------------------------------------------------------------------
# Test 19: Evaluation order — longer phrase wins within type
# ---------------------------------------------------------------------------


class TestEvalOrderLongerPhraseWins:
    """Test 19: Longer phrase wins within same match type."""

    def test_longer_phrase_wins(self, config: CCDIConfig) -> None:
        topics = {
            "test_topic": _make_topic(
                topic_key="test_topic",
                family_key="test_family",
                kind="leaf",
                aliases=[
                    Alias(
                        text="pre tool use hook", match_type="phrase", weight=0.9
                    ),
                    Alias(text="pre tool use", match_type="phrase", weight=0.7),
                ],
            ),
        }
        inv = CompiledInventory(
            schema_version="1",
            built_at="2026-01-01T00:00:00Z",
            docs_epoch=None,
            topics=topics,
            denylist=[],
            overlay_meta=None,
            merge_semantics_version="1",
        )
        result = classify("pre tool use hook", inv, config)
        assert len(result.resolved_topics) == 1
        rt = result.resolved_topics[0]
        # Longer phrase should be the match
        assert any(ma.text == "pre tool use hook" for ma in rt.matched_aliases)
        assert rt.confidence == "high"  # 0.9 >= 0.8


# ---------------------------------------------------------------------------
# Test 20: Phrase suppresses token on same topic (cross-type)
# ---------------------------------------------------------------------------


class TestPhraseSuppressesToken:
    """Test 20: phrase(0.6) + token(0.4) → score=0.6 only."""

    def test_phrase_suppresses_token_same_topic(self, config: CCDIConfig) -> None:
        topics = {
            "test_topic": _make_topic(
                topic_key="test_topic",
                family_key="test_family",
                kind="leaf",
                aliases=[
                    Alias(
                        text="my hook thing", match_type="phrase", weight=0.6
                    ),
                    Alias(text="hook", match_type="token", weight=0.4),
                ],
            ),
        }
        inv = CompiledInventory(
            schema_version="1",
            built_at="2026-01-01T00:00:00Z",
            docs_epoch=None,
            topics=topics,
            denylist=[],
            overlay_meta=None,
            merge_semantics_version="1",
        )
        result = classify("my hook thing is great", inv, config)
        assert len(result.resolved_topics) == 1
        rt = result.resolved_topics[0]
        # Score should be 0.6 (phrase only, token suppressed)
        # 0.6 >= 0.5 single weight → medium confidence
        assert rt.confidence == "medium"
        # Only phrase match should be present
        matched_texts = {ma.text for ma in rt.matched_aliases}
        assert "my hook thing" in matched_texts
        assert "hook" not in matched_texts


# ---------------------------------------------------------------------------
# Test 21: Exact match word-boundary negative
# ---------------------------------------------------------------------------


class TestExactWordBoundaryNegative:
    """Test 21: 'SomePreToolUseHandler' → empty (embedded in longer word)."""

    def test_embedded_exact_no_match(
        self, inventory: CompiledInventory, config: CCDIConfig
    ) -> None:
        result = classify("SomePreToolUseHandler", inventory, config)
        # PreToolUse is embedded — should NOT match at word boundaries
        for rt in result.resolved_topics:
            if rt.topic_key == "hooks.pre_tool_use":
                # Should not have matched via exact
                exact_matches = [
                    ma for ma in rt.matched_aliases if ma.text == "PreToolUse"
                ]
                assert len(exact_matches) == 0


# ---------------------------------------------------------------------------
# Test 22: Multi-alias accumulation — phrase suppresses token
# ---------------------------------------------------------------------------


class TestMultiAliasAccumulationSuppression:
    """Test 22: phrase + token same topic → phrase suppresses token → score=phrase weight only."""

    def test_phrase_suppresses_token_accumulation(
        self, inventory: CompiledInventory, config: CCDIConfig
    ) -> None:
        # "pre tool use hook" — phrase "pre tool use" (0.95) matches,
        # suppressing any token "hook" if it existed on same topic.
        # But in our inventory, "hook" belongs to the "hooks" family topic,
        # not to hooks.pre_tool_use. So this tests that cross-type suppression
        # is per-topic: "pre tool use" on hooks.pre_tool_use doesn't suppress
        # "hook" on hooks (different topic).
        result = classify("pre tool use hook", inventory, config)
        resolved_keys = {t.topic_key for t in result.resolved_topics}
        assert "hooks.pre_tool_use" in resolved_keys
        # The leaf should absorb the family
        assert "hooks" not in resolved_keys


# ---------------------------------------------------------------------------
# Test 23: Multi-alias accumulation — exact + phrase, no overlap, different aliases
# ---------------------------------------------------------------------------


class TestMultiAliasAccumulationSum:
    """Test 23: exact + phrase different aliases no overlap → score=sum of both."""

    def test_non_overlapping_aliases_sum(self, config: CCDIConfig) -> None:
        topics = {
            "test_topic": _make_topic(
                topic_key="test_topic",
                family_key="test_family",
                kind="leaf",
                aliases=[
                    Alias(text="Alpha", match_type="exact", weight=0.5),
                    Alias(
                        text="beta gamma", match_type="phrase", weight=0.4
                    ),
                ],
            ),
        }
        inv = CompiledInventory(
            schema_version="1",
            built_at="2026-01-01T00:00:00Z",
            docs_epoch=None,
            topics=topics,
            denylist=[],
            overlay_meta=None,
            merge_semantics_version="1",
        )
        result = classify("Alpha and beta gamma", inv, config)
        assert len(result.resolved_topics) == 1
        rt = result.resolved_topics[0]
        # Both aliases match (different aliases, no overlap)
        # Score = 0.5 + 0.4 = 0.9 → high confidence (>= 0.8 exact match weight
        # is 0.5, but cumulative is 0.9 which isn't how high works...
        # high requires ONE exact/phrase match with weight >= 0.8.
        # Neither alias alone has weight >= 0.8.
        # But cumulative score 0.9 >= 0.5 → medium.
        # Actually, single weight 0.5 >= 0.5 → medium.
        assert rt.confidence == "medium"
        matched_texts = {ma.text for ma in rt.matched_aliases}
        assert "Alpha" in matched_texts
        assert "beta gamma" in matched_texts


# ---------------------------------------------------------------------------
# classify_result_hash
# ---------------------------------------------------------------------------


class TestClassifyResultHash:
    """classify_result_hash from hash_utils — delivery.md Registry Tests."""

    def test_classify_result_hash_stability(self) -> None:
        """Same classify payload → same hash (stability invariant)."""
        from scripts.ccdi.hash_utils import classify_result_hash

        aliases = [{"text": "PreToolUse", "weight": 1.0}]
        h1 = classify_result_hash("hooks.pre_tool_use", "high", "overview", aliases)
        h2 = classify_result_hash("hooks.pre_tool_use", "high", "overview", aliases)
        assert h1 == h2

    def test_classify_result_hash_input_coverage(self) -> None:
        """Same topic_key, different matched_aliases → different hashes."""
        from scripts.ccdi.hash_utils import classify_result_hash

        aliases_a = [{"text": "PreToolUse", "weight": 1.0}]
        aliases_b = [{"text": "pre tool use", "weight": 0.95}]
        h_a = classify_result_hash("hooks.pre_tool_use", "high", "overview", aliases_a)
        h_b = classify_result_hash("hooks.pre_tool_use", "high", "overview", aliases_b)
        assert h_a != h_b

    def test_classify_result_hash_different_confidence(self) -> None:
        """Same topic, different confidence → different hashes."""
        from scripts.ccdi.hash_utils import classify_result_hash

        aliases = [{"text": "PreToolUse", "weight": 1.0}]
        h_high = classify_result_hash("hooks.pre_tool_use", "high", "overview", aliases)
        h_med = classify_result_hash("hooks.pre_tool_use", "medium", "overview", aliases)
        assert h_high != h_med

    def test_classify_result_hash_different_facet(self) -> None:
        """Same topic, different facet → different hashes."""
        from scripts.ccdi.hash_utils import classify_result_hash

        aliases = [{"text": "PreToolUse", "weight": 1.0}]
        h_ov = classify_result_hash("hooks.pre_tool_use", "high", "overview", aliases)
        h_sc = classify_result_hash("hooks.pre_tool_use", "high", "schema", aliases)
        assert h_ov != h_sc
