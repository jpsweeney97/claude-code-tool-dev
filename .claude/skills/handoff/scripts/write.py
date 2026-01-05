#!/usr/bin/env python3
"""
write.py - Create a handoff document from session context.

Part of the handoff skill.

Responsibilities:
- Gather git state (branch, commit, uncommitted files)
- Generate structured handoff markdown
- Write to project and global locations
- Enforce retention policy

Usage:
    python write.py --title "description" [options]
    echo '{"title": "...", "goal": "..."}' | python write.py --stdin

Examples:
    python write.py --title "JWT auth middleware" --goal "Enable stateless auth"
    python write.py --title "Bug fix" --decisions '["Used retry logic"]'

Exit Codes:
    0  - Success
    1  - Input error (missing required fields)
    2  - Write error (permission, disk)
"""

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from common import Result, get_project_name, get_project_handoffs_dir, get_global_handoffs_dir


def parse_flexible_list(value: str) -> List[str]:
    """Parse a list from JSON array or comma-separated string.

    Accepts:
        '["a", "b", "c"]'  -> ["a", "b", "c"]  (JSON array)
        'a,b,c'            -> ["a", "b", "c"]  (comma-separated)
        'a, b, c'          -> ["a", "b", "c"]  (with spaces)
    """
    value = value.strip()
    if not value:
        return []

    # Try JSON first
    if value.startswith("["):
        try:
            result = json.loads(value)
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass

    # Fall back to comma-separated
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass
class GitState:
    """Git repository state."""
    is_repo: bool = False
    branch: Optional[str] = None
    commit: Optional[str] = None
    uncommitted: List[str] = field(default_factory=list)


def get_git_state() -> GitState:
    """Gather git state if in a repository."""
    state = GitState()

    try:
        # Check if in git repo
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0:
            return state

        state.is_repo = True

        # Get branch
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            state.branch = result.stdout.strip()

        # Get commit
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            state.commit = result.stdout.strip()

        # Get uncommitted files
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            state.uncommitted = [
                line[3:] for line in result.stdout.strip().split("\n")
                if line.strip()
            ]
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return state


def slugify(text: str) -> str:
    """Convert text to filename-safe slug."""
    # Lowercase, replace spaces/special chars with hyphens
    slug = text.lower()
    for char in [" ", "/", "\\", ":", ".", ",", "'", '"', "(", ")"]:
        slug = slug.replace(char, "-")
    # Remove multiple hyphens
    while "--" in slug:
        slug = slug.replace("--", "-")
    # Trim hyphens
    slug = slug.strip("-")
    # Fall back to "untitled" if slug is empty (e.g., title was all special chars)
    if not slug:
        slug = "untitled"
    # Limit length
    return slug[:50]


