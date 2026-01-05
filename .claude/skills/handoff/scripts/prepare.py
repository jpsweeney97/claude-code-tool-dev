#!/usr/bin/env python3
"""
prepare.py - Prepare transcript for synthesis.

Part of the handoff skill.

Responsibilities:
- Load session transcript from JSONL
- Filter noise (tool results, metadata entries)
- Annotate with line numbers
- Output formatted text for Opus synthesis prompt

Usage:
    python prepare.py                    # Current session (uses CLAUDE_SESSION_ID)
    python prepare.py --session <uuid>   # Specific session
    python prepare.py --list             # List available sessions
    python prepare.py --project <name>   # Override project detection

Output:
    Formatted transcript with metadata header, ready for synthesis prompt.

Exit Codes:
    0  - Success
    1  - Session not found
    2  - No transcript content
"""

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from common import Result, get_project_name


@dataclass
class TranscriptEntry:
    """Parsed transcript entry."""
    line_num: int
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[str] = None
    model: Optional[str] = None


def get_claude_projects_dir() -> Path:
    """Get Claude projects directory."""
    return Path.home() / ".claude" / "projects"


def get_project_dir_name() -> str:
    """Get URL-encoded project directory name from current working directory."""
    cwd = Path.cwd()
    # Claude encodes paths: / becomes -, . becomes - (resulting in -- for /.)
    encoded = str(cwd).replace("/", "-")
    # Handle dots in path components (like .claude becomes -claude, not --claude)
    # The actual pattern seems to be: /. becomes --
    # So "/Users/jp/.claude" -> "-Users-jp--claude"
    return encoded.replace("-.", "--")


def find_transcript_path(session_id: str, project_name: Optional[str] = None) -> Optional[Path]:
    """Find transcript file for a session.

    Supports partial UUID matching - prefix of session ID will match.
    Returns None if no match or multiple matches found.
    """
    projects_dir = get_claude_projects_dir()

    def find_in_dir(project_dir: Path) -> Optional[Path]:
        """Find session in a project directory, supporting partial match."""
        if not project_dir.exists():
            return None

        # Try exact match first
        exact = project_dir / f"{session_id}.jsonl"
        if exact.exists():
            return exact

        # Try partial match (prefix)
        matches = list(project_dir.glob(f"{session_id}*.jsonl"))
        if len(matches) == 1:
            return matches[0]

        return None

    if project_name:
        # Direct project name provided
        return find_in_dir(projects_dir / project_name)

    # Try current project first
    current_project = get_project_dir_name()
    result = find_in_dir(projects_dir / current_project)
    if result:
        return result

    # Search all projects
    for project_dir in projects_dir.iterdir():
        if project_dir.is_dir():
            result = find_in_dir(project_dir)
            if result:
                return result

    return None


def list_sessions(project_name: Optional[str] = None) -> List[dict]:
    """List available sessions with metadata."""
    projects_dir = get_claude_projects_dir()
    sessions = []

    if project_name:
        project_dirs = [projects_dir / project_name]
    else:
        # Use current project
        current_project = get_project_dir_name()
        project_dirs = [projects_dir / current_project]

    for project_dir in project_dirs:
        if not project_dir.exists():
            continue

        for transcript in project_dir.glob("*.jsonl"):
            session_id = transcript.stem
            stat = transcript.stat()

            # Try to get summary from first line
            summary = None
            try:
                with open(transcript) as f:
                    first_line = f.readline()
                    entry = json.loads(first_line)
                    if entry.get("type") == "summary":
                        summary = entry.get("summary", "")
            except (json.JSONDecodeError, KeyError):
                pass

            sessions.append({
                "session_id": session_id,
                "project": project_dir.name,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "size_kb": round(stat.st_size / 1024, 1),
                "summary": summary
            })

    # Sort by modification time, newest first
    sessions.sort(key=lambda x: x["modified"], reverse=True)
    return sessions


def load_transcript(path: Path) -> List[dict]:
    """Load JSONL transcript file."""
    entries = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return entries


def extract_text_content(content) -> str:
    """Extract text from message content (string or array of blocks)."""
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        texts = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    texts.append(block.get("text", ""))
                elif block.get("type") == "tool_use":
                    # Include tool name for context
                    tool_name = block.get("name", "unknown")
                    texts.append(f"[Tool: {tool_name}]")
                # Skip tool_result - it's noise
        return " ".join(texts)

    return ""


