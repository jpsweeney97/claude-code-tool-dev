"""CCDI inventory build-time tool.

Scaffold generation from dump_index_metadata + overlay merging + config overrides.

Pure functions for testability — MCP client integration only in CLI __main__.

Import pattern:
    from scripts.ccdi.build_inventory import generate_scaffold, merge_overlay, build_inventory
"""

from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone
from typing import Any

from scripts.ccdi.config import BUILTIN_DEFAULTS
from scripts.ccdi.types import (
    Alias,
    AppliedRule,
    CompiledInventory,
    DenyRule,
    DocRef,
    OverlayMeta,
    QueryPlan,
    QuerySpec,
    TopicRecord,
)

logger = logging.getLogger(__name__)

_SCHEMA_VERSION = "1"
_OVERLAY_SCHEMA_VERSION = "1"
_MERGE_SEMANTICS_VERSION = "1"

_VALID_ROOT_KEYS = {
    "overlay_version",
    "overlay_schema_version",
    "merge_semantics_version",
    "rules",
    "config_overrides",
}

_VALID_OPERATIONS = {
    "add_topic",
    "remove_alias",
    "override_weight",
    "replace_aliases",
    "replace_refs",
    "replace_queries",
    "add_deny_rule",
}

# ---------------------------------------------------------------------------
# Build errors — all use sys.exit for non-zero exit
# ---------------------------------------------------------------------------


class _BuildError(Exception):
    """Internal: raised to trigger sys.exit in build_inventory."""


def _fail(msg: str) -> None:
    """Log error and exit non-zero."""
    logger.error(msg)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Scaffold generation
# ---------------------------------------------------------------------------


def generate_scaffold(metadata: dict[str, Any]) -> CompiledInventory:
    """Generate inventory scaffold from dump_index_metadata response.

    Scaffold rules:
    - category name → family TopicRecord
    - heading → leaf TopicRecord
    - code_literal → exact alias (weight=0.9 for distinctive, 0.5 otherwise)
    - config_keys → exact alias with facet_hint="config" (weight=0.7)
    - distinctive_term → phrase alias if multi-word, else token alias (weight=0.6)
    - category.aliases → token aliases on the family topic (weight=0.4)
    """
    topics: dict[str, TopicRecord] = {}

    for cat in metadata.get("categories", []):
        cat_name: str = cat["name"]

        # Family aliases: category name + declared aliases
        family_aliases: list[Alias] = [
            Alias(text=cat_name, match_type="token", weight=0.5, source="generated"),
        ]
        for alias_text in cat.get("aliases", []):
            family_aliases.append(
                Alias(
                    text=alias_text, match_type="token", weight=0.4, source="generated"
                )
            )

        # Family query plan
        family_qp = QueryPlan(
            default_facet="overview",
            facets={
                "overview": [
                    QuerySpec(q=cat_name, category=cat_name, priority=1),
                ],
            },
        )

        topics[cat_name] = TopicRecord(
            topic_key=cat_name,
            family_key=cat_name,
            kind="family",
            canonical_label=cat_name.replace("-", " ").title(),
            category_hint=cat_name,
            parent_topic=None,
            aliases=family_aliases,
            query_plan=family_qp,
            canonical_refs=[],
        )

        # Leaf topics for each heading
        for heading in cat.get("headings", []):
            slug: str = heading["slug"]
            topic_key = f"{cat_name}.{slug}"
            heading_text: str = heading["text"]

            leaf_aliases: list[Alias] = [
                Alias(
                    text=heading_text,
                    match_type="phrase",
                    weight=0.8,
                    source="generated",
                ),
            ]

            # code_literals → exact alias
            seen_literals: set[str] = set()
            for lit in heading.get("code_literals", []):
                if lit in seen_literals:
                    continue
                seen_literals.add(lit)
                # Distinctive: longer or mixed-case = 0.9, short common = 0.5
                weight = 0.9 if (len(lit) > 3 or any(c.isupper() for c in lit)) else 0.5
                leaf_aliases.append(
                    Alias(
                        text=lit, match_type="exact", weight=weight, source="generated"
                    )
                )

            # config_keys → exact alias with facet_hint="config"
            for ck in heading.get("config_keys", []):
                leaf_aliases.append(
                    Alias(
                        text=ck,
                        match_type="exact",
                        weight=0.7,
                        facet_hint="config",
                        source="generated",
                    )
                )

            # distinctive_terms → phrase if multi-word, else token
            for term in heading.get("distinctive_terms", []):
                if " " in term:
                    leaf_aliases.append(
                        Alias(
                            text=term,
                            match_type="phrase",
                            weight=0.6,
                            source="generated",
                        )
                    )
                else:
                    leaf_aliases.append(
                        Alias(
                            text=term,
                            match_type="token",
                            weight=0.6,
                            source="generated",
                        )
                    )

            leaf_qp = QueryPlan(
                default_facet="overview",
                facets={
                    "overview": [
                        QuerySpec(q=heading_text, category=cat_name, priority=1),
                    ],
                },
            )

            topics[topic_key] = TopicRecord(
                topic_key=topic_key,
                family_key=cat_name,
                kind="leaf",
                canonical_label=heading_text,
                category_hint=cat_name,
                parent_topic=cat_name,
                aliases=leaf_aliases,
                query_plan=leaf_qp,
                canonical_refs=[],
            )

    return CompiledInventory(
        schema_version=_SCHEMA_VERSION,
        built_at=datetime.now(timezone.utc).isoformat(),
        docs_epoch=None,
        topics=topics,
        denylist=[],
        overlay_meta=None,
        merge_semantics_version=_MERGE_SEMANTICS_VERSION,
    )


