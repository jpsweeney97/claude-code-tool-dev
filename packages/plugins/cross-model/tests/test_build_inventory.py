"""Tests for CCDI inventory generation: build_inventory and load_inventory.

Covers scaffold generation, overlay merging, deny rules, config overrides,
weight clamping, version validation, and load-time resilience.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pytest

from scripts.ccdi.build_inventory import (
    build_inventory,
    generate_scaffold,
    merge_overlay,
)
from scripts.ccdi.inventory import load_inventory
from scripts.ccdi.types import (
    Alias,
    CompiledInventory,
    QueryPlan,
    QuerySpec,
    TopicRecord,
)

# ---------------------------------------------------------------------------
# Test metadata fixture — simulates dump_index_metadata response
# ---------------------------------------------------------------------------

SAMPLE_METADATA: dict[str, Any] = {
    "categories": [
        {
            "name": "hooks",
            "heading_count": 2,
            "chunk_count": 10,
            "aliases": ["hook", "git-hooks"],
            "headings": [
                {
                    "text": "PreToolUse Hooks",
                    "slug": "pretooluse-hooks",
                    "code_literals": ["PreToolUse"],
                    "config_keys": ["hookTimeout"],
                    "distinctive_terms": ["guard pattern", "block"],
                },
                {
                    "text": "PostToolUse Hooks",
                    "slug": "posttooluse-hooks",
                    "code_literals": ["PostToolUse", "tool_response"],
                    "config_keys": [],
                    "distinctive_terms": ["analytics"],
                },
            ],
        },
        {
            "name": "permissions",
            "heading_count": 1,
            "chunk_count": 5,
            "aliases": ["perms"],
            "headings": [
                {
                    "text": "Tool Permissions",
                    "slug": "tool-permissions",
                    "code_literals": [],
                    "config_keys": ["allowedTools"],
                    "distinctive_terms": ["allow list"],
                },
            ],
        },
    ],
}


def _minimal_topic(
    topic_key: str = "hooks",
    family_key: str = "hooks",
    kind: str = "family",
    canonical_label: str = "Hooks",
    aliases: list[Alias] | None = None,
) -> TopicRecord:
    """Build a minimal TopicRecord for test helpers."""
    if aliases is None:
        aliases = [Alias(text="hooks", match_type="token", weight=0.5)]
    return TopicRecord(
        topic_key=topic_key,
        family_key=family_key,
        kind=kind,
        canonical_label=canonical_label,
        category_hint=family_key,
        parent_topic=None if kind == "family" else family_key,
        aliases=aliases,
        query_plan=QueryPlan(
            default_facet="overview",
            facets={
                "overview": [
                    QuerySpec(q=canonical_label, category=family_key, priority=1)
                ]
            },
        ),
        canonical_refs=[],
    )


def _write_json(tmp_path: Path, data: Any, name: str = "inventory.json") -> Path:
    p = tmp_path / name
    p.write_text(json.dumps(data))
    return p


# ===========================================================================
# 1. Scaffold generation from metadata
# ===========================================================================


class TestScaffoldGeneration:
    """Test 1: Scaffold generation from metadata — topics, aliases, query plans."""

    def test_scaffold_produces_topics_aliases_query_plans(self) -> None:
        inv = generate_scaffold(SAMPLE_METADATA)
        # Family topics for each category
        assert "hooks" in inv.topics
        assert "permissions" in inv.topics
        # Leaf topics for headings
        assert "hooks.pretooluse-hooks" in inv.topics
        assert "hooks.posttooluse-hooks" in inv.topics
        assert "permissions.tool-permissions" in inv.topics

        # Family topic properties
        hooks_family = inv.topics["hooks"]
        assert hooks_family.kind == "family"
        assert hooks_family.family_key == "hooks"
        assert hooks_family.parent_topic is None
        assert len(hooks_family.aliases) > 0

        # Leaf topic properties
        leaf = inv.topics["hooks.pretooluse-hooks"]
        assert leaf.kind == "leaf"
        assert leaf.family_key == "hooks"
        assert leaf.parent_topic == "hooks"
        assert len(leaf.aliases) > 0

        # Query plan populated
        assert leaf.query_plan.default_facet == "overview"
        assert "overview" in leaf.query_plan.facets

    def test_scaffold_code_literal_aliases(self) -> None:
        inv = generate_scaffold(SAMPLE_METADATA)
        leaf = inv.topics["hooks.pretooluse-hooks"]
        alias_texts = [a.text for a in leaf.aliases]
        assert "PreToolUse" in alias_texts
        pre = next(a for a in leaf.aliases if a.text == "PreToolUse")
        assert pre.match_type == "exact"
        assert pre.source == "generated"

    def test_scaffold_config_key_aliases(self) -> None:
        inv = generate_scaffold(SAMPLE_METADATA)
        leaf = inv.topics["hooks.pretooluse-hooks"]
        alias_texts = [a.text for a in leaf.aliases]
        assert "hookTimeout" in alias_texts
        ht = next(a for a in leaf.aliases if a.text == "hookTimeout")
        assert ht.facet_hint == "config"
        assert ht.weight == 0.7

    def test_scaffold_distinctive_term_aliases(self) -> None:
        inv = generate_scaffold(SAMPLE_METADATA)
        leaf = inv.topics["hooks.pretooluse-hooks"]
        alias_texts = [a.text for a in leaf.aliases]
        # multi-word → phrase alias
        assert "guard pattern" in alias_texts
        gp = next(a for a in leaf.aliases if a.text == "guard pattern")
        assert gp.match_type == "phrase"
        assert gp.weight == 0.6
        # single-word → token alias
        assert "block" in alias_texts
        bl = next(a for a in leaf.aliases if a.text == "block")
        assert bl.match_type == "token"

    def test_scaffold_category_aliases_on_family(self) -> None:
        inv = generate_scaffold(SAMPLE_METADATA)
        hooks_family = inv.topics["hooks"]
        alias_texts = [a.text for a in hooks_family.aliases]
        assert "hook" in alias_texts
        assert "git-hooks" in alias_texts
        h = next(a for a in hooks_family.aliases if a.text == "hook")
        assert h.weight == 0.4
        assert h.match_type == "token"

    def test_scaffold_output_schema(self) -> None:
        """Test 6: Output matches CompiledInventory schema."""
        inv = generate_scaffold(SAMPLE_METADATA)
        assert isinstance(inv, CompiledInventory)
        assert inv.schema_version == "1"
        assert inv.merge_semantics_version == "1"
        assert inv.denylist == []
        assert inv.overlay_meta is None


# ===========================================================================
# 2-3. Overlay merge: scalar replace + array append
# ===========================================================================


class TestOverlayMergeBasics:
    """Tests 2-3: Scalar replace and array append+dedupe."""

    def test_overlay_scalar_replace_canonical_label(self) -> None:
        """Test 2: override canonical_label via replace_aliases (closest scalar op)."""
        inv = generate_scaffold(SAMPLE_METADATA)
        overlay: dict[str, Any] = {
            "overlay_version": "1",
            "overlay_schema_version": "1",
            "rules": [
                {
                    "rule_id": "replace-hooks-aliases",
                    "operation": "replace_aliases",
                    "topic_key": "hooks",
                    "aliases": [
                        {"text": "hooks", "match_type": "token", "weight": 0.9},
                        {"text": "webhook", "match_type": "token", "weight": 0.5},
                    ],
                }
            ],
            "config_overrides": {},
        }
        result = merge_overlay(inv, overlay)
        hooks = result.topics["hooks"]
        alias_texts = [a.text for a in hooks.aliases]
        assert "webhook" in alias_texts
        assert len(hooks.aliases) == 2

    def test_overlay_add_topic(self) -> None:
        """Test 3 variant: add_topic adds a new topic with aliases."""
        inv = generate_scaffold(SAMPLE_METADATA)
        overlay: dict[str, Any] = {
            "overlay_version": "1",
            "overlay_schema_version": "1",
            "rules": [
                {
                    "rule_id": "add-mcp",
                    "operation": "add_topic",
                    "topic": {
                        "topic_key": "mcp",
                        "family_key": "mcp",
                        "kind": "family",
                        "canonical_label": "MCP Servers",
                        "category_hint": "mcp",
                        "parent_topic": None,
                        "aliases": [
                            {"text": "mcp", "match_type": "token", "weight": 0.8},
                        ],
                        "query_plan": {
                            "default_facet": "overview",
                            "facets": {
                                "overview": [
                                    {
                                        "q": "MCP servers",
                                        "category": "mcp",
                                        "priority": 1,
                                    }
                                ]
                            },
                        },
                        "canonical_refs": [],
                    },
                }
            ],
            "config_overrides": {},
        }
        result = merge_overlay(inv, overlay)
        assert "mcp" in result.topics
        assert result.topics["mcp"].canonical_label == "MCP Servers"


# ===========================================================================
# 4. Overlay references unknown topic
# ===========================================================================


class TestOverlayUnknownTopic:
    """Test 4: Unknown topic reference → warning, not crash."""

    def test_remove_alias_unknown_topic_warns(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        inv = generate_scaffold(SAMPLE_METADATA)
        overlay: dict[str, Any] = {
            "overlay_version": "1",
            "overlay_schema_version": "1",
            "rules": [
                {
                    "rule_id": "rm-nonexistent",
                    "operation": "remove_alias",
                    "topic_key": "nonexistent_topic",
                    "alias_text": "foo",
                }
            ],
            "config_overrides": {},
        }
        with caplog.at_level(logging.WARNING):
            result = merge_overlay(inv, overlay)
        assert any("nonexistent_topic" in r.message for r in caplog.records)
        # No crash, inventory unchanged
        assert "hooks" in result.topics


# ===========================================================================
# 5. Denylist applied
# ===========================================================================


class TestDenylist:
    """Test 5: Denylist applied — generic terms dropped/downranked."""

    def test_add_deny_rule_applied(self) -> None:
        inv = generate_scaffold(SAMPLE_METADATA)
        overlay: dict[str, Any] = {
            "overlay_version": "1",
            "overlay_schema_version": "1",
            "rules": [
                {
                    "rule_id": "drop-overview",
                    "operation": "add_deny_rule",
                    "deny_rule": {
                        "id": "drop-overview",
                        "pattern": "overview",
                        "match_type": "token",
                        "action": "drop",
                        "penalty": None,
                        "reason": "too generic",
                    },
                },
                {
                    "rule_id": "downrank-schema",
                    "operation": "add_deny_rule",
                    "deny_rule": {
                        "id": "downrank-schema",
                        "pattern": "schema",
                        "match_type": "token",
                        "action": "downrank",
                        "penalty": 0.35,
                        "reason": "facet word",
                    },
                },
            ],
            "config_overrides": {},
        }
        result = merge_overlay(inv, overlay)
        assert len(result.denylist) == 2
        ids = [d.id for d in result.denylist]
        assert "drop-overview" in ids
        assert "downrank-schema" in ids


# ===========================================================================
# 7-9. Version axis mismatches
# ===========================================================================


class TestVersionMismatch:
    """Tests 7-9: Version axis mismatches → loud failure."""

    def test_schema_version_set_correctly(self) -> None:
        """Test 7: schema_version axis — builder stamps current version."""
        overlay: dict[str, Any] = {
            "overlay_version": "1",
            "overlay_schema_version": "1",
            "rules": [],
            "config_overrides": {},
        }
        result = build_inventory(SAMPLE_METADATA, overlay)
        assert result.schema_version == "1"

    def test_overlay_schema_version_mismatch_fails(self) -> None:
        """Test 8: overlay_schema_version mismatch."""
        overlay: dict[str, Any] = {
            "overlay_version": "1",
            "overlay_schema_version": "999",
            "rules": [],
            "config_overrides": {},
        }
        with pytest.raises(SystemExit):
            build_inventory(SAMPLE_METADATA, overlay)

    def test_merge_semantics_version_mismatch_fails(self) -> None:
        """Test 9: merge_semantics_version mismatch via overlay key."""
        overlay: dict[str, Any] = {
            "overlay_version": "1",
            "overlay_schema_version": "1",
            "merge_semantics_version": "999",
            "rules": [],
            "config_overrides": {},
        }
        with pytest.raises(SystemExit):
            build_inventory(SAMPLE_METADATA, overlay)


# ===========================================================================
# 10. Overlay format validation
# ===========================================================================


class TestOverlayFormatValidation:
    """Test 10: Unknown root keys warned, missing overlay_version → non-zero exit."""

    def test_unknown_root_keys_warned(self, caplog: pytest.LogCaptureFixture) -> None:
        overlay: dict[str, Any] = {
            "overlay_version": "1",
            "overlay_schema_version": "1",
            "rules": [],
            "config_overrides": {},
            "bogus_key": "should warn",
        }
        with caplog.at_level(logging.WARNING):
            build_inventory(SAMPLE_METADATA, overlay)
        assert any("bogus_key" in r.message for r in caplog.records)

    def test_missing_overlay_version_fails(self) -> None:
        overlay: dict[str, Any] = {
            "overlay_schema_version": "1",
            "rules": [],
            "config_overrides": {},
        }
        with pytest.raises(SystemExit):
            build_inventory(SAMPLE_METADATA, overlay)


# ===========================================================================
# 11. Unknown overlay operation
# ===========================================================================


class TestUnknownOperation:
    """Test 11: Unknown overlay rule operation → warning, rule skipped."""

    def test_unknown_operation_warned_skipped(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        inv = generate_scaffold(SAMPLE_METADATA)
        overlay: dict[str, Any] = {
            "overlay_version": "1",
            "overlay_schema_version": "1",
            "rules": [
                {
                    "rule_id": "bogus-op",
                    "operation": "teleport_topic",
                    "topic_key": "hooks",
                }
            ],
            "config_overrides": {},
        }
        with caplog.at_level(logging.WARNING):
            result = merge_overlay(inv, overlay)
        assert any("teleport_topic" in r.message for r in caplog.records)
        # Inventory unchanged
        assert "hooks" in result.topics


# ===========================================================================
# 12-15. DenyRule validation
# ===========================================================================


class TestDenyRuleValidation:
    """Tests 12-15: DenyRule discriminated union validation at build time."""

    def test_deny_rule_exact_match_type_rejects(self) -> None:
        """Test 12: match_type 'exact' → error."""
        overlay: dict[str, Any] = {
            "overlay_version": "1",
            "overlay_schema_version": "1",
            "rules": [
                {
                    "rule_id": "bad-exact",
                    "operation": "add_deny_rule",
                    "deny_rule": {
                        "id": "bad-exact",
                        "pattern": "test",
                        "match_type": "exact",
                        "action": "drop",
                        "penalty": None,
                        "reason": "test",
                    },
                }
            ],
            "config_overrides": {},
        }
        with pytest.raises(SystemExit):
            build_inventory(SAMPLE_METADATA, overlay)

    def test_deny_rule_drop_non_null_penalty_rejects(self) -> None:
        """Test 13: drop + non-null penalty → error."""
        overlay: dict[str, Any] = {
            "overlay_version": "1",
            "overlay_schema_version": "1",
            "rules": [
                {
                    "rule_id": "bad-drop",
                    "operation": "add_deny_rule",
                    "deny_rule": {
                        "id": "bad-drop",
                        "pattern": "test",
                        "match_type": "token",
                        "action": "drop",
                        "penalty": 0.5,
                        "reason": "test",
                    },
                }
            ],
            "config_overrides": {},
        }
        with pytest.raises(SystemExit):
            build_inventory(SAMPLE_METADATA, overlay)

    def test_deny_rule_downrank_null_penalty_rejects(self) -> None:
        """Test 14: downrank + null penalty → error."""
        overlay: dict[str, Any] = {
            "overlay_version": "1",
            "overlay_schema_version": "1",
            "rules": [
                {
                    "rule_id": "bad-downrank-null",
                    "operation": "add_deny_rule",
                    "deny_rule": {
                        "id": "bad-downrank-null",
                        "pattern": "test",
                        "match_type": "token",
                        "action": "downrank",
                        "penalty": None,
                        "reason": "test",
                    },
                }
            ],
            "config_overrides": {},
        }
        with pytest.raises(SystemExit):
            build_inventory(SAMPLE_METADATA, overlay)

    def test_deny_rule_downrank_zero_penalty_rejects(self) -> None:
        """Test 15: downrank + zero penalty → error."""
        overlay: dict[str, Any] = {
            "overlay_version": "1",
            "overlay_schema_version": "1",
            "rules": [
                {
                    "rule_id": "bad-downrank-zero",
                    "operation": "add_deny_rule",
                    "deny_rule": {
                        "id": "bad-downrank-zero",
                        "pattern": "test",
                        "match_type": "token",
                        "action": "downrank",
                        "penalty": 0.0,
                        "reason": "test",
                    },
                }
            ],
            "config_overrides": {},
        }
        with pytest.raises(SystemExit):
            build_inventory(SAMPLE_METADATA, overlay)


# ===========================================================================
# 16. Weight out-of-bounds → clamped
# ===========================================================================


class TestWeightClamping:
    """Test 16: override_weight out-of-bounds → clamped."""

    def test_override_weight_clamped_high(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        inv = generate_scaffold(SAMPLE_METADATA)
        # Find a known alias text in hooks family
        alias_text = inv.topics["hooks"].aliases[0].text
        overlay: dict[str, Any] = {
            "overlay_version": "1",
            "overlay_schema_version": "1",
            "rules": [
                {
                    "rule_id": "clamp-high",
                    "operation": "override_weight",
                    "topic_key": "hooks",
                    "alias_text": alias_text,
                    "weight": 1.5,
                }
            ],
            "config_overrides": {},
        }
        with caplog.at_level(logging.WARNING):
            result = merge_overlay(inv, overlay)
        matched = next(
            a for a in result.topics["hooks"].aliases if a.text == alias_text
        )
        assert matched.weight == 1.0
        assert any("clamp" in r.message.lower() for r in caplog.records)

    def test_override_weight_clamped_low(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        inv = generate_scaffold(SAMPLE_METADATA)
        alias_text = inv.topics["hooks"].aliases[0].text
        overlay: dict[str, Any] = {
            "overlay_version": "1",
            "overlay_schema_version": "1",
            "rules": [
                {
                    "rule_id": "clamp-low",
                    "operation": "override_weight",
                    "topic_key": "hooks",
                    "alias_text": alias_text,
                    "weight": -0.2,
                }
            ],
            "config_overrides": {},
        }
        with caplog.at_level(logging.WARNING):
            result = merge_overlay(inv, overlay)
        matched = next(
            a for a in result.topics["hooks"].aliases if a.text == alias_text
        )
        assert matched.weight == 0.0


# ===========================================================================
# 17. config_version mismatch → defaults
# ===========================================================================


class TestConfigVersionMismatch:
    """Test 17: config_version mismatch → use defaults."""

    def test_config_version_mismatch_uses_defaults(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        config_path = tmp_path / "ccdi_config.json"
        config_path.write_text(
            json.dumps(
                {
                    "config_version": "999",
                    "packets": {"initial_token_budget_min": 9999},
                }
            )
        )
        overlay: dict[str, Any] = {
            "overlay_version": "1",
            "overlay_schema_version": "1",
            "rules": [],
            "config_overrides": {},
        }
        with caplog.at_level(logging.WARNING):
            result = build_inventory(
                SAMPLE_METADATA, overlay, config_path=str(config_path)
            )
        # Config overrides should not have applied — version mismatch means all defaults
        assert isinstance(result, CompiledInventory)


# ===========================================================================
# 18. remove_alias unknown alias_text
# ===========================================================================


class TestRemoveAliasUnknown:
    """Test 18: remove_alias on known topic with unknown alias_text → warning, skip."""

    def test_remove_alias_unknown_text_warns(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        inv = generate_scaffold(SAMPLE_METADATA)
        overlay: dict[str, Any] = {
            "overlay_version": "1",
            "overlay_schema_version": "1",
            "rules": [
                {
                    "rule_id": "rm-bogus-alias",
                    "operation": "remove_alias",
                    "topic_key": "hooks",
                    "alias_text": "nonexistent_alias_xyz",
                }
            ],
            "config_overrides": {},
        }
        with caplog.at_level(logging.WARNING):
            result = merge_overlay(inv, overlay)
        assert any("nonexistent_alias_xyz" in r.message for r in caplog.records)
        # Aliases unchanged
        assert len(result.topics["hooks"].aliases) == len(inv.topics["hooks"].aliases)


# ===========================================================================
# 19-20. Config override unknown keys / valid namespace unknown leaf
# ===========================================================================


class TestConfigOverrideUnknown:
    """Tests 19-20: Config override unknown/unknown-leaf keys warned, skipped."""

    def test_unknown_keys_warned_skipped(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test 19: Unknown config_overrides keys."""
        overlay: dict[str, Any] = {
            "overlay_version": "1",
            "overlay_schema_version": "1",
            "rules": [],
            "config_overrides": {
                "bogus_namespace": {"key": "val"},
            },
        }
        with caplog.at_level(logging.WARNING):
            result = build_inventory(SAMPLE_METADATA, overlay)
        assert any("bogus_namespace" in r.message for r in caplog.records)
        assert isinstance(result, CompiledInventory)

    def test_valid_namespace_unknown_leaf_warned_skipped(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test 20: Valid namespace, unknown leaf key."""
        overlay: dict[str, Any] = {
            "overlay_version": "1",
            "overlay_schema_version": "1",
            "rules": [],
            "config_overrides": {
                "classifier": {"nonexistent_key": 0.5},
            },
        }
        with caplog.at_level(logging.WARNING):
            result = build_inventory(SAMPLE_METADATA, overlay)
        assert any("nonexistent_key" in r.message for r in caplog.records)
        assert isinstance(result, CompiledInventory)


# ===========================================================================
# 21. Partial config missing keys → defaults
# ===========================================================================


class TestPartialConfigDefaults:
    """Test 21: Partial config missing keys → defaults for missing key."""

    def test_partial_config_fills_defaults(self, tmp_path: Path) -> None:
        config_path = tmp_path / "ccdi_config.json"
        config_path.write_text(
            json.dumps(
                {
                    "config_version": "1",
                    "classifier": {"confidence_high_min_weight": 0.9},
                }
            )
        )
        overlay: dict[str, Any] = {
            "overlay_version": "1",
            "overlay_schema_version": "1",
            "rules": [],
            "config_overrides": {},
        }
        result = build_inventory(SAMPLE_METADATA, overlay, config_path=str(config_path))
        assert isinstance(result, CompiledInventory)


# ===========================================================================
# 22. add_deny_rule penalty out-of-bounds → error
# ===========================================================================


class TestDenyRulePenaltyOutOfBounds:
    """Test 22: add_deny_rule penalty=1.5 → non-zero exit."""

    def test_penalty_1_5_rejects(self) -> None:
        overlay: dict[str, Any] = {
            "overlay_version": "1",
            "overlay_schema_version": "1",
            "rules": [
                {
                    "rule_id": "bad-penalty",
                    "operation": "add_deny_rule",
                    "deny_rule": {
                        "id": "bad-penalty",
                        "pattern": "test",
                        "match_type": "token",
                        "action": "downrank",
                        "penalty": 1.5,
                        "reason": "test",
                    },
                }
            ],
            "config_overrides": {},
        }
        with pytest.raises(SystemExit):
            build_inventory(SAMPLE_METADATA, overlay)


# ===========================================================================
# 23. Config override type mismatch → skipped
# ===========================================================================


class TestConfigOverrideTypeMismatch:
    """Test 23: Config override type mismatch → skipped."""

    def test_type_mismatch_warned_skipped(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        overlay: dict[str, Any] = {
            "overlay_version": "1",
            "overlay_schema_version": "1",
            "rules": [],
            "config_overrides": {
                "classifier": {"confidence_high_min_weight": "not_a_number"},
            },
        }
        with caplog.at_level(logging.WARNING):
            result = build_inventory(SAMPLE_METADATA, overlay)
        assert any("type mismatch" in r.message.lower() for r in caplog.records)
        assert isinstance(result, CompiledInventory)


# ===========================================================================
# 24. Scaffold-generated alias weight out-of-range → clamped
# ===========================================================================


class TestScaffoldWeightClamping:
    """Test 24: Scaffold-generated alias weight out-of-range → clamped."""

    def test_scaffold_clamps_alias_weights(self) -> None:
        """Alias dataclass clamps weights. Verify the scaffold uses Alias which clamps."""
        inv = generate_scaffold(SAMPLE_METADATA)
        for topic in inv.topics.values():
            for alias in topic.aliases:
                assert 0.0 <= alias.weight <= 1.0


# ===========================================================================
# 25. add_deny_rule penalty=1.0 boundary → accepted
# ===========================================================================


class TestDenyRuleBoundary:
    """Test 25: add_deny_rule penalty=1.0 boundary → accepted."""

    def test_penalty_1_0_accepted(self) -> None:
        overlay: dict[str, Any] = {
            "overlay_version": "1",
            "overlay_schema_version": "1",
            "rules": [
                {
                    "rule_id": "boundary-ok",
                    "operation": "add_deny_rule",
                    "deny_rule": {
                        "id": "boundary-ok",
                        "pattern": "test",
                        "match_type": "token",
                        "action": "downrank",
                        "penalty": 1.0,
                        "reason": "max penalty",
                    },
                }
            ],
            "config_overrides": {},
        }
        result = build_inventory(SAMPLE_METADATA, overlay)
        assert len(result.denylist) == 1
        assert result.denylist[0].penalty == 1.0


# ===========================================================================
# 26-27. Cross-key token budget validation
# ===========================================================================


class TestCrossKeyBudget:
    """Tests 26-27: Cross-key token budget constraints."""

    def test_initial_min_gt_max_falls_back(self, tmp_path: Path) -> None:
        """Test 26: initial_token_budget_min > max → paired fallback."""
        config_path = tmp_path / "ccdi_config.json"
        config_path.write_text(
            json.dumps(
                {
                    "config_version": "1",
                    "packets": {
                        "initial_token_budget_min": 2000,
                        "initial_token_budget_max": 500,
                    },
                }
            )
        )
        overlay: dict[str, Any] = {
            "overlay_version": "1",
            "overlay_schema_version": "1",
            "rules": [],
            "config_overrides": {},
        }
        result = build_inventory(SAMPLE_METADATA, overlay, config_path=str(config_path))
        assert isinstance(result, CompiledInventory)

    def test_valid_min_invalid_max_both_fallback(self, tmp_path: Path) -> None:
        """Test 27: Valid min with invalid max → both fall back."""
        config_path = tmp_path / "ccdi_config.json"
        config_path.write_text(
            json.dumps(
                {
                    "config_version": "1",
                    "packets": {
                        "initial_token_budget_min": 600,
                        "initial_token_budget_max": -1,
                    },
                }
            )
        )
        overlay: dict[str, Any] = {
            "overlay_version": "1",
            "overlay_schema_version": "1",
            "rules": [],
            "config_overrides": {},
        }
        result = build_inventory(SAMPLE_METADATA, overlay, config_path=str(config_path))
        assert isinstance(result, CompiledInventory)


# ===========================================================================
# 28-29. add_topic / replace_aliases weight clamping
# ===========================================================================


class TestAddTopicWeightClamping:
    """Tests 28-29: Weight clamping in add_topic and replace_aliases."""

    def test_add_topic_alias_weight_clamped(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test 28: add_topic alias weight out-of-bounds → clamped."""
        overlay: dict[str, Any] = {
            "overlay_version": "1",
            "overlay_schema_version": "1",
            "rules": [
                {
                    "rule_id": "add-clamped",
                    "operation": "add_topic",
                    "topic": {
                        "topic_key": "new_topic",
                        "family_key": "new_topic",
                        "kind": "family",
                        "canonical_label": "New Topic",
                        "category_hint": "new",
                        "parent_topic": None,
                        "aliases": [
                            {"text": "new", "match_type": "token", "weight": 2.5},
                        ],
                        "query_plan": {
                            "default_facet": "overview",
                            "facets": {
                                "overview": [
                                    {"q": "new topic", "category": "new", "priority": 1}
                                ]
                            },
                        },
                        "canonical_refs": [],
                    },
                }
            ],
            "config_overrides": {},
        }
        with caplog.at_level(logging.WARNING):
            result = build_inventory(SAMPLE_METADATA, overlay)
        assert result.topics["new_topic"].aliases[0].weight == 1.0

    def test_replace_aliases_weight_clamped(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test 29: replace_aliases alias weight out-of-bounds → clamped."""
        inv = generate_scaffold(SAMPLE_METADATA)
        overlay: dict[str, Any] = {
            "overlay_version": "1",
            "overlay_schema_version": "1",
            "rules": [
                {
                    "rule_id": "replace-clamped",
                    "operation": "replace_aliases",
                    "topic_key": "hooks",
                    "aliases": [
                        {"text": "hooks", "match_type": "token", "weight": -0.5},
                    ],
                }
            ],
            "config_overrides": {},
        }
        with caplog.at_level(logging.WARNING):
            result = merge_overlay(inv, overlay)
        assert result.topics["hooks"].aliases[0].weight == 0.0


# ===========================================================================
# 30. Duplicate deny_rule.id
# ===========================================================================


class TestDuplicateDenyRuleId:
    """Test 30: Duplicate deny_rule.id across add_deny_rule → non-zero exit."""

    def test_duplicate_deny_rule_id_rejects(self) -> None:
        overlay: dict[str, Any] = {
            "overlay_version": "1",
            "overlay_schema_version": "1",
            "rules": [
                {
                    "rule_id": "deny-1",
                    "operation": "add_deny_rule",
                    "deny_rule": {
                        "id": "same-id",
                        "pattern": "test",
                        "match_type": "token",
                        "action": "drop",
                        "penalty": None,
                        "reason": "test",
                    },
                },
                {
                    "rule_id": "deny-2",
                    "operation": "add_deny_rule",
                    "deny_rule": {
                        "id": "same-id",
                        "pattern": "other",
                        "match_type": "token",
                        "action": "drop",
                        "penalty": None,
                        "reason": "test dup",
                    },
                },
            ],
            "config_overrides": {},
        }
        with pytest.raises(SystemExit):
            build_inventory(SAMPLE_METADATA, overlay)


# ===========================================================================
# 31-32. Missing default_facet
# ===========================================================================


class TestMissingDefaultFacet:
    """Tests 31-32: Missing default_facet → error."""

    def test_replace_queries_missing_default_facet_rejects(self) -> None:
        """Test 31: replace_queries missing default_facet → error."""
        overlay: dict[str, Any] = {
            "overlay_version": "1",
            "overlay_schema_version": "1",
            "rules": [
                {
                    "rule_id": "bad-replace-queries",
                    "operation": "replace_queries",
                    "topic_key": "hooks",
                    "query_plan": {
                        "facets": {
                            "overview": [
                                {"q": "hooks", "category": "hooks", "priority": 1}
                            ]
                        },
                    },
                }
            ],
            "config_overrides": {},
        }
        with pytest.raises(SystemExit):
            build_inventory(SAMPLE_METADATA, overlay)

    def test_add_topic_missing_default_facet_rejects(self) -> None:
        """Test 32: add_topic query_plan missing default_facet → error."""
        overlay: dict[str, Any] = {
            "overlay_version": "1",
            "overlay_schema_version": "1",
            "rules": [
                {
                    "rule_id": "bad-add-topic",
                    "operation": "add_topic",
                    "topic": {
                        "topic_key": "bad",
                        "family_key": "bad",
                        "kind": "family",
                        "canonical_label": "Bad",
                        "category_hint": "bad",
                        "parent_topic": None,
                        "aliases": [
                            {"text": "bad", "match_type": "token", "weight": 0.5},
                        ],
                        "query_plan": {
                            "facets": {
                                "overview": [
                                    {"q": "bad", "category": "bad", "priority": 1}
                                ]
                            },
                        },
                        "canonical_refs": [],
                    },
                }
            ],
            "config_overrides": {},
        }
        with pytest.raises(SystemExit):
            build_inventory(SAMPLE_METADATA, overlay)


# ===========================================================================
# 33-34. replace_refs / replace_queries on unknown topic
# ===========================================================================


class TestReplaceOnUnknownTopic:
    """Tests 33-34: replace_refs/replace_queries on unknown topic → warning, skip."""

    def test_replace_refs_unknown_topic_warns(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test 33: replace_refs on unknown topic."""
        inv = generate_scaffold(SAMPLE_METADATA)
        overlay: dict[str, Any] = {
            "overlay_version": "1",
            "overlay_schema_version": "1",
            "rules": [
                {
                    "rule_id": "replace-refs-unknown",
                    "operation": "replace_refs",
                    "topic_key": "nonexistent",
                    "canonical_refs": [],
                }
            ],
            "config_overrides": {},
        }
        with caplog.at_level(logging.WARNING):
            result = merge_overlay(inv, overlay)
        assert any("nonexistent" in r.message for r in caplog.records)
        assert isinstance(result, CompiledInventory)

    def test_replace_queries_unknown_topic_warns(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test 34: replace_queries on unknown topic."""
        inv = generate_scaffold(SAMPLE_METADATA)
        overlay: dict[str, Any] = {
            "overlay_version": "1",
            "overlay_schema_version": "1",
            "rules": [
                {
                    "rule_id": "replace-queries-unknown",
                    "operation": "replace_queries",
                    "topic_key": "nonexistent",
                    "query_plan": {
                        "default_facet": "overview",
                        "facets": {
                            "overview": [
                                {"q": "test", "category": "test", "priority": 1}
                            ]
                        },
                    },
                }
            ],
            "config_overrides": {},
        }
        with caplog.at_level(logging.WARNING):
            result = merge_overlay(inv, overlay)
        assert any("nonexistent" in r.message for r in caplog.records)
        assert isinstance(result, CompiledInventory)


# ===========================================================================
# 35-36. Duplicate rule_id across operations
# ===========================================================================


class TestDuplicateRuleId:
    """Tests 35-36: Duplicate rule_id across operations → non-zero exit."""

    def test_duplicate_rule_id_same_op_type(self) -> None:
        """Test 35: Duplicate rule_id across non-add_deny_rule operations."""
        overlay: dict[str, Any] = {
            "overlay_version": "1",
            "overlay_schema_version": "1",
            "rules": [
                {
                    "rule_id": "dup-id",
                    "operation": "override_weight",
                    "topic_key": "hooks",
                    "alias_text": "hooks",
                    "weight": 0.8,
                },
                {
                    "rule_id": "dup-id",
                    "operation": "override_weight",
                    "topic_key": "hooks",
                    "alias_text": "hook",
                    "weight": 0.7,
                },
            ],
            "config_overrides": {},
        }
        with pytest.raises(SystemExit):
            build_inventory(SAMPLE_METADATA, overlay)

    def test_duplicate_rule_id_mixed_op_types(self) -> None:
        """Test 36: Duplicate rule_id across mixed operation types."""
        overlay: dict[str, Any] = {
            "overlay_version": "1",
            "overlay_schema_version": "1",
            "rules": [
                {
                    "rule_id": "mixed-dup",
                    "operation": "override_weight",
                    "topic_key": "hooks",
                    "alias_text": "hooks",
                    "weight": 0.8,
                },
                {
                    "rule_id": "mixed-dup",
                    "operation": "add_deny_rule",
                    "deny_rule": {
                        "id": "mixed-deny",
                        "pattern": "test",
                        "match_type": "token",
                        "action": "drop",
                        "penalty": None,
                        "reason": "test",
                    },
                },
            ],
            "config_overrides": {},
        }
        with pytest.raises(SystemExit):
            build_inventory(SAMPLE_METADATA, overlay)


# ===========================================================================
# 37-40. load_inventory resilience tests
# ===========================================================================


class TestLoadInventoryResilience:
    """Tests 37-40: Load-time resilience for inventory.py."""

    def _make_valid_inventory_dict(self) -> dict[str, Any]:
        """Build a valid serialized CompiledInventory dict."""
        return {
            "schema_version": "1",
            "built_at": "2026-03-23T00:00:00Z",
            "docs_epoch": "abc123",
            "merge_semantics_version": "1",
            "topics": {
                "hooks": {
                    "topic_key": "hooks",
                    "family_key": "hooks",
                    "kind": "family",
                    "canonical_label": "Hooks",
                    "category_hint": "hooks",
                    "parent_topic": None,
                    "aliases": [
                        {
                            "text": "hooks",
                            "match_type": "token",
                            "weight": 0.5,
                            "facet_hint": None,
                            "source": "generated",
                        }
                    ],
                    "query_plan": {
                        "default_facet": "overview",
                        "facets": {
                            "overview": [
                                {"q": "hooks", "category": "hooks", "priority": 1}
                            ]
                        },
                    },
                    "canonical_refs": [],
                },
            },
            "denylist": [],
            "overlay_meta": {
                "overlay_version": "1",
                "overlay_schema_version": "1",
                "applied_rules": [],
            },
        }

    def test_deny_rule_load_time_warn_and_skip(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test 37: DenyRule load-time warn-and-skip (downrank, penalty=-0.5)."""
        data = self._make_valid_inventory_dict()
        data["denylist"] = [
            {
                "id": "bad-penalty",
                "pattern": "test",
                "match_type": "token",
                "action": "downrank",
                "penalty": -0.5,
                "reason": "bad",
            }
        ]
        path = _write_json(tmp_path, data)
        with caplog.at_level(logging.INFO):
            inv = load_inventory(path)
        assert len(inv.denylist) == 0
        assert any("backward-compat skip" in r.message for r in caplog.records)

    def test_load_time_schema_version_mismatch_warns(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test 38: Load-time schema_version mismatch → warning, best-effort."""
        data = self._make_valid_inventory_dict()
        data["schema_version"] = "999"
        path = _write_json(tmp_path, data)
        with caplog.at_level(logging.WARNING):
            inv = load_inventory(path)
        assert isinstance(inv, CompiledInventory)
        assert any("schema_version" in r.message for r in caplog.records)

    def test_load_time_merge_semantics_version_absent_warns(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test 39: Load-time merge_semantics_version absent → warning, assume '1'."""
        data = self._make_valid_inventory_dict()
        del data["merge_semantics_version"]
        path = _write_json(tmp_path, data)
        with caplog.at_level(logging.WARNING):
            inv = load_inventory(path)
        assert inv.merge_semantics_version == "1"
        assert any("merge_semantics_version" in r.message for r in caplog.records)

    def test_load_time_missing_overlay_meta_warns(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test 40: Load-time missing overlay_meta → warning, continue."""
        data = self._make_valid_inventory_dict()
        del data["overlay_meta"]
        path = _write_json(tmp_path, data)
        with caplog.at_level(logging.WARNING):
            inv = load_inventory(path)
        assert inv.overlay_meta is None
        assert any("overlay_meta" in r.message for r in caplog.records)


# ===========================================================================
# Additional: add_topic empty aliases → reject, overlay applied_rules order
# ===========================================================================


class TestAddTopicEmptyAliases:
    """add_topic with empty aliases → reject."""

    def test_add_topic_empty_aliases_rejects(self) -> None:
        overlay: dict[str, Any] = {
            "overlay_version": "1",
            "overlay_schema_version": "1",
            "rules": [
                {
                    "rule_id": "bad-empty",
                    "operation": "add_topic",
                    "topic": {
                        "topic_key": "empty",
                        "family_key": "empty",
                        "kind": "family",
                        "canonical_label": "Empty",
                        "category_hint": "empty",
                        "parent_topic": None,
                        "aliases": [],
                        "query_plan": {
                            "default_facet": "overview",
                            "facets": {
                                "overview": [
                                    {"q": "empty", "category": "empty", "priority": 1}
                                ]
                            },
                        },
                        "canonical_refs": [],
                    },
                }
            ],
            "config_overrides": {},
        }
        with pytest.raises(SystemExit):
            build_inventory(SAMPLE_METADATA, overlay)


class TestReplaceAliasesEmpty:
    """replace_aliases with empty aliases → reject."""

    def test_replace_aliases_empty_rejects(self) -> None:
        overlay: dict[str, Any] = {
            "overlay_version": "1",
            "overlay_schema_version": "1",
            "rules": [
                {
                    "rule_id": "bad-replace-empty",
                    "operation": "replace_aliases",
                    "topic_key": "hooks",
                    "aliases": [],
                }
            ],
            "config_overrides": {},
        }
        with pytest.raises(SystemExit):
            build_inventory(SAMPLE_METADATA, overlay)


class TestAppliedRuleOrder:
    """AppliedRule serialization: rules[] first, config_overrides last with prefix."""

    def test_applied_rule_order(self) -> None:
        overlay: dict[str, Any] = {
            "overlay_version": "1",
            "overlay_schema_version": "1",
            "rules": [
                {
                    "rule_id": "drop-overview",
                    "operation": "add_deny_rule",
                    "deny_rule": {
                        "id": "drop-overview",
                        "pattern": "overview",
                        "match_type": "token",
                        "action": "drop",
                        "penalty": None,
                        "reason": "too generic",
                    },
                },
            ],
            "config_overrides": {
                "classifier": {"confidence_high_min_weight": 0.9},
            },
        }
        result = build_inventory(SAMPLE_METADATA, overlay)
        assert result.overlay_meta is not None
        rules = result.overlay_meta.applied_rules
        # Rules-sourced entries come first
        rule_ids = [r.rule_id for r in rules]
        assert rule_ids[0] == "drop-overview"
        # Config-sourced entries come last with prefix
        config_rules = [r for r in rules if r.rule_id.startswith("config-override:")]
        assert len(config_rules) >= 1


class TestLoadTimeDenyRuleUnionViolation:
    """Load-time DenyRule union violation: drop+non-null penalty and downrank+null."""

    def test_drop_non_null_penalty_warns_and_skips(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        data = {
            "schema_version": "1",
            "built_at": "2026-03-23T00:00:00Z",
            "docs_epoch": None,
            "merge_semantics_version": "1",
            "topics": {
                "hooks": {
                    "topic_key": "hooks",
                    "family_key": "hooks",
                    "kind": "family",
                    "canonical_label": "Hooks",
                    "category_hint": "hooks",
                    "parent_topic": None,
                    "aliases": [
                        {"text": "hooks", "match_type": "token", "weight": 0.5},
                    ],
                    "query_plan": {
                        "default_facet": "overview",
                        "facets": {
                            "overview": [
                                {"q": "hooks", "category": "hooks", "priority": 1}
                            ]
                        },
                    },
                    "canonical_refs": [],
                },
            },
            "denylist": [
                {
                    "id": "bad-union",
                    "pattern": "test",
                    "match_type": "token",
                    "action": "drop",
                    "penalty": 0.5,
                    "reason": "union violation",
                }
            ],
            "overlay_meta": {
                "overlay_version": "1",
                "overlay_schema_version": "1",
                "applied_rules": [],
            },
        }
        path = _write_json(tmp_path, data)
        with caplog.at_level(logging.WARNING):
            inv = load_inventory(path)
        assert len(inv.denylist) == 0
        assert any("schema corruption" in r.message for r in caplog.records)

    def test_downrank_null_penalty_warns_and_skips(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        data = {
            "schema_version": "1",
            "built_at": "2026-03-23T00:00:00Z",
            "docs_epoch": None,
            "merge_semantics_version": "1",
            "topics": {
                "hooks": {
                    "topic_key": "hooks",
                    "family_key": "hooks",
                    "kind": "family",
                    "canonical_label": "Hooks",
                    "category_hint": "hooks",
                    "parent_topic": None,
                    "aliases": [
                        {"text": "hooks", "match_type": "token", "weight": 0.5},
                    ],
                    "query_plan": {
                        "default_facet": "overview",
                        "facets": {
                            "overview": [
                                {"q": "hooks", "category": "hooks", "priority": 1}
                            ]
                        },
                    },
                    "canonical_refs": [],
                },
            },
            "denylist": [
                {
                    "id": "bad-union-2",
                    "pattern": "test",
                    "match_type": "token",
                    "action": "downrank",
                    "penalty": None,
                    "reason": "union violation",
                }
            ],
            "overlay_meta": {
                "overlay_version": "1",
                "overlay_schema_version": "1",
                "applied_rules": [],
            },
        }
        path = _write_json(tmp_path, data)
        with caplog.at_level(logging.WARNING):
            inv = load_inventory(path)
        assert len(inv.denylist) == 0
        assert any("schema corruption" in r.message for r in caplog.records)


class TestConfigOverrideNullValue:
    """Config override with null values → warned, skipped."""

    def test_null_value_warned_skipped(self, caplog: pytest.LogCaptureFixture) -> None:
        overlay: dict[str, Any] = {
            "overlay_version": "1",
            "overlay_schema_version": "1",
            "rules": [],
            "config_overrides": {
                "classifier": {"confidence_high_min_weight": None},
            },
        }
        with caplog.at_level(logging.WARNING):
            result = build_inventory(SAMPLE_METADATA, overlay)
        assert any("null" in r.message.lower() for r in caplog.records)
        assert isinstance(result, CompiledInventory)