def filter_and_annotate(entries: List[dict]) -> List[TranscriptEntry]:
    """Filter to user/assistant messages and annotate with line numbers."""
    result = []
    line_num = 0

    for entry in entries:
        entry_type = entry.get("type")

        # Skip metadata entries
        if entry_type in ("summary", "file-history-snapshot", "queue-operation"):
            continue

        # Skip meta messages (system injections)
        if entry.get("isMeta"):
            continue

        # Process user and assistant messages
        if entry_type in ("user", "assistant"):
            message = entry.get("message", {})
            content = message.get("content", "")

            text = extract_text_content(content)
            if not text.strip():
                continue

            # Truncate very long content (tool outputs)
            if len(text) > 2000:
                text = text[:2000] + "... [truncated]"

            line_num += 1
            result.append(TranscriptEntry(
                line_num=line_num,
                role=entry_type,
                content=text.strip(),
                timestamp=entry.get("timestamp"),
                model=message.get("model") if entry_type == "assistant" else None
            ))

    return result


def format_for_synthesis(entries: List[TranscriptEntry], metadata: dict) -> str:
    """Format transcript with metadata header for synthesis prompt."""
    lines = []

    # Metadata header
    lines.append("# Session Metadata")
    lines.append(f"branch: {metadata.get('branch', 'unknown')}")
    lines.append(f"commit: {metadata.get('commit', 'unknown')}")
    lines.append(f"date: {metadata.get('date', datetime.now().isoformat())}")
    lines.append(f"repository: {metadata.get('repository', 'unknown')}")
    lines.append("")
    lines.append("# Transcript")
    lines.append("")

    # Annotated transcript
    for entry in entries:
        role_tag = "[user]" if entry.role == "user" else "[assistant]"
        lines.append(f"L{entry.line_num}: {role_tag} {entry.content}")

    return "\n".join(lines)


def get_git_metadata() -> dict:
    """Gather git metadata."""
    metadata = {
        "branch": None,
        "commit": None,
        "date": datetime.now().isoformat(),
        "repository": get_project_name()
    }

    try:
        # Get branch
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            metadata["branch"] = result.stdout.strip()

        # Get commit
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            metadata["commit"] = result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return metadata


def main():
    parser = argparse.ArgumentParser(
        description="Prepare transcript for synthesis",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--session", "-s",
        help="Session ID (UUID). Defaults to CLAUDE_SESSION_ID env var."
    )

    parser.add_argument(
        "--project", "-p",
        help="Project directory name (overrides auto-detection)"
    )

    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List available sessions"
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON (for --list)"
    )

    args = parser.parse_args()

    # List mode
    if args.list:
        sessions = list_sessions(args.project)
        if args.json:
            print(json.dumps(sessions, indent=2))
        else:
            if not sessions:
                print("No sessions found.", file=sys.stderr)
                sys.exit(1)

            print(f"{'Session ID':<40} {'Modified':<25} {'Size':<10} Summary")
            print("-" * 100)
            for s in sessions[:10]:  # Show last 10
                summary = (s["summary"] or "")[:30]
                print(f"{s['session_id']:<40} {s['modified']:<25} {s['size_kb']:<10} {summary}")
        sys.exit(0)

    # Get session ID
    session_id = args.session or os.environ.get("CLAUDE_SESSION_ID")
    if not session_id:
        print("Error: No session ID. Use --session or set CLAUDE_SESSION_ID.", file=sys.stderr)
        sys.exit(1)

    # Find transcript
    transcript_path = find_transcript_path(session_id, args.project)
    if not transcript_path:
        print(f"Error: Transcript not found for session {session_id}", file=sys.stderr)
        sys.exit(1)

    # Load and process
    entries = load_transcript(transcript_path)
    filtered = filter_and_annotate(entries)

    if not filtered:
        print("Error: No conversation content found in transcript.", file=sys.stderr)
        sys.exit(2)

    # Get metadata and format
    metadata = get_git_metadata()
    output = format_for_synthesis(filtered, metadata)

    print(output)
    sys.exit(0)


if __name__ == "__main__":
    main()
