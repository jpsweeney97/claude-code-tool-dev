"""CCDI topic classifier pipeline.

Two-stage pure function: candidate generation (recall-biased) followed by
ambiguity resolution (precision-biased). Takes input text and a compiled
inventory, returns resolved topics with confidence levels and facet hints.

Import pattern:
    from scripts.ccdi.classifier import classify
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

from scripts.ccdi.config import CCDIConfig
from scripts.ccdi.types import (
    Alias,
    ClassifierResult,
    CompiledInventory,
    DenyRule,
    MatchedAlias,
    ResolvedTopic,
    SuppressedCandidate,
    TopicRecord,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Match type priority (lower number = higher priority)
# ---------------------------------------------------------------------------

_MATCH_TYPE_PRIORITY: dict[str, int] = {
    "exact": 0,
    "phrase": 1,
    "token": 2,
    "regex": 3,
}

# Generic terms that act as facet modifiers, not topic selectors.
# Populated from denylist entries with action="downrank".
# Additionally these well-known terms are always treated as generic.
_BUILTIN_GENERIC_TERMS: frozenset[str] = frozenset(
    {"schema", "config", "configuration", "json", "settings", "overview"}
)

# ---------------------------------------------------------------------------
# Internal candidate types
# ---------------------------------------------------------------------------


@dataclass
class _AliasMatch:
    """A single alias match found during candidate generation."""

    alias: Alias
    span: tuple[int, int]
    effective_weight: float


@dataclass
class _Candidate:
    """A candidate topic from Stage 1."""

    topic_key: str
    topic: TopicRecord
    matches: list[_AliasMatch] = field(default_factory=list)
    score: float = 0.0
    facet_hint: str | None = None
    has_anchor: bool = False  # True if any non-generic match exists


# ---------------------------------------------------------------------------
# Text normalization
# ---------------------------------------------------------------------------


def _normalize_text(text: str) -> str:
    """Normalize input text: strip backticks, collapse whitespace."""
    # Remove backtick wrappers (common in markdown)
    text = text.replace("`", "")
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ---------------------------------------------------------------------------
# Denylist application
# ---------------------------------------------------------------------------


def _build_deny_map(
    denylist: list[DenyRule],
) -> dict[str, tuple[str, float | None]]:
    """Build a lookup from lowercased pattern → (action, penalty).

    Only handles token and phrase deny rules. Regex deny rules would need
    separate handling (not needed for current inventory).
    """
    deny_map: dict[str, tuple[str, float | None]] = {}
    for rule in denylist:
        if rule.match_type in ("token", "phrase"):
            deny_map[rule.pattern.lower()] = (rule.action, rule.penalty)
    return deny_map


def _apply_deny(
    alias: Alias,
    deny_map: dict[str, tuple[str, float | None]],
) -> float:
    """Apply denylist to an alias, returning effective weight.

    Returns 0.0 if the alias is dropped.
    """
    key = alias.text.lower()
    if key in deny_map:
        action, penalty = deny_map[key]
        if action == "drop":
            return 0.0
        if action == "downrank" and penalty is not None:
            return max(0.0, alias.weight - penalty)
    return alias.weight


# ---------------------------------------------------------------------------
# Stage 1: Candidate Generation
# ---------------------------------------------------------------------------


def _find_exact_match(
    alias_text: str, text: str
) -> tuple[int, int] | None:
    """Find case-sensitive exact match at word boundaries.

    Word boundary: the matched text must NOT be preceded or followed by
    [a-zA-Z0-9_].
    """
    start = 0
    while True:
        idx = text.find(alias_text, start)
        if idx == -1:
            return None
        end = idx + len(alias_text)
        # Check word boundaries
        preceded_by_word = idx > 0 and re.match(r"[a-zA-Z0-9_]", text[idx - 1])
        followed_by_word = end < len(text) and re.match(
            r"[a-zA-Z0-9_]", text[end]
        )
        if not preceded_by_word and not followed_by_word:
            return (idx, end)
        start = idx + 1
    return None


def _find_phrase_match(
    alias_text: str, text: str
) -> tuple[int, int] | None:
    """Find case-insensitive multi-word match."""
    lower_text = text.lower()
    lower_alias = alias_text.lower()
    idx = lower_text.find(lower_alias)
    if idx == -1:
        return None
    return (idx, idx + len(alias_text))


def _find_token_match(
    alias_text: str, text: str
) -> tuple[int, int] | None:
    """Find case-insensitive single-word match."""
    pattern = re.compile(r"\b" + re.escape(alias_text) + r"\b", re.IGNORECASE)
    m = pattern.search(text)
    if m:
        return (m.start(), m.end())
    return None


def _find_regex_match(
    alias_text: str, text: str
) -> tuple[int, int] | None:
    """Find regex pattern match."""
    try:
        m = re.search(alias_text, text)
        if m:
            return (m.start(), m.end())
    except re.error:
        logger.warning("Invalid regex pattern in alias: %r", alias_text)
    return None


_MATCH_FINDERS = {
    "exact": _find_exact_match,
    "phrase": _find_phrase_match,
    "token": _find_token_match,
    "regex": _find_regex_match,
}


def _is_generic_term(alias: Alias, deny_map: dict[str, tuple[str, float | None]]) -> bool:
    """Check if an alias is a generic/denied term (facet modifier, not topic anchor)."""
    lower = alias.text.lower()
    if lower in _BUILTIN_GENERIC_TERMS:
        return True
    if lower in deny_map:
        return True
    return False


def _generate_candidates(
    text: str,
    inventory: CompiledInventory,
    deny_map: dict[str, tuple[str, float | None]],
) -> dict[str, _Candidate]:
    """Stage 1: Generate candidates by scanning all aliases.

    Evaluation order: exact > phrase > token > regex.
    Within same type, longer alias text takes precedence.
    Cross-type suppression: higher-priority match suppresses lower on same topic.
    Repeated mentions of same alias do NOT inflate score.
    """
    candidates: dict[str, _Candidate] = {}

    for topic_key, topic in inventory.topics.items():
        # Group aliases by match type, sort by length desc within each type
        aliases_by_type: dict[str, list[Alias]] = {}
        for alias in topic.aliases:
            mt = alias.match_type
            if mt not in aliases_by_type:
                aliases_by_type[mt] = []
            aliases_by_type[mt].append(alias)

        # Sort each group by text length descending (longer = more specific)
        for mt in aliases_by_type:
            aliases_by_type[mt].sort(key=lambda a: len(a.text), reverse=True)

        # Track which alias texts have already matched (for dedup)
        matched_alias_texts: set[str] = set()
        # Track which match types have contributed a match
        matched_type_priorities: set[int] = set()
        # Collect surviving matches
        surviving_matches: list[_AliasMatch] = []
        has_anchor = False

        # Process in priority order: exact, phrase, token, regex
        for mt in ["exact", "phrase", "token", "regex"]:
            if mt not in aliases_by_type:
                continue
            mt_priority = _MATCH_TYPE_PRIORITY[mt]

            for alias in aliases_by_type[mt]:
                # Skip if this alias text already matched
                if alias.text in matched_alias_texts:
                    continue

                finder = _MATCH_FINDERS.get(mt)
                if finder is None:
                    continue

                span = finder(alias.text, text)
                if span is None:
                    continue

                # Apply denylist
                effective_weight = _apply_deny(alias, deny_map)
                if effective_weight <= 0.0:
                    continue

                # Cross-type suppression: check if a higher-priority type
                # already matched on this topic. If so, this lower-priority
                # match is suppressed.
                # "higher-priority match on a topic suppresses lower-priority
                # matches on the SAME topic" — but only for the SAME alias
                # text, not all aliases. The spec says "a higher-priority match
                # on a topic suppresses lower-priority matches on the same
                # topic from contributing to the score — e.g., an exact match
                # for alias X prevents a token match for the same alias X."
                #
                # Interpretation: suppress the SAME underlying concept
                # (overlapping text), not unrelated aliases on the same topic.
                # For different alias texts (e.g., "Alpha" exact + "beta gamma"
                # phrase on same topic), both contribute.
                #
                # We check: does this match's text overlap with any
                # higher-priority match already recorded?
                suppressed = False
                for existing in surviving_matches:
                    existing_priority = _MATCH_TYPE_PRIORITY[
                        existing.alias.match_type
                    ]
                    if existing_priority < mt_priority:
                        # Check text overlap: if the lower-priority alias text
                        # is contained in (or overlaps with) the higher-priority
                        # match's span, suppress.
                        # Simple check: does the token alias text appear within
                        # the span of the existing match in the input?
                        ex_start, ex_end = existing.span
                        ma_start, ma_end = span
                        if _spans_overlap(
                            (ex_start, ex_end), (ma_start, ma_end)
                        ):
                            suppressed = True
                            break
                        # Also check: same alias text (different case)
                        if alias.text.lower() == existing.alias.text.lower():
                            suppressed = True
                            break

                if suppressed:
                    continue

                matched_alias_texts.add(alias.text)
                matched_type_priorities.add(mt_priority)

                is_generic = _is_generic_term(alias, deny_map)
                if not is_generic:
                    has_anchor = True

                surviving_matches.append(
                    _AliasMatch(
                        alias=alias,
                        span=span,
                        effective_weight=effective_weight,
                    )
                )

        if surviving_matches:
            score = sum(m.effective_weight for m in surviving_matches)
            # Determine facet hint from generic terms present
            facet_hint = _extract_facet_hint(text, deny_map)
            candidates[topic_key] = _Candidate(
                topic_key=topic_key,
                topic=topic,
                matches=surviving_matches,
                score=score,
                facet_hint=facet_hint,
                has_anchor=has_anchor,
            )

    return candidates


def _spans_overlap(a: tuple[int, int], b: tuple[int, int]) -> bool:
    """Check if two spans overlap."""
    return a[0] < b[1] and b[0] < a[1]


def _extract_facet_hint(
    text: str, deny_map: dict[str, tuple[str, float | None]]
) -> str | None:
    """Extract facet hint from generic terms in the text.

    Generic terms like 'schema', 'config' shift the facet rather than
    identifying a topic.
    """
    lower = text.lower()
    # Check for known facet-shifting terms
    facet_terms: dict[str, str] = {
        "schema": "schema",
        "input": "input",
        "output": "output",
        "config": "config",
        "configuration": "config",
        "control": "control",
    }
    for term, facet in facet_terms.items():
        # Match as whole word
        if re.search(r"\b" + re.escape(term) + r"\b", lower):
            return facet
    return None


# ---------------------------------------------------------------------------
# Stage 2: Ambiguity Resolution
# ---------------------------------------------------------------------------


def _resolve_candidates(
    candidates: dict[str, _Candidate],
    config: CCDIConfig,
) -> ClassifierResult:
    """Stage 2: Apply four deterministic resolution rules.

    1. Prefer leaf over family
    2. Generic terms are facet modifiers
    3. Collapse nested family matches
    4. Suppress orphaned generics
    """
    resolved: list[ResolvedTopic] = []
    suppressed: list[SuppressedCandidate] = []

    # Rule 4: Suppress orphaned generics (no anchor)
    # Do this first so they don't interfere with other rules
    active: dict[str, _Candidate] = {}
    for key, cand in candidates.items():
        if not cand.has_anchor:
            suppressed.append(
                SuppressedCandidate(
                    topic_key=key,
                    reason="orphaned generic: no non-generic anchor match",
                )
            )
        else:
            active[key] = cand

    # Group by family
    families: dict[str, list[str]] = {}
    for key, cand in active.items():
        fk = cand.topic.family_key
        if fk not in families:
            families[fk] = []
        families[fk].append(key)

    # Rule 1: Prefer leaf over family
    # If a leaf has a strong match, absorb the parent family
    for family_key, members in families.items():
        family_cand = active.get(family_key)
        leaf_members = [
            k for k in members if active[k].topic.kind == "leaf"
        ]
        strong_leaves = [
            k for k in leaf_members if active[k].score >= config.classifier_confidence_medium_min_score
        ]

        if family_cand and family_cand.topic.kind == "family" and strong_leaves:
            # Family absorbed by strong leaf(s)
            suppressed.append(
                SuppressedCandidate(
                    topic_key=family_key,
                    reason="family collapsed under stronger leaf",
                )
            )
            active.pop(family_key, None)
            # Update the members list
            families[family_key] = [
                k for k in members if k != family_key
            ]

    # Rule 3: Collapse nested family matches
    # Multiple weak leaves in same family → elevate to family
    for family_key, members in families.items():
        leaf_members = [
            k for k in members
            if k in active and active[k].topic.kind == "leaf"
        ]
        if len(leaf_members) < 2:
            continue

        # Check if ALL leaves are weak
        all_weak = all(
            active[k].score < config.classifier_confidence_medium_min_score
            for k in leaf_members
        )
        if not all_weak:
            continue

        # Collapse: remove leaves, add/keep family at overview
        for lk in leaf_members:
            suppressed.append(
                SuppressedCandidate(
                    topic_key=lk,
                    reason=f"weak leaf collapsed into family {family_key}",
                )
            )
            active.pop(lk, None)

        # Ensure family topic exists in the inventory
        # Build a family-level resolved topic
        # Collect all matches from collapsed leaves
        all_matches: list[_AliasMatch] = []
        combined_score = 0.0
        for lk in leaf_members:
            cand = candidates[lk]  # Use original candidates, not active
            all_matches.extend(cand.matches)
            combined_score += cand.score

        # Also include any family-level match if it existed
        family_orig = candidates.get(family_key)
        if family_orig:
            all_matches.extend(family_orig.matches)
            combined_score += family_orig.score

        # Create a synthetic family candidate
        family_topic = None
        # Try to find the family topic in the inventory
        for tk, t in candidates.items():
            if t.topic.topic_key == family_key and t.topic.kind == "family":
                family_topic = t.topic
                break

        if family_topic is None:
            # Family topic might not be in candidates (wasn't matched).
            # The resolved topic is built above regardless; family_topic
            # lookup is best-effort for potential future use.
            pass

        # Add as a resolved family topic directly
        confidence = _compute_confidence(combined_score, all_matches, config)
        matched = [
            MatchedAlias(text=m.alias.text, span=m.span, weight=m.effective_weight)
            for m in all_matches
        ]
        resolved.append(
            ResolvedTopic(
                topic_key=family_key,
                family_key=family_key,
                coverage_target="family",
                confidence=confidence,
                facet="overview",
                matched_aliases=matched,
                reason=f"collapsed {len(leaf_members)} weak leaves into family",
            )
        )

    # Build resolved topics from remaining active candidates
    for key, cand in active.items():
        confidence = _compute_confidence(cand.score, cand.matches, config)

        # Determine facet
        facet = _determine_facet(cand)

        matched = [
            MatchedAlias(
                text=m.alias.text, span=m.span, weight=m.effective_weight
            )
            for m in cand.matches
        ]

        reason_parts = []
        for m in cand.matches:
            reason_parts.append(f"{m.alias.match_type} {m.alias.text!r}")
        reason = ", ".join(reason_parts)

        resolved.append(
            ResolvedTopic(
                topic_key=key,
                family_key=cand.topic.family_key,
                coverage_target=cand.topic.kind,
                confidence=confidence,
                facet=facet,
                matched_aliases=matched,
                reason=reason,
            )
        )

    # Sort resolved topics for deterministic output (by topic_key)
    resolved.sort(key=lambda r: r.topic_key)
    suppressed.sort(key=lambda s: s.topic_key)

    return ClassifierResult(
        resolved_topics=resolved,
        suppressed_candidates=suppressed,
    )


def _compute_confidence(
    score: float,
    matches: list[_AliasMatch],
    config: CCDIConfig,
) -> str:
    """Compute confidence level from score and match characteristics.

    high:   at least one exact/phrase match with weight >= high_min_weight
    medium: cumulative score >= medium_min_score OR one match with weight >= medium_min_single_weight
    low:    below medium thresholds
    """
    # High: at least one exact/phrase match with weight >= threshold
    for m in matches:
        if m.alias.match_type in ("exact", "phrase"):
            if m.effective_weight >= config.classifier_confidence_high_min_weight:
                return "high"

    # Medium: cumulative score >= threshold OR single match >= threshold
    if score >= config.classifier_confidence_medium_min_score:
        return "medium"
    for m in matches:
        if m.effective_weight >= config.classifier_confidence_medium_min_single_weight:
            return "medium"

    return "low"


def _determine_facet(cand: _Candidate) -> str:
    """Determine the facet for a resolved topic.

    Uses facet_hint from generic terms, falling back to the topic's
    default_facet from its query_plan. If the hinted facet isn't available
    in the query plan, falls back to default.
    """
    default_facet = cand.topic.query_plan.default_facet
    available_facets = set(cand.topic.query_plan.facets.keys())

    # Check alias-level facet hints first
    for m in cand.matches:
        if m.alias.facet_hint and m.alias.facet_hint in available_facets:
            return m.alias.facet_hint

    # Check extracted facet hint from generic terms
    if cand.facet_hint:
        if cand.facet_hint in available_facets:
            return cand.facet_hint
        # Facet not available — fall back to default
        return default_facet

    return default_facet


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def classify(
    text: str,
    inventory: CompiledInventory,
    config: CCDIConfig,
) -> ClassifierResult:
    """Classify input text against the topic inventory.

    Two-stage pipeline:
    1. Candidate generation (recall-biased): linear scan over all aliases
    2. Ambiguity resolution (precision-biased): four deterministic rules

    Args:
        text: Input text to classify.
        inventory: Compiled topic inventory snapshot.
        config: CCDI configuration with classifier thresholds.

    Returns:
        ClassifierResult with resolved topics and suppressed candidates.
    """
    normalized = _normalize_text(text)
    if not normalized:
        return ClassifierResult(resolved_topics=[], suppressed_candidates=[])

    deny_map = _build_deny_map(inventory.denylist)
    candidates = _generate_candidates(normalized, inventory, deny_map)

    if not candidates:
        return ClassifierResult(resolved_topics=[], suppressed_candidates=[])

    return _resolve_candidates(candidates, config)
