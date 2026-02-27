"""distill.py — Extract durable knowledge from handoffs.

Deterministic extraction pipeline: parses handoff sections into
subsection-level candidates, classifies durability, computes provenance
hashes, checks exact deduplication, and outputs JSON for the distill
skill to synthesize into Phase 0 learning entries.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Subsection:
    """A ### subsection extracted from a ## section's content."""

    heading: str  # Bare heading text (no ### prefix). Empty if no heading.
    raw_markdown: str  # Full markdown content of this subsection.


# Durability classification keywords
_DURABLE_KEYWORDS: tuple[str, ...] = (
    "pattern",
    "convention",
    "gotcha",
    "invariant",
    "constraint",
    "rule",
    "principle",
    "anti-pattern",
    "antipattern",
    "workaround",
)

_EPHEMERAL_KEYWORDS: tuple[str, ...] = (
    "architecture",
    "structure",
    "overview",
    "layout",
    "key locations",
    "key code locations",
    "file:line",
    "dependency",
    "version",
    "current state",
)


def parse_subsections(content: str) -> list[Subsection]:
    """Split a ## section's content into ### subsections.

    Returns one Subsection per ### heading. If content has no ###
    headings, returns a single Subsection with empty heading containing
    the full content. Leading text before the first ### heading is
    returned as a Subsection with empty heading.

    Code fences (both backtick ``` and tilde ~~~) are tracked to avoid
    false splits on ### inside fences. #### headings are NOT split —
    extraction granularity is ### only.
    """
    if not content:
        return [Subsection(heading="", raw_markdown="")]

    lines = content.splitlines(keepends=True)
    subsections: list[Subsection] = []
    current_heading = ""
    current_lines: list[str] = []
    inside_fence = False
    fence_marker = ""  # Track which fence type opened (``` or ~~~)

    for line in lines:
        stripped = line.rstrip()
        if not inside_fence and (
            stripped.startswith("```") or stripped.startswith("~~~")
        ):
            inside_fence = True
            fence_marker = stripped[:3]
        elif inside_fence and stripped.startswith(fence_marker):
            inside_fence = False
            fence_marker = ""

        if not inside_fence and line.startswith("### "):
            # Save previous subsection
            text = "".join(current_lines).strip()
            if current_heading or text:
                subsections.append(
                    Subsection(
                        heading=current_heading,
                        raw_markdown=text,
                    )
                )
            current_heading = line[4:].strip()
            current_lines = []
        else:
            current_lines.append(line)

    # Save last subsection
    text = "".join(current_lines).strip()
    if current_heading or text or not subsections:
        subsections.append(
            Subsection(
                heading=current_heading,
                raw_markdown=text,
            )
        )

    return subsections


def classify_durability(heading: str, content: str) -> str:
    """Classify a Codebase Knowledge subsection's durability.

    Returns "likely_durable", "likely_ephemeral", or "unknown".
    Uses keyword matching on heading and content. The distill skill
    makes the final inclusion decision — this is directional only.
    """
    heading_lower = heading.lower()
    content_lower = content.lower()

    # Check heading for durable keywords first
    for keyword in _DURABLE_KEYWORDS:
        if keyword in heading_lower:
            return "likely_durable"

    # Check heading for ephemeral keywords
    for keyword in _EPHEMERAL_KEYWORDS:
        if keyword in heading_lower:
            return "likely_ephemeral"

    # Fall back to content keywords (can upgrade unknown to durable)
    for keyword in _DURABLE_KEYWORDS:
        if keyword in content_lower:
            return "likely_durable"

    return "unknown"
