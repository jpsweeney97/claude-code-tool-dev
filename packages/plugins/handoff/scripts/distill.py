"""distill.py — Extract durable knowledge from handoffs.

Deterministic extraction pipeline: parses handoff sections into
subsection-level candidates, classifies durability, computes provenance
hashes, checks exact deduplication, and outputs JSON for the distill
skill to synthesize into Phase 0 learning entries.
"""

from __future__ import annotations

import argparse
import hashlib
import json as json_mod  # avoid shadowing
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from scripts.handoff_parsing import parse_handoff


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


def _document_identity(frontmatter: dict[str, str]) -> str:
    """Extract session_id from frontmatter as document identity.

    Requires session_id — raises ValueError if absent or blank.
    The quality_check hook reports missing session_id but cannot prevent
    a handoff from being written without it (PostToolUse hooks always
    exit 0). This function enforces the invariant.
    """
    session_id = frontmatter.get("session_id", "").strip()
    if not session_id:
        raise ValueError(
            "No session_id in frontmatter. Cannot compute stable "
            "document identity. Handoff may pre-date session_id requirement."
        )
    return session_id


def compute_source_uid(
    document_identity: str,
    section_name: str,
    subsection_heading: str,
    heading_ix: int,
) -> str:
    """Compute deterministic source UID from location identity.

    Uses heading_ix (0-based occurrence count of this heading within the
    section) to disambiguate duplicate ### headings. Always included —
    conditional disambiguation causes multiplicity churn when headings
    change between unique and duplicated.

    Uses canonical JSON hashing for unambiguous key composition (avoids
    delimiter collision if components contain ':'). Format: sha256:<hex>.
    """
    payload = json_mod.dumps({
        "v": 1,
        "doc": document_identity,
        "section": section_name,
        "heading": subsection_heading,
        "heading_ix": heading_ix,
    }, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def compute_content_hash(content: str) -> str:
    """Compute normalized content hash.

    Normalizes whitespace (collapse runs, strip) before hashing so that
    formatting-only changes don't create false non-duplicates.
    """
    normalized = re.sub(r'\s+', ' ', content).strip()
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def make_distill_meta(
    source_uid: str,
    source_anchor: str,
    content_sha256: str,
    distilled_at: str = "",
) -> str:
    """Create a distill-meta HTML comment for provenance tracking.

    Format: <!-- distill-meta {"v": 1, "source_uid": "...", ...} -->

    The skill MUST pass a non-empty distilled_at (ISO date) at append time.
    The script produces candidates with distilled_at="" as a placeholder;
    the skill fills it before writing to learnings.md.
    """
    meta = {
        "v": 1,
        "source_uid": source_uid,
        "source_anchor": source_anchor,
        "content_sha256": content_sha256,
        "distilled_at": distilled_at,
    }
    return f"<!-- distill-meta {json_mod.dumps(meta, sort_keys=True)} -->"


_DISTILL_META_RE = re.compile(r'<!--\s*distill-meta\s+(\{.*?\})\s*-->')


def _extract_distill_metas(learnings_content: str) -> list[dict]:
    """Extract all distill-meta JSON payloads from HTML comments.

    Only searches inside <!-- distill-meta ... --> comments to avoid
    false positives from prose that happens to contain JSON key-value
    patterns.
    """
    metas: list[dict] = []
    for match in _DISTILL_META_RE.finditer(learnings_content):
        try:
            metas.append(json_mod.loads(match.group(1)))
        except (json_mod.JSONDecodeError, ValueError):
            continue
    return metas


def check_exact_dup_source(source_uid: str, learnings_content: str) -> bool:
    """Check if source_uid already exists in learnings.md distill-meta comments."""
    return any(
        m.get("source_uid") == source_uid
        for m in _extract_distill_metas(learnings_content)
    )


def check_exact_dup_content(content_hash: str, learnings_content: str) -> bool:
    """Check if content_hash already exists in learnings.md distill-meta comments."""
    return any(
        m.get("content_sha256") == content_hash
        for m in _extract_distill_metas(learnings_content)
    )


# Sections to extract candidates from
_DISTILL_SECTIONS: tuple[str, ...] = ("Decisions", "Learnings", "Codebase Knowledge", "Gotchas")


def extract_signals(raw_markdown: str) -> dict[str, str]:
    """Extract confidence and reversibility signals from bold-labeled fields."""
    signals: dict[str, str] = {}
    for field in ("Confidence", "Reversibility"):
        pattern = rf'\*\*{field}:\*\*\s*(.+)'
        match = re.search(pattern, raw_markdown)
        if match:
            signals[field.lower()] = match.group(1).strip()
    return signals


def _section_name(heading: str) -> str:
    """Extract bare section name from ## heading."""
    if heading.startswith("## "):
        return heading[3:].strip()
    return heading.strip()


def _make_anchor(handoff_filename: str, section_name: str, subsection_heading: str) -> str:
    """Create a source anchor for provenance."""
    slug = re.sub(r'[^a-z0-9]+', '-', subsection_heading.lower()).strip('-')
    return f"{handoff_filename}#{section_name.lower()}/{slug}"


def extract_candidates(
    handoff_path: str,
    learnings_content: str,
    extra_sections: tuple[str, ...] = (),
) -> dict:
    """Extract distill candidates from a handoff file.

    Returns a dict with handoff metadata and a list of candidates, each
    containing raw_markdown, signals, provenance hashes, and dedup status.

    extra_sections: additional section names to extract (e.g., ("Context",)
    when --include-section Context is passed). Merged with _DISTILL_SECTIONS.
    """
    active_sections = _DISTILL_SECTIONS + extra_sections
    path = Path(handoff_path)
    try:
        handoff = parse_handoff(path)
    except (OSError, UnicodeDecodeError) as exc:
        return {
            "handoff_path": handoff_path,
            "handoff_date": "",
            "handoff_title": "",
            "candidates": [],
            "output_version": 1,
            "error": f"Failed to read handoff file: {exc}",
            "error_code": "HANDOFF_UNREADABLE",
        }
    try:
        doc_id = _document_identity(handoff.frontmatter)
    except ValueError as exc:
        return {
            "handoff_path": handoff_path,
            "handoff_date": "",
            "handoff_title": "",
            "candidates": [],
            "output_version": 1,
            "error": str(exc),
            "error_code": "NO_DOCUMENT_IDENTITY",
        }

    candidates: list[dict] = []

    for section in handoff.sections:
        name = _section_name(section.heading)
        if name not in active_sections:
            continue

        subsections = parse_subsections(section.content)
        heading_counts: dict[str, int] = {}

        for sub in subsections:
            # Skip empty or heading-only subsections
            if not sub.raw_markdown.strip():
                continue
            # Merge preamble (leading text before first ###) into first
            # headed subsection to avoid silent information loss.
            if not sub.heading and any(s.heading for s in subsections):
                for other in subsections:
                    if other.heading:
                        other.raw_markdown = sub.raw_markdown.strip() + "\n\n" + other.raw_markdown
                        break
                continue

            ix = heading_counts.get(sub.heading, 0)
            heading_counts[sub.heading] = ix + 1
            source_uid = compute_source_uid(doc_id, name, sub.heading, heading_ix=ix)
            content_hash = compute_content_hash(sub.raw_markdown)

            # Determine dedup status (4-state matrix)
            source_match = check_exact_dup_source(source_uid, learnings_content)
            content_match = check_exact_dup_content(content_hash, learnings_content)
            if source_match and content_match:
                dedup_status = "EXACT_DUP_SOURCE"
            elif source_match and not content_match:
                dedup_status = "UPDATED_SOURCE"
            elif not source_match and content_match:
                dedup_status = "EXACT_DUP_CONTENT"
            else:
                dedup_status = "NEW"

            candidate: dict = {
                "source_section": name,
                "subsection_heading": sub.heading,
                "raw_markdown": sub.raw_markdown,
                "signals": extract_signals(sub.raw_markdown),
                "source_uid": source_uid,
                "content_sha256": content_hash,
                "source_anchor": _make_anchor(path.name, name, sub.heading),
                "dedup_status": dedup_status,
            }

            # Add durability hint for Codebase Knowledge and Gotchas
            if name in ("Codebase Knowledge", "Gotchas"):
                candidate["durability_hint"] = classify_durability(
                    sub.heading, sub.raw_markdown
                )

            candidates.append(candidate)

    return {
        "handoff_path": handoff_path,
        "handoff_date": handoff.frontmatter.get("date", ""),
        "handoff_title": handoff.frontmatter.get("title", path.stem),
        "candidates": candidates,
        "output_version": 1,
        "error": None,
        "error_code": None,
    }


def main(argv: list[str] | None = None) -> str:
    """CLI entry point. Returns JSON string."""
    parser = argparse.ArgumentParser(description="Extract knowledge candidates from a handoff")
    parser.add_argument("handoff", help="Path to handoff markdown file")
    parser.add_argument("--learnings", help="Path to learnings.md for dedup checking", default="")
    parser.add_argument(
        "--include-section",
        action="append",
        default=[],
        help="Additional section names to extract (e.g., Context). May be repeated.",
    )
    args = parser.parse_args(argv)

    handoff_path = args.handoff
    if not Path(handoff_path).exists():
        return json_mod.dumps({
            "handoff_path": handoff_path,
            "handoff_date": "",
            "handoff_title": "",
            "candidates": [],
            "output_version": 1,
            "error": f"Handoff file not found: {handoff_path}",
            "error_code": "HANDOFF_NOT_FOUND",
        })

    learnings_content = ""
    if args.learnings:
        learnings_path = Path(args.learnings)
        if not learnings_path.exists():
            import sys as _sys
            print(
                f"Warning: learnings file not found: {args.learnings}. "
                "Dedup checking disabled.",
                file=_sys.stderr,
            )
        else:
            try:
                learnings_content = learnings_path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as exc:
                return json_mod.dumps({
                    "handoff_path": handoff_path,
                    "handoff_date": "",
                    "handoff_title": "",
                    "candidates": [],
                    "output_version": 1,
                    "error": f"Failed to read learnings file: {exc}",
                    "error_code": "LEARNINGS_UNREADABLE",
                })

    result = extract_candidates(
        handoff_path, learnings_content,
        extra_sections=tuple(args.include_section),
    )
    return json_mod.dumps(result, indent=2)


if __name__ == "__main__":
    print(main())
    sys.exit(0)