# ---------------------------------------------------------------------------
# Overlay merging
# ---------------------------------------------------------------------------


def merge_overlay(
    inventory: CompiledInventory,
    overlay: dict[str, Any],
) -> CompiledInventory:
    """Apply overlay operations to inventory.

    Operations applied in order from overlay rules[] array.
    Returns new CompiledInventory (immutable dataclasses, so we rebuild).
    """
    # Mutable working copies
    topics: dict[str, TopicRecord] = dict(inventory.topics)
    denylist: list[DenyRule] = list(inventory.denylist)
    applied_rules: list[AppliedRule] = []

    for rule in overlay.get("rules", []):
        rule_id = rule.get("rule_id", "<unnamed>")
        op = rule.get("operation", "")

        if op not in _VALID_OPERATIONS:
            logger.warning(
                "Unknown overlay operation %r in rule %r; skipping", op, rule_id
            )
            continue

        if op == "add_topic":
            topic_data = rule.get("topic", {})
            _apply_add_topic(topics, topic_data, rule_id, applied_rules)

        elif op == "remove_alias":
            _apply_remove_alias(
                topics,
                rule.get("topic_key", ""),
                rule.get("alias_text", ""),
                rule_id,
                applied_rules,
            )

        elif op == "override_weight":
            _apply_override_weight(
                topics,
                rule.get("topic_key", ""),
                rule.get("alias_text", ""),
                rule.get("weight", 0.5),
                rule_id,
                applied_rules,
            )

        elif op == "replace_aliases":
            _apply_replace_aliases(
                topics,
                rule.get("topic_key", ""),
                rule.get("aliases", []),
                rule_id,
                applied_rules,
            )

        elif op == "replace_refs":
            _apply_replace_refs(
                topics,
                rule.get("topic_key", ""),
                rule.get("canonical_refs", []),
                rule_id,
                applied_rules,
            )

        elif op == "replace_queries":
            _apply_replace_queries(
                topics,
                rule.get("topic_key", ""),
                rule.get("query_plan", {}),
                rule_id,
                applied_rules,
            )

        elif op == "add_deny_rule":
            _apply_add_deny_rule(
                denylist, rule.get("deny_rule", {}), rule_id, applied_rules
            )

    overlay_version = overlay.get("overlay_version", "")
    overlay_schema_version = overlay.get("overlay_schema_version", "")

    return CompiledInventory(
        schema_version=inventory.schema_version,
        built_at=inventory.built_at,
        docs_epoch=inventory.docs_epoch,
        topics=topics,
        denylist=denylist,
        overlay_meta=OverlayMeta(
            overlay_version=overlay_version,
            overlay_schema_version=overlay_schema_version,
            applied_rules=applied_rules,
        ),
        merge_semantics_version=inventory.merge_semantics_version,
    )


