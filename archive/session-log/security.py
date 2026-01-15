"""Security utilities for session-log MCP server."""

from pathlib import Path


def validate_summary_path(summary_path: str, base_dir: Path | None = None) -> str | None:
    """Validate summary path is within expected directory.

    Prevents path traversal attacks by ensuring the resolved path
    stays within the expected base directory.

    Args:
        summary_path: Path to validate.
        base_dir: Base directory to restrict to (default: ~/.claude).

    Returns:
        Validated path string if safe, None otherwise.
    """
    if base_dir is None:
        base_dir = Path.home() / ".claude"

    try:
        path = Path(summary_path).resolve()
        base_resolved = base_dir.resolve()

        # Check path is within base directory
        if not path.is_relative_to(base_resolved):
            return None

        # Check file exists
        if not path.exists():
            return None

        return str(path)
    except (ValueError, OSError):
        return None
