"""Summary generation from parsed transcript data."""

from datetime import datetime, timezone
from pathlib import Path

from .transcript import TranscriptData


def generate_title(transcript_data: TranscriptData, branch: str | None) -> str:
    """Generate a session title from content."""
    # Use branch name as hint if available
    if branch and branch not in ("main", "master"):
        # Convert branch name to title
        # feat/auth-fix -> auth fix
        parts = branch.split("/")[-1].replace("-", " ").replace("_", " ")
        return parts.title()

    # Fall back to first file touched
    if transcript_data.files_touched:
        first_file = sorted(transcript_data.files_touched)[0]
        return Path(first_file).stem.replace("_", " ").title()

    return "Session"


def generate_slug(title: str) -> str:
    """Generate a filename slug from title."""
    return title.lower().replace(" ", "-")[:30]


def calculate_duration_minutes(start_time: str, end_time: datetime) -> int:
    """Calculate session duration in minutes."""
    start = datetime.fromisoformat(start_time)
    # Handle timezone-naive datetimes by assuming UTC
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    if end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=timezone.utc)
    delta = end_time - start
    return max(1, int(delta.total_seconds() / 60))


def generate_summary(
    transcript_data: TranscriptData,
    session_state: dict,
    commit_end: str | None = None,
    commits_made: int = 0,
    end_time: datetime | None = None,
) -> str:
    """Generate a session summary markdown document."""
    if end_time is None:
        end_time = datetime.now(timezone.utc)

    start_time = session_state.get("start_time", end_time.isoformat())
    branch = session_state.get("branch")
    project = Path(session_state.get("cwd", ".")).name

    title = generate_title(transcript_data, branch)
    duration = calculate_duration_minutes(start_time, end_time)

    # Build frontmatter
    frontmatter_lines = [
        "---",
        f"date: {start_time}",
        f"duration_minutes: {duration}",
        f"project: {project}",
    ]

    if branch:
        frontmatter_lines.append(f"branch: {branch}")
    if session_state.get("commit_start"):
        frontmatter_lines.append(f"commit_start: {session_state['commit_start']}")
    if commit_end:
        frontmatter_lines.append(f"commit_end: {commit_end}")
    if commits_made:
        frontmatter_lines.append(f"commits_made: {commits_made}")

    frontmatter_lines.extend([
        f"files_touched: {len(transcript_data.files_touched)}",
        f"commands_run: {len(transcript_data.commands_run)}",
        "---",
    ])

    # Build content
    content_lines = [
        "",
        f"# Session: {title}",
        "",
        "## Accomplished",
        "",
        "- Session summary pending analysis",
        "",
        "## Files",
        "",
    ]

    if transcript_data.files_touched:
        files = sorted(transcript_data.files_touched)
        if len(files) <= 5:
            content_lines.append(", ".join(files))
        else:
            content_lines.append(", ".join(files[:5]) + f" (+{len(files) - 5})")
    else:
        content_lines.append("No files modified")

    content_lines.append("")

    return "\n".join(frontmatter_lines + content_lines)


def get_summary_filename(session_state: dict, title: str) -> str:
    """Generate the summary filename."""
    start_time = session_state.get("start_time", datetime.now(timezone.utc).isoformat())
    try:
        dt = datetime.fromisoformat(start_time)
    except ValueError:
        dt = datetime.now(timezone.utc)
    date_str = dt.strftime("%Y-%m-%d_%H-%M-%S")
    slug = generate_slug(title)
    return f"{date_str}_{slug}.md"