def _apply_add_topic(
    topics: dict[str, TopicRecord],
    topic_data: dict[str, Any],
    rule_id: str,
    applied_rules: list[AppliedRule],
) -> None:
    """Add a new TopicRecord from overlay data."""
    topic_key = topic_data.get("topic_key", "")
    aliases = [_parse_alias_overlay(a) for a in topic_data.get("aliases", [])]
    qp_data = topic_data.get("query_plan", {})
    refs_data = topic_data.get("canonical_refs", [])
    refs = [
        DocRef(
            chunk_id=r["chunk_id"], category=r["category"], source_file=r["source_file"]
        )
        for r in refs_data
    ]
    facets = _parse_facets(qp_data)
    query_plan = QueryPlan(
        default_facet=qp_data.get("default_facet", "overview"),
        facets=facets,
    )

    topic = TopicRecord(
        topic_key=topic_key,
        family_key=topic_data.get("family_key", topic_key),
        kind=topic_data.get("kind", "leaf"),
        canonical_label=topic_data.get("canonical_label", topic_key),
        category_hint=topic_data.get("category_hint", ""),
        parent_topic=topic_data.get("parent_topic"),
        aliases=aliases,
        query_plan=query_plan,
        canonical_refs=refs,
    )
    topics[topic_key] = topic
    applied_rules.append(
        AppliedRule(rule_id=rule_id, operation="add_topic", target=topic_key)
    )


def _apply_remove_alias(
    topics: dict[str, TopicRecord],
    topic_key: str,
    alias_text: str,
    rule_id: str,
    applied_rules: list[AppliedRule],
) -> None:
    """Remove an alias from a topic."""
    if topic_key not in topics:
        logger.warning(
            "remove_alias: unknown topic %r in rule %r; skipping", topic_key, rule_id
        )
        return
    topic = topics[topic_key]
    new_aliases = [a for a in topic.aliases if a.text != alias_text]
    if len(new_aliases) == len(topic.aliases):
        logger.warning(
            "remove_alias: alias_text %r not found in topic %r; skipping",
            alias_text,
            topic_key,
        )
        return
    topics[topic_key] = _replace_topic_aliases(topic, new_aliases)
    applied_rules.append(
        AppliedRule(rule_id=rule_id, operation="remove_alias", target=topic_key)
    )


def _apply_override_weight(
    topics: dict[str, TopicRecord],
    topic_key: str,
    alias_text: str,
    weight: float,
    rule_id: str,
    applied_rules: list[AppliedRule],
) -> None:
    """Override the weight of a specific alias."""
    if topic_key not in topics:
        logger.warning(
            "override_weight: unknown topic %r in rule %r; skipping", topic_key, rule_id
        )
        return
    topic = topics[topic_key]
    # Clamp with warning
    clamped = _clamp_weight(weight, f"override_weight rule {rule_id}")
    new_aliases = []
    found = False
    for a in topic.aliases:
        if a.text == alias_text:
            new_aliases.append(
                Alias(
                    text=a.text,
                    match_type=a.match_type,
                    weight=clamped,
                    facet_hint=a.facet_hint,
                    source=a.source,
                )
            )
            found = True
        else:
            new_aliases.append(a)
    if not found:
        logger.warning(
            "override_weight: alias_text %r not found in topic %r; skipping",
            alias_text,
            topic_key,
        )
        return
    topics[topic_key] = _replace_topic_aliases(topic, new_aliases)
    applied_rules.append(
        AppliedRule(rule_id=rule_id, operation="override_weight", target=topic_key)
    )


def _apply_replace_aliases(
    topics: dict[str, TopicRecord],
    topic_key: str,
    aliases_data: list[dict[str, Any]],
    rule_id: str,
    applied_rules: list[AppliedRule],
) -> None:
    """Replace entire aliases array for a topic."""
    if topic_key not in topics:
        logger.warning(
            "replace_aliases: unknown topic %r in rule %r; skipping", topic_key, rule_id
        )
        return
    new_aliases = [_parse_alias_overlay(a) for a in aliases_data]
    topics[topic_key] = _replace_topic_aliases(topics[topic_key], new_aliases)
    applied_rules.append(
        AppliedRule(rule_id=rule_id, operation="replace_aliases", target=topic_key)
    )


