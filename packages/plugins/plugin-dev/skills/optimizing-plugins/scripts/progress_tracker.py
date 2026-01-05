#!/usr/bin/env python3
"""
Track optimization implementation progress.

Manages state across sessions, marking suggestions complete and
recalculating projected scores.

Usage:
    python progress_tracker.py init <design-doc.md>
    python progress_tracker.py status
    python progress_tracker.py complete <suggestion-id>
    python progress_tracker.py reset

Exit Codes:
    0  - Success
    1  - General failure
    2  - Invalid arguments
    10 - State file error
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional


STATE_DIR = Path.home() / ".cache" / "optimizing-plugins"
STATE_FILE = STATE_DIR / "progress.json"


@dataclass
class Suggestion:
    """A single optimization suggestion."""
    id: str
    priority: str
    lens: str
    title: str
    status: str = "pending"  # pending | in_progress | completed | skipped
    completed_at: Optional[str] = None


@dataclass
class ProgressState:
    """Overall progress state."""
    version: str = "1.0"
    plugin_name: str = ""
    design_doc: str = ""
    created_at: str = ""
    updated_at: str = ""
    suggestions: list = field(default_factory=list)
    scores_before: dict = field(default_factory=dict)
    scores_projected: dict = field(default_factory=dict)


@dataclass
class Result:
    """Operation result."""
    success: bool
    message: str
    data: Optional[dict] = None
    errors: list = field(default_factory=list)


def load_state() -> Optional[ProgressState]:
    """Load state from file."""
    if not STATE_FILE.exists():
        return None

    try:
        data = json.loads(STATE_FILE.read_text())
        state = ProgressState(
            version=data.get("version", "1.0"),
            plugin_name=data.get("plugin_name", ""),
            design_doc=data.get("design_doc", ""),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            suggestions=data.get("suggestions", []),
            scores_before=data.get("scores_before", {}),
            scores_projected=data.get("scores_projected", {}),
        )
        return state
    except (json.JSONDecodeError, KeyError) as e:
        return None


def save_state(state: ProgressState) -> bool:
    """Save state to file."""
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        state.updated_at = datetime.now().isoformat()
        STATE_FILE.write_text(json.dumps(asdict(state), indent=2))
        return True
    except Exception:
        return False


def extract_suggestions_from_doc(doc_path: Path) -> list[dict]:
    """Extract suggestions from design document."""
    if not doc_path.exists():
        return []

    content = doc_path.read_text()
    suggestions = []

    # Try to extract from embedded JSON first
    json_pattern = re.compile(
        r'<!--\s*OPTIMIZATION_DATA\s*\n(.*?)\n\s*-->',
        re.DOTALL
    )
    match = json_pattern.search(content)
    if match:
        try:
            data = json.loads(match.group(1))
            if "suggestions" in data:
                return data["suggestions"]
        except json.JSONDecodeError:
            pass

    # Fall back to parsing markdown
    # Look for ### [Priority] Title patterns
    suggestion_pattern = re.compile(
        r'^### \[(\w+(?:\s+\w+)?)\]\s+(.+?)$\n.*?^\*\*Lens:\*\*\s*(\w+)',
        re.MULTILINE
    )

    for i, match in enumerate(suggestion_pattern.finditer(content)):
        priority = match.group(1).lower().replace(" ", "_")
        title = match.group(2).strip()
        lens = match.group(3).strip().lower().replace(" ", "_")

        suggestions.append({
            "id": f"S{i+1}",
            "priority": priority,
            "lens": lens,
            "title": title,
            "status": "pending",
        })

    return suggestions


def extract_scores_from_doc(doc_path: Path) -> dict:
    """Extract scores from design document."""
    if not doc_path.exists():
        return {}

    content = doc_path.read_text()

    # Try embedded JSON
    json_pattern = re.compile(
        r'<!--\s*OPTIMIZATION_DATA\s*\n(.*?)\n\s*-->',
        re.DOTALL
    )
    match = json_pattern.search(content)
    if match:
        try:
            data = json.loads(match.group(1))
            return data.get("scores", {})
        except json.JSONDecodeError:
            pass

    return {}


def cmd_init(args) -> Result:
    """Initialize tracking from a design document."""
    doc_path = Path(args.design_doc)

    if not doc_path.exists():
        return Result(
            success=False,
            message=f"Design document not found: {doc_path}",
            errors=["File not found"]
        )

    suggestions = extract_suggestions_from_doc(doc_path)
    scores = extract_scores_from_doc(doc_path)

    if not suggestions:
        return Result(
            success=False,
            message="No suggestions found in document",
            errors=["Could not parse suggestions from document"]
        )

    # Extract plugin name from document
    content = doc_path.read_text()
    name_match = re.search(r'^# Plugin Optimization:\s*(.+)$', content, re.MULTILINE)
    plugin_name = name_match.group(1).strip() if name_match else doc_path.stem

    state = ProgressState(
        plugin_name=plugin_name,
        design_doc=str(doc_path.absolute()),
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
        suggestions=suggestions,
        scores_before=scores.get("before", {}),
        scores_projected=scores.get("after", {}),
    )

    if not save_state(state):
        return Result(
            success=False,
            message="Failed to save state",
            errors=["Could not write state file"]
        )

    return Result(
        success=True,
        message=f"Initialized tracking for {plugin_name} with {len(suggestions)} suggestions",
        data={
            "plugin": plugin_name,
            "suggestion_count": len(suggestions),
            "state_file": str(STATE_FILE),
        }
    )


def cmd_status(args) -> Result:
    """Show current progress status."""
    state = load_state()

    if not state:
        return Result(
            success=False,
            message="No progress tracked. Run 'init' first.",
            errors=["No state file found"]
        )

    total = len(state.suggestions)
    completed = sum(1 for s in state.suggestions if s.get("status") == "completed")
    in_progress = sum(1 for s in state.suggestions if s.get("status") == "in_progress")
    pending = sum(1 for s in state.suggestions if s.get("status") == "pending")
    skipped = sum(1 for s in state.suggestions if s.get("status") == "skipped")

    # Group by priority
    by_priority = {}
    for s in state.suggestions:
        priority = s.get("priority", "unknown")
        if priority not in by_priority:
            by_priority[priority] = {"total": 0, "completed": 0}
        by_priority[priority]["total"] += 1
        if s.get("status") == "completed":
            by_priority[priority]["completed"] += 1

    return Result(
        success=True,
        message=f"Progress: {completed}/{total} complete ({100*completed//total if total else 0}%)",
        data={
            "plugin": state.plugin_name,
            "total": total,
            "completed": completed,
            "in_progress": in_progress,
            "pending": pending,
            "skipped": skipped,
            "by_priority": by_priority,
            "scores_before": state.scores_before,
            "scores_projected": state.scores_projected,
            "suggestions": state.suggestions,
        }
    )


def cmd_complete(args) -> Result:
    """Mark a suggestion as complete."""
    state = load_state()

    if not state:
        return Result(
            success=False,
            message="No progress tracked. Run 'init' first.",
            errors=["No state file found"]
        )

    suggestion_id = args.suggestion_id.upper()
    found = False

    for s in state.suggestions:
        if s.get("id", "").upper() == suggestion_id:
            s["status"] = "completed"
            s["completed_at"] = datetime.now().isoformat()
            found = True
            break

    if not found:
        available = [s.get("id") for s in state.suggestions]
        return Result(
            success=False,
            message=f"Suggestion {suggestion_id} not found",
            errors=[f"Available: {', '.join(available)}"]
        )

    if not save_state(state):
        return Result(
            success=False,
            message="Failed to save state",
            errors=["Could not write state file"]
        )

    completed = sum(1 for s in state.suggestions if s.get("status") == "completed")
    total = len(state.suggestions)

    return Result(
        success=True,
        message=f"Marked {suggestion_id} complete. Progress: {completed}/{total}",
        data={
            "suggestion_id": suggestion_id,
            "completed": completed,
            "total": total,
        }
    )


def cmd_reset(args) -> Result:
    """Reset all progress."""
    if STATE_FILE.exists():
        STATE_FILE.unlink()

    return Result(
        success=True,
        message="Progress reset",
        data={"state_file": str(STATE_FILE)}
    )


def main():
    parser = argparse.ArgumentParser(
        description="Track optimization implementation progress",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # init command
    init_parser = subparsers.add_parser("init", help="Initialize from design doc")
    init_parser.add_argument("design_doc", type=str, help="Path to design document")

    # status command
    subparsers.add_parser("status", help="Show progress status")

    # complete command
    complete_parser = subparsers.add_parser("complete", help="Mark suggestion complete")
    complete_parser.add_argument("suggestion_id", type=str, help="Suggestion ID (e.g., S1)")

    # reset command
    subparsers.add_parser("reset", help="Reset all progress")

    args = parser.parse_args()

    # Route to command
    if args.command == "init":
        result = cmd_init(args)
    elif args.command == "status":
        result = cmd_status(args)
    elif args.command == "complete":
        result = cmd_complete(args)
    elif args.command == "reset":
        result = cmd_reset(args)
    else:
        result = Result(success=False, message=f"Unknown command: {args.command}")

    if args.json:
        print(json.dumps(asdict(result), indent=2))
    else:
        if result.success:
            print(f"✓ {result.message}")
            if result.data and args.command == "status":
                print()
                data = result.data
                print(f"Plugin: {data['plugin']}")
                print(f"Progress: {data['completed']}/{data['total']} suggestions")
                print()
                print("By priority:")
                for priority, counts in data.get("by_priority", {}).items():
                    print(f"  {priority}: {counts['completed']}/{counts['total']}")
                print()
                print("Suggestions:")
                for s in data.get("suggestions", []):
                    status_icon = {"completed": "✓", "in_progress": "→", "pending": "○", "skipped": "–"}.get(s["status"], "?")
                    print(f"  {status_icon} [{s['id']}] {s['title'][:50]}")
        else:
            print(f"✗ {result.message}")
            for error in result.errors:
                print(f"  {error}")

    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    main()