def generate_handoff_markdown(
    title: str,
    goal: str = "",
    task_status: List[str] = None,
    decisions: List[str] = None,
    abandoned: List[str] = None,
    changes: List[str] = None,
    learnings: List[str] = None,
    references: List[str] = None,
    artifacts: List[str] = None,
    user_context: List[str] = None,
    next_steps: List[str] = None,
    tags: List[str] = None,
    git_state: GitState = None
) -> str:
    """Generate handoff markdown document."""

    now = datetime.now()

    # Build frontmatter
    frontmatter = {
        "date": now.isoformat(),
        "version": 1,
    }

    if git_state and git_state.is_repo:
        if git_state.commit:
            frontmatter["git_commit"] = git_state.commit
        if git_state.branch:
            frontmatter["branch"] = git_state.branch

    frontmatter["repository"] = get_project_name()

    if tags:
        frontmatter["tags"] = tags

    # Build YAML frontmatter string
    yaml_lines = ["---"]
    for key, value in frontmatter.items():
        if isinstance(value, list):
            yaml_lines.append(f"{key}: {json.dumps(value)}")
        else:
            yaml_lines.append(f"{key}: {value}")
    yaml_lines.append("---")

    # Build markdown body
    lines = yaml_lines + ["", f"# Handoff: {title}", ""]

    if goal:
        lines.extend(["## Goal", goal, ""])

    if task_status:
        lines.append("## Task Status")
        for item in task_status:
            # Preserve checkbox format if present
            if item.startswith("- ["):
                lines.append(item)
            elif item.startswith("["):
                lines.append(f"- {item}")
            else:
                lines.append(f"- [ ] {item}")
        lines.append("")

    if decisions:
        lines.append("## Key Decisions")
        for decision in decisions:
            if decision.startswith("- "):
                lines.append(decision)
            else:
                lines.append(f"- {decision}")
        lines.append("")

    if abandoned:
        lines.append("## Attempted but Abandoned")
        for item in abandoned:
            if item.startswith("- "):
                lines.append(item)
            else:
                lines.append(f"- {item}")
        lines.append("")

    if changes:
        lines.append("## Recent Changes")
        for change in changes:
            if change.startswith("- "):
                lines.append(change)
            else:
                lines.append(f"- {change}")
        lines.append("")

    if learnings:
        lines.append("## Learnings")
        for learning in learnings:
            if learning.startswith("- "):
                lines.append(learning)
            else:
                lines.append(f"- {learning}")
        lines.append("")

    if references:
        lines.append("## Critical References")
        for ref in references:
            if ref.startswith("- "):
                lines.append(ref)
            else:
                lines.append(f"- {ref}")
        lines.append("")

    if artifacts:
        lines.append("## Artifacts")
        for artifact in artifacts:
            if artifact.startswith("- "):
                lines.append(artifact)
            else:
                lines.append(f"- {artifact}")
        lines.append("")

    if user_context:
        lines.append("## User Context")
        for ctx in user_context:
            if ctx.startswith("- "):
                lines.append(ctx)
            else:
                lines.append(f"- {ctx}")
        lines.append("")

    if next_steps:
        lines.append("## Next Steps")
        for i, step in enumerate(next_steps, 1):
            # Remove leading number if present
            step_text = step.lstrip("0123456789. ")
            lines.append(f"{i}. {step_text}")
        lines.append("")

    # Add git uncommitted if present
    if git_state and git_state.uncommitted:
        lines.append("## Uncommitted Files")
        lines.append("```")
        for file in git_state.uncommitted[:10]:  # Limit to 10
            lines.append(file)
        if len(git_state.uncommitted) > 10:
            lines.append(f"... and {len(git_state.uncommitted) - 10} more")
        lines.append("```")
        lines.append("")

    return "\n".join(lines)


def enforce_retention(handoffs_dir: Path, keep: int = 10) -> List[Path]:
    """Remove old handoffs, keep most recent N. Returns removed files."""
    if not handoffs_dir.exists():
        return []

    # Filter out symlinks to avoid FileNotFoundError on broken symlinks
    handoffs = sorted(
        [p for p in handoffs_dir.glob("*.md") if not p.is_symlink()],
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )

    removed = []
    for handoff in handoffs[keep:]:
        try:
            handoff.unlink()
            removed.append(handoff)
        except Exception:
            # Non-fatal: continue pruning other files if one fails
            pass

    return removed


def write_handoff(
    title: str,
    content: str,
    project_dir: Path,
    global_dir: Path
) -> Result:
    """Write handoff to project and global locations."""

    now = datetime.now()
    slug = slugify(title)
    filename = f"{now.strftime('%Y-%m-%d_%H-%M-%S')}_{slug}.md"

    # Ensure directories exist
    project_dir.mkdir(parents=True, exist_ok=True)
    global_dir.mkdir(parents=True, exist_ok=True)

    # Write to project directory
    project_path = project_dir / filename
    try:
        project_path.write_text(content)
    except Exception as e:
        return Result(
            success=False,
            message=f"Failed to write handoff: {e}",
            errors=[str(e)]
        )

    # Create symlink in global directory
    global_path = global_dir / f"{get_project_name()}_{filename}"
    try:
        if global_path.exists() or global_path.is_symlink():
            global_path.unlink()
        global_path.symlink_to(project_path)
    except Exception as e:
        # Non-fatal - log but continue
        pass

    # Enforce retention
    removed = enforce_retention(project_dir, keep=10)

    return Result(
        success=True,
        message=f"Handoff created: {project_path}",
        data={
            "path": str(project_path),
            "filename": filename,
            "removed_count": len(removed)
        }
    )


