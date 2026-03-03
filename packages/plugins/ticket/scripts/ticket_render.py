"""Template-based markdown rendering for v1.0 tickets.

Renders a complete ticket markdown file with fenced YAML frontmatter
and ordered sections per the contract.
"""
from __future__ import annotations

from typing import Any


def render_ticket(
    *,
    id: str,
    title: str,
    date: str,
    status: str,
    priority: str,
    problem: str,
    effort: str = "",
    source: dict[str, str] | None = None,
    tags: list[str] | None = None,
    blocked_by: list[str] | None = None,
    blocks: list[str] | None = None,
    contract_version: str = "1.0",
    defer: dict[str, Any] | None = None,
    approach: str = "",
    acceptance_criteria: list[str] | None = None,
    verification: str = "",
    key_files: list[dict[str, str]] | None = None,
    context: str = "",
    prior_investigation: str = "",
    decisions_made: str = "",
    related: str = "",
) -> str:
    """Render a complete v1.0 ticket markdown file.

    Returns the full file content as a string.
    Section ordering follows the contract: Problem -> Context -> Prior Investigation ->
    Approach -> Decisions Made -> Acceptance Criteria -> Verification -> Key Files -> Related.
    """
    source = source or {"type": "ad-hoc", "ref": "", "session": ""}
    tags = tags or []
    blocked_by = blocked_by or []
    blocks = blocks or []

    # --- YAML frontmatter ---
    lines = [
        f"# {id}: {title}",
        "",
        "```yaml",
        f"id: {id}",
        f'date: "{date}"',
        f"status: {status}",
        f"priority: {priority}",
    ]

    if effort:
        lines.append(f"effort: {effort}")

    lines.extend([
        "source:",
        f"  type: {source['type']}",
        f"  ref: \"{source.get('ref', '')}\"",
        f"  session: \"{source.get('session', '')}\"",
        f"tags: {tags}",
        f"blocked_by: {blocked_by}",
        f"blocks: {blocks}",
    ])

    if defer is not None:
        lines.extend([
            "defer:",
            f"  active: {str(defer.get('active', False)).lower()}",
            f"  reason: \"{defer.get('reason', '')}\"",
            f"  deferred_at: \"{defer.get('deferred_at', '')}\"",
        ])

    lines.append(f'contract_version: "{contract_version}"')
    lines.append("```")
    lines.append("")

    # --- Required sections ---
    lines.extend(["## Problem", problem, ""])

    # --- Optional sections (in contract order) ---
    if context:
        lines.extend(["## Context", context, ""])

    if prior_investigation:
        lines.extend(["## Prior Investigation", prior_investigation, ""])

    if approach:
        lines.extend(["## Approach", approach, ""])

    if decisions_made:
        lines.extend(["## Decisions Made", decisions_made, ""])

    # Acceptance criteria.
    if acceptance_criteria:
        lines.append("## Acceptance Criteria")
        for criterion in acceptance_criteria:
            lines.append(f"- [ ] {criterion}")
        lines.append("")

    # Verification.
    if verification:
        lines.extend([
            "## Verification",
            "```bash",
            verification,
            "```",
            "",
        ])

    # Key files.
    if key_files:
        lines.extend([
            "## Key Files",
            "| File | Role | Look For |",
            "|------|------|----------|",
        ])
        for kf in key_files:
            lines.append(f"| {kf.get('file', '')} | {kf.get('role', '')} | {kf.get('look_for', '')} |")
        lines.append("")

    if related:
        lines.extend(["## Related", related, ""])

    return "\n".join(lines)
