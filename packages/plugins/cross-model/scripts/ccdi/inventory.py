"""CCDI inventory runtime loading.

Loads a pre-built CompiledInventory from JSON with graceful degradation:
schema_version mismatch → warn + best-effort, DenyRule violations → warn-and-skip,
missing overlay_meta → warn + empty.

Import pattern:
    from scripts.ccdi.inventory import load_inventory
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

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

_CURRENT_SCHEMA_VERSION = "1"
_CURRENT_MERGE_SEMANTICS_VERSION = "1"


def load_inventory(path: Path | str) -> CompiledInventory:
    """Load a pre-built inventory file with graceful degradation.

    Resilience rules:
    - schema_version mismatch: warn, best-effort (additive-only evolution)
    - DenyRule load-time validation: warn-and-skip per resilience principle
      - Union violations (drop+non-null, downrank+null): WARNING, "schema corruption"
      - Range violations (penalty <= 0, penalty > 1.0): INFO, "backward-compat skip"
    - merge_semantics_version absent: assume "1" with warning
    - merge_semantics_version mismatch: warn + best-effort
    - missing overlay_meta: warn + empty applied_rules
    """
    path = Path(path)
    text = path.read_text()
    data: dict[str, Any] = json.loads(text)

    # Schema version check — warn, best-effort
    sv = data.get("schema_version", "1")
    if sv != _CURRENT_SCHEMA_VERSION:
        logger.warning(
            "Inventory schema_version %r differs from expected %r; loading best-effort",
            sv,
            _CURRENT_SCHEMA_VERSION,
        )

    # merge_semantics_version — absent → assume "1"
    msv = data.get("merge_semantics_version")
    if msv is None:
        logger.warning(
            "Inventory merge_semantics_version absent; assuming %r",
            _CURRENT_MERGE_SEMANTICS_VERSION,
        )
        msv = _CURRENT_MERGE_SEMANTICS_VERSION
    elif msv != _CURRENT_MERGE_SEMANTICS_VERSION:
        logger.warning(
            "Inventory merge_semantics_version %r differs from expected %r; loading best-effort",
            msv,
            _CURRENT_MERGE_SEMANTICS_VERSION,
        )

    # overlay_meta — missing → warn + None
    overlay_meta: OverlayMeta | None = None
    raw_om = data.get("overlay_meta")
    if raw_om is None:
        logger.warning(
            "Inventory overlay_meta missing; continuing with empty applied_rules"
        )
    else:
        overlay_meta = _parse_overlay_meta(raw_om)

    # Topics
    topics: dict[str, TopicRecord] = {}
    for key, tdata in data.get("topics", {}).items():
        topics[key] = _parse_topic(tdata)

    # Denylist — warn-and-skip invalid rules
    denylist: list[DenyRule] = []
    for rdata in data.get("denylist", []):
        rule = _parse_deny_rule_resilient(rdata)
        if rule is not None:
            denylist.append(rule)

    return CompiledInventory(
        schema_version=sv,
        built_at=data.get("built_at", ""),
        docs_epoch=data.get("docs_epoch"),
        topics=topics,
        denylist=denylist,
        overlay_meta=overlay_meta,
        merge_semantics_version=msv,
    )


def _parse_overlay_meta(data: dict[str, Any]) -> OverlayMeta:
    """Parse OverlayMeta from dict."""
    applied = [
        AppliedRule(
            rule_id=r.get("rule_id", ""),
            operation=r.get("operation", ""),
            target=r.get("target", ""),
        )
        for r in data.get("applied_rules", [])
    ]
    return OverlayMeta(
        overlay_version=data.get("overlay_version", ""),
        overlay_schema_version=data.get("overlay_schema_version", ""),
        applied_rules=applied,
    )


def _parse_topic(data: dict[str, Any]) -> TopicRecord:
    """Parse a TopicRecord from dict."""
    aliases = [_parse_alias(a) for a in data.get("aliases", [])]
    qp_data = data.get("query_plan", {})
    facets: dict[str, list[QuerySpec]] = {}
    for facet_name, specs in qp_data.get("facets", {}).items():
        facets[facet_name] = [
            QuerySpec(
                q=s["q"], category=s.get("category"), priority=s.get("priority", 1)
            )
            for s in specs
        ]
    query_plan = QueryPlan(
        default_facet=qp_data.get("default_facet", "overview"),
        facets=facets,
    )
    refs = [
        DocRef(
            chunk_id=r["chunk_id"],
            category=r["category"],
            source_file=r["source_file"],
        )
        for r in data.get("canonical_refs", [])
    ]
    return TopicRecord(
        topic_key=data["topic_key"],
        family_key=data["family_key"],
        kind=data.get("kind", "leaf"),
        canonical_label=data.get("canonical_label", data["topic_key"]),
        category_hint=data.get("category_hint", data.get("family_key", "")),
        parent_topic=data.get("parent_topic"),
        aliases=aliases,
        query_plan=query_plan,
        canonical_refs=refs,
    )


def _parse_alias(data: dict[str, Any]) -> Alias:
    """Parse an Alias from dict."""
    return Alias(
        text=data["text"],
        match_type=data["match_type"],
        weight=data.get("weight", 0.5),
        facet_hint=data.get("facet_hint"),
        source=data.get("source", "generated"),
    )


def _parse_deny_rule_resilient(data: dict[str, Any]) -> DenyRule | None:
    """Parse a DenyRule with warn-and-skip on validation failure.

    Union violations (drop+non-null, downrank+null): WARNING, "schema corruption" prefix.
    Range violations (penalty <= 0, penalty > 1.0): INFO, "backward-compat skip" prefix.
    """
    rule_id = data.get("id", "<unknown>")
    action = data.get("action", "")
    penalty = data.get("penalty")
    match_type = data.get("match_type", "")

    # match_type validation
    if match_type not in ("token", "phrase", "regex"):
        logger.warning(
            "schema corruption: DenyRule %r has invalid match_type %r; skipping",
            rule_id,
            match_type,
        )
        return None

    # Union violations
    if action == "drop" and penalty is not None:
        logger.warning(
            "schema corruption: DenyRule %r has drop action with non-null penalty %r; skipping",
            rule_id,
            penalty,
        )
        return None

    if action == "downrank" and penalty is None:
        logger.warning(
            "schema corruption: DenyRule %r has downrank action with null penalty; skipping",
            rule_id,
        )
        return None

    # Range violations for downrank
    if action == "downrank" and penalty is not None:
        if not (0.0 < penalty <= 1.0):
            logger.info(
                "backward-compat skip: DenyRule %r has downrank penalty %r outside (0.0, 1.0]; skipping",
                rule_id,
                penalty,
            )
            return None

    try:
        return DenyRule(
            id=data["id"],
            pattern=data["pattern"],
            match_type=match_type,
            action=action,
            penalty=penalty,
            reason=data.get("reason", ""),
        )
    except (ValueError, KeyError) as exc:
        logger.warning("DenyRule %r failed validation: %s; skipping", rule_id, exc)
        return None