def _apply_replace_refs(
    topics: dict[str, TopicRecord],
    topic_key: str,
    refs_data: list[dict[str, Any]],
    rule_id: str,
    applied_rules: list[AppliedRule],
) -> None:
    """Replace canonical_refs for a topic."""
    if topic_key not in topics:
        logger.warning(
            "replace_refs: unknown topic %r in rule %r; skipping", topic_key, rule_id
        )
        return
    refs = [
        DocRef(
            chunk_id=r["chunk_id"], category=r["category"], source_file=r["source_file"]
        )
        for r in refs_data
    ]
    topic = topics[topic_key]
    topics[topic_key] = TopicRecord(
        topic_key=topic.topic_key,
        family_key=topic.family_key,
        kind=topic.kind,
        canonical_label=topic.canonical_label,
        category_hint=topic.category_hint,
        parent_topic=topic.parent_topic,
        aliases=topic.aliases,
        query_plan=topic.query_plan,
        canonical_refs=refs,
    )
    applied_rules.append(
        AppliedRule(rule_id=rule_id, operation="replace_refs", target=topic_key)
    )


def _apply_replace_queries(
    topics: dict[str, TopicRecord],
    topic_key: str,
    qp_data: dict[str, Any],
    rule_id: str,
    applied_rules: list[AppliedRule],
) -> None:
    """Replace query_plan for a topic."""
    if topic_key not in topics:
        logger.warning(
            "replace_queries: unknown topic %r in rule %r; skipping", topic_key, rule_id
        )
        return
    facets = _parse_facets(qp_data)
    query_plan = QueryPlan(
        default_facet=qp_data.get("default_facet", "overview"),
        facets=facets,
    )
    topic = topics[topic_key]
    topics[topic_key] = TopicRecord(
        topic_key=topic.topic_key,
        family_key=topic.family_key,
        kind=topic.kind,
        canonical_label=topic.canonical_label,
        category_hint=topic.category_hint,
        parent_topic=topic.parent_topic,
        aliases=topic.aliases,
        query_plan=query_plan,
        canonical_refs=topic.canonical_refs,
    )
    applied_rules.append(
        AppliedRule(rule_id=rule_id, operation="replace_queries", target=topic_key)
    )


def _apply_add_deny_rule(
    denylist: list[DenyRule],
    deny_data: dict[str, Any],
    rule_id: str,
    applied_rules: list[AppliedRule],
) -> None:
    """Add a DenyRule to the denylist. Validation errors are raised (caught by build_inventory)."""
    deny_rule = DenyRule(
        id=deny_data["id"],
        pattern=deny_data["pattern"],
        match_type=deny_data["match_type"],
        action=deny_data["action"],
        penalty=deny_data.get("penalty"),
        reason=deny_data.get("reason", ""),
    )
    denylist.append(deny_rule)
    applied_rules.append(
        AppliedRule(rule_id=rule_id, operation="add_deny_rule", target=deny_data["id"])
    )


# ---------------------------------------------------------------------------
# Full build pipeline
# ---------------------------------------------------------------------------


