"""CCDI packet builder.

Builds FactPackets from search results, applies deduplication, quality
thresholds, budget constraints, and renders to markdown for injection.

Import pattern:
    from scripts.ccdi.packets import build_packet, render_initial, render_mid_turn
"""

from __future__ import annotations

import logging
import re

from scripts.ccdi.config import CCDIConfig
from scripts.ccdi.types import DocRef, FactItem, FactPacket, TopicRegistryEntry

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Token estimation
# ---------------------------------------------------------------------------

_CHARS_PER_TOKEN = 4


def _estimate_tokens(text: str) -> int:
    """Estimate token count. Heuristic: ~4 characters per token."""
    return max(1, len(text) // _CHARS_PER_TOKEN)


# ---------------------------------------------------------------------------
# Mode selection
# ---------------------------------------------------------------------------

# Backtick pattern: content with backtick-delimited identifiers (field names,
# enum values, flags, JSON schema fragments)
_BACKTICK_RE = re.compile(r"`[^`]+`")


def _select_mode(content: str) -> str:
    """Decide snippet vs paraphrase based on content type.

    snippet: field names, enum values, flags, JSON schema fragments
             (detected by backtick patterns)
    paraphrase: conceptual behavior, sequencing, design implications
    Default: paraphrase
    """
    backtick_matches = _BACKTICK_RE.findall(content)
    if not backtick_matches:
        return "paraphrase"

    # If backtick content dominates (>30% of content length), use snippet
    backtick_chars = sum(len(m) for m in backtick_matches)
    if backtick_chars > len(content) * 0.3:
        return "snippet"

    return "paraphrase"


# ---------------------------------------------------------------------------
# Paraphrase extraction (extractive, not generative)
# ---------------------------------------------------------------------------

_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")


def _extract_paraphrase(content: str, facet: str, budget_chars: int) -> str:
    """Pick most relevant sentence(s) from content based on facet keyword overlap.

    Deterministic: tied-score sentences broken by position (first wins).
    Trimmed to budget.
    """
    sentences = _SENTENCE_RE.split(content.strip())
    if not sentences:
        return content[:budget_chars]

    facet_keywords = set(facet.lower().split("_"))

    # Score sentences by keyword overlap
    scored: list[tuple[int, int, str]] = []
    for idx, sentence in enumerate(sentences):
        sentence = sentence.strip()
        if not sentence:
            continue
        words = set(sentence.lower().split())
        overlap = len(facet_keywords & words)
        # Negative overlap for reverse sort; idx for tiebreaker (ascending)
        scored.append((-overlap, idx, sentence))

    scored.sort()

    # Accumulate sentences within budget
    selected: list[str] = []
    total_chars = 0
    for _neg_overlap, _idx, sentence in scored:
        if total_chars + len(sentence) + 1 > budget_chars and selected:
            break
        selected.append(sentence)
        total_chars += len(sentence) + 1  # +1 for space

    if not selected:
        # At minimum, take the first sentence trimmed to budget
        return sentences[0].strip()[:budget_chars]

    return " ".join(selected)


# ---------------------------------------------------------------------------
# Snippet extraction
# ---------------------------------------------------------------------------


def _extract_snippet(content: str, budget_chars: int) -> str:
    """Extract snippet text: backtick-delimited items from content.

    Truncates to budget.
    """
    matches = _BACKTICK_RE.findall(content)
    if not matches:
        return content[:budget_chars]

    result = "\n".join(f"- {m}" for m in matches)
    if len(result) > budget_chars:
        # Trim to fit
        lines = result.split("\n")
        trimmed: list[str] = []
        total = 0
        for line in lines:
            if total + len(line) + 1 > budget_chars and trimmed:
                break
            trimmed.append(line)
            total += len(line) + 1
        result = "\n".join(trimmed)

    return result


# ---------------------------------------------------------------------------
# Core: build_packet
# ---------------------------------------------------------------------------


def build_packet(
    results: list[dict],
    mode: str,
    config: CCDIConfig,
    registry_entry: TopicRegistryEntry | None = None,
    facet: str = "overview",
) -> FactPacket | None:
    """Build a fact packet from search results. Returns None if empty.

    Process:
    1. Dedupe against injected_chunk_ids from registry entry
    2. Filter by quality threshold
    3. Rank by score (tiebreaker: chunk_id ascending)
    4. Enforce topic cardinality
    5. Build facts within budget
    6. Return None if quality_min_useful_facts not met
    """
    if not results:
        return None

    # --- Dedup against already-injected chunks ---
    injected_ids: set[str] = set()
    if registry_entry is not None:
        injected_ids = set(registry_entry.coverage_injected_chunk_ids)

    filtered = [r for r in results if r["chunk_id"] not in injected_ids]
    if not filtered:
        return None

    # --- Quality threshold: filter by score ---
    quality_min = config.packets_quality_min_result_score
    filtered = [r for r in filtered if r.get("score", 0) >= quality_min]
    if not filtered:
        return None

    # --- Rank: by score descending, tiebreaker chunk_id ascending ---
    filtered.sort(key=lambda r: (-r.get("score", 0), r["chunk_id"]))

    # --- Mode-specific limits ---
    if mode == "mid_turn":
        max_topics = config.packets_mid_turn_max_topics
        max_facts = config.packets_mid_turn_max_facts
        token_budget_max = config.packets_mid_turn_token_budget_max
    else:
        max_topics = config.packets_initial_max_topics
        max_facts = config.packets_initial_max_facts
        token_budget_max = config.packets_initial_token_budget_max

    # --- Topic cardinality enforcement ---
    # Derive topic keys from category of results
    topic_keys_seen: list[str] = []
    topic_limited: list[dict] = []
    for r in filtered:
        topic_key = r.get("category", "unknown")
        if topic_key not in topic_keys_seen:
            if len(topic_keys_seen) >= max_topics:
                continue
            topic_keys_seen.append(topic_key)
        topic_limited.append(r)

    if not topic_limited:
        return None

    # --- Build facts within budget ---
    facts: list[FactItem] = []
    total_tokens = 0
    snippet_count = 0
    budget_chars = token_budget_max * _CHARS_PER_TOKEN

    for r in topic_limited:
        if len(facts) >= max_facts:
            break

        content = r.get("content", "")
        chunk_id = r["chunk_id"]
        category = r.get("category", "unknown")
        source_file = r.get("source_file", "")

        # Mode selection
        fact_mode = _select_mode(content)

        # Mid-turn: at most 1 snippet
        if mode == "mid_turn" and fact_mode == "snippet" and snippet_count >= 1:
            fact_mode = "paraphrase"

        # Remaining budget in chars
        remaining_chars = budget_chars - (total_tokens * _CHARS_PER_TOKEN)
        if remaining_chars <= 0:
            break

        # Extract text
        if fact_mode == "snippet":
            text = _extract_snippet(content, remaining_chars)
            snippet_count += 1
        else:
            text = _extract_paraphrase(content, facet, remaining_chars)

        if not text:
            continue

        fact_tokens = _estimate_tokens(text)

        # Check budget
        if total_tokens + fact_tokens > token_budget_max and facts:
            break

        ref = DocRef(
            chunk_id=chunk_id,
            category=category,
            source_file=source_file,
        )
        facts.append(
            FactItem(
                mode=fact_mode,
                facet=facet,
                text=text,
                refs=[ref],
            )
        )
        total_tokens += fact_tokens

    # --- Quality gate: min useful facts ---
    if len(facts) < config.packets_quality_min_useful_facts:
        return None

    # --- Derive final topic list from facts ---
    final_topics: list[str] = []
    for f in facts:
        for ref in f.refs:
            if ref.category not in final_topics:
                final_topics.append(ref.category)

    if not final_topics:
        return None

    return FactPacket(
        packet_kind=mode,
        topics=final_topics,
        facet=facet,
        facts=facts,
        token_estimate=total_tokens,
    )


# ---------------------------------------------------------------------------
# Renderers
# ---------------------------------------------------------------------------


def _format_citation(chunk_id: str) -> str:
    """Format a citation reference."""
    return f"[ccdocs:{chunk_id}]"


def render_initial(packet: FactPacket) -> str:
    """Render initial injection markdown under ### Claude Code Extension Reference.

    Render order: paraphrase-mode facts first, then snippet-mode facts.
    Each fact gets an inline citation.
    """
    lines: list[str] = []
    lines.append("### Claude Code Extension Reference")

    # Topic list
    topic_str = ", ".join(f"`{t}`" for t in packet.topics)
    lines.append(f"Detected topics: {topic_str}")
    lines.append("")

    # Separate paraphrase and snippet facts
    paraphrase_facts = [f for f in packet.facts if f.mode == "paraphrase"]
    snippet_facts = [f for f in packet.facts if f.mode == "snippet"]

    # Paraphrase facts first
    for fact in paraphrase_facts:
        citations = " ".join(_format_citation(ref.chunk_id) for ref in fact.refs)
        lines.append(f"- {fact.text}")
        lines.append(f"  {citations}")

    # Snippet facts
    if snippet_facts:
        lines.append("")
        lines.append("Exact fields:")
        for fact in snippet_facts:
            citations = " ".join(_format_citation(ref.chunk_id) for ref in fact.refs)
            lines.append(f"- {fact.text}")
            lines.append(f"  {citations}")

    return "\n".join(lines)


def render_mid_turn(packet: FactPacket) -> str:
    """Render mid-turn injection with <!-- ccdi-packet --> metadata comment.

    Render order: paraphrase-mode facts first, then snippet-mode facts.
    Each fact gets an inline citation.
    """
    lines: list[str] = []

    # Metadata comment
    topics_str = ",".join(packet.topics)
    lines.append(f'<!-- ccdi-packet topics="{topics_str}" facet="{packet.facet}" -->')
    lines.append("Claude Code docs context:")

    # Separate paraphrase and snippet facts
    paraphrase_facts = [f for f in packet.facts if f.mode == "paraphrase"]
    snippet_facts = [f for f in packet.facts if f.mode == "snippet"]

    # Paraphrase facts first
    for fact in paraphrase_facts:
        citations = " ".join(_format_citation(ref.chunk_id) for ref in fact.refs)
        lines.append(f"- {fact.text}")
        lines.append(f"  {citations}")

    # Snippet facts
    for fact in snippet_facts:
        citations = " ".join(_format_citation(ref.chunk_id) for ref in fact.refs)
        lines.append(f"- {fact.text}")
        lines.append(f"  {citations}")

    return "\n".join(lines)