def main():
    parser = argparse.ArgumentParser(
        description="Create a handoff document",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--title", "-t",
        required=False,
        help="Handoff title/description"
    )

    parser.add_argument(
        "--goal", "-g",
        default="",
        help="What you were working on"
    )

    parser.add_argument(
        "--task-status",
        type=json.loads,
        default=[],
        help="Task checkboxes (JSON array)"
    )

    parser.add_argument(
        "--decisions",
        type=json.loads,
        default=[],
        help="Key decisions (JSON array)"
    )

    parser.add_argument(
        "--abandoned",
        type=json.loads,
        default=[],
        help="Attempted but abandoned (JSON array)"
    )

    parser.add_argument(
        "--changes",
        type=json.loads,
        default=[],
        help="Recent changes (JSON array)"
    )

    parser.add_argument(
        "--learnings",
        type=json.loads,
        default=[],
        help="Learnings (JSON array)"
    )

    parser.add_argument(
        "--references",
        type=json.loads,
        default=[],
        help="Critical references (JSON array)"
    )

    parser.add_argument(
        "--artifacts",
        type=json.loads,
        default=[],
        help="Artifacts created (JSON array)"
    )

    parser.add_argument(
        "--user-context",
        type=json.loads,
        default=[],
        help="User context/preferences (JSON array)"
    )

    parser.add_argument(
        "--next-steps",
        type=json.loads,
        default=[],
        help="Next steps (JSON array)"
    )

    parser.add_argument(
        "--tags",
        type=parse_flexible_list,
        default=[],
        help="Tags for categorization (JSON array or comma-separated)"
    )

    parser.add_argument(
        "--stdin",
        action="store_true",
        help="Read JSON input from stdin"
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output result as JSON"
    )

    parser.add_argument(
        "--project-dir",
        type=Path,
        help="Override project handoffs directory"
    )

    args = parser.parse_args()

    # Read from stdin if specified
    if args.stdin:
        try:
            data = json.load(sys.stdin)
            title = data.get("title", args.title)
            goal = data.get("goal", args.goal)
            task_status = data.get("task_status", args.task_status)
            decisions = data.get("decisions", args.decisions)
            abandoned = data.get("abandoned", args.abandoned)
            changes = data.get("changes", args.changes)
            learnings = data.get("learnings", args.learnings)
            references = data.get("references", args.references)
            artifacts = data.get("artifacts", args.artifacts)
            user_context = data.get("user_context", args.user_context)
            next_steps = data.get("next_steps", args.next_steps)
            tags = data.get("tags", args.tags)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON input: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        title = args.title
        goal = args.goal
        task_status = args.task_status
        decisions = args.decisions
        abandoned = args.abandoned
        changes = args.changes
        learnings = args.learnings
        references = args.references
        artifacts = args.artifacts
        user_context = args.user_context
        next_steps = args.next_steps
        tags = args.tags

    # Validate required fields
    if not title:
        print("Error: --title is required", file=sys.stderr)
        sys.exit(1)

    # Check if there's meaningful content
    has_content = any([
        goal, task_status, decisions, changes, learnings, next_steps
    ])
    if not has_content:
        print("Warning: No substantial content. Consider adding --goal or --next-steps", file=sys.stderr)

    # Gather git state
    git_state = get_git_state()

    # Generate markdown
    content = generate_handoff_markdown(
        title=title,
        goal=goal,
        task_status=task_status,
        decisions=decisions,
        abandoned=abandoned,
        changes=changes,
        learnings=learnings,
        references=references,
        artifacts=artifacts,
        user_context=user_context,
        next_steps=next_steps,
        tags=tags,
        git_state=git_state
    )

    # Write handoff
    project_dir = args.project_dir or get_project_handoffs_dir()
    global_dir = get_global_handoffs_dir()

    result = write_handoff(title, content, project_dir, global_dir)

    # Output
    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        if result.success:
            print(f"Handoff created: {result.data['path']}")
            if result.data.get("removed_count", 0) > 0:
                print(f"Pruned {result.data['removed_count']} old handoff(s)")
        else:
            print(f"Error: {result.message}", file=sys.stderr)

    sys.exit(0 if result.success else 2)


if __name__ == "__main__":
    main()