def build_inventory(
    metadata: dict[str, Any],
    overlay: dict[str, Any] | None = None,
    *,
    config_path: str | None = None,
) -> CompiledInventory:
    """Full build pipeline: scaffold + overlay merge + config overrides.

    Validates overlay format, version axes, rule uniqueness, deny rules,
    and post-merge invariants. Exits non-zero on fatal errors.
    """
    inv = generate_scaffold(metadata)

    if overlay is None:
        return inv

    # --- Overlay format validation ---
    _validate_overlay_format(overlay)

    # --- Version axis validation ---
    _validate_version_axes(overlay)

    # --- Rule ID uniqueness ---
    _validate_rule_id_uniqueness(overlay)

    # --- Deny rule pre-validation (fail loudly at build time) ---
    _validate_deny_rules_strict(overlay)

    # --- Empty aliases / missing default_facet pre-validation ---
    _validate_topic_rules(overlay)

    # --- Merge overlay ---
    try:
        inv = merge_overlay(inv, overlay)
    except (ValueError, KeyError) as exc:
        _fail(f"Overlay merge failed: {exc}")

    # --- Post-merge: every topic must have >= 1 alias ---
    for key, topic in inv.topics.items():
        if not topic.aliases:
            _fail(f"Post-merge: topic {key!r} has no aliases")

    # --- Config overrides (from overlay, not config file) ---
    applied_config_rules = _apply_config_overrides(overlay.get("config_overrides", {}))

    # --- Merge config-override AppliedRules into overlay_meta ---
    if inv.overlay_meta is not None and applied_config_rules:
        all_rules = list(inv.overlay_meta.applied_rules) + applied_config_rules
        inv = CompiledInventory(
            schema_version=inv.schema_version,
            built_at=inv.built_at,
            docs_epoch=inv.docs_epoch,
            topics=inv.topics,
            denylist=inv.denylist,
            overlay_meta=OverlayMeta(
                overlay_version=inv.overlay_meta.overlay_version,
                overlay_schema_version=inv.overlay_meta.overlay_schema_version,
                applied_rules=all_rules,
            ),
            merge_semantics_version=inv.merge_semantics_version,
        )

    return inv


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def _validate_overlay_format(overlay: dict[str, Any]) -> None:
    """Validate overlay format: required keys, warn unknown root keys."""
    # Missing overlay_version → fatal
    if "overlay_version" not in overlay:
        _fail("Overlay missing required 'overlay_version' key")

    # Unknown root keys → warn
    for key in overlay:
        if key not in _VALID_ROOT_KEYS:
            logger.warning("Overlay has unknown root key %r; ignoring", key)


def _validate_version_axes(overlay: dict[str, Any]) -> None:
    """Validate version axes. Mismatch → non-zero exit."""
    osv = overlay.get("overlay_schema_version", _OVERLAY_SCHEMA_VERSION)
    if osv != _OVERLAY_SCHEMA_VERSION:
        _fail(
            f"Overlay overlay_schema_version {osv!r} != expected {_OVERLAY_SCHEMA_VERSION!r}"
        )

    msv = overlay.get("merge_semantics_version")
    if msv is not None and msv != _MERGE_SEMANTICS_VERSION:
        _fail(
            f"Overlay merge_semantics_version {msv!r} != expected {_MERGE_SEMANTICS_VERSION!r}"
        )


def _validate_rule_id_uniqueness(overlay: dict[str, Any]) -> None:
    """Validate rule_id uniqueness across ALL rules[] entries."""
    seen_rule_ids: set[str] = set()
    seen_deny_ids: set[str] = set()

    for rule in overlay.get("rules", []):
        rule_id = rule.get("rule_id", "")
        if rule_id in seen_rule_ids:
            _fail(f"Duplicate rule_id {rule_id!r} in overlay rules")
        seen_rule_ids.add(rule_id)

        # Also check deny_rule.id uniqueness
        if rule.get("operation") == "add_deny_rule":
            deny_data = rule.get("deny_rule", {})
            deny_id = deny_data.get("id", "")
            if deny_id in seen_deny_ids:
                _fail(f"Duplicate deny_rule.id {deny_id!r} in overlay rules")
            seen_deny_ids.add(deny_id)


def _validate_deny_rules_strict(overlay: dict[str, Any]) -> None:
    """Build-time strict validation of deny rules. Fail loudly."""
    for rule in overlay.get("rules", []):
        if rule.get("operation") != "add_deny_rule":
            continue
        deny = rule.get("deny_rule", {})
        match_type = deny.get("match_type", "")
        action = deny.get("action", "")
        penalty = deny.get("penalty")

        # match_type "exact" → reject
        if match_type == "exact":
            _fail(
                f"DenyRule {deny.get('id', '<unnamed>')!r}: match_type 'exact' "
                "not allowed for deny rules"
            )

        # match_type must be valid
        if match_type not in ("token", "phrase", "regex"):
            _fail(
                f"DenyRule {deny.get('id', '<unnamed>')!r}: invalid match_type {match_type!r}"
            )

        # Discriminated union
        if action == "drop" and penalty is not None:
            _fail(
                f"DenyRule {deny.get('id', '<unnamed>')!r}: drop action requires "
                "penalty to be null"
            )
        if action == "downrank":
            if penalty is None:
                _fail(
                    f"DenyRule {deny.get('id', '<unnamed>')!r}: downrank action requires "
                    "non-null penalty in (0.0, 1.0]"
                )
            if not (0.0 < penalty <= 1.0):
                _fail(
                    f"DenyRule {deny.get('id', '<unnamed>')!r}: downrank penalty "
                    f"{penalty} outside (0.0, 1.0]"
                )


