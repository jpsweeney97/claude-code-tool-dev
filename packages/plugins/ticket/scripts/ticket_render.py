"""Template-based markdown rendering for v1.0 tickets.

Renders a complete ticket markdown file with fenced YAML frontmatter
and ordered sections per the contract.
"""
from __future__ import annotations

from typing import Any

import yaml


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

    # --- YAML frontmatter (safe_dump prevents injection via special chars) ---
    frontmatter: dict[str, Any] = {
        "id": id,
        "date": date,
        "status": status,
        "priority": priority,
    }
    if effort:
        frontmatter["effort"] = effort
    frontmatter["source"] = {
        "type": source["type"],
        "ref": source.get("ref", ""),
        "session": source.get("session", ""),
    }
    frontmatter["tags"] = tags
    frontmatter["blocked_by"] = blocked_by
    frontmatter["blocks"] = blocks

    if defer is not None:
        frontmatter["defer"] = {
            "active": defer.get("active", False),
            "reason": defer.get("reason", ""),
            "deferred_at": defer.get("deferred_at", ""),
        }

    frontmatter["contract_version"] = contract_version

    yaml_str = yaml.safe_dump(
        frontmatter,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
    ).rstrip("\n")

    lines = [
        f"# {id}: {title}",
        "",
        "```yaml",
        yaml_str,
        "```",
        "",
    ]

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