def _validate_topic_rules(overlay: dict[str, Any]) -> None:
    """Validate add_topic and replace_aliases rules for empty aliases and missing default_facet."""
    for rule in overlay.get("rules", []):
        op = rule.get("operation", "")
        rule_id = rule.get("rule_id", "<unnamed>")

        if op == "add_topic":
            topic = rule.get("topic", {})
            aliases = topic.get("aliases", [])
            if not aliases:
                _fail(f"add_topic rule {rule_id!r}: empty aliases not allowed")
            qp = topic.get("query_plan", {})
            if "default_facet" not in qp:
                _fail(f"add_topic rule {rule_id!r}: query_plan missing default_facet")

        elif op == "replace_aliases":
            aliases = rule.get("aliases", [])
            if not aliases:
                _fail(f"replace_aliases rule {rule_id!r}: empty aliases not allowed")

        elif op == "replace_queries":
            qp = rule.get("query_plan", {})
            if "default_facet" not in qp:
                _fail(
                    f"replace_queries rule {rule_id!r}: query_plan missing default_facet"
                )


def _apply_config_overrides(
    config_overrides: dict[str, Any],
) -> list[AppliedRule]:
    """Apply config_overrides: scalar replace only. Unknown/type-mismatch → warn+skip.

    Returns list of AppliedRule with "config-override:" prefix.
    """
    applied: list[AppliedRule] = []

    for namespace, overrides in config_overrides.items():
        if namespace not in BUILTIN_DEFAULTS:
            logger.warning("Config override: unknown namespace %r; skipping", namespace)
            continue

        if not isinstance(overrides, dict):
            logger.warning(
                "Config override: namespace %r value is not a dict; skipping", namespace
            )
            continue

        defaults = BUILTIN_DEFAULTS[namespace]
        for key, value in overrides.items():
            if key not in defaults:
                logger.warning(
                    "Config override: unknown key %r in namespace %r; skipping",
                    key,
                    namespace,
                )
                continue

            # Null check
            if value is None:
                logger.warning(
                    "Config override: null value for %s.%s is not a valid scalar; skipping",
                    namespace,
                    key,
                )
                continue

            # Type mismatch check
            default_val = defaults[key]
            if isinstance(default_val, float) and not isinstance(value, (int, float)):
                logger.warning(
                    "Config override: type mismatch for %s.%s — expected numeric, got %s; skipping",
                    namespace,
                    key,
                    type(value).__name__,
                )
                continue
            if isinstance(default_val, int) and not isinstance(value, (int, float)):
                logger.warning(
                    "Config override: type mismatch for %s.%s — expected numeric, got %s; skipping",
                    namespace,
                    key,
                    type(value).__name__,
                )
                continue

            applied.append(
                AppliedRule(
                    rule_id=f"config-override:{namespace}.{key}",
                    operation="config_override",
                    target=f"{namespace}.{key}",
                )
            )

    return applied


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_alias_overlay(data: dict[str, Any]) -> Alias:
    """Parse an alias from overlay data, clamping weight with warning."""
    weight = data.get("weight", 0.5)
    clamped = _clamp_weight(weight, f"alias {data.get('text', '<unnamed>')!r}")
    return Alias(
        text=data["text"],
        match_type=data.get("match_type", "token"),
        weight=clamped,
        facet_hint=data.get("facet_hint"),
        source="overlay",
    )


def _clamp_weight(weight: float, context: str) -> float:
    """Clamp weight to [0.0, 1.0] with warning if out-of-bounds."""
    if weight > 1.0:
        logger.warning("Weight clamped from %r to 1.0 in %s", weight, context)
        return 1.0
    if weight < 0.0:
        logger.warning("Weight clamped from %r to 0.0 in %s", weight, context)
        return 0.0
    return weight


def _replace_topic_aliases(topic: TopicRecord, new_aliases: list[Alias]) -> TopicRecord:
    """Create a new TopicRecord with replaced aliases (frozen dataclass)."""
    return TopicRecord(
        topic_key=topic.topic_key,
        family_key=topic.family_key,
        kind=topic.kind,
        canonical_label=topic.canonical_label,
        category_hint=topic.category_hint,
        parent_topic=topic.parent_topic,
        aliases=new_aliases,
        query_plan=topic.query_plan,
        canonical_refs=topic.canonical_refs,
    )


def _parse_facets(qp_data: dict[str, Any]) -> dict[str, list[QuerySpec]]:
    """Parse facets dict from query_plan data."""
    facets: dict[str, list[QuerySpec]] = {}
    for facet_name, specs in qp_data.get("facets", {}).items():
        facets[facet_name] = [
            QuerySpec(
                q=s["q"],
                category=s.get("category"),
                priority=s.get("priority", 1),
            )
            for s in specs
        ]
    return facets


# ---------------------------------------------------------------------------
# Serialization (for writing built inventory to disk)
# ---------------------------------------------------------------------------


def serialize_inventory(inv: CompiledInventory) -> dict[str, Any]:
    """Serialize CompiledInventory to JSON-compatible dict."""
    topics: dict[str, Any] = {}
    for key, t in inv.topics.items():
        topics[key] = {
            "topic_key": t.topic_key,
            "family_key": t.family_key,
            "kind": t.kind,
            "canonical_label": t.canonical_label,
            "category_hint": t.category_hint,
            "parent_topic": t.parent_topic,
            "aliases": [
                {
                    "text": a.text,
                    "match_type": a.match_type,
                    "weight": a.weight,
                    "facet_hint": a.facet_hint,
                    "source": a.source,
                }
                for a in t.aliases
            ],
            "query_plan": {
                "default_facet": t.query_plan.default_facet,
                "facets": {
                    fn: [
                        {"q": s.q, "category": s.category, "priority": s.priority}
                        for s in specs
                    ]
                    for fn, specs in t.query_plan.facets.items()
                },
            },
            "canonical_refs": [
                {
                    "chunk_id": r.chunk_id,
                    "category": r.category,
                    "source_file": r.source_file,
                }
                for r in t.canonical_refs
            ],
        }

    denylist = [
        {
            "id": d.id,
            "pattern": d.pattern,
            "match_type": d.match_type,
            "action": d.action,
            "penalty": d.penalty,
            "reason": d.reason,
        }
        for d in inv.denylist
    ]

    overlay_meta: dict[str, Any] | None = None
    if inv.overlay_meta is not None:
        overlay_meta = {
            "overlay_version": inv.overlay_meta.overlay_version,
            "overlay_schema_version": inv.overlay_meta.overlay_schema_version,
            "applied_rules": [
                {
                    "rule_id": r.rule_id,
                    "operation": r.operation,
                    "target": r.target,
                }
                for r in inv.overlay_meta.applied_rules
            ],
        }

    return {
        "schema_version": inv.schema_version,
        "built_at": inv.built_at,
        "docs_epoch": inv.docs_epoch,
        "topics": topics,
        "denylist": denylist,
        "overlay_meta": overlay_meta,
        "merge_semantics_version": inv.merge_semantics_version,
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(description="Build CCDI inventory")
    parser.add_argument("--force", action="store_true", help="Force rebuild")
    parser.add_argument("--overlay", type=str, help="Path to overlay JSON file")
    parser.add_argument(
        "--output", type=str, default="data/compiled_inventory.json", help="Output path"
    )
    parser.add_argument("--config", type=str, help="Path to config JSON file")
    args = parser.parse_args()

    # In real usage, metadata comes from MCP dump_index_metadata.
    # For CLI, read from a metadata file or MCP call.
    logger.error(
        "MCP client integration not yet implemented. "
        "Use generate_scaffold() and merge_overlay() programmatically."
    )
    sys.exit(1)
